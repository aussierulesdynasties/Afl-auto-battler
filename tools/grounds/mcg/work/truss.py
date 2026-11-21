import sys,numpy as np;sys.path.insert(0,'work');import tri
from PIL import Image
from scipy.signal import find_peaks
def projv(c,X):
    d=X-c['C'];z=d@c['fwd'];return np.stack([c['W']/2+c['f']*(d@c['right'])/z,c['H']/2-c['f']*(d@c['up'])/z],-1)
z=float(sys.argv[1])
res={}
for v,b0,b1 in [('n_ne',20,80),('n_e',50,130),('n_se',100,170),('n_s',140,220),('n_sw',190,260),('n_w',240,320),('n_nw',290,350),('n_n',330,400)]:
    c=tri.camv(v);im=np.asarray(Image.open(f'ge/{v}.png').convert('RGB')).astype(int)
    R=np.arange(85,150,0.25);B=np.arange(b0,b1,0.2);a=np.radians(B)[:,None]
    X=np.stack([R[None]*np.sin(a),R[None]*np.cos(a),np.full((len(B),len(R)),z)],-1);P=projv(c,X)
    u=P[...,0].round().astype(int);w=P[...,1].round().astype(int);ok=(u>=0)&(u<1920)&(w>=90)&(w<1045)
    S=im[np.clip(w,0,1079),np.clip(u,0,1919)];blue=(S[...,2]-S[...,0]>35)&(S[...,2]>S[...,1]+5)&ok
    prof=blue.sum(1);pk,_=find_peaks(prof,height=12,distance=10)
    print(v,[ (round(B[p]%360,1),int(prof[p]), round(float(R[blue[p]].min()),1), round(float(R[blue[p]].max()),1)) for p in pk])
