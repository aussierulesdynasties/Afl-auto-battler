import cv2,numpy as np,sys
r=cv2.imread(sys.argv[1],cv2.IMREAD_UNCHANGED);ph=cv2.imread('mu.png');a=r[...,3:4]/255.0
comp=(r[...,:3]*a+ph*(1-a)).astype(np.uint8)
# edge overlay: model edges (alpha + colour edges of render) drawn in magenta over the photo
e=cv2.Canny(cv2.cvtColor(r[...,:3],cv2.COLOR_BGR2GRAY),60,140)|cv2.Canny(r[...,3],10,50)
ed=ph.copy();ed[e>0]=(255,0,255)
diff=cv2.absdiff(comp,ph)
cv2.imwrite(sys.argv[2],np.vstack([np.hstack([ph,comp]),np.hstack([ed,(np.clip(diff.astype(int)*3,0,255)).astype(np.uint8)])]))
