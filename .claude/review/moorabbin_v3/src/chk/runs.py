import json,math,numpy as np
exec(open('chk/ringover.py').read().split("cam=np.array")[0])
def inpoly(q,poly):
    x,y=q;c=False;n=len(poly)
    for i in range(n):
        x1,y1=poly[i];x2,y2=poly[(i+1)%n]
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:c=not c
    return c
BLD={b['n']:np.array(b['pts'],float)[:,:2] for b in O['club'] if b['n']!='redtower'}
HI=wrap(hi);LO2=lo+2*math.pi
AC=np.linspace(HI,LO2,6000)
prev=None
for a in AC:
    q=pt(a,d_out(a)-0.05)[:2];ins=[n for n,p in BLD.items() if inpoly(q,p)]
    k=tuple(ins)
    if k!=prev:print(round(math.degrees(a)%360,2),k,np.round(q,1));prev=k
