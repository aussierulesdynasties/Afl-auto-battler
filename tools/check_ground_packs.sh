#!/usr/bin/env bash
# Prove the per-ground packs end to end on this machine: a build with no ground models fetches a
# ground's pack over HTTP, checks it, keeps it and builds the ground from it; a second start
# loads the kept pack with no download. (tests/ground_packs_check.gd; docs/ITCH_BUILDS.md)
#
#   GODOT=/path/to/godot tools/check_ground_packs.sh [slug]     # default: engie, the smallest
# Needs an imported project.
set -u
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
GODOT="${GODOT:-godot}"
SLUG="${1:-engie}"
WORK="$(mktemp -d)"
PORT=$((20000 + RANDOM % 20000))
cp export_presets.cfg "$WORK/presets.bak"
cleanup() {
	cp "$WORK/presets.bak" "$ROOT/export_presets.cfg"
	rm -f "$ROOT/ground_packs.json"
	[ -n "${SERVER:-}" ] && kill "$SERVER" 2>/dev/null
	rm -rf "$WORK"
}
trap cleanup EXIT
mkdir -p "$WORK/www/grounds" "$WORK/run"

echo "-- the ground's pack"
GODOT="$GODOT" tools/ground_packs/export.sh windows "$WORK/www/grounds" "$SLUG" || exit 1
python3 - "$WORK/www/grounds/ground_packs.json" "http://127.0.0.1:$PORT/grounds" > "$ROOT/ground_packs.json" <<'PY'
import json, sys
m = json.load(open(sys.argv[1])); m["url"] = sys.argv[2]; print(json.dumps(m, indent=2))
PY

echo "-- a build with no ground models"
cat > "$ROOT/export_presets.cfg" <<'PRESET'
[preset.0]

name="PackBase"
platform="Linux"
runnable=true
export_filter="all_resources"
include_filter="ground_packs.json"
exclude_filter="docs/*, tools/*, tests/*, addons/*, assets/grounds/*"
export_path=""

[preset.0.options]

binary_format/embed_pck=false
binary_format/architecture="x86_64"
PRESET
if ! "$GODOT" --headless --path "$ROOT" --export-pack "PackBase" "$WORK/run/game.pck" > "$WORK/export.log" 2>&1; then
	tail -20 "$WORK/export.log"; echo "FAIL: could not export the base pack"; exit 1
fi
cp "$WORK/presets.bak" "$ROOT/export_presets.cfg"

(cd "$WORK/www" && exec python3 -m http.server "$PORT" --bind 127.0.0.1 > "$WORK/http.log" 2>&1) &
SERVER=$!
sleep 1
fail=0
for run in fetch kept; do
	echo "-- start ($run)"
	# HOME and XDG under the work folder, so user:// is a fresh one for this check.
	if (cd "$WORK/run" && HOME="$WORK/home" XDG_DATA_HOME="$WORK/home/data" timeout 300 "$GODOT" --headless \
			--main-pack game.pck --script "$ROOT/tests/ground_packs_check.gd" -- "$SLUG") > "$WORK/$run.log" 2>&1; then
		grep "Ground packs check:" "$WORK/$run.log"; grep -c -E "WARNING|ERROR" "$WORK/$run.log" | sed "s/^/warnings and errors in the log: /"; grep -E "WARNING|ERROR" "$WORK/$run.log" | sort | uniq -c | sort -rn | head -5
	else
		grep -E "Ground packs check|ERROR" "$WORK/$run.log" | head -20
		fail=1
	fi
done
downloads=$(grep -c "GET /grounds/.*\.pck" "$WORK/http.log")
echo "pack downloads served: $downloads (want 1)"
[ "$downloads" = 1 ] || fail=1
echo "-- a 3D match at the ground: fails with no server, a real tap on the line fetches it"
if (cd "$WORK/run" && HOME="$WORK/home2" XDG_DATA_HOME="$WORK/home2/data" timeout 600 "$GODOT" --headless \
		--main-pack game.pck --script "$ROOT/tests/ground_packs_check.gd" -- "$SLUG" pitch) > "$WORK/pitch.log" 2>&1; then
	grep "Ground packs check:" "$WORK/pitch.log"
else
	grep -E "Ground packs check|ERROR|SCRIPT" "$WORK/pitch.log" | head -20
	fail=1
fi
[ $fail = 0 ] && echo "ground packs: ok" || echo "FAIL: ground packs"
exit $fail
