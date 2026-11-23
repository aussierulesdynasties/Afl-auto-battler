# Marvel Stadium exterior, geometry in the stadium frame (u south+, v west+, z up from the street lawns).
# Measured values: sat/measures.md. Writes parts2.json: per part V (world xyz), F, M (material per face), UV (metres per corner).
import sys,os,json,math,numpy as np
MV=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','mv');sys.path.insert(0,MV);os.chdir(MV)
from sf import *
from scipy.interpolate import UnivariateSpline
PRM=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'prm.json'))) if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)),'prm.json')) else {}
def G(k,d):return PRM.get(k,d)
ZS=G('ZS',44.0);ZO=G('ZO',37.5);ZG=G('ZG',34.0);ZT=G('ZT',55.0);ZB=G('ZB',46.0);ZP=G('ZP',6.5);FL=G('FL',4.0)
OA,OB,ON=G('OA',118.0),G('OB',108.5),G('ON',2.5)
PARTS=[]
def wv(p):return np.asarray(uvw(p[0],p[1],p[2]),float).tolist()
def auto_uv(P):
    P=np.asarray(P,float);n=np.cross(P[1]-P[0],P[2]-P[0])
    if len(P)>3:n=n+np.cross(P[2]-P[0],P[3]-P[0])
    n=n/(np.linalg.norm(n)+1e-12)
    if abs(n[2])>0.7:return P[:,:2].tolist()
    t=np.array([-n[1],n[0]]);t/=np.linalg.norm(t)+1e-12;return np.stack([P[:,:2]@t,P[:,2]],1).tolist()
def add(name,V,F,M,UV=None):
    V=np.asarray(V,float);M=[M]*len(F) if isinstance(M,str) else M
    if UV is None:UV=[auto_uv(V[f]) for f in F]
    PARTS.append(dict(name=name,V=[wv(p) for p in V],F=[list(map(int,f)) for f in F],M=M,UV=UV))
# ---------------- primitives (all in u,v,z)
def prism(name,q,z0,z1,side,top,bottom=None,side_m=None):
    q=np.asarray(q,float);n=len(q)
    a=0.5*np.sum(q[:,0]*np.roll(q[:,1],-1)-np.roll(q[:,0],-1)*q[:,1])
    if a<0:q=q[::-1]
    V=[(x,y,z0) for x,y in q]+[(x,y,z1) for x,y in q]
    F=[[i,(i+1)%n,n+(i+1)%n,n+i] for i in range(n)];M=[side_m[i] if side_m else side for i in range(n)]
    F.append(list(range(n,2*n)));M.append(top)
    if bottom:F.append(list(range(n))[::-1]);M.append(bottom)
    add(name,V,F,M)
def box(name,u0,u1,v0,v1,z0,z1,side,top,bottom=None):prism(name,[(u0,v0),(u1,v0),(u1,v1),(u0,v1)],z0,z1,side,top,bottom)
def beamV(a,b,w):
    a=np.asarray(a,float);b=np.asarray(b,float);d=b-a;L=np.linalg.norm(d);d/=L
    u=np.cross(d,[0,0,1.0])
    if np.linalg.norm(u)<1e-3:u=np.array([1.0,0,0])
    u/=np.linalg.norm(u);v=np.cross(u,d);h=w/2
    c=[a+h*(su*u+sv*v) for su,sv in((-1,-1),(1,-1),(1,1),(-1,1))]+[b+h*(su*u+sv*v) for su,sv in((-1,-1),(1,-1),(1,1),(-1,1))]
    F=[[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7],[3,2,1,0],[4,5,6,7]]
    UV=[[(0,0),(w,0),(w,L),(0,L)]]*4+[[(0,0),(w,0),(w,w),(0,w)]]*2
    return c,F,UV
def beams(name,segs,w,mat):
    V=[];F=[];UV=[]
    for a,b in segs:
        c,f,uv=beamV(a,b,w);o=len(V);V+=c;F+=[[o+i for i in ff] for ff in f];UV+=uv
    add(name,V,F,mat,UV)
def cyl(name,c,r,z0,z1,mat,top,k=20):
    a=np.linspace(0,2*np.pi,k,endpoint=False);q=np.stack([c[0]+r*np.cos(a),c[1]+r*np.sin(a)],1);n=k
    V=[(x,y,z0) for x,y in q]+[(x,y,z1) for x,y in q];F=[[i,(i+1)%n,n+(i+1)%n,n+i] for i in range(n)]+[list(range(n,2*n))]
    ar=2*np.pi*r/k;UV=[[(i*ar,z0),((i+1)*ar,z0),((i+1)*ar,z1),(i*ar,z1)] for i in range(n)]+[auto_uv(np.array(V)[list(range(n,2*n))])]
    add(name,V,F,[mat]*n+[top],UV)
def loft(name,rings,mats,closed=True):
    # rings: list of (K,3) arrays; band j between ring j and j+1 gets mats[j] (str or per-segment list)
    R=[np.asarray(r,float) for r in rings];K=len(R[0]);V=[];F=[];M=[];UV=[]
    for r in R:V+=r.tolist()
    acc=0.0;prof=[0.0]
    for j in range(len(R)-1):acc+=np.mean(np.linalg.norm(R[j+1]-R[j],axis=1));prof.append(acc)
    for j in range(len(R)-1):
        arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(np.r_[R[j],R[j][:1]] if closed else R[j],axis=0)[:,:2],axis=1))]
        for i in range(K if closed else K-1):
            i2=(i+1)%K;F.append([j*K+i,j*K+i2,(j+1)*K+i2,(j+1)*K+i])
            m=mats[j] if isinstance(mats[j],str) else mats[j][i];M.append(m)
            UV.append([(arc[i],prof[j]),(arc[i+1],prof[j]),(arc[i+1],prof[j+1]),(arc[i],prof[j+1])])
    add(name,V,F,M,UV)
# ---------------- plan shapes
def se_r(th,a,b,n):return 1/((np.abs(np.cos(th))/a)**n+(np.abs(np.sin(th))/b)**n)**(1/n)
K=288;TH=np.linspace(-np.pi,np.pi,K,endpoint=False)
# extra samples at the four side-roof corners (wall point 0.96*r with |u|=84), so the wall top steps vertically there
from scipy.optimize import brentq
_tc=[]
for su,sv in((1,1),(1,-1),(-1,1),(-1,-1)):
    f=lambda t:0.96*se_r(t,OA,OB,ON)*abs(np.cos(t))-84.0
    t=brentq(f,0.05,np.pi/2-0.05);_tc+=[math.atan2(sv*math.sin(t),su*math.cos(t))]
TH=np.sort(np.r_[TH,[t+e for t in _tc for e in(-1e-4,1e-4)]]);K=len(TH)
def ring(o,z,a=OA,b=OB,n=ON):
    r=se_r(TH,a,b,n)+o;zz=z if np.ndim(z) else np.full(K,z)
    return np.stack([r*np.cos(TH),r*np.sin(TH),zz],1)
# roof end arcs (measured outer edge, smoothed by a spline in angle)
# The end roofs' outer edges: one circle each, fitted to the edge traced on Google Earth's top view (tools/grounds/
# marvel/fit: the view tied to the harbour edge, median 1.1 m; refit until the re-measured edge's median was under 0.3 m). Both
# centres sit about 5 m east of the stadium's axis, which is why the east halves read longer (2026-11-22).
ARC_FIT={'N':(-21.98,-5.19,101.15),'S':(21.15,-6.74,102.56)}
def _circ(k,sg,n=17):
    cu,cv,r=ARC_FIT[k];vs=np.linspace(74,-74,n) if sg<0 else np.linspace(-74,74,n)
    return [(round(float(cu+sg*math.sqrt(r*r-(v-cv)**2)),3),round(float(v),3)) for v in vs]
