import numpy as np,json,math
W,H=1920,1080
def R(yaw,pitch_,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch_),math.sin(pitch_);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    X=np.atleast_2d(np.asarray(X,float));C=np.array(p[:3]);M=R(*p[3:6]);fo=p[6];d=(X-C)@M.T
    return np.stack([p[7]+fo*d[:,0]/d[:,2],p[8]-fo*d[:,1]/d[:,2]],1)
def ray(p,u,v):
    M=R(*p[3:6]);d=np.array([(u-p[7])/p[6],-(v-p[8])/p[6],1.0]);w=M.T@d;return w/np.linalg.norm(w)
def at_z(p,u,v,z=0.0):
    C=np.array(p[:3]);w=ray(p,u,v);t=(z-C[2])/w[2];return C+t*w
def height(p,base_xy,top_uv):
    C=np.array(p[:3]);w=ray(p,*top_uv);A=np.array([[w[0]],[w[1]]]);rhs=np.array([base_xy[0]-C[0],base_xy[1]-C[1]])
    t=np.linalg.lstsq(A,rhs,rcond=None)[0][0];return (C+t*w)[2]
la0,lo0=-37.816495302702705,144.9475565216216
def load_map():
    d=json.load(open('osm/map.json'));N={e['id']:e for e in d['elements'] if e['type']=='node'}
    def xy(n):return ((n['lon']-lo0)*111320.0*math.cos(math.radians(la0)),(n['lat']-la0)*110574.0)
    ways=[(e.get('tags',{}),[xy(N[n]) for n in e['nodes'] if n in N]) for e in d['elements'] if e['type']=='way']
    nodes=[(n.get('tags',{}),xy(n)) for n in N.values() if n.get('tags')]
    return ways,nodes
