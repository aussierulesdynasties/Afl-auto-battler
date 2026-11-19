#!/bin/bash
# full rebuild: textures, Blender build and renders, crop boards, region brightness vs p1
cd "$(dirname "$0")"
python tex.py >/dev/null && python mktex.py >/dev/null && python texdetail.py || { echo TEX FAIL; exit 1; }
D=$(cygpath -m "$PWD"); "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --python build.py -- "$D" "$D/gmhba.glb" "$D/ren.png" > build.log 2>&1
grep -A3 "build.py\", line" build.log && { echo BUILD FAIL; exit 1; }
ls -l --time-style=+%H:%M:%S ren.png
python crops.py crop_pocket.png 820 270 1000 420 6; python crops.py crop_north.png 230 250 560 380 4; python crops.py crop_wedge.png 180 420 470 600 4; python crops.py crop_annex.png 60 440 300 580 4
python -c "
from PIL import Image
import numpy as np
ph=np.array(Image.open('photo.jpg').convert('RGB')).astype(int);r=np.array(Image.open('ren.png').convert('RGB')).astype(int)
for n,b in [('north lower',(300,305,420,340)),('north upper',(300,275,420,290)),('far stand',(600,300,800,330)),('pocket',(850,372,930,392)),('pitch',(500,360,700,390)),('prem front',(450,470,680,540)),('box front',(300,455,370,475)),('roof',(450,410,700,440))]:
  x0,y0,x1,y1=b;print(n,ph[y0:y1,x0:x1].reshape(-1,3).mean(0).round(),r[y0:y1,x0:x1].reshape(-1,3).mean(0).round())
"
