# Plane-sweep match: a pick (view A,u,v) -> best 3D point by NCC along the ray against other views.
import sys,json,cv2,numpy as np;sys.path.insert(0,'work');import earthcam as E,tri as T
IM={}
def img(v):
    if v not in IM: IM[v]=cv2.cvtColor(cv2.imread(f'ge/{v}.png'),cv2.COLOR_BGR2GRAY).astype(np.float32)
    return IM[v]
def patch(v,X,ex,ey,R=12):
    c=T.camv(v);p0=E.proj(c,X);px=E.proj(c,X+ex)-p0;py=E.proj(c,X+ey)-p0
    g=np.arange(-R,R+1);gx,gy=np.meshgrid(g,g)
    mx=(p0[0]+gx*px[0]+gy*py[0]).astype(np.float32);my=(p0[1]+gx*px[1]+gy*py[1]).astype(np.float32)
    if mx.min()<0 or my.min()<90 or mx.max()>1919 or my.max()>1040: return None
    return cv2.remap(img(v),mx,my,cv2.INTER_LINEAR)
def ncc(a,b):
    a=a-a.mean();b=b-b.mean();d=np.sqrt((a*a).sum()*(b*b).sum());return (a*b).sum()/d if d>1e-6 else -1
def match(A,u,v,Bs,zr=(-3,95),R=12):
    o,d=T.ray(A,u,v);c=T.camv(A)
    best=[]
    for B in Bs:
        sc=[]
        for z in np.arange(zr[0],zr[1],0.25):
            s=(z-o[2])/d[2];X=o+s*d;k=s/c['f']  # metres per A pixel at that depth
            pa=patch(A,X,c['right']*k,-c['up']*k,R);pb=patch(B,X,c['right']*k,-c['up']*k,R)
            if pa is None or pb is None: continue
            sc.append((ncc(pa,pb),z,X))
        if sc: best.append(max(sc,key=lambda t:t[0])+(B,))
    return best
if __name__=='__main__':
    A=sys.argv[1];Bs=sys.argv[2].split(',')
    for s in sys.argv[3:]:
        u,v=map(float,s.split(','))
        for n,z,X,B in match(A,u,v,Bs): print(f'{A} {u:.0f},{v:.0f} vs {B}: ncc {n:.2f}  X {X[0]:.1f} {X[1]:.1f} {X[2]:.1f}')