NP=_circ('N',-1);SP=_circ('S',1)
# The side roofs' edges, measured on the same view: the west roof's inner edge 2.25 m further in than the old 51.0
# and its outer edge 1.1 m in; the east roof's outer edge 1.6 m further out (its inner edge measured -0.25 m: kept).
VW_IN,VW_OUT,VE_IN,VE_OUT=48.8,101.7,-52.2,-105.2
def arc(pts,sgn,n=97):
    p=np.array(pts,float);c=np.array([sgn*40.0,0]);d=p-c;ph=np.arctan2(d[:,1],sgn*d[:,0]);r=np.hypot(*d.T);o=np.argsort(ph)
    sp=UnivariateSpline(ph[o],r[o],k=3,s=len(p)*0.8);q=np.linspace(ph[o][0],ph[o][-1],n);rr=sp(q)
    out=np.stack([c[0]+sgn*rr*np.cos(q),rr*np.sin(q)],1);out[0]=p[o][0];out[-1]=p[o][-1];return out
ARC_N=np.array(_circ('N',-1,97))[::-1];ARC_S=np.array(_circ('S',1,97))  # the fitted circles exactly (arc() smoothed hand-picked points)
# Side roofs' top, from Google Earth's mesh heights (status bar, 2026-11-22; field 8 m): 36-37 m above the
# field at the opening's edge, 38-39 m from v 60 out, i.e. nearly flat. It had sloped down to ZO (32.6 m above
# the field) at the edge, and the shut roof sat 5 m low with it (published: 38 m). ZI is the edge's height.
ZI=G('ZI',42.4)
def slab_z(av):  # side roof top height at |v|
    return np.where(av>=60,ZS,ZI+(np.clip(av,51,60)-51)/9*(ZS-ZI))
def end_prof(s):return ZG+(ZO-ZG)*(1-s**1.6)
UE=84.0
# ---------------- side roofs (slabs) with fascia, soffit, panel stack
def slab(name,vin,vout,u0,u1):
    sg=np.sign(vout)
    sec=[(vout,ZS),(sg*60,ZS),(vin,ZI),(vin,ZI-1.1),(sg*60,ZS-1.1),(vout,ZS-1.1)]  # (v,z)
    mats=['deck','deck','fascia','soffit','soffit','fascia']
    V=[(u0,v,z) for v,z in sec]+[(u1,v,z) for v,z in sec];n=len(sec);F=[];M=[]
    for i in range(n):F.append([i,(i+1)%n,n+(i+1)%n,n+i]);M.append(mats[i])
    F.append(list(range(n))[::-1]);M.append('fascia');F.append(list(range(n,2*n)));M.append('fascia')
    add(name,V,F,M)
    # retracted roof panels stacked along the opening edge (v ~50..60): three plates, each a step higher
    for k in range(3):
        a=vin+sg*0.0;b=vin+sg*(9.5-2.2*k);zz=lambda v:float(slab_z(np.array(abs(v))))+0.35*(k+1)
        q=[(u0+1,a,ZI+0.35*(k+1)),(u1-1,a,ZI+0.35*(k+1)),(u1-1,b,zz(b)),(u0+1,b,zz(b))]
        q2=[(x,y,z-0.3) for x,y,z in q];V=q+q2;F=[[0,1,2,3],[4,7,6,5],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]]
        add('roofopen_%s_%d'%(name[-1],k),V,F,['deck2','soffit','fascia','fascia','fascia','fascia'])
    # the same three plates run out over the opening when the roof is shut (the game shows one state or
    # the other, GroundModels.ROOFS): each covers a third of the half-span, the outer plate highest, so
    # the two halves meet at the centreline v=0
    for k in range(3):
        a=sg*(0.15+vin*sg*k/3-(0.4 if k else 0.0));b=sg*(abs(vin)*(k+1)/3+0.4);z=ZS+0.35*(k+1)  # over the slabs' top (38-39 m above the field)
        q=[(u0+1,a,z),(u1-1,a,z),(u1-1,b,z),(u0+1,b,z)]
        q2=[(x,y,zq-0.3) for x,y,zq in q];V=q+q2;F=[[0,1,2,3],[4,7,6,5],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]]
        add('roofshut_%s_%d'%(name[-1],k),V,F,['deck2','soffit','fascia','fascia','fascia','fascia'])
slab('slab_w',VW_IN,VW_OUT,-84.3,84.0);slab('slab_e',VE_IN,VE_OUT,-84.1,84.6)
# ---------------- end roofs: inner edge at the opening ends (u=-+84, z ZO), outer edge on the measured arc (z ZG)
def end_z(u,v):
    A=ARC_N if u<0 else ARC_S;o=np.argsort(A[:,1]);uo=np.interp(v,A[o,1],A[o,0]);s=np.clip((abs(u)-UE)/max(abs(uo)-UE,1),0,1)
    return float(end_prof(s))
def end_roof(name,ARC,sgn):
    J=10;rows=[]
    for j in range(J+1):
        s=j/J;inn=np.stack([np.full(len(ARC),sgn*UE),np.clip(ARC[:,1],-74,74)],1);p=inn+(ARC-inn)*s
        rows.append(np.c_[p,np.full(len(ARC),end_prof(s))])
    loft(name,rows,['endroof']*J,closed=False)
    # dark radial channels (2019 aerial: every ~5.3 deg about the arc centre u=+-40, from outside the arch to ~3.5 m short of the gutter)
    c=np.array([sgn*40.0,0]);d=ARC-c;ph=np.arctan2(d[:,1],sgn*d[:,0]);rr=np.hypot(*d.T);V=[];F=[];UV=[]
    for f in np.radians(np.arange(-55.65,56,5.3)):
        e=np.array([sgn*math.cos(f),math.sin(f)]);nn=np.array([-e[1],e[0]])
        r1=np.interp(f,ph,rr)-3.5;r0=max(48.0/abs(math.cos(f)),(UE+4-40)/abs(math.cos(f)))
        if r1<=r0+2:continue
        for k,t in enumerate(np.linspace(r0,r1,14)):
            q=c+e*t
            for w in(-0.7,0.7):x,y=q+nn*w;V.append((x,y,end_z(x,y)+0.08))
        o=len(V)-28
        for k in range(13):F.append([o+2*k,o+2*k+1,o+2*k+3,o+2*k+2]);UV.append([(0,0),(1,0),(1,2),(0,2)])
    add(name+'_channels',V,F,'endrib',UV)
    out=np.array([ARC[i]-ARC[i-1] if i else ARC[1]-ARC[0] for i in range(len(ARC))]);nrm=np.stack([sgn*out[:,1],-sgn*out[:,0]],1)
    nrm=-nrm if np.mean(np.sum(nrm*(ARC-[sgn*60,0]),1))<0 else nrm;nrm/=np.linalg.norm(nrm,axis=1)[:,None]
    g0=np.c_[ARC,np.full(len(ARC),ZG)];g1=np.c_[ARC+nrm*0.9,np.full(len(ARC),ZG+0.25)];g2=np.c_[ARC+nrm*0.9,np.full(len(ARC),ZG-0.9)];g3=np.c_[ARC,np.full(len(ARC),ZG-0.9)]
    loft(name+'_gutter',[g0,g1,g2,g3],['gutter','gutter','soffit'],closed=False)
    # end faces between the slab corners and the arc ends are covered by the slab end fascia + corner blocks
end_roof('end_n',ARC_N,-1);end_roof('end_s',ARC_S,1)
# ---------------- roof height function (top), for walls/brackets under it
def roof_top(u,v):
    if abs(u)<=UE and (v>=VW_IN or v<=VE_IN):return float(slab_z(np.array(abs(v))))
    return end_z(u,v)
