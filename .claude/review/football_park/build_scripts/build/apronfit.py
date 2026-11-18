# The paved ground reaches 3 m past every stadium structure that stands on it (stand foot, buildings, light-tower
# bases), so nothing stands over the void. Same 3 m margin already used for the stand foot.
import math
A0,B0=72.5,88.5
def td(x,y):
    lo,hi=-72.0,600.0
    for _ in range(60):
        m=(lo+hi)/2
        if (x/(A0+m))**2+(y/(B0+m))**2>1:lo=m
        else:hi=m
    d=(lo+hi)/2;return math.degrees(math.atan2(y/(B0+d),x/(A0+d)))%360,d
def _circ(ks,t):
    ks=sorted(ks)
    for (t0,v0),(t1,v1) in zip(ks,ks[1:]+[(ks[0][0]+360,ks[0][1])]):
        tt=t if t>=t0 else t+360
        if t0<=tt<=t1:return v0+(v1-v0)*(tt-t0)/((t1-t0) or 1)
    return ks[0][1]
def _edges(poly,step=0.5):
    out=[]
    for i in range(len(poly)):
        (x0,y0),(x1,y1)=poly[i][:2],poly[(i+1)%len(poly)][:2];n=max(1,int(math.hypot(x1-x0,y1-y0)/step))
        out+=[(x0+(x1-x0)*k/n,y0+(y1-y0)*k/n) for k in range(n)]
    return out
def _boxpoly(b):
    t=math.radians(b['t']);c=((A0+b['d'])*math.cos(t),(B0+b['d'])*math.sin(t))
    if 'yaw' in b:a=math.radians(b['yaw']);tg=(math.cos(a),math.sin(a));rd=(-tg[1],tg[0])
    else:
        g=(-A0*math.sin(t),B0*math.cos(t));L=math.hypot(*g);tg=(g[0]/L,g[1]/L);rd=(tg[1],-tg[0])
        if rd[0]*c[0]+rd[1]*c[1]<0:rd=(-rd[0],-rd[1])
    w,dp=b['w']/2,b['dep']/2
    return [(c[0]+tg[0]*s*w+rd[0]*r*dp,c[1]+tg[1]*s*w+rd[1]*r*dp) for s,r in ((-1,-1),(1,-1),(1,1),(-1,1))]
def fit(kedge,prisms,boxes,towers,margin=3.0):
    pts=[]
    for pr in prisms:pts+=_edges(pr['bot'])
    for b in boxes:
        if b.get('z0',0)<=0.01:pts+=_edges(_boxpoly(b))
    tw=[(x,y) for x,y in towers.values()]
    env=[-1e9]*360
    for x,y,r in [(x,y,0.0) for x,y in pts]+[(x,y,1.2) for x,y in tw]:
        t,d=td(x,y);rr=math.hypot(x,y);sp=math.degrees((margin+r)/max(rr,1))
        for k in range(int(math.floor(t-sp)),int(math.ceil(t+sp))+1):
            env[k%360]=max(env[k%360],d+r+margin)
    return [(float(t),max(_circ(kedge,t),env[t])) for t in range(360)]
