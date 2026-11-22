cd "D:/Temp/claude/534e6ed5702e321f/e26221bc-b0d7-453b-b6bd-aa7897b49bd3/scratchpad/proto"
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
"$B" -b -P scene.py -- spec/marvel.json 2>&1 | grep -E "SAVED|Error:"
for j in map ortho tex fence_g fence2_g fence3_g fence4_g p3_w p4_w p5_w stills; do "$B" -b out/marvel/scene.blend -P render.py -- out/marvel/job_$j.json 2>&1 | grep -cE "RENDERED|Saved" | sed "s/^/$j /"; done
python photo_board.py out/marvel/photo_overlay/photo_overlay_sheet.jpg
bash video_marvel.sh 2>&1 | tail -2
echo FINAL_DONE
