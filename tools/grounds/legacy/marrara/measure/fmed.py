import json,glob,numpy as np,sys
s=0.2931;files=sys.argv[2:];J=[json.load(open(f)) for f in files]
A=np.array([p[0] for p in J[0]['pts']]);t=np.radians(A)
R=np.array([[p[1] if p[2] else np.nan for p in j['pts']] for j in J]);M=np.nanmedian(R,0);sp=np.nanmedian(np.abs(R-M),0)
B=lambda t,K: np.column_stack([np.ones_like(t)]+[q(k*t) for k in range(1,K+1) for q in (np.cos,np.sin)])
keep=~np.isnan(M)
for it in range(6):
    c,*_=np.linalg.lstsq(B(t[keep],10),M[keep],rcond=None);res=M-B(t,10)@c;sd=1.4826*np.nanmedian(np.abs(res[keep]));keep=(~np.isnan(M))&(np.abs(res)<max(3*sd,1))
print(len(J),'dates kept',keep.sum(),'rms m %.2f'%(s*np.sqrt((res[keep]**2).mean())),'date spread m per 30deg',[round(s*float(np.nanmedian(sp[(A>=a)&(A<a+30)])),1) for a in range(0,360,30)])
a=np.radians(np.arange(0,360,0.1));r=B(a,10)@c;x=r*np.cos(a);y=r*np.sin(a);best=(0,0)
for th in np.arange(0,180,0.1):
    u=x*np.cos(np.radians(th))+y*np.sin(np.radians(th));best=max(best,(u.max()-u.min(),th))
th=np.radians(best[1]);v=-x*np.sin(th)+y*np.cos(th);print('long %.1f axis %.1f wide %.1f'%(best[0]*s,best[1],(v.max()-v.min())*s))
json.dump({'cx':J[0]['cx'],'cy':J[0]['cy'],'K':10,'c':c.tolist(),'scale_m_px':s,'dates':files,'note':'fence wall, radius px from (cx,cy) in hist_02 (31 Dec 2007) pixels, angle ccw from east, image y down'},open(sys.argv[1],'w'))
