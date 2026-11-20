# Manuka Oval exterior, world metres (x east, y north, z up). Writes model.json for bl_build.py.
import json,math,numpy as np
from polar import redge,PC,G,MASTS,HN,AL
MATS={'turf':(95,120,45),'teal':(45,115,150),'multi':(150,90,80),'conc':(196,186,170),'roofg':(150,156,162),
 'white':(228,230,232),'facade':(95,70,50),'pavroof':(105,110,115),'red':(175,40,40),'fence':(236,236,236),
 'pave':(165,160,152),'hill':(105,130,58),'tower':(214,214,214),'glass':(40,50,60),'wseat':(225,225,222),'dark':(55,58,62),'banner':(30,30,32)}
OBJ=[]
def add(name,mat,V,F,n=0,uv=None):
    o={'name':name,'mat':mat,'n':n,'v':np.round(np.array(V,float),3).tolist(),'f':[list(map(int,f)) for f in F]}
    if uv is not None:o['uv']=[[float(a),float(b)] for a,b in uv]
    OBJ.append(o)
# photo grass edge = OSM pitch edge + a smooth correction fitted to the manual grass-edge points (deg, metres)
# grass edge correction (metres beyond the OSM edge) by angle: north/west from manual points, south and east from a pixel scan
# of the turf boundary against the fence top (2026-11-18); exact periodic linear interpolation
_GE=[(231,-0.41),(221,-0.21),(208,0.0),(194,0.05),(181,-0.12),(156,-1.08),(141,-1.92),(118,-3.17),(28,-0.91),
    (0,1.5),(10,1.1),(20,0.3),(270,4.3),(290,4.0),(295,4.1),(300,4.3),(305,4.0),(310,4.2),(315,4.2),(320,4.4),(325,4.6),(330,5.0),(335,5.0),(340,5.5),(345,5.8)]
_GT=np.array([t for t,_ in _GE],float);_GV=np.array([v for _,v in _GE],float)
def edge(a):return redge(a)+float(np.interp(math.degrees(a)%360,_GT,_GV,period=360))
def P(a,d,z):r=edge(a)+d;return (PC[0]+r*math.cos(a),PC[1]+r*math.sin(a),z)
def hits(poly,a):
    u=np.array([math.cos(a),math.sin(a)]);out=[];Pp=np.array(poly)
    for i in range(len(Pp)-1):
        p,q=Pp[i]-PC,Pp[i+1]-PC;e=q-p;M=np.array([u,-e]).T
        if abs(np.linalg.det(M))<1e-9:continue
        t,s=np.linalg.solve(M,p)
        if 0<=s<=1 and t>0:out.append(t)
    return sorted(out)
def band(name,mat,t0,t1,prof,step=1.0,closed=False):
    """prof(a)->list of (d,z): a strip surface swept around the pitch from angle t0..t1 (deg)."""
    A_=list(np.arange(t0,t1+1e-6,step)) if t1>t0 else [t0]
    if A_[-1]<t1-1e-6:A_.append(t1)
    ang=np.radians(A_)
    V=[];F=[];n=None
    for a in ang:
        pr=prof(a);n=len(pr)
        for d,z in pr:V.append(P(a,d,z))
    for i in range(len(ang)-1):
        for j in range(n-1):
            A=i*n+j;F.append([A,A+1,A+n+1,A+n])
    add(name,mat,V,F,n)
def seatblocks(name,mat,t0,t1,prof,aisles,step=0.5):
    """seat band t0..t1 split into blocks by stair aisles [(a0,a1),...] (deg, read off the photo unwraps z/uw_*.png)"""
    cur=t0
    for a0,a1 in sorted(aisles):
        if a1<=t0 or a0>=t1:continue
        a0,a1=max(a0,t0),min(a1,t1)
        if a0>cur:band(name,mat,cur,a0,prof,step)
        band(name+'_stair','stairs',a0,a1,prof,step);cur=a1
    if cur<t1:band(name,mat,cur,t1,prof,step)
def prism(name,mat,poly,z0,z1,top=True):
    poly=[tuple(p) for p in poly];
    if poly[0]==poly[-1]:poly=poly[:-1]
    n=len(poly);V=[(x,y,z0) for x,y in poly]+[(x,y,z1) for x,y in poly];F=[[i,(i+1)%n,n+(i+1)%n,n+i] for i in range(n)]
    if top:F.append(list(range(2*n-1,n-1,-1))[::-1])
    add(name,mat,V,F)
