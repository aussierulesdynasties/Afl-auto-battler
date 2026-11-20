#!/usr/bin/env bash
# rebuild both models and every proof after the join fixes
set -e; cd "$(dirname "$0")"; export FAST=0
TEXDIR=$PWD/tex_A bash run.sh spec_A.py AT ../a/camA.json 407 612
TEXDIR=$PWD/tex_B bash run.sh spec_B.py BT ../b/camB.json 1300 956
python vs.py ../dl/comp_A1K6CR.jpg rBT.png vsBT.png 956; python vs.py ../dl/g1997_612.jpg rAT.png vsAT.png 1224
TEXDIR=$PWD/tex_B BORDER=0.03,0.39,0.37,0.69 PCT=500 bash run.sh spec_B.py BZ ../b/camB.json 1300 956
TEXDIR=$PWD/tex_A PCT=400 bash run.sh spec_A.py AZ ../a/camA.json 407 612
python bz.py rBZ.png ../dl/comp_A1K6CR.jpg 1300 956 0.03 0.39 0.37 0.69 bdBZ.png; python bz.py rAZ.png ../dl/g1997_612.jpg 407 612 0 0 1 1 bdAZ.png
for V in A B; do TEXDIR=$PWD/tex_$V bash run.sh spec_$V.py ${V}S shots$V.json 1600 1000; TEXDIR=$PWD/tex_$V bash run.sh spec_$V.py ${V}C shots${V}_close.json 1600 1000; done
python - <<'PY'
from PIL import Image
for V in 'AB':
    bd=Image.new('RGBA',(3200,2000),(58,60,66,255))
    for k in range(4):bd.alpha_composite(Image.open(f'tt{V}_{k}.png').convert('RGBA'),((k%2)*1600,(k//2)*1000))
    bd.convert('RGB').save(f'tt{V}_board.png')
    for n in ([f'close{V}']+(['closeB_nw'] if V=='B' else [])):
        c=Image.open(n+'.png').convert('RGBA');b=Image.new('RGBA',c.size,(150,170,190,255));b.alpha_composite(c);b.convert('RGB').save(n+'_bg.png')
print('boards ok')
PY
echo PROOFS DONE
