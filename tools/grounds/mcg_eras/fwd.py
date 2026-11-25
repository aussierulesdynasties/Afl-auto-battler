# Forward model of the roof-front shadow on the turf; fits roof-front heights at nodes.
import numpy as np,cv2,sys
from scipy.optimize import least_squares
F=np.loadtxt(__import__('os').path.join(__import__('os').path.dirname(__file__),'measure','front_north.txt'))
RES=0.25; N=int(260/RES); O=130.0
def arena_r(b):
    t=np.radians(b); a,bb=87.19,73.39
    return 1/np.sqrt((np.sin(t)/a)**2+(np.cos(t)/bb)**2)
def shadow_mask(nodes,hs,az,e):
    th=np.arange(F[0,0],F[-1,0]+0.01,0.25); r=np.interp(th,F[:,0],F[:,1]); h=np.interp(th,nodes,hs)
    P=np.c_[r*np.sin(np.radians(th)),r*np.cos(np.radians(th))]
    d=np.array([np.sin(np.radians(az+180)),np.cos(np.radians(az+180))]); t=1/np.tan(np.radians(e))
    Q=P+(h*t)[:,None]*d
    m=np.zeros((N,N),np.uint8)
    pix=lambda X:np.c_[(X[:,0]+O)/RES,(O-X[:,1])/RES]
    Pp,Qp=pix(P),pix(Q)
    for i in range(len(th)-1):
        poly=np.array([Pp[i],Pp[i+1],Qp[i+1],Qp[i]])
        cv2.fillPoly(m,[np.round(poly*8).astype(np.int32)],1,shift=3)
    return m
def pred_edge(m,b,r0=25,r1=95):
    rr=np.arange(r0,r1,0.1); x=rr*np.sin(np.radians(b)); y=rr*np.cos(np.radians(b))
    v=cv2.remap(m.astype(np.float32),((x+O)/RES).astype(np.float32)[None],((O-y)/RES).astype(np.float32)[None],cv2.INTER_LINEAR)[0]
    i=np.argmax(v>=0.5); return rr[i] if v[i]>=0.5 else np.nan
def obs(fn,lo,hi):
    S=np.loadtxt(fn); S=S[~np.isnan(S[:,1])]
    keep=[]
    for b,r in S:
        bu=b if b>=lo else b+360
        if lo<=bu<=hi and r<arena_r(b)-2.5: keep.append((bu,r))
    return np.array(keep)
def fit(fn,az,e,nodes,h0,lo=300,hi=490,fixed=None):
    S=obs(fn,lo,hi)
    def res(hs):
        m=shadow_mask(nodes,hs,az,e); p=np.array([pred_edge(m,b%360) for b in S[:,0]])
        p=np.where(np.isnan(p),S[:,1]+15,p); return p-S[:,1]
    sol=least_squares(res,h0,bounds=(0,70),diff_step=0.02,loss='soft_l1',f_scale=1.5)
    rr=res(sol.x); J=sol.jac; 
    try:
        cov=np.linalg.inv(J.T@J)*np.mean(rr**2); sd=np.sqrt(np.diag(cov))
    except Exception: sd=np.full(len(h0),np.nan)
    return sol.x,sd,S,rr
if __name__=='__main__':
    nodes=[237.5,260,285,297.5,312.5,330,340,360,380,400,420,425,445,470,490]
    h0=[25]*len(nodes)
    for name,fn,az,e in [('Jun 2001','jun_edge.txt',28.7,23.04),('Jul 2001','jul_edge.txt',29.6,23.24)]:
        x,sd,S,rr=fit(fn,az,e,nodes,np.array(h0,float))
        print(name,'rms %.2f m over %d turf points'%(np.sqrt(np.mean(rr**2)),len(S)))
        for n,h,s in zip(nodes,x,sd): print('   %6.1f  h %5.1f  +-%.1f'%(n%360,h,s))
        print('   residuals',' '.join('%d:%+.1f'%(b%360,r) for b,r in zip(S[:,0],rr)))
