#!/bin/bash
# full rebuild: textures -> mesh -> glb + reference render -> board + Messenger crop
cd "$(dirname "$0")";S=$(pwd -W);B="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
python texgen.py >/dev/null && python export2.py 2>&1 | tail -1 && \
"$B" -b --python build_hand.py -- "$S" "$S/out/scg.glb" "$S/out/r0.png" cam.json > g/bl.log 2>&1; grep "DONE" g/bl.log
python board.py refs/scg.jpg out/r0.png g/board0.png "L:0,0,600,675" "R:600,0,1200,675"
python crop2.py ${1:-140,130,440,390} g/mes1.png
