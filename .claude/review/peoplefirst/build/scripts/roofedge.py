import json,math
from unp import pr
D=json.load(open('geo_build.json'))
def la(A,a):
    f=(a%360)*4;i=int(f)%1440;t=f-int(f);return A[i]*(1-t)+A[(i+1)%1440]*t
def cf(c,a):r=math.radians(a);return c[0]+c[1]*math.cos(r)+c[2]*math.sin(r)
SH=D.get('roofshift',[0,0])
def P(a,dr,dz=0):
    r=la(D['rin'],a)+dr;z=cf(D['hin'],a)+dz;t=math.radians(a);return pr((r*math.cos(t)+SH[0],r*math.sin(t)+SH[1],z))
print(D['a0'],D['a1'])
for a in range(int(D['a0']),int(D['a1'])+1,10):
    print(a,P(a,0),P(a,-4),P(a,-6,-1))
