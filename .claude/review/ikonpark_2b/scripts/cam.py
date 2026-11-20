import json,numpy as np,math
g=json.load(open('osm/geo.json',encoding='utf-8'))
def R(yaw,pitch,roll):
    cy,sy,cp,sp=np.cos(yaw),np.sin(yaw),np.cos(pitch),np.sin(pitch)
    f=np.array([cy*cp,sy*cp,sp]); r=np.array([sy,-cy,0.]); u=np.cross(r,f)
    cr,sr=np.cos(roll),np.sin(roll)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def load(fn):
    q=np.array(json.load(open(fn))['q']);return q
def mk(q):
    p=q[:9];C=p[:3];M=R(*p[3:6]);fo=p[6];cx0,cy0=p[7],p[8]
    class K:pass
    k=K();k.p=p;k.C=C;k.M=M
    def proj(X):
        X=np.atleast_2d(np.array(X,float))
        if X.shape[1]==2:X=np.c_[X,np.zeros(len(X))]
        d=(X-C)@M.T;return np.c_[cx0+fo*d[:,0]/d[:,2],cy0-fo*d[:,1]/d[:,2]]
    def ray(u,v):
        d=np.array([(u-cx0)/fo,-(v-cy0)/fo,1.0]);w=M.T@d;return w/np.linalg.norm(w)
    def at_z(u,v,z=0.0):
        w=ray(u,v);t=(z-C[2])/w[2];return C+t*w
    def at_xy(u,v,b):
        w=ray(u,v);A=np.array([[w[0]],[w[1]]]);rhs=np.array([b[0]-C[0],b[1]-C[1]]);t=np.linalg.lstsq(A,rhs,rcond=None)[0][0];return C+t*w
    def height(base,top):
        b=at_z(*base);return at_xy(*top,b[:2])[2]
    def hit_poly(u,v,poly,zmax=80):
        # first crossing of the ray (ground track) with polygon edges, return point with z
        w=ray(u,v);best=None
        P=np.array(poly)
        for i in range(len(P)):
            a,b=P[i],P[(i+1)%len(P)]
            # solve C.xy + t w.xy = a + s(b-a)
            A=np.array([[w[0],-(b-a)[0]],[w[1],-(b-a)[1]]])
            try: t,s=np.linalg.solve(A,a-C[:2])
            except: continue
            if 0<=s<=1 and t>0:
                X=C+t*w
                if -5<X[2]<zmax and (best is None or t<best[0]):best=(t,X)
        return None if best is None else best[1]
    k.proj=proj;k.ray=ray;k.at_z=at_z;k.at_xy=at_xy;k.height=height;k.hit_poly=hit_poly
    return k
