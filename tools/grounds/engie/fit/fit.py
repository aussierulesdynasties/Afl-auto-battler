# Run from a work folder holding the Google Earth shots in ge/ (never committed; looking and measuring only).
import numpy as np, json, math, cv2, sys
from scipy.optimize import least_squares
C=json.load(open('cal.json')); S,DX,DY=C['s'],C['dx'],C['dy']
E=json.load(open('edges.json'))
f=np.load('field.npy').astype(np.uint8)
cs,_=cv2.findContours(f,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); c=max(cs,key=len)[:,0,:].astype(float)
fe=(c[:,0]-640)*S+DX; fn=-(c[:,1]-360)*S+DY; fb=np.degrees(np.arctan2(fe,fn))%360
sel=(fb>25)&(fb<190); F0=np.c_[fe[sel],fn[sel]]
def xy(lst): a=np.array(lst); return np.c_[a[:,1]*np.sin(np.radians(a[:,0])),a[:,1]*np.cos(np.radians(a[:,0]))]
RF,RB=xy(E['rf']),xy(E['rb'])
K=int(sys.argv[1]) if len(sys.argv)>1 else 4
T=np.linspace(0,2*np.pi,2880,endpoint=False)
def curve(p):
    cx,cy=p[0],p[1]; a=p[2:3+2*K]
    r=a[0]+sum(a[2*k-1]*np.cos(k*T)+a[2*k]*np.sin(k*T) for k in range(1,K+1))
    x=cx+r*np.sin(T); y=cy+r*np.cos(T)
    dx=np.gradient(x); dy=np.gradient(y); L=np.hypot(dx,dy); nx,ny=dy/L,-dx/L   # outward for clockwise param
    return x,y,nx,ny
def ring(p,d):
    x,y,nx,ny=curve(p); return np.c_[x+d*nx,y+d*ny]
def dist(P,R):
    from scipy.spatial import cKDTree
    return cKDTree(R).query(P)[0]
def res(p):
    d1,d2=p[-2],p[-1]
    return np.r_[dist(F0,ring(p,0)),dist(RF,ring(p,d1)),dist(RB,ring(p,d2))]
p0=np.r_[0,0,75]+0; p0=np.r_[0.0,0.0,76.0,np.zeros(2*K),5.0,30.0]
r=least_squares(res,p0,loss='soft_l1',f_scale=1.0)
p=r.x; nF=len(F0); nR=len(RF)
rF,rR,rB=r.fun[:nF],dist(RF,ring(p,p[-2])),dist(RB,ring(p,p[-1]))
def st(v): return 'rms %.2f m, 95%% %.2f m, max %.2f m'%(np.sqrt((v**2).mean()),np.percentile(v,95),v.max())
print('K',K,'offsets roof front %.2f roof back %.2f'%(p[-2],p[-1]))
print('field edge',st(rF)); print('roof front',st(rR)); print('roof back',st(rB))
# per stand
ST={'N 2012':(315.3,363),'E 2012':(77,135.4),'SE':(141.4,172.2),'S':(178.2,205.8),'SW':(211.8,239.3),'W':(245.3,272.3),'NW':(278.3,309.3)}
for nm,(a,b) in ST.items():
    for lab,P,v in (('front',RF,rR),('back',RB,rB)):
        bb=np.degrees(np.arctan2(P[:,0],P[:,1]))%360; m=((bb-a)%360)<=(b-a)
        # signed: + = real outside the ring
        R=ring(p,p[-2] if lab=='front' else p[-1]); from scipy.spatial import cKDTree; i=cKDTree(R).query(P[m])[1]
        x,y,nx,ny=curve(p); sgn=np.sign(((P[m]-R[i])*np.c_[nx[i],ny[i]]).sum(1))
        sv=v[m]*sgn
        print('  %-7s %-5s n=%3d mean %+.2f rms %.2f max %.2f'%(nm,lab,m.sum(),sv.mean() if m.sum() else 0,np.sqrt((sv**2).mean()) if m.sum() else 0,np.abs(sv).max() if m.sum() else 0))
json.dump({'p':p.tolist(),'K':K,'rings':[ring(p,0)[::8].tolist(),ring(p,p[-2])[::8].tolist(),ring(p,p[-1])[::8].tolist()]},open('fit.json','w'))
print('--- excluding gross mistraces (>8 m: points on pavilion roofs or red seats) ---')
for lab,v in (('field edge',rF),('roof front',rR),('roof back',rB)):
    m=v<8; print('%-10s kept %d/%d  rms %.2f  95%% %.2f  max %.2f'%(lab,m.sum(),len(v),np.sqrt((v[m]**2).mean()),np.percentile(v[m],95),v[m].max()))
