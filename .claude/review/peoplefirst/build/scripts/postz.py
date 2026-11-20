import math,numpy as np,json
exec(open('nearsolve.py').read().split('# model')[0])
G=json.load(open('geo_n.json'));RO=G['rout']
def edgept(a,z):t=math.radians(a);r=lerp(RO,a);return (r*math.cos(t)+SH[0],r*math.sin(t)+SH[1],z)
def edgeang(x):
    A=np.arange(120,250,0.02);Q=proj([edgept(a,hout(a)) for a in A]);i=np.argmin(abs(Q[:,0]-x));return A[i]
for x,yt,yb in ((760,920,952),(838,935,968),(912,950,985),(722,915,948)):
    a=edgeang(x);Z=np.arange(0,35,0.1);Q=proj([edgept(a,z) for z in Z])
    zt=Z[np.argmin(abs(Q[:,1]-yt))];zb=Z[np.argmin(abs(Q[:,1]-yb))]
    print('post x%d: angle %.1f rout %.1f hout %.1f | photo top y%d -> z %.1f, foot y%d -> z %.1f, len %.1f m'%(x,a,lerp(RO,a),hout(a),yt,zt,yb,zb,zt-zb))
from wallz import wallang
for x in (722,848,700,950,1100): print('wall angle at photo x',x,round(wallang(x),1),' edge angle',round(edgeang(x),1))
