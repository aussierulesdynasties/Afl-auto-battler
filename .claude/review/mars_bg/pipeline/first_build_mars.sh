cd "D:/Temp/claude/6a5fdc1be2cf0baf/f0b104f0-c447-4a40-a59b-216e29157d33/scratchpad/proto"
while ! grep -q END fetch_mars.log; do sleep 15; done
cat fetch_mars.log
while ! grep -q WATERDONE ../../tasks/bijhalgwc.output 2>/dev/null; do sleep 10; done
C:/Python314/python.exe -E osm_merge.py mars
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
"$B" -b -P probe_outline.py -- ground/mars.glb data/mars/prep/footprint.json 2>&1 | grep OUTLINE
C:/Python314/python.exe -E mk_road_tex.py spec/mars.json && C:/Python314/python.exe -E -P prep.py spec/mars.json 2>&1 | tail -5
C:/Python314/python.exe -E bake_ground.py mars | tail -1
"$B" -b -P scene.py -- spec/mars.json 2>&1 | grep -E "SAVED|Error|built" | grep -v unregister
for j in job_stills job_map; do "$B" -b out/mars/scene.blend -P render.py -- out/mars/$j.json 2>&1 | grep -iE "rendered|Error" | grep -v unregister | tail -2; done; echo BUILDDONE
