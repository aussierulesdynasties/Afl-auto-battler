# Marvel Stadium exterior, geometry in the stadium frame (u south+, v west+, z up from the street lawns).
# Measured values: sat/measures.md. Writes parts2.json: per part V (world xyz), F, M (material per face), UV (metres per corner).
import sys,os,json,math,numpy as np
MV=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','mv');sys.path.insert(0,MV);os.chdir(MV)
from sf import *
from scipy.interpolate import UnivariateSpline
PRM=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'prm.json'))) if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)),'prm.json')) else {}
def G(k,d):return PRM.get(k,d)
ZS=G('ZS',44.0);ZO=G('ZO',38.0);ZG=G('ZG',33.0);ZT=G('ZT',55.0);ZB=G('ZB',46.0);ZP=G('ZP',6.5);FL=G('FL',4.0)
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
NP=[(-84.3,74),(-90,68),(-98,61),(-105.5,52.5),(-112,40),(-115,35),(-118,23.5),(-119.5,15),(-120,0),(-119.25,-15),(-116.25,-30),(-113.75,-35),(-108,-45),(-98,-60),(-90,-67),(-84.1,-74)]
SP=[(84.6,-74),(90,-69),(97,-64),(103.5,-60),(114.5,-40),(116.25,-35),(120.5,-15),(124.5,0),(122.75,10),(120.5,15),(117.5,35),(115,40),(110,50),(103.5,60),(97,64),(90,69),(84,74)]
def arc(pts,sgn,n=97):
    p=np.array(pts,float);c=np.array([sgn*40.0,0]);d=p-c;ph=np.arctan2(d[:,1],sgn*d[:,0]);r=np.hypot(*d.T);o=np.argsort(ph)
    sp=UnivariateSpline(ph[o],r[o],k=3,s=len(p)*0.8);q=np.linspace(ph[o][0],ph[o][-1],n);rr=sp(q)
    out=np.stack([c[0]+sgn*rr*np.cos(q),rr*np.sin(q)],1);out[0]=p[o][0];out[-1]=p[o][-1];return out
ARC_N=arc(NP,-1);ARC_S=arc(SP,1)
def slab_z(av):  # side roof top height at |v|
    return np.where(av>=66,ZS,ZO+(np.clip(av,51,66)-51)/15*(ZS-ZO))
def end_prof(s):return ZG+(ZO-ZG)*(1-s**1.6)
UE=84.0
# ---------------- side roofs (slabs) with fascia, soffit, panel stack
def slab(name,vin,vout,u0,u1):
    sg=np.sign(vout)
    sec=[(vout,ZS),(sg*66,ZS),(vin,ZO),(vin,ZO-1.1),(sg*66,ZS-1.1),(vout,ZS-1.1)]  # (v,z)
    mats=['deck','deck','fascia','soffit','soffit','fascia']
    V=[(u0,v,z) for v,z in sec]+[(u1,v,z) for v,z in sec];n=len(sec);F=[];M=[]
    for i in range(n):F.append([i,(i+1)%n,n+(i+1)%n,n+i]);M.append(mats[i])
    F.append(list(range(n))[::-1]);M.append('fascia');F.append(list(range(n,2*n)));M.append('fascia')
    add(name,V,F,M)
    # retracted roof panels stacked along the opening edge (v ~50..60): three plates, each a step higher
    for k in range(3):
        a=vin+sg*0.0;b=vin+sg*(9.5-2.2*k);zz=lambda v:float(slab_z(np.array(abs(v))))+0.35*(k+1)
        q=[(u0+1,a,ZO+0.35*(k+1)),(u1-1,a,ZO+0.35*(k+1)),(u1-1,b,zz(b)),(u0+1,b,zz(b))]
        q2=[(x,y,z-0.3) for x,y,z in q];V=q+q2;F=[[0,1,2,3],[4,7,6,5],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]]
        add(name+'_panel%d'%k,V,F,['deck2','soffit','fascia','fascia','fascia','fascia'])
