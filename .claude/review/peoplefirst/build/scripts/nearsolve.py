# Near roof outer edge from the photo (director 2026-11-19 via lead: "The photo", smooth edge on the photo's yellow line).
# Per photo column: bottom of the white membrane (first white run below the navy band). Per angle: the radius at the
# roof's outer height hout(a) whose projection through cam_j lands on that edge. Writes geo_n.json and prints residuals.
import json,math,numpy as np,cv2,sys
from scipy.ndimage import median_filter,uniform_filter1d
D=json.load(open('geo_j.json'));p=json.load(open('cam.json'))['p'];SH=D['roofshift']
ph=cv2.imread('photo_clean.png').astype(float);Hi,Wi=ph.shape[:2]
g=ph.mean(-1);sat=ph.max(-1)-ph.min(-1);wh=(g>200)&(sat<45)
def R(yaw,p_,roll):
    cy,sy,cp,sp,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(p_),np.sin(p_),np.cos(roll),np.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f);return np.array([cr*r+sr*u,-sr*r+cr*u,f])
Rm=R(*p[3:6])
def proj(X):d=(np.array(X)-p[:3])@Rm.T;return np.c_[Wi/2+p[6]*d[:,0]/d[:,2],Hi/2-p[6]*d[:,1]/d[:,2]]
def lerp(A,a):f=(a%360)*4;i=int(f)%1440;t=f-int(f);return A[i]*(1-t)+A[(i+1)%1440]*t
def cf(c,a):r=math.radians(a);return c[0]+c[1]*math.cos(r)+c[2]*math.sin(r)
hout=lambda a:cf(D['hout'],a)+lerp(D['hout_dz'],a)
# model's projected outer edge (satellite plan) gives the search start row for each column
E={}
for x in range(420,1481):
    # expected edge row from the current model, then the first white->non-white transition within +-45 px of it
    E[x]=None
A=np.arange(126,252.5,0.05);M=proj([((lerp(D['rout'],a))*math.cos(math.radians(a))+SH[0],(lerp(D['rout'],a))*math.sin(math.radians(a))+SH[1],hout(a)) for a in A])
for x in range(420,1481):
    k=np.where(np.abs(M[:,0]-x)<0.6)[0]
    if not len(k):continue
    v0=int(M[k,1].mean());col=wh[:,x];best=None
    for y in range(max(v0-45,0),min(v0+45,Hi-4)):
        if col[y-6:y].all() and not col[y:y+3].any():best=y;break
    E[x]=best
xs=np.array([x for x in E if E[x]]);ys=np.array([E[x] for x in xs],float)
ys=median_filter(ys,15)   # drop lamp-tower and post outliers
edge=lambda u:np.interp(u,xs,ys,left=np.nan,right=np.nan)
out=[];ang=[]
for a in np.arange(126,252.5,0.25):
    t=math.radians(a);rr=np.arange(lerp(D['rout'],a)-12,lerp(D['rout'],a)+12,0.05)
    P=proj([(r*math.cos(t)+SH[0],r*math.sin(t)+SH[1],hout(a)) for r in rr]);d=P[:,1]-edge(P[:,0])
    s=np.where(np.sign(d[:-1])!=np.sign(d[1:]))[0]
    if len(s) and not np.isnan(d[s[0]]):ang.append(a);out.append(rr[s[0]])
ang=np.array(ang);out=np.array(out);sm=uniform_filter1d(median_filter(out,9),9,mode='nearest')
sat=np.array([lerp(D['rout'],a) for a in ang])
print('solved',len(ang),'angles',ang.min(),'-',ang.max())
for lo in range(int(ang.min()),int(ang.max())+1,8):
    k=(ang>=lo)&(ang<lo+8)
    if k.any():print(f'{lo:3d}-{lo+8:3d} deg  photo-satellite mean {np.mean(sm[k]-sat[k]):+5.2f} m  min {np.min(sm[k]-sat[k]):+5.2f} max {np.max(sm[k]-sat[k]):+5.2f}')
np.save('nearsolve.npy',np.vstack([ang,out,sm,sat]))
