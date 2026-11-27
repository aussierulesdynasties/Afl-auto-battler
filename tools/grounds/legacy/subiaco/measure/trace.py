# trace.py IMG cx cy mpp OUT.json : per bearing (0.5 deg), radii (m) of the turf edge, roof inner edge, roof outer edge
import sys,cv2,numpy as np,json
f,cx,cy,mpp,out=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),sys.argv[5]
im=cv2.imread(f).astype(np.float32);im=cv2.GaussianBlur(im,(0,0),0.8)
s=im.sum(2)+1;g=im[...,1]/s;r=im[...,2]/s;b=im[...,0]/s;L=s/3
hsv=cv2.cvtColor(np.clip(im,0,255).astype(np.uint8),cv2.COLOR_BGR2HSV).astype(np.float32)
sat=hsv[...,1]/255;val=hsv[...,2]/255
turf=(g>0.37)&(g>r+0.04)&(g>b+0.02)
roof=(sat<0.13)&(val>0.62)
def run_first(m,n):  # first index where n consecutive True
    c=np.convolve(m.astype(int),np.ones(n,int),'valid')>=n
    return int(np.argmax(c)) if c.any() else -1
res=[]
R=np.arange(50,190,0.1)
for a in np.arange(0,360,0.5):
    t=np.radians(a);X=(cx+R*np.cos(t)/mpp).astype(np.float32);Y=(cy-R*np.sin(t)/mpp).astype(np.float32)
    T=cv2.remap(turf.astype(np.uint8),X[None],Y[None],cv2.INTER_NEAREST)[0]>0
    F=cv2.remap(roof.astype(np.uint8),X[None],Y[None],cv2.INTER_NEAREST)[0]>0
    i=run_first(~T,15); fence=R[i] if i>=0 else None
    j0=i if i>=0 else 0
    k=run_first(F[j0:],20); rin=R[j0+k] if k>=0 else None
    if k>=0:
        e=run_first(~F[j0+k:],25); rout=R[j0+k+e] if e>=0 else None
    else: rout=None
    res.append([float(a),fence and float(fence),rin and float(rin),rout and float(rout)])
json.dump(res,open(out,'w'))
P=cv2.imread(f)
for a,fe,ri,ro in res:
    t=np.radians(a)
    for v,c in((fe,(0,255,0)),(ri,(0,0,255)),(ro,(255,0,255))):
        if v:cv2.circle(P,(int(cx+v*np.cos(t)/mpp),int(cy-v*np.sin(t)/mpp)),1,c,-1)
cv2.imwrite(out.replace('.json','.jpg'),P[560:1480,300:1600])
