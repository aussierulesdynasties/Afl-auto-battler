# turf2.py IMG OUT.json : turf edge per 0.5 deg round (941,1021) at 0.2945 m/px with a 'lit' flag (the turf just inside is sunlit)
import sys,cv2,numpy as np,json,os
f,out=sys.argv[1],sys.argv[2];cx,cy,mpp=float(os.environ.get('CX',941)),float(os.environ.get('CY',1021)),float(os.environ.get('MPP',0.2945))
im=cv2.imread(f).astype(np.float32);im=cv2.GaussianBlur(im,(0,0),1.0)
s=im.sum(2)+1;g=im[...,1]/s;r=im[...,2]/s;b=im[...,0]/s
gr=float(os.environ.get('GR','0.0'))
m=((g>r+gr)&(g>b-0.02)&(s>40)).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
fill=m.copy();ff=np.zeros((m.shape[0]+2,m.shape[1]+2),np.uint8)
for dx in(-40,-25,25,40):
    p=(int(cx+dx/mpp),int(cy))
    if fill[p[1],p[0]]==1:cv2.floodFill(fill,ff,p,2)
T=(fill==2).astype(np.uint8);T=cv2.morphologyEx(T,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
cs,_=cv2.findContours(T,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE);c=max(cs,key=cv2.contourArea);T=np.zeros_like(T);cv2.drawContours(T,[c],-1,1,-1)
med=np.median(s[T>0]);res=[];R=np.arange(40,120,0.1)
for a in np.arange(0,360,0.5):
    t=np.radians(a);X=(cx+R*np.cos(t)/mpp).astype(np.float32);Y=(cy-R*np.sin(t)/mpp).astype(np.float32)
    v=cv2.remap(T,X[None],Y[None],cv2.INTER_NEAREST)[0]
    cc=np.convolve((v==0).astype(int),np.ones(10,int),'valid')>=10
    if not cc.any():res.append([float(a),None,False]);continue
    rr=R[np.argmax(cc)];k=np.argmax(cc)
    sv=cv2.remap(s,X[None],Y[None],cv2.INTER_LINEAR)[0][max(0,k-30):max(1,k-5)].mean()
    res.append([float(a),float(rr),bool(sv>0.75*med)])
json.dump(res,open(out,'w'))
print(f,'lit',sum(x[2] for x in res),'of',len(res))
