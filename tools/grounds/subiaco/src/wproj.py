import json,math,numpy as np
from camlib import proj
cam=json.load(open('camB.json'))['p'];J=json.load(open('layoutA.json'));C0=J['C0'];FJ=J['fence'];co=FJ['co'];K=FJ['K']
def rf(a):
    t=math.radians(a);return sum(co[k]*math.cos(k*t) for k in range(K+1))+sum(co[K+k]*math.sin(k*t) for k in range(1,K+1))
def P(a,d,z):
    r=rf(a)+d;t=math.radians(a);return [C0[0]+r*math.cos(t),C0[1]+r*math.sin(t),z]
JB=json.load(open('layoutB.json'))
for k in ('LW','FL1','FL2'):
    for zz in (0,None):
        X=[P(a,d,(z if zz is None else 0)) for a,d,z in JB[k]];q=proj(cam,np.array(X),500,300)
        print(k,'top' if zz is None else 'base',[tuple(np.round(p).astype(int)) for p in q])
for k in ('SF','SB'):
    S=JB[k];print(k,'n',len(S),'angles',min(s[0] for s in S),max(s[0] for s in S))
    S2=[s for s in S if s[0]<-120 or s[0]>180];
    for s in sorted(S2)[:6]:print('  ',s,tuple(np.round(proj(cam,np.array([P(*s)]),500,300)[0]).astype(int)))