# ---------------- space trusses (teal): two bottom chords, one arched top chord, Warren web, posts to the roof
def arcz(x,half,z0,z1):
    rise=z1-z0;R=(half**2+rise**2)/(2*rise);return z1-R+np.sqrt(np.maximum(R*R-x*x,0))
def side_truss(name,v1,v2,u0,u1,n=24):
    vm=(v1+v2)/2;uc=(u0+u1)/2;half=(u1-u0)/2
    zf=lambda v:float(slab_z(np.array(abs(v))))
    T=[];B1=[];B2=[]
    for i in range(n+1):
        u=u0+(u1-u0)*i/n;x=u-uc
        T.append((u,vm,float(arcz(x,half,zf(vm),ZT))));B1.append((u,v1,float(arcz(x,half,zf(v1)+0.3,ZB))));B2.append((u,v2,float(arcz(x,half,zf(v2)+0.3,ZB))))
    ch=[(X[i],X[i+1]) for X in (T,B1,B2) for i in range(n)]
    web=[]
    for i in range(n+1):web+=[(B1[i],B2[i])]+([(B1[i],T[i]),(B2[i],T[i])] if 0<i<n else [])
    for i in range(n):k,j=(i,i+1) if i<n/2 else (i+1,i);web+=[(B1[k],T[j]),(B2[k],T[j])]
    posts=[(B,(B[0],B[1],zf(B[1]))) for X in (B1,B2) for B in X[1:-1] if B[2]-zf(B[1])>0.6]
    beams(name+'_ch',ch,0.8,'teal');beams(name+'_web',web+posts,0.32,'teal')
for sg,(o1,o2,i1,i2),(u0,u1) in((1,(88.75,97.5,57.5,66.0),(-84.3,84.0)),(-1,(-88.75,-97.5,-57.5,-66.0),(-84.1,84.6))):
    side_truss('truss_%s_out'%('w' if sg>0 else 'e'),o1,o2,u0,u1);side_truss('truss_%s_in'%('w' if sg>0 else 'e'),i1,i2,u0,u1)
def end_arch(name,sgn,n=20):
    v0,v1=VE_IN+0.8,VW_IN-0.8;half=(v1-v0)/2;vc=(v0+v1)/2;T=[];B1=[];B2=[]
    for i in range(n+1):
        v=v0+(v1-v0)*i/n;x=v-vc;f=1-(x/half)**2
        T.append((sgn*(UE+6.0*f),v,float(arcz(x,half,ZO,ZT))));B1.append((sgn*UE,v,float(arcz(x,half,ZO+0.3,ZB+1))));B2.append((sgn*(UE+3.5*f+0.5),v,float(arcz(x,half,ZO+0.3,ZB+1))))
    ch=[(X[i],X[i+1]) for X in (T,B1,B2) for i in range(n)];web=[]
    for i in range(n+1):web+=[(B1[i],B2[i])]+([(B1[i],T[i]),(B2[i],T[i])] if 0<i<n else [])
    for i in range(n):k,j=(i,i+1) if i<n/2 else (i+1,i);web+=[(B1[k],T[j]),(B2[k],T[j])]
    beams(name+'_ch',ch,0.8,'teal');beams(name+'_web',web,0.32,'teal')
end_arch('arch_n',-1);end_arch('arch_s',1)
# ---------------- bowl: outer wall lofted round a superellipse (face measured at the west centre: v 108.5)
r0=se_r(TH,OA,OB,ON);PU=r0*np.cos(TH);PV=r0*np.sin(TH)
RU=np.array([roof_top(u*1.0,v*1.0)-1.2 for u,v in zip(PU*0.96,PV*0.96)])  # roof underside just inside the face
# slab end faces: close the gap between the end roof (inner edge z ZO) and the slab underside, v 51..74
for nm,(u_,vin,vout) in(('w0',(-84.3,VW_IN,74.0)),('w1',(84.0,VW_IN,74.0)),('e0',(-84.1,VE_IN,-74.0)),('e1',(84.6,VE_IN,-74.0))):
    vs=np.linspace(vin,vout,12);top=[float(slab_z(np.array(abs(v))))-1.1 for v in vs]
    q=[(u_,v,ZO-0.2) for v in vs]+[(u_,v,t) for v,t in zip(vs[::-1],top[::-1])]
    add('slab_end_'+nm,q,[list(range(len(q)))],'soffit')  # under the roof, so the underside's paint, not the bright fascia
south=PU>92
def segm(a,b):return [b if s else a for s in south]
def cl(z):return np.minimum(z,RU-0.4) if np.ndim(z) else np.minimum(np.full(K,z),RU-0.4)
# (offset from the face, height) read off the aerial pixel table at u 10 (mv/p2uv.py, mv/vert.py)
prof=[(-4,ZP),(-4,13.2),(0,13.2),(0,14.3),(-0.6,14.3),(-0.6,21.4),(0,21.4),(0,24.9),(-0.4,24.9),(-0.4,26.3),(0,26.3),(0,27.7),
      (-3,27.7),(-3,33.9),(0,33.9),(0,36.5),(-5,36.5),(-5,None)]
mats=['glass','soffit','silver','soffit',segm('curtain','curtain'),'soffit','silver','soffit','glass','soffit','silver','soffit',
      'glass','soffit','silver','silver','upperwall']  # the band over the braces up to the roof: dark blue (Google Earth c_ne)
rings=[ring(o,RU if z is None else cl(z)) for o,z in prof]
loft('bowl_wall',rings,mats)
# white round columns in front of the shopfront, one every 8 m of perimeter (none behind the west podium)
per=np.r_[0,np.cumsum(np.hypot(np.diff(np.r_[PU,PU[:1]]),np.diff(np.r_[PV,PV[:1]])))];k=0
for L in np.arange(2,per[-1],8.0):
    i=np.searchsorted(per,L)-1;t=(L-per[i])/(per[i+1]-per[i]);th=TH[i]+(t*(2*np.pi/K));r=se_r(th,OA,OB,ON)-1.0
    cu,cv=r*np.cos(th),r*np.sin(th)
    if -40<cu<46 and cv>0:continue
    cyl('col%03d'%k,(cu,cv),0.4,ZP,13.2,'white','white',12);k+=1
# braces in the upper recess (27.7..33.9): a pale grey-green post from the band up to the roof's fascia every 19 m, each
# with one raking strut in the face's plane from the post's top down to the band 6 m along, alternate ones mirrored
# (Wikimedia Commons Marvel_Stadium_2019, west side: braces about two fascia panels apart, about 19 m taking the recess
# as 6.2 m tall; the first build had a V every 8 m, which read as a continuous white zigzag against Google Earth's dark band)
segs=[];posts=[];BR=19.0
for k,L in enumerate(np.arange(4.0,per[-1]-4.0,BR)):
    i=np.searchsorted(per,L)-1;th=TH[max(i,0)];sg=1 if k%2==0 else -1;th2=th+sg*6.0/per[-1]*2*np.pi
    def P3(t_,o,z):r=se_r(t_,OA,OB,ON)+o;return (r*np.cos(t_),r*np.sin(t_),z)
    zt=min(33.9,float(roof_top(*P3(th,-5,0)[:2]))-1.6)
    if zt<29:continue
    posts+=[(P3(th,-1.0,27.8),P3(th,-1.0,zt))];segs+=[(P3(th,-1.0,zt-0.4),P3(th2,-1.0,27.8))]
