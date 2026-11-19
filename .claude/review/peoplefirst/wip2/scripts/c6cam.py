# camera for the c6 drone photo from 7 points: sign corners and the three yellow V-column feet
import numpy as np,cv2,math,json
cb=np.array([-36.45,-106.9,0.0]);t=math.radians(250.25);n=np.array([math.cos(t),math.sin(t),0]);tg=np.array([-math.sin(t),math.cos(t),0])
sw=3.15*13.06;sh=sw/7.33;c=cb+n*0.8;z0=8.0
X=[c-tg*sw/2+[0,0,z0+sh],c+tg*sw/2+[0,0,z0+sh],c-tg*sw/2+[0,0,z0],c+tg*sw/2+[0,0,z0],[-48.44,-101.73,0],cb,[-23.79,-110.05,0]]
x=[(145,336),(1070,342),(145,456),(1066,468),(310,645),(600,660),(890,655)]
X=np.array(X,float);x=np.array(x,float);best=None
for f in np.arange(500,2500,10):
    K=np.array([[f,0,640],[0,f,360],[0,0,1.]])
    ok,rv,tv=cv2.solvePnP(X,x,K,None,flags=cv2.SOLVEPNP_ITERATIVE)
    p,_=cv2.projectPoints(X,rv,tv,K,None);e=np.sqrt(((p[:,0]-x)**2).sum(1)).mean()
    if best is None or e<best[0]:best=(e,f,rv,tv,p[:,0])
e,f,rv,tv,p=best;Rm,_=cv2.Rodrigues(rv);C=(-Rm.T@tv).ravel();fwd=Rm.T@np.array([0,0,1.])
print('err',round(e,1),'f',f,'hfov',round(math.degrees(2*math.atan(640/f)),1),'C',C.round(1),'tgt',(C+fwd*60).round(1))
print(np.c_[x,p.round(0)])
up=-(Rm.T@np.array([0,1.,0]));print('up',up.round(3))
json.dump({'C':C.tolist(),'T':(C+fwd*60).tolist(),'up':up.tolist(),'hfov':math.degrees(2*math.atan(640/f))},open('c6cam.json','w',newline=''))
