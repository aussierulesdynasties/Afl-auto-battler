#!/bin/sh
# Build C6, render its lean-matched top-down, and overlay it on the 2018-10 image (old frame).
cd /c/Users/DANTE/AppData/Local/Temp/claude/cec579e0cf1e721a/27ab9b53-76bc-414a-b98e-5c4e22e13159/scratchpad/sub
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"; SP=$(pwd -W)
TD=/d/Temp/claude/b6b84c744aa9573f/2803de85-c3b2-4949-965c-641fb38c8ee9/scratchpad/td
python mkC6.py > /dev/null
"$B" -b --python buildC6.py -- "$SP" "$SP/subC6.glb" "$SP/renC6.png" > logC6.txt 2>&1 || { tail -20 logC6.txt; exit 1; }
grep -i "error\|traceback" logC6.txt | head -5
"$B" -b --python $TD/topdown.py -- "$SP/subC6.glb" "$(cygpath -w $TD)/topC6o.png" 0.45 14.42 0.2532 1600 0.353 0.098 > logtd.txt 2>&1
cd $TD && python ovl.py topC6o.png 0.45 14.42 e18820_T.png ovC6o.png 640 380 1860 1610 > /dev/null && python -c "
from PIL import Image
I=Image.open('ovC6o.png');w,h=I.size;t=(h-60)//3
I.crop((0,2*(t+20)+20,w,2*(t+20)+20+t)).save('ovC6o_line.png');I.crop((0,(t+20)+20,w,(t+20)+20+t)).save('ovC6o_half.png')"
echo done