beams('recess_posts',posts,0.45,'teal');beams('recess_braces',segs,0.35,'teal')
# ---------------- concourse plinth: ring 3 m outside the face, 0..6.5 m; west deck out to the measured balustrade
def se_poly(o,n=K):return np.stack([(se_r(TH,OA,OB,ON)+o)*np.cos(TH),(se_r(TH,OA,OB,ON)+o)*np.sin(TH)],1)
def z3(P,z):return np.c_[P,np.full(len(P),z)]
_po,_pi=se_poly(3.0),se_poly(-6.0)
loft('plinth',[z3(_po,0.0),z3(_po,ZP),z3(_pi,ZP),z3(_pi,0.0)],['base','paving','base'])
BAL=np.array([(-56.2,108.0),(-56.2,110.4),(-46.8,120.5),(-35.8,126.6),(-12,128.6),(9.9,128.9),(30,128.6),(42.4,127.9),(51.8,121.0),(55.5,115.3),(55.5,112.0)])
from scipy.interpolate import splprep,splev
tck,_=splprep(BAL.T,s=6.0);bal=np.array(splev(np.linspace(0,1,80),tck)).T
prism('plinth_deck',np.r_[bal,[(55.5,95.0),(-56.2,95.0)]],0.0,ZP,'base','paving')
gl=[np.c_[bal,np.full(len(bal),ZP)],np.c_[bal,np.full(len(bal),ZP+1.1)]];loft('plinth_balustrade',gl,['glass'],closed=False)
loft('plinth_balustrade_top',[np.c_[bal,np.full(len(bal),ZP+1.1)],np.c_[bal,np.full(len(bal),ZP+1.22)]],['white'],closed=False)
# ---------------- west podium: glazed ground storey (front v 119), terrace 13.2, upper block (front v 113.5) to 21.4
def band_poly(u0,u1,vout,o=-3.0):
    us=np.linspace(u0,u1,25);vb=[]
    for u in us:
        vv=np.linspace(0,130,2600);thv=np.arctan2(vv,u);j=np.where(np.hypot(u,vv)<=se_r(thv,OA,OB,ON)+o)[0][-1];vb.append(vv[j])
    return [(u,vout) for u in us]+[(u,v) for u,v in zip(us[::-1],vb[::-1])]
def prism_f(name,q,z0,z1,fn,top):
    q=np.asarray(q,float);a=0.5*np.sum(q[:,0]*np.roll(q[:,1],-1)-np.roll(q[:,0],-1)*q[:,1])
    if a<0:q=q[::-1]
    sm=[fn((q[i]+q[(i+1)%len(q)])/2) for i in range(len(q))];prism(name,q,z0,z1,'x',top,side_m=sm)
def podium_storey(nm,u0,u1,vout,z0,z1,nb,zo,rec=1.2,top='paving'):
    # photo: grey-blue panel piers (Google Earth c_w: darker than the white they were) on the front line, deep recessed glazed bays between, a solid spandrel band above the bays
    prism_f(nm,band_poly(u0,u1,vout-rec),z0,z1,lambda m:'shopglass' if m[1]>vout-rec-0.05 else 'podiumpanel',top)
    pitch=(u1-u0)/nb;pw=pitch-zo
    for i in range(nb+1):
        uc=u0+i*pitch;a,b=max(u0,uc-pw/2),min(u1,uc+pw/2)
        box(nm+'_pier%d'%i,a,b,vout-rec,vout,z0,z1,'podiumpanel','concrete')
    box(nm+'_spandrel',u0,u1,vout-rec,vout,z1-1.8 if z1-z0>7.5 else z1-1.6,z1,'podiumpanel','concrete')
podium_storey('podium_l1',-40.0,46.0,119.0,ZP,13.2,10,6.4)
box('podium_rail',-40,46,118.85,119.0,13.2,14.3,'glass','white');box('podium_rail_top',-40,46,118.8,119.05,14.3,14.42,'white','white')
podium_storey('podium_l2',-43.0,31.0,113.5,13.2,21.4,9,5.6,top='concrete')
for i,(u,w) in enumerate(((-41.5,5),(-26.0,4.4),(-21.6,4.4),(9.6,4.4),(14.0,4.4),(28.5,5))):
    box('canopy%d'%i,u-w/2,u+w/2,114.0,118.4,15.7,16.0,'canvas','canvas','canvas')
    for du,dv in((-1,0.2),(1,0.2),(-1,4.2),(1,4.2)):cyl('canopy%d_post%d%d'%(i,du>0,dv>1),(u+du*(w/2-0.2),114+dv),0.07,13.2,15.7,'white','white',6)
for cu,cv,h in((-45.8,110.4,17.8),(43.3,111.8,16.7)):
    for du,dv in((-1.3,-1.3),(1.3,-1.3),(-1.3,1.3),(1.3,1.3)):cyl('tank_%d_%d%d'%(cu,du>0,dv>0),(cu+du,cv+dv),1.2,ZP,h,'tank','tank')
# ---------------- seating bowl inside (no field): three tiers between the pitch fence and the outer wall
PA,PB,PN=G('PA',86.0),G('PB',72.0),G('PN',2.2)
rp=se_r(TH,PA,PB,PN)+2.0;D=r0-6.0-rp
SEATS=[];SEATUV=[]
def _arc(R):
    Rc=np.r_[R,R[:1]];d=np.linalg.norm(np.diff(Rc[:,:2],axis=0),axis=1);return Rc,d,np.r_[0,np.cumsum(d)]
def aisle_angles(R,pitch=0.5,block=24,aisle=1.2):
    # radial aisle stairs: one every 24 seats along the tier's front row; every row above keeps the same angles
    Rc,d,cs=_arc(R);out=[];s=0.6+block*pitch
    while s<cs[-1]-0.6:
        j=max(0,min(int(np.searchsorted(cs,s))-1,len(R)-1));p=Rc[j]+(Rc[j+1]-Rc[j])*(s-cs[j])/max(d[j],1e-9)
        out.append(math.atan2(p[1],p[0]));s+=block*pitch+aisle
    return np.array(out)
def seat_row(R,AA,pitch=0.5,aisle=1.2):
    Rc,d,cs=_arc(R);s=0.3
    while s<cs[-1]-0.3:
        j=max(0,min(int(np.searchsorted(cs,s))-1,len(R)-1));p=Rc[j]+(Rc[j+1]-Rc[j])*(s-cs[j])/max(d[j],1e-9)
        r=math.hypot(p[0],p[1]);da=np.abs((AA-math.atan2(p[1],p[0])+np.pi)%(2*np.pi)-np.pi)*r
        if len(AA) and da.min()<aisle/2+0.22:s+=0.1;continue
        w0=np.array(wv(p));w1=np.array(wv(p*np.array([0.99,0.99,1.0])))  # inward = towards the pitch centre
        dv=w1[:2]-w0[:2];dv/=np.linalg.norm(dv)+1e-12;SEATS.append([round(float(w0[0]),3),round(float(w0[1]),3),round(float(w0[2]),3),round(float(dv[0]),4),round(float(dv[1]),4)])
        SEATUV.append((float(p[0]),float(p[1]),float(p[2])));s+=pitch
def tier(name,f0,f1,zf,zb,lip=1.1,front='concrete'):
    a=rp+D*f0;b=rp+D*f1;c=np.cos(TH);s=np.sin(TH)
    P=lambda r,z:np.stack([r*c,r*s,np.full(K,z) if np.ndim(z)==0 else z],1)
    # stepped concrete rows (0.8 m treads) with a real seat on each row (pan + back, 0.44 m wide, 0.5 m pitch, 1.2 m aisle every 24)
    n=max(1,int(round(np.mean(b-a)/0.8)));zz=lambda i:zf+(np.asarray(zb)-zf)*i/n;rr=lambda i:a+(b-a)*i/n
    # the treads a mid grey: as white concrete the aisle stairs read as bright ladders between the seats
    rings=[P(a,zf-lip-0.6),P(a,zf)];mats=[front];AA=aisle_angles(P(a+(b-a)*0.55/n,zf))
    for i in range(n):
        rings+=[P(rr(i+1),zz(i)),P(rr(i+1),zz(i+1))];mats+=['tread','riser']
        rs=rr(i)+(rr(i+1)-rr(i))*0.55;seat_row(P(rs,zz(i)),AA)
    rings+=[P(b,np.asarray(zb)-1.0),P(a,zf-lip-0.6)];mats+=['concrete','soffit']
    loft(name,rings,mats)
