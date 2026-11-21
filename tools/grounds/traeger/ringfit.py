# ring = OSM pitch outline (way 242194673) fitted onto the fence points read off the Google satellite (shift + scale)
import json,numpy as np
from scipy.optimize import least_squares
O=np.array(json.load(open('osm_pitch_field.json')));O=O[:-1] if np.allclose(O[0],O[-1]) else O
SAT=np.array([(75,0),(74.6,10),(74,20),(73,30),(75,-10),(74.4,-20),(73.4,-30),(72,-40),(70,50),      # east (tE)
              (-63,15),(-63,5),(-63,-5),(-63.2,25),(-64.5,-12),(-65,-20),(-64.5,-25),(-63.5,-30),(-62,-35),(-60.6,-40),   # west apron
              (-56.1,-45),(-53.3,-50),(-50.6,-55),(-46.7,-60),(-41.7,-65),(-35.6,-70),        # south-west (fsw)
              (-20.6,98.75),(-28.75,95),(-36.25,90),(-42.5,84.4),(-46.25,80),(-5,97.6),(5,98),(15,98)])   # north (tNW, tN)
def seg_d(P,A):
    B=np.roll(A,-1,0);d=B-A;out=[]
    for p in P:
        t=np.clip(((p-A)*d).sum(1)/(d*d).sum(1),0,1);q=A+t[:,None]*d;out.append(np.min(np.hypot(*(p-q).T)))
    return np.array(out)
def side(P,A):   # signed: + outside
    from matplotlib.path import Path
    ins=Path(A).contains_points(P);return np.where(ins,-1,1)
c=O.mean(0)
def tf(x):return (O-c)*[x[2],x[3]]+c+x[:2]
def res(x):A=tf(x);return seg_d(SAT,A)*side(SAT,A)
r=least_squares(res,[0,0,1,1]);x=r.x;R=res(x)
print('shift %.2f %.2f scale %.4f %.4f'%tuple(x));print('residuals m: rms %.2f max %.2f'%(np.sqrt((R**2).mean()),abs(R).max()))
for p,e in zip(SAT,R):
    if abs(e)>1.5:print('  off',p,round(e,2))
json.dump(tf(x).tolist(),open('ring_sat.json','w'))
# ---- final ring: through every satellite point; the fitted OSM shape only fills the gaps (shadowed stretches) ----
EXTRA=np.array([(-35,-70),(-25,-75),(-15,-78),(-5,-80),(5,-80.4),(15,-80),(25,-78.6),(35,-76),(45,-73),(55,-69),(63,-64),   # south (tS)
                (20,97.5),(25,97),(47.5,83.75),(56,75),(65,65),(70,57.5),(72.5,46)])                                       # north, north-east (tN, tNE)
PTS=np.vstack([SAT,EXTRA]);C=np.array([5.0,10.0])
A=tf(x);ang=lambda P:np.degrees(np.arctan2(P[:,1]-C[1],P[:,0]-C[0]))%360
def r_osm(th):   # radius of the fitted OSM outline along a ray (densified polygon)
    D=np.vstack([np.linspace(A[i],A[(i+1)%len(A)],20,endpoint=False) for i in range(len(A))]);a=ang(D);r=np.hypot(*(D-C).T);o=np.argsort(a)
    return np.interp(th,a[o],r[o],period=360)
ta=ang(PTS);res_=np.hypot(*(PTS-C).T)-r_osm(ta);o=np.argsort(ta)
th=np.arange(0,360,1.0);rr=np.interp(th,ta[o],res_[o],period=360)
k=np.exp(-0.5*(np.arange(-6,7)/2.0)**2);k/=k.sum();rr=np.convolve(np.r_[rr[-6:],rr,rr[:6]],k,'valid')    # 2-degree smoothing
R=r_osm(th)+rr;ring=np.c_[C[0]+R*np.cos(np.radians(th)),C[1]+R*np.sin(np.radians(th))]
chk=seg_d(PTS,ring);print('final ring vs satellite points: rms %.2f max %.2f m'%(np.sqrt((chk**2).mean()),chk.max()))
json.dump(ring.tolist(),open('ring_sat.json','w'))
