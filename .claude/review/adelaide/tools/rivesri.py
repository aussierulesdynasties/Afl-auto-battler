import sys, os, json, numpy as np
sys.path.insert(0, 'tools'); from esri import m2px
from PIL import Image, ImageDraw
_argv=sys.argv; sys.argv=['gen.py']
src=open('tools/gen.py').read().split('# ---------------------------------------------------------------- build')[0]
__file__=os.path.abspath('tools/gen.py'); exec(src); sys.argv=_argv
im=Image.open('esri/mosaic.jpg').convert('RGB'); d=ImageDraw.Draw(im)
q=json.load(open('fit_river.json'))['q']
for nm,col in (('river',(255,0,0)),('east',(0,255,0)),('west',(0,128,255))):
    rf={r['name']:r for r in SPEC['roofs']}[nm]; P=way(rf['way'])
    pts=[m2px(*p) for p in P]; d.line(pts+[pts[0]],fill=col,width=2)
    # lean-corrected at roof height ~ hb (tops move +0.82 px/m E, +0.26 px/m S)
    h=(rf['hf']+rf['hb'])/2; pts2=[(a+0.82*h,b+0.26*h) for a,b in pts]; d.line(pts2+[pts2[0]],fill=(255,0,255),width=1)
    if nm=='river':
        cen=P[:-1].mean(0); P2=(P-cen)*q[2]+cen+[q[0],q[1]]
        pts3=[m2px(*p) for p in P2]; pts3=[(a+0.82*h,b+0.26*h) for a,b in pts3]; d.line(pts3+[pts3[0]],fill=(255,255,0),width=2)
xs=[];ys=[]
rf={r['name']:r for r in SPEC['roofs']}['river']; P=way(rf['way']); pp=np.array([m2px(*p) for p in P])
x0,y0=pp.min(0)-120; x1,y1=pp.max(0)+120
im.crop((int(x0),int(y0),int(x1),int(y1))).save('grid/river_esri.jpg'); print(x0,y0,x1,y1)
