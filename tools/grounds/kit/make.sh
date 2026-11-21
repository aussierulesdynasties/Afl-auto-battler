#!/usr/bin/env bash
# Build one ground end to end: textures, GLB + seat files into tools/grounds/<slug>/model/, proof renders, review boards
# into .claude/review/<slug>/.  tools/grounds/kit/make.sh <slug> [jobs...]   (BLENDER = path to Blender 5.2)
# Default jobs: glb ship stills top seats low orbit. Renders go to tools/grounds/<slug>/render (git-ignored).
set -euo pipefail
cd "$(dirname "$0")/../../.."
SLUG=$1; shift; JOBS=${*:-glb ship stills top seats low orbit}
export GROUND=tools/grounds/$SLUG; BLENDER=${BLENDER:-blender}; R=$GROUND/render
python3 tools/grounds/kit/paint.py "$GROUND"
"$BLENDER" -b --python tools/grounds/kit/proofs.py -- "$R" $JOBS > "$R.log" 2>&1 || { tail -40 "$R.log"; exit 1; }
grep -E "seats instanced|seat mean" "$R.log" || true
if [[ " $JOBS " == *" glb "* ]]; then rm -f "$GROUND"/model/seats_*.bin; cp "$R/$SLUG.glb" "$R"/seat_tmpl.bin "$GROUND/model/"
  for f in "$R"/seats_*.bin; do [[ -e $f ]] && cp "$f" "$GROUND/model/"; done; fi
python3 tools/grounds/kit/boards.py "$GROUND" "$R" ".claude/review/$SLUG"
