# project the cleaned photos onto the baked atlas where their camera sees a face well; the rest keeps the lit close-up bake
import os
os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
import cv2,numpy as np,json,sys
pos=np.load('bake_pos.npy')[...,:3].astype(np.float64)
nrm=np.load('bake_nrm.npy')[...,:3].astype(np.float64)
lit=cv2.imread('bake_lit.png').astype(np.float32)
H,W=pos.shape[:2]
valid=np.linalg.norm(nrm,axis=2)>0.1
nrm=nrm*2-1
CAMS=json.load(open('cams.json'))  # [{"img":..., "p":[...], "w":2000,"h":1333}]
def R(yaw,p_,roll):
    cy,sy,cp,sp,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(p_),np.sin(p_),np.cos(roll),np.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
P=pos[valid];N=nrm[valid];N/=np.linalg.norm(N,axis=1,keepdims=True)
best_w=np.zeros(len(P));best_c=np.zeros((len(P),3),np.float32)
for cam in CAMS:
    p=cam['p'];Wi,Hi=cam['w'],cam['h'];img=cv2.imread(cam['img']).astype(np.float32)
    M=R(*p[3:6]);d=(P-np.array(p[:3]))@M.T
    z=d[:,2];u=Wi/2+p[6]*d[:,0]/z;v=Hi/2-p[6]*d[:,1]/z
    ins=(z>1)&(u>=0)&(u<Wi-1)&(v>=0)&(v<Hi-1)
    dist=np.linalg.norm(P-np.array(p[:3]),axis=1)
    # z-buffer from the texels themselves
    S=2;iu=np.clip((u*S).astype(int),0,Wi*S-1);iv=np.clip((v*S).astype(int),0,Hi*S-1)
    zb=np.full(Hi*S*Wi*S,np.inf);idx=iv*Wi*S+iu
    np.minimum.at(zb,idx[ins],dist[ins])
    zb=zb.reshape(Hi*S,Wi*S).astype(np.float32);ze=cv2.erode(zb,np.ones((3,3),np.uint8));zb=np.where(np.isinf(zb),ze,zb)  # fill empty pixels only
    vis=ins&(dist<=zb[iv,iu]+0.8+0.004*dist)
    view=(np.array(p[:3])-P)/dist[:,None];cs=np.abs((N*view).sum(1))
    ppm=p[6]/dist
    w=vis*np.clip((cs-0.08)/0.22,0,1)*np.clip(ppm/4.0,0,1.5)*cam.get('prio',1.0)
    uu=np.clip(u,0,Wi-1.001);vv=np.clip(v,0,Hi-1.001);x0=uu.astype(int);y0=vv.astype(int);fx=(uu-x0)[:,None];fy=(vv-y0)[:,None]
    col=(img[y0,x0]*(1-fx)*(1-fy)+img[y0,x0+1]*fx*(1-fy)+img[y0+1,x0]*(1-fx)*fy+img[y0+1,x0+1]*fx*fy)
    take=w>best_w;best_w[take]=w[take];best_c[take]=col[take]
    print(cam['img'],'visible texels',int(vis.sum()),'used',int(take.sum()))
out=lit.copy();L=lit[valid]
a=np.clip(best_w,0,1)[:,None]
out[valid]=L*(1-a)+best_c*a
cv2.imwrite('atlas.png',np.clip(out,0,255).astype(np.uint8))
wm=np.zeros((H,W),np.float32);wm[valid]=best_w;cv2.imwrite('atlas_w.png',(np.clip(wm,0,1)*255).astype(np.uint8))
print('photo-covered share of texels',float((best_w>0.5).mean()))
