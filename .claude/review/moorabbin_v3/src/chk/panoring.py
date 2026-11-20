import json,math,numpy as np
from scipy.optimize import least_squares
exec(open('chk/ringover.py').read().split("cam=np.array")[0])
po=O['poles'];ps=O['posts']
W={'N':np.mean(np.array(ps['north'])[1:3,:2],0),'S':np.mean(np.array(ps['south'])[1:3,:2],0),'SS':np.array([-46.35,-94.27]),'SN':np.array([-68.44,60.41])}
obs=dict(N=1647,S=471,SS=280,SN=1168)
def cpos(t):return np.array(pt(t,d_out(t)-1.0,0)[:2])
def res(p):
    C=cpos(p[0]);r=[]
    for k,v in obs.items():
        d=W[k]-C;a=math.atan2(d[1],d[0]);r.append(p[2]*((p[1]-a+math.pi)%(2*math.pi)-math.pi)+1000-v)
    return r
best=None
for t0 in np.radians(np.arange(-80,80,5)):
  for a00 in np.linspace(0,2*math.pi,8,endpoint=False):
    s=least_squares(res,[t0,a00,600],bounds=([-math.pi,-10,100],[math.pi,10,3000]))
    if best is None or s.cost<best.cost:best=s
p=best.x;print('cam ang',round(math.degrees(p[0]),1),'pos',cpos(p[0]).round(1),'f',round(p[2]),'res',np.round(best.fun,1))
json.dump({'p':list(p)},open('chk/panoring.json','w'))
C=cpos(p[0])
def ang_of_u(u):return p[1]-(u-1000)/p[2]
# for billboard u ranges, intersect the ray with the bank crest ring
for name,(u0,u1) in {'FOSTERS':(0,52),'white2':(57,105),'white3':(105,177),'TABARET':(180,210),'PHILIPMORRIS':(214,292),'N_white':(1663,1718),'scorebd_right':(1930,2000)}.items():
    pts=[]
    for u in (u0,u1):
        a=ang_of_u(u);dvec=np.array([math.cos(a),math.sin(a)])
        best_=None
        for r in np.arange(5,400,0.25):
            X=C+dvec*r;aa=math.atan2(X[1]-PC[1],X[0]-PC[0]);dd=np.hypot(*(X-PC))-rp(aa)
            if r>20 and abs(dd-d_out(aa))<0.6:best_=(X,math.degrees(aa));break
        pts.append(best_)
    print(name,[(None if q is None else (q[0].round(1).tolist(),round(q[1],1))) for q in pts])
