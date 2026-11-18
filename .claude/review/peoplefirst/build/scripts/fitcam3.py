import numpy as np,json,math,cv2
from scipy.optimize import least_squares
from fitcam import GW,GP,R,proj,W,Hh,S,m
Hc=np.load('Hc_v1.npy')
def w2(u,v):
    q=cv2.perspectiveTransform(np.float32([[[u,v]]]),np.linalg.inv(Hc))[0,0];return ((q[0]-S['px'])*m,-(q[1]-S['py'])*m)
PTS=[((837,1287),(902,1312),3.5),((930,1255),(985,1277),3.5),((1022,1287),(1080,1305),3.5),((1177,1270),(1200,1290),3.5),
((978,1202),(1020,1209),0),((1515,1088),(1512,1109),4),((1770,1015),(1750,1027),4),((1887,930),(1875,937),4),((1720,700),(1760,705),1),((265,695),(250,710),0)]
X=np.array([(*w2(*s),z) for p,s,z in PTS]);Y=np.array([p for p,s,z in PTS],float)
TW=[((654,488),(648,200)),((330,783),(312,450)),((1340,1043),(1333,693))]
nt=len(TW)
def unpack(q):return q[:7],q[7:].reshape(nt,3)
def res(q):
    p,T=unpack(q);r1=(proj(p,X)-Y).ravel()
    pp=proj(p,GW);dd=np.sqrt(((GP[:,None,:]-pp[None])**2).sum(-1)).min(1)
    rt=[]
    for (b,t),(x,y,h) in zip(TW,T):rt+=list(proj(p,np.array([[x,y,0.0]]))[0]-b)+list(proj(p,np.array([[x,y,h]]))[0]-t)
    return np.concatenate([r1,dd*0.7,np.array(rt)*1.5])
p0=json.load(open('cam_v1.json'))['p'];T0=[(92,68,66),(-85,44,70),(-89,-77,74)]
best=None
for k in (1.0,0.6,1.5):
    q=np.array(p0,float);q[:3]*=k;q[6]*=k
    s=least_squares(res,np.concatenate([q,np.array(T0,float).ravel()]),loss='soft_l1',f_scale=8)
    if best is None or s.cost<best.cost:best=s
s=best;r=s.fun;n=2*len(X);ng=len(GP)
print('pts',np.round(r[:n].reshape(-1,2),1).tolist())
print('grass rms',round(math.sqrt(((r[n:n+ng]/0.7)**2).mean()),1),'tower',np.round(r[n+ng:]/1.5,1))
p,T=unpack(s.x);print(np.round(p,4).tolist());print(np.round(T,1).tolist())
json.dump({'p':list(p)},open('cam.json','w'))
