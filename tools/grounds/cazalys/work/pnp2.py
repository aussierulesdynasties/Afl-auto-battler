exec(open('pnp.py').read().split('from scipy')[0].split('best=None')[0])
from scipy.optimize import least_squares
W=W[:6]; I=I[:6]
def proj(p,Wp=None):
    Wp=W if Wp is None else Wp
    ex,ey,yaw,pit,fov=p; f=300/math.tan(math.radians(fov/2)); C=np.array([ex,ey,1.6])
    fw=np.array([math.cos(pit)*math.cos(yaw),math.cos(pit)*math.sin(yaw),math.sin(pit)]); rt=np.cross(fw,[0,0,1]); rt/=np.linalg.norm(rt); up=np.cross(rt,fw)
    d=Wp-C; return np.c_[400+f*(d@rt)/(d@fw),300-f*(d@up)/(d@fw)]
best=None
for ex in range(30,70,4):
  for ey in range(-170,-100,5):
    for fov in (45,55,65):
      r=least_squares(lambda p:(proj(p)-I).ravel(),[ex,ey,math.atan2(-139-ey,33.7-ex),0.15,fov],bounds=([0,-220,-10,-1,25],[100,-60,10,1,90]))
      if best is None or r.cost<best.cost: best=r
p=best.x; e=np.sqrt(((proj(p)-I)**2).sum(1))
fw=np.array([math.cos(p[3])*math.cos(p[2]),math.cos(p[3])*math.sin(p[2]),math.sin(p[3])])
print('err',e.round(1),'eye',p[:2].round(2),'fov',round(p[4],1),'target',(np.array([p[0],p[1],1.6])+fw*15).round(2))
# where should the bollards be? back-project bollard tops to z=1.15
f=300/math.tan(math.radians(p[4]/2)); C=np.array([p[0],p[1],1.6]); rt=np.cross(fw,[0,0,1]); rt/=np.linalg.norm(rt); up=np.cross(rt,fw)
for u,v in [(471,425),(506,427),(538,430),(570,432),(640,440)]:
    d=fw+rt*(u-400)/f+up*(300-v)/f; t=(1.15-1.6)/d[2]; print('bollard',(u,v),(C+d*t).round(1))
