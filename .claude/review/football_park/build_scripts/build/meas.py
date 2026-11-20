import sys,json,math,numpy as np
sys.path.insert(0,'../b');from camlib import at_z,proj
from PIL import Image
A0,B0=72.5,88.5
def td(x,y):
    d=0.0
    for _ in range(40):
        t=math.atan2(y/(B0+d),x/(A0+d));d=math.hypot(x,y)/math.hypot(A0*math.cos(t)+0,B0*math.sin(t))*0  # placeholder
        # solve |P - ring(t,d)| along normal: use scaling so x=(A0+d)cos t, y=(B0+d) sin t
        f=lambda dd:(x/(A0+dd))**2+(y/(B0+dd))**2-1
        lo,hi=-70.0,800.0
        for _ in range(60):
            m=(lo+hi)/2
            if f(m)>0:lo=m
            else:hi=m
        d=(lo+hi)/2;t=math.atan2(y/(B0+d),x/(A0+d));break
    return math.degrees(t)%360,d
if __name__=='__main__':
    pB=json.load(open('../b/camB.json'))['p'];im=np.asarray(Image.open('../dl/comp_A1K6CR.jpg').convert('RGB')).astype(int)
    r,g,b=im[...,0],im[...,1],im[...,2];pink=(r>140)&(r-g>28)&(r-b>25)&(g>80)
    ys,xs=np.nonzero(pink[373:660,39:481]);ys+=373;xs+=39
    T=[];D=[]
    for u,v in zip(xs[::3],ys[::3]):
        X=at_z(pB,u+0.5,v+0.5,0);t,d=td(X[0],X[1])
        if 10<d<120:T.append(t);D.append(d)
    T=np.array(T);D=np.array(D)
    for t0 in range(0,360,10):
        m=(T>=t0)&(T<t0+10)
        if m.sum()>30:print(t0,m.sum(),np.percentile(D[m],[5,50,95]).round(1))
