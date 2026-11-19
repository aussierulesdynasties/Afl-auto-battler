import json,math,numpy as np,cv2
exec(open('nearsolve.py').read().split('# model')[0])
ph=cv2.imread('photo_clean.png').astype(int);B,G,Rr=ph[...,0],ph[...,1],ph[...,2]
red=(Rr>150)&(G<90)&(B<90);lite=(ph.mean(-1)>195)
def zat(x,y,r):
    # height z on the vertical cylinder of radius r (model plan) seen at photo pixel (x,y)
    best=None
    for a in np.arange(150,200,0.05):
        t=math.radians(a)
        for z in np.arange(5,25,0.25):pass
    return None
# angle and z at wall radius: search over (a,z) grid on the wall surface, nearest projection
A=np.arange(150,205,0.1);Z=np.arange(6,24,0.1)
def wallpt(x,y,rw):
    bestd=1e9;bb=None
    for a in A[::5]:
        t=math.radians(a);P=proj([(rw*math.cos(t)+SH[0],rw*math.sin(t)+SH[1],z) for z in Z[::10]])
        d=np.min(np.hypot(P[:,0]-x,P[:,1]-y))
        if d<bestd:bestd,bb=d,a
    a0=bb;best=(1e9,None,None)
    for a in np.arange(a0-0.6,a0+0.6,0.02):
        t=math.radians(a);P=proj([(rw*math.cos(t)+SH[0],rw*math.sin(t)+SH[1],z) for z in Z]);d=np.hypot(P[:,0]-x,P[:,1]-y);i=np.argmin(d)
        if d[i]<best[0]:best=(d[i],a,Z[i])
    return best[1],best[2]
for x in range(700,960,20):
    col=red[:,x];ys=np.where(col[880:1010])[0]+880
    if not len(ys):print(x,'no red');continue
    rt,rb=ys.min(),ys.max();f=rb+1
    while f<1010 and not lite[f:f+3,x].all():f+=1
    out=[x,rt,rb,f]
    for y in (rt,rb,f):a,z=wallpt(x,y,96.0);out+=[round(a,1),round(z,1)]
    print('x %d red y %d-%d foot y %d | at r96: red top a%.1f z%.1f, red bottom a%.1f z%.1f, foot a%.1f z%.1f'%tuple(out))
