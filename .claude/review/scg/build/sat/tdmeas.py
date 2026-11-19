# top-down check: model edges vs satellite edges per half degree (same world grid, north up). Prints stats in metres.
import numpy as np,cv2,json
exec(open('sat/trace.py').read().split("sat=cv2.imread")[0])   # polar()
T=json.load(open('sat/trace.json'))
t=cv2.imread('sat/top.png',cv2.IMREAD_UNCHANGED);hsv=cv2.cvtColor(t[:,:,:3],cv2.COLOR_BGR2HSV);al=t[:,:,3]>10
white=((hsv[...,2]>185)&(hsv[...,1]<45)&al).astype(np.uint8);white=cv2.morphologyEx(white,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
wp,Rr=polar(white*255);ap,_=polar(al.astype(np.uint8)*255)
res={'roof_in':[],'roof_out':[],'outer':[],'fence':[]}
for i in range(720):
    w=np.where(wp[:,i]>0)[0];a=np.where(ap[:,i]>0)[0]
    if T['wout'][i] and len(w):
        w=w[Rr[w]>60]
        if len(w):
            runs=np.split(w,np.where(np.diff(w)>8)[0]+1);r0=runs[0] if len(runs[0])>40 else max(runs,key=len)
            res['roof_in'].append((i/2,Rr[r0[0]]-T['win'][i]));res['roof_out'].append((i/2,Rr[r0[-1]]-T['wout'][i]))
    if len(a) and T['grass'][i]:res['fence'].append((i/2,Rr[a[0]]-T['grass'][i]))
for k,v in res.items():
    if not v:continue
    d=np.array([x[1] for x in v]);ad=np.abs(d)
    print('%-9s n=%3d  median|d| %.2f m  p90 %.2f m  within2m %.0f%%  worst %+.1f at %.1f deg'%(k,len(d),np.median(ad),np.percentile(ad,90),100*np.mean(ad<=2),d[ad.argmax()],v[ad.argmax()][0]))
    bad=[(a,round(x,1)) for a,x in v if abs(x)>2];print('   >2 m:',len(bad),bad[:40])
# outer silhouette: model's outermost solid run (alpha, closed to drop thin gaps; isolated boxes beyond a 3 m gap ignored) vs the satellite's white-roof outer edge
alc=cv2.morphologyEx(al.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((7,7),np.uint8));apc,_=polar(alc*255)
d=[]
for i in range(720):
    if not T['wout'][i]:continue
    a=np.where(apc[:,i]>0)[0];a=a[Rr[a]>60]
    if not len(a):continue
    runs=np.split(a,np.where(np.diff(a)>12)[0]+1);r=Rr[runs[0][-1]];d.append((i/2,r-T['wout'][i]))
v=np.array([x[1] for x in d]);av=np.abs(v)
print('OUTER n=%d median|d| %.2f m  within 2 m %.0f%%  within 3 m %.0f%%'%(len(v),np.median(av),100*np.mean(av<=2),100*np.mean(av<=3)))
import itertools
bad=[x for x in d if abs(x[1])>2]
for k,g in itertools.groupby(bad,key=lambda x:int(x[0]//5)):g=list(g);print('  %5.1f-%5.1f deg  n%2d  mean %+.1f'%(g[0][0],g[-1][0],len(g),np.mean([x[1] for x in g])))
