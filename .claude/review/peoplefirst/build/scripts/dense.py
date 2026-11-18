import cv2,numpy as np,json
S=json.load(open('sat.json'));m=S['mpp'];Hc=np.load('Hc.npy')
ph=cv2.cvtColor(cv2.imread('photo.png'),cv2.COLOR_BGR2GRAY).astype(np.float32)
w=cv2.warpPerspective(cv2.cvtColor(cv2.imread('sat.png'),cv2.COLOR_BGR2GRAY),Hc,(2000,1333)).astype(np.float32)
roof=cv2.imread('wm_roof.png',0);excl=cv2.dilate(roof,np.ones((61,61),np.uint8))
# also exclude the bowl interior (pitch region) - handled by roof hull
hull=cv2.convexHull(cv2.findNonZero(roof));cv2.fillConvexPoly(excl,hull,255)
def hp(x):
    x=cv2.GaussianBlur(x,(0,0),1.5);gx=cv2.Sobel(x,cv2.CV_32F,1,0);gy=cv2.Sobel(x,cv2.CV_32F,0,1);return np.sqrt(gx*gx+gy*gy)
P=hp(ph);Wp=hp(w);out=[]
Hi=np.linalg.inv(Hc)
for y in range(120,1333-120,40):
    for x in range(120,2000-120,40):
        if excl[y,x]:continue
        t=P[y-60:y+61,x-60:x+61]
        if t.std()<8:continue
        sr=Wp[y-110:y+111,x-110:x+111]
        if sr.shape!=(221,221):continue
        r=cv2.matchTemplate(sr,t,cv2.TM_CCOEFF_NORMED);_,mx,_,loc=cv2.minMaxLoc(r)
        if mx<0.30:continue
        # second peak check
        r2=r.copy();cv2.circle(r2,loc,12,-1,-1);
        if r2.max()>mx-0.03:continue
        wx,wy=x-110+loc[0]+60,y-110+loc[1]+60   # matched location in warped-sat image
        q=cv2.perspectiveTransform(np.float32([[[wx,wy]]]),Hi)[0,0]
        X=((q[0]-S['px'])*m,-(q[1]-S['py'])*m)
        out.append((x,y,X[0],X[1],mx,wx-x,wy-y))
O=np.array(out);np.save('dense.npy',O);print(len(O));print(np.round(O[:,5:7].mean(0),1),np.round(np.median(np.abs(O[:,5:7]),0),1))
vis=cv2.imread('photo.png')
for x,y,_,_,s,dx,dy in O:cv2.arrowedLine(vis,(int(x),int(y)),(int(x+dx*3),int(y+dy*3)),(0,0,255),2)
cv2.imwrite('dense.jpg',cv2.resize(vis,(1400,933)))
