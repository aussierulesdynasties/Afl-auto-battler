set -x
B="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"; G="bash C:/kt/gpu_slot.sh"; export GPU_SLOT_OWNER=fremantle
O=build/proof20; mkdir -p $O
$G "$B" -b --python build/build.py -- close $O > build/p20b_close.log 2>&1
$G "$B" -b --python build/build.py -- a04 $O/a04.png > build/p20b_a04.log 2>&1
$G "$B" -b --python build/build.py -- photos $O/g34h.png fit/cam_g34g.json 0 > build/p20b_g34.log 2>&1
$G "$B" -b --python build/build.py -- photos $O/a02s0.png fit/cam_a02s0.json 0 $O/g18h.png fit/cam_g18h.json 0 > build/p20b_photos.log 2>&1
$G "$B" -b --python build/build.py -- top $O/top.png -135 -135 115 140 4 > build/p20b_top.log 2>&1
$G "$B" -b --python build/build.py -- turn $O > build/p20b_turn.log 2>&1
$G "$B" -b --python build/build.py -- glb $O/fremantle_oval.glb > build/p20b_glb.log 2>&1
grep -n 'File ".*build.py", line' build/p20b_*.log
ls $O | wc -l
