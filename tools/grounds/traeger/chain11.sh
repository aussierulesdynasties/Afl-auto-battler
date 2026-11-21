S="C:/Users/DANTE/AppData/Local/Temp/claude/4a2d69a2e2816321/2e119eb6-c1b8-4f9d-a827-983cffaeebc1/scratchpad";cd "$S"
B="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
date +%H:%M:%S
"$B" -b out/r10/traeger.blend --python drop_field.py -- "$S/out/r11" > out/drop11.log 2>&1; echo "drop: $(grep -c SAVED11 out/drop11.log) $(grep -E "DEL|RING" out/drop11.log)"
"$B" -b out/r11/traeger.blend --python aerial.py > out/aerial11.log 2>&1; echo "aerial: $(grep -c 'AERIAL OK' out/aerial11.log)"
"$B" -b out/r11/traeger.blend --python rcam.py -- cam_w04b.json "$S/out/r11/render_w04.png" 1 > out/w04_11.log 2>&1; echo "w04: $(grep -c '^OK' out/w04_11.log)"
"$B" -b out/r11/traeger.blend --python shots.py -- "$S/out/proof11" > out/shots11.log 2>&1; echo "shots OK: $(ls out/proof11/*.png 2>/dev/null | wc -l)"
python proofboard.py "$S/out/r11" "$S/out/proof11"
date +%H:%M:%S
