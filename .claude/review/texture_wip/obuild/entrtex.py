# Hand-made glazed entrance storey for the podium sides o2 cannot see (section from close-ups 092 and 192:
# doors 0-4.2 m, grey metal panel band 4.2-5.85 m, clerestory 5.85-7.0 m; glass modules ~2.4 m).
# One bay wide (14.52 m) x 7.0 m, 100 px/m, v=0 at the plaza. Also writes 'column' (white render).
import numpy as np,json,os
from PIL import Image
T=os.path.join(os.path.dirname(os.path.abspath(__file__)),'tex');RNG=np.random.default_rng(11)
def pnoise(h,w,scale):
    z=RNG.standard_normal((h,w));F=np.fft.fft2(z);ky=np.fft.fftfreq(h)[:,None];kx=np.fft.fftfreq(w)[None,:]
    F*=np.exp(-((kx**2+ky**2)*scale**2)*4);r=np.real(np.fft.ifft2(F));return (r-r.mean())/(r.std()+1e-9)
PM=100;BAY=755.1/52;W=int(round(BAY*PM));H=int(7.0*PM);M=W/6
a=np.zeros((H,W,3),np.float32)
z=(H-1-np.arange(H))/PM                                   # metres above the plaza for each row
def rows(z0,z1):return slice(int(H-z1*PM),int(H-z0*PM))
FR=np.array((118,120,122),np.float32)                     # anodised grey frames
# doors / fixed glass 0-4.2 m: sky reflection at the top fading into the lit concourse, plaza reflected low down
g=rows(0,4.2);zz=z[g][:,None,None]
sky=np.array((176,190,198),np.float32);inside=np.array((112,108,100),np.float32);low=np.array((150,146,140),np.float32)
t=np.clip((zz-1.4)/2.8,0,1);a[g]=inside*(1-t)+sky*t
a[rows(0,0.9)]=low*0.85+a[rows(0,0.9)]*0.15
a[rows(1.05,1.12)]=(226,228,228)                          # handrail line seen through the glass
xx=np.arange(W)[None,:]                                 # crisp diagonal sky-reflection bands, no mottling
band=((xx*0.55+np.arange(H)[:,None])%380<70)&(z[:,None]>1.4)&(z[:,None]<4.2);a[band]*=1.07
for k in range(6):
    x0=int(k*M);x1=int((k+1)*M)
    a[g,x0:x0+8]=FR;a[g,x1-8:x1]=FR                       # mullions
    if k in (1,4):                                        # door pair: centre stiles, push bars, thresholds
        xc=(x0+x1)//2;a[g,xc-7:xc+7]=FR*0.92
        a[rows(1.0,1.06),x0+20:x1-20]=(205,207,208)
        a[rows(0,0.05),x0:x1]=(90,90,92)
a[rows(4.12,4.2)]=FR*0.8                                  # head transom
# grey metal panel band 4.2-5.85 m: one panel per module, fine joints
g=rows(4.2,5.85);a[g]=(104,102,101);a[g]*=(1+pnoise(H,W,3)[g][...,None]*0.008)
for k in range(7):x=int(k*M);a[g,max(0,x-3):x+3]=(66,65,66)
a[rows(5.85,5.92)]=FR*0.75
# clerestory 5.92-7.0 m: dark interior with ceiling lights, frames
g=rows(5.92,7.0);a[g]=(58,64,67);
lr=rows(6.35,6.45)
for k in range(6):
    x0=int(k*M);a[g,x0:x0+7]=FR
    for xl in (x0+int(M*0.3),x0+int(M*0.7)):a[lr,xl-12:xl+12]=(236,236,228)
a[rows(6.94,7.0)]=FR*0.7
Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(os.path.join(T,'entrance.png'))
c=np.ones((256,256,3),np.float32)*(236,236,233);c*=(1+pnoise(256,256,6)[...,None]*0.015)
Image.fromarray(np.clip(c,0,255).astype(np.uint8)).save(os.path.join(T,'column.png'))
I=json.load(open(os.path.join(T,'info.json')));I['entrance_bay_m']=BAY;I['entrance_h_m']=7.0
json.dump(I,open(os.path.join(T,'info.json'),'w',newline=''));print('entrance ok',W,H)
