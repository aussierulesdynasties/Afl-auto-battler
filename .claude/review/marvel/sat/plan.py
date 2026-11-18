# Resample the satellite into the local frame (s down = south, t: west to the LEFT? keep map: x=-t... ) with a labelled 10 m grid.
import sys,os,math,json,numpy as np
HERE=os.path.dirname(os.path.abspath(sys.argv[0]));SV=os.path.join(HERE,'..','sv');__file__=os.path.join(SV,'sv.py')
exec(open(os.path.join(SV,'sv.py'),encoding='utf-8').read().split('if __name__')[0])
from PIL import Image,ImageDraw
Z,X0,Y0=map(int,open(os.path.join(HERE,'sat_z19.txt')).read().split())
A=np.asarray(Image.open(os.path.join(HERE,'sat_z19.jpg')).convert('RGB'))
def px(la,lo):
    n=2**Z;x=(lo+180)/360*n;y=(1-np.arcsinh(np.tan(np.radians(la)))/np.pi)/2*n;return (x-X0)*256,(y-Y0)*256
# output: north up, east right, 0.2 m/px, centred on local (0,0); rows = world y, cols = world x
M=0.2;H=int(sys.argv[1]) if len(sys.argv)>1 else 220
g=np.arange(-H,H,M);xx,yy=np.meshgrid(g,-g)
c0=wld(0,0)[:2];la=LA0+(yy+c0[1])/KL;lo=LO0+(xx+c0[0])/KC
u,v=px(la,lo);u=np.clip(u.astype(int),0,A.shape[1]-1);v=np.clip(v.astype(int),0,A.shape[0]-1)
im=Image.fromarray(A[v,u]);dr=ImageDraw.Draw(im)
# local grid lines (s,t) every 10 m
def topx(s,t):w=wld(s,t)[:2]-c0;return ((w[0]+H)/M,(H-w[1])/M)
for k in range(-200,201,10):
    col=(255,255,0) if k%50==0 else (255,255,0,90)
    dr.line([topx(k,-200),topx(k,200)],fill=(255,230,0) if k%50==0 else (200,200,0),width=2 if k%50==0 else 1)
    dr.line([topx(-200,k),topx(200,k)],fill=(0,230,255) if k%50==0 else (0,170,200),width=2 if k%50==0 else 1)
    if k%50==0:
        for j in range(-200,201,50):dr.text(topx(k,j),'s%d t%d'%(k,j),fill='white')
im.save(os.path.join(HERE,'plan_loc.jpg'),quality=92);print(im.size)
