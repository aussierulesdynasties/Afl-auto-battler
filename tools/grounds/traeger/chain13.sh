S="C:/Users/DANTE/AppData/Local/Temp/claude/4a2d69a2e2816321/2e119eb6-c1b8-4f9d-a827-983cffaeebc1/scratchpad";cd "$S"
B="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
date +%H:%M:%S
python stand.py > out/st13.log 2>&1 && python standuv.py >> out/st13.log 2>&1 && python club.py >> out/st13.log 2>&1 && python model.py >> out/st13.log 2>&1; echo "py: $?"
"$B" -b --python blend.py -- prims.json cam.json "$S/out/r13a" > out/build13.log 2>&1; echo "build: $?"
"$B" -b out/r13a/traeger.blend --python drop_field.py -- "$S/out/r13" > out/drop13.log 2>&1; echo "drop: $(grep -c SAVED11 out/drop13.log) $(grep -E "DEL|RING" out/drop13.log)"
"$B" -b out/r13/traeger.blend --python aerial.py > out/aerial13.log 2>&1; echo "aerial: $(grep -c 'AERIAL OK' out/aerial13.log)"
"$B" -b out/r13/traeger.blend --python rcam.py -- cam_w04s.json "$S/out/r13/render_w04.png" 1 > out/w04_13.log 2>&1; echo "w04: $(grep -c '^OK' out/w04_13.log)"
"$B" -b out/r13/traeger.blend --python rcam.py -- cam_c06s.json "$S/out/r13/render_c06.png" 1 > out/c06_13.log 2>&1; echo "c06: $(grep -c '^OK' out/c06_13.log)"
"$B" -b out/r13/traeger.blend --python shots.py -- "$S/out/proof13" > out/shots13.log 2>&1; echo "shots OK: $(ls out/proof13/*.png 2>/dev/null | wc -l)"
date +%H:%M:%S
"$B" -b out/r13/traeger.blend --python topdown.py -- "$S/out/r13/top_model.png" -100 -100 95 112 4 > out/top13.log 2>&1; echo "top: $(grep "TOP OK" out/top13.log)"
"$B" -b out/r13/traeger.blend --python topdown.py -- "$S/out/r13/top_model20.png" -100 -40 -40 40 8 >> out/top13.log 2>&1; echo "top20: $(grep -c "TOP OK" out/top13.log)"
