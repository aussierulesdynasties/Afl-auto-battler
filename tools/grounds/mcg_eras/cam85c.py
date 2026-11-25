import cv2,numpy as np,json
from scipy.optimize import least_squares
import cam85b as cb
arena_img=np.array([(300,745),(330,728),(370,721),(410,718),(450,716),(490,716),(530,717),(570,720),(610,727),(650,740),(675,760),(280,765),(287,788),(680,782)],float)
t=np.radians(np.arange(0,360,0.5)); a,b,ang=87.19,73.39,np.radians(-3.3)
x=a*np.cos(t); y=b*np.sin(t); E=np.c_[0.53+x*np.cos(ang)-y*np.sin(ang),0.39+x*np.sin(ang)+y*np.cos(ang),np.zeros_like(t)]
def res(q,w_ar=1.0):
    p=q[:7]; zH=q[7]
    r=[]
    for n,(u,v) in cb.heads.items(): pp=cb.proj(p,[(cb.T[n][0],cb.T[n][1],zH)])[0]; r+=[pp[0]-u,pp[1]-v]
    for n,pts in cb.shafts.items():
        A,B=cb.proj(p,[(cb.T[n][0],cb.T[n][1],4.2),(cb.T[n][0],cb.T[n][1],zH)]); d=(B-A)/np.linalg.norm(B-A); nr=np.array([-d[1],d[0]])
        for u,v in pts: r.append(np.dot(np.array([u,v])-A,nr))
    P=cb.proj(p,E)
    for u,v in arena_img: r.append(w_ar*np.min(np.hypot(P[:,0]-u,P[:,1]-v)))
    return np.array(r)
p0=np.array(json.load(open(__import__('os').path.join(__import__('os').path.dirname(__file__),'measure','cam_1985.json')))['p'])
best=None
for zH in [66,70,74,78,82,86]:
    s=least_squares(res,np.r_[p0,zH])
    if best is None or s.cost<best.cost: best=s
q=best.x; r=res(q); R,_=cv2.Rodrigues(q[:3]); C=-R.T@q[3:6]
print('f %.0f zHead %.1f cam %s rms %.2f px'%(q[6],q[7],C.round(1),np.sqrt(np.mean(r**2))))
print('heads',np.round(r[:12],1)); print('shafts',np.round(r[12:20],1)); print('arena',np.round(r[20:],1))
json.dump({'p':q[:7].tolist(),'zH':q[7]},open('cam85c.json','w'))
