from cam import *
from scipy.optimize import least_squares
ways,nodes=load_map()
a=np.array([-150,-5.]);b=np.array([-118,-95.]);u=(b-a)/np.linalg.norm(b-a);n=np.array([-u[1],u[0]])
TR=[];
for t,(x,y) in nodes:
    if t.get('natural')=='tree':
        q=np.array([x,y])-a;s=q@u;o=q@n
        if -40<s<140 and abs(o)<25:TR.append((x,y))
TR=np.array(TR)
TIPS=np.array([(359,1012),(450,1000),(550,998),(650,998),(750,998),(844,998),(952,998),(1046,998),(1136,998),(1230,998),(1374,1000),(1467,1000)],float)
G=json.load(open('osm/geo.json'))
dr=np.array(G['ways']['33261092'][:17]);  # drum arc (-137,36)...(-157,45)
th=np.linspace(0,2*np.pi,90);DC=np.array([-147.5,40.5]);DRUM=np.stack([DC[0]+11*np.cos(th),DC[1]+11*np.sin(th)],1)
ARC=np.array([(0,873),(50,866),(100,850),(140,825),(163,800)],float)
FIX=[((442,942),(-146.5,-6.5,'hA')),((1297,942),(-115.5,-91,'hA')),((1090,55),(147,-11,72)),((1650,65),(99,-132,72))]
def unpack(q):
    p=list(q[:7])+[960,q[7]];return p,dict(hA=q[8],hT=q[9],hD=q[10])
def res(q):
    p,h=unpack(q);r=[]
    for (uv,(x,y,z)) in FIX:
        z=h[z] if isinstance(z,str) else z;r+=list(proj(p,[(x,y,z)])[0]-np.array(uv))
    pt=proj(p,np.c_[TR,np.full(len(TR),h['hT'])]);dd=np.sqrt(((TIPS[:,None]-pt[None])**2).sum(-1)).min(1);r+=list(dd)
    pd=proj(p,np.c_[DRUM,np.full(len(DRUM),h['hD'])]);dd=np.sqrt(((ARC[:,None]-pd[None])**2).sum(-1)).min(1);r+=list(dd*0.5)
    return np.array(r)
import math
p0=json.load(open('c0.json'))['p']
yaw=math.radians(20);pit=math.radians(-38)
best=None
for D in(150,200,260):
  for yawd in(15,20,25):
    yaw=math.radians(yawd);tx,ty=-120,-45
    C=(tx-D*math.cos(pit)*math.cos(yaw),ty-D*math.cos(pit)*math.sin(yaw),20-D*math.sin(pit))
    q0=[*C,yaw,pit,0,1300,540,6,8,15]
    s=least_squares(res,q0,bounds=([-1e4]*3+[-3,-1.3,-0.3,500,300,0,2,2],[1e4]*3+[3,0,0.3,4000,800,20,20,40]))
    if best is None or s.cost<best.cost:best=s
s=best;p,h=unpack(s.x);r=s.fun
print('rms',round(math.sqrt((r**2).mean()),1),[round(v,2) for v in s.x]);print(np.round(r,1))
json.dump({'p':p,'h':h},open('c1.json','w'))
