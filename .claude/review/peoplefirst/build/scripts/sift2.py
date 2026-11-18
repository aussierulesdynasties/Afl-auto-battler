import cv2,numpy as np,json
S=json.load(open('sat.json'));m=S['mpp']
def w2s(x,y):return (S['px']+x/m,S['py']-y/m)
W=[(-168,-9),(-164,-44),(-106,-108),(-10,84),(75,0)]
P=[(930,1265),(1100,1275),(1514,1086),(507,707),(914,561)]
H0,_=cv2.findHomography(np.float32([w2s(*w) for w in W]),np.float32(P))
ph=cv2.imread('photo.png');sat=cv2.imread('sat.png')
Hc=H0
for it in range(3):
    warp=cv2.warpPerspective(sat,Hc,(ph.shape[1],ph.shape[0]))
    sift=cv2.SIFT_create(30000)
    k1,d1=sift.detectAndCompute(cv2.cvtColor(ph,cv2.COLOR_BGR2GRAY),None);k2,d2=sift.detectAndCompute(cv2.cvtColor(warp,cv2.COLOR_BGR2GRAY),None)
    mm=cv2.BFMatcher().knnMatch(d1,d2,k=2);good=[a for a,b in mm if a.distance<0.8*b.distance]
    p1=np.float32([k1[g.queryIdx].pt for g in good]);p2=np.float32([k2[g.trainIdx].pt for g in good])
    near=np.hypot(*(p1-p2).T)<150;p1,p2=p1[near],p2[near]
    Hd,mask=cv2.findHomography(p2,p1,cv2.RANSAC,3.0,maxIters=20000)
    Hc=Hd@Hc;print(it,len(good),near.sum(),int(mask.sum()))
inl=mask.ravel()==1
# map inlier warped-sat points back to world
q=cv2.perspectiveTransform(p2[inl][None],np.linalg.inv(Hc@np.linalg.inv(Hd)))[0]
Wd=np.stack([(q[:,0]-S['px'])*m,-(q[:,1]-S['py'])*m],1)
np.save('corr.npy',np.concatenate([Wd,p1[inl]],1));np.save('H.npy',Hc)
warp=cv2.warpPerspective(sat,Hc,(ph.shape[1],ph.shape[0]))
ov=cv2.addWeighted(ph,0.5,warp,0.5,0)
for (x,y) in p1[inl]:cv2.circle(ov,(int(x),int(y)),3,(0,0,255),-1)
cv2.imwrite('sift_ov.jpg',cv2.resize(ov,(1400,933)))
