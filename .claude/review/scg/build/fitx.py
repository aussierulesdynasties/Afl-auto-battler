import numpy as np,json,math,sys
CW=60
from scipy.optimize import least_squares
exec(open('cam.py').read())
cj=json.load(open('cam.json'));T=np.array(cj['T']);H=cj['p'][9]
order=['F','A','B','C','D','E']  # N,NE,SE,S,SW,W
pitch=dens(G['4000006'],12);pitch=np.c_[pitch,np.zeros(len(pitch))]
def fit(HEAD,SHAFT,W,Hh,p0,GR=None,wg=0.5,extra=None,free_c=True):
    def res(q):
        p=list(q)+[H];r=[]
        for k,v in HEAD.items():
            i=order.index(k);r+=list(proj(p,[(*T[i],H)])[0]-np.array(v))
        for k,L in SHAFT.items():
            i=order.index(k);a,b=proj(p,[(*T[i],0),(*T[i],H)]);t=(b-a)/np.linalg.norm(b-a);n=np.array([-t[1],t[0]])
            for v in L:r.append(float((np.array(v)-a)@n))
        if extra:
            for X,v in extra:r+=list(proj(p,[X])[0]-np.array(v))
        if GR is not None:
            pp=proj(p,pitch);r+=list(np.sqrt(((GR[:,None,:]-pp[None])**2).sum(-1)).min(1)*wg)
        return np.array(r)
    lo=[-4e3,-4e3,30,-math.pi*2,-1.5,-0.5,300,W/2-CW,Hh/2-CW];hi=[4e3,4e3,4e3,math.pi*2,-0.05,0.5,20000,W/2+CW,Hh/2+CW]
    q=np.clip(np.array(p0,float),np.array(lo)+1e-6,np.array(hi)-1e-6)
    s=least_squares(res,q,bounds=(lo,hi))
    nt=2*len(HEAD)+sum(len(v) for v in SHAFT.values())
    print('tower rms',round(math.sqrt((s.fun[:nt]**2).mean()),2),np.round(s.fun[:nt],1))
    if GR is not None:print('grass rms',round(math.sqrt((s.fun[nt:]**2).mean())/wg,2))
    return list(s.x)+[H]
def multistart(HEAD,SHAFT,W,Hh,GR,wg=0.5,azs=range(0,360,20),**kw):
    best=None;PCc=np.array([0.94,-11.82,0])
    for az in azs:
        for d in (500,800,1200,1800):
            for el in (25,40,55):
                a=math.radians(az);e=math.radians(el)
                C=PCc+d*np.array([math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)])
                v=(PCc-C)/d;yaw=math.atan2(v[1],v[0]);pit=math.asin(v[2])
                for f in (W*1.2,W*2.0):
                    import io,contextlib
                    with contextlib.redirect_stdout(io.StringIO()):p=fit(HEAD,SHAFT,W,Hh,[*C,yaw,pit,0,f,W/2,Hh/2],GR,wg,**kw)
                    c=cost(HEAD,SHAFT,p,GR,wg)
                    if best is None or c<best[0]:best=(c,p)
    p=best[1];fit(HEAD,SHAFT,W,Hh,p[:9],GR,wg,**kw);return p
def cost(HEAD,SHAFT,p,GR,wg):
    r=[]
    for k,v in HEAD.items():r+=list(proj(p,[(*T[order.index(k)],H)])[0]-np.array(v))
    pp=proj(p,pitch);g=np.sqrt(((GR[:,None,:]-pp[None])**2).sum(-1)).min(1)*wg if GR is not None else []
    return float(np.sum(np.square(r))+np.sum(np.square(g)))
