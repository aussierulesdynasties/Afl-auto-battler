cd "D:/Temp/claude/6a5fdc1be2cf0baf/f0b104f0-c447-4a40-a59b-216e29157d33/scratchpad/proto"
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
md5sum ground/mars.glb
"$B" -b -P scene.py -- spec/mars.json 2>&1 | grep -E "park bays|SAVED|Error|built|Traceback" | grep -v unregister
bash video_mars.sh
"$B" -b out/mars/scene.blend -P render.py -- out/mars/job_ortho.json 2>&1 | grep -E "RENDERED|rror" | grep -v unregister | tail -1
echo EXIT $?
