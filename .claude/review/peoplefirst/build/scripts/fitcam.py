import numpy as np,json,math,cv2
from scipy.optimize import least_squares
S=json.load(open('sat.json'));m=S['mpp'];H0=np.load('H0.npy')
def warp2w(u,v):
    q=cv2.perspectiveTransform(np.float32([[[u,v]]]),np.linalg.inv(H0))[0,0];return ((q[0]-S['px'])*m,-(q[1]-S['py'])*m)
# (photo uv, satwarp uv, z)
PTS=[((940,1268),(920,1252),3.5),((1095,1277),(1100,1275),3.5),((1870,832),(1825,840),3.5),((1850,912),(1805,910),3.5),((1510,1095),(1487,1085),0.0)]
X=np.array([(*warp2w(*s),z) for p,s,z in PTS]);Y=np.array([p for p,s,z in PTS],float)
GW=np.load('grass_w.npy');GW=np.concatenate([GW,np.zeros((len(GW),1))],1)
GP=np.load('grass_p.npy');GP=GP[(GP[:,1]<650)&(GP[:,0]>700)&(GP[:,0]<1340)]
GP=np.concatenate([GP,np.array([(658,598),(608,620),(572,642),(542,664),(520,692),(506,720),(500,748)],float)])
W,Hh=2000,1333
def R(yaw,pitch_,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch_),math.sin(pitch_);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    C=p[:3];M=R(*p[3:6]);fo=p[6];d=(X-C)@M.T
    return np.stack([W/2+fo*d[:,0]/d[:,2],Hh/2-fo*d[:,1]/d[:,2]],1)
def res(p):
    r1=(proj(p,X)-Y).ravel()
    pp=proj(p,GW);dd=np.sqrt(((GP[:,None,:]-pp[None])**2).sum(-1)).min(1)
    return np.concatenate([r1,dd*0.7])
if __name__=='__main__':
    best=None
    for d0 in (500,800,1200):
        p0=[-d0*0.9,0,d0*0.6,0.0,-0.55,0,2500]
        s=least_squares(res,p0)
        if best is None or s.cost<best.cost:best=s
    s=best;r=s.fun;n=2*len(X)
    print('pt rms',round(math.sqrt((r[:n]**2).mean()),1),'grass rms',round(math.sqrt((r[n:]**2/0.49).mean()),1))
    print([round(v,3) for v in s.x]);print(np.round(r[:n].reshape(-1,2),1))
    json.dump({'p':list(s.x)},open('cam.json','w'))
