exec(open('fence.py',encoding='utf-8').read().split('#MAIN')[0])
import json
from PIL import Image
CQ=np.array(json.load(open('camr6.json'))['q']);W,H=1023,576
def R(yaw,pit,rol):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pit),math.sin(pit);cr,sr=math.cos(rol),math.sin(rol)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(X,p=CQ):
    X=np.atleast_2d(X);d=(X-p[:3])@R(*p[3:6]).T
    return np.stack([W/2+p[7]+p[6]*d[:,0]/d[:,2],H/2+p[8]-p[6]*d[:,1]/d[:,2]],1)
PH=np.asarray(Image.open('ref.jpg').convert('RGB')).astype(float)
RN=np.asarray(Image.open('out/render.png').convert('RGBA').resize((W,H),Image.LANCZOS)).astype(float)
def samp(img,pts):
    pts=np.round(pts).astype(int);ok=(pts[:,0]>=0)&(pts[:,0]<W)&(pts[:,1]>=0)&(pts[:,1]<H)
    return img[pts[ok,1],pts[ok,0]]
