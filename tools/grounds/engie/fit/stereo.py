# Run from a work folder holding the Google Earth shots in ge/ (never committed; looking and measuring only).
import cv2, numpy as np, json
f=3858.6; B=150.0; D=1500.0
def disp(A,Bm,transpose=False):
    a=cv2.imread(A,0); b=cv2.imread(Bm,0)
    if transpose: a=np.ascontiguousarray(a.T); b=np.ascontiguousarray(b.T)
    # pre-shift b by the expected ground disparity to keep the search range small
    g=int(round(f*B/D)); 
    bs=np.zeros_like(b); bs[:,g:]=b[:,:-g]
    sg=cv2.StereoSGBM_create(minDisparity=-24,numDisparities=64,blockSize=7,P1=8*49,P2=32*49,uniquenessRatio=8,speckleWindowSize=60,speckleRange=2,mode=cv2.STEREO_SGBM_MODE_HH)
    d=sg.compute(a,bs).astype(np.float32)/16.0
    d[d<=-24]=np.nan
    d=d+g
    if transpose: d=d.T
    return d
dWE=disp('ge/st_W.png','ge/st_E.png')            # in W image coords
dSN=disp('ge/st_N.png','ge/st_S.png',True)       # N camera image (point lower in N image) vs S
np.save('dWE.npy',dWE); np.save('dSN.npy',dSN)
for nm,d in (('WE',dWE),('SN',dSN)): print(nm,np.nanpercentile(d,[5,50,95]), np.isnan(d).mean())
