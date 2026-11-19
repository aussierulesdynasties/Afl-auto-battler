# python work/topov.py render.png out.png : Esri z19 (0.25 m/px, north up) with the model: cyan = silhouette edge, magenta = model edges, 10 m grid
import sys,cv2,numpy as np
S=cv2.imread('sat/esri_025.png');r=cv2.imread(sys.argv[1],cv2.IMREAD_UNCHANGED);o=S.copy()
for k in range(0,1600,40):
  o[:,k]=o[:,k]//2+60;o[k,:]=o[k,:]//2+60
c=r[:,:,:3].astype(int);d=np.zeros(c.shape[:2],bool)
d[1:]|=np.abs(c[1:]-c[:-1]).sum(2)>30;d[:,1:]|=np.abs(c[:,1:]-c[:,:-1]).sum(2)>30
d&=r[:,:,3]>0;o[d]=(255,0,255)
a=r[:,:,3]>128;e=a^cv2.erode(a.astype(np.uint8),np.ones((3,3))).astype(bool);e=cv2.dilate(e.astype(np.uint8),np.ones((2,2))).astype(bool);o[e]=(255,255,0)
for k in range(0,1601,200):cv2.putText(o,str(int(k*0.25-200)),(k+2,14),0,0.4,(0,255,255),1);cv2.putText(o,str(int(200-k*0.25)),(2,k+14),0,0.4,(0,255,255),1)
cv2.imwrite(sys.argv[2],o)
