import sys,cv2,json
from camsolve import *
q=np.array(eval(sys.argv[1])); out=sys.argv[2]
img=cv2.imread('/home/user/work/subi/refs/commons/Subiaco_Oval.jpg')
a=np.linspace(0,360,1441)
for z,col in ((0,(0,0,255)),(1.0,(0,255,255))):
  uv,zz=proj(q,fpt(a,z))
  for i in range(len(a)-1):
    if zz[i]>0 and zz[i+1]>0: cv2.line(img,tuple(int(v) for v in uv[i]),tuple(int(v) for v in uv[i+1]),col,2)
for k,b in TW.items():
  uv,zz=proj(q,np.array([[b[0],b[1],0],[b[0],b[1],65]]))
  if (zz>0).all(): cv2.line(img,tuple(int(v) for v in uv[0]),tuple(int(v) for v in uv[1]),(255,0,255),3); cv2.putText(img,k,tuple(int(v) for v in uv[1]),0,1.2,(255,0,255),3)
J=np.array(json.load(open('/home/user/Afl-auto-battler/tools/grounds/legacy/subiaco/measure/north_roof_front_heights_2008.json')))
J=J[(J[:,5]>14)&(J[:,5]<22)]
P=np.array([[*px2m(r[1],r[2]),r[5]] for r in J]); uv,zz=proj(q,P)
for p in uv[zz>0]: cv2.circle(img,tuple(int(v) for v in p),4,(255,255,0),-1)
cv2.imwrite(out,img)
