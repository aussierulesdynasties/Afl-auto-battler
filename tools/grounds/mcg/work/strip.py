import sys,numpy as np;sys.path.insert(0,'work');import tri
from PIL import Image,ImageDraw
def projv(c,X):
    d=X-c['C'];z=d@c['fwd'];return np.stack([c['W']/2+c['f']*(d@c['right'])/z,c['H']/2-c['f']*(d@c['up'])/z],-1)
def strip(v,z,b0,b1,r0,r1,out,k=6):
    c=tri.camv(v);im=np.asarray(Image.open(f'ge/{v}.png').convert('RGB'))
    R=np.arange(r0,r1,0.25);B=np.arange(b0,b1,1.0);a=np.radians(B)[:,None]
    X=np.stack([R[None]*np.sin(a),R[None]*np.cos(a),np.full((len(B),len(R)),z)],-1);P=projv(c,X)
    u=np.clip(P[...,0].round().astype(int),0,1919);w=np.clip(P[...,1].round().astype(int),0,1079)
    S=im[w,u];I=Image.fromarray(S).resize((len(R)*3,len(B)*k),Image.NEAREST);d=ImageDraw.Draw(I)
    for r in range(int(r0),int(r1)+1,2):
        x=(r-r0)*12;d.line([x,0,x,I.height],fill=(255,0,255) if r%10==0 else (120,0,120));
        if r%10==0:d.text((x+2,2),str(r),fill=(255,255,0))
    for b in range(int(b0),int(b1),5):
        y=(b-b0)*k;d.line([0,y,30,y],fill=(255,255,0));d.text((2,y+1),str(b),fill=(255,255,0))
    I.save(out)
if __name__=='__main__':
    a=sys.argv;strip(a[1],float(a[2]),float(a[3]),float(a[4]),float(a[5]),float(a[6]),a[7],int(a[8]) if len(a)>8 else 6)