def box(name,mat,c,sx,sy,sz,rot=0.0,z0=0.0):
    ca,sa=math.cos(rot),math.sin(rot);pts=[(-sx/2,-sy/2),(sx/2,-sy/2),(sx/2,sy/2),(-sx/2,sy/2)]
    poly=[(c[0]+ca*x-sa*y,c[1]+sa*x+ca*y) for x,y in pts];prism(name,mat,poly,z0,z0+sz)
def quad(name,mat,pts):add(name,mat,pts,[[0,1,2,3]])
# ground and turf
sv=[P(math.radians(t),62,-0.05) for t in range(0,360,3)];add('site','lawn',sv,[list(range(len(sv)))])
tv=[P(math.radians(t),0,0.03) for t in range(0,360,2)];add('turf','turf',tv,[list(range(len(tv)))])
# boundary fence all round (front wall of stands where they exist)
band('fence','fence',0,360,lambda a:[(0.0,0.03),(0.0,1.1),(0.3,1.1)],step=1.0)
# ---- north stand (Hawke), footprint 40..142 deg
HW=G['122524195']
def wN(a):h=hits(HW,a);return (h[-1]-edge(a)) if len(h)>=2 else 13.0
NL=dict(fz=1.1,ld=4.5,lz=2.3,cd=7.0,uz=3.3,ud=16.0,uz2=8.0,rf=7.0,rfz=8.6,rb=17.0,rbz=9.4)
def nprof(a):
    q=NL;return q
seatblocks('n_lower','teal',50,152,lambda a:[(-1.5,NL['fz']),(NL['ld'],NL['lz'])],[(64.25, 65.5), (73, 74.25), (81.75, 83.5), (87, 88.6), (95.5, 97), (104.1, 105.2), (113, 113.8), (121.2, 122.4), (130.4, 131.4), (140, 141.1)])
band('n_conc','conc',57,152,lambda a:[(NL['ld'],NL['lz']),(NL['cd'],NL['lz']),(NL['cd'],NL['uz'])])
seatblocks('n_upper','navy',57,88.6,lambda a:[(NL['cd'],NL['uz']),(NL['ud'],NL['uz2'])],[(64.4, 65.6), (73.0, 74.19999999999999), (81.5, 82.69999999999999), (89.7, 90.89999999999999), (95.60000000000001, 96.8), (104.60000000000001, 105.8), (113.30000000000001, 114.5), (122.5, 123.69999999999999), (131.6, 132.79999999999998), (140.9, 142.1)])
seatblocks('n_upper','multi',88.6,152,lambda a:[(NL['cd'],NL['uz']),(NL['ud'],NL['uz2'])],[(64.4, 65.6), (73.0, 74.19999999999999), (81.5, 82.69999999999999), (89.7, 90.89999999999999), (95.60000000000001, 96.8), (104.60000000000001, 105.8), (113.30000000000001, 114.5), (122.5, 123.69999999999999), (131.6, 132.79999999999998), (140.9, 142.1)])
band('n_back','tower',57,152,lambda a:[(NL['ud'],NL['uz2']),(NL['rb'],NL['uz2']),(NL['rb'],0.0)])
band('n_roof','roofg',57,152,lambda a:[(NL['rf'],NL['rfz']),(NL['rb'],NL['rbz'])])
band('n_fascia','white',57,152,lambda a:[(NL['rf']-0.05,NL['rfz']-0.7),(NL['rf']-0.05,NL['rfz']+0.05)])   # white front edge of the roof (reference)
# ---- photo-traced helpers: photo outline back-projected at a height, extruded to the ground
import cam as _cam
def W(u,v,z):return tuple(_cam.at_z(u,v,z))
def photoprism(name,mat,uv,zt,z0=0.0,roofmat=None):
    poly=[W(u,v,zt)[:2] for u,v in uv];prism(name,mat,poly,z0,zt,top=roofmat is None)
    if roofmat:add(name+'_roof',roofmat,[(x,y,zt+0.05) for x,y in poly],[list(range(len(poly)))])
def ang(p):return math.atan2(p[1]-PC[1],p[0]-PC[0])
def face_to_fence(name,uvb,h,fmat,tmat,fz=1.1):
    G0=[W(u,v,0) for u,v in uvb];n=len(G0)
    V=[];F=[]
    for g in G0:V+= [g,(g[0],g[1],h),P(ang(g),0.3,fz)]
    for i in range(n-1):
        A=3*i;F.append([A,A+3,A+4,A+1])
    add(name,fmat,V,F)
    T=[];TF=[]
    for i in range(n-1):
        A=3*i;T.append([A+1,A+4,A+5,A+2])
    add(name+'_top',tmat,V,T)
