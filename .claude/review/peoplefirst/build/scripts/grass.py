import cv2,numpy as np,json
S=json.load(open('sat.json'));m=S['mpp']
def green(im):
    h=cv2.cvtColor(im,cv2.COLOR_BGR2HSV);return ((h[...,0]>30)&(h[...,0]<90)&(h[...,1]>60)&(h[...,2]>50)).astype(np.uint8)*255
def blob(mask,seed):
    mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((5,5),np.uint8));mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
    n,lab=cv2.connectedComponents(mask);l=lab[seed[1],seed[0]];b=(lab==l).astype(np.uint8)*255
    cs,_=cv2.findContours(b,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE);return max(cs,key=cv2.contourArea)[:,0,:].astype(float),b
sat=cv2.imread('sat.png');c,b=blob(green(sat),(int(S['px'])+60,int(S['py'])+60))
W=np.stack([(c[:,0]-S['px'])*m,-(c[:,1]-S['py'])*m],1);print('sat grass extent',W.min(0),W.max(0))
np.save('grass_w.npy',W)
ph=cv2.imread('photo.png');c2,b2=blob(green(ph),(930,700))
hsv=cv2.cvtColor(ph,cv2.COLOR_BGR2HSV);white=((hsv[...,2]>185)&(hsv[...,1]<50)).astype(np.uint8)
n,lab,st,_=cv2.connectedComponentsWithStats(white);big=np.isin(lab,[i for i in range(1,n) if st[i,4]>40000]).astype(np.uint8)
dark=((hsv[...,2]<90)).astype(np.uint8)
white=cv2.dilate(big,np.ones((31,31),np.uint8))
c2=c2[[white[int(y),int(x)]==0 for x,y in c2]][::4]
np.save('grass_p.npy',c2)
v=ph.copy();[cv2.circle(v,(int(x),int(y)),3,(0,0,255),-1) for x,y in c2]
cv2.imwrite('grass_p.jpg',cv2.resize(v,(1000,667)))
v=sat.copy();cv2.polylines(v,[c.astype(np.int32)],True,(0,0,255),3);cv2.imwrite('grass_s.jpg',cv2.resize(v,(800,800)))
