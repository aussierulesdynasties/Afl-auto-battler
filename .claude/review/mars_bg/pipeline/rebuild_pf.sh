cd "D:/Temp/claude/6a5fdc1be2cf0baf/f0b104f0-c447-4a40-a59b-216e29157d33/scratchpad/proto"; O=out/peoplefirst; B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
C:/Python314/python.exe -E mk_road_tex.py spec/peoplefirst.json && C:/Python314/python.exe -E -P prep.py spec/peoplefirst.json && C:/Python314/python.exe -E bake_ground.py peoplefirst | tail -1
"$B" -b -P scene.py -- spec/peoplefirst.json 2>&1 | grep -E "SAVED|Error:|built"
for j in ${JOBS:-job_stills job_map job_ortho job_fence_g}; do "$B" -b $O/scene.blend -P render.py -- $O/$j.json 2>&1 | grep -iE "rendered" | tail -1; done; echo DONE
