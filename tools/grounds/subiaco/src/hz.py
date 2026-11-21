import numpy as np,json
from camlib import *
J=json.load(open('camA_final.json'));cam=J['p'][:7];cx,cy=J['W']/2,J['H']/2
OV=np.array(J['oval']);OVc=np.vstack([OV,OV[:1]])
F={600:116,500:120,440:128,400:136,360:146,340:151,320:158,300:166,280:175,260:187}
B={600:93,500:94,440:100,400:109,360:116,340:117,320:122,300:127}
def bp(D,z):return np.array([at_z(cam,x,y,cx,cy,z)[:2] for x,y in D.items()])
for nm,D in(('front',F),('back',B)):
  for z in range(0,40,4):
    P=bp(D,z);d=curve_d(P,OVc);print(nm,z,'mean %.1f std %.2f'%(d.mean(),d.std()))
# north stand roof rectangle
NS=[(642.5,112),(770,121),(767.5,158),(634.5,148)]
for z in range(0,40,3):
  P=np.array([at_z(cam,x,y,cx,cy,z)[:2] for x,y in NS]);E=[P[(i+1)%4]-P[i] for i in range(4)]
  ang=[np.degrees(np.arccos(np.dot(E[i],-E[i-1])/np.linalg.norm(E[i])/np.linalg.norm(E[i-1]))) for i in range(4)]
  print('NS',z,np.round(ang,1),np.round([np.linalg.norm(e) for e in E],1))
