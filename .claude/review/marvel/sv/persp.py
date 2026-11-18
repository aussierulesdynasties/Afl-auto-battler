# Render a flat (rectilinear) view from a stitched equirect panorama.
# python persp.py PANO.jpg OUT.png H P R  view_heading view_pitch fov [w h] [tiltsign]
# H,P,R = pano heading / tilt (90=level) / roll from photometa.
import sys,numpy as np
from PIL import Image
def rot(h,p,r,sg=-1):
    # world (E,N,U) -> pano frame (x fwd, y left, z up)
    h=np.radians(h);t=np.radians((p-90)*sg);r=np.radians(r*sg)
    Rz=np.array([[np.sin(h),np.cos(h),0],[np.cos(h),-np.sin(h),0],[0,0,1]])  # rows: fwd(E,N) , right
    Rz=np.array([[np.sin(h),np.cos(h),0],[-np.cos(h),np.sin(h),0],[0,0,1]])   # fwd, left
    Rt=np.array([[np.cos(t),0,-np.sin(t)],[0,1,0],[np.sin(t),0,np.cos(t)]])
    Rr=np.array([[1,0,0],[0,np.cos(r),-np.sin(r)],[0,np.sin(r),np.cos(r)]])
    return Rr@Rt@Rz
def render(pano,H,P,R,vh,vp,fov,w=1600,h=1200,sg=-1):
    A=np.asarray(pano);PH,PW=A.shape[:2]
    f=w/2/np.tan(np.radians(fov)/2);x,y=np.meshgrid(np.arange(w)-w/2+0.5,np.arange(h)-h/2+0.5)
    hd,pt=np.radians(vh),np.radians(vp)
    fw=np.array([np.sin(hd)*np.cos(pt),np.cos(hd)*np.cos(pt),np.sin(pt)]);rt=np.array([np.cos(hd),-np.sin(hd),0]);up=np.cross(rt,fw)
    d=fw[None,None]*f+x[...,None]*rt+(-y)[...,None]*up;d/=np.linalg.norm(d,axis=-1,keepdims=True)
    c=d@rot(H,P,R,sg).T
    yaw=np.arctan2(-c[...,1],c[...,0]);el=np.arcsin(np.clip(c[...,2],-1,1))
    u=((yaw/(2*np.pi)+0.5)%1)*PW;v=(0.5-el/np.pi)*PH
    u0=np.floor(u).astype(int);v0=np.clip(np.floor(v).astype(int),0,PH-2);fu=(u-u0)[...,None];fv=(v-v0)[...,None]
    u1=(u0+1)%PW;u0%=PW
    o=(A[v0,u0]*(1-fu)*(1-fv)+A[v0,u1]*fu*(1-fv)+A[v0+1,u0]*(1-fu)*fv+A[v0+1,u1]*fu*fv)
    return Image.fromarray(o.astype(np.uint8))
if __name__=='__main__':
    a=sys.argv[1:];im=Image.open(a[0]).convert('RGB')
    H,P,R,vh,vp,fov=map(float,a[2:8]);w,h=(int(a[8]),int(a[9])) if len(a)>9 else (1600,1200);sg=float(a[10]) if len(a)>10 else -1
    render(im,H,P,R,vh,vp,fov,w,h,sg).save(a[1])
