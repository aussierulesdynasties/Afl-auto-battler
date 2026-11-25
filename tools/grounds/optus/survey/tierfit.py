import json,math,numpy as np,sys
sys.path.insert(0,'/home/user/Afl-auto-battler/tools/grounds/optus');import shape as S
P=json.load(open('tier_pts.json'));R=[]
for k,v in P.items():
    if not v:continue
    u,vv,X,Y,h=v;th=math.atan2(Y-S.OC[1],X-S.OC[0]);d=math.hypot(X-S.OC[0],Y-S.OC[1])-S.edge_r(th);R.append((th,d,h))
R=np.array(R);th,d,h=R.T
tiers={'upper':(h>=18.5)&(d>-31)&(d<-6),'mid':(h>=8)&(h<=17.5)&(d>-41)&(d<-20),'lower':(h>=2)&(h<=6.5)&(d<-38)&(d>-58)}
out={}
for nm,m in tiers.items():
    A=np.stack([np.ones(m.sum()),np.cos(th[m]),np.sin(th[m]),h[m]],1);c,*_=np.linalg.lstsq(A,d[m],rcond=None)
    r=d[m]-A@c;keep=abs(r)<2.5*max(np.std(r),0.3)
    c,*_=np.linalg.lstsq(A[keep],d[m][keep],rcond=None);r=d[m][keep]-A[keep]@c
    out[nm]=dict(c=[float(x) for x in c[:3]],slope=float(c[3]),rms=float(np.sqrt((r**2).mean())),n=int(keep.sum()),drop=int((~keep).sum()),hmin=float(h[m].min()),hmax=float(h[m].max()))
    print(nm,out[nm])
json.dump(out,open('tier_fit.json','w'),indent=1)
