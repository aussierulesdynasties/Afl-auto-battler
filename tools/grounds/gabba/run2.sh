set -e
cd "$(dirname "$0")"
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P build.py -- $1 gabba.glb "$PWD/gabba.blend" "$PWD/htex" 2>&1 | grep -E "TRIS|Error" || true
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b "$PWD/gabba.blend" -P render.py -- camB.json "$PWD/r.png" 2>&1 | grep -E "Error" || true
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b "$PWD/gabba.blend" -P render.py -- camB.json "$PWD/m.png" mask 2>&1 | grep -E "Error" || true
python compose.py go r.png m.png $2
