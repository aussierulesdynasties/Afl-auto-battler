# Solve a GE capture's camera (C, yaw, pitch, roll; F fixed) from the painted field lines (z=0).
import sys,json,math,os,numpy as np
TH=float(os.environ.get('TH','9'))
from PIL import Image,ImageDraw
from scipy import ndimage as nd
from scipy.optimize import least_squares
sys.path.insert(0,'ob'); import cam
F=cam.F
BL=[-1.28,-3.71,69.9,82.7,29.12]
def lines():
    cx,cy,a,b,r=BL; r=math.radians(r); ua=np.array([math.cos(r),math.sin(r)]); ub=np.array([-math.sin(r),math.cos(r)]); c=np.array([cx,cy])
    t=np.linspace(0,2*np.pi,1440); P=[c+np.outer(a*np.cos(t),ua)+np.outer(b*np.sin(t),ub)]
    def inside(Q): q=Q-c; return (q@ua/a)**2+(q@ub/b)**2<0.995
    for s in (1,-1):
        G=c+s*b*ub; t=np.linspace(0,2*np.pi,1440); Q=G+50*np.stack([np.cos(t),np.sin(t)],1); P.append(Q[inside(Q)])
    s=np.linspace(-25,25,200)
    for k in (-25,25): P.append(c+np.outer(s,ua)+k*ub); P.append(c+k*ua+np.outer(s,ub))
    for rr in (5,): t=np.linspace(0,2*np.pi,200); P.append(c+rr*np.stack([np.cos(t),np.sin(t)],1))
    P=np.concatenate(P); return np.c_[P,np.zeros(len(P))]
L=lines()
def R_of(yaw,pitch,roll):
    f=np.array([math.sin(yaw)*math.cos(pitch), math.cos(yaw)*math.cos(pitch), math.sin(pitch)])
    r=np.cross(f,[0,0,1.0]); r/=np.linalg.norm(r); up=np.cross(r,f)
    cr,sr=math.cos(roll),math.sin(roll); r2=cr*r+sr*up; u2=-sr*r+cr*up; return f,r2,u2
def proj(p,P):
    C=p[:3]; f,r,u=R_of(*p[3:6]); Q=P-C; z=Q@f
    return np.stack([640+F*(Q@r)/z, 360-F*(Q@u)/z],1), z
def init(v):
    C,T=cam.pose(v); d=T-C; d/=np.linalg.norm(d)
    return np.r_[C, math.atan2(d[0],d[1]), math.asin(d[2]), 0.0]
def ridge(im):
    g=np.asarray(im.convert('L'),float); hsv=np.asarray(im.convert('HSV'),float)
    a=np.asarray(im,float); green=(a[...,1]>a[...,0]+2)&(a[...,1]>a[...,2]+5)
    bl=a[...,2]; th=bl-nd.grey_opening(bl,size=(7,7)); m=(th>TH)
    near=nd.binary_dilation(green,iterations=6)&(nd.uniform_filter(green.astype(float),25)>0.6)
    m&=near; m[:60]=False
    return m
def solve(name,v,out):
    im=Image.open(f'of/ge/{name}.png').convert('RGB'); m=ridge(im)
    dt,ind=nd.distance_transform_edt(~m,return_indices=True)
    p0=init(v); uv0,z0=proj(p0,L); vis=(z0>0)&(uv0[:,0]>20)&(uv0[:,0]<1260)&(uv0[:,1]>80)&(uv0[:,1]<700)
    def res(p,cap):
        uv,z=proj(p,L); ok=(z>0)&(uv[:,0]>2)&(uv[:,0]<1277)&(uv[:,1]>62)&(uv[:,1]<717)
        dd=nd.map_coordinates(dt,[np.clip(uv[:,1],0,719),np.clip(uv[:,0],0,1279)],order=1)
        r=np.where(ok, np.minimum(dd,cap), cap); return r[vis]
    p=p0
    for cap in (60,25,10,5):
        sol=least_squares(lambda q:res(q,cap),p,loss='soft_l1',f_scale=cap/3,x_scale=[1,1,1,.01,.01,.01],diff_step=[2e-3]*3+[2e-4]*3)
        p=sol.x
    uv,z=proj(p,L); ok=(z>0)&(uv[:,0]>2)&(uv[:,0]<1277)&(uv[:,1]>62)&(uv[:,1]<717)
    i=uv[ok,1].round().astype(int); j=uv[ok,0].round().astype(int); d=dt[i,j]
    inl=d<3
    print(name,'pts',ok.sum(),'inliers %.0f%%'%(100*inl.mean()),'rms(inl) %.2f px'%np.sqrt((d[inl]**2).mean()),'median %.2f'%np.median(d),
          'dC',np.round(p[:3]-p0[:3],1),'dang deg',np.round(np.degrees(p[3:]-p0[3:]),2))
    o=im.copy(); dr=ImageDraw.Draw(o)
    a=np.asarray(o).copy(); a[m]=[255,0,255]; o=Image.fromarray(a); dr=ImageDraw.Draw(o)
    for q in uv[ok]: dr.point(tuple(q),fill=(0,255,255))
    o.save(out); return p
if __name__=='__main__':
    V={v['name']:v for v in json.load(open(sys.argv[1]))}; S={}
    for k in sys.argv[2:]: S[k]=list(map(float,solve(k,V[k],f'of/{k}_sol.png')))
    json.dump(S,open('of/solved.json','w'),indent=1)
