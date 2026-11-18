import numpy as np,json,cv2
from scipy.optimize import least_squares
from scipy.ndimage import map_coordinates
from meas import pr
wm=cv2.imread('wm_roof.png',0)>0
bd=(wm^cv2.erode(wm.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool))
dt=cv2.distanceTransform((~bd).astype(np.uint8),cv2.DIST_L2,5)
G=json.load(open('geo_build.json'));rin=np.array(G['rin']);rout=np.array(G['rout'])
A=np.arange(0,1440,4);deg=A/4;sp=(deg>=106)|(deg<=35);A=A[sp];th=np.radians(A/4)
def curve(r,c,s):
    h=c[0]+c[1]*np.cos(th)+c[2]*np.sin(th);return np.stack([r*np.cos(th)+s[0],r*np.sin(th)+s[1],h],1)
def res(q):
    s=q[:2];out=[]
    for r,c in ((rin[A],q[2:5]),(rout[A],q[5:8])):
        uv=pr(curve(r,c,s));ok=(uv[:,0]>2)&(uv[:,0]<1997)&(uv[:,1]>2)&(uv[:,1]<1330)
        v=map_coordinates(dt,[uv[:,1],uv[:,0]],order=1,mode='nearest');v[~ok]=0;out.append(np.minimum(v,25))
    return np.concatenate(out)
for fs in ([0,0,25,0,0,23,0,0],[3,0,25,0,0,23,0,0],[-3,3,25,0,0,23,0,0]):
    s=least_squares(res,fs,loss='soft_l1',f_scale=3,diff_step=0.05)
    print(np.round(s.x,2).tolist(),'med',round(float(np.median(s.fun)),2),'mean',round(float(s.fun.mean()),2))
q0=[0,0,*G['hin'],*G['hout']];print('current',round(float(np.median(res(q0))),2),round(float(res(q0).mean()),2))
