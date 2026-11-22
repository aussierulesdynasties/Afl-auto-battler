#!/bin/sh
# Rebuild the People First Stadium model (needs Blender 5.2, or `pip install bpy==5.2.4` and python3 with build_bpy.py).
# EVEN..MEMB reproduce the model the director passed (#1853, #1860); r36 adds the MCG-standard details in build.py;
# r37 (BANDR BANDM SAG LOBE_IN) reshapes the glazed inner band to Google Earth: deeper arcs per bay, narrow at the ribs.
cd "$(dirname "$0")"
export GEO=geo_n.json SATRIBS=1 FARRIBS=farribs_A.json FARVR=farvr.json FARDZ=3 LOBE_FAR=2.2 FARPOW=2.5 EVEN=1 NEARDZ=3 MEMB=0.27 BANDR=1.6 BANDM=6.0 SAG=2.6 LOBE_IN=0.9
if command -v blender >/dev/null; then blender -b -P build.py -- "${1:-out.glb}" "${2:-render.png}"; else python3 build_bpy.py "${1:-out.glb}"; fi
