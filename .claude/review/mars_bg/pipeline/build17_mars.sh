cd "D:/Temp/claude/6a5fdc1be2cf0baf/f0b104f0-c447-4a40-a59b-216e29157d33/scratchpad/proto"
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
P=C:/Python314/python.exe
"$B" -b -P probe_outline.py -- ground/mars.glb data/mars/prep/footprint.json 2>&1 | grep OUTLINE
$P -E -P prep.py spec/mars.json 2>&1 | grep -iE "msbf|split|cycle|rror"
$P -E bake_ground.py mars 2>&1 | tail -1
$P -E bake_ground.py mars 8192 390 2>&1 | grep -E "track|rror"
bash build16_mars.sh
