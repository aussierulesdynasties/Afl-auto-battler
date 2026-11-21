cd "D:/Temp/claude/be4131086f5178a8/2acaba2f-ab04-4c99-b2ff-bfdb665b1686/scratchpad/proto"; O=out/riverway; B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
C:/Python314/python.exe -E mk_road_tex.py spec/riverway.json && C:/Python314/python.exe -E -P prep.py spec/riverway.json && C:/Python314/python.exe -E bake_ground.py riverway | tail -1 && C:/Python314/python.exe -E water_col.py spec/riverway.json
"$B" -b -P scene.py -- spec/riverway.json 2>&1 | grep -E "SAVED|Error:|built"
for j in ${JOBS:-job_stills job_map job_ortho job_fence_g}; do "$B" -b $O/scene.blend -P render.py -- $O/$j.json 2>&1 | grep -iE "rendered" | tail -1; done; echo DONE
