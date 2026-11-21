from frame import *
from scipy.optimize import least_squares
ZD=HH['zr']+1.2;S0,T0=4.75,4.0
rot=lambda p:np.array([2*S0-p[0],2*T0-p[1]])
IL=bp(310,393,ZD);IR=bp(1473,382,ZD);NFIL=rot(IR);NFIR=rot(IL)
ANp=np.array([(323,380),(337,330),(357,290),(383,253),(417,220),(450,210),(483,212),(517,223),(533,233)],float)
ASp=np.array([(1473,377),(1467,350),(1457,310),(1440,263),(1413,223),(1367,198)],float)
def pts(a,b,H,phi,g,lean,m=400):
    l=np.linspace(0,1,m)[:,None];p=a+(b-a)*l;r=(H-ZD)*np.clip(4*l*(1-l),0,1)**g
    return np.array([wld(*(q+lean*rr*np.sin(phi)),ZD+rr*np.cos(phi)) for q,rr in zip(p,r[:,0])])
def res(x):
    out=[]
    for a,b,lean,px in ((IL,NFIL,np.array([1.0,0]),ANp),(IR,NFIR,np.array([-1.0,0]),ASp)):
        c=proj(P,pts(a,b,x[0],x[1],x[2],lean));out+=[np.min(np.linalg.norm(c-q,axis=1)) for q in px]
    return np.array(out)
for x0 in ([60,0.3,0.7],[60,-0.3,0.7]):
    f=least_squares(res,x0,bounds=([50,-1.2,0.3],[80,1.2,2]));print(f.x.round(3),'deg',np.degrees(f.x[1]).round(1),'rms',np.sqrt(np.mean(f.fun**2)).round(1),f.fun.round(1))
print('feet N',IL.round(1),NFIL.round(1),'S',IR.round(1),NFIR.round(1))
