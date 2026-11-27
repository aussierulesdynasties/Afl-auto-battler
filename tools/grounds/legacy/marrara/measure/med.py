# med.py: median turf edge over the registered dates (reg/t*.json), robust polar Fourier K=10, size and axis at the scale given
import json,glob,numpy as np,sys
s=float(sys.argv[1]);J=[json.load(open(f)) for f in sorted(glob.glob('reg/t*.json'))]
cx,cy=J[0]['cx'],J[0]['cy'];A=np.array([p[0] for p in J[0]['pts']])
R=np.array([[p[1] if p[2] else np.nan for p in j['pts']] for j in J])
M=np.nanmedian(R,0);sp=np.nanmedian(np.abs(R-M),0)
def B(a,K):
    t=np.radians(a);return np.column_stack([np.ones_like(t)]+[q(k*t) for k in range(1,K+1) for q in (np.cos,np.sin)])
keep=np.ones(len(A),bool)
for it in range(6):
    c,*_=np.linalg.lstsq(B(A[keep],10),M[keep],rcond=None);res=M-B(A,10)@c;sd=1.4826*np.median(np.abs(res[keep]));keep=np.abs(res)<max(3*sd,1)
print('dates',len(J),'kept',keep.sum(),'rms px %.2f m %.2f'%(np.sqrt((res[keep]**2).mean()),s*np.sqrt((res[keep]**2).mean())))
for a0 in range(0,360,30):
    m=(A>=a0)&(A<a0+30);print('sector',a0,'median date spread px %.1f'%np.median(sp[m]))
a=np.arange(0,360,0.1);r=B(a,10)@c;x=r*np.cos(np.radians(a));y=r*np.sin(np.radians(a))
best=(0,0)
for th in np.arange(0,180,0.1):
    u=x*np.cos(np.radians(th))+y*np.sin(np.radians(th));L=u.max()-u.min()
    if L>best[0]: best=(L,th)
th=best[1];v=-x*np.sin(np.radians(th))+y*np.cos(np.radians(th))
print('long %.1f m axis %.1f deg ccw from east, wide %.1f m'%(best[0]*s,th,(v.max()-v.min())*s))
json.dump({'cx':cx,'cy':cy,'K':10,'c':c.tolist(),'scale_m_px':s,'note':'radius px from (cx,cy) in hist_02 (31 Dec 2007) pixels, angle ccw from east, image y down'},open('tmed_fit.json','w'))
json.dump({'angles':A.tolist(),'median_px':[None if np.isnan(v) else float(v) for v in M]},open('tmed.json','w'))
