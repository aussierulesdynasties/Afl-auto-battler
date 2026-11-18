from frame import *
from scipy.optimize import least_squares
ZD=HH['zr']+1.2
FL=bp(198,485,ZD);FR=bp(1560,472,ZD)
TOP=np.array([(260,452),(320,442),(400,412),(520,407),(670,387),(870,364),(1300,392),(1410,415),(1540,457)],float)
inward=np.array([0,-1.0])
def pts(a,b,H,phi,g=1.0,m=400):
    l=np.linspace(0,1,m)[:,None];p=a+(b-a)*l;r=(H-ZD)*np.clip(4*l*(1-l),0,1)**g
    return np.array([wld(*(q+inward*rr*np.sin(phi)),ZD+rr*np.cos(phi)) for q,rr in zip(p,r[:,0])]),p
def res(x):
    c,_=pts(FL,FR,x[0],x[1],x[2]);c=proj(P,c);return np.array([np.min(np.linalg.norm(c-q,axis=1)) for q in TOP])
f=least_squares(res,[59,0.3,1.0],bounds=([50,-1.2,0.3],[80,1.2,2]));print('apex',f.x.round(3),'deg',np.degrees(f.x[1]).round(1),'rms',np.sqrt(np.mean(f.fun**2)).round(1),f.fun.round(1))
c,p=pts(FL,FR,*f.x,m=3);print('apex point local',np.round(loc(c[1:2]),1),'z',c[1,2].round(1))
IL=bp(310,393,ZD);IR=bp(1473,382,ZD);inward=np.array([0,1.0])
from scipy.optimize import brentq
def vap(H):
    c,_=pts(IL,IR,H,f.x[1],f.x[2],m=401);q=proj(P,c);i=np.argmin(abs(q[:,0]-870));return q[i,1]
H2=brentq(lambda H:vap(H)-297,50,75);print('inner apex z',round(H2,2))
c,_=pts(IL,IR,H2,f.x[1],f.x[2],m=3);print('inner apex local',np.round(loc(c[1:2]),1),c[1,2].round(1))
json.dump(dict(front=dict(a=FL.tolist(),b=FR.tolist(),H=f.x[0],phi=f.x[1],g=f.x[2]),inner=dict(a=IL.tolist(),b=IR.tolist(),H=H2,phi=f.x[1],g=f.x[2])),open('truss.json','w'))
