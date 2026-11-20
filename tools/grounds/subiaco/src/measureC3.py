import json
from subC2 import *
JB=json.load(open('layoutB.json'))
BB=sorted([(p[0],p[1]) for p in JB['BB']])
def bbd(a):return float(np.interp(a,[p[0] for p in BB],[p[1] for p in BB]))
# inner (roof front / canopy front) pixels, ring order from the far-left corner clockwise
front=[(265,262),(225,275),(185,300),(160,330),(150,365),(165,395),(200,410),(250,425),(300,430),(350,435),(400,437),(500,432),(600,416),(650,400),(700,385),(750,365),(800,340),(850,315),(885,265),(900,225),(890,190),(860,165),(800,145),(700,137),(600,140),(540,150),(510,200),(420,218),(340,235)]
back=[(230,250),(150,272),(110,295),(88,330),(84,370),(95,400),(150,460),(200,458),(250,459),(300,460),(350,462),(400,460),(450,457),(500,452),(550,445),(600,433),(650,415),(700,410),(750,400),(800,390),(850,375),(920,330),(948,280),(955,230),(940,185),(900,155),(860,135),(780,122),(700,120),(600,125),(530,135),(515,170),(400,195),(300,225)]
F=[];B=[]
for u,v in front:
    p=at_d(u,v,3.0)
    if p is None:p=list(pol(u,v,8.0))
    F.append([float(p[0]),float(p[1]),float(p[2])])
for u,v in back:
    a,d,z=pol(u,v,27.0)
    if 40<a<132 or (u<560 and v<200 and u>290):   # far (north) stand: depth from B, height from this photo
        a0=a
        for _ in range(3):
            dd=bbd(a0);p=cross(u,v,dd,18.0)
            if p is None:break
            a0=p[0]
        if p is not None:a,d,z=p[0],dd,p[2]
    B.append([float(a),float(d),float(z)])
for n,L in (('F',F),('B',B)):
    for p,px in zip(L,front if n=='F' else back):print(n,px,[round(x,1) for x in p])
json.dump({'RF':F,'RB':B},open('layoutC2.json','w',newline=''))