# ---- Bradman stand: flat roof z 12 (back edge fitted to OSM back wall), glazed box z 6.5-12, seats fence -> box
SB,NB=(-100.3,-20.2),(-89.4,36.0)
BF_N,BF_S=(-73.1,32.1),(-85.9,-16.7)      # box face at z 6.5 (photo glass bottom line)
RF_N,RF_S=(-71.2,32.6),(-84.0,-16.2)      # roof front, 2 m proud of the box face
quad('b_roof','white',[(*SB,12),(*RF_S,12),(*RF_N,12),(*NB,12)])
prism('b_box','glass',[SB,BF_S,BF_N,NB],6.5,11.9,top=False)
prism('b_under','dark',[SB,BF_S,BF_N,NB],0,6.5,top=False)
def seg_hit(a,p0,p1):
    u=np.array([math.cos(a),math.sin(a)]);p0=np.array(p0)-PC;e=np.array(p1)-np.array(p0)-0;e=np.array(p1)-PC-p0
    M=np.array([u,-e]).T;t,s=np.linalg.solve(M,p0);return t,s
def bseat(a):
    t,s=seg_hit(a,BF_S,BF_N);s=min(max(s,0),1);x=BF_S[0]+s*(BF_N[0]-BF_S[0]);y=BF_S[1]+s*(BF_N[1]-BF_S[1])
    return math.hypot(x-PC[0],y-PC[1])-edge(a)
seatblocks('b_seats','wseat',158,190,lambda a:[(0.3,1.1),(bseat(a),6.5)],[(185.8, 186.8), (177.5, 178.5), (169.1, 170.1), (160.7, 161.7)])
# two vomitory hoods in the Bradman seats (light grey boxes at 180.8 and 166.8 deg, half to three-quarters up the rake)
for c in (180.8,166.8):
    a0,a1=math.radians(c-0.6),math.radians(c+0.6);am=math.radians(c);D=bseat(am)-0.3
    dA,zA,dB,zB=0.3+0.5*D,1.1+0.5*5.4,0.3+0.75*D,1.1+0.75*5.4
    prism('b_vom','white',[P(a0,dA,0)[:2],P(a1,dA,0)[:2],P(a1,dB,0)[:2],P(a0,dB,0)[:2]],zA-1.5,zB+0.4)
# ---- WSW stand 190..243: lower teal tier, concourse, upper multicolour tier, canopies at z 9.5 (ring-fitted)
seatblocks('w_lower','teal',190,237,lambda a:[(0.3,1.1),(9.0,3.0)],[(230.6, 231.6), (221.6, 222.6), (212.8, 213.8), (203.6, 204.6), (193.8, 194.8)])
band('w_conc','conc',190,237,lambda a:[(9.0,3.0),(11.0,3.0),(11.0,3.6)])
seatblocks('w_upper','multi',190,237,lambda a:[(11.0,3.6),(20,8.0)],[(230.6, 231.6), (221.6, 222.6), (212.8, 213.8), (203.6, 204.6), (193.8, 194.8)])
band('w_back','dark',190,237,lambda a:[(20,8.0),(21,8.0),(21,0)])
for t0,t1 in [(190,205),(206,218),(219,228),(229,237)]:
    band('w_canopy','canopy',t0,t1,lambda a:[(12.0,9.5),(21.5,9.8)])
    for t in (t0+1,t1-1):
        q=P(math.radians(t),21.0,0);box('w_post','tower',q,0.4,0.4,9.6)
# ---- SW curved building (photo-traced roof at z 14), lower outer roof z 9, glazed tip canopy
photoprism('s_bld','facade',[(205,790),(220,773),(250,760),(300,753),(355,758),(400,775),(450,795),(500,810),(540,826),(560,834),(530,845),(512,858),(500,878),(480,893),(450,890),(400,876),(350,863),(300,853),(250,842),(215,826),(203,808)],14.0,roofmat='white')
_o=[o for o in OBJ if o['name']=='s_bld'][0];OBJ.remove(_o)
_V=np.array(_o['v']);_west=min(W(u,v,0)[0] for u,v in [(250,760),(250,842)])
_parts={'mc_fins':[],'mc_field':[],'mc_ebony':[]}
for _f in _o['f']:
    _c=_V[_f].mean(0);_e=_V[_f[1]]-_V[_f[0]];_nrm=np.array([_e[1],-_e[0]]);_nrm/=np.linalg.norm(_nrm)+1e-9
    _toPC=np.array(PC)-_c[:2];_toPC/=np.linalg.norm(_toPC)
    _side=_nrm if _nrm@(_c[:2]-_V[:,:2].mean(0))>0 else -_nrm      # outward normal
    _j=_f[0];_U=[205,220,250,300,355,400,450,500,540,560,530,512,500,480,450,400,350,300,250,215,203]
    k='mc_fins' if (len(_f)==4 and _j<21 and (_U[_j]+_U[(_j+1)%21])/2<262) else ('mc_field' if _side@_toPC>0.3 else 'mc_ebony')
    _parts[k].append(_f)
