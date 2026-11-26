import json,numpy as np
from PIL import Image
from scipy import ndimage
cal=json.load(open('calib_top.json'));HC=905.4;W,H=1280,720
U=np.array([0.33632,-0.94215]);V=np.array([-0.94215,-0.33632]);C=np.array([2.315119484644029,0.6397467287638265])
def P(u,v,z):
    E=C[0]+u*U[0]+v*V[0];N=C[1]+u*U[1]+v*V[1];k=HC/(HC-z);E*=k;N*=k;c,s=np.cos(cal['th']),np.sin(cal['th'])
    return np.array([W/2+cal['tx']+(c*E-s*N)/cal['mpp'], H/2+cal['ty']-(s*E+c*N)/cal['mpp']])
im=np.asarray(Image.open('/tmp/claude-0/ref/geA/ge_top.png').convert('RGB'),float);lum=ndimage.gaussian_filter(im.mean(2),1.0)
z=38.0;mpp=cal['mpp']*(HC-z)/HC
edges={'W inner (v=48.8)':[((u,48.8),(0,1)) for u in np.arange(-78,78,1.0)],'E inner (v=-52.2)':[((u,-52.2),(0,-1)) for u in np.arange(-78,78,1.0)],
       'N inner (u=-84)':[((-84.0,v),(-1,0)) for v in np.arange(-46,46,1.0)],'S inner (u=84)':[((84.0,v),(1,0)) for v in np.arange(-46,46,1.0)]}
for nm,L in edges.items():
    d=[]
    for (u,v),(du,dv) in L:
        ks=np.arange(-6,6.01,0.25);pts=np.array([P(u+du*k,v+dv*k,z) for k in ks])
        if pts[:,1].min()<62:continue
        prof=ndimage.map_coordinates(lum,[pts[:,1],pts[:,0]],order=1);g=np.gradient(prof)  # dark opening -> bright roof going outward: g>0
        pk=[i for i in range(1,len(g)-1) if g[i]>=g[i-1] and g[i]>=g[i+1] and g[i]>8 and prof[min(i+6,len(g)-1)]>150 and prof[max(i-6,0)]<prof[min(i+6,len(g)-1)]-40]
        if pk:j=min(pk,key=lambda i:abs(ks[i]));d.append(ks[j])
    d=np.array(d);print('%-18s n=%3d median %+.2f m (+ = Google Earth edge further out, into the roof)  |d|<=1 %3.0f%%'%(nm,len(d),np.median(d),100*np.mean(np.abs(d)<=1)))
