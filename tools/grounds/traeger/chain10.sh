S="C:/Users/DANTE/AppData/Local/Temp/claude/4a2d69a2e2816321/2e119eb6-c1b8-4f9d-a827-983cffaeebc1/scratchpad";cd "$S"
B="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
date +%H:%M:%S
"$B" -b out/r9/traeger.blend --python drop_es.py -- "$S/out/r10" > out/drop10.log 2>&1; echo "drop: $(grep -c SAVED10 out/drop10.log) $(grep DEL out/drop10.log)"
"$B" -b out/r10/traeger.blend --python aerial.py > out/aerial10.log 2>&1; echo "aerial: $(grep -c 'AERIAL OK' out/aerial9.log)"
"$B" -b out/r10/traeger.blend --python rcam.py -- cam_w04b.json "$S/out/r10/render_w04.png" 1 > out/w04_10.log 2>&1; echo "w04: $(grep -c '^OK' out/w04_9.log)"
"$B" -b out/r10/traeger.blend --python shots.py -- "$S/out/proof10" > out/shots10.log 2>&1; echo "shots OK: $(ls out/proof10/*.png 2>/dev/null | wc -l)"
python proofboard.py "$S/out/r10" "$S/out/proof10"
date +%H:%M:%S
