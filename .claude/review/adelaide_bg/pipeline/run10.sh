cd D:/Temp/claude/b012626c2f559e8f/6855d913-d54b-43b8-92a6-1e4e1b34589b/scratchpad/proto
bash build.sh adelaide > out/adelaide/build10.log 2>&1
cd out/adelaide
for j in job_map job_fence job_street; do "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b scene.blend -P ../../render.py -- $j.json 2>&1 | grep -iE "saved|error|Traceback" | grep -v unregister | tail -3; done
C:/Python314/python.exe -E ../../glbtris.py scene_bg.glb
echo ALLDONE
