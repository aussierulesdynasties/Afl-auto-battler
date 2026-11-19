# surface close-ups for the texture pass: each surface type far (game camera distance) and near
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"; D=$(pwd -W); mkdir -p rend/s
R() { "$B" -b -P tools/render.py -- "$@" > /dev/null 2>&1; }
o() { RW=1280 RH=720 POS=$2 TGT=$3 SUN_AZ=${4:-250} SUN_EL=35 R orbit "$D/rend/s/$1.png" 0 0 0; }
o seats_far 0,-20,22 -90,-20,18
o seats_near -50,-20,20 -80,-20,16
o membrane_far 40,10,70 95,10,35 150
o membrane_near 82,10,47 96,10,36 150
o concrete_far -185,-60,14 -125,-60,10 200
o concrete_near -142,-60,7 -126,-60,8 200
o steel_far 0,-30,8 -70,-30,22
o steel_near -45,-30,12 -60,-30,20
o hill_far 28,62,14 22,118,7 150
o hill_near 2,92,5 4,112,1 150
o board_far 22,70,9 22,118,11 150
o board_near 22,100,10 22,118,11 150
echo done > rend/s/done.txt
