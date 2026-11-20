# Local-frame plan: rows = s (south down), cols = -t (west left). M m/px. Grid every 10 m, labels every 20 m.
import sys,os,math,json,numpy as np
HERE=os.path.dirname(os.path.abspath(sys.argv[0]));SV=os.path.join(HERE,'..','sv');__file__=os.path.join(SV,'sv.py')
exec(open(os.path.join(SV,'sv.py'),encoding='utf-8').read().split('if __name__')[0])
from PIL import Image,ImageDraw
Z,X0,Y0=map(int,open(os.path.join(HERE,'esri_z19.txt')).read().split())
A=np.asarray(Image.open(os.path.join(HERE,'esri_z19.jpg')).convert('RGB'))
def px(la,lo):
    n=2**Z;x=(lo+180)/360*n;y=(1-np.arcsinh(np.tan(np.radians(la)))/np.pi)/2*n;return (x-X0)*256,(y-Y0)*256
s0,s1,t0,t1,M=[float(a) for a in sys.argv[1:6]];out=sys.argv[6]
ss=np.arange(s0,s1,M);tt=np.arange(t1,t0,-M)    # cols: t from t1 (west, left) down to t0
S,T=np.meshgrid(ss,tt,indexing='ij')
c=np.array(c_ if False else wld(0,0)[:2]);Dv=wld(1,0)[:2]-c;Nv=wld(0,1)[:2]-c
X=c[0]+S*Dv[0]+T*Nv[0];Y=c[1]+S*Dv[1]+T*Nv[1]
la=LA0+Y/KL;lo=LO0+X/KC;u,v=px(la,lo)
from scipy.ndimage import map_coordinates
im=np.stack([map_coordinates(A[...,k].astype(float),[v,u],order=1) for k in range(3)],-1).astype(np.uint8)
im=Image.fromarray(im);im.save(out.replace(".jpg","_clean.png"));dr=ImageDraw.Draw(im)
for k in range(-300,301,10):
    if s0<=k<=s1:y=(k-s0)/M;dr.line([(0,y),(im.width,y)],fill=(255,220,0) if k%50==0 else (150,140,0),width=1)
    if t0<=k<=t1:x=(t1-k)/M;dr.line([(x,0),(x,im.height)],fill=(0,220,255) if k%50==0 else (0,130,160),width=1)
for a in range(-300,301,20):
    for b in range(-300,301,20):
        if s0<=a<=s1 and t0<=b<=t1:dr.text(((t1-b)/M+2,(a-s0)/M+1),'%d,%d'%(a,b),fill=(255,255,255))
im.save(out,quality=92);print(im.size)
