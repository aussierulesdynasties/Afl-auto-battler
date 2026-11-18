import cv2,numpy as np,json,math
D=json.load(open('geo_build.json'));p=json.load(open('cam.json'))['p']
ph=cv2.imread('photo_clean.png');Hi,Wi=ph.shape[:2];hsv=cv2.cvtColor(ph,cv2.COLOR_BGR2HSV).astype(float)
RG=np.array(D['RG'])
def rg(a):f=(a%360)*4;i=int(f)%1440;t=f-int(f);return RG[i]*(1-t)+RG[(i+1)%1440]*t
def R(yaw,p_,roll):
    cy,sy,cp,sp,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(p_),np.sin(p_),np.cos(roll),np.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f);return np.array([cr*r+sr*u,-sr*r+cr*u,f])
Rm=R(*p[3:6])
def proj(X):
    d=(np.array(X)-p[:3])@Rm.T;return np.c_[Wi/2+p[6]*d[:,0]/d[:,2],Hi/2-p[6]*d[:,1]/d[:,2]]
def tier(d0,z0,d1,z1,n=7):
    A=np.arange(0,360,0.05);S=[];U=[]
    for k in range(n):
        s=(k+0.5)/n;d=d0+(d1-d0)*s;z=z0+(z1-z0)*s
        X=[(( rg(a)+d)*math.cos(math.radians(a)),(rg(a)+d)*math.sin(math.radians(a)),z) for a in A]
        uv=proj(X);U.append(uv);x=np.clip(uv[:,0].round().astype(int),0,Wi-1);y=np.clip(uv[:,1].round().astype(int),0,Hi-1)
        S.append(hsv[y,x,1])
    return A,np.array(S),U
for nm,(d0,z0,d1,z1) in {'low':(1.5,1.0,6.5,4.0),'up':(8.5,6.0,18.0,12.7)}.items():
    A,S,U=tier(d0,z0,d1,z1);np.save('ais_%s.npy'%nm,S)
    ov=ph.copy()
    for uv in U[::3]:
        for i in range(0,len(A),20):
            x,y=uv[i];cv2.circle(ov,(int(x),int(y)),1,(255,255,0) if (A[i]%10)<0.06 else (0,255,0),-1)
            if abs(A[i]%10)<0.06 and uv is U[0]:cv2.putText(ov,str(int(A[i])),(int(x),int(y)+12),0,0.4,(255,255,0),1)
    cv2.imwrite('ais_%s.jpg'%nm,ov)
