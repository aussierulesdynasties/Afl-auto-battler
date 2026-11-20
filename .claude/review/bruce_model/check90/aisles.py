import sys,numpy as np,cv2
sys.path.insert(0,'C:/kt/bruce1990/.claude/review/bruce_model');import aerial90 as A
src=cv2.imread('bruce/legacy/src90.png')[:,:,::-1].astype(np.float32)
def prof(b0,b1,g0,g1,h):
    B=np.arange(b0,b1,0.1);G=np.arange(g0,g1,0.25);t=np.radians(B)[:,None];r=A.r_grass(np.radians(B))[:,None]+G[None]
    P=np.stack([A.CX+r*np.cos(t),A.CY+r*np.sin(t)],-1).reshape(-1,2);px=A.m2px(P,h).reshape(len(B),len(G),2).astype(np.float32)
    S=cv2.remap(src,px[...,0],px[...,1],cv2.INTER_LINEAR);pal=S[...,2]-S[...,0]*0.5  # blue up = grey/white concrete vs terracotta
    p=pal.mean(1);p=p-np.convolve(p,np.ones(41)/41,'same');return B,p
from scipy.signal import find_peaks
for nm,(b0,b1,g0,g1,h) in {'SE':(-68,2,19,28,4),'N':(70,108,5,12,3),'SWa':(-150,-132,3,10,3),'SWb':(-171,-153,2,9,3)}.items():
    B,p=prof(b0,b1,g0,g1,h);k,_=find_peaks(p,distance=40,prominence=4);print(nm,np.round(B[k],1),np.round(np.diff(B[k]),2),np.round(p[k],1))
