import json,numpy as np
from PIL import Image,ImageDraw
from shapely.geometry import Polygon
from shapely.ops import unary_union
from scipy import ndimage
J=json.load(open('/home/user/Afl-auto-battler/.claude/review/marvel/mv2/parts2.json'));C0=np.zeros(3)
cal=json.load(open('calib_top.json'));HC=905.4;W,H=1280,720
def proj(E,N,Z):
    k=HC/(HC-Z);E=E*k;N=N*k;c,s=np.cos(cal['th']),np.sin(cal['th'])
    return W/2+cal['tx']+(c*E-s*N)/cal['mpp'], H/2+cal['ty']-(s*E+c*N)/cal['mpp']
polys=[];ZM=[]
for p in J['parts']:
    nm=p['name']
    if not (nm in('slab_w','slab_e','end_n','end_s') or nm.endswith('_gutter')):continue
    V=np.array(p['V'])-C0;x,y=proj(V[:,0],V[:,1],V[:,2])
    for f in p['F']:
        q=Polygon(list(zip(x[f],y[f]))).buffer(0)
        if q.area>0.01:polys.append(q)
U=unary_union([q.buffer(0.4) for q in polys]).buffer(-0.4)
G=max(U.geoms,key=lambda g:g.area) if U.geom_type=='MultiPolygon' else U
ring=G.exterior;L=ring.length
im=np.asarray(Image.open('/tmp/claude-0/ref/geA/ge_top.png').convert('RGB'),float);lum=ndimage.gaussian_filter(im.mean(2),1.0)
mpp=cal['mpp']*(HC-40)/HC  # m per px at roof height (the arcs are at 33 m: 0.8% off, under 0.05 m here)
res=[];vis=Image.open('/tmp/claude-0/ref/geA/ge_top.png').convert('RGB');D=ImageDraw.Draw(vis)
cx,cy=G.centroid.x,G.centroid.y
for i in range(int(L/ (1.0/mpp))):
    a=np.array(ring.interpolate(i/mpp).coords[0]);b=np.array(ring.interpolate(i/mpp+0.5).coords[0])
    t=b-a;t/=np.linalg.norm(t)+1e-9;n=np.array([t[1],-t[0]])
    if np.dot(n,a-[cx,cy])<0:n=-n
    ks=np.arange(-12/mpp,12/mpp+0.01,0.5)
    P=a[None,:]+ks[:,None]*n[None,:]
    if P[:,1].min()<60 or P[:,0].min()<2 or P[:,0].max()>W-2 or P[:,1].max()>H-2:continue
    prof=ndimage.map_coordinates(lum,[P[:,1],P[:,0]],order=1)
    g=-(np.gradient(prof))  # bright inside -> dark outside: positive
    w=int(round(2.0/mpp/0.5))
    def ok_(i):
        if i-w<0 or i+w>=len(prof):return False
        inn=prof[i-w:i-1].mean();out=prof[i+2:i+w].mean()
        return inn>185 and out<inn-25
    pk=[i for i in range(1,len(g)-1) if g[i]>=g[i-1] and g[i]>=g[i+1] and g[i]>12 and abs(ks[i]*mpp)<=6 and ok_(i)]
    if not pk:continue
    j=min(pk,key=lambda i:abs(ks[i]))
    ang=np.degrees(np.arctan2(-(a[1]-cy),a[0]-cx))
    res.append((ang,ks[j]*mpp,g[j],a[0],a[1]))
    q=P[j];D.point(tuple(q),fill=(0,255,0))
    D.point(tuple(a),fill=(255,0,0))
R=np.array(res);json.dump(R.tolist(),open('meas.json','w'))
vis.save('meas_vis_strict.png')
ok=R[:,2]>6
d=R[ok,1]
print('samples',len(R),'with a clear edge',ok.sum())
print('offset m (GE edge minus model edge, + = GE outside): median %.2f mean |d| %.2f p90 |d| %.2f max |d| %.2f'%(np.median(d),np.mean(np.abs(d)),np.percentile(np.abs(d),90),np.abs(d).max()))
for a0 in range(-180,180,30):
    s=ok&(R[:,0]>=a0)&(R[:,0]<a0+30)
    if s.sum():print('sector %4d..%4d n=%3d median %+.2f p90|d| %.2f'%(a0,a0+30,s.sum(),np.median(R[s,1]),np.percentile(np.abs(R[s,1]),90)))

# ---- per segment, in the stadium frame
U=np.array([0.33632,-0.94215]);V=np.array([-0.94215,-0.33632])
c,s=np.cos(cal['th']),np.sin(cal['th']);k=(HC-40)/HC
x=(R[:,3]-W/2-cal['tx'])*cal['mpp']*k;y=-(R[:,4]-H/2-cal['ty'])*cal['mpp']*k
E=c*x+s*y;N=-s*x+c*y;u=E*U[0]+N*U[1];v=E*V[0]+N*V[1]
cls=np.where((v>95)&(np.abs(u)<82),'W slab outer edge',np.where((v<-95)&(np.abs(u)<82),'E slab outer edge',np.where(u<-86,'N end roof arc',np.where(u>86,'S end roof arc','slab ends/corners'))))
good=(R[:,2]>10)&(np.abs(R[:,1])<8)
out={}
for C in sorted(set(cls)):
    m=cls==C;g=m&good;d=R[g,1]
    out[C]=dict(n=int(m.sum()),matched=int(g.sum()),median=float(np.median(d)) if len(d) else None,
        within1=float(np.mean(np.abs(d)<=1)) if len(d) else 0,within2=float(np.mean(np.abs(d)<=2)) if len(d) else 0,p90=float(np.percentile(np.abs(d),90)) if len(d) else None)
    print('%-20s samples %3d matched %3d  median %+.2f m  |d|<=1m %3.0f%%  |d|<=2m %3.0f%%  p90 %.2f m'%(C,m.sum(),g.sum(),np.median(d),100*np.mean(np.abs(d)<=1),100*np.mean(np.abs(d)<=2),np.percentile(np.abs(d),90)))
