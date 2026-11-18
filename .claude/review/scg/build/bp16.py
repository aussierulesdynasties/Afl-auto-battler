# back-project photo-16 pixels onto the wall line r=rw(d)+off: returns (deg, z, s along the roof edge)
import sys;exec(open('cam.py').read());exec(open('meas.py').read().split('def theta')[0]);_c=json.load(open('cam16.json'));p=np.array(_c['p']);C=p[:3];M=R(*p[3:6]);fo=p[6];cx0,cy0=p[7],p[8]
_GO=polar(G['598232976'])[:,1]
def rw(d):return float(_GO[int(round((d%360)*2))%720])+7.5
def ray(u,v):
    d=np.array([(u-cx0)/fo,-(v-cy0)/fo,1.0]);w=M.T@d;return w/np.linalg.norm(w)
def hit(u,v,off=0.0):
    w=ray(u,v);best=None
    for t in np.linspace(100,1500,14001):
        X=C+t*w;r=math.hypot(X[0]-PC[0],X[1]-PC[1]);d=math.degrees(math.atan2(X[1]-PC[1],X[0]-PC[0]))%360
        if r<=rw(d)+off:return d,X[2],t
    return None
J=json.load(open('g/uw16b.png.json'));S_=np.array(J['s']);D_=np.array(J['ds'])
for a in sys.argv[1:]:
    n,uv=a.split('=');u,v=map(float,uv.split(','));h=hit(u,v)
    print(f'{n:14s} u{u:7.1f} v{v:6.1f} -> {h[0]:7.2f} deg  z {h[1]:5.1f}  s {np.interp(h[0],D_,S_):6.1f}' if h else n+' miss')
