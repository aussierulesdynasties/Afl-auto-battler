B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"; D="C:/Users/DANTE/AppData/Local/Temp/claude/b11ecf2cca45cfb5/002c0964-89cd-46e5-bf30-bd32e1451dbd/scratchpad/wh/"
for m in trim fill; do
 WH_APRON=$m "$B" -b --python ${D}build.py -- ${D}v_$m.glb 2>&1 | grep -i "BUILD\|Error:" | grep -v unregister
 "$B" -b --python ${D}rcam.py -- ${D}v_$m.glb ${D}v_$m.png 2>&1 | grep -i "Error:" | grep -v unregister
done; echo VDONE