# the middle and top tiers' fronts carry the ribbon screens that run right round the bowl.
# Heights and depths measured 2026-11-23 (row 202) from three sources that agree, not guessed:
# - two match photos with their cameras solved from the centre square (Wikimedia Commons curtain raiser and Hawthorn v
#   Brisbane 2024; the boundary fence lands within about 5 px in both): the middle tier's ribbon, 198 points round
#   the bowl, fits a centre 6 m above the field (median miss 5 px); the top tier's front 15 m (6 points, 4 px);
#   the top tier's back row about 26-27 m, and the curtain-raiser photographer's eye 22.5 m up about 20 m past the
#   fence, a few rows into the top tier (so the top tier rakes about 35 degrees, not steeper);
# - Google Earth's 3D mesh over each end (bowl picks, tools/grounds/marvel/fit): 6-7.5 m at 3-6 m past the fence
#   (the middle tier's overhanging front), 13-16 m at 10-11 m (the top tier's front), 20-24 m at 15-20 m.
# The middle tier hangs out over the lower tier close to the field and the top tier over a level of glazed boxes,
# which is why Marvel's stands read so steep and close. (The first build had them 7 and 10 m higher.)
tier('tier1',0.0,0.55,FL+1.4,FL+8.1)
tier('tier2',0.13,0.36,FL+8.4,FL+11.9,front='ribbon');_b3=rp+D*1.0;_rt=np.array([roof_top(r*math.cos(t),r*math.sin(t)) for r,t in zip(_b3,TH)])
tier('tier3',0.42,1.0,FL+16.9,np.minimum(FL+27.4,_rt-1.5),front='ribbon')
# the boxes' glass front between the middle tier's back row and the top tier's underside, and the boxes' floor
_bx=rp+D*0.40;_bP=lambda r,z:np.stack([r*np.cos(TH),r*np.sin(TH),np.full(K,z)],1)
loft('boxes',[_bP(rp+D*0.36,FL+11.9),_bP(_bx,FL+11.9),_bP(_bx,FL+15.2)],['concrete','glass'])
# ---------------- under the roof (photos of the bowl, Wikimedia Commons: Docklands_Stadium_Dec2022, Marvel_Stadium_
# during_curtain_raiser, Marvel_Stadium_before_Hawthorn_Hawks_vs_Brisbane_Lions_-_26_May_2024; looked at, not copied).
# The roof's underside is a grid of pale steel: cross girders every 10.5 m, purlins along, and a diagonal in every
# bay, so it reads as triangles from the seats. A lighting gantry runs round the opening's edge with two rows of
# floodlights under it; screens hang from it at the ends and the four corners. All modelled, nothing painted.
from scipy.spatial import cKDTree
_ST=cKDTree(np.array(SEATUV)[:,:2]);_SZ=np.array(SEATUV)[:,2]
def clear(a,b,gap=2.6):
    """True when every point of the member a-b is gap m above the seats within 2.5 m of it (heads and sightlines)."""
    for t in np.linspace(0,1,max(2,int(np.linalg.norm(np.subtract(b,a))/1.5)+1)):
        q=np.add(a,np.subtract(b,a)*t);ii=_ST.query_ball_point(q[:2],2.5)
        if ii and q[2]-0.4<_SZ[ii].max()+gap:return False
    return True
def grid(name,uu,vv,zf,w=0.38,drop=0.45,diag=True):
    """Members on a (u,v) lattice hanging drop m under the surface z=zf(u,v): cross girders along v, purlins along u,
    one diagonal per bay (alternating), each kept only where it clears the seats."""
    P=lambda u,v:(u,v,zf(u,v)-drop);segs=[]
    for u in uu:segs+=[(P(u,vv[j]),P(u,vv[j+1])) for j in range(len(vv)-1)]
    for v in vv:segs+=[(P(uu[i],v),P(uu[i+1],v)) for i in range(len(uu)-1)]
    if diag:
        for i in range(len(uu)-1):
            for j in range(len(vv)-1):
                a,b=((uu[i],vv[j]),(uu[i+1],vv[j+1])) if (i+j)%2 else ((uu[i],vv[j+1]),(uu[i+1],vv[j]))
                segs.append((P(*a),P(*b)))
    segs=[sg for sg in segs if clear(*sg)]
    if segs:beams(name,segs,w,'white')
def under_slab(sg,vin,u0,u1):
    zf=lambda u,v:float(slab_z(np.array(abs(v))))-1.1
    vv=[sg*abs(v) for v in (abs(vin)+0.6,58.5,66.0,74.0,82.0,90.0,98.0)]
    grid('slab_under_%s'%('w' if sg>0 else 'e'),np.linspace(u0+0.6,u1-0.6,17),vv,zf)
under_slab(1,VW_IN,-84.3,84.0);under_slab(-1,VE_IN,-84.1,84.6)
# the shut roof's three plates each side: the same grid under each (group roofshut, so it goes when the roof opens)
for sg,vin in((1,VW_IN),(-1,-VE_IN)):
    for k in range(3):
        a=0.15+vin*k/3+(0.6 if k else 0.4);b=vin*(k+1)/3-0.2;zb=ZS+0.35*(k+1)-0.3
        grid('roofshut_under_%s%d'%('w' if sg>0 else 'e',k),np.linspace(-83.0,83.0,17),[sg*a,sg*(a+b)/2,sg*b],lambda u,v,zb=zb:zb,w=0.34,drop=0.32)
# end roofs: radial ribs under the channels, three rings across them
def under_end(nm,ARC,sgn):
    c=np.array([sgn*40.0,0]);d=ARC-c;ph=np.arctan2(d[:,1],sgn*d[:,0]);rr=np.hypot(*d.T);segs=[];rings={}
    for f in np.radians(np.arange(-55.65,56,5.3)):
        e=np.array([sgn*math.cos(f),math.sin(f)]);r1=np.interp(f,ph,rr)-3.0;r0=(UE+0.8-40)/abs(math.cos(f))
        if r1<=r0+2:continue
        pts=[]
        for t in np.linspace(r0,r1,9):x,y=c+e*t;pts.append((x,y,end_z(x,y)-0.55))
        segs+=[(pts[i],pts[i+1]) for i in range(len(pts)-1)]
        for k in(2,4,6):rings.setdefault(k,[]).append(pts[k])
    for k,R in rings.items():segs+=[(R[i],R[i+1]) for i in range(len(R)-1)]
    segs=[s_ for s_ in segs if clear(*s_)]
    beams(nm,segs,0.38,'white')
