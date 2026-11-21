# Brighton Homes Arena hand repaint (texture pass 2026-11-20). Painted in code, no photo pixels.
import numpy as np
from PIL import Image,ImageFilter
R=np.random.default_rng(7);N=1024
from scipy.ndimage import gaussian_filter
def blur(a,s):return gaussian_filter(a.astype(float),s,mode='wrap') if np.any(np.array(s)>0) else a
def noise(s,amp):g=R.normal(0,1,(N,N));g=blur(g,s);return g/g.std()*amp
def save(n,a):a=np.clip(a,0,255).astype(np.uint8);Image.fromarray(a).save('new/'+n+'.png');print(n,'sd %.1f'%a.mean(2).std())
def src(n):return np.asarray(Image.open('img/'+n+'.png').convert('RGB')).astype(float)
def sheet(n,base,tile,pitch,pan=None,dark=0.80,hi=1.06):
    # trapezoidal sheet: ribs along v every `pitch` m; light on one flank, shade on the other; faint run streaks
    x=(np.arange(N)/N*tile)%pitch/pitch
    prof=np.ones(N);rib=x<0.10;prof[rib]=hi;fl=(x>=0.10)&(x<0.16);prof[fl]=dark;prof[(x>=0.16)&(x<0.22)]=0.93
    st=blur(R.random((N,N))*(R.random((1,N))<0.12),[60,2])
    a=np.ones((N,N,3))*np.array(base,float)*prof[None,:,None]
    a*=(1-0.025*st/ (st.max()+1e-6))[...,None]
    a*=(1+noise(1.0,0.006))[...,None]
    if pan:
        y=(np.arange(N)/N*tile)%pan<0.02;a[y]*=0.93
    return a
save('roof_white_c_roof_white',sheet('',(232,235,234),2.80,0.70))
save('roof_blue_c_roof_blue',sheet('',(86,128,180),2.79,0.70))
save('roof_grey_c_roof_grey',sheet('',(120,134,160),2.79,0.70))
save('roof_c_roof',sheet('',(203,211,225),2.80,0.70))
def even(n,base,tile,jx=None,jy=None,jk=0.88,grain=1.5,tone=0.01,pan=None):
    a=np.ones((N,N,3))*np.array(base,float)
    if pan:
        k=(np.arange(N)/N*tile//pan).astype(int);t=1+R.normal(0,tone,(k.max()+1,k.max()+1))[k[:,None],k[None,:]];a*=t[...,None]
    a+=noise(0.7,grain)[...,None]
    c=np.arange(N)/N*tile
    if jx:a[:,(c%jx)<0.012]*=jk
    if jy:a[(c%jy)<0.012,:]*=jk
    return a
save('concrete_c',even('',(192,190,184),3.0,1.5,1.5,0.90,2.0,0.012,1.5))
save('concrete_dark_c',even('',(86,87,90),3.0,None,None,1,1.6))
save('clad_black_c',even('',(16,16,18),1.0,None,None,1,1.0))
save('copper_frame_c',even('',(122,64,42),1.0,None,None,1,1.4))
save('wall_ws_c',even('',(190,183,184),3.0,1.5,3.0,0.90,1.4,0.01,1.5))
save('paint_white_c',even('',(243,243,238),1.0,None,None,1,1.4))
save('concrete_band_c',even('',(146,150,142),3.0,1.5,None,0.88,1.6))
# grass: QLD couch, even green, fine blade grain, no cloud blotches
def grass(base):
    g=R.normal(0,1,(N,N));bl=g*40
    bl=blur(bl,0.6)
    a=np.ones((N,N,3))*np.array(base,float)*(1+bl[...,None]/128*0.25)
    a*=(1+noise(40,0.02))[...,None]
    return a
save('lawn_c_lawn',grass((92,128,58)))
save('grass_terrace_c',grass((88,132,56)))
save('turf_a_c_turf_00',grass((90,126,54)))