for k,F in _parts.items():
    if F:add('s_bld_'+k,'facade',_V,F);OBJ[-1]['tex']={'mc_fins':'bronze'}.get(k,k)
# Media Centre roof: dark rim 0.7 m deep, 1.0 m overhang beyond the bronze screen (reference z/ref_bronze.png)
_SB=[W(u,v,14.0)[:2] for u,v in [(205,790),(220,773),(250,760),(300,753),(355,758),(400,775),(450,795),(500,810),(540,826),(560,834),(530,845),(512,858),(500,878),(480,893),(450,890),(400,876),(350,863),(300,853),(250,842),(215,826),(203,808)]]
def _offset(poly,dist):
    Pq=np.array(poly);n=len(Pq);out=[]
    sg=np.sign(sum(Pq[i,0]*Pq[(i+1)%n,1]-Pq[(i+1)%n,0]*Pq[i,1] for i in range(n)))
    for i in range(n):
        a_,b_,c_=Pq[i-1],Pq[i],Pq[(i+1)%n]
        n1=np.array([(b_-a_)[1],-(b_-a_)[0]])/np.linalg.norm(b_-a_);n2=np.array([(c_-b_)[1],-(c_-b_)[0]])/np.linalg.norm(c_-b_)
        m=(n1+n2);m/=np.linalg.norm(m);out.append(tuple(b_+sg*m*dist/max(0.5,float(m@n1))))
    return out
_SO=_offset(_SB,1.0)
prism('s_rim','dark',_SO,13.3,14.0,top=False)
add('s_roof_over','white',[(x,y,14.02) for x,y in _SO],[list(range(len(_SO)))])
# curved white canopy over the top-floor balcony on the south-east face (photo x 400-515)
_cp=[_SB[i] for i in (16,15,14,13,12,11)]
_co=_offset(_SB,2.6);_cq=[_co[i] for i in (16,15,14,13,12,11)]
add('s_canopy','white',[(x,y,11.4) for x,y in _cp]+[(x,y,11.0) for x,y in _cq],[[i,i+1,6+i+1,6+i] for i in range(5)])
photoprism('s_low','facade',[(300,866),(400,880),(470,893),(480,897),(470,905),(400,898),(330,890)],9.0,roofmat='white')
[o for o in OBJ if o['name']=='s_low'][0]['tex']='mc_ebony'
photoprism('s_tip','glass',[(515,822),(565,835),(545,848),(518,840)],13.5,z0=10.0)
# ---- south pavilion (grey roof, photo-traced at z 7) and low teal terrace along the south fence
# pavilion: walls to the eave at z 7 (two storeys, verandah on the upper floor), grey hipped roof rising 2.2 m to a ridge on the long axis
_pp=[W(u,v,7.0)[:2] for u,v in [(530,925),(620,930),(705,940),(755,945),(750,975),(700,985),(600,975),(530,960)]]
prism('p_pav','white',_pp,0.0,7.0,top=False);OBJ[-1]['tex']='pav_wall'
_P=np.array(_pp);_c=_P.mean(0);_ev,_evec=np.linalg.eigh(np.cov((_P-_c).T));_ax=_evec[:,1]
_pr=(_P-_c)@_ax;_pw=np.abs((_P-_c)@_evec[:,0]).max();_r0,_r1=_pr.min()+_pw,_pr.max()-_pw
_top=[tuple(_c+_ax*min(max(t,_r0),_r1))+(9.2,) for t in _pr]
_V=[(x,y,7.0) for x,y in _pp]+_top;_n=len(_pp)
add('p_pav_roof','pavroof',_V,[[i,(i+1)%_n,_n+(i+1)%_n,_n+i] for i in range(_n)])
# ---- south "manuka oval" building and SE white buildings: faces measured with vertical edges, tops run back to the fence
def facade(name,uvb,h,fmat,tmat,deck):
    """facade traced at its photo base line (vertical edges measured), with a roof deck `deck` m deep toward the pitch"""
    G0=[W(u,v,0) for u,v in uvb];V=[];F=[];T=[];TF=[]
    for g in G0:
        V+=[g,(g[0],g[1],h)];a=ang(g);T+=[(g[0],g[1],h),(g[0]-deck*math.cos(a),g[1]-deck*math.sin(a),h)]
    for i in range(len(G0)-1):A=2*i;F.append([A,A+2,A+3,A+1]);TF.append([A,A+2,A+3,A+1])
    L=np.concatenate([[0],np.cumsum([math.dist(G0[i][:2],G0[i+1][:2]) for i in range(len(G0)-1)])]);UV=[]
    for s_ in L:UV+=[(s_/L[-1],0.0),(s_/L[-1],1.0)]
    add(name,fmat,V,F,uv=UV);OBJ[-1]['tex']=name;add(name+'_top',tmat,T,TF)
    poly=[g[:2] for g in G0];th=sorted(math.degrees(ang(g))%360 for g in G0)
    fd=lambda a:hits(poly,a)[0]-edge(a)
    return th[0]+0.3,th[-1]-0.3,fd
