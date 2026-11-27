# lid.py: Sky Stadium from LINZ 1 m DSM (Wellington 2013-2014): field level, field edge (first rise of 0.8 m), roof inner edge and heights per bearing
import numpy as np,json
d=np.load('dsm_1m.npy');d[d<-100]=np.nan;N=d.shape[0]
# array row 0 = north; x east. centre guess = array centre
f=np.nanmedian(d[180:220,180:220]);print('field level %.2f m'%f)
# refine centre: centroid of the low field region connected to centre
low=(d<f+0.5);import scipy.ndimage as nd
lab,_=nd.label(low);m=lab==lab[200,200];yy,xx=np.nonzero(m);cy,cx=yy.mean(),xx.mean();print('field region centroid px',cx,cy,'area m2',m.sum())
out=[]
for b in range(0,360,2):
    t=np.radians(b);r=np.arange(20,180,0.5);xs=cx+r*np.cos(t);ys=cy-r*np.sin(t)
    v=nd.map_coordinates(np.nan_to_num(d,nan=-99),[ys,xs],order=1)
    i=np.argmax(v>f+0.8);re=r[i]
    j=np.argmax(v>f+15);rr=r[j];k=len(v)-1-np.argmax(v[::-1]>f+15);ro=r[k]
    roof=v[(r>=rr)&(r<=ro)]
    out.append(dict(b=b,edge=float(re),roof_in=float(rr),roof_out=float(ro),roof_in_h=float(np.median(v[j:j+3])-f),roof_max_h=float(roof.max()-f) if len(roof) else None,roof_out_h=float(np.median(v[k-3:k+1])-f)))
json.dump(dict(field_level=float(f),centre_px=[float(cx),float(cy)],rays=out),open('lidar_profile.json','w'),indent=0)
E=np.array([[o['b'],o['edge']] for o in out]);x=E[:,1]*np.cos(np.radians(E[:,0]));y=E[:,1]*np.sin(np.radians(E[:,0]))
best=(0,0)
for th in np.arange(0,180,0.5):
    tt=np.radians(th);u=x*np.cos(tt)+y*np.sin(tt);best=max(best,(u.max()-u.min(),th))
tt=np.radians(best[1]);v=-x*np.sin(tt)+y*np.cos(tt);print('field edge long %.1f axis %.1f wide %.1f'%(best[0],best[1],v.max()-v.min()))
for o in out[::10]: print(o)
