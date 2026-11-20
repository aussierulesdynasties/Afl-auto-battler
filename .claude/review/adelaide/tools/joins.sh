# close-ups of the three joins the gate failed, from the board's angles (turntable frames 0, 2, 3)
D=$(pwd -W); B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
r(){ POS=$1 TGT=$2 SUN_AZ=$4 SUN_EL=40 RW=1600 RH=900 "$B" -b -P tools/render.py -- orbit "$D/$3.png" 0 0 0 > rend/j.log 2>&1; }
r -60,170,110 70,40,22 ${1:-grid}/join_west 150
r 160,-230,95 20,-115,35 ${1:-grid}/join_river 150
r 210,150,95 95,30,20 ${1:-grid}/join_east 150