# south "manuka oval" building: 7.5 m facade, 1.5 m walkway deck, seats raked from the fence up to the deck (photo seat back line)
s0,s1,sfd=facade('sign_bld',[(840,1045),(900,1045),(1000,1045),(1100,1043)],7.5,'white','conc',1.5)
band('sign_seats','teal',s0,s1,lambda a:[(0.3,1.1),(0.3+0.82*(sfd(a)-1.8),1.1+0.82*6.4)],step=0.5)
band('sign_seats_top','red',s0,s1,lambda a:[(0.3+0.82*(sfd(a)-1.8),1.1+0.82*6.4),(sfd(a)-1.5,7.5)],step=0.5)   # top rows red (reference)
# SE building: grass strip, kerb + walkway, red seats raked up to a 2 m deck on a 5 m white facade (pixel readings z/zg_se.png)
e0,e1,efd=facade('se_bld',[(1125,1000),(1200,975),(1300,950),(1400,915),(1450,905),(1500,885)],5.0,'white','conc',2.0)
band('se_grass','turf',e0,e1,lambda a:[(0.3,0.03),(3.0,0.03)],step=0.5)
band('se_walk','pave',e0,e1,lambda a:[(3.0,0.03),(3.0,0.3),(6.0,0.3)],step=0.5)
band('se_seats','red',e0,e1,lambda a:[(6.0,0.3),(efd(a)-2.0,5.0)],step=0.5)
# pavilion front seats (low teal terrace) up to the sign building, and the short gap between the two south buildings
band('p_seats','teal',270,s0,lambda a:[(0.3,1.1),(1.5,0.6),(9.0,1.6)])
band('g_seats','teal',s1,e0,lambda a:[(0.3,1.1),(1.5,0.6),(9.0,1.6)],step=0.5)
# ---- east grass hill
band('hill','hill',-12,40,lambda a:[(0.3,1.1),(4,1.5),(7,1.2),(9,0.05)])   # narrow bank to the forecourt (reference z/tg_e.png)
# scoreboard (Jack Fingleton), OSM footprint, 9 m
prism('scoreboard','white',G['1290130248'],0,9.0)
# ---- six light towers: tapered, leaning inward by AL, fan head above the neck at HN
def tower(k):
    b=MASTS[k];inw=(PC-b)/np.linalg.norm(PC-b);ax=np.array([inw[0]*math.sin(AL),inw[1]*math.sin(AL),math.cos(AL)])
    side=np.array([-inw[1],inw[0],0.0]);fwd=np.cross(side,ax);base=np.array([b[0],b[1],0.0])
    V=[];F=[];N=12
    for h,r in [(0,0.65),(HN,0.35)]:
        c=base+ax*h
        for i in range(N):t=2*math.pi*i/N;V.append(c+r*(math.cos(t)*side+math.sin(t)*fwd))
    for i in range(N):F.append([i,(i+1)%N,N+(i+1)%N,N+i])
    add(f'tower{k}_pole','tower',V,F)
    # head (measured on g_m6): fan frame 0.6 m wide at the neck to 8.4 m at the top, 16 m long, top tilted 15 deg toward the pitch
    tl=math.radians(15);up=ax*math.cos(tl)+fwd*math.sin(tl);nrm=-ax*math.sin(tl)+fwd*math.cos(tl)
    n=base+ax*HN;top=n+up*16.0
    V=[n-side*0.3,n+side*0.3,top+side*4.2,top-side*4.2];V=[np.array(v) for v in V]
    V+= [v-nrm*0.8 for v in V];add(f'tower{k}_head','tower',V,uv=[(0.46,0),(0.54,0),(1,1),(0,1)]*2,F=[[0,1,2,3],[7,6,5,4],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]]);OBJ[-1]['tex']='lamps'
