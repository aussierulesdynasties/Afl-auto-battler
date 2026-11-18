import numpy as np,json,math
exec(open('fitA11.py').read().split('best=None\nfor f0')[0])
def res1(p):
    cam=p[:7];q=pd(cam,sqc(p));best=None
    for k in range(4):
        d=(q[[(i+k)%4 for i in range(4)]]-SQI).ravel()
        if best is None or (d**2).sum()<(best**2).sum():best=d
    return np.concatenate([best*4,curve_d(RRI,pd(cam,RR)),[p[8]*0.3,p[9]*0.3]])
cands=[]
for f0 in (700,900,1100,1300,1600,2000):
  for th in (-6,0,6):
    D=f0*50/170*1.0
    for pit in (-35,-42,-50):
      pr=math.radians(pit);C=[0,-D*math.cos(pr),D*math.sin(-pr)]
      p0=C+[math.radians(93),pr,math.radians(-3),f0,math.radians(th),0,0,90,62]
      sol=least_squares(lambda q:res1(np.r_[q,90,62]),p0[:10],loss='soft_l1',f_scale=2)
      cands.append(((sol.fun**2).mean(),np.r_[sol.x,90,62]))
cands.sort(key=lambda c:c[0]);json.dump(list(cands[0][1]),open('pA12s1.json','w'))
for c,p in cands[:6]:print(round(c,2),'f',round(p[6]),'C',np.round(p[:3]),'ypr',np.round(np.degrees(p[3:6]),1),'th',round(math.degrees(p[7]),1))
# stage 2 from best 3
best=None
for c,p in cands[:3]:
    sol=least_squares(res,p,loss='soft_l1',f_scale=2,max_nfev=2000);r1,r2,r3=res(sol.x,True);cc=(sol.fun**2).mean()
    print('S2',round(cc,2),'f',round(sol.x[6]),'AB',np.round(sol.x[10:12],1),'lines med',round(float(np.median(r1)),2),'sq',round(float(np.sqrt((r2**2).mean())),2),'rr',round(float(np.sqrt((r3**2).mean())),2),flush=True)
    if best is None or cc<best[0]:best=(cc,sol.x)
p=best[1]
print('cam',np.round(p[:3],1),np.round(np.degrees(p[3:6]),2),round(p[6],1),'ground',np.round([math.degrees(p[7]),*p[8:12]],2))
b=at_z(p[:7],924,554,cx,cy,2);q=proj(p[:7],b+[0,0,15],cx,cy)[0];print('pole dir',np.round((q-[924,554])/np.linalg.norm(q-[924,554]),2),'photo',np.round(np.array([17,-84])/np.hypot(17,84),2))
ov,sq,arcs=model(p)
json.dump({'p':list(p[:7])+[1.0],'W':W,'H':H,'ground':list(p[7:12]),'oval':ov.tolist(),'square':sqc(p).tolist(),'arcs':[a.tolist() for a in arcs]},open('camA12.json','w'))
