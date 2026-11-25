import cv2,numpy as np,sys
for ph,rn,out in(('refs/scg.jpg','out/r0.png','proof/match_aerial.png'),('refs3/063.jpg','out/r63.png','proof/match_063.png')):
    p=cv2.imread(ph);r=cv2.imread(rn,cv2.IMREAD_UNCHANGED);r=cv2.resize(r,(p.shape[1],p.shape[0]))
    a=r[...,3:4]/255.0;comp=(r[...,:3]*a+p*(1-a)).astype(np.uint8);bl=(0.5*comp+0.5*p).astype(np.uint8)
    cv2.imwrite(out,np.hstack([p,comp,bl]))