under_end('end_n_under',ARC_N,-1);under_end('end_s_under',ARC_S,1)
# lighting gantry: a box truss 2.4 m deep under the opening's edge, floodlights every 2 m in two rows under it
LAMPS=[]
def gantry(nm,a,b,ztop,inward):
    a=np.asarray(a,float);b=np.asarray(b,float);L=np.linalg.norm(b-a);t=(b-a)/L;n=np.asarray(inward,float);n/=np.linalg.norm(n)
    m=max(2,int(L/2.4));top=[];bot=[]
    for i in range(m+1):
        p=a+t*L*i/m;top.append([(p[0]+n[0]*w,p[1]+n[1]*w,ztop) for w in(-1.0,1.0)]);bot.append([(p[0]+n[0]*w,p[1]+n[1]*w,ztop-2.4) for w in(-1.0,1.0)])
    segs=[]
    for X in(top,bot):
        for s_ in(0,1):segs+=[(X[i][s_],X[i+1][s_]) for i in range(m)]
    web=[]
    for i in range(m+1):
        web+=[(top[i][0],bot[i][0]),(top[i][1],bot[i][1]),(bot[i][0],bot[i][1])]
        if i<m:web+=[(top[i][0],bot[i+1][0]),(top[i][1],bot[i+1][1])]
    beams(nm+'_ch',segs,0.3,'silver');beams(nm+'_web',web,0.14,'silver')
    k=int(L/2.0)
    for i in range(k):
        p=a+t*(1.0+i*2.0)
        for w in(-0.55,0.55):LAMPS.append((p[0]+n[0]*w,p[1]+n[1]*w,ztop-2.4,n))
gantry('gantry_w',(-83.6,VW_IN+0.6),(83.3,VW_IN+0.6),ZI-1.2,(0,-1));gantry('gantry_e',(-83.4,VE_IN-0.6),(83.9,VE_IN-0.6),ZI-1.2,(0,1))
# end edge girders (Google Earth 3D picks, 2026-11-22): the end roofs' inner edge sits at |u| 80.8, 3.2 m inside the
# slab ends, as a deep girder whose top reads 39.4 in this frame from |u| 80.8 to about 86; the roof falls away behind it
UO=G('UO',80.8);ZEG=G('ZEG',39.4)
for sg_,nm_ in((-1,'edge_n'),(1,'edge_s')):
    a_,b_=sorted((sg_*UO,sg_*86.0));box(nm_,a_,b_,VE_IN,VW_IN,ZO-1.3,ZEG,'fascia','deck',bottom='soffit')
gantry('gantry_n',(-UO-0.6,VE_IN+2.2),(-UO-0.6,VW_IN-1.4),ZO-1.3,(1,0));gantry('gantry_s',(UO+0.6,VE_IN+1.6),(UO+0.6,VW_IN-0.6),ZO-1.3,(-1,0))
# each floodlight: a housing tipped 30 deg towards the pitch, lens on its lower face
V=[];F=[];M=[]
for x,y,z,n in LAMPS:
    tip=np.array([n[0]*0.5,n[1]*0.5,-0.866]);ax=np.array([-n[1],n[0],0.0]);up=np.cross(ax,tip);c=np.array([x,y,z-0.35])
    o=len(V)
    for sz in(-0.28,0.28):
        for sa,su in((-0.28,-0.28),(0.28,-0.28),(0.28,0.28),(-0.28,0.28)):V.append(tuple(c+tip*sz+ax*sa+up*su))
    F+=[[0+o,1+o,2+o,3+o],[4+o,7+o,6+o,5+o],[o,4+o,5+o,1+o],[1+o,5+o,6+o,2+o],[2+o,6+o,7+o,3+o],[3+o,7+o,4+o,o]]
    M+=['signblack','lamp','signblack','signblack','signblack','signblack']
add('gantry_lamps',V,F,M)
# screens: the two big ones hang from the end gantries, one off each side of the axis (diagonally opposite); four
# smaller ones hang at the opening's corners, angled to the centre. Face material 'screen' (Oval3DScreens draws on it).
def screen(nm,c,facing,w,h,ztop,d=1.0,hang=2.6,label=0.0):
    c=np.asarray(c,float);f=np.asarray(facing,float);f/=np.linalg.norm(f);s_=np.array([-f[1],f[0]])
    q=[c-s_*w/2-f*d,c+s_*w/2-f*d,c+s_*w/2,c-s_*w/2]
    prism(nm+'_box',[tuple(x) for x in q],ztop-h-0.5,ztop,'signblack','signblack',bottom='signblack')
    fr=[c-s_*(w/2-0.35)+f*0.02,c+s_*(w/2-0.35)+f*0.02]
    add(nm,[(fr[0][0],fr[0][1],ztop-h-0.15),(fr[1][0],fr[1][1],ztop-h-0.15),(fr[1][0],fr[1][1],ztop-0.65),(fr[0][0],fr[0][1],ztop-0.65)],[[0,1,2,3]],'screen',[[(0,0),(1,0),(1,1),(0,1)]])
    if hang>0:
        for k in(-1,1):beams(nm+'_hang%d'%(k>0),[((*(c+s_*k*w/3-f*0.5),ztop+label),(*(c+s_*k*w/3-f*0.5),ztop+label+hang))],0.12,'silver')
    if label>0:  # the MARVEL STADIUM name board on top (white lettering on black, tex sign_mvst)
        prism(nm+'_labelbox',[tuple(x) for x in q],ztop,ztop+label,'signblack','signblack')
        lw=min(w*0.8,label*8.5);fl=[c-s_*lw/2+f*0.02,c+s_*lw/2+f*0.02]
        add(nm+'_label',[(fl[0][0],fl[0][1],ztop+0.1),(fl[1][0],fl[1][1],ztop+0.1),(fl[1][0],fl[1][1],ztop+label-0.1),(fl[0][0],fl[0][1],ztop+label-0.1)],[[0,1,2,3]],'sign_mvst',[[(0,0),(1,0),(1,1),(0,1)]])
zg=ZO-1.3-2.4-0.6
# the two big screens hang centred on the long axis in front of the end girders, 27 x 8.5 m, face centre 29 m above
# the field: Google Earth's angled views show both boxes centred in the opening, and the camera solved from the centre
# square in the 2024 Hawthorn v Brisbane photo puts the far one at v 0, 27 m wide, centre 29 m up (2026-11-23)
screen('screen_n',(-UO+1.4,0.0),(1,0),27.0,8.5,39.05,hang=0.4);screen('screen_s',(UO-1.4,0.0),(-1,0),27.0,8.5,39.05,hang=0.4)
# the small scoreboards hang over the top tier's front rows at the corners, 13.5 x 7 m, face centre 25.2 m above the
# field, each with a MARVEL STADIUM name board on top. The curtain-raiser photo's solved camera fixes the ray to each
# north board; where along it is set by the photo showing the board in front of the top tier's seats, so it sits where
# the ray first clears those seats by 2.5 m (u -77.3, v +-64.5; re-measured 2026-11-23 after the tiers were lowered).
# Hangers to the roof's underside. The south pair is by the stadium's symmetry (no photo of those corners yet).
for i,(cu,cv) in enumerate(((-77.3,64.5),(77.3,64.5),(-77.3,-64.5),(77.3,-64.5))):
    fc=np.array([-cu,-cv]);zt=5.4+25.2+3.5+1.6
    screen('screen_c%d'%i,(cu,cv),fc,13.5,7.0,5.4+25.2+3.5,hang=max(0.0,roof_top(cu,cv)-1.2-zt),label=1.6)
