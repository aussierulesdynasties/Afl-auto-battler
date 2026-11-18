import numpy as np,json,math
exec(open('fitA11.py').read().split('best=None\nfor f0')[0])
p=np.array(json.load(open('pA12s1.json')))
def curves(p):
    ov,sq,arcs=model(p);return [ov,sq]+arcs
def assign(p,tol):
    cam=p[:7];C=curves(p);D=np.array([curve_d(LP,pd(cam,c)) if len(c)>1 else np.full(len(LP),1e3) for c in C]);k=D.argmin(0);dm=D.min(0)
    return [LP[(k==i)&(dm<tol)] for i in range(len(C))]
def res(p,G,full=False):
    cam=p[:7];C=curves(p);r=[curve_d(g,pd(cam,c)) for g,c in zip(G,C) if len(g)]
    q=pd(cam,sqc(p));best=None
    for k in range(4):
        d=(q[[(i+k)%4 for i in range(4)]]-SQI).ravel()
        if best is None or (d**2).sum()<(best**2).sum():best=d
    r3=curve_d(RRI,pd(cam,RR))
    return (r,best,r3) if full else np.concatenate(r+[best*3,r3*3,[p[8]*0.3,p[9]*0.3]])
# first A,B only
for tol in (25,15,10,7,5):
    G=assign(p,tol)
    sol=least_squares(lambda q:res(np.r_[p[:10],q],G),p[10:12],loss='soft_l1',f_scale=2);p[10:12]=sol.x
    sol=least_squares(lambda q:res(q,G),p,loss='soft_l1',f_scale=2);p=sol.x
    r,b,r3=res(p,G,True)
    print(tol,'n',[len(g) for g in G],'curve rms',[round(float(np.sqrt(np.mean(x**2))),2) for x in r],'sq',round(float(np.sqrt(np.mean(b**2))),2),'rr',round(float(np.sqrt(np.mean(r3**2))),2),'f',round(p[6]),'AB',np.round(p[10:12],1),flush=True)
print('cam',np.round(p[:3],1),np.round(np.degrees(p[3:6]),2),round(p[6],1),'ground',np.round([math.degrees(p[7]),*p[8:12]],2))
b=at_z(p[:7],924,554,cx,cy,2);q=proj(p[:7],b+[0,0,15],cx,cy)[0];print('pole dir',np.round((q-[924,554])/np.linalg.norm(q-[924,554]),2),'photo',np.round(np.array([17,-84])/np.hypot(17,84),2))
json.dump(list(p),open('pA13.json','w'))
ov,sq,arcs=model(p)
json.dump({'p':list(p[:7])+[1.0],'W':W,'H':H,'ground':list(p[7:12]),'oval':ov.tolist(),'square':sqc(p).tolist(),'arcs':[a.tolist() for a in arcs]},open('camA13.json','w'))