slab('slab_w',51.0,102.8,-84.3,84.0);slab('slab_e',-52.2,-103.6,-84.1,84.6)
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
    add(name+'_channels',V,F,'riser',UV)
    out=np.array([ARC[i]-ARC[i-1] if i else ARC[1]-ARC[0] for i in range(len(ARC))]);nrm=np.stack([sgn*out[:,1],-sgn*out[:,0]],1)
    nrm=-nrm if np.mean(np.sum(nrm*(ARC-[sgn*60,0]),1))<0 else nrm;nrm/=np.linalg.norm(nrm,axis=1)[:,None]
    g0=np.c_[ARC,np.full(len(ARC),ZG)];g1=np.c_[ARC+nrm*0.9,np.full(len(ARC),ZG+0.25)];g2=np.c_[ARC+nrm*0.9,np.full(len(ARC),ZG-0.9)];g3=np.c_[ARC,np.full(len(ARC),ZG-0.9)]
    loft(name+'_gutter',[g0,g1,g2,g3],['gutter','gutter','soffit'],closed=False)
    # end faces between the slab corners and the arc ends are covered by the slab end fascia + corner blocks
end_roof('end_n',ARC_N,-1);end_roof('end_s',ARC_S,1)
# ---------------- roof height function (top), for walls/brackets under it
def roof_top(u,v):
    if abs(u)<=UE and abs(v)>=51:return float(slab_z(np.array(abs(v))))
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
    v0,v1=-51.4,50.2;half=(v1-v0)/2;vc=(v0+v1)/2;T=[];B1=[];B2=[]
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
for nm,(u_,vin,vout) in(('w0',(-84.3,51.0,74.0)),('w1',(84.0,51.0,74.0)),('e0',(-84.1,-52.2,-74.0)),('e1',(84.6,-52.2,-74.0))):
    vs=np.linspace(vin,vout,12);top=[float(slab_z(np.array(abs(v))))-1.1 for v in vs]
    q=[(u_,v,ZO-0.2) for v in vs]+[(u_,v,t) for v,t in zip(vs[::-1],top[::-1])]
    add('slab_end_'+nm,q,[list(range(len(q)))],'fascia')
south=PU>92
def segm(a,b):return [b if s else a for s in south]
def cl(z):return np.minimum(z,RU-0.4) if np.ndim(z) else np.minimum(np.full(K,z),RU-0.4)
# (offset from the face, height) read off the aerial pixel table at u 10 (mv/p2uv.py, mv/vert.py)
prof=[(-4,ZP),(-4,13.2),(0,13.2),(0,14.3),(-0.6,14.3),(-0.6,21.4),(0,21.4),(0,24.9),(-0.4,24.9),(-0.4,26.3),(0,26.3),(0,27.7),
      (-3,27.7),(-3,33.9),(0,33.9),(0,36.5),(-5,36.5),(-5,None)]
mats=['glass','soffit','silver','soffit',segm('curtain','curtain'),'soffit','silver','soffit','glass','soffit','silver','soffit',
      'glass','soffit','silver','silver','soffit']
rings=[ring(o,RU if z is None else cl(z)) for o,z in prof]
loft('bowl_wall',rings,mats)
# white round columns in front of the shopfront, one every 8 m of perimeter (none behind the west podium)
per=np.r_[0,np.cumsum(np.hypot(np.diff(np.r_[PU,PU[:1]]),np.diff(np.r_[PV,PV[:1]])))];k=0
for L in np.arange(2,per[-1],8.0):
    i=np.searchsorted(per,L)-1;t=(L-per[i])/(per[i+1]-per[i]);th=TH[i]+(t*(2*np.pi/K));r=se_r(th,OA,OB,ON)-1.0
    cu,cv=r*np.cos(th),r*np.sin(th)
    if -40<cu<46 and cv>0:continue
    cyl('col%03d'%k,(cu,cv),0.4,ZP,13.2,'white','white',12);k+=1
# teal V-braces in the upper recess (27.7..33.9), every 8 m round the bowl
segs=[]
for L in np.arange(0,per[-1],8.0):
    i=np.searchsorted(per,L)-1;th=TH[max(i,0)];th2=th+8.0/per[-1]*2*np.pi*0.5
    def P3(t_,o,z):r=se_r(t_,OA,OB,ON)+o;return (r*np.cos(t_),r*np.sin(t_),z)
    zt=min(33.9,float(roof_top(*P3(th,-5,0)[:2]))-1.6)
    if zt<29:continue
    segs+=[(P3(th,-1.0,27.8),P3(th2,-1.0,zt)),(P3(th2,-1.0,zt),P3(th+8.0/per[-1]*2*np.pi,-1.0,27.8))]
