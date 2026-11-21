import json, numpy as np, math
from scipy.optimize import least_squares
src=open('build.py').read(); a=src.index('def front_path'); b=src.index('def club_front'); ns={'np':np,'math':math}; exec(src[a:b],ns)
C=json.load(open('cazalys.json'))['club_front']; cat,cQ,_,_=ns['front_path'](C['chamfer']); co=C['canopy'][2]
at,Q,_,_=ns['front_path'](C['front'],True)
W=[];
for s,t in C['posts']: W+= [cQ(s,co-0.7,0), cQ(s-0.04*t,co-0.7,t)]
for b in C['bollards'][:4]: W.append(Q(b,C['aw_o'],1.15))
W=np.array(W,float)[:6]
I=np.array([(232,430),(210,245),(327,440),(312,302),(457,452),(437,180),(471,425),(506,427),(538,430),(570,432)],float)[:6]
def proj(p):
    ex,ey,yaw,pit,fov=p; f=300/math.tan(math.radians(fov/2)); E=np.array([ex,ey,1.6])
    fw=np.array([math.cos(pit)*math.cos(yaw),math.cos(pit)*math.sin(yaw),math.sin(pit)]); rt=np.cross(fw,[0,0,1]); rt/=np.linalg.norm(rt); up=np.cross(rt,fw)
    d=W-E; return np.c_[400+f*(d@rt)/(d@fw),300-f*(d@up)/(d@fw)]
best=None
for ex in range(36,70,3):
  for ey in range(-135,-95,3):
    r=least_squares(lambda p:(proj(p)-I).ravel(),[ex,ey,math.atan2(-136-ey,35-ex),0.15,60],bounds=([0,-220,-10,-1,25],[100,-60,10,1,90]))
    if best is None or r.cost<best.cost: best=r
p=best.x; e=np.sqrt(((proj(p)-I)**2).sum(1)); fw=np.array([math.cos(p[3])*math.cos(p[2]),math.cos(p[3])*math.sin(p[2]),math.sin(p[3])])
print('err',e.round(1)); print('eye %.2f,%.2f,1.6 target %s fov %.1f'%(p[0],p[1],','.join('%.2f'%v for v in np.array([p[0],p[1],1.6])+fw*15),p[4]))
