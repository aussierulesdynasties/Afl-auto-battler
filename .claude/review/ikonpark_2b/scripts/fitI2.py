import json,numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
exec(open('w/cam.py').read())
W,H=1200,710
P=np.array(g['22779384']);D=[]
for i in range(len(P)):
    a,b=P[i],P[(i+1)%len(P)]
    for t in np.linspace(0,1,30,endpoint=False): D.append(a+(b-a)*t)
D=np.array(D);cen=P.mean(0);Nn=D-cen;Nn/=np.linalg.norm(Nn,axis=1)[:,None]
man=np.array([(0,361),(70,361),(200,363),(300,365),(400,367),(500,371.7),(600,376),(700,379),(790,384),(850,387),(900,391.7),(950,394),(1000,396.7),(1050,400),(1100,403),(1150,406.7)])
T=json.load(open('w/i2_trace.json'))
E=np.array([p for p in T['edge'] if abs(p[1]-np.interp(p[0],man[:,0],man[:,1]))<3 and not (1010<p[0]<1145)])
print('edge pts',len(E))
PB=np.array([(1026,402),(1058,404),(1092,407),(1134,412)]);GB0=np.array([[-32.75,19.72],[-32.03,25.82],[-31.25,32.41],[-30.45,39.12]]);AX=np.array([0.99304538,-0.11773218])
def pr(q,X):
    M=R(*q[3:6]);d=(X-q[:3])@M.T
    return np.c_[W/2+q[6]*d[:,0]/d[:,2],H/2-q[6]*d[:,1]/d[:,2]],d[:,2]
def res(q):
    X=np.c_[D+Nn*q[7],np.zeros(len(D))];P2,z=pr(q,X)
    far=(z>0)&(X[:,1]<40)&(P2[:,0]>-50)&(P2[:,0]<W+50)
    r=list(cKDTree(P2[far]).query(E)[0])
    pb,_=pr(q,np.c_[GB0+AX*q[8],np.zeros(4)]); r+=list(((pb-PB)*3).ravel())
    return np.array(r)
best=None
for cx in (-20,10,40):
  for cy in (100,115):
    for f0 in (800,1300):
      v=np.array([20.,-40.])-np.array([cx,cy]);yaw=np.arctan2(v[1],v[0])
      q0=np.r_[cx,cy,4.0,yaw,-0.02,0,f0,4.0,0]
      try:o=least_squares(res,q0,loss='soft_l1',f_scale=2,max_nfev=1500,bounds=([-np.inf]*2+[0.5]+[-np.inf]*3+[300,0,-6],[np.inf]*6+[4000,20,6]))
      except Exception as e: continue
      if best is None or o.cost<best.cost: best=o
q=best.x;rr=res(q);n=len(E)
print('q',np.round(q,3),'cost',round(best.cost,2));print('edge rms',np.sqrt(np.mean(rr[:n]**2)),'bases',np.round(rr[n:]/3,1))
json.dump({'q':list(q[:7])+[W/2,H/2],'off':q[7],'shift':q[8]},open('w/camI2.json','w'))
