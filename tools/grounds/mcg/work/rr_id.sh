set -e
cd D:/Temp/claude/c705dfb168facc8f/874a7c40-ffe1-4e7f-a2d3-504f6380309b/scratchpad
bash work/rr_all.sh
V=$(ls rf/id16 | sed 's/.png//' | tr '\n' ' ')
FLAT=2 "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --python model/rv.py -- "$(pwd -W)/rf/id16" $V > work/id16_log.txt 2>&1
echo IDDONE
