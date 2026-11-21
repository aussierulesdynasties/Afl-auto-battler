import sys,cv2,numpy as np
# python model/ov.py photo render out : photo | render over sky | 50% overlay
p=cv2.imread(sys.argv[1]);r=cv2.imread(sys.argv[2],cv2.IMREAD_UNCHANGED)
r=cv2.resize(r,(p.shape[1],p.shape[0]));a=r[:,:,3:4]/255.0;rgb=r[:,:,:3].astype(float)
ren=(rgb*a+np.array([235,215,190])*(1-a)).astype(np.uint8)
ov=(p*0.5+ren*0.5).astype(np.uint8)
e=cv2.Canny(cv2.cvtColor(r[:,:,:3],cv2.COLOR_BGR2GRAY),60,150)|cv2.Canny(r[:,:,3],50,150)
ov2=p.copy();ov2[e>0]=(0,0,255)
cv2.imwrite(sys.argv[3],np.vstack([np.hstack([p,ren]),np.hstack([ov,ov2])]))
