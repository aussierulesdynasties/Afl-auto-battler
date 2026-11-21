cd "D:/Temp/claude/9cde8b3442051ee1/8e9d400c-05c9-4bcc-aeef-038762663b40/scratchpad/proto"; C:/Python314/python.exe -E spec/mk_accor.py && O=out/accor; B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
C:/Python314/python.exe -E mk_road_tex.py spec/accor.json && C:/Python314/python.exe -E mk_accor_pavers.py && C:/Python314/python.exe -E -P prep.py spec/accor.json && C:/Python314/python.exe -E bake_ground.py accor | tail -1 && C:/Python314/python.exe -E tex_facade_atlas.py accor
"$B" -b -P scene.py -- spec/accor.json 2>&1 | grep -E "SAVED|Error:|built|landmark|towers"
for j in ${JOBS:-job_stills job_map job_ortho job_fence_g}; do "$B" -b $O/scene.blend -P render.py -- $O/$j.json 2>&1 | grep -iE "rendered" | tail -1; done; echo DONE
