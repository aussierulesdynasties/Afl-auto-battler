#!/usr/bin/env bash
# One pack per ground: everything under assets/grounds/<slug>/ (the model, its textures, seats and
# surroundings) as its own Godot pack, for a build that leaves the ground models out and loads a
# ground's pack when a match is played there (GroundPacks.gd; docs/ITCH_BUILDS.md).
#
#   tools/ground_packs/export.sh <android|windows|web> <out dir> [slug ...]
#
# Writes <out>/<slug>-<id>.pck per ground and <out>/ground_packs.json, the list a build carries:
# {"platform", "godot", "packs": {slug: {"file", "bytes", "sha256"}}}. <id> is the ground folder's
# git tree hash (first 10), so a pack's name changes exactly when its ground changes, and the
# same commit gives the same names on any machine. Texture formats follow the platform
# (Android ETC2/ASTC, Windows S3TC/BPTC, Web both), so each platform has its own packs.
# Needs an imported project (godot --headless --import) and export templates.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
GODOT="${GODOT:-godot}"
target="${1:?platform: android, windows or web}"
OUT="$(mkdir -p "${2:?out dir}" && cd "$2" && pwd)"
shift 2
case "$target" in
	android) platform="Android" ;;
	windows) platform="Windows Desktop" ;;
	web) platform="Web" ;;
	*) echo "unknown platform $target" >&2; exit 1 ;;
esac
slugs=("$@")
if [ ${#slugs[@]} -eq 0 ]; then
	for d in assets/grounds/*/; do slugs+=("$(basename "$d")"); done
fi

# The real presets come back however this ends.
cp export_presets.cfg "$OUT/.presets.bak"
trap 'cp "$OUT/.presets.bak" export_presets.cfg; rm -f "$OUT/.presets.bak"' EXIT

godot_version="$("$GODOT" --version 2>/dev/null | head -1 | tr -d '\r')"
json="$OUT/ground_packs.json"
{
	echo "{"
	echo "  \"platform\": \"$target\","
	echo "  \"godot\": \"$godot_version\","
	echo "  \"packs\": {"
} > "$json.tmp"
first=1
for slug in "${slugs[@]}"; do
	dir="assets/grounds/$slug"
	[ -d "$dir" ] || { echo "no $dir" >&2; exit 1; }
	id="$(git rev-parse --short=10 "HEAD:$dir" 2>/dev/null || echo untracked)"
	if [ -n "$(git status --porcelain -- "$dir" ':!*.import')" ]; then
		id="${id}-dirty"
	fi
	file="$slug-$id.pck"
	# Every imported resource in the folder (its .import beside it) plus every other file
	# (seats .bin, surroundings, json) by the include filter.
	files=""
	for imp in "$dir"/*.import; do
		[ -e "$imp" ] || continue
		files+="\"res://${imp%.import}\", "
	done
	cat > export_presets.cfg <<PRESET
[preset.0]

name="GroundPack"
platform="$platform"
runnable=false
dedicated_server=false
custom_features=""
export_filter="resources"
export_files=PackedStringArray(${files%, })
include_filter="$dir/*.bin, $dir/*.json"
exclude_filter=""
export_path=""

[preset.0.options]

PRESET
	rm -f "$OUT/$file"
	work="$OUT/.work-$slug"
	rm -rf "$work" && mkdir -p "$work/files" "$work/empty"
	if ! "$GODOT" --headless --path "$ROOT" --export-pack "GroundPack" "$work/export.pck" > "$work/log" 2>&1 || [ ! -s "$work/export.pck" ]; then
		tail -20 "$work/log" >&2
		echo "FAIL: $slug pack" >&2
		exit 1
	fi
	# Only the ground's own files: an export always adds the game's own (strip.py).
	python3 "$ROOT/tools/ground_packs/strip.py" "$work/export.pck" "$slug" "$work/files" > /dev/null
	# Packed from an empty folder, so no project (and none of its autoloads) starts.
	if ! (cd "$work/empty" && "$GODOT" --headless --script "$ROOT/tools/ground_packs/pack.gd" -- "$work/files" "$OUT/$file") >> "$work/log" 2>&1 \
			|| [ ! -s "$OUT/$file" ]; then
		tail -20 "$work/log" >&2
		echo "FAIL: $slug pack" >&2
		exit 1
	fi
	rm -rf "$work"
	bytes="$(stat -c %s "$OUT/$file")"
	sha="$(sha256sum "$OUT/$file" | cut -d' ' -f1)"
	[ $first -eq 1 ] || echo "," >> "$json.tmp"
	first=0
	printf '    "%s": {"file": "%s", "bytes": %s, "sha256": "%s"}' "$slug" "$file" "$bytes" "$sha" >> "$json.tmp"
	echo "$slug $file $((bytes / 1000000)) MB"
done
printf '\n  }\n}\n' >> "$json.tmp"
mv "$json.tmp" "$json"
