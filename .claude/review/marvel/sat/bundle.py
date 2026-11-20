import sys,os;sys.path.insert(0,os.getcwd())
from frame import *
from cam import proj
from scipy.optimize import least_squares
from PIL import Image,ImageDraw
GC=[((-29.8,141.6,0.3),(480,1032)),((-29.8,136.4,0.3),(485,1002)),((3.6,138.4,0.3),(802,1032)),((17.2,134.8,0.3),(917,1030)),((50,132,0.3),(1245,1030))]
G={'NW':(-90,51.7),'NE':(-101.25,-50),'SE':(61.25,-67),'SW':(73.75,30.5)}
FL=np.array([543,230.]);FR=np.array([1295,223.])
LL=(np.array([543,230.]),np.array([413,350.]));LR=(np.array([1295,223.]),np.array([1413,350.]))
ZO=float(sys.argv[1]) if len(sys.argv)>1 else 38.0
def pl(q,l):a,b=l;d=(b-a)/np.linalg.norm(b-a);v=q-a;return v[0]*d[1]-v[1]*d[0]
P0=json.load(open('c3_k1.json'))['p']
KF=np.array([-6.94,-2.2])/38.0
def unpack(x):return list(x[:7])+[960,540],KF
def pj(p,s,t,z):return proj(p,[wld(s,t,z)])[0]
def res(x,wk=1.0):
    p,k=unpack(x);r=[]
    for (s,t,z),uv in GC:r+=list(pj(p,s,t,z)-uv)
    o=lambda c:pj(p,G[c][0]-k[0]*ZO,G[c][1]-k[1]*ZO,ZO)
    r+=list(o('NE')-FL)+list(o('SE')-FR)+[pl(o('NW'),LL),pl(o('SW'),LR)]
    return np.array(r)
f=least_squares(res,list(P0[:7]),x_scale='jac')
p,k=unpack(f.x);print('z',ZO,'rms %.1f'%np.sqrt(np.mean(f.fun**2)),np.round(f.fun,1));print('p',np.round(p,3).tolist(),'lean/m',np.round(k,3),'lean@z',np.round(k*ZO,2))
C=np.array(p[:3]);print('cam local',loc(C[None])[0].round(1),C[2].round(1))
json.dump({'p':[float(v) for v in p],'k':[float(v) for v in k],'zo':ZO},open('c5.json','w'))
