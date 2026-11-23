import json,subprocess,sys
from PIL import Image,ImageDraw
C={'P1':(-126.33,25.14),'P2':(-110.36,18.33),'P3':(-106.86,-77.44),'P4':(-99.17,-73.17),'P5':(6.7,-134.39),'P6':(7.94,-142.19)}
S=json.load(open('pave.json'));ppm=8;H=20
for n,(mx,my) in C.items():
  cx,cy=mx+9,my+22;x0,x1,y0,y1=cx-H,cx+H,cy-H,cy+H
  out=f'cc_{n}.png'
  subprocess.run([sys.executable,'../w/wbcrop_ng.py',str(x0),str(x1),str(y0),str(y1),str(ppm),out],check=True)
  ppm2=ppm*2;im=Image.open(out).convert('RGB');d=ImageDraw.Draw(im)
  P=lambda x,y:((x-x0)*ppm2,(y1-y)*ppm2)
  for a,b,c,e,m in S:
    d.line([P(a+9,b+22),P(c+9,e+22)],fill=(0,255,255),width=1)
  px,py=P(cx,cy);d.ellipse([px-4,py-4,px+4,py+4],outline=(255,0,0),width=2)
  for t in range(0,2*H+1,5):
    d.line([(t*ppm2,0),(t*ppm2,8)],fill=(255,255,0));d.line([(0,t*ppm2),(8,t*ppm2)],fill=(255,255,0))
  im.save(out);print(n,im.size)
