# Marvel Stadium exterior: geometry from the matched camera's measurements (local s,t metres -> world).
from frame import *
from scipy.optimize import least_squares
from scipy.interpolate import CubicSpline
G=json.load(open('osm/geo.json'))
S0,T0=4.75,4.0;ZP=6.0
def rot(p):p=np.asarray(p,float);return np.array([2*S0-p[0],2*T0-p[1]])
def W(s,t,z):return wld(s,t,z)
PARTS=[]
def add(name,V,F,mat='photo',sym=False):PARTS.append(dict(name=name,V=np.asarray(V).tolist(),F=F,mat=mat,sym=sym))
def osm_loc(id):
    a=np.array(G['ways'][id]);q=loc(np.c_[a,np.zeros(len(a))]);return q[:-1] if np.allclose(q[0],q[-1]) else q
def prism(name,q,z0,z1,mat='photo',sym=False,bottom=False):
    q=np.asarray(q,float);n=len(q);V=[W(s,t,z0) for s,t in q]+[W(s,t,z1) for s,t in q]
    F=[[i,(i+1)%n,n+(i+1)%n,n+i] for i in range(n)]+[list(range(n,2*n))]
    if bottom:F.append(list(range(n))[::-1])
    add(name,V,F,mat,sym)   # normals fixed in Blender (recalculate outside)
def beam(a,b,w):
    a=np.asarray(a,float);b=np.asarray(b,float);d=b-a;d/=np.linalg.norm(d)
    u=np.cross(d,[0,0,1.0])
    if np.linalg.norm(u)<1e-3:u=np.array([1.0,0,0])
    u/=np.linalg.norm(u);v=np.cross(u,d);h=w/2
    c=[a+h*(su*u+sv*v) for su,sv in((-1,-1),(1,-1),(1,1),(-1,1))]+[b+h*(su*u+sv*v) for su,sv in((-1,-1),(1,-1),(1,1),(-1,1))]
    F=[[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7],[3,2,1,0],[4,5,6,7]];return c,F
def beams(name,segs,w,mat,sym):
    V=[];F=[]
    for a,b in segs:
        c,f=beam(a,b,w);o=len(V);V+=c;F+=[[o+i for i in ff] for ff in f]
    add(name,V,F,mat,sym)
# ---------- roof outline: superellipse about (S0,T0), fitted to measured edge points + their 180 deg copies
RN=[(-93.5,-0.2),(-97.3,7.5),(-96.7,30.5),(-94.0,48.7),(-88.7,64.6),(-82.8,77.4),(-73.7,92.8),(-67.7,98.8)]
RS=[(90.5,89.7),(95.6,80.3),(100.0,69.2),(104.0,56.4),(106.0,46.1),(106.1,34.9),(106.8,30.7),(104.5,2.0),(94.4,-19.6)]
RF=[(11.7,108.8)]
E=np.array(RN+RS+RF);E=np.vstack([E,[rot(p) for p in E]])-[S0,T0]
def se_r(th,a,b,n):return 1/((np.abs(np.cos(th))/a)**n+(np.abs(np.sin(th))/b)**n)**(1/n)
def res(p):
    a,b,n=p;th=np.arctan2(E[:,1],E[:,0]);return np.hypot(*E.T)-se_r(th,a,b,n)
fit=least_squares(res,[100,105,3]);A_,B_,N_=fit.x
print('roof superellipse a %.1f b %.1f n %.2f rms %.2f'%(A_,B_,N_,np.sqrt(np.mean(fit.fun**2))),np.round(fit.fun,1))
# replace the superellipse by a periodic spline through the measured edge points (and their 180 deg copies);
# (94.4,-19.6) dropped: the far side of the south end bends down out of sight there
_E=np.array([p for p in RN+RS+RF if p!=(94.4,-19.6)],float);_E=np.vstack([_E,[rot(p) for p in _E]])-[S0,T0]
_th=np.arctan2(_E[:,1],_E[:,0]);_r=np.hypot(*_E.T);_o=np.argsort(_th);_th,_r=_th[_o],_r[_o]
# periodic spline through the measured points; points closer than 6 m (a point and a twin of another) are averaged first,
# otherwise the spline overshoots between them
def _merge(P,d=6.0):
    P=[np.array(q) for q in P];out=[]
    while P:
        q=P.pop(0);grp=[q]+[w for w in P if np.hypot(*(w-q))<d];P=[w for w in P if np.hypot(*(w-q))>=d];out.append(np.mean(grp,0))
    return np.array(out)
