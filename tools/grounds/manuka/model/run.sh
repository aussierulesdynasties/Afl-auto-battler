#!/bin/sh
# Build the Manuka glb + seat files and proof renders with pip bpy (no Blender install needed):
#   tools/grounds/manuka/model/run.sh OUTDIR [glb] [stills] [close]
PY=${BPY_PYTHON:-python3}
F=$(cd "$(dirname "$0")" && pwd)/proofs.py
OUT=$1; shift
exec "$PY" -c "
import sys;F='$F';sys.argv=['blender','--','$OUT']+'$*'.split()
exec(compile(open(F).read(),F,'exec'),{'__file__':F,'__name__':'__main__'})"
