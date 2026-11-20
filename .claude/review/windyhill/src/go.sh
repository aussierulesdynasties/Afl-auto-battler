B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"; D="$(cd "$(dirname "$0")" && pwd -W)/"
"$B" -b --python ${D}build.py -- ${D}wh.glb 2>&1 | grep -v unregister | grep -i "ok\|error\|Traceback\|line " 
"$B" -b --python ${D}rcam.py -- ${D}wh.glb ${D}rend.png 2>&1 | grep -i "error\|line " | grep -v unregister
python ${D}cmp.py
"$B" -b --python ${D}orbit.py -- ${D}wh.glb ${D}orb_ 2>&1 | grep -i "error\|line " | grep -v unregister
echo DONE