# north roof A-frame struts: apex x read off the photo strip (955..1535), angles matched on the projected ring, apex 3 m above the roof
def beam(name,mat,p0,p1,w=0.25):
    p0=np.array(p0,float);p1=np.array(p1,float);d=p1-p0;d/=np.linalg.norm(d)
    a=np.cross(d,[0,0,1.0]);a=a/np.linalg.norm(a) if np.linalg.norm(a)>1e-6 else np.array([1.0,0,0]);b=np.cross(d,a)
    V=[p+w/2*(sx*a+sy*b) for p in (p0,p1) for sx,sy in ((-1,-1),(1,-1),(1,1),(-1,1))]
    add(name,mat,V,[[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]])
for i,t in enumerate([127.75,118.75,109.5,100.25,91.5,81.5,70.25]):
    a=math.radians(t);r=NL['rb']-3;dt=math.radians(1.2)
    ap=P(a,r,NL['rbz']+3)
    beam(f'strut{i}_l','white',P(a-dt,r,NL['rbz']-0.3),ap);beam(f'strut{i}_r','white',P(a+dt,r,NL['rbz']-0.3),ap)
    beam(f'strut{i}_tie','white',ap,P(a,NL['rf']+0.5,NL['rfz']+0.1),0.15)
# camera gantry on stilts behind the north stand's east end (photo 1437-1547, 315-362; back-projected theta 78-88, d 30-33, z 11-14)
band('gantry','glass',78,88,lambda a:[(30,11),(30,14)])                 # dark glazed front (reference)
band('gantry_roof','white',78,88,lambda a:[(29.8,14),(33,14)])
band('gantry_back','tower',78,88,lambda a:[(33,14),(33,11),(30,11)])
for i,a in enumerate([79,83,87]):
    for d in (30.3,32.7):
        q=P(math.radians(a),d,0);box(f'gantry_leg{i}_{int(d)}','tower',q,0.35,0.35,11.0)
for k in range(6):tower(k)
# ---- west gate A-frames (J26-05, s 0.01217 m/px): apex px read off the reference at z 10, frames splay along the stand,
# legs 0.25 m on 0.4 x 0.8 m plinths, half-span 1.80 m at the foot, centre post 0.15 m, crossbar z 6.74, lamp box z 7.4,
# Corroboree banner trapezoid z 1.168-6.29 (3.139 m bottom, 1.204 m top) on the outer face, ties to the canopy at z 9.6
GATES=[((204,612),[(261,624),(249,636)]),((171,664),[(229,670),(223,684)]),((157,718),[(215,721),(212,734)]),((173,771),[(220,772)])]
for k,(apx,ties) in enumerate(GATES):
    A=np.array(W(*apx,10.0));rad=A[:2]-PC;rad/=np.linalg.norm(rad);t=np.array([-rad[1],rad[0]]);o3=np.array([rad[0],rad[1],0.0]);t3=np.array([t[0],t[1],0.0])
    base=np.array([A[0],A[1],0.0]);ap=base+[0,0,9.85]
    for sgn in (-1,1):
        ft=base+t3*1.80*sgn;box(f'gate{k}_plinth','conc',ft,0.4,0.4,0.8,rot=math.atan2(t[1],t[0]))
        beam(f'gate{k}_leg','white',ft+[0,0,0.8],ap)
    beam(f'gate{k}_post','white',base,ap,0.15)
    hw=1.80*(10-6.74)/9.2;beam(f'gate{k}_bar','white',base+[0,0,6.74]-t3*hw,base+[0,0,6.74]+t3*hw,0.15)
    box(f'gate{k}_lamp','dark',base,0.35,0.35,0.5,rot=math.atan2(t[1],t[0]),z0=7.15)
    box(f'gate{k}_cap','white',base,0.4,0.4,0.3,rot=math.atan2(t[1],t[0]),z0=9.7)
    bw,tw,z0,z1=3.139,1.204,1.168,6.29;c=base+o3*0.2
    V=[c-t3*bw/2+[0,0,z0],c+t3*bw/2+[0,0,z0],c+t3*tw/2+[0,0,z1],c-t3*tw/2+[0,0,z1]]
    # seen from outside (looking back toward the pitch) the viewer's right is +t, so u runs along +t
    UV=[((x+bw/2)/bw,(zz-z0)/(z1-z0)) for x,zz in [(-bw/2,z0),(bw/2,z0),(tw/2,z1),(-tw/2,z1)]]
    add(f'gate{k}_banner','banner',V,[[0,1,2,3]],uv=UV)
    for j,tp in enumerate(ties):beam(f'gate{k}_tie{j}','white',ap,W(*tp,9.6),0.12)
