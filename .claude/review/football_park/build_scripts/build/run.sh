# bash run.sh SPEC TAG CAM W H  -> fp<TAG>.glb, r<TAG>.png
cd "$(dirname "$0")"; s=$(date +%s)
FAST=${FAST-1} "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --factory-startup -b --python build.py -- $1 fp$2.glb $3 r$2.png $4 $5 > log$2.txt 2>&1
grep -iE "^Error|Traceback|File \"" log$2.txt | head; echo "took $(( $(date +%s)-s ))s"
