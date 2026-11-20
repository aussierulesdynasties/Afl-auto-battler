# proof.sh: renders the whole gate set into rend/ (A/B/C matches, turntable, Hill c09/c11, Hill close-ups, joins, facades, top-down)
D=$(pwd -W); B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"; R(){ "$B" -b -P tools/render.py -- "$@" > rend/proof.log 2>&1; }
mkdir -p rend/p rend/j rend/top
R match "$D/rend/A_fix.png"
CAM=camB.json R match "$D/rend/B_fix.png"
CAM=camC14.json SUN_AZ=330 SUN_EL=35 R match "$D/rend/C_fix.png"
RW=1920 RH=1080 R turn "$D/rend/turn4" 4 30 420
CAM=camH09.json R match "$D/rend/p/h09.png"
CAM=camH11b.json R match "$D/rend/p/h11.png"
RW=1920 RH=1080 POS=28,62,14 TGT=22,118,7 SUN_AZ=150 SUN_EL=40 R orbit "$D/rend/p/hill_close.png" 0 0 0
RW=1920 RH=1080 POS=80,40,60 TGT=10,118,4 SUN_AZ=150 SUN_EL=40 R orbit "$D/rend/p/hill_above.png" 0 0 0
RW=1920 RH=1080 POS=185,10,12 TGT=130,10,12 R orbit "$D/rend/p/closeup_hotel_facade.png" 0 0 0
RW=1920 RH=1080 POS=-170,-20,8 TGT=-120,-20,7 R orbit "$D/rend/p/closeup_west_brick_facade.png" 0 0 0
bash tools/joins.sh rend/j
TOP=0,-10,400 TRES=1600 SUN_EL=60 LEAN=0.2008,-0.0637 R top "$D/rend/top/topL.png"
TOP=0,-10,400 python tools/topdown.py rend/top/topL.png rend/top/ovlL.png
echo ALLDONE > rend/p/done.txt