# ---- trees placed by eye on the gridded reference (trees_eye.py); crown tint = nearest of three read off the photo
from trees_eye import T as _T
from PIL import Image as _Im
_ph=np.array(_Im.open('photo.png').convert('RGB'),float)
_TINT={'leaf_bright':(130,170,50),'leaf_pale':(170,165,130),'leaf_dark':(60,80,50)}
for _k in list(_TINT)+['bark','asphalt','gravel','stairs','canopy','navy','lamps']:MATS.setdefault(_k,(128,128,128))
MATS.setdefault('lawn',(92,112,54))
def _mpp(X):
    a_=cam.proj([X])[0];b_=cam.proj([(X[0]+1,X[1],X[2])])[0];c_=cam.proj([(X[0],X[1]+1,X[2])])[0]
    return 1.0/max(np.linalg.norm(b_-a_),np.linalg.norm(c_-a_))   # horizontal metres per px (crown width is not foreshortened)
import cam
_rng=np.random.default_rng(3)
for i,(u,v,r) in enumerate(_T):
    cz=9.0
    for _ in range(3):
        X=cam.at_z(u,v,cz);rc=r*_mpp(X);cz=2.5+0.8*rc
    yy,xx=np.ogrid[:_ph.shape[0],:_ph.shape[1]];m=(xx-u)**2+(yy-v)**2<(r*0.5)**2;col=_ph[m].mean(0)
    tint=min(_TINT,key=lambda k:np.sum((np.array(_TINT[k])-col)**2))
    V=[];F=[];NA,NB=14,8
    cone=(tint=='leaf_pale') or (tint=='leaf_dark' and r<25)
    if cone:
        # cedar / cypress (reference): stacked drooping cones, widest low, tip high
        Ht=2.6*rc if tint=='leaf_pale' else 4.0*rc;z0=1.5;cz=z0+0.45*Ht;X=cam.at_z(u,v,cz)
        for t_ in range(4):
            zb=z0+Ht*t_*0.22;zt=zb+Ht*0.42;Rb=rc*(1.0-0.2*t_);b0=len(V)
            for k in range(NA):
                th=2*math.pi*k/NA;rr=Rb*(0.85+0.3*_rng.random())
                V.append((X[0]+rr*math.cos(th),X[1]+rr*math.sin(th),zb+0.4*_rng.random()))
            V.append((X[0],X[1],zt));tip=len(V)-1
            for k in range(NA):F.append([b0+k,b0+(k+1)%NA,tip])
            F.append(list(range(b0+NA-1,b0-1,-1)))
    else:
      lobes=[(0,0,0,0.7)]+[(0.38*math.cos(t),0.38*math.sin(t),0.1+0.2*_rng.random(),0.45+0.12*_rng.random()) for t in np.linspace(0,2*math.pi,7)[:-1]+_rng.random()]
      for ox,oy,oz,sc_ in lobes:
        b0=len(V);R_=rc*sc_
        for j in range(NB+1):
            ph_=math.pi*j/NB
            for k in range(NA):
                th=2*math.pi*k/NA;rr=R_*(0.92+0.16*_rng.random()) if 0<j<NB else R_
                V.append((X[0]+ox*rc+rr*math.sin(ph_)*math.cos(th),X[1]+oy*rc+rr*math.sin(ph_)*math.sin(th),cz+oz*rc+0.75*R_*math.cos(ph_)))
        for j in range(NB):
            for k in range(NA):F.append([b0+j*NA+k,b0+j*NA+(k+1)%NA,b0+(j+1)*NA+(k+1)%NA,b0+(j+1)*NA+k])
    add(f'tree{i}_crown',tint,V,F);OBJ[-1]['smooth']=True
    box(f'tree{i}_trunk','bark',X[:2],0.5,0.5,cz)
# site lawn grows outward only where a photo tree stands past the 62 m disc (smooth +-12 deg bulge); roads still clip to sv
# director 2026-11-18 "just get the stadium model done not extra stuff": no trees, roads or background; the lawn ends
# 4 m past the outermost stadium part at each bearing (gates, buildings, light towers)
OBJ[:]=[o for o in OBJ if not o['name'].startswith('tree')]
_B=np.arange(0,360,1.5);_rm=np.zeros(len(_B))
for _o in OBJ:
    if _o['name']=='site':continue
    for _x,_y,_z in _o['v']:
        _a=math.degrees(math.atan2(_y-PC[1],_x-PC[0]))%360;_k=int(_a/1.5)%len(_B)
        _rm[_k]=max(_rm[_k],math.hypot(_x-PC[0],_y-PC[1]))