from shapely.geometry import Polygon,Point
def vent_block(nm,f,z0,z1,zb0,zb1,bay=7.0,pier=1.6,depth=0.45,wall='bluepanel',top='concrete'):
    # the blue service blocks (Google Earth c_ne): solid blue cladding with big louvred vent openings cut
    # into it, the louvres set back behind the cladding's face, not painted on it
    P=Polygon(f);f=list(P.exterior.coords)[:-1];core=list(P.buffer(-depth,join_style=2).exterior.coords)[:-1]
    prism(nm+'_vents',core,zb0,zb1,'grille',top)
    prism(nm,f,z0,zb0,wall,wall)
    prism(nm+'_head',f,zb1,z1,wall,top,bottom=wall)
    n=len(f)
    for i in range(n):
        a=np.array(f[i]);b=np.array(f[(i+1)%n]);L=np.linalg.norm(b-a)
        if L<pier*2:continue
        d=(b-a)/L;out=np.array([d[1],-d[0]])
        if P.contains(Point(*(0.5*(a+b)+out*0.3))):out=-out
        k=max(1,int((L-pier)/(bay+pier)));w=(L-pier*(k+1))/k
        for j in range(k+1):
            t0=j*(w+pier);c0=a+d*t0;c1=a+d*(t0+pier)
            q4=[tuple(c0),tuple(c1),tuple(c1-out*depth),tuple(c0-out*depth)]
            prism(nm+'_pier%d_%d'%(i,j),q4,zb0,zb1,wall,wall)
def office_box(nm,q,z0=9.0,z1=24.0,storey=3.75):
    # modelled, not painted: an open ground floor (slim round columns every 7.5 m on the outer line, the
    # glazed lobby wall set 2.5 m back under the box's soffit); above, the glazing set 0.35 m back behind a
    # proud pale spandrel band at the foot of every storey and a parapet, with slim pale fins every 0.75 m
    f=lean(q,z1);P=Polygon(f)
    core=list(P.buffer(-0.35,join_style=2).exterior.coords)[:-1];lobby=list(P.buffer(-2.5,join_style=2).exterior.coords)[:-1]
    prism(nm+'_lobby',lobby,0.0,z0,'shopglass','concrete')
    # its glass a light grey: the east boxes read pale grey/white in Google Earth, and blue 'glass' rendered them 33 darker (PC check round 3)
    prism(nm,core,z0,z1-0.8,'officeglass','concrete',bottom='concrete')
    prism(nm+'_soffit',f,z0-0.45,z0,'panel_lt','panel_lt',bottom='concrete')
    z=z0
    while z<z1-1.0:
        prism(nm+'_band%d'%int(z*10),f,z,z+1.2,'panel_lt','panel_lt',bottom='panel_lt');z+=storey
    prism(nm+'_parapet',f,z1-0.8,z1,'panel_lt','concrete',bottom='panel_lt')
    # the edges that face out (the one along the stadium wall, v -107, has no fins or columns)
    V=[];F=[];UV=[];n=len(q)
    for i in range(n):
        if abs(q[i][1]+107.0)<0.01 and abs(q[(i+1)%n][1]+107.0)<0.01:continue
        a=np.array(f[i]);b=np.array(f[(i+1)%n]);L=np.linalg.norm(b-a);d=(b-a)/L;out=np.array([d[1],-d[0]])
        if P.contains(Point(*(0.5*(a+b)+out*0.5))):out=-out
        for t in np.arange(0.6,L-0.3,0.75):
            c=a+d*t-out*0.18
            for zz0,zz1 in [(z0+1.2+k*storey,min(z0+(k+1)*storey,z1-0.8)) for k in range(int((z1-z0)/storey)+1)]:
                if zz1-zz0<0.2:continue
                cc,ff,uu=beamV(np.r_[c,zz0],np.r_[c,zz1],0.0);o=len(V)
                pts=[np.r_[c+d*sx*0.05+out*sy*0.17,zz] for zz in (zz0,zz1) for sx,sy in((-1,-1),(1,-1),(1,1),(-1,1))]
                V+=[tuple(p_) for p_ in pts];F+=[[o+i_ for i_ in fa] for fa in ([0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7])]
                UV+=[[(0,zz0),(0.1,zz0),(0.1,zz1),(0,zz1)]]*4
        for t in np.arange(3.0,L-1.0,7.5):
            c=a+d*t-out*0.6;cyl(nm+'_col%d_%d'%(i,int(t)),tuple(c),0.32,0.0,z0-0.45,'white','white',12)
    if V:add(nm+'_fins',V,F,'silver',UV)
# ---------------- corner complexes (west measured: satellite lean + aerial, mv/sz.py, mv/vert.py); east = 180-degree twin
def face_v(u,o=0.0):
    vv=np.linspace(0,130,2600);thv=np.arctan2(vv,u);j=np.where(np.hypot(u,vv)<=se_r(thv,OA,OB,ON)+o)[0];return vv[j[-1]] if len(j) else 0.0
def rbox(name,c,L,W,ang,z0,z1,side,top,side_m=None):
    d=np.array([math.cos(ang),math.sin(ang)]);n=np.array([-d[1],d[0]]);c=np.array(c)
    q=[c-d*L/2-n*W/2,c+d*L/2-n*W/2,c+d*L/2+n*W/2,c-d*L/2+n*W/2];prism(name,q,z0,z1,side,top,side_m=side_m)
def fill(name,u0,u1,line,z0,z1,side,top,o=-1.0):
    us=np.linspace(u0,u1,16);q=[(u,line(u)) for u in us]+[(u,face_v(u,o)) for u in us[::-1]];prism(name,q,z0,z1,side,top)
CORN=[]
# corner tower tops read off mu.png at their roof height (mv/p2uv.py); fill lines from the louvred block edges (z 0-22)
TWN=[(-118.8,66.0),(-113.5,59.4),(-101.1,66.1),(-101.8,77.3)];TWS=[(97.9,72.0),(112.0,69.5),(110.9,83.0),(92.5,87.9)]
FLN=[(-101.0,72.0),(-95.3,74.5),(-83.5,88.9),(-77.7,92.7),(-56.0,103.0)];FLS=[(56.0,104.0),(75.0,97.5),(84.1,81.0),(92.2,81.4),(95.0,74.0)]
def fill_line(name,L,z0,z1,off,side,top):
    L=np.array(L,float);us=np.linspace(L[0,0],L[-1,0],24);vo=np.interp(us,L[:,0],L[:,1]) if L[0,0]<L[-1,0] else np.interp(us,L[::-1,0],L[::-1,1])
    q=[(u,max(v+off,face_v(u,-1.0)+0.5)) for u,v in zip(us,vo)]+[(u,face_v(u,-2.0)) for u in us[::-1]]
    return q
for sg in(1,-1):
    tw='w' if sg>0 else 'e';m=lambda u,v:(sg*u,sg*v)
    prism('cornerN_tower_'+tw,[m(*c) for c in TWN],0.0,33.0,'bluepanel','concrete')
    if sg>0:prism('cornerS_tower_'+tw,[m(*c) for c in TWS],0.0,33.0,'bluepanel','concrete')
    for uc,vc in((-54.2,107.2),(54.3,108.4)):
        cu,cv=m(uc,vc);box('beige_%s_%d'%(tw,int(uc)),cu-6,cu+6,cv-5,cv+5,0.0,27.4,'slate','glass' if (sg<0 and cu<0) else 'canvas')
    for u0_,u1_ in((-80,-58),(57,80)):
        us=np.linspace(u0_,u1_,12);q=[m(u,face_v(u,3.5)) for u in us]+[m(u,face_v(u,-2)) for u in us[::-1]]
        prism('pod_%s_%d'%(tw,u0_),q,24.0,31.0,'curtain','silver')
    for k,L in enumerate((FLN,FLS)):
        if sg<0 and k==1:L=[c for c in L if c[0]<88.0]  # NE: the satellite shows open paving north of u -88
        q=fill_line('',L,0,0,0.0,'','');vent_block('fill1_%s_%d'%(tw,k),[m(*c) for c in q],0.0,22.0,9.0,16.0)
        q=fill_line('',L,0,0,2.5,'','');prism('fill0_%s_%d'%(tw,k),[m(*c) for c in q],0.0,10.0,'slate','concrete')