json.dump(out,open('seg_near.json','w'),indent=1)
print('--- along the arcs and the east edge, by v (stadium frame)')
for C in('N end roof arc','S end roof arc'):
    for v0 in range(-80,80,20):
        m=(cls==C)&good&(v>=v0)&(v<v0+20)
        if m.sum()>3:print('%s v %4d..%4d n=%2d median %+.2f'%(C,v0,v0+20,m.sum(),np.median(R[m,1])))
for u0 in range(-80,80,20):
    m=(cls=='E slab outer edge')&good&(u>=u0)&(u<u0+20)
    if m.sum()>3:print('E slab u %4d..%4d n=%2d median %+.2f'%(u0,u0+20,m.sum(),np.median(R[m,1])))
# ---- refit the end-roof arcs' measured points to the trace
NP=[(-84.3,74),(-90,68),(-98,61),(-105.5,52.5),(-112,40),(-115,35),(-118,23.5),(-119.5,15),(-120,0),(-119.25,-15),(-116.25,-30),(-113.75,-35),(-108,-45),(-98,-60),(-90,-67),(-84.1,-74)]
SP=[(84.6,-74),(90,-69),(97,-64),(103.5,-60),(114.5,-40),(116.25,-35),(120.5,-15),(124.5,0),(122.75,10),(120.5,15),(117.5,35),(115,40),(110,50),(103.5,60),(97,64),(90,69),(84,74)]
sel=good&((cls=='N end roof arc')|(cls=='S end roof arc'))
uu,vv,dd=u[sel],v[sel],R[sel,1]
out={}
for nm,PTS,sg in(('NP',NP,-1),('SP',SP,1)):
    new=[]
    for pu,pv in PTS:
        m=(np.sign(uu)==sg)&(np.hypot(uu-pu,vv-pv)<9)
        if m.sum()>=3 and abs(pu)>86:
            d=float(np.median(dd[m]));c=np.array([sg*40.0,0]);nrm=np.array([pu,pv])-c;nrm/=np.linalg.norm(nrm)
            q=np.array([pu,pv])+nrm*d;new.append((round(float(q[0]),2),round(float(q[1]),2),round(d,2),int(m.sum())))
        else:new.append((pu,pv,None,int(m.sum())))
    out[nm]=new
    for r_ in new:print(nm,r_)
json.dump(out,open('arcfit.json','w'))
# ---- the trace itself (Google Earth edge points in the stadium frame) and one smooth curve per end
from scipy import optimize as OPT
def trace(C):
    m=good&(cls==C);pts=[]
    for i in np.where(m)[0]:
        a=np.array([R[i,3],R[i,4]])
        pts.append((u[i],v[i],R[i,1]))
    return np.array(pts)
fits={}
for C,sg in(('N end roof arc',-1),('S end roof arc',1)):
    T=trace(C)
    # these edges are at the gutter's height (33 m), not the 40 m used to classify: redo their frame position
    m_=good&(cls==C);k2=(HC-33.0)/HC
    x2=(R[m_,3]-W/2-cal['tx'])*cal['mpp']*k2;y2=-(R[m_,4]-H/2-cal['ty'])*cal['mpp']*k2
    c_,s_=np.cos(cal['th']),np.sin(cal['th']);E2=c_*x2+s_*y2;N2=-s_*x2+c_*y2;T[:,0]=E2*U[0]+N2*U[1];T[:,1]=E2*V[0]+N2*V[1]
    # GE point = model point moved along the outward normal (about the arc centre u=sg*40) by d
    c=np.array([sg*40.0,0]);P=T[:,:2];n=(P-c)/np.linalg.norm(P-c,axis=1)[:,None];G=P+n*T[:,2:3]
    def res(q):
        cu,cv,r=q;return np.hypot(G[:,0]-cu,G[:,1]-cv)-r
    q=OPT.least_squares(res,[sg*40,0,80],loss='soft_l1',f_scale=1.0).x
    e=res(q);fits[C]=dict(centre=[float(q[0]),float(q[1])],radius=float(q[2]),n=len(G),median_abs=float(np.median(np.abs(e))),p90=float(np.percentile(np.abs(e),90)))
    print(C,'circle centre (%.2f, %.2f) r %.2f  n=%d  |err| median %.2f p90 %.2f max %.2f'%(q[0],q[1],q[2],len(G),np.median(np.abs(e)),np.percentile(np.abs(e),90),np.abs(e).max()))
    # how far the current model arc is from that circle
    A=np.array(NP if sg<0 else SP,float);print('   model arc points vs circle:',np.round(np.hypot(A[:,0]-q[0],A[:,1]-q[1])-q[2],2))
json.dump(fits,open('circfit.json','w'))
