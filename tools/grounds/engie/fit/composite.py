import numpy as np, json, math, sys
from scipy.optimize import minimize_scalar
FIT=json.load(open('fit.json')); p=np.array(FIT['p']); K=FIT['K']; E=json.load(open('edges_true.json'))
dF,dB=-p[-2],-p[-1]
def base(t):
    t=np.asarray(t,float); r=p[2]+sum(p[2+2*k-1]*np.cos(k*t)+p[2+2*k]*np.sin(k*t) for k in range(1,K+1))
    return np.c_[p[0]+r*np.sin(t),p[1]+r*np.cos(t)]
def offset_pt(t,d):
    a=base(t); b=base(t+1e-4); tg=(b-a)/np.linalg.norm(b-a,axis=1)[:,None]; n=np.c_[-tg[:,1],tg[:,0]]  # outward (clockwise param)
    return a+d*n, tg
def ray_hit(bdeg,P0,tg):
    u=np.array([math.sin(math.radians(bdeg)),math.cos(math.radians(bdeg))])
    # solve s*u = P0 + l*tg
    A=np.array([u,-tg]).T; s,l=np.linalg.solve(A,P0); return s
# polar radius of the offset curve at bearing b
TT=np.linspace(0,2*np.pi,14400,endpoint=False)
def offset_polar(d):
    Q,_=offset_pt(TT,d); bb=np.degrees(np.arctan2(Q[:,0],Q[:,1]))%360; rr=np.hypot(Q[:,0],Q[:,1]); o=np.argsort(bb)
    bb,rr=bb[o],rr[o]; return lambda b: float(np.interp(b%360,np.r_[bb-360,bb,bb+360],np.r_[rr,rr,rr]))
def tparam_at_bearing(b,d):
    Q,_=offset_pt(TT,d); bb=np.degrees(np.arctan2(Q[:,0],Q[:,1]))%360; i=np.argmin(np.abs(((bb-b+180)%360)-180)); return TT[i]
STANDS={'N':dict(rng=(315.3,363.0),join='lo',search=(308,317),fit=(318,356)),
        'E':dict(rng=(77.0,135.4),join='hi',search=(134,143),fit=(84,133))}
def inr(b,a,c): return ((np.asarray(b)-a)%360)<=((c-a)%360)
def pts(key):
    a=np.array(E[key]); return a[:,0], np.c_[a[:,1]*np.sin(np.radians(a[:,0])),a[:,1]*np.cos(np.radians(a[:,0]))]
def line_for(d,bj):
    t=tparam_at_bearing(bj,d); P0,tg=offset_pt(np.array([t]),d); return P0[0],tg[0]
def resid_line(P,P0,tg):
    n=np.array([-tg[1],tg[0]]); return (P-P0)@n
def fit_join(key,d,st):
    b,P=pts(key); m=inr(b,*st['fit']); Q=P[m]
    def cost(bj):
        P0,tg=line_for(d,bj); r=resid_line(Q,P0,tg); r=r[np.abs(r)<6]; return np.mean(np.minimum(r**2,9.0))
    res=minimize_scalar(cost,bounds=st['search'],method='bounded'); bj=res.x
    P0,tg=line_for(d,bj); r=resid_line(Q,P0,tg); kept=np.abs(r)<6
    return bj,P0,tg,r,kept
OUT={}
for key,d in (('rf',dF),('rb',dB)):
    for nm,st in STANDS.items():
        bj,P0,tg,r,kept=fit_join(key,d,st)
        OUT[(key,nm)]=(bj,P0,tg)
        rk=r[kept]; print('%s %s tangent join at %.1f deg: rms %.2f m, 95%% %.2f, max %.2f (n=%d, %d mistraces >6 m dropped)'%(key,nm,bj,np.sqrt((rk**2).mean()),np.percentile(np.abs(rk),95),np.abs(rk).max(),kept.sum(),(~kept).sum()))
json.dump({'%s_%s'%k:[v[0],v[1].tolist(),v[2].tolist()] for k,v in OUT.items()},open('joins.json','w'))