beams('recess_braces',segs,0.35,'teal')
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
# ---------------- west podium: glazed ground storey (front v 119), terrace 13.2, upper block (front v 113.5) to 21.4
def band_poly(u0,u1,vout,o=-3.0):
    us=np.linspace(u0,u1,25);vb=[]
    for u in us:
        vv=np.linspace(0,130,2600);thv=np.arctan2(vv,u);j=np.where(np.hypot(u,vv)<=se_r(thv,OA,OB,ON)+o)[0][-1];vb.append(vv[j])
    return [(u,vout) for u in us]+[(u,v) for u,v in zip(us[::-1],vb[::-1])]
prism('podium_l1',band_poly(-40,46,119.0),ZP,13.2,'base','paving')
box('podium_rail',-40,46,118.8,119.0,13.2,14.3,'glass','white')
prism('podium_l2',band_poly(-43,31,113.5),13.2,21.4,'navy','concrete')
for i,(u,w) in enumerate(((-41.5,5),(-26.0,4.4),(-21.6,4.4),(9.6,4.4),(14.0,4.4),(28.5,5))):
    box('canopy%d'%i,u-w/2,u+w/2,114.0,118.4,15.7,16.0,'canvas','canvas','canvas')
    for du,dv in((-1,0.2),(1,0.2),(-1,4.2),(1,4.2)):cyl('canopy%d_post%d%d'%(i,du>0,dv>1),(u+du*(w/2-0.2),114+dv),0.07,13.2,15.7,'white','white',6)
for cu,cv,h in((-45.8,110.4,17.8),(43.3,111.8,16.7)):
    for du,dv in((-1.3,-1.3),(1.3,-1.3),(-1.3,1.3),(1.3,1.3)):cyl('tank_%d_%d%d'%(cu,du>0,dv>0),(cu+du,cv+dv),1.2,ZP,h,'tank','tank')
# ---------------- seating bowl inside (no field): three tiers between the pitch fence and the outer wall
PA,PB,PN=G('PA',86.0),G('PB',72.0),G('PN',2.2)
rp=se_r(TH,PA,PB,PN)+2.0;D=r0-6.0-rp
def tier(name,f0,f1,zf,zb,lip=1.1):
    a=rp+D*f0;b=rp+D*f1;c=np.cos(TH);s=np.sin(TH)
    P=lambda r,z:np.stack([r*c,r*s,np.full(K,z) if np.ndim(z)==0 else z],1)
    rings=[P(a,zf-lip-0.6),P(a,zf),P(b,zb),P(b,zb-1.0),P(a,zf-lip-0.6)]
    loft(name,rings[:4]+[rings[0]],['concrete','seats','concrete','soffit'])
tier('tier1',0.0,0.62,FL+1.4,FL+12.0);tier('tier2',0.40,0.80,FL+15.0,FL+23.0);_b3=rp+D*1.0;_rt=np.array([roof_top(r*math.cos(t),r*math.sin(t)) for r,t in zip(_b3,TH)])
tier('tier3',0.62,1.0,FL+26.5,np.minimum(FL+37.0,_rt-1.5))  # back row stays under the roof (ends at 33-38 m)
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
    prism('cornerN_tower_'+tw,[m(*c) for c in TWN],0.0,33.0,'louvre','concrete')
    if sg>0:prism('cornerS_tower_'+tw,[m(*c) for c in TWS],0.0,33.0,'louvre','concrete')
    for uc,vc in((-54.2,107.2),(54.3,108.4)):
        cu,cv=m(uc,vc);box('beige_%s_%d'%(tw,int(uc)),cu-6,cu+6,cv-5,cv+5,0.0,27.4,'slate','glass' if (sg<0 and cu<0) else 'canvas')
    for u0_,u1_ in((-80,-58),(57,80)):
        us=np.linspace(u0_,u1_,12);q=[m(u,face_v(u,3.5)) for u in us]+[m(u,face_v(u,-2)) for u in us[::-1]]
        prism('pod_%s_%d'%(tw,u0_),q,24.0,31.0,'curtain','silver')
    for k,L in enumerate((FLN,FLS)):
        if sg<0 and k==1:L=[c for c in L if c[0]<88.0]  # NE: the satellite shows open paving north of u -88
        q=fill_line('',L,0,0,0.0,'','');prism('fill1_%s_%d'%(tw,k),[m(*c) for c in q],0.0,22.0,'louvre','concrete')
        q=fill_line('',L,0,0,2.5,'','');prism('fill0_%s_%d'%(tw,k),[m(*c) for c in q],0.0,10.0,'slate','concrete')
