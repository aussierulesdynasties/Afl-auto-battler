#!/usr/bin/env bash
# Guard the exported build's data path. The editor and every other test read
# the source tree, where all CSVs exist whatever their importer - so a CSV on
# Godot's default csv_translation importer (which an export leaves out) goes
# unnoticed there. This exports a real .pck and runs the game data load from
# that pack alone.
#
#   GODOT=/path/to/godot tools/check_export_data.sh
#
# Step 1 (no Godot needed): every data/*.csv must be imported with "keep".
# Step 2: export a pack from the tracked + working-tree files with a throwaway
# preset, then run tests/export_data_check.gd against the pack in an empty
# directory: the player data must be there, loaded, with ages.
set -u
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
GODOT="${GODOT:-godot}"
fail=0

echo "-- data CSV import settings"
for csv in data/*.csv; do
	imp="$csv.import"
	if [ ! -f "$imp" ]; then
		echo "FAIL: $csv has no .import file (Godot would default it to a translation import)"
		fail=1
	elif ! grep -q '^importer="keep"' "$imp"; then
		echo "FAIL: $imp is not importer=\"keep\" ($(grep '^importer=' "$imp")) - an export would leave $csv out"
		fail=1
	fi
done
[ "$fail" = 0 ] && echo "all data CSVs use the keep importer"

echo "-- web export: phone keyboard"
# The web build must have the engine's phone keyboard on. With it off a
# phone's browser has no keyboard support: the one that shows opens and closes
# by itself and drops what is typed (godotengine/godot#99602; the director's
# clips of 2026-10-14).
if grep -q '^html/experimental_virtual_keyboard=true' "$ROOT/export_presets.cfg"; then
	echo "the Web preset has html/experimental_virtual_keyboard=true"
else
	echo "FAIL: export_presets.cfg must set html/experimental_virtual_keyboard=true (the phone keyboard in a browser)"
	fail=1
fi

echo "-- exported pack data load"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/project" "$WORK/run"
# Tracked and new (unignored) files as they are on disk: the same set an
# export from this checkout would see, without .godot/ caches or builds.
git ls-files -co --exclude-standard -z | (cd "$ROOT" && tar --null -T - -cf -) | tar -xf - -C "$WORK/project"
# The Epic/MetaHuman files are ignored (docs/EPIC_ASSETS.md), so ls-files leaves them out; an export
# fetches them first (tools/export_builds.sh), so copy the ones the lock pins in as well.
# The ground models are ignored too (docs/GROUND_ASSETS.md): copy assets/grounds/ whole, with the
# textures Godot extracts from each model on import, as an export from this checkout would see it.
cp -R "$ROOT/assets/grounds/." "$WORK/project/assets/grounds/"
awk '$1 ~ /^[0-9a-f]+$/ && length($1) == 64 {print $2}' "$ROOT/tools/epic_assets.lock" | while read -r f; do
	if [ -f "$ROOT/$f" ]; then
		mkdir -p "$WORK/project/$(dirname "$f")"
		cp "$ROOT/$f" "$WORK/project/$f"
	fi
done
# The Android preset's own include and exclude filters, so the pack holds what the
# phone's build holds: an asset its filters leave out is missing here too (an
# exclude of every *.glb once took the 3D footballer out of the phone build, and
# Club Forge's Create a player crashed on it).
android_filter() {
	awk -v key="$1" '/^\[preset\.[0-9]+\]$/ {sec=$0} /^name="Android"$/ {a=sec}
		a != "" && sec == a && index($0, key "=") == 1 {sub(key "=", ""); print; exit}' "$ROOT/export_presets.cfg"
}
INCLUDE="$(android_filter include_filter)"
EXCLUDE="$(android_filter exclude_filter)"
if [ -z "$EXCLUDE" ]; then
	echo "FAIL: no exclude_filter found for the Android preset in export_presets.cfg"
	exit 1
fi
echo "-- exported pack, with the Android preset's filters"
echo "include: $INCLUDE"
echo "exclude: $EXCLUDE"
cat > "$WORK/project/export_presets.cfg" <<PRESET
[preset.0]

name="DataCheck"
platform="Linux"
runnable=true
export_filter="all_resources"
include_filter=$INCLUDE
exclude_filter=$EXCLUDE
export_path=""

[preset.0.options]

binary_format/embed_pck=false
binary_format/architecture="x86_64"
PRESET
# The checkout's own import, when it has one, so the ground models (hundreds of MB of glb) are
# not imported a second time: Godot re-imports only what changed since.
[ -d "$ROOT/.godot/imported" ] && cp -a "$ROOT/.godot" "$WORK/project/"
"$GODOT" --headless --path "$WORK/project" --import > "$WORK/import.log" 2>&1
if ! "$GODOT" --headless --path "$WORK/project" --export-pack "DataCheck" "$WORK/run/game.pck" > "$WORK/export.log" 2>&1 \
		|| [ ! -s "$WORK/run/game.pck" ]; then
	tail -20 "$WORK/export.log"
	echo "FAIL: could not export a pack"
	exit 1
fi
# Run from an empty directory so res:// can only resolve inside the pack.
if (cd "$WORK/run" && timeout 300 "$GODOT" --headless --main-pack game.pck \
		--script "$ROOT/tests/export_data_check.gd") > "$WORK/check.log" 2>&1; then
	grep "Export data check:" "$WORK/check.log"
else
	grep -E "Export data check|^ERROR" "$WORK/check.log" | head -20
	echo "FAIL: the exported pack does not load complete player data, or Club Forge's Create a player fails in it"
	fail=1
fi
exit "$fail"
