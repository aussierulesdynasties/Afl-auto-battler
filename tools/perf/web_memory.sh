#!/usr/bin/env bash
# Browser memory of the Web build with the per-ground packs (docs/ITCH_BUILDS.md): exports the
# Web build as the 3D phone probe (feature perf_probe, no ground models in it), the grounds'
# packs beside it in grounds/, serves it with the headers the threaded Web build needs, and plays
# each ground in headless Chromium, reading the page's memory before and after each ground.
#
#   GODOT=/path/to/godot tools/perf/web_memory.sh <out dir> [ground slugs, default marvel,mcg]
# Needs an imported project, the Web export templates and Playwright's Chromium.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
GODOT="${GODOT:-godot}"
OUT="$(mkdir -p "${1:?out dir}" && cd "$1" && pwd)"
GROUNDS="${2:-marvel,mcg}"
rm -rf "$OUT/site" && mkdir -p "$OUT/site/grounds"
GODOT="$GODOT" tools/ground_packs/export.sh web "$OUT/site/grounds" ${GROUNDS//,/ }
cp "$OUT/site/grounds/ground_packs.json" ground_packs.json
cp export_presets.cfg "$OUT/presets.bak"
trap 'cp "$OUT/presets.bak" "$ROOT/export_presets.cfg"; rm -f "$ROOT/ground_packs.json" "$OUT/presets.bak"' EXIT
# The Web preset as it ships, as the probe: its main scene the phone probe, the probe's own
# folder in, the packs' list in.
python3 - "$ROOT/export_presets.cfg" <<'PY'
import re, sys
text = open(sys.argv[1]).read()
blocks = re.split(r"(?m)^(?=\[preset\.\d+(?:\.options)?\]\s*$)", text)
web = None
for i, b in enumerate(blocks):
    if re.match(r'\[preset\.\d+\]', b) and '\nname="Web"\n' in b:
        web = i
head = blocks[web].replace('[preset.%s]' % re.match(r'\[preset\.(\d+)\]', blocks[web]).group(1), '[preset.0]', 1)
opts = blocks[web + 1].replace(re.match(r'\[preset\.\d+\.options\]', blocks[web + 1]).group(0), '[preset.0.options]', 1)
head = re.sub(r'(?m)^name=.*$', 'name="WebProbe"', head)
head = re.sub(r'(?m)^custom_features=.*$', 'custom_features="perf_probe"', head)
head = re.sub(r'(?m)^include_filter="(.*)"$', r'include_filter="\1, ground_packs.json"', head)
head = re.sub(r'(?m)^exclude_filter=.*$', 'exclude_filter="docs/*, tests/*, addons/debug_draw_3d/*, addons/openvat_animated/*, assets/grounds/*, tools/kits/*, tools/legacy_1990s/*, tools/oval3d/*, tools/grounds/*"', head)
open(sys.argv[1], "w").write(head + opts)
PY
"$GODOT" --headless --path "$ROOT" --export-release "WebProbe" "$OUT/site/index.html" > "$OUT/export.log" 2>&1 || { tail -20 "$OUT/export.log"; exit 1; }
ls -la "$OUT/site" | grep -E "pck|wasm"
node "$ROOT/tools/perf/web_memory.js" "$OUT/site" "$GROUNDS" "$OUT"
