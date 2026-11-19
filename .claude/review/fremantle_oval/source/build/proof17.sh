set -x
B="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
O=build/proof17; mkdir -p $O
"$B" -b --python build/build.py -- a04 $O/a04.png > build/p17_a04.log 2>&1
"$B" -b --python build/build.py -- close $O > build/p17_close.log 2>&1
"$B" -b --python build/build.py -- photo $O/hq_g18_photocam.png fit/cam_g18.json 1.63 > build/p17_photo.log 2>&1
"$B" -b --python build/build.py -- turn $O > build/p17_turn.log 2>&1
"$B" -b --python build/build.py -- glb $O/fremantle_oval.glb > build/p17_glb.log 2>&1
grep -n 'File ".*build.py", line' build/p17_*.log
ls $O | wc -l
