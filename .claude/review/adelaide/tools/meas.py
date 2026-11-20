import sys;sys_argv=sys.argv;sys.argv=['x']
exec(open('tools/fitcam.py').read().split("if __name__")[0])
p=np.array(json.load(open('cam.json'))['p'])
PC=np.array(G['ways']['4681536']).mean(0)
def side(w,which):
    P=np.array(G['ways'][w]);n=len(P)-1;out=[]
    # orientation-independent: a vertex is 'in' if the segment's midpoint is closer to the pitch centre than the polygon centroid offset along that ray
    cen=P[:-1].mean(0)
    for i in range(n):
        a,b=P[i],P[i+1];m=(a+b)/2;d=b-a;nrm=np.array([d[1],-d[0]]);
        if (nrm@(m-cen))<0:nrm=-nrm  # outward normal
        facing_in=(nrm@(PC-m))>0
        if facing_in==(which=='in'):out.append((a,b))
    return out
def dense(segs,k=20):
    return np.array([a*(1-t)+b*t for a,b in segs for t in np.linspace(0,1,k)])
def fit_h(w,which,px,hs=np.arange(0,80,0.5)):
    S=dense(side(w,which));px=np.array(px,float);best=None
    for h in hs:
        q=proj(p,np.c_[S,np.full(len(S),h)]);dd=np.sqrt(((px[:,None]-q[None])**2).sum(-1)).min(1);m=dd.mean()
        if best is None or m<best[0]:best=(m,h,dd)
    return best
def ray(u,v):
    M=R(*p[3:6]);d=np.array([(u-p[7])/p[6],-(v-p[8])/p[6],1.0]);w=M.T@d;return w/np.linalg.norm(w)
def at_z(u,v,z=0.0):
    w=ray(u,v);t=(z-p[2])/w[2];return p[:3]+t*w
def height_above(u,v,xy):
    w=ray(u,v);C=p[:3];t=np.linalg.lstsq(w[:2,None],np.array(xy)-C[:2],rcond=None)[0][0];return (C+t*w)[2]
