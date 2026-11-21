cd "D:/Temp/claude/6a5fdc1be2cf0baf/f0b104f0-c447-4a40-a59b-216e29157d33/scratchpad/proto"
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
C:/Python314/python.exe -E -P prep.py spec/mars.json 2>&1 | tail -6
C:/Python314/python.exe -E bake_ground.py mars | tail -1
C:/Python314/python.exe -E bake_ground.py mars 8192 390 | tail -1
"$B" -b -P scene.py -- spec/mars.json 2>&1 | grep -E "SAVED|Error|built|Traceback" | grep -v unregister
for j in job_stills job_map; do "$B" -b out/mars/scene.blend -P render.py -- out/mars/$j.json 2>&1 | grep -iE "rendered|Error" | grep -v unregister | tail -2; done; echo BUILDDONE