_M=_merge(list(_E));_th=np.arctan2(_M[:,1],_M[:,0]);_r=np.hypot(*_M.T);_o=np.argsort(_th);_th,_r=_th[_o],_r[_o]
_cs=CubicSpline(np.r_[_th,_th[0]+2*np.pi],np.r_[_r,_r[0]],bc_type='periodic')
def se_r(th,a=0,b=0,n=0):return _cs(np.mod(np.asarray(th)-_th[0],2*np.pi)+_th[0])
def outline(k=160,off=0.0):
    th=np.linspace(-np.pi,np.pi,k,endpoint=False);r=se_r(th,A_,B_,N_)+off
    return np.stack([S0+r*np.cos(th),T0+r*np.sin(th)],1)
# ---------- opening corners (near measured, far by symmetry)
NIL=np.array([-69.5,69.3]);NIR=np.array([84.4,62.4]);FIL=rot(NIR);FIR=rot(NIL)
NFL=np.array([-66.0,106.7]);NFR=np.array([86.9,98.7])   # near-front truss feet
DFL=np.array([-66.9,110.8]);DFR=np.array([87.4,105.7])  # near deck front corners
# ---------- roof ring (fixed roof) between outline and opening quad
def ray_quad(th,quad):
    o=np.array([S0,T0]);d=np.array([np.cos(th),np.sin(th)]);best=1e9
    for i in range(4):
        a=quad[i];b=quad[(i+1)%4];M=np.array([d,a-b]).T
        try:x=np.linalg.solve(M,a-o)
        except np.linalg.LinAlgError:continue
        if x[0]>0 and -1e-6<=x[1]<=1+1e-6:best=min(best,x[0])
    return o+best*d
K=160;OUT=outline(K)
th=np.linspace(-np.pi,np.pi,K,endpoint=False);INN=np.array([ray_quad(a,[NIL,NIR,FIR,FIL]) for a in th])
ring=lambda A,B,za,zb:([W(*p,za) for p in A]+[W(*p,zb) for p in B],[[i,(i+1)%K,K+(i+1)%K,K+i] for i in range(K)])
add('roof_ring',*ring(OUT,INN,ZR,ZR),mat='roof',sym=True)
FZ=2.5;INS=3.0;BW=outline(K,-INS)
add('roof_fascia',*ring(OUT,OUT,ZR,ZR-FZ),sym=True)
add('roof_soffit',*ring(OUT,BW,ZR-FZ,ZR-FZ),sym=True)
add('bowl_wall',*ring(BW,BW,ZP,ZR-FZ),sym=True)
# ---------- near roof panel deck (slab); far twin added at the end
PT=1.2;ZD=ZR+PT
prism('panel_near',[NIL,NIR,DFR,DFL],ZR,ZD,'roof',True)
# ---------- space trusses (triangular section: curved top chord, two straight deck chords), fitted to photo pixels
TJ=json.load(open('truss.json'))
def spacetruss(a,b,H,phi,g,lean,n,o1,o2):
    a=np.asarray(a,float);b=np.asarray(b,float);lean=np.asarray(lean,float);T=[];B1=[];B2=[]
    for i in range(n+1):
        l=i/n;p=a+(b-a)*l;r=(H-ZD)*max(4*l*(1-l),0)**g
        T.append(W(*(p+lean*r*np.sin(phi)),ZD+r*np.cos(phi)));B1.append(W(*(p+lean*o1),ZD));B2.append(W(*(p+lean*o2),ZD))
    ch=[(X[i],X[i+1]) for X in (T,B1,B2) for i in range(n)]
    web=[(T[i],B1[i]) for i in range(1,n)]+[(T[i],B2[i]) for i in range(1,n)]
    for i in range(n):
        k,j=(i,i+1) if i<n/2 else (i+1,i)
        web+=[(B1[k],T[j]),(B2[k],T[j]),(B1[i],B2[i+1]) if i%2==0 else (B2[i],B1[i+1])]
    return ch,web
def add_truss(name,ch,web):
    beams(name+'_ch',ch,0.7,'teal',True);beams(name+'_web',web,0.35,'teal',True)
