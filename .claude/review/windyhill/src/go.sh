B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"; D="C:/Users/DANTE/AppData/Local/Temp/claude/b11ecf2cca45cfb5/002c0964-89cd-46e5-bf30-bd32e1451dbd/scratchpad/wh/"
"$B" -b --python ${D}build.py -- ${D}wh.glb 2>&1 | grep -v unregister | grep -i "ok\|error\|Traceback\|line " 
"$B" -b --python ${D}rcam.py -- ${D}wh.glb ${D}rend.png 2>&1 | grep -i "error\|line " | grep -v unregister
python ${D}cmp.py
"$B" -b --python ${D}orbit.py -- ${D}wh.glb ${D}orb_ 2>&1 | grep -i "error\|line " | grep -v unregister
echo DONE
