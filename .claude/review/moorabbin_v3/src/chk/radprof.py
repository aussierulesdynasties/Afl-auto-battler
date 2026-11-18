import json,math,numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates,gaussian_filter1d
exec(open('chk/ringover.py').read().split("cam=np.array")[0])
cam=np.array(O['cam'])
I=np.asarray(Image.open('A.jpg').convert('L')).astype(float)
out={}
for deg in [-90,-75,-60,-45,-30,-15,0,15,30,45,60,75]:
    a0=math.radians(deg);prof=[]
    for da in np.linspace(-4,4,9):   # average across 9 nearby radials
        a=a0+math.radians(da);do=d_out(a)
        ds=np.linspace(0.3,do,300);X=np.array([pt(a,d,0) for d in ds]);q=proj(cam,X)
        prof.append(map_coordinates(I,[q[:,1],q[:,0]],order=1))
    pr=np.mean(prof,0);hp=pr-gaussian_filter1d(pr,12)
    # count local minima stronger than noise
    mins=[i for i in range(2,len(hp)-2) if hp[i]<hp[i-1] and hp[i]<hp[i+1] and hp[i]<-1.0]
    do=d_out(a0);px=np.hypot(*(proj(cam,np.array([pt(a0,0.3,0)]))[0]-proj(cam,np.array([pt(a0,do,0)]))[0]))
    out[deg]=(round(do,1),round(px,1),[round(0.3+(do-0.3)*i/299,1) for i in mins])
    print(deg,'depth m',round(do,1),'image px',round(px,1),'dark lines at m:',out[deg][2])
