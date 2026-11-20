echo $$ > runall.pid
set -x
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
"$B" -b --python blend2.py -- final w3 > log_w3.txt 2>&1
"$B" -b --python blend2.py -- final w3t tt > log_w3t.txt 2>&1
python board2.py w3_matched.png whitten_vs_photo.png whitten_parts.png
python crop.py w3_matched.png cW.png 400 120 640 240 3
python crop.py w3_matched.png cE.png 560 140 780 300 3
python crop.py w3_matched.png cN.png 440 380 680 470 3
"$B" -b w3t.blend --python tt.py -- close out apron apron_dirt boundary_fence ejs_coaches_box ejs_north_building ejs_stand ejw_race > log_c1.txt 2>&1
"$B" -b w3t.blend --python tt.py -- close out ejw_stand main_stand north_pole_hut north_scoreboard north_terrace nw_hut nw_shed_1 > log_c2.txt 2>&1
"$B" -b w3t.blend --python tt.py -- close out nw_shed_2 south_bank south_east_block south_huts south_shed west_seats > log_c3.txt 2>&1
"$B" -b w3t.blend --python tt.py -- close out old_stand main_stand_end_block ejs_south_building south_scoreboard > log_c4.txt 2>&1
ls -la --time-style=+%H:%M out/whitten_closeup_*.png
"$B" -b w3t.blend --python tt.py -- stills out > log_st.txt 2>&1
"$B" -b w3.blend --python bake.py -- glb/whitten_exterior_1986.glb > log_glb.txt 2>&1
rm -f out/whitten_exterior_0001-0120.mp4
"$B" -b w3t.blend --python tt.py -- mp4 out > log_mp4.txt 2>&1
ls -la --time-style=+%H:%M out glb
echo ALLDONE
