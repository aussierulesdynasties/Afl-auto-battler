# Hand-made plaza ground over the whole apron (world UV). o2 is read only for the LAYOUT: at each ground point the
# photo pixel is classed as paving / tan path / lawn (by hue, so sun and shade don't matter); points the photo can't
# see default to paving. Each class is then filled with a hand-made texture. Writes tex/ground.png + info ground_box.
import numpy as np,json,math,os
from PIL import Image,ImageFilter
H_=os.path.dirname(os.path.abspath(__file__));T=os.path.join(H_,'tex');RNG=np.random.default_rng(3)
J=json.load(open(os.path.join(H_,'geom.json')));P=json.load(open(os.path.join(H_,'cam7.json')))['p']
O=np.asarray(Image.open(os.path.join(H_,'photo.jpg')).convert('RGB')).astype(float)
POD=np.array(J['pod']);DR=np.array(J['drum']);PC=POD.mean(0)
R=np.linalg.norm(POD-PC,axis=1).max()+46;x0,y0=PC-R;span=2*R
S=6144;PXM=S/span;print('px/m',PXM)
def pnoise(h,w,scale):
    z=RNG.standard_normal((h,w));F=np.fft.fft2(z);ky=np.fft.fftfreq(h)[:,None];kx=np.fft.fftfreq(w)[None,:]
    F*=np.exp(-((kx**2+ky**2)*scale**2)*4);r=np.real(np.fft.ifft2(F));return ((r-r.mean())/(r.std()+1e-9)).astype(np.float32)
# --- layout from o2 on a coarse 0.5 m grid
G=int(span/0.5);gy,gx=np.mgrid[0:G,0:G];X=x0+(gx+0.5)*0.5;Y=y0+(G-1-gy+0.5)*0.5
yw,pi,ro=P[3],P[4],P[5];f=np.array([math.cos(yw)*math.cos(pi),math.sin(yw)*math.cos(pi),math.sin(pi)]);r=np.array([math.sin(yw),-math.cos(yw),0]);u=np.cross(r,f)
R0=math.cos(ro)*r+math.sin(ro)*u;R1=-math.sin(ro)*r+math.cos(ro)*u;C=np.array(P[:3])
d=np.stack([X-C[0],Y-C[1],-C[2]*np.ones_like(X)],-1);z=d@f;px=P[7]+P[6]*(d@R0)/z;py=P[8]-P[6]*(d@R1)/z
inf=(px>=0)&(px<1920)&(py>=0)&(py<1079)
from matplotlib.path import Path
pp=Path(POD);pd=Path(DR);vis=inf.copy()
PB=[Path(np.array(J['bld'][k])[:,:2]) for k in ('near','far')]   # pavilions (not modelled) hide ground and show roof colour
for t in np.linspace(0.02,0.98,40):                     # line of sight blocked by the podium (6.4 m) or the drum/roof (34 m)
    q=np.stack([X,Y,np.zeros_like(X)],-1)*(1-t)+C*t;qz=q[...,2];flat=q[...,:2].reshape(-1,2)
    blk=((qz<6.4)&pp.contains_points(flat).reshape(X.shape))|((qz<34.5)&pd.contains_points(flat).reshape(X.shape))
    for pb in PB:blk|=(qz<9.2)&pb.contains_points(flat).reshape(X.shape)
    vis&=~blk
ix=np.clip(px.astype(int),0,1919);iy=np.clip(py.astype(int),0,1078);c=O[iy,ix];s=c.sum(-1)+1
rb=(c[...,0]-c[...,2])/s*3;gr=(c[...,1]-c[...,0])/s*3
lawn=vis&(gr>0.03);path=vis&(rb>0.45)&~lawn
inpod=pp.contains_points(np.stack([X,Y],-1).reshape(-1,2)).reshape(X.shape);lawn&=~inpod;path&=~inpod
for pb in PB:
    ib=pb.contains_points(np.stack([X,Y],-1).reshape(-1,2)).reshape(X.shape);lawn&=~ib;path&=~ib
from scipy import ndimage as nd
def sm(b,sig,minarea):                                   # smooth outline (blur+threshold), fill holes, drop specks
    m=nd.gaussian_filter(b.astype(np.float32),sig)>0.5;m=nd.binary_fill_holes(nd.binary_closing(m,iterations=3))
    lab,n=nd.label(m);sz=nd.sum(m,lab,range(1,n+1));keep=np.zeros(n+1,bool);keep[1:]=sz>=minarea;return keep[lab]
lawn=sm(lawn,3.0,400);path=sm(path,2.0,160)&~lawn
def up(b):return np.asarray(Image.fromarray((b*255).astype(np.uint8)).resize((S,S),Image.BILINEAR).filter(ImageFilter.GaussianBlur(2)))>127
L=up(lawn);Pm=up(path)
# --- hand-made fills
a=np.empty((S,S,3),np.float32);a[:]=(195,175,155)
a*=(1+pnoise(S,S,0.5)*0.045+pnoise(S,S,80)*0.02)[...,None]
spk=RNG.random((S,S))<0.03;a[spk]=(150,138,122)
step=int(round(2.0*PXM))
for k in range(0,S,step):a[:,k:k+1]*=0.92;a[k:k+1,:]*=0.92           # saw-cut joints every 2 m
tan=np.empty_like(a);tan[:]=(200,150,104);tan*=(1+pnoise(S,S,0.5)*0.06)[...,None];a[Pm]=tan[Pm]
gr_=np.empty_like(a);gr_[:]=(112,140,58);gr_*=(1+pnoise(S,S,0.6)*0.07+pnoise(S,S,60)*0.04)[...,None];a[L]=gr_[L]
Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(os.path.join(T,'ground.png'))
I=json.load(open(os.path.join(T,'info.json')));I['ground_box']=[float(x0),float(y0),float(span)];json.dump(I,open(os.path.join(T,'info.json'),'w',newline=''))
print('ground ok',x0,y0,span,'lawn',L.mean(),'path',Pm.mean())
