# chamfer check of the model's top-down outline against the satellite (0.2 m/px world grid, north up):
# for every pixel on the model's outer silhouette, distance to the nearest satellite edge. Writes a heat overlay.
import numpy as np,cv2,math
sat=cv2.imread('sat/sat_world.png');t=cv2.imread('sat/top.png',cv2.IMREAD_UNCHANGED);px=340/t.shape[0]
al=cv2.morphologyEx((t[:,:,3]>10).astype(np.uint8),cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
# fill holes (the open field) so only the outer silhouette remains
ff=al.copy();h,w=ff.shape;m=np.zeros((h+2,w+2),np.uint8);cv2.floodFill(ff,m,(0,0),2);outer=(ff!=2).astype(np.uint8)
cs,_=cv2.findContours(outer,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE);c=max(cs,key=cv2.contourArea)[:,0,:]
g=cv2.GaussianBlur(cv2.cvtColor(sat,cv2.COLOR_BGR2GRAY),(0,0),1.5);e=cv2.Canny(g,25,70)
dt=cv2.distanceTransform((e==0).astype(np.uint8),cv2.DIST_L2,5)*px
d=dt[c[:,1],c[:,0]]
print('outline pts %d (%.0f m)  median %.2f m  p90 %.2f m  within 1 m %.0f%%  within 2 m %.0f%%  max %.1f m'%(len(d),len(d)*px,np.median(d),np.percentile(d,90),100*np.mean(d<=1),100*np.mean(d<=2),d.max()))
H=170;PC=(0.94,-11.82)
X=PC[0]-H+(c[:,0]+0.5)*px;Y=PC[1]+H-(c[:,1]+0.5)*px;A=(np.degrees(np.arctan2(Y-PC[1],X-PC[0])))%360
for a0 in range(0,360,30):
    s=(A>=a0)&(A<a0+30);print('  %3d-%3d deg  n%5d  median %.2f  p90 %.2f  >2 m %.0f%%'%(a0,a0+30,s.sum(),np.median(d[s]),np.percentile(d[s],90),100*np.mean(d[s]>2)))
ol=sat.copy()
for (x,y),v in zip(c,d):cv2.circle(ol,(int(x),int(y)),2,(0,255,0) if v<=1 else (0,255,255) if v<=2 else (0,0,255),-1)
for k in range(-150,151,50):
    p=int((k+H)/(2*H)*t.shape[0]);cv2.line(ol,(p,0),(p,h),(255,255,0),1);cv2.line(ol,(0,p),(w,p),(255,255,0),1)
cv2.imwrite('sat/td_chamfer.png',ol)
