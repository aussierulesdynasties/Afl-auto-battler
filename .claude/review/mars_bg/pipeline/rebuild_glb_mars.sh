cd "D:/Temp/claude/6a5fdc1be2cf0baf/f0b104f0-c447-4a40-a59b-216e29157d33/scratchpad/proto"
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
"$B" -b -P probe_outline.py -- ground/mars.glb data/mars/prep/footprint.json 2>&1 | grep OUTLINE
bash build2_mars.sh
bash video_mars.sh
