set -e
G=/c/Users/DANTE/Desktop/Godot_v4.7.2-stable_win64.exe/Godot_v4.7.2-stable_win64_console.exe
R=/c/kt/bruce1990/.claude/review/bruce; mkdir -p $R
rm -rf tt96 cf cs ct cx; mkdir -p tt96 cf cs ct cx
read e1 t1 < g/eye.txt; read e2 t2 < g/eye_t.txt
GPU_SLOT_OWNER=bruce-tt bash /c/kt/gpu_slot.sh $G --path tt -s turntable.gd -- "$PWD/bruce3.glb" "$PWD/tt96" 96 22 1.0
GPU_SLOT_OWNER=bruce-tt bash /c/kt/gpu_slot.sh $G --path tt -s turntable.gd -- "$PWD/bruce3.glb" "$PWD/cf" 1 22 1.0 "-95,128,22" "-50,95,4"
GPU_SLOT_OWNER=bruce-tt bash /c/kt/gpu_slot.sh $G --path tt -s turntable.gd -- "$PWD/bruce3.glb" "$PWD/cs" 1 22 1.0 "$e1" "$t1"
GPU_SLOT_OWNER=bruce-tt bash /c/kt/gpu_slot.sh $G --path tt -s turntable.gd -- "$PWD/bruce3.glb" "$PWD/ct" 1 22 1.0 "$e2" "$t2"
# extra close-ups (eye; target): SE seats, both bowl/stand joins, S grass bank, E bank + rim, SW seats
i=0; while read e t n; do mkdir -p cx/$n; GPU_SLOT_OWNER=bruce-tt bash /c/kt/gpu_slot.sh $G --path tt -s turntable.gd -- "$PWD/bruce3.glb" "$PWD/cx/$n" 1 22 1.0 "$e" "$t"; done < g/cx.txt
FF=C:/Users/DANTE/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe
"$FF" -y -loglevel error -framerate 24 -i tt96/f%03d.png -c:v libx264 -pix_fmt yuv420p -crf 18 bruce_exterior.mp4
cp bruce_exterior.mp4 $R/; cp pf/bruce_vs_photo*.png $R/
for d in cx/*; do cp $d/f000.png $R/bruce_close_$(basename $d).png; done
for f in pf/board_*.png; do cp $f $R/bruce_$(basename $f); done
for n in 000 024 048 072; do cp tt96/f$n.png $R/bruce_still_$n.png; done
cp cf/f000.png $R/bruce_facade_closeup.png; cp cs/f000.png $R/bruce_stairs_closeup.png; cp ct/f000.png $R/bruce_turnstiles_closeup.png
echo DONE
