import numpy as np,json,cv2
from scipy.ndimage import median_filter,uniform_filter1d
from scipy.signal import find_peaks
P=np.load('polar.npy');N=1440;deg=np.arange(N)/4
RG=np.load('grass_polar.npy')  # indexed from -180
RG=np.roll(RG,-720)            # now indexed from 0 deg
span=(deg>=104)|(deg<=37)
def clean(v,k):
    v=v.copy();v[~span]=np.nan
    good=~np.isnan(v);i=np.arange(N)
    v=np.interp(i,i[good],v[good],period=N);v=median_filter(v,k,mode='wrap');return v
rin=uniform_filter1d(clean(P[:,0],41),41,mode='wrap');rout=clean(P[:,1],9)
# heights: cosine fits through measured sector values
def cfit(pts):
    A=np.array([[1,np.cos(np.radians(a)),np.sin(np.radians(a))] for a,_ in pts]);b=np.array([h for _,h in pts])
    c=np.linalg.lstsq(A,b,rcond=None)[0];return [float(x) for x in c]
hin=[23.9,-1.3,-0.26];hout=[23.07,-2.58,-0.53]  # rooffit.py: fitted to the photo roof outline
# scallop panels from outer-edge peaks inside the span
o=np.concatenate([rout[416:],rout[:150]]);d=np.concatenate([deg[416:],deg[:150]+360])
pk,_=find_peaks(uniform_filter1d(o,5),distance=12,prominence=1.0);vl,_=find_peaks(-uniform_filter1d(o,5),distance=12,prominence=1.0)
print('peaks',len(pk),np.round(d[pk]%360,1));print('valleys',len(vl))
J=dict(roofshift=[1.04,-2.48],RG=RG.tolist(),rin=rin.tolist(),rout=rout.tolist(),hin=hin,hout=hout,a0=124.0,a1=37.0+360,
 valleys=[float(x) for x in d[vl]],
 towers=[[93.8,72.4,65.5],[92.3,-36.1,69.1],[-26.8,112.5,70.3],[38.8,-123.7,63.8],[-92.8,36.1,65.4],[-90.7,-78.7,70.1]],
 scoreboard=[[27.5,104.3],[55.8,95.3],4.0,14.6])
json.dump(J,open('geo_build.json','w'))
print('hin',np.round(hin,2),'hout',np.round(hout,2))
# ground texture: sat crop +-200m, roof pixels -> paving
S=json.load(open('sat.json'));m=S['mpp'];im=cv2.imread('sat.png');mk=cv2.imread('roof_mask.png',0)
mk=cv2.dilate(mk,np.ones((9,9),np.uint8))
pave=np.median(im[(mk==0)].reshape(-1,3)[::50],0);fill=cv2.inpaint(im,mk,7,cv2.INPAINT_TELEA)
R=200;x0=int(S['px']-R/m);y0=int(S['py']-R/m);x1=int(S['px']+R/m);y1=int(S['py']+R/m)
print('crop',x0,y0,x1,y1,im.shape)
c=np.full((y1-y0,x1-x0,3),pave,np.uint8);sx0,sy0=max(x0,0),max(y0,0);sx1,sy1=min(x1,im.shape[1]),min(y1,im.shape[0])
c[sy0-y0:sy1-y0,sx0-x0:sx1-x0]=fill[sy0:sy1,sx0:sx1]
cv2.imwrite('tex/ground.png',cv2.resize(c,(2048,2048),interpolation=cv2.INTER_AREA))