Fj=TJ['front'];Ij=TJ['inner']
add_truss('truss_near_front',*spacetruss(Fj['a'],Fj['b'],Fj['H'],Fj['phi'],Fj['g'],[0,-1],23,4.7,15.5))
add_truss('truss_near_inner',*spacetruss(Ij['a'],Ij['b'],Ij['H'],Ij['phi'],Ij['g'],[0,1],23,4.7,15.5))
# end arches: feet at the opening corners, leaning outward (fit: apex 59.3, 37 deg), rail (tan) 5 m in from the feet
IL=bp(310,393,ZD);IR=bp(1473,382,ZD)
EAH,EAPHI,EAG=59.287,-0.65,1.602
add_truss('arch_north',*spacetruss(IL,rot(IR),EAH,EAPHI,EAG,[1,0],20,0.0,5.0))
beams('rail_north',[(W(*(IL+[5,0]),ZD+0.6),W(*(rot(IR)+[5,0]),ZD+0.6))],1.6,'tan',True)
# ---------- front podium (measured chain at s 11.7), terrace and deck
FR_T=108.8
def band(s0,s1,d0,d1,z0,z1,name,k=40):
    thh=np.linspace(-np.pi,np.pi,4000);r=se_r(thh,A_,B_,N_);x=S0+r*np.cos(thh);y=T0+r*np.sin(thh)
    m=(y>T0)&(x>=s0)&(x<=s1);thh=np.linspace(thh[m].min(),thh[m].max(),k);r=se_r(thh,A_,B_,N_)
    nrm=lambda r0:np.stack([S0+r0*np.cos(thh),T0+r0*np.sin(thh)],1)
    prism(name,np.vstack([nrm(r+d1),nrm(r+d0)[::-1]]),z0,z1)
band(-34,55,-INS,108.4-FR_T,ZP,22.3,'podium_upper')
band(-35,58,-INS,112.0-FR_T,ZP,13.9,'terrace')
PAR=np.array([(-44.8,108.0),(-31.5,118.4),(-23.0,123.2),(-13.7,124.2),(11.9,125.1),(36.7,122.3),(43.3,119.9),(53.2,115.1),(65.2,102.9)])
cs=CubicSpline(PAR[:,0],PAR[:,1]);ss=np.linspace(PAR[0,0],PAR[-1,0],40);front=np.stack([ss,cs(ss)],1)
back=np.array([p for p in outline(800,-INS) if p[1]>T0 and PAR[0,0]<=p[0]<=PAR[-1,0]]);back=back[np.argsort(-back[:,0])]
prism('deck',np.vstack([front,back]),ZP,7.0)
# ---------- cylinders (vents) on the deck; measured top pixels at 13.9
def cyl(name,c,r,z0,z1,k=16):
    a=np.linspace(0,2*np.pi,k,endpoint=False);prism(name,np.stack([c[0]+r*np.cos(a),c[1]+r*np.sin(a)],1),z0,z1)
for i,(u,v) in enumerate([(490,734),(504,722),(528,728),(514,740),(1228,718),(1252,714),(1238,732),(1262,726)]):
    c=bp(u,v,13.9);cyl('cyl%d'%i,c+np.array([0,-1.2]),1.2,7.0,13.9)
# ---------- towers (measured tops, absolute z)
TW={'tower_T1':([(-54.9,94.4),(-50.7,83.8),(-41.4,90.5),(-45.8,100.5)],21.9),'tower_T2':([(57.1,88.8),(64.6,83.5),(70.9,91.3),(63.5,97.3)],23.7),
    'tower_NW':([(-119,48.1),(-113.6,39.8),(-99,48.6),(-104.6,59.1)],28.3),'tower_SW':([(109.6,30.6),(122.8,16),(130.3,23),(117.5,36.9)],24.2)}
for k,(q,h) in TW.items():prism(k,q,ZP,h)
# ---------- plaza slab and AFL House pavilion (OSM)
prism('plaza',osm_loc('23272382'),0.0,ZP)
prism('pavilion',osm_loc('57019580'),0.0,6.6)
# ---------- twins: 180 deg copies of the near-only symmetric parts
Cw=wld(S0,T0,0);out=[]
for p in PARTS:
    out.append(p)
    if p['name'].split('_ch')[0].split('_web')[0] in('panel_near','truss_near_inner','truss_near_front','arch_north','rail_north'):
        V=np.array(p['V']);V2=V.copy();V2[:,:2]=2*Cw[:2]-V[:,:2]
        out.append(dict(name=p['name']+'_tw',V=V2.tolist(),F=p['F'],mat=p['mat'],sym=True))
json.dump(dict(parts=out,C=Cw[:2].tolist(),cam=P),open('parts.json','w'))
print(len(out),'parts',sum(len(p['F']) for p in out),'faces')
