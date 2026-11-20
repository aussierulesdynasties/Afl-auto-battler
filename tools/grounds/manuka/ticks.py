import numpy as np, math, io, contextlib, sys
with contextlib.redirect_stdout(io.StringIO()):
    import model as M
import cam
from PIL import Image, ImageDraw
# tier: angle range, profile line (d,z) start/end; draw ticks every 1 deg across the tier, labels every 2 deg
TIERS={'n':(48,154,[(-1.5,1.1),(16,8.0)]),'w':(150,240,[(0.3,1.1),(20,8.0)])}
k=sys.argv[1];t0,t1,(p0,p1)=TIERS[k];x0,y0,x1,y1=map(int,sys.argv[2:6]);sc=int(sys.argv[6])
im=Image.open('photo.png').convert('RGB').crop((x0,y0,x1,y1));im=im.resize((im.width*sc,im.height*sc),Image.LANCZOS);d=ImageDraw.Draw(im)
for t in range(t0,t1+1):
    a=math.radians(t)
    A=cam.proj([M.P(a,p0[0],p0[1])])[0];B=cam.proj([M.P(a,p1[0],p1[1])])[0]
    q=lambda p:((p[0]-x0)*sc,(p[1]-y0)*sc)
    d.line([q(A),q(B)],fill=(255,0,255) if t%2==0 else (255,255,0),width=1)
    if t%2==0:d.text(q(B),str(t),fill=(255,255,255))
im.save(f'z/tick_{k}.png')
