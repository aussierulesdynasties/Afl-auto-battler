import numpy as np,json,math,itertools
from scipy.optimize import least_squares
exec(open('cam.py').read())
HEAD={'A':(396,45),'B':(869,30),'C':(982,88),'D':(892,478),'E':(410,483)}
BASE={'C':(962,210),'D':(872,638),'E':(432,640),'F':(205,475)}
order=['F','A','B','C','D','E']
GR=np.load('grass.npy').astype(float)
pitch=dens(G['4000006']);pitch=np.c_[pitch,np.zeros(len(pitch))]
best=None
for sh in [0]:
    lab={order[i]:TN[(i+sh)%6] for i in range(6)}
    X=[];Y=[];isH=[]
    for k,v in HEAD.items():X.append((*TOW[lab[k]],0));Y.append(v);isH.append(1)
    for k,v in BASE.items():X.append((*TOW[lab[k]],0));Y.append(v);isH.append(0)
    X=np.array(X,float);Y=np.array(Y,float);isH=np.array(isH,bool)
    def res(p):
        Xh=X.copy();Xh[isH,2]=p[9]
        r1=(proj(p,Xh)-Y).ravel()
        pp=proj(p,pitch);dd=np.sqrt(((GR[:,None,:]-pp[None])**2).sum(-1)).min(1)
        return np.concatenate([r1,dd*0.7])
    for yaw0 in np.radians(np.arange(-180,180,30)):
        d=500;C0=[-d*math.cos(yaw0)*0.7,-d*math.sin(yaw0)*0.7,400]
        p0=[*C0,yaw0,-0.6,0,1100,600,337,60]
        try:s=least_squares(res,p0,bounds=([-3e3,-3e3,50,-10,-1.5,-0.4,300,200,0,30],[3e3,3e3,2e3,10,-0.05,0.4,4000,1000,700,95]))
        except Exception as e:continue
        r=s.fun;tr=math.sqrt((r[:2*len(X)]**2).mean());gr=math.sqrt((r[2*len(X):]**2).mean()/0.49)
        if best is None or s.cost<best[0]:best=(s.cost,sh,tr,gr,s.x,lab,r[:2*len(X)].reshape(-1,2))
print(np.round(best[6],0));print('shift',best[1],'tower rms',round(best[2],1),'grass rms',round(best[3],1));p=best[4]
print([round(v,3) for v in p]);json.dump({'p':list(p),'lab':best[5]},open('cam.json','w'))
