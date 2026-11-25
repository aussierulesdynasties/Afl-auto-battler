#!/bin/sh
# Rebuild the People First Stadium model (needs Blender 5.2, or `pip install bpy==5.2.4` and python3 with build_bpy.py).
# MEMB..LOBE_IN reproduce the model the director passed (#1853, #1860) with the MCG-standard details in build.py (r36)
# and the glazed inner band reshaped to Google Earth (r37: BANDR BANDM SAG LOBE_IN).
# r38 (RIBFIT): the roof plan is one fitted construction from ../measure/roof_edge_fit.py (38 measured bays, smooth
# valley and crest curves, smooth inner line) in place of the raw satellite traces, the even ribs (EVEN) and the
# photo's far ribs (FARRIBS FARVR), which the shape audit found up to 7.9 m off.
cd "$(dirname "$0")"
export GEO=geo_n.json SATRIBS=1 RIBFIT=ribfit.json NEARDZ=3 MEMB=0.27 BANDR=1.6 BANDM=6.0 SAG=2.6 LOBE_IN=0.9
if command -v blender >/dev/null; then blender -b -P build.py -- "${1:-out.glb}" "${2:-render.png}"; else python3 build_bpy.py "${1:-out.glb}"; fi