# ---------------- east side, read off the straight-down satellite (roof outline seen at height z, footprint = roof + lean*z,
# lean du +0.1738, dv +0.0805 per metre); heights from the shadow lengths (0.5 m of shadow per metre, calibrated on the roof edge)
def lean(q,z):return [(u+0.1738*z,v+0.0805*z) for u,v in q]
# NE corner: one long block (roof 9.3 m wide, 38.7 m long) from the roof corner to the plaza, z 33, plant room on top to 37
NEB=[(-120.3,-59.1),(-125.6,-66.7),(-93.9,-88.9),(-88.6,-81.3)]
prism('cornerNE_block',lean(NEB,33.0),0.0,33.0,'bluepanel','concrete')
_c=np.mean(lean([(-106.4,-78.3)],37.0),0);rbox('cornerNE_plant',tuple(_c),9.0,7.5,math.atan2(-0.574,0.819),33.0,37.0,'silver','concrete')
# B: office block north of the deck (Google Earth c_e, c_ne: pale boxes, a spandrel band and a ribbon of
# glass behind fins every storey, over an open ground floor of slim columns): roof u -55..-21, v -107..-125 (north half), out to -131 south of u -40; z 24
from shapely.geometry import Point
for nm,q in(('eastB_n',[(-55.0,-107.0),(-55.0,-125.0),(-40.0,-125.0),(-40.0,-107.0)]),('eastB_s',[(-40.0,-107.0),(-40.0,-131.0),(-21.0,-131.0),(-21.0,-107.0)])):
    office_box(nm,q)
# D: office block south of the deck: roof u 10..47.5, east edge v -127.5 at u 12 to -124.4 at u 47.5; z 24
office_box('eastD',[(10.0,-107.0),(10.0,-131.3),(47.5,-124.6),(47.5,-107.0)])
# roof plant on B and D (the dark grilles in the satellite)
for nm,q,z in(('eastB_plant',[(-54.0,-109.0),(-54.0,-117.0),(-47.0,-117.0),(-47.0,-109.0)],24.0),('eastB_plant2',[(-38.0,-108.5),(-38.0,-123.0),(-22.5,-123.0),(-22.5,-108.5)],24.0),
                ('eastD_plant',[(11.0,-110.0),(11.0,-124.0),(28.0,-124.0),(28.0,-110.0)],24.0),('eastD_plant2',[(32.0,-107.5),(32.0,-116.0),(44.5,-116.0),(44.5,-107.5)],24.0)):
    vent_block(nm,lean(q,z+2.0),z,z+2.0,z+0.25,z+1.75,bay=3.0,pier=0.8,depth=0.25,wall='silver',top='silver')
# C: car deck between B and D (roof u -21..10, v -116..-124, z 7) and the white walkway strip beside the wall (v -107..-116, z 10)
prism('eastC_deck',lean([(-21.0,-116.0),(-21.0,-124.0),(10.0,-124.0),(10.0,-116.0)],7.0),0.0,7.0,'navy','paving')
prism('eastC_walk',lean([(-21.0,-107.0),(-21.0,-116.0),(10.0,-116.0),(10.0,-107.0)],10.0),0.0,10.0,'officeglass','white')
# ---------------- west forecourt: glazed hall under the terrace, front v 139.4, roof = deck 6.5; stairs down at both ends
FU0,FU1,FV=-47.0,46.5,139.4
fb=[(u,v) for u,v in bal if FU0<u<FU1]
# its street front is blue-grey glass behind posts, darker than the south curtain wall (PC check 2026-11-23: GE (76, 102, 118))
prism('plinth_forecourt',[(FU0,120.5),(FU0,FV),(FU1,FV),(FU1,125.0)]+sorted(fb,key=lambda t:-t[0]),0.0,ZP,'fcglass','paving')
def stair(name,u0,u1,v0,v1,zt):
    V=[(u0,v0,zt),(u0,v1,zt),(u1,v1,0.0),(u1,v0,0.0),(u0,v0,0.0),(u0,v1,0.0)]
    add(name,V,[[0,1,2,3],[4,0,3],[5,2,1],[0,4,5,1]],['paving','concrete','concrete','concrete'])
stair('plinth_stairN',FU0,-62.0,124.0,137.0,ZP);stair('plinth_stairS',FU1,60.5,126.0,137.0,ZP)
# ---------------- the MARVEL STADIUM sign stands on the roof over the west side, on short posts above the fascia: red MARVEL
# panel + black STADIUM panel, lettering on the outward face only (ground's own sign, director 2026-11-19). Placed
# 2026-11-23 from Google Earth's 3D picks (the sign's face at v 96-97, its top 49.4 m) and the Marvel_Stadium_2019 photo
# (Wikimedia Commons: the sign clear above the roof's edge, posts under it); it had been tucked under the roof's edge.
# Height from the sign's own proportions, which need no camera: 4.2 wide to 1 tall in the 2019 photo and 4.3 in Google
# Earth's view from the west, so about 7.6 m on its 33.4 m width (Google Earth's mesh, which smooths thin tops, reads 4.7).
SV0,SZ0,SZ1=97.0,45.6,53.2  # 45.6 = 6 tiles of 7.6 m, so the lettering texture starts at the panel's foot
prism('sign_red',[(-16,SV0),(-2.5,SV0),(-2.5,SV0+1.0),(-16,SV0+1.0)],SZ0,SZ1,'signred','signred',side_m=['signred','signred','sign_marvel','signred'],bottom='signred')
prism('sign_black',[(-2.5,SV0),(17.4,SV0),(17.4,SV0+1.0),(-2.5,SV0+1.0)],SZ0,SZ1,'signblack','signblack',side_m=['signblack','signblack','sign_stadium','signblack'],bottom='signblack')
beams('sign_posts',[((u_,SV0+0.5,roof_top(u_,SV0+0.5)-0.2),(u_,SV0+0.5,SZ0)) for u_ in(-14.0,-6.0,2.0,10.0,16.0)],0.3,'silver')
from shapely.geometry import Polygon,MultiPoint
from shapely.ops import unary_union
_S=np.array([uvw(u,v,0.0)[:2] for u,v in((0,0),(1,0),(0,1))]);_A=np.linalg.inv(np.stack([_S[1]-_S[0],_S[2]-_S[0]],1))
def to_uv(xy):return (_A@(np.asarray(xy)[:2]-_S[0]))
_fp=[]
for p in PARTS:
    V=np.asarray(p['V']);g=V[V[:,2]<0.5]
    if len(g)>=3 and V[:,2].max()>2.0:
        h=MultiPoint([tuple(to_uv(x)) for x in g]).convex_hull
        if h.area>1.0:_fp.append(h.buffer(0.01))
_U=unary_union(_fp).buffer(6.0,join_style=2).buffer(-4.0,join_style=2)
_U=max(_U.geoms,key=lambda g:g.area) if _U.geom_type=='MultiPolygon' else _U
_ex=np.array(_U.exterior.coords)[:-1];_ang=np.arctan2(_ex[:,1],_ex[:,0])
# radial ring with the same angles for the hole (plinth inner edge), so the pad is one loft band (top) plus an outer skirt
_r=np.hypot(_ex[:,0],_ex[:,1]);_hole=np.stack([(se_r(_ang,OA,OB,ON)-6.0)*np.cos(_ang),(se_r(_ang,OA,OB,ON)-6.0)*np.sin(_ang)],1)
ZB0=-1.0;ZB1=0.05
loft('site_base',[z3(_ex,ZB0),z3(_ex,ZB1),z3(_hole,ZB1)],['concrete','paving'])
json.dump(dict(parts=PARTS,seats=SEATS,cam=P('c5.json')),open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'parts2.json'),'w'))
print(len(SEATS),'seats',len(PARTS),'parts',sum(len(p['F']) for p in PARTS),'faces')
