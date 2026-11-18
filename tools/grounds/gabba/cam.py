import numpy as np,json,math
G=json.load(open('osm/geo.json'));geo=G['geo'];tags=G['tags']
W,H=1600,1066
sails=[np.array(geo[k]) for k,t in tags.items() if t.get('building:part')=='roof']
C0=np.array([5.0,-4.0])
def ringpts(which):
    pts=[]
    for s in sails:
        r=np.hypot(*(s-C0).T);
        idx=np.argsort(r);sel=s[idx[-2:]] if which=='o' else s[idx[:2]]
        pts+=list(sel)
    pts=np.array(pts);a=np.arctan2(pts[:,1]-C0[1],pts[:,0]-C0[0]);pts=pts[np.argsort(a)]
    # densify closed
    out=[]
    for i in range(len(pts)):
        p,q=pts[i],pts[(i+1)%len(pts)]
        for t in np.linspace(0,1,12,endpoint=False):out.append(p*(1-t)+q*t)
    return np.array(out)
RO=ringpts('o');RI=ringpts('i')
def R(yaw,pitch_,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch_),math.sin(pitch_);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    C=p[:3];M=R(*p[3:6]);fo=p[6];d=(np.atleast_2d(np.array(X,float))-C)@M.T;a=d[:,0]/d[:,2];b=d[:,1]/d[:,2]
    k=p[31] if len(p)>31 else 0.0;g=1+k*(a*a+b*b)
    return np.stack([p[7]+fo*a*g,p[8]-fo*b*g],1)
    C=p[:3];M=R(*p[3:6]);fo=p[6];d=(np.atleast_2d(X)-C)@M.T
    return np.stack([p[7]+fo*d[:,0]/d[:,2],p[8]-fo*d[:,1]/d[:,2]],1)
def z3(P,z):return np.column_stack([P,np.full(len(P),z)])
