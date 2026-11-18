import cv2,numpy as np,json
S=json.load(open('sat.json'));m=S['mpp']
ph=cv2.imread('photo.png',0);sat=cv2.imread('sat.png',0)
sift=cv2.SIFT_create(20000)
k1,d1=sift.detectAndCompute(ph,None);k2,d2=sift.detectAndCompute(sat,None)
bf=cv2.BFMatcher();mm=bf.knnMatch(d1,d2,k=2)
good=[a for a,b in mm if a.distance<0.8*b.distance]
print(len(k1),len(k2),len(good))
p1=np.float32([k1[g.queryIdx].pt for g in good]);p2=np.float32([k2[g.trainIdx].pt for g in good])
H,mask=cv2.findHomography(p2,p1,cv2.RANSAC,6.0,maxIters=20000)
print('inliers',mask.sum());print(H)
np.save('H.npy',H)
inl=mask.ravel()==1
W=np.stack([(p2[inl,0]-S['px'])*m,-(p2[inl,1]-S['py'])*m],1)
np.save('corr.npy',np.concatenate([W,p1[inl]],1))
warp=cv2.warpPerspective(cv2.imread('sat.png'),H,(ph.shape[1],ph.shape[0]))
col=cv2.imread('photo.png');ov=cv2.addWeighted(col,0.5,warp,0.5,0)
for (x,y) in p1[inl]:cv2.circle(ov,(int(x),int(y)),4,(0,0,255),-1)
cv2.imwrite('sift_ov.jpg',cv2.resize(ov,(1400,933)))
