# refine2.py IMG FIT.json OUT.json [W] : per 0.5 deg, the turf edge as the half-way crossing of greenness (G-R) within +-W m of a smooth fit
import sys,cv2,json,numpy as np,os
img,fj,out=sys.argv[1:4];Wd=float(sys.argv[4]) if len(sys.argv)>4 else 2.0
cx,cy,mpp=float(os.environ['CX']),float(os.environ['CY']),float(os.environ['MPP'])
im=cv2.imread(img).astype(np.float32);G=cv2.GaussianBlur(im[...,1]-im[...,2],(0,0),0.7)
f=json.load(open(fj));K=f['K'];c=np.array(f['c'])
def fr(a):
    t=np.radians(np.atleast_1d(a));return (np.column_stack([np.ones_like(t)]+[g(k*t) for k in range(1,K+1) for g in (np.cos,np.sin)])@c)
res=[]
for a in np.arange(0,360,0.5):
    r0=fr(a)[0];t=np.radians(a);R=np.arange(r0-Wd-3,r0+Wd+3,0.03)
    X=(cx+R*np.cos(t)/mpp).astype(np.float32);Y=(cy-R*np.sin(t)/mpp).astype(np.float32)
    v=cv2.remap(G,X[None],Y[None],cv2.INTER_LINEAR)[0]
    inner=np.median(v[R<r0-Wd]);outer=np.median(v[R>r0+Wd]);
    if inner-outer<float(os.environ.get("MINC","4")): res.append([float(a),None,False]);continue
    h=(inner+outer)/2;w=(R>=r0-Wd)&(R<=r0+Wd);idx=np.where(w)[0]
    cr=[i for i in idx[:-1] if v[i]>=h and v[i+1]<h]
    if not cr: res.append([float(a),None,False]);continue
    i=cr[0];x=R[i]+(v[i]-h)/(v[i]-v[i+1])*(R[i+1]-R[i])
    res.append([float(a),float(x),True,float(inner-outer)])
json.dump(res,open(out,'w'))
