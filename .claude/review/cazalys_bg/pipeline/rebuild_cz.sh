cd "D:/Temp/claude/bc8b0dd212458270/fd779ef0-41a7-4714-ad51-5cba401d7797/scratchpad/proto"; O=out/cazalys; B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
if [ -z "$SKIP_PREP" ]; then C:/Python314/python.exe -E mk_road_tex.py spec/cazalys.json && C:/Python314/python.exe -E -P prep.py spec/cazalys.json && C:/Python314/python.exe -E aerial_paving.py cazalys && C:/Python314/python.exe -E bake_ground.py cazalys | tail -1 && C:/Python314/python.exe -E post_ground.py cazalys; fi; C:/Python314/python.exe -E landclass.py cazalys
"$B" -b -P scene.py -- spec/cazalys.json 2>&1 | grep -E "SAVED|Error:|built|NO GROUND"
for j in ${JOBS:-job_stills job_map job_ortho job_fence_g}; do "$B" -b $O/scene.blend -P render.py -- $O/$j.json 2>&1 | grep -iE "rendered" | tail -1; done; echo DONE
