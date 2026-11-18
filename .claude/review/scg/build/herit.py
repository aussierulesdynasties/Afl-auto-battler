# heritage roofs: hip roof over any outline. Roof height = eave + slope x distance to the nearest wall
# (the shape a real hipped roof takes), capped at 'cap' metres; ridge points come from the outline's medial axis.
from shapely.geometry import Polygon as _SP,Point as _Pt
from scipy.spatial import Voronoi as _Vor,Delaunay as _Del
def hiproof(W_,ze,slope,cap,mroof,mwall,walls=True,step=0.6):
    W_=np.array(W_,float);pg=_SP(W_)
    if not pg.is_valid:pg=pg.buffer(0)
    pg=pg.simplify(1.0,preserve_topology=True);W_=np.array(pg.exterior.coords)[:-1]   # drop pixel-read wobble (<1 m): each wobble was a stray hip
    if pg.exterior.is_ccw is False:W_=W_[::-1]
    bnd=[]
    for i in range(len(W_)):
        a,b=W_[i],W_[(i+1)%len(W_)];n=max(1,int(np.ceil(np.linalg.norm(b-a)/step)))
        for t in range(n):bnd.append(a+(b-a)*t/n)
    bnd=np.array(bnd);pts=list(bnd)
    vo=_Vor(bnd)
    for q in vo.vertices:
        if pg.contains(_Pt(q)) and pg.exterior.distance(_Pt(q))>0.25:pts.append(q)
    # dense interior grid: the roof planes are sampled every 'step' m so no long thin triangle cuts across a ridge (the lumps)
    x0,y0,x1,y1=pg.bounds
    for gx in np.arange(x0+step/2,x1,step):
        for gy in np.arange(y0+step/2,y1,step):
            q=_Pt(gx,gy)
            if pg.contains(q) and pg.exterior.distance(q)>step*0.4:pts.append(np.array([gx,gy]))
    pts=np.array(pts);dl=_Del(pts)
    zs=[ze+min(slope*pg.exterior.distance(_Pt(q)),cap) for q in pts]
    ids=[v(q[0],q[1],z) for q,z in zip(pts,zs)]
    for s in dl.simplices:
        c=pts[s].mean(0)
        if not pg.contains(_Pt(c)):continue
        a,b,c_=s
        e1=pts[b]-pts[a];e2=pts[c_]-pts[a]
        if e1[0]*e2[1]-e1[1]*e2[0]<0:b,c_=c_,b
        tri(ids[a],ids[b],ids[c_],mroof)
    if walls:
        for i in range(len(W_)):
            a,b=W_[i],W_[(i+1)%len(W_)]
            quad(v(a[0],a[1],0),v(b[0],b[1],0),v(b[0],b[1],ze),v(a[0],a[1],ze),mwall)
    return W_
def px_world(px,z):return [at_z(u_,w_,z)[:2] for u_,w_ in px]
def prism(cx,cy,r,n,z0,z1,m,rot=0.0):
    """n-sided upright prism (n=4 square tower, n=24 round drum)."""
    a=[rot+2*math.pi*i/n for i in range(n)]
    lo=[v(cx+r*math.cos(t),cy+r*math.sin(t),z0) for t in a];hi=[v(cx+r*math.cos(t),cy+r*math.sin(t),z1) for t in a]
    for i in range(n):j=(i+1)%n;quad(lo[i],lo[j],hi[j],hi[i],m)
    return hi
def cone(cx,cy,r,n,z0,z1,m,rot=0.0,bulge=0.0):
    """roof over a prism: straight cone/pyramid, or a dome when bulge>0 (profile r*(1-t^2) style)."""
    a=[rot+2*math.pi*i/n for i in range(n)];K=6 if bulge else 1;rings=[]
    for k in range(K+1):
        t=k/K;rk=r*(1-t) if not bulge else r*math.cos(t*math.pi/2);zk=z0+(z1-z0)*(t if not bulge else math.sin(t*math.pi/2))
        rings.append([v(cx+rk*math.cos(q),cy+rk*math.sin(q),zk) for q in a])
    for k in range(K):
        for i in range(n):j=(i+1)%n;quad(rings[k][i],rings[k][j],rings[k+1][j],rings[k+1][i],m)
