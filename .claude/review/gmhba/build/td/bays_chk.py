# model outer edge (top render mask) at each satellite notch and tip, vs the satellite reading; lean 0.035 m/m at z~21
import sys,math,numpy as np;sys.path.insert(0,'.')
from zk import rp,PCx,PCy
CX,CY,H,M=-10.75,-24.16,220.0,0.25
m=np.load('mask.npy')
def out(a):
    t=math.radians(a);last=None
    for d in np.arange(0,80,0.25):
        r=rp(a)+d;x,y=PCx+r*math.cos(t),PCy+r*math.sin(t);u,v=int(round((x-CX+H)/M)),int(round((CY+H-y)/M))
        if m[v,u]:last=d
    return last
src=open('../gm/build.py',encoding='utf-8').read()
ns={};exec(src[src.index('BKN=['):src.index('def BZ')],ns)
print('kind  angle  sat_d  model_d  diff')
for k in range(2,len(ns['BKN'])):
    for kind,p in(('notch',ns['BKN'][k]),('tip',ns['BKT'][k])):
        a,d=p;o=out(a);print(f'{kind:5s} {a:7.2f} {d:6.2f} {o:7.2f} {o-d:+6.2f}')
