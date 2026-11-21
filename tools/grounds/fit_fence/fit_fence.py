import numpy as np, sys, json
def load(p):
    v = np.fromfile(p, dtype=np.float32).reshape(-1,3,3).astype(np.float64)
    return v
def floor_at(T, c):
    # triangles under point c (2D xz) that are near-horizontal
    a=T[:,0][:,[0,2]]; b=T[:,1][:,[0,2]]; d=T[:,2][:,[0,2]]
    def cross(u,v): return u[:,0]*v[:,1]-u[:,1]*v[:,0]
    p=np.array(c)
    s1=cross(b-a,p-a); s2=cross(d-b,p-b); s3=cross(a-d,p-d)
    inside=((s1>=0)&(s2>=0)&(s3>=0))|((s1<=0)&(s2<=0)&(s3<=0))
    ys=T[inside][:,:,1].mean(axis=1)
    return sorted(ys.tolist())
def segments(T, h):
    y=T[:,:,1]
    m=(y.min(1)<h)&(y.max(1)>h)
    t=T[m]; segs=[]
    pts=[]
    for i,j in ((0,1),(1,2),(2,0)):
        a=t[:,i]; b=t[:,j]
        cr=((a[:,1]-h)*(b[:,1]-h))<0
        f=np.where(cr,(h-a[:,1])/np.where(cr,b[:,1]-a[:,1],1),np.nan)
        q=a+(b-a)*f[:,None]
        pts.append(q[:,[0,2]])
    P=np.stack(pts,1) # n,3,2 with nan for non crossing edges
    out=[]
    for k in range(P.shape[0]):
        r=P[k][~np.isnan(P[k][:,0])]
        if len(r)>=2: out.append(r[:2])
    return np.array(out)
def rays(S, c, n=720, rmin=40):
    A=S[:,0]-c; B=S[:,1]-c
    hits=[]
    for k in range(n):
        th=2*np.pi*k/n; d=np.array([np.cos(th),np.sin(th)])
        e=B-A
        den=d[0]*e[:,1]-d[1]*e[:,0]
        ok=np.abs(den)>1e-9
        den=np.where(ok,den,1)
        t=(A[:,0]*e[:,1]-A[:,1]*e[:,0])/den
        u=(A[:,0]*d[1]-A[:,1]*d[0])/den
        good=ok&(u>=0)&(u<=1)&(t>rmin)
        if good.any(): hits.append(c+d*t[good].min())
    return np.array(hits)
def fit_ellipse(P):
    x=P[:,0]; y=P[:,1]
    D=np.stack([x*x,x*y,y*y,x,y,np.ones_like(x)],1)
    _,_,V=np.linalg.svd(D); a,b,cc,d,e,f=V[-1]
    M=np.array([[a,b/2],[b/2,cc]])
    ctr=np.linalg.solve(2*M,[-d,-e])
    f0=f+ (a*ctr[0]**2+b*ctr[0]*ctr[1]+cc*ctr[1]**2) - (a*ctr[0]**2*2+b*ctr[0]*ctr[1]*2+cc*ctr[1]**2*2) + (-d*ctr[0]-e*ctr[1])*0
    # simpler: evaluate constant at centre
    k=-(a*ctr[0]**2+b*ctr[0]*ctr[1]+cc*ctr[1]**2+d*ctr[0]+e*ctr[1]+f)
    w,U=np.linalg.eigh(M/k)
    ax=1/np.sqrt(w)
    return ctr, ax, U
def resid(P,ctr,ax,U):
    q=(P-ctr)@U
    return (np.sqrt((q[:,0]/ax[0])**2+(q[:,1]/ax[1])**2)-1)*ax.min()
def analyse(T, h_off=0.5, c0=None, floor=None):
    tall=T[T[:,:,1].max(1)>T[:,:,1].min()+0]
    if c0 is None:
        hi=T[T[:,:,1].mean(1)>8]
        xz=hi[:,:,[0,2]].reshape(-1,2)
        c0=(xz.min(0)+xz.max(0))/2
    c=np.array(c0,float)
    if floor is None:
        f=floor_at(T,c)
        floor=max(f) if f else 0.0
    for it in range(3):
        S=segments(T,floor+h_off)
        H=rays(S,c)
        P=H
        for k in range(4):
            ctr,ax,U=fit_ellipse(P)
            r=np.abs(resid(P,ctr,ax,U))
            P=P[r<max(2.0,np.percentile(r,80))]
        c=ctr
    long=U[:, np.argmax(ax)]
    ang=np.degrees(np.arctan2(long[1],long[0]))
    return dict(centre=[round(c[0],2),round(c[1],2)],floor=round(floor,2),half=[round(ax.max(),2),round(ax.min(),2)],long_deg=round(ang,1),kept=len(P),hits=len(H))
if __name__=="__main__":
    for p in sys.argv[1:]:
        T=load(p)
        try: print(p.split('/')[-1], analyse(T))
        except Exception as e: print(p, "ERR", e)

def inside_ellipse(T, ctr, ax, U, grow=1.03):
    q=(T[:,:,[0,2]].mean(1)-ctr)@U
    return ((q[:,0]/(ax[0]*grow))**2+(q[:,1]/(ax[1]*grow))**2)<=1
def analyse2(T):
    hi=T[T[:,:,1].mean(1)>8]
    xz=hi[:,:,[0,2]].reshape(-1,2); c=(xz.min(0)+xz.max(0))/2
    floor=0.0
    log=[]
    for it in range(4):
        S=segments(T,floor+0.5)
        H=rays(S,c); P=H
        for k in range(4):
            ctr,ax,U=fit_ellipse(P)
            r=np.abs(resid(P,ctr,ax,U))
            P=P[r<max(1.5,np.percentile(r,85))]
        c=ctr
        m=inside_ellipse(T,ctr,ax,U)
        nf=float(np.percentile(T[m][:,:,1],1)) if m.any() else floor
        log.append((round(floor,2),round(ax.max(),1),round(ax.min(),1)))
        if abs(nf-floor)<0.05: floor=nf; break
        floor=nf
    long=U[:, np.argmax(ax)]
    ang=float(np.degrees(np.arctan2(long[1],long[0])))
    r=np.abs(resid(H,ctr,ax,U))
    return dict(centre=[round(float(c[0]),2),round(float(c[1]),2)],floor=round(floor,2),half=[round(float(ax.max()),2),round(float(ax.min()),2)],long_deg=round(ang,1),fit_rms=round(float(np.sqrt(np.mean(np.minimum(r,10)**2))),2),within1m=round(float((r<1).mean()),2),log=log)
