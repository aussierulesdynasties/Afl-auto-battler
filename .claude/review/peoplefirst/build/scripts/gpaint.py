# Hand-painted ground: layout = satellite classes, colours = medians read from the main photo. No photo pixels.
import cv2,numpy as np,json
cls=np.load('g_cls.npy');lines=np.load('g_lines.npy')>0
N=2048;HALF=200.0;ppm=N/(2*HALF);NC=8
ph=cv2.imread('photo_clean.png');Hi,Wi=ph.shape[:2]
al=cv2.imread('render_r5.png',cv2.IMREAD_UNCHANGED)[:,:,3]
p=json.load(open('cam.json'))['p']
def R(yaw,p_,roll):
    cy,sy,cp,sp,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(p_),np.sin(p_),np.cos(roll),np.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f);return np.array([cr*r+sr*u,-sr*r+cr*u,f])
xs=(np.arange(N)+0.5)/ppm-HALF;X,Y=np.meshgrid(xs,-xs)
P3=np.c_[X.ravel(),Y.ravel(),np.zeros(N*N)]
d=(P3-np.array(p[:3]))@R(*p[3:6]).T;ok=d[:,2]>1
u=Wi/2+p[6]*d[:,0]/d[:,2];v=Hi/2-p[6]*d[:,1]/d[:,2]
ui=np.round(u).astype(int);vi=np.round(v).astype(int)
ok&=(ui>=0)&(ui<Wi)&(vi>=0)&(vi<Hi)
ok[ok]&=al[vi[ok],ui[ok]]==0
# erode class masks so samples sit well inside each region (edges mix colours)
cl=cls.ravel();col={};sd={}
for k in range(NC):
    m=cv2.erode((cls==k).astype(np.uint8),np.ones((7,7),np.uint8)).ravel()>0
    s=ok&m&~lines.ravel()
    if s.sum()<50:s=ok&(cl==k)
    px=ph[vi[s],ui[s]].astype(np.float32)
    col[k]=np.median(px,0) if len(px) else np.array([128,128,128.]);sd[k]=float(np.median(np.abs(px-col[k]).mean(1))) if len(px) else 4.0
    print(k,int(s.sum()),col[k].round().tolist(),round(sd[k],1))
lm=ok.reshape(N,N)&cv2.dilate(lines.astype(np.uint8),np.ones((2,2),np.uint8)).astype(bool)
lc=np.median(ph[vi[lm.ravel()],ui[lm.ravel()]],0) if lm.sum()>20 else np.array([235,235,235.])
print('lines',int(lm.sum()),lc.tolist())
# paint at 4096 (10.24 px/m): smooth class boundaries, crisp edges
M=4096;rng=np.random.default_rng(7)
oh=np.stack([cv2.GaussianBlur((cls==k).astype(np.float32),(0,0),1.5) for k in range(NC)],-1)
up=np.stack([cv2.resize(oh[...,k],(M,M),interpolation=cv2.INTER_CUBIC) for k in range(NC)],-1)
C=up.argmax(-1);del up,oh
def vnoise(scale_px,seed):
    g=np.random.default_rng(seed).random((M//scale_px+2,M//scale_px+2)).astype(np.float32)
    return cv2.resize(g,(M+scale_px*2,M+scale_px*2),interpolation=cv2.INTER_CUBIC)[scale_px:scale_px+M,scale_px:scale_px+M]-0.5
fine=vnoise(2,1)*0.6+vnoise(6,2)*0.4;mid=vnoise(24,3);big=vnoise(96,4)
img=np.zeros((M,M,3),np.float32)
for k in range(NC):img[C==k]=col[k]
amp=np.zeros((M,M),np.float32)
for k in range(NC):amp[C==k]=min(sd[k],14)
img+=((fine*0.9+mid*0.5+big*0.4)*amp*1.6)[...,None]
# trees: clumpy canopy - lit crowns and dark gaps from blob noise
T=C==5;blob=cv2.GaussianBlur(vnoise(10,5)+vnoise(4,6)*0.5,(0,0),1.2)
img[T]*=(1+blob[T]*0.9)[:,None]
# water: slow ripple streaks
W=C==6;img[W]+=(vnoise(40,8)*6+vnoise(3,9)*3)[W][:,None]
# crisp lines
L=cv2.resize(lines.astype(np.uint8)*255,(M,M),interpolation=cv2.INTER_LINEAR)>110
img[L]=lc
out=np.clip(img,0,255).astype(np.uint8);cv2.imwrite('htex/ground.png',out)
tj=json.load(open('htex/tex.json'));tj['ground']=[400.0,400.0];json.dump(tj,open('htex/tex.json','w',newline=''))
cv2.imwrite('ground_prev.jpg',cv2.resize(out,(2048,2048)),[cv2.IMWRITE_JPEG_QUALITY,90])
cv2.imwrite('ground_zoom.jpg',out[2400:3200,2600:3400])
