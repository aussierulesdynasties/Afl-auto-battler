# Two fits: (1) the field edge, a 3-harmonic polar curve fitted to the sunlit field edge (east, south and the open
# north-east end; the west and north field edge lies in shadow under the stands in Google Earth); (2) the 1998
# bowl, a 6-harmonic curve fitted to the old stands' roof front, its roof back an exact normal offset of it.
import numpy as np, json, math, cv2
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
C=json.load(open('cal.json')); S,DX,DY=C['s'],C['dx'],C['dy']; E=json.load(open('edges_true.json'))
f=np.load('field.npy').astype(np.uint8)
cs,_=cv2.findContours(f,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); c=max(cs,key=len)[:,0,:].astype(float)
fe=(c[:,0]-640)*S+DX; fn=-(c[:,1]-360)*S+DY; fb=np.degrees(np.arctan2(fe,fn))%360
F0=np.c_[fe,fn][(fb>20)&(fb<200)]
# the west and north field edge, traced in the shade (fieldshadow.py): turf to apron step
SH=np.array(json.load(open('field_shadow.json'))); SB=SH[:,0]
FS=np.c_[SH[:,1]*np.sin(np.radians(SB)),SH[:,1]*np.cos(np.radians(SB))]
F0s=F0; F0=np.r_[F0,FS]
T=np.linspace(0,2*np.pi,2880,endpoint=False)
def curve(p,K):
    r=p[2]+sum(p[2+2*k-1]*np.cos(k*T)+p[2+2*k]*np.sin(k*T) for k in range(1,K+1))
    x=p[0]+r*np.sin(T); y=p[1]+r*np.cos(T); dx=np.gradient(x); dy=np.gradient(y); L=np.hypot(dx,dy)
    return x,y,-dy/L,dx/L    # outward normal
def ring(p,K,d): x,y,nx,ny=curve(p,K); return np.c_[x+d*nx,y+d*ny]
def st(v): return 'rms %.2f m, 95%% %.2f, max %.2f (n=%d)'%(np.sqrt((v**2).mean()),np.percentile(v,95),v.max(),len(v))
# (1) field
KF=5
rF=least_squares(lambda p: cKDTree(ring(p,KF,0)).query(F0)[0],np.r_[0,0,76,np.zeros(2*KF)],loss='soft_l1').x
vF=cKDTree(ring(rF,KF,0)).query(F0s)[0]; print('field edge sunlit (K=%d):'%KF,st(vF))
vS=cKDTree(ring(rF,KF,0)).query(FS)[0]; print('field edge shaded:',st(vS[vS<4]),' %d mistraces >4 m'%(vS>=4).sum())
# (2) bowl from old stands' roof edges
def pts(key,lo=139,hi=311):
    a=np.array(E[key]); m=(a[:,0]>=lo)&(a[:,0]<=hi); a=a[m]; return np.c_[a[:,1]*np.sin(np.radians(a[:,0])),a[:,1]*np.cos(np.radians(a[:,0]))]
RF,RB=pts('rf'),pts('rb'); K=6
def res(p):
    w=p[-1]; return np.r_[cKDTree(ring(p[:-1],K,0)).query(RF)[0],cKDTree(ring(p[:-1],K,w)).query(RB)[0]]
r=least_squares(res,np.r_[0,0,83,np.zeros(2*K),26.0],loss='soft_l1',f_scale=1.0); p=r.x
vf=cKDTree(ring(p[:-1],K,0)).query(RF)[0]; vb=cKDTree(ring(p[:-1],K,p[-1])).query(RB)[0]
print('1998 bowl roof front:',st(vf[vf<4]),' %d mistraces >4 m'%(vf>=4).sum())
print('1998 bowl roof back (exact offset %.2f m):'%p[-1],st(vb[vb<4]),' %d mistraces >4 m'%(vb>=4).sum())
# write in the old fit.json layout for composite.py: base = the roof front ring, offsets 0 and the width (negated)
json.dump({'p':list(p[:-1])+[-0.0,-float(p[-1])],'K':K,'field':{'p':rF.tolist(),'K':KF},'rings':[ring(rF,KF,0)[::8].tolist(),ring(p[:-1],K,0)[::8].tolist(),ring(p[:-1],K,p[-1])[::8].tolist()]},open('fit.json','w'))