_rs=np.array([max(_rm[(k+j)%len(_B)] for j in range(-4,5)) for k in range(len(_B))])
_rs=np.array([max(_rs[k],np.mean([_rs[(k+j)%len(_B)] for j in range(-10,11)])) for k in range(len(_B))])
_rs=np.array([np.mean([_rs[(k+j)%len(_B)] for j in range(-5,6)]) for k in range(len(_B))])+2.0
def _dd(a):return float(np.interp(math.degrees(a)%360,_B,_rs,period=360))+4.0-edge(a)
_sv2=[P(math.radians(t),_dd(math.radians(t)),-0.05) for t in np.arange(0,360,1.5)]
# secretary 2026-11-18 (director "Send all 3"): no field floor, the game draws the grass inside the fence -> lawn is a ring
_in=[P(math.radians(t),0,-0.05) for t in np.arange(0,360,1.5)];_n=len(_in)
for _o in OBJ:
    if _o['name']=='site':_o['v']=np.round(np.array(_in+_sv2,float),3).tolist();_o['f']=[[k,(k+1)%_n,_n+(k+1)%_n,_n+k] for k in range(_n)]
def _clip(poly,clipper):
    """Sutherland-Hodgman: clip poly to the convex site disc"""
    C=np.array(clipper);sg=np.sign(sum(C[i,0]*C[(i+1)%len(C),1]-C[(i+1)%len(C),0]*C[i,1] for i in range(len(C))))
    out=[np.array(p) for p in poly]
    for i in range(len(C)):
        A,B=C[i],C[(i+1)%len(C)];inside=lambda p:sg*((B[0]-A[0])*(p[1]-A[1])-(B[1]-A[1])*(p[0]-A[0]))>=0
        src=out;out=[]
        for j in range(len(src)):
            P_,Q_=src[j-1],src[j]
            def X_(P_,Q_):
                d1=sg*((B[0]-A[0])*(P_[1]-A[1])-(B[1]-A[1])*(P_[0]-A[0]));d2=sg*((B[0]-A[0])*(Q_[1]-A[1])-(B[1]-A[1])*(Q_[0]-A[0]))
                return P_+(Q_-P_)*d1/(d1-d2)
            if inside(Q_):
                if not inside(P_):out.append(X_(P_,Q_))
                out.append(Q_)
            elif inside(P_):out.append(X_(P_,Q_))
        if not out:break
    return [tuple(p) for p in out]
# Jack Fingleton video screen: dark panel z 8-18 on two legs, facing the pitch (photo 1690-1720, 520-640; base back-projected)
_sb=np.array(W(1705,650,0));_in=(np.array(PC)-_sb[:2]);_in/=np.linalg.norm(_in);_rot=math.atan2(_in[1],_in[0])
box('screen','dark',_sb[:2],1.0,12.0,10.0,rot=_rot,z0=8.0)
for _o in (-4.5,4.5):box('screen_leg','dark',(_sb[0]-_in[1]*_o,_sb[1]+_in[0]*_o),0.6,0.6,8.0)
# roads and service yards (asphalt), traced at ground level on z/tg_*.png
for _k,_uv in enumerate([[(0,975),(280,1115),(680,1280),(330,1280),(0,1120)],
    [(95,750),(175,750),(175,860),(250,950),(220,965),(95,850)],
    [(100,560),(330,560),(330,780),(100,780)],
    [(1640,560),(1790,560),(1890,640),(1900,1000),(1780,1000),(1690,860),(1730,760),(1640,700)]]):
    _q=_clip([W(u,v,0)[:2] for u,v in _uv],[tuple(p[:2]) for p in sv])
    if len(_q)<3:continue
    add(f'road{_k}','asphalt',[(x,y,0.01) for x,y in _q],[list(range(len(_q)))])
# east forecourt (red-brown gravel), traced at ground level on z/tg_e.png
_fc=[W(u,v,0)[:2] for u,v in [(1600,700),(1720,700),(1720,800),(1640,860),(1560,860),(1540,800)]]
add('forecourt','gravel',[(x,y,0.0) for x,y in _fc],[list(range(len(_fc)))])
OBJ[:]=[o for o in OBJ if not o['name'].startswith('road') and o['name']!='turf']
json.dump({'mats':MATS,'objs':OBJ},open('model.json','w'))
print(len(OBJ),'objects')
