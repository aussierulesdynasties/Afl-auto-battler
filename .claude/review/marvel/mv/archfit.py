import sys;sys.argv=['x'];exec(open('parts.py').read().split('# ---------- end arches')[0])
from scipy.optimize import least_squares
ANp=np.array([(323,380),(337,330),(357,290),(383,253),(417,220),(450,210),(483,212),(517,223),(533,233)],float)
ASp=np.array([(1303,213),(1367,198),(1413,223),(1440,263),(1457,310),(1467,350),(1473,377)],float)
def pts(a,b,H,phi,out,m=300):
    l=np.linspace(0,1,m)[:,None];p=a+(b-a)*l;r=(H-ZD)*4*l*(1-l)
    return np.array([W(*(q+out*rr*np.sin(phi)),ZD+rr*np.cos(phi)) for q,rr in zip(p,r[:,0])])
def res(x):
    H,phi=x;r=[]
    for (a,b,o),px in(((NIL,FIR,np.array([-1.0,0])),ANp),((NIR,FIL,np.array([1.0,0])),ASp)):
        c=proj(P,pts(a,b,H,phi,o))
        for q in px:r.append(np.min(np.linalg.norm(c-q,axis=1)))
    return np.array(r)
for H0,ph0 in [(70,0.3),(70,-0.3),(80,0.6)]:
    f=least_squares(res,[H0,ph0]);print(np.round(f.x,3),np.degrees(f.x[1]).round(1),'rms',np.sqrt(np.mean(f.fun**2)).round(1),np.round(f.fun,1))
