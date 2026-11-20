import sys;exec(open('parts.py').read().split('# ---------- end arches')[0])
from scipy.optimize import least_squares
ANp=np.array([(323,380),(337,330),(357,290),(383,253),(417,220),(450,210),(483,212),(517,223),(533,233)],float)
ASp=np.array([(1303,213),(1367,198),(1413,223),(1440,263),(1457,310),(1467,350),(1473,377)],float)
def pts(a,b,H,g,phi,out,m=400):
    l=np.linspace(0,1,m)[:,None];p=a+(b-a)*l;r=(H-ZD)*np.clip(4*l*(1-l),0,1)**g
    return np.array([W(*(q+out*rr*np.sin(phi)),ZD+rr*np.cos(phi)) for q,rr in zip(p,r[:,0])])
def res(x,mode):
    H,g,phi,e=x
    if mode==0:phi=0
    r=[]
    for (a,b,o),px in(((NIL,FIR,np.array([-1.0,0])),ANp),((NIR,FIL,np.array([1.0,0])),ASp)):
        b2=b+(b-a)/np.linalg.norm(b-a)*e
        c=proj(P,pts(a,b2,H,g,phi,o))
        for q in px:r.append(np.min(np.linalg.norm(c-q,axis=1)))
    return np.array(r)
for mode in (0,1):
  for x0 in ([65,0.5,0,0],[65,0.5,0.2,20],[65,1,-0.2,10]):
    f=least_squares(res,x0,args=(mode,),bounds=([50,0.2,-1,-30],[120,2,1,80]));print(mode,np.round(f.x,2),'rms',np.sqrt(np.mean(f.fun**2)).round(1),np.round(f.fun,1))
