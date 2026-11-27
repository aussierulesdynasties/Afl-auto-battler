# reg.py REF IMG OUT.json : similarity transform IMG -> REF from SIFT matches on the ground outside the stadium (RANSAC, 1 px)
import sys,cv2,numpy as np,json
ref,img,out=sys.argv[1:4]
A=cv2.imread(ref,0)[170:1950];B=cv2.imread(img,0)[170:1950]
msk=np.full(A.shape,255,np.uint8);msk[cv2.imread("z/labelmask.png",0)[170:1950]>0]=0;cv2.ellipse(msk,(941,1021-170),(560,420),0,0,360,0,-1)   # leave the stadium out (it leans)
s=cv2.SIFT_create(8000);ka,da=s.detectAndCompute(A,msk);kb,db=s.detectAndCompute(B,msk)
m=cv2.BFMatcher().knnMatch(db,da,k=2);g=[x for x,y in m if x.distance<0.75*y.distance]
pb=np.float32([kb[x.queryIdx].pt for x in g]);pa=np.float32([ka[x.trainIdx].pt for x in g])
M,inl=cv2.estimateAffinePartial2D(pb,pa,ransacReprojThreshold=1.0,maxIters=20000,confidence=0.999)
inl=inl.ravel()>0;res=np.linalg.norm((pb[inl]@M[:,:2].T+M[:,2])-pa[inl],axis=1)
M[1,2]+=170-170 # same crop both
sc=np.hypot(M[0,0],M[1,0]);rot=np.degrees(np.arctan2(M[1,0],M[0,0]))
print(img,'matches',len(g),'inliers',inl.sum(),'scale %.4f rot %.3f shift %.1f %.1f rms %.2f px'%(sc,rot,M[0,2],M[1,2],np.sqrt((res**2).mean())))
json.dump({'M':M.tolist(),'inliers':int(inl.sum()),'rms_px':float(np.sqrt((res**2).mean()))},open(out,'w'))
