import numpy as np,json,math
from scipy.optimize import least_squares
from camlib import *
W,H=1200,676;cx,cy=W/2,H/2
E=json.load(open('edgeA.json'))
T={};Bo={}
for x,y,t in E:(T if t=='t' else Bo)[x]=y
LP=np.load('linesA.npy')[:,::-1].astype(float)  # (x,y)
keep=[]
for x,y in LP:
    xs=int(x//5*5)
    if xs in T and xs in Bo and T[xs]+6<y<Bo[xs]-6:keep.append((x,y))
LP=np.array(keep)
LOGO=[(535,240,585,280),(590,240,645,280),(650,250,695,280),(510,380,560,415),(565,390,615,425),(630,390,685,430)]
m=np.ones(len(LP),bool)
for a,b,c,d in LOGO:m&=~((LP[:,0]>a)&(LP[:,0]<c)&(LP[:,1]>b)&(LP[:,1]<d))
LP=LP[m];rng=np.random.default_rng(1);LP=LP[rng.choice(len(LP),min(2500,len(LP)),replace=False)]
print('line px',len(LP),flush=True)
a0=math.radians(172);U0=np.array([math.cos(a0),math.sin(a0)]);V0=np.array([-math.sin(a0),math.cos(a0)])
P0=PITCH-PITCH.mean(0);PN=np.c_[P0@U0/92.65,P0@V0/64.15]
SQI=np.array([(535,274.3),(691.3,283),(685.5,391.8),(513.8,380.5)],float)
RR=np.vstack([way(1430111014),way(951696127),way(1374562961),way(951696126),way(951696125)])
RRI=np.array([(100,611),(400,618),(700,625),(1000,633)],float)
t=np.linspace(0,2*np.pi,181)
def model(p):
    th,dx,dy,A,B=p[7:12];a=a0+th;U=np.array([math.cos(a),math.sin(a)]);V=np.array([-math.sin(a),math.cos(a)]);c=np.array([dx,dy])
    ov=np.outer(PN[:,0]*A,U)+np.outer(PN[:,1]*B,V)+c;ov=np.vstack([ov,ov[:1]])
    sq=np.outer(np.array([1,1,-1,-1,1])*25,U)+np.outer(np.array([1,-1,-1,1,1])*25,V)+c
    arcs=[]
    for s in(1,-1):
        g=c+s*A*U;pts=g+50*np.c_[np.cos(t),np.sin(t)];rel=pts-c;e=(rel@U/A)**2+(rel@V/B)**2
        tt=np.mod(t-math.atan2(-s*U[1],-s*U[0])+np.pi,2*np.pi)-np.pi;sel=e<0.97;pts=pts[sel];pts=pts[np.argsort(tt[sel])];arcs.append(pts)
    return ov,sq,arcs
def sqc(p):
    th,dx,dy=p[7:10];a=a0+th;U=np.array([math.cos(a),math.sin(a)]);V=np.array([-math.sin(a),math.cos(a)])
    return np.outer(np.array([1,1,-1,-1])*25,U)+np.outer(np.array([1,-1,-1,1])*25,V)+[dx,dy]
def pd(cam,P):return proj(cam,np.c_[P,np.zeros(len(P))],cx,cy)
def arcd(pts,q):
    # distance to point set (arc sampled every 2 deg ~ 1.7 m)
    return np.sqrt(((pts[:,None,:]-q[None])**2).sum(-1)).min(1)
def res(p,full=False):
    cam=p[:7];ov,sq,arcs=model(p)
    D=[curve_d(LP,pd(cam,ov)),curve_d(LP,pd(cam,sq))]+[arcd(LP,pd(cam,a)) if len(a) else np.full(len(LP),1e3) for a in arcs]
    r1=np.min(D,0)
    q=pd(cam,sqc(p));best=None
    for k in range(4):
        d=(q[[(i+k)%4 for i in range(4)]]-SQI).ravel()
        if best is None or (d**2).sum()<(best**2).sum():best=d
    r3=curve_d(RRI,pd(cam,RR))
    out=np.concatenate([r1,best*4,r3*3,[p[8],p[9]]])
    return (r1,best,r3) if full else out
best=None
for f0,k in [(600,0.75),(1000,1.0),(1600,1.5),(2500,2.2)]:
    p0=[0,-150*k,170*k,math.radians(93),math.radians(-45),math.radians(-2),f0,0,0,0,85,60]
    sol=least_squares(res,p0,loss='soft_l1',f_scale=2,max_nfev=3000);c=(sol.fun**2).mean()
    r1,r2,r3=res(sol.x,True)
    print(f0,round(c,2),'f',round(sol.x[6]),'AB',np.round(sol.x[10:12],1),'med line',round(float(np.median(r1)),2),'sq',round(float(np.sqrt((r2**2).mean())),2),'rr',round(float(np.sqrt((r3**2).mean())),2),flush=True)
    if best is None or c<best[0]:best=(c,sol.x)
p=best[1]
print('cam',np.round(p[:3],1),np.round(np.degrees(p[3:6]),2),round(p[6],1),'ground',np.round([math.degrees(p[7]),*p[8:12]],2))
b=at_z(p[:7],924,554,cx,cy,2);q=proj(p[:7],b+[0,0,15],cx,cy)[0];print('pole: base (924,554) +15m ->',np.round(q,1),'photo top (941,470) direction',np.round((q-[924,554])/np.linalg.norm(q-[924,554]),2),np.round(np.array([17,-84])/np.hypot(17,84),2))
ov,sq,arcs=model(p)
json.dump({'p':list(p[:7])+[1.0],'W':W,'H':H,'ground':list(p[7:12]),'oval':ov.tolist(),'square':sqc(p).tolist(),'arcs':[a.tolist() for a in arcs]},open('camA11.json','w'))
