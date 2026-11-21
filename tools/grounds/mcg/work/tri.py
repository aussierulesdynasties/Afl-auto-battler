# Triangulate 3D points from pixel picks in GE views (cams.json). Usage: python work/tri.py "view:u:v view:u:v ..." [...]
# or import: tri([(view,u,v),...]) -> (xyz, rms px)
import sys,json,numpy as np;sys.path.insert(0,'work');import earthcam as E
C=json.load(open('work/cams.json'))
def camv(v):
    x0,y0,a,d,h,t=C[v];return E.cam(h,t,d,tz=a-13,tx=x0,ty=y0)
def ray(v,u,w):
    c=camv(v);dx=(u-c['W']/2)/c['f'];dy=-(w-c['H']/2)/c['f']
    r=c['fwd']+dx*c['right']+dy*c['up'];return c['C'],r/np.linalg.norm(r)
def tri(P):
    A=np.zeros((3,3));b=np.zeros(3)
    for v,u,w in P:
        o,d=ray(v,u,w);M=np.eye(3)-np.outer(d,d);A+=M;b+=M@o
    X=np.linalg.solve(A,b)
    e=[np.linalg.norm(E.proj(camv(v),X)-[u,w]) for v,u,w in P]
    return X,float(np.sqrt(np.mean(np.square(e))))
def onz(v,u,w,z):
    o,d=ray(v,u,w);s=(z-o[2])/d[2];return o+s*d
if __name__=='__main__':
    for a in sys.argv[1:]:
        P=[(s.split(':')[0],float(s.split(':')[1]),float(s.split(':')[2])) for s in a.split()]
        X,e=tri(P);print(' '.join(f'{x:.1f}' for x in X),f'rms {e:.1f}px')
