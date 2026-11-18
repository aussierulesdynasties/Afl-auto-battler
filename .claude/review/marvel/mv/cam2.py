from cam import *
import json
_C=json.load(open('c3_k1.json'));P=_C['p'];K1=_C['k1'];HH=_C['h']
CEN=np.array([960,540.])
def dis(uv):
    uv=np.atleast_2d(np.asarray(uv,float));d=(uv-CEN)/1000;r2=(d**2).sum(1,keepdims=True);return CEN+d*1000*(1+K1*r2)
def und(uv):
    uv=np.atleast_2d(np.asarray(uv,float));x=uv.copy()
    for _ in range(20):x=x+(uv-dis(x))
    return x
def P2(X):return dis(proj(P,X))          # world -> photo pixel (m.png)
def ray2(u,v):x=und([(u,v)])[0];return ray(P,*x)
def at_z2(u,v,z=0.0):x=und([(u,v)])[0];return at_z(P,*x,z)
def height2(xy,uv):x=und([uv])[0];return height(P,xy,x)