# ---------------- east side, read off the straight-down satellite (roof outline seen at height z, footprint = roof + lean*z,
# lean du +0.1738, dv +0.0805 per metre); heights from the shadow lengths (0.5 m of shadow per metre, calibrated on the roof edge)
def lean(q,z):return [(u+0.1738*z,v+0.0805*z) for u,v in q]
# NE corner: one long block (roof 9.3 m wide, 38.7 m long) from the roof corner to the plaza, z 33, plant room on top to 37
NEB=[(-120.3,-59.1),(-125.6,-66.7),(-93.9,-88.9),(-88.6,-81.3)]
prism('cornerNE_block',lean(NEB,33.0),0.0,33.0,'louvre','concrete')
_c=np.mean(lean([(-106.4,-78.3)],37.0),0);rbox('cornerNE_plant',tuple(_c),9.0,7.5,math.atan2(-0.574,0.819),33.0,37.0,'silver','concrete')
# B: office block north of the deck: roof u -55..-21, v -107..-125 (north half), out to -131 south of u -40; z 24
for nm,q in(('eastB_n',[(-55.0,-107.0),(-55.0,-125.0),(-40.0,-125.0),(-40.0,-107.0)]),('eastB_s',[(-40.0,-107.0),(-40.0,-131.0),(-21.0,-131.0),(-21.0,-107.0)])):
    f=lean(q,24.0);prism(nm+'_lo',f,0.0,9.0,'glass','concrete');prism(nm,f,9.0,24.0,'louvre','concrete')
# D: office block south of the deck: roof u 10..47.5, east edge v -127.5 at u 12 to -124.4 at u 47.5; z 24
q=[(10.0,-107.0),(10.0,-131.3),(47.5,-124.6),(47.5,-107.0)];f=lean(q,24.0)
prism('eastD_lo',f,0.0,9.0,'glass','concrete');prism('eastD',f,9.0,24.0,'louvre','concrete')
# roof plant on B and D (the dark grilles in the satellite)
for nm,q,z in(('eastB_plant',[(-54.0,-109.0),(-54.0,-117.0),(-47.0,-117.0),(-47.0,-109.0)],24.0),('eastB_plant2',[(-38.0,-108.5),(-38.0,-123.0),(-22.5,-123.0),(-22.5,-108.5)],24.0),
                ('eastD_plant',[(11.0,-110.0),(11.0,-124.0),(28.0,-124.0),(28.0,-110.0)],24.0),('eastD_plant2',[(32.0,-107.5),(32.0,-116.0),(44.5,-116.0),(44.5,-107.5)],24.0)):
    prism(nm,lean(q,z+2.0),z,z+2.0,'louvre','silver')
# C: car deck between B and D (roof u -21..10, v -116..-124, z 7) and the white walkway strip beside the wall (v -107..-116, z 10)
prism('eastC_deck',lean([(-21.0,-116.0),(-21.0,-124.0),(10.0,-124.0),(10.0,-116.0)],7.0),0.0,7.0,'navy','paving')
prism('eastC_walk',lean([(-21.0,-107.0),(-21.0,-116.0),(10.0,-116.0),(10.0,-107.0)],10.0),0.0,10.0,'glass','white')
# ---------------- west forecourt: glazed hall under the terrace, front v 139.4, roof = deck 6.5; stairs down at both ends
FU0,FU1,FV=-47.0,46.5,139.4
fb=[(u,v) for u,v in bal if FU0<u<FU1]
prism('plinth_forecourt',[(FU0,120.5),(FU0,FV),(FU1,FV),(FU1,125.0)]+sorted(fb,key=lambda t:-t[0]),0.0,ZP,'curtain','paving')
def stair(name,u0,u1,v0,v1,zt):
    V=[(u0,v0,zt),(u0,v1,zt),(u1,v1,0.0),(u1,v0,0.0),(u0,v0,0.0),(u0,v1,0.0)]
    add(name,V,[[0,1,2,3],[4,0,3],[5,2,1],[0,4,5,1]],['paving','concrete','concrete','concrete'])
stair('plinth_stairN',FU0,-62.0,124.0,137.0,ZP);stair('plinth_stairS',FU1,60.5,126.0,137.0,ZP)
# ---------------- sign box on the wall top under the roof (no lettering): red panel + black panel
box('sign_red',-16,-2.5,104.5,105.5,36.5,41.2,'signred','signred');box('sign_black',-2.5,17.4,104.5,105.5,36.5,41.2,'signblack','signblack')
json.dump(dict(parts=PARTS,cam=P('c5.json')),open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'parts2.json'),'w'))
print(len(PARTS),'parts',sum(len(p['F']) for p in PARTS),'faces')
