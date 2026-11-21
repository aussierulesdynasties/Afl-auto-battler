# python work/footchk.py : facade footprint over Esri. yellow = wall top (z=block height) sheared by the Esri lean
# (x+0.22z, y+0.39z), cyan = wall foot. 10 m grid, bearing ticks every 5 deg. -> work/foot_<N|E|S|W>.png
import sys,json,numpy as np,cv2;sys.path.insert(0,'model')
from PIL import Image
D=json.load(open('model/mcg.json'))
def pol(b,r):return (r*np.sin(np.radians(b)),r*np.cos(np.radians(b)))
def polar(P,bs):
    P=np.array(P,float);out=np.full(len(bs),np.nan);Bq=np.roll(P,-1,0)
    for i,b in enumerate(bs):
        d=np.array(pol(b,1.0));best=np.nan
        for a,c in zip(P,Bq):
            e=c-a;M=np.array([[d[0],-e[0]],[d[1],-e[1]]])
            if abs(np.linalg.det(M))<1e-9:continue
            t,s=np.linalg.solve(M,a)
            if t>0 and 0<=s<=1:best=t if np.isnan(best) else max(best,t)
        out[i]=best
    return out
bs=np.arange(0,360,0.5);fp=np.full(len(bs),np.nan)
for k in ('shane_warne','mcc','olympic','ponsford'):fp=np.fmax(fp,polar(D['osm'][k],bs))
def seg(b):
    for s in D['facade']:
        if s[0]<=b%360<s[1]:return s
S=cv2.imread('sat/esri_025.png');o=S.copy()
P=lambda x,y:(int(round((x+260)*4)),int(round((260-y)*4)))
for v in range(-250,260,10):
    cv2.line(o,P(v,-260),P(v,260),(200,200,200),1);cv2.line(o,P(-260,v),P(260,v),(200,200,200),1)
for i,b in enumerate(bs):
    j=(i+1)%len(bs);z=seg(b)[2]
    if np.isnan(fp[i]) or np.isnan(fp[j]):continue
    x0,y0=pol(b,fp[i]);x1,y1=pol(bs[j],fp[j])
    cv2.line(o,P(x0,y0),P(x1,y1),(255,255,0),2)
    cv2.line(o,P(x0+0.22*z,y0+0.39*z),P(x1+0.22*z,y1+0.39*z),(0,255,255),2)
    if b%5==0:
        cv2.putText(o,str(int(b)),P(*pol(b,fp[i]+14)),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,0,255),2)
cv2.imwrite('work/foot.png',o)
for n,(xa,xb,ya,yb) in dict(N=(-110,110,100,200),S=(-110,110,-200,-100),E=(90,200,-110,110),W=(-200,-90,-110,110)).items():
    c=o[P(0,yb)[1]:P(0,ya)[1],P(xa,0)[0]:P(xb,0)[0]];cv2.imwrite(f'work/foot_{n}.png',c)
print('ok')
