import json,sys,numpy as np,cv2
s=float(sys.argv[1]);K=int(sys.argv[2]);fs=sys.argv[3:]
def B(a,K):
    t=np.radians(a);return np.column_stack([np.ones_like(t)]+[q(k*t) for k in range(1,K+1) for q in (np.cos,np.sin)])
A=[];R=[]
for f in fs:
    j=json.load(open(f));cx,cy=j['cx'],j['cy']
    for a,r,k in j['pts']:
        if k: A.append(a);R.append(r)
A=np.array(A);R=np.array(R);keep=np.ones(len(A),bool)
for it in range(8):
    c,*_=np.linalg.lstsq(B(A[keep],K),R[keep],rcond=None);res=R-B(A,K)@c;sd=1.4826*np.median(np.abs(res[keep]));keep=np.abs(res)<max(2.5*sd,1)
print('kept %d/%d rms px %.2f m %.2f'%(keep.sum(),len(A),np.sqrt((res[keep]**2).mean()),s*np.sqrt((res[keep]**2).mean())))
for a0 in range(0,360,45):
    m=(A>=a0)&(A<a0+45);print(' sector',a0,'kept %d/%d'%((keep&m).sum(),m.sum()),'mean res px %.1f'%res[m&keep].mean())
a=np.arange(0,360,0.1);r=B(a,K)@c;x=r*np.cos(np.radians(a));y=r*np.sin(np.radians(a));best=(0,0)
for th in np.arange(0,180,0.1):
    u=x*np.cos(np.radians(th))+y*np.sin(np.radians(th));L=u.max()-u.min()
    if L>best[0]:best=(L,th)
th=best[1];v=-x*np.sin(np.radians(th))+y*np.cos(np.radians(th))
print('long %.1f m wide %.1f m axis %.1f deg ccw from east'%(best[0]*s,(v.max()-v.min())*s,th))
json.dump({'cx':cx,'cy':cy,'K':K,'c':c.tolist(),'scale_m_px':s},open('fit.json','w'))
im=cv2.imread('reg/h05.png');cv2.polylines(im,[np.stack([cx+r*np.cos(np.radians(a)),cy-r*np.sin(np.radians(a))],1).astype(np.int32)],True,(0,255,255),1)
cv2.imwrite('fit.jpg',im[int(cy-450):int(cy+450),int(cx-380):int(cx+380)])
