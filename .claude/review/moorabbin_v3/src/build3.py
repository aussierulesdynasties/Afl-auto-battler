import bpy,bmesh,json,math,sys,os
import numpy as np
from mathutils import Vector,Matrix
D=os.path.dirname(os.path.abspath(__file__))
O=json.load(open(os.path.join(D,'build.json')))
argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT=argv[0] if argv else os.path.join(D,'moorabbin.glb')
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
def lin(c):return [x**2.2 for x in c[:3]]+[1]
MATS={};FLAT={}
def mat(n,c,rough=0.85,vc=True):
    FLAT[n]=list(c[:3])
    if n in MATS:return MATS[n]
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=lin(c) if not vc else (1,1,1,1);b.inputs['Roughness'].default_value=rough
    if vc:
        a=m.node_tree.nodes.new('ShaderNodeVertexColor');a.layer_name='Col';m.node_tree.links.new(a.outputs['Color'],b.inputs['Base Color'])
    MATS[n]=m;return m
def obj(name,bm,m):
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);sc.collection.objects.link(o)
    for mm in (m if isinstance(m,list) else [m]):me.materials.append(mm)
    return o
def quad(bm,a,b,c,d,mi=0):
    f=bm.faces.new([bm.verts.new(v) for v in (a,b,c,d)]);f.material_index=mi;return f
def prism(bm,poly,z0,z1,mi=0,top=True,mi_w=None):
    n=len(poly);B=[bm.verts.new((x,y,z0)) for x,y in poly];T=[bm.verts.new((x,y,z1)) for x,y in poly]
    for i in range(n):
        j=(i+1)%n;f=bm.faces.new([B[i],B[j],T[j],T[i]]);f.material_index=mi if mi_w is None else mi_w
    if top:
        f=bm.faces.new(T);f.material_index=mi
    return T
def ccw(poly):
    poly=[tuple(q) for q in poly]
    a=sum(poly[i][0]*poly[(i+1)%len(poly)][1]-poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly)))
    return poly if a>0 else poly[::-1]
C=O['colors']
P=np.array(O['pitch'])
if np.allclose(P[0],P[-1]):P=P[:-1]
PC=P.mean(0)
ang=np.arctan2(P[:,1]-PC[1],P[:,0]-PC[0]);rad=np.hypot(P[:,0]-PC[0],P[:,1]-PC[1]);o_=np.argsort(ang)
def rp(a):return np.interp(a,ang[o_],rad[o_],period=2*math.pi)
def polar(xy):
    xy=np.array(xy);a=np.arctan2(xy[:,1]-PC[1],xy[:,0]-PC[0]);return a,np.hypot(xy[:,0]-PC[0],xy[:,1]-PC[1])-rp(a)
def pt(a,d,z=0):
    r=rp(a)+d;return (PC[0]+r*math.cos(a),PC[1]+r*math.sin(a),z)
# ---- no playing field: the game draws its own grass inside the fence (director 2026-11-18: 'Leave field out')
# ---- stand angular range (angles unwrapped, stand runs north -> south)
sf=np.array(O['stand']['front']);sr=np.array(O['stand']['rear'])
fa,fd=polar(sf);ra,rd=polar(sr)
fa=np.unwrap(fa);ra=np.unwrap(ra)
lo,hi=min(fa.min(),ra.min()),max(fa.max(),ra.max())
def wrap(a):return np.mod(a-lo,2*math.pi)+lo
def iu(a,A,V):
    o=np.argsort(A);return np.interp(a,A[o],V[o])
ta,td=polar(O['terr_out']);ZT=O['terr_z'];ta=wrap(ta)
def in_stand(a):return wrap(a)<=hi
AA=np.concatenate([ta,fa]);VV=np.concatenate([td,iu(fa,ra,rd)]);oo=np.argsort(AA);AA=AA[oo];VV=VV[oo]
def d_out(a):return float(np.interp(wrap(a),AA,VV,period=2*math.pi))
NA=720;angs=np.linspace(-math.pi,math.pi,NA,endpoint=False)
def zprof(a,d):
    if in_stand(a):
        df=float(iu(wrap(a),fa,fd))
        return 0.15+min(d,df)/max(df,1)*0.85 if d<=df+0.5 else 0.0
    do=d_out(a)
    if d<0.6:return 0.0
    if d<=do:
        return ZT*(d-0.6)/(do-0.6)
    if d<=do+6:return ZT*(1-(d-do)/6)
    return 0.0
_bp=np.array([q for b in O['club'] if b['n']!='redtower' for q in b['pts']],float)  # stadium only: free-standing outbuildings removed (secretary 2026-11-18)
_ba,_bd=polar(_bp);_ba=wrap(_ba)
def dmax(a):
    w=wrap(a);near=np.abs(((_ba-w)+math.pi)%(2*math.pi)-math.pi)<math.radians(4)
    reach=(_bd[near].max()+3) if near.any() else 0
    return max(d_out(a)+(2 if in_stand(a) else 8),reach)
# ---- terraces (1993 panorama: concrete steps from the boundary apron up to a walkway on the crest, chain-wire
#      fence on the crest, grass behind). The banks keep their measured depth round the ground (23-41 m), so each
#      sector's tread differs: 20 risers of 0.15 m spread over that sector's own depth. Stand pocket: 8 low steps.
NRB=20;RB=ZT/NRB;WALK=1.8
def bank_prof(a):
    do=d_out(a);d0=0.6;d1=do-WALK;t=(d1-d0)/NRB
    pts=[(0.3,0,0),(0.6,0,0)]
    for q in range(NRB):pts+=[(d0+q*t,(q+1)*RB,0),(d0+(q+1)*t,(q+1)*RB,0)]
    pts+=[(do,ZT,0),(do+6,0,1),(max(dmax(a),do+6.5),0,1)]
    return pts
NPK=8
def pocket_prof(a):
    df=float(iu(wrap(a),fa,fd));t=(df-0.3)/NPK;r=0.85/NPK
    pts=[(0.3,0,0),(0.3,0.15,0)]
    for q in range(NPK):pts+=[(0.3+q*t,0.15+(q+1)*r,0),(0.3+(q+1)*t,0.15+(q+1)*r,0)]
    pts+=[(df+0.5,-0.02,0),(dmax(a),-0.02,1)]   # 2 cm under the bank's back ground where the two overlap
    return pts
def grid(A,prof,name,a0f=None):
    bm=bmesh.new();uvl=bm.loops.layers.uv.new('UVMap');cols=[prof(a) for a in A]
    V=[[bm.verts.new(pt(a0f(d) if (i==0 and a0f) else A[i],d,z)) for d,z,_ in cols[i]] for i in range(len(A))]
    SC={0:1.4,1:10.0}
    for i in range(len(A)-1):
        for k in range(len(cols[i])-1):
            mi=cols[i][k+1][2];s=SC[mi]
            f=bm.faces.new([V[i][k],V[i][k+1],V[i+1][k+1],V[i+1][k]]);f.material_index=mi
            L=lambda j,kk:sum(math.hypot(cols[j][m+1][0]-cols[j][m][0],cols[j][m+1][1]-cols[j][m][1]) for m in range(kk))
            uvs=[]
            for j,kk in ((i,k),(i,k+1),(i+1,k+1),(i+1,k)):uvs.append((A[j]*(rp(A[j])+cols[j][kk][0])/s,L(j,kk)/s))
            for lp,uv in zip(f.loops,uvs):lp[uvl].uv=uv
    for i,sg in ((0,1),(len(A)-1,-1)):                     # end caps down to the ground
        c=cols[i]
        for k in range(len(c)-1):
            if c[k][1]<=0 and c[k+1][1]<=0:continue
            vv=[V[i][k],V[i][k+1],bm.verts.new(pt(A[i],c[k+1][0],0)),bm.verts.new(pt(A[i],c[k][0],0))]
            f=bm.faces.new(vv if sg<0 else vv[::-1]);f.material_index=0
            for lp in f.loops:co=lp.vert.co;dd=math.hypot(co.x-PC[0],co.y-PC[1]);lp[uvl].uv=(dd/1.4,co.z/1.4)
    bm.normal_update()
    o=obj(name,bm,[mat('apron',(0.6,0.6,0.58),0.9),mat('ground_grass',(0.4,0.6,0.3),0.95)]);o['uv_final']=1;return o
HI=wrap(hi);LO2=lo+2*math.pi
AB=np.linspace(HI,LO2,int((LO2-HI)/math.radians(0.5))+1)
AP=np.linspace(lo,HI,int((HI-lo)/math.radians(0.5))+1)
# south end: the bank's first column follows the long stand's slanted end wall (front corner -> rear corner), so the
# steps, walkway and crest fence run right up to the wall with no wedge between them
RAE=float(ra[np.argmax(wrap(ra))]);RAE=wrap(RAE);RDE=float(rd[np.argmax(wrap(ra))]);DFE=float(fd[np.argmax(fa)])
def south_wall_ang(d):
    if d<=DFE:return HI
    if d<=RDE:return HI+(RAE-HI)*(d-DFE)/(RDE-DFE)
    return RAE
terr=grid(AB,bank_prof,'terrace',south_wall_ang);grid(AP,pocket_prof,'terrace_pocket')
# ---- chain-wire fence on the crest's outer edge (1993 panorama): 1.2 m mesh, posts every 2.5 m, top rail; it stops
#      at the walls of the club buildings that stand in the bank
def inpoly(q,poly):
    x,y=q;c=False;n=len(poly)
    for i in range(n):
        x1,y1=poly[i];x2,y2=poly[(i+1)%n]
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:c=not c
    return c
BLD=[np.array(b['pts'],float)[:,:2] for b in O['club'] if b['n']!='redtower']
CF=1.2;AC=np.linspace(HI,LO2,6000);CR=np.array([pt(RAE,RDE-0.05)[:2]]+[pt(a,d_out(a)-0.05)[:2] for a in AC[1:]]);inside=np.array([any(inpoly(q,p_) for p_ in BLD) for q in CR])
runs=[];cur=[]
for q,ins in zip(CR,inside):
    if ins:
        if len(cur)>1:runs.append(np.array(cur))
        cur=[]
    else:cur.append(q)
if len(cur)>1:runs.append(np.array(cur))
bw=bmesh.new();uvw=bw.loops.layers.uv.new('UVMap');bp_=bmesh.new()
def seg_box(bmx,a_,b_,z0,z1,th,mi=0):
    t_=(b_-a_)/np.linalg.norm(b_-a_);nn=np.array([-t_[1],t_[0]]);prism(bmx,ccw([a_-nn*th/2,b_-nn*th/2,b_+nn*th/2,a_+nn*th/2]),z0,z1,mi,True)
def sq(bmx,c,w,z0,z1,mi=0):prism(bmx,ccw([c+np.array(v) for v in ((-w/2,-w/2),(w/2,-w/2),(w/2,w/2),(-w/2,w/2))]),z0,z1,mi,True)
crest_posts=[]
for r_ in runs:
    s_=np.concatenate([[0],np.cumsum(np.hypot(*np.diff(r_,axis=0).T))]);L_=s_[-1]
    if L_<1.0:continue
    nseg=max(1,int(math.ceil(L_/2.5)));ps=[r_[min(np.searchsorted(s_,L_*k/nseg),len(r_)-1)] for k in range(nseg+1)]
    for k in range(nseg):
        a_,b_=ps[k],ps[k+1];u1=np.linalg.norm(b_-a_)/0.5
        f=bw.faces.new([bw.verts.new((*a_,ZT+0.05)),bw.verts.new((*b_,ZT+0.05)),bw.verts.new((*b_,ZT+CF)),bw.verts.new((*a_,ZT+CF))])
        for lp,uv in zip(f.loops,((0,0.1),(u1,0.1),(u1,CF/0.5),(0,CF/0.5))):lp[uvw].uv=uv
        seg_box(bp_,a_,b_,ZT+CF-0.02,ZT+CF+0.02,0.04)
    for q in ps:sq(bp_,q,0.06,ZT-0.1,ZT+CF+0.03);crest_posts.append(q)
cw=obj('crest_wire',bw,mat('chainwire',(0.6,0.6,0.62),0.5,vc=False));cw['uv_final']=1
obj('crest_posts',bp_,mat('crest_post',(0.6,0.61,0.62),0.5))
print('crest fence runs',len(runs),'posts',len(crest_posts),flush=True)
# ---- bank-top billboards (1993 panorama, camera fitted on the east crest; ends read to about +-3 deg): blank panels,
#      no lettering (ruling). Straight panels of at most 6 m follow the crest, 0.6 m behind the fence.
BB=[]   # bank billboards removed: ads are not modelled (ground rules, 2026-11-19); were [(-71.9,-78.2),(-78.9,-86.7),(-86.7,-98.5),(-98.8,-104.5),(-105.3,'RAE'),(76.4,81.0)]
BZ0,BZ1=ZT+1.8,ZT+3.8
bb=bmesh.new()
def oface(bmx,vs,want,mi):
    vs=[np.array(v,float) for v in vs];n_=np.cross(vs[1]-vs[0],vs[2]-vs[0])
    if n_@np.array(want,float)<0:vs=vs[::-1]
    f=bmx.faces.new([bmx.verts.new(tuple(v)) for v in vs]);f.material_index=mi;return f
for a0,a1 in BB:
    A0=wrap(math.radians(a0));A1=RAE if a1=='RAE' else wrap(math.radians(a1));AA_=np.linspace(min(A0,A1),max(A0,A1),200)
    Q=np.array([pt(a,d_out(a)+0.6)[:2] for a in AA_]);s_=np.concatenate([[0],np.cumsum(np.hypot(*np.diff(Q,axis=0).T))]);L_=s_[-1]
    n_=max(1,int(math.ceil(L_/6)));ps=[Q[min(np.searchsorted(s_,L_*k/n_),len(Q)-1)] for k in range(n_+1)]
    NN=[(PC-q)/np.linalg.norm(PC-q) for q in ps]                      # each joint's inward normal: neighbours share it, so panels meet
    for k in range(n_):
        a_,b_=ps[k],ps[k+1];na,nb=NN[k],NN[k+1];nm=(na+nb)/2
        oface(bb,[(*a_,BZ0),(*b_,BZ0),(*b_,BZ1),(*a_,BZ1)],(*nm,0),0)                       # front, blank white
        oface(bb,[(*(a_-na*0.08),BZ0),(*(b_-nb*0.08),BZ0),(*(b_-nb*0.08),BZ1),(*(a_-na*0.08),BZ1)],(*-nm,0),1)
        oface(bb,[(*a_,BZ1),(*b_,BZ1),(*(b_-nb*0.08),BZ1),(*(a_-na*0.08),BZ1)],(0,0,1),1)
        oface(bb,[(*a_,BZ0),(*b_,BZ0),(*(b_-nb*0.08),BZ0),(*(a_-na*0.08),BZ0)],(0,0,-1),1)
    for k,q in enumerate(ps):
        sq(bb,q-NN[k]*0.14,0.1,ZT*(1-0.80/6)-0.05,BZ1,1)                                       # leg behind every joint
        if k in (0,len(ps)-1):
            t_=(ps[1]-ps[0]) if k==0 else (ps[-1]-ps[-2]);t_/=np.linalg.norm(t_);t_=-t_ if k==0 else t_
            oface(bb,[(*q,BZ0),(*(q-NN[k]*0.08),BZ0),(*(q-NN[k]*0.08),BZ1),(*q,BZ1)],(*t_,0),1)
if BB:
    bbo=obj('billboards',bb,[mat('bb_front',(0.92,0.92,0.9),0.6),mat('bb_back',(0.32,0.33,0.33),0.6)])
    for p_ in bbo.data.polygons:p_.use_smooth=False
# (outside-site ground removed: stadium only, director 2026-11-18)
# ---- boundary fence: separate boards with a joint every BAY m, gates read off the photos
bm=bmesh.new();n=len(P);fv=[]
for i in range(n):
    a=P[i];b=P[(i+1)%n];L=np.hypot(*(b-a));k=max(1,int(L/2))
    for t in np.linspace(0,1,k,endpoint=False):fv.append(a+(b-a)*t)
fv=np.array(fv);dv=fv-PC;fv=fv+0.3*dv/np.linalg.norm(dv,axis=1)[:,None]
RING=np.vstack([fv,fv[:1]]);RS=np.concatenate([[0],np.cumsum(np.hypot(*np.diff(RING,axis=0).T))]);RL=RS[-1]
def ring_at(s):
    s=s%RL;i=min(np.searchsorted(RS,s,side='right')-1,len(RS)-2);t=(s-RS[i])/(RS[i+1]-RS[i]);return RING[i]+(RING[i+1]-RING[i])*t
def ring_s_ang(a):
    A=np.arctan2(fv[:,1]-PC[1],fv[:,0]-PC[0]);k=int(np.argmin(np.abs((A-a+math.pi)%(2*math.pi)-math.pi)));return RS[k]
def ring_s_pt(q):k=int(np.argmin(np.hypot(*(fv-np.array(q)).T)));return RS[k]
def outn(q):d=np.array(q)-PC;return d/np.linalg.norm(d)
BAY=5.9;GAP=0.03;TH=0.06;FH=1.0
# gates: NE pocket = dark 9.0 m break on the aerial (A.jpg px 364..383, angles 0.798..0.695);
#        players' race = 1993 panorama, race box between the long stand's north end and the Huggins, 3.8 m wide
gA,gB=sorted((ring_s_ang(0.798),ring_s_ang(0.695)))
s_race=ring_s_pt(((-68.44-67.1)/2,(60.41+67.6)/2))
GATES=[(gA,gB),(s_race-1.9,s_race+1.9)]
cuts=[]
for g0,g1 in GATES:cuts+=[g0,g1]
# joints run from the NE gate's end, every BAY m, round the ring; a joint closer than 1.5 m to a gate edge is dropped
s=gB+BAY
while s<gB+RL-0.5:
    ss=s%RL
    if all(min(abs(ss-c),RL-abs(ss-c))>1.5 for c in cuts) and not any(g0<ss<g1 for g0,g1 in GATES):cuts.append(ss)
    s+=BAY
cuts=sorted(set(round(c,4) for c in cuts))
def in_gate(a,b):
    m=(a+(b-a if b>a else b+RL-a)/2)%RL;return any(g0<=m<=g1 for g0,g1 in GATES)
uvl=bm.loops.layers.uv.new('UVMap')
def fquad(a,b,c,d,mi,uv):
    f=quad(bm,a,b,c,d,mi)
    for lp,u in zip(f.loops,uv):lp[uvl].uv=u
    return f
posts_s=[]
for i in range(len(cuts)):
    a=cuts[i];b=cuts[(i+1)%len(cuts)];b=b if b>a else b+RL
    if in_gate(a,b%RL if b>RL else b):continue
    posts_s.append(a)
    GE=[g for gg in GATES for g in gg];isg=lambda x:any(abs((x%RL)-g)<1e-3 for g in GE)
    s0=a+(0.05 if isg(a) else GAP/2);s1=b-(0.05 if isg(b) else GAP/2)   # boards beside a gate stop at the gate post's face
    ss=[s0]+[x for x in RS if s0<x<s1]+[x+RL for x in RS if s0<x+RL<s1]+[s1];ss=sorted(ss)
    F=[ring_at(x) for x in ss];Bk=[q+outn(q)*TH for q in F]
    for k in range(len(ss)-1):
        u0=(ss[k]-s0)/6;u1=(ss[k+1]-s0)/6
        fquad((*F[k],0),(*F[k+1],0),(*F[k+1],FH),(*F[k],FH),0,[(u0,0),(u1,0),(u1,1),(u0,1)])          # front
        fquad((*Bk[k],FH),(*Bk[k+1],FH),(*Bk[k+1],0),(*Bk[k],0),0,[(u0,1),(u1,1),(u1,0),(u0,0)])      # back
        fquad((*F[k],FH),(*F[k+1],FH),(*Bk[k+1],FH),(*Bk[k],FH),0,[(u0,0),(u1,0),(u1,0.06),(u0,0.06)]) # top cap
    for q,bq,sg in ((F[0],Bk[0],1),(F[-1],Bk[-1],-1)):                                                # board ends
        e=[(*q,0),(*bq,0),(*bq,FH),(*q,FH)]
        if sg<0:e=e[::-1]
        fquad(*e,0,[(0,0),(0.01,0),(0.01,1),(0,1)])
fence=obj('fence',bm,mat('fence_white',(0.93,0.93,0.91),0.6))
fence['uv_final']=1
# joint posts: 80 mm square steel post behind every joint, to the board top
bm=bmesh.new()
def boxp(c,t_,nn,w,d,z0,z1,mi=0):
    q=[c-t_*w/2,c+t_*w/2,c+t_*w/2+nn*d,c-t_*w/2+nn*d];prism(bm,ccw(q),z0,z1,mi,True)
for c_ in cuts:
    if any(abs(c_-g)<1e-3 for gg in GATES for g in gg):continue
    q=ring_at(c_);t_=ring_at(c_+0.05)-ring_at(c_-0.05);t_/=np.linalg.norm(t_);boxp(q+outn(q)*TH,t_,outn(q),0.08,0.08,0,FH)
# gates: tube frame + vertical bars (no photo pixels), dark steel; hinge posts 100 mm, leaves meet in the middle
for g0,g1 in GATES:
    for sg in (g0,g1):
        q=ring_at(sg);t_=ring_at(sg+0.05)-ring_at(sg-0.05);t_/=np.linalg.norm(t_);boxp(q-outn(q)*0.02,t_,outn(q),0.10,0.10,0,FH,1)
    W_g=g1-g0;mid=(g0+g1)/2
    for l0,l1 in ((g0+0.07,mid-0.01),(mid+0.01,g1-0.07)):
        n_=max(2,int((l1-l0)/0.12))
        for k in range(n_+1):                       # vertical bars incl. the two stiles
            sb=l0+(l1-l0)*k/n_;q=ring_at(sb);t_=ring_at(sb+0.05)-ring_at(sb-0.05);t_/=np.linalg.norm(t_)
            w=0.05 if k in (0,n_) else 0.022;boxp(q+outn(q)*0.01,t_,outn(q),w,w,0.05,FH,1)
        for z0 in (0.05,FH-0.025):                   # bottom and top rails, segmented along the curve
            m_=max(1,int((l1-l0)/1.0))
            for k in range(m_):
                sa=l0+(l1-l0)*k/m_;sb=l0+(l1-l0)*(k+1)/m_;qa=ring_at(sa);qb=ring_at(sb);t_=(qb-qa)/np.linalg.norm(qb-qa)
                c=(qa+qb)/2;L_=np.linalg.norm(qb-qa)+0.002;boxp(c+outn(c)*0.01,t_,outn(c),L_,0.05,z0-0.025,z0+0.025,1)
obj('fence_posts_gates',bm,[mat('fence_post',(0.3,0.31,0.31),0.5),mat('gate_steel',(0.24,0.27,0.26),0.5)])
json.dump({'gates':[[ring_at(a).tolist(),ring_at(b).tolist(),outn(ring_at((a+b)/2)).tolist()] for a,b in GATES],'joints':[[ring_at(c).tolist(),outn(ring_at(c)).tolist()] for c in cuts]},open(os.path.join(D,'fencepts.json'),'w'))
print('fence: boards',len(posts_s),'joints',len(cuts),'gates',[(round(a,1),round(b,1),round(b-a,2)) for a,b in GATES],'ring',round(RL,1),flush=True)
# ---- grandstand: real section read off the photos
def resample(L,N):
    L=np.array(L);s=np.concatenate([[0],np.cumsum(np.hypot(*np.diff(L,axis=0).T))]);t=np.linspace(0,s[-1],N)
    return np.stack([np.interp(t,s,L[:,0]),np.interp(t,s,L[:,1])],1),s[-1]
H=O['stand']['h'];HB=O['stand']['hb']
_,Lr=resample(sr,2);NS=int(round(Lr/1.4));RR,Lr=resample(sr,NS+1)
FF=[]
for x,y in RR:
    a=wrap(math.atan2(y-PC[1],x-PC[0]));a=min(max(a,fa.min()),fa.max())
    FF.append(pt(a,float(iu(a,fa,fd)))[:2])
FF=np.array(FF);SL=np.concatenate([[0],np.cumsum(np.hypot(*np.diff(RR,axis=0).T))])
NROWS=14;S_FW=1.5;Z_FW=3.5;Z_TOP=8.0;Z_UND=9.9;Z_UNDR=10.2;FASC=0.6;BAY=5.6;AISLE=1.2;AISLE_EVERY=2
def P_(i,s,z):
    f=FF[i];r=RR[i];D_=np.linalg.norm(r-f);return (*(f+(r-f)*min(s,D_)/D_),z)
def depth(i):return float(np.linalg.norm(RR[i]-FF[i]))
def in_aisle(l):
    k=l/(BAY*AISLE_EVERY);return abs(k-round(k))*BAY*AISLE_EVERY<AISLE/2 and 0<l<Lr
bm=bmesh.new();uvq=[]
def Q(a,b,c,d,mi,uv):
    f=quad(bm,a,b,c,d,mi);uvq.append((f,uv))
for i in range(len(RR)-1):
    j=i+1;l0,l1=SL[i],SL[j];D0,D1=depth(i),depth(j)
    rk0,rk1=D0-3,D1-3
    # roof top, underside, fascia
    Q(P_(i,0,H),P_(i,D0,H),P_(j,D1,H),P_(j,0,H),0,[(l0,0),(l0,D0),(l1,D1),(l1,0)])
    Q(P_(i,0,Z_UND),P_(j,0,Z_UND),P_(j,D1,Z_UNDR),P_(i,D0,Z_UNDR),5,[(l0,0),(l1,0),(l1,D1),(l0,D0)])
    Q(P_(j,0,Z_UND),P_(i,0,Z_UND),P_(i,0,H),P_(j,0,H),5,[(l1,Z_UND),(l0,Z_UND),(l0,H),(l1,H)])
    # rear wall (outside face) and its white band
    Q(P_(i,D0,0),P_(j,D1,0),P_(j,D1,7.3),P_(i,D0,7.3),3,[(l0,0),(l1,0),(l1,7.3),(l0,7.3)])
    Q(P_(i,D0,7.3),P_(j,D1,7.3),P_(j,D1,H),P_(i,D0,H),2,[(l0,7.3),(l1,7.3),(l1,H),(l0,H)])
    # rear rooms front wall and concourse floor
    Q(P_(j,D1-1.5,Z_TOP),P_(i,D0-1.5,Z_TOP),P_(i,D0-1.5,Z_UNDR),P_(j,D1-1.5,Z_UNDR),6,[(l1,0),(l0,0),(l0,Z_UNDR-Z_TOP),(l1,Z_UNDR-Z_TOP)])
    Q(P_(i,rk0,Z_TOP),P_(j,rk1,Z_TOP),P_(j,D1-1.5,Z_TOP),P_(i,D0-1.5,Z_TOP),7,[(l0,0),(l1,0),(l1,1.5),(l0,1.5)])
    # front wall
    Q(P_(j,S_FW,0),P_(i,S_FW,0),P_(i,S_FW,Z_FW-0.7),P_(j,S_FW,Z_FW-0.7),9,[(l1,0),(l0,0),(l0,Z_FW-0.7),(l1,Z_FW-0.7)])
    Q(P_(j,S_FW,Z_FW-0.7),P_(i,S_FW,Z_FW-0.7),P_(i,S_FW,Z_FW),P_(j,S_FW,Z_FW),8,[(l1,0),(l0,0),(l0,.7),(l1,.7)])
    Q(P_(i,S_FW,Z_FW),P_(j,S_FW,Z_FW),P_(j,S_FW+0.3,Z_FW),P_(i,S_FW+0.3,Z_FW),8,[(l0,0),(l1,0),(l1,.3),(l0,.3)])
    # stepped rows
    lm=(l0+l1)/2;ais=in_aisle(lm)
    for k in range(NROWS):
        s0a=S_FW+(rk0-S_FW)*k/NROWS;s1a=S_FW+(rk0-S_FW)*(k+1)/NROWS
        s0b=S_FW+(rk1-S_FW)*k/NROWS;s1b=S_FW+(rk1-S_FW)*(k+1)/NROWS
        z=Z_FW+(Z_TOP-Z_FW)*(k+1)/NROWS;zp=Z_FW+(Z_TOP-Z_FW)*k/NROWS
        Q(P_(j,s0b,zp),P_(i,s0a,zp),P_(i,s0a,z),P_(j,s0b,z),7,[(l1,0),(l0,0),(l0,z-zp),(l1,z-zp)])
        Q(P_(i,s0a,z),P_(j,s0b,z),P_(j,s1b,z),P_(i,s1a,z),7,[(l0,0),(l1,0),(l1,s1b-s0b),(l0,s1a-s0a)])
        if ais:
            zm=(z+zp)/2;sma=(s0a+s1a)/2;smb=(s0b+s1b)/2  # aisle half step
            Q(P_(j,sma,z),P_(i,sma,z),P_(i,sma,z+(z-zp)/2),P_(j,smb,z+(z-zp)/2),7,[(l1,0),(l0,0),(l0,.2),(l1,.2)])
            Q(P_(i,sma,z+(z-zp)/2),P_(j,smb,z+(z-zp)/2),P_(j,s1b,z+(z-zp)/2),P_(i,s1a,z+(z-zp)/2),7,[(l0,0),(l1,0),(l1,.4),(l0,.4)])
        else:
            # bench: seat slab and back
            sa=s0a+0.15;sb=s0b+0.15;za=z+0.42
            Q(P_(i,sa,za),P_(j,sb,za),P_(j,sb+0.38,za),P_(i,sa+0.38,za),4,[(l0,0),(l1,0),(l1,.38),(l0,.38)])
            Q(P_(j,sb,za-0.05),P_(i,sa,za-0.05),P_(i,sa,za),P_(j,sb,za),4,[(l1,0),(l0,0),(l0,.05),(l1,.05)])
            Q(P_(j,sb+0.42,za+0.05),P_(i,sa+0.42,za+0.05),P_(i,sa+0.48,za+0.45),P_(j,sb+0.48,za+0.45),4,[(l1,0),(l0,0),(l0,.4),(l1,.4)])
# roof ribs every bay, tapering 0.9 m at the rear to 0.3 m at the front
nr=int(Lr/BAY)
for k in range(nr+1):
    i=int(np.argmin(np.abs(SL-k*Lr/nr)));f=FF[i];r=RR[i];d_=(r-f)/np.linalg.norm(r-f);nv=np.array([-d_[1],d_[0]])*0.15;D_=depth(i)
    if k in (0,nr):   # end ribs sit inside the end walls, not 0.15 m past them
        ia,ib=(0,1) if k==0 else (-1,-2);tf=FF[ib]-FF[ia];tf/=np.linalg.norm(tf);tr=RR[ib]-RR[ia];tr/=np.linalg.norm(tr);f=f+tf*0.15;r=r+tr*0.15
    for a,b in ((f-nv,r-nv),(r+nv,f+nv)):
        hb_=0.9 if a is not None else 0
        Q((*a,H),(*b,H),(*b,H+(0.9 if np.allclose(b,r-nv) or np.allclose(b,r+nv) else 0.3)),(*a,H+(0.3 if np.allclose(a,f-nv) or np.allclose(a,f+nv) else 0.9)),1,[(0,0),(D_,0),(D_,.9),(0,.3)])
    Q((*(f-nv),H+0.3),(*(r-nv),H+0.9),(*(r+nv),H+0.9),(*(f+nv),H+0.3),1,[(0,0),(D_,0),(D_,.3),(0,.3)])
# end walls
for i in (0,len(RR)-1):
    D_=depth(i);Q(P_(i,0,0),P_(i,D_,0),P_(i,D_,H),P_(i,0,H),3,[(0,0),(D_,0),(D_,H),(0,H)])
uvl=bm.loops.layers.uv.new('UVMap')
for f,uv in uvq:
    for lp,(u,v) in zip(f.loops,uv):lp[uvl].uv=(u,v)
stand=obj('grandstand',bm,[mat('roof',C['roof'],0.5),mat('rib',C['rib'],0.6),mat('band',C['band'],0.5),mat('standback',C['back'],0.9),mat('benches',(0.18,0.36,0.30),0.8),mat('roof_under',(0.08,0.08,0.09),0.9),mat('rear_rooms',(0.12,0.13,0.16),0.6),mat('concrete',(0.62,0.61,0.58),0.9),mat('frontwall',(0.85,0.85,0.83),0.8),mat('undercroft',(0.45,0.46,0.46),0.9)])
# ---- club complex
for b in O['club']:
    if b['n'] in ('darkroof','greyroof','redtower'):continue
    if b['n']=='rearroof':
        bm=bmesh.new();prism(bm,ccw(b['pts']),0,b['h'],0,True,1);obj('club_rearroof',bm,[mat('r_rearroof',b['c'],0.6),mat('w_rearroof',(0.92,0.92,0.9),0.8)]);continue  # redtower stands 11.9 m clear of the Huggins: removed
    if b['n']=='sawtooth':
        # sawtooth roof (aerial: white strips across the building); walls 12 m, teeth to 13.5 m, below the Huggins roof (1993 photo)
        q=[np.array(v) for v in b['pts']];bm=bmesh.new();prism(bm,ccw(b['pts']),0,12.0,1,False)
        A0,A1,B1,B0=q[0],q[3],q[2],q[1];NT=6
        for k in range(NT):
            f0,f1=k/NT,(k+1)/NT
            a0=A0+(A1-A0)*f0;a1=A0+(A1-A0)*f1;b0=B0+(B1-B0)*f0;b1=B0+(B1-B0)*f1
            quad(bm,(*a0,12.0),(*b0,12.0),(*b1,13.5),(*a1,13.5),0)
            quad(bm,(*a1,12.0),(*a1,13.5),(*b1,13.5),(*b1,12.0),2)
            bm.faces.new([bm.verts.new((*a0,12.0)),bm.verts.new((*a1,12.0)),bm.verts.new((*a1,13.5))]).material_index=1
            bm.faces.new([bm.verts.new((*b0,12.0)),bm.verts.new((*b1,13.5)),bm.verts.new((*b1,12.0))]).material_index=1
        obj('club_sawtooth',bm,[mat('r_sawtooth',b['c'],0.6),mat('w_sawtooth',(0.92,0.92,0.9),0.8),mat('st_glass',(0.15,0.17,0.2),0.3)]);continue
    pts_=b['pts']
    if b['n']=='whiteblock':
        # beside the Huggins west end (1993 panorama), not inside it: keep the part west of the stand's end line
        _R0=np.array([-19.0,93.1]);_R1=np.array([-67.1,67.6]);_tv=(_R1-_R0)/np.linalg.norm(_R1-_R0);_L=49.5
        P=[np.array(q) for q in pts_];out=[]
        for i in range(len(P)):
            a_,b2=P[i],P[(i+1)%len(P)];da=np.dot(a_-_R0,_tv)-_L;db=np.dot(b2-_R0,_tv)-_L
            if da>=0:out.append(a_)
            if (da>=0)!=(db>=0):out.append(a_+(b2-a_)*(da/(da-db)))
        pts_=[list(q) for q in out]
    bm=bmesh.new();poly=ccw(pts_)
    wall=(0.62,0.17,0.15) if b['n'] in ('redtower','brickblock') else (0.92,0.92,0.9)
    hb=min(b['h'],13.5) if b['n']=='redtower' else b['h']  # 1993 panorama: nothing rises above the Huggins roof
    if b['n'] in ('redtower','whiteblock','brickblock'):
        # plain brick below the first window row (3.4 m tile): the 3 m bank meets these walls, and the 1993 panorama shows plain brick low down
        prism(bm,poly,0,3.4,2,False,2);prism(bm,poly,3.4,hb,0,True,1)
    else:prism(bm,poly,0,hb,0,True,1)
    bmesh.ops.subdivide_edges(bm,edges=bm.edges[:],cuts=14,use_grid_fill=True)
    obj('club_'+b['n'],bm,[mat('r_'+b['n'],b['c'],0.6),mat('w_'+b['n'],wall,0.8),mat('p_'+b['n'],wall,0.8)])
# ---- G.G. Huggins Stand: tiers read off the near-frontal photo, plan from the aerial
R0=np.array([-19.0,93.1]);R1=np.array([-67.1,67.6]);tv=(R1-R0)/float(np.linalg.norm(R1-R0));LH=49.5;R1=R0+tv*LH;no=np.array([-tv[1],tv[0]])  # length: straight-down Esri 2014/2017, dark roof ends 49-50 m from the east end
if np.dot(PC-R0,no)>0:no=-no
HD=15.0  # roof back edge: straight-down Esri 2014-07/2017-02 show the dark roof 15 m deep behind the fascia
def HP(t,s_,z):q=R0+tv*t+no*s_;return (q[0],q[1],z)
bl=np.array(O['blueseats']);bt=[(np.dot(q-R0,tv)) for q in bl];BT0,BT1=min(bt),max(bt)
bm=bmesh.new();uvq=[]
def HQ(a,b,c,d,mi,uv):f=quad(bm,a,b,c,d,mi);uvq.append((f,uv))
def tier(t0,t1,s0,s1,z0,z1,n,mi):
    for k in range(n):
        sa=s0+(s1-s0)*k/n;sb=s0+(s1-s0)*(k+1)/n;za=z0+(z1-z0)*k/n;zb=z0+(z1-z0)*(k+1)/n
        HQ(HP(t1,sa,za),HP(t0,sa,za),HP(t0,sa,zb),HP(t1,sa,zb),mi,[(t1,0.44),(t0,0.44),(t0,0.8),(t1,0.8)])
        HQ(HP(t0,sa,zb),HP(t1,sa,zb),HP(t1,sb,zb),HP(t0,sb,zb),mi,[(t0,0),(t1,0),(t1,0.44),(t0,0.44)])
def wall(t0,t1,s_,z0,z1,mi,flip=False):
    a,b=(t1,t0) if not flip else (t0,t1)
    HQ(HP(a,s_,z0),HP(b,s_,z0),HP(b,s_,z1),HP(a,s_,z1),mi,[(a,z0),(b,z0),(b,z1),(a,z1)])
def slab(t0,t1,s0,s1,z,mi,down=False):
    q=[HP(t0,s0,z),HP(t1,s0,z),HP(t1,s1,z),HP(t0,s1,z)];uv=[(t0,s0),(t1,s0),(t1,s1),(t0,s1)]
    if down:q=q[::-1];uv=uv[::-1]
    HQ(*q,mi,uv)
wall(BT0,BT1,-15.8,0,0.5,0)                       # front rail wall
tier(BT0,BT1,-15.8,-6.0,0.5,3.5,12,1)            # blue tier
slab(BT0,BT1,-6.0,-5.0,3.5,2)                     # walkway
wall(0,LH,-5.0,0,5.2,0)                           # white parapet
tier(0,LH,-5.0,0.0,5.2,7.0,6,3)                  # middle green tier
HQ(HP(LH,0,7.8),HP(0,0,7.8),HP(0,0,10.0),HP(LH,0,10.0),4,[(0,0),(LH,0),(LH,2.2),(0,2.2)])  # blue sign fascia, u west->east
wall(0,LH,0.0,7.0,7.8,5)                          # glazing behind middle tier
tier(0,LH,0.0,5.8,10.0,12.6,7,3)                 # upper green tier
HQ(HP(LH,5.8,12.6),HP(0,5.8,12.6),HP(0,5.8,13.6),HP(LH,5.8,13.6),7,[(LH,0),(0,0),(0,1),(LH,1)])  # rear wall: bays with round windows (1993)
slab(0,LH,5.8,HD,12.6,2)
slab(0,LH,-0.4,HD,14.0,6)                       # roof top
slab(0,LH,-0.4,HD,13.6,6,True)                  # roof underside
wall(0,LH,-0.4,13.6,14.0,6)                       # roof fascia
for k in range(11):                               # roof rafters (aerial: white ribs across the roof, one per 5.44 m bay)
    t_=min(max(k*LH/10,0.15),LH-0.15);t0,t1=t_-0.15,t_+0.15
    slab(t0,t1,-0.4,HD,14.45,0)
    HQ(HP(t0,-0.4,14),HP(t0,HD,14),HP(t0,HD,14.45),HP(t0,-0.4,14.45),0,[(0,14),(HD+0.4,14),(HD+0.4,14.45),(0,14.45)])
    HQ(HP(t1,HD,14),HP(t1,-0.4,14),HP(t1,-0.4,14.45),HP(t1,HD,14.45),0,[(0,14),(HD+0.4,14),(HD+0.4,14.45),(0,14.45)])
    wall(t0,t1,-0.4,14,14.45,0);wall(t0,t1,HD,14,14.45,0,True)
wall(0,LH,HD,0,14.0,0,True)                     # back wall
for t_ in (0,LH):                                 # end walls
    q=[HP(t_,-5,0),HP(t_,HD,0),HP(t_,HD,14),HP(t_,-5,14)];q=q if t_==0 else q[::-1]
    HQ(*q,0,[(0,0),(HD+5,0),(HD+5,14),(0,14)])
for t_ in (BT0,BT1):
    q=[HP(t_,-15.8,0),HP(t_,-5,0),HP(t_,-5,3.5),HP(t_,-15.8,0.5)];q=q if t_==BT0 else q[::-1]
    HQ(*q,0,[(0,0),(10.8,0),(10.8,3.5),(0,.5)])
uvl=bm.loops.layers.uv.new('UVMap')
for f,uv in uvq:
    for lp,(u,v) in zip(f.loops,uv):lp[uvl].uv=(u,v)
hg=obj('huggins_stand',bm,[mat('h_white',(0.92,0.92,0.9),0.8),mat('h_blue',(0.3,0.36,0.5),0.7),mat('h_conc',(0.7,0.69,0.66),0.9),mat('h_green',(0.27,0.42,0.36),0.7),mat('h_band',(0.2,0.3,0.55),0.6),mat('h_glass',(0.15,0.17,0.2),0.3),mat('h_roof',(0.27,0.24,0.21),0.7),mat('h_rear',(0.23,0.21,0.2),0.7)])
# ---- Ian Drake Junior Development Pavilion (1993 panorama), on the aerial's grey-roof footprint, front facing the pitch
G=[np.array(q) for q in next(b for b in O['club'] if b['n']=='greyroof')['pts']]
PA,PB=G[0],G[1];LP=float(np.linalg.norm(PA-PB));pt=(PA-PB)/LP;pn=np.array([-pt[1],pt[0]])
if np.dot(G[2]-PB,pn)<0:pn=-pn
DP=float(abs(np.dot(G[2]-PB,pn)))
def PP(t,s_,z):q=PB+pt*t+pn*s_;return (q[0],q[1],z)
bm=bmesh.new()
quad(bm,PP(0,0,0),PP(LP,0,0),PP(LP,0,4.2),PP(0,0,4.2),2)          # ground floor rooms
NR=7;zs0,zs1,ss0,ss1=5.0,7.6,0.4,7.6
quad(bm,PP(0,0,5.0),PP(LP,0,5.0),PP(LP,0,5.3),PP(0,0,5.3),0)       # front rail wall
quad(bm,PP(0,0,5.0),PP(0,ss0,5.0),PP(LP,ss0,5.0),PP(LP,0,5.0),4)
for r in range(NR):
    a=ss0+(ss1-ss0)*r/NR;b_=ss0+(ss1-ss0)*(r+1)/NR;z0=zs0+(zs1-zs0)*r/NR;z1=zs0+(zs1-zs0)*(r+1)/NR
    quad(bm,PP(0,a,z0),PP(LP,a,z0),PP(LP,a,z1),PP(0,a,z1),4)
    quad(bm,PP(0,a,z1),PP(0,b_,z1),PP(LP,b_,z1),PP(LP,a,z1),3)
quad(bm,PP(0,ss1,zs1),PP(0,DP,zs1),PP(LP,DP,zs1),PP(LP,ss1,zs1),4)
quad(bm,PP(LP,DP,0),PP(0,DP,0),PP(0,DP,8.8),PP(LP,DP,8.8),0)       # back wall
quad(bm,PP(LP,0,0),PP(LP,DP,0),PP(LP,DP,8.8),PP(LP,0,8.8),0)       # white north end wall
quad(bm,PP(0,DP,0),PP(0,0,0),PP(0,0,8.8),PP(0,DP,8.8),0)
for k in range(5):                                                 # roof posts on the front rail
    t=0.3+(LP-0.6)*k/4;c=np.array(PP(t,0.15,0)[:2])
    prism(bm,[c+q for q in (np.array([-.1,-.1]),np.array([.1,-.1]),np.array([.1,.1]),np.array([-.1,.1]))],5.3,8.8,1,False)
# hip roof: eaves 8.8 (front overhang 0.8), ridge 10.8 along the middle
e=[PP(-0.3,-0.8,8.8),PP(LP+0.3,-0.8,8.8),PP(LP+0.3,DP+0.3,8.8),PP(-0.3,DP+0.3,8.8)];sm=(DP-0.5)/2
r0,r1=PP(sm+0.2,sm,10.8),PP(LP-sm-0.2,sm,10.8)
quad(bm,e[0],e[1],r1,r0,5);quad(bm,e[2],e[3],r0,r1,5)
bm.faces.new([bm.verts.new(e[1]),bm.verts.new(e[2]),bm.verts.new(r1)]).material_index=5
bm.faces.new([bm.verts.new(e[3]),bm.verts.new(e[0]),bm.verts.new(r0)]).material_index=5
quad(bm,e[1],e[0],e[3],e[2],1)                                      # roof underside
# the lighter sheeting panel on the front slope (photo: middle 45% of the length, upper half)
def onroof(t,f):a=np.array(PP(t,-0.8,8.8));b=np.array(PP(t,sm,10.8));q=a+(b-a)*f;return tuple(q+np.array([0,0,0.03]))
quad(bm,onroof(LP*0.28,0.25),onroof(LP*0.75,0.25),onroof(LP*0.75,0.9),onroof(LP*0.28,0.9),6)
bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=(R0[0],R0[1],0),plane_no=(tv[0],tv[1],0),clear_outer=True)  # pavilion stops at the Huggins east end wall (its SW corner ran 3.5 m into the stand)
obj('ian_drake_pavilion',bm,[mat('p_white',(0.92,0.92,0.9),0.8),mat('p_steel',(0.5,0.5,0.5),0.6),mat('p_rooms',(0.2,0.2,0.22),0.4),mat('p_tread',(0.7,0.69,0.66),0.9),mat('p_seat',(0.27,0.42,0.36),0.7),mat('p_roof',(0.72,0.73,0.72),0.6),mat('p_panel',(0.88,0.88,0.86),0.5)])
bm=bmesh.new();f=quad(bm,PP(0,-0.02,4.2),PP(LP,-0.02,4.2),PP(LP,-0.02,5.0),PP(0,-0.02,5.0),0)
uvl=bm.loops.layers.uv.new('UVMap')
for lp,uv in zip(f.loops,((0,0),(1,0),(1,1),(0,1))):lp[uvl].uv=uv
so_=obj('ian_drake_sign',bm,mat('p_sign',(0.9,0.9,0.88),0.7,vc=False));so_['uv_final']=1
# ---- light towers (1993 panorama + aerial heads): slender tapered pole, frame of 2x3 floodlights tilted at the pitch
bm=bmesh.new();bl=bmesh.new();luv=[]
for n_,(xy,h) in O['poles'].items():
    x,y=xy;seg=12;rb,rt=0.32,0.13
    r0=[bm.verts.new((x+rb*math.cos(2*math.pi*s/seg),y+rb*math.sin(2*math.pi*s/seg),0)) for s in range(seg)]
    r1=[bm.verts.new((x+rt*math.cos(2*math.pi*s/seg),y+rt*math.sin(2*math.pi*s/seg),h-1.0)) for s in range(seg)]
    for s in range(seg):bm.faces.new([r0[s],r0[(s+1)%seg],r1[(s+1)%seg],r1[s]]).material_index=0
    bm.faces.new(r1).material_index=0
    d_=PC-np.array(xy);d_/=np.linalg.norm(d_);nv=np.array([-d_[1],d_[0]]);c=np.array([x,y])
    tl=math.radians(25)  # lamps face down toward the pitch
    fwd=np.array([d_[0]*math.cos(tl),d_[1]*math.cos(tl),-math.sin(tl)]);up=np.array([-d_[0]*math.sin(tl),-d_[1]*math.sin(tl),math.cos(tl)]);side=np.array([nv[0],nv[1],0.0])
    base=np.array([x,y,h-0.6])+np.array([d_[0],d_[1],0])*0.25
    # crossbars
    for zz in (-0.55,0.55):
        cb=base+up*zz
        q=[cb-side*1.7-up*0.06,cb+side*1.7-up*0.06,cb+side*1.7+up*0.06,cb-side*1.7+up*0.06]
        vs=[bm.verts.new(v) for v in q];bk=[bm.verts.new(v-fwd*0.12) for v in q]
        bm.faces.new(vs).material_index=0;bm.faces.new(bk[::-1]).material_index=0
        for k in range(4):bm.faces.new([vs[k],bk[k],bk[(k+1)%4],vs[(k+1)%4]]).material_index=0
    for row in (-0.55,0.55):
        for col in (-1.1,0,1.1):
            cc=base+side*col+up*row+fwd*0.05;hw=0.45;dp=0.5
            fr=[cc+side*sx*hw+up*sz*hw for sx,sz in ((-1,-1),(1,-1),(1,1),(-1,1))]
            bk=[v-fwd*dp*(0.7 if k in (2,3) else 1.0) for k,v in enumerate(fr)]
            F=[bm.verts.new(v) for v in fr];B=[bm.verts.new(v) for v in bk]
            bm.faces.new(B[::-1]).material_index=1
            for k in range(4):bm.faces.new([F[k],B[k],B[(k+1)%4],F[(k+1)%4]]).material_index=1
            L=[bl.verts.new(v+fwd*0.005) for v in fr];luv.append(bl.faces.new(L))
obj('light_towers',bm,[mat('pole',(0.78,0.79,0.8),0.5,vc=False),mat('lamp_body',(0.85,0.86,0.86),0.5,vc=False)])
uvl=bl.loops.layers.uv.new('UVMap')
for f in luv:
    for lp,uv in zip(f.loops,((0,0),(1,0),(1,1),(0,1))):lp[uvl].uv=uv
lo=obj('lamp_lenses',bl,mat('lamp_lens',(0.85,0.85,0.8),0.2,vc=False));lo['uv_final']=1
# goal posts left out (director "Posts out": the game draws its own)
# ---- scoreboard (aerial: size, place, white front with a dark lower panel; 1993 panorama: plain board on two
#      end posts that run to the ground, dark back with vertical battens and a rail). Face blank: no lettering.
S=O['score'];e0,e1=np.array(S['ends'][0]),np.array(S['ends'][1]);cen=(e0+e1)/2;tv=(e1-e0)/np.linalg.norm(e1-e0);w=np.linalg.norm(e1-e0)/2
fn=np.array([-tv[1],tv[0]]);fn=fn if np.dot(PC-cen,fn)>0 else -fn
bm=bmesh.new();SD=0.35;H_=S['top']-S['bot']
def sbq(vs,want,mi):
    vs=[np.array(v,float) for v in vs];n_=np.cross(vs[1]-vs[0],vs[2]-vs[0])
    if n_@np.array(want,float)<0:vs=vs[::-1]
    f=bm.faces.new([bm.verts.new(tuple(v)) for v in vs]);f.material_index=mi;return f
L_,R_=cen-tv*w,cen+tv*w
prism(bm,ccw([L_,R_,R_-fn*SD,L_-fn*SD]),S['bot'],S['top'],3,True,3)          # board body, dark back and edges
P3=lambda q,z,o=0.0:(*(q+fn*o),z)
sbq([P3(L_,S['bot'],0.01),P3(R_,S['bot'],0.01),P3(R_,S['top'],0.01),P3(L_,S['top'],0.01)],(*fn,0),0)   # white front
fz0,fz1=S['bot']+0.08*H_,S['bot']+0.55*H_;fl,fr_=L_+tv*0.06*2*w,R_-tv*0.06*2*w
sbq([P3(fl,fz0,0.02),P3(fr_,fz0,0.02),P3(fr_,fz1,0.02),P3(fl,fz1,0.02)],(*fn,0),2)                       # blank dark face
for s_ in (0.0,1.0):                                                                                    # end posts, ground to top
    c=L_+(R_-L_)*s_-fn*(SD+0.18)+tv*(0.18 if s_==0 else -0.18);prism(bm,ccw([c+q for q in (np.array([-.18,-.18]),np.array([.18,-.18]),np.array([.18,.18]),np.array([-.18,.18]))]),0,S['top']+0.15,1,True,1)
nb=int(round(2*w/1.8))
for k in range(1,nb):                                                                                   # back battens
    c=L_+(R_-L_)*k/nb-fn*(SD+0.06);prism(bm,ccw([c-tv*0.06,c+tv*0.06,c+tv*0.06-fn*0.12,c-tv*0.06-fn*0.12]),S['bot'],S['top'],1,True,1)
for z_ in (S['bot']+0.1,S['bot']+H_/2,S['top']-0.1):                                                    # back rails
    prism(bm,ccw([L_-fn*(SD+0.18)+tv*0.36,R_-fn*(SD+0.18)-tv*0.36,R_-fn*(SD+0.3)-tv*0.36,L_-fn*(SD+0.3)+tv*0.36]),z_-0.08,z_+0.08,1,True,1)
sbo=obj('scoreboard',bm,[mat('sb_white',S['c'],0.6),mat('sb_leg',(0.4,0.4,0.4),0.7),mat('sb_face',S['face'],0.5),mat('sb_back',(0.17,0.18,0.18),0.8)])
# ---- sheds
# red shed and north shed removed: free-standing, outside the stadium (secretary 2026-11-18)
# ---- hand-made textures (no photo pixels): UVs in metres / tile size, tinted copies for measured colours
p=np.array(O['cam'])
TL=json.load(open(os.path.join(D,'hand','tiles.json')))
IMG={}
def timg(t,tint=None):
    k=(t,tuple(np.round(tint,3)) if tint is not None else None)
    if k in IMG:return IMG[k]
    im=bpy.data.images.load(os.path.join(D,'hand',t+'.png'),check_existing=True)
    if tint is None:IMG[k]=im;return im
    w,h=im.size;px_=np.array(im.pixels[:]).reshape(h,w,4).copy();mean=px_[...,:3].reshape(-1,3).mean(0)
    px_[...,:3]=np.clip(px_[...,:3]*(np.array(tint[:3])/np.maximum(mean,1e-3)),0,1)
    # a dark or near-white tint scales the grain down with the colour: stretch it about the tint until grey std >= 10.5/255 (ground rule: std >= 10)
    base=px_[...,:3].copy();tm=np.array(tint[:3]);k=1.0
    while k<8:
        q=np.clip(tm+(base-tm)*k,0,1);g=(q*np.array([0.299,0.587,0.114])).sum(-1)
        if g.std()*255>=10.5:break
        k*=1.15
    px_[...,:3]=q
    n2=bpy.data.images.new(t+'_'+'%02x%02x%02x'%tuple(int(c*255) for c in tint[:3]),w,h);n2.pixels[:]=px_.ravel();n2.pack();IMG[k]=n2;return n2
TEXMAP={'grass':('grass',None),'ground':('bank_dirt',None),'ground_grass':('park_grass',None),'h_white':('white',None),'h_blue':('blue_seat',None),'h_conc':('concrete',None),'h_green':('green_seat',None),'h_band':('huggins_band',None),'h_glass':('glass',None),'h_roof':('brown_roof',None),'h_rear':('hug_rear',None),'apron':('concrete',None),'fence_white':('white',None),'ad_white':('adboard',None),'ad_red':('adboard',(0.7,0.17,0.15)),'ad_blue':('adboard',(0.37,0.49,0.67)),'g_park':('park_grass',None),'g_asphalt':('asphalt',None),'g_gravel':('gravel',None),'g_path':('path',None),'g_nets':('nets',None),'fence':('white',None),'fence_post':('steel',(0.3,0.31,0.31)),'gate_steel':('steel',(0.24,0.27,0.26)),'roof':('roof_deck',None),'rib':('roof_deck',None),
 'band':('white',None),'frontwall':('white',None),'undercroft':('white',(0.45,0.46,0.46)),'standback':('darkwall',None),'benches':('bench',None),'roof_under':('roof_under',None),
 'rear_rooms':('rear_rooms',None),'concrete':('concrete',None),'blue':('blue_seat',None),'pole':('steel',None),'st_glass':('glass',None),'p_white':('white',None),'p_steel':('steel',None),'p_rooms':('rear_rooms',None),'p_tread':('concrete',None),'p_seat':('green_seat',None),'p_roof':('roof_deck',(0.72,0.73,0.72)),'p_panel':('roof_deck',(0.9,0.9,0.88)),'p_sign':('pav_sign',None),'lamp_body':('white',(0.86,0.87,0.87)),'lamp_lens':('lamp',None),'posts':('white',None),
 'sb_white':('white',S['c']),'sb_leg':('steel',(0.4,0.4,0.4)),'sb_face':('white',S['face']),'sb_back':('darkwall',(0.17,0.18,0.18)),'apron':('concrete',None),'chainwire':('chainwire',None),'crest_post':('steel',(0.6,0.61,0.62)),'bb_front':('white',(0.92,0.92,0.9)),'bb_back':('steel',(0.32,0.33,0.33)),'redshed':('roof_deck',O['redshed_c']),'shedn':('roof_deck',C['shedn'])}
for b_ in O['club']:
    TEXMAP['r_'+b_['n']]=('roof_deck',b_['c'])
    TEXMAP['w_'+b_['n']]=('brick_win',None) if b_['n'] in ('redtower','whiteblock','brickblock') else ('white',(0.92,0.92,0.9))
    TEXMAP['p_'+b_['n']]=('brick',None)
def retex(m):
    t,tint=TEXMAP[m.name];nt=m.node_tree;bs=nt.nodes['Principled BSDF']
    for n in list(nt.nodes):
        if n.type in ('VERTEX_COLOR','TEX_IMAGE'):nt.nodes.remove(n)
    ti=nt.nodes.new('ShaderNodeTexImage');ti.image=timg(t,tint);nt.links.new(ti.outputs['Color'],bs.inputs['Base Color'])
    if m.name=='chainwire':                      # cut-out mesh: glTF alphaMode MASK via a Round node
        r_=nt.nodes.new('ShaderNodeMath');r_.operation='ROUND';nt.links.new(ti.outputs['Alpha'],r_.inputs[0]);nt.links.new(r_.outputs[0],bs.inputs['Alpha'])
    return TL[t]
for o in list(sc.objects):
    if o.type!='MESH':continue
    me=o.data;tiles=[retex(m) for m in me.materials]
    had=len(me.uv_layers)>0
    if not had:me.uv_layers.new(name='UVMap')
    uvd=me.uv_layers[0].data
    for f in me.polygons:
        tw,th=tiles[f.material_index];n=f.normal
        for li in f.loop_indices:
            X=me.vertices[me.loops[li].vertex_index].co
            if had and o.get('uv_final'):continue
            if had:u,v=uvd[li].uv
            elif abs(n.z)>0.7:u,v=X.x,X.y
            else:
                t=Vector((-n.y,n.x,0)).normalized();u,v=X.dot(t),X.z
            uvd[li].uv=(u/tw,v/th)
    print('textured',o.name,flush=True)
def Rm(yaw,pitch_,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch_),math.sin(pitch_);cr,sr_=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr_*u,-sr_*r+cr*u,f])
M=Rm(*p[3:6]);Cc=p[:3];W_,H_=1024,576
# ---- camera from the fit
cam=bpy.data.cameras.new('photo');co=bpy.data.objects.new('photo_cam',cam);sc.collection.objects.link(co)
rr,uu,ff=M[0],M[1],M[2];Rot=Matrix([[rr[0],uu[0],-ff[0]],[rr[1],uu[1],-ff[1]],[rr[2],uu[2],-ff[2]]])
co.matrix_world=Matrix.Translation(Vector(Cc))@Rot.to_4x4()
cam.sensor_fit='HORIZONTAL';cam.sensor_width=36;cam.lens=p[6]*36/W_;cam.shift_x=(W_/2-p[7])/W_;cam.shift_y=(p[8]-H_/2)/W_;cam.clip_end=5000
sc.camera=co;sc.render.resolution_x=W_;sc.render.resolution_y=H_
sun=bpy.data.lights.new('sun','SUN');sun.energy=3.0;so=bpy.data.objects.new('sun',sun);sc.collection.objects.link(so);so.rotation_euler=(math.radians(40),0,math.radians(150))
wd=bpy.data.worlds.new('w');sc.world=wd;wd.use_nodes=True;wd.node_tree.nodes['Background'].inputs['Color'].default_value=(0.75,0.8,0.85,1);wd.node_tree.nodes['Background'].inputs['Strength'].default_value=0.9
sc.view_settings.view_transform='Standard'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D,'moorabbin3.blend'))
for o in sc.objects:o.select_set(o.type=='MESH')
bpy.ops.export_scene.gltf(filepath=OUT,use_selection=True,export_format='GLB',export_vertex_color='NONE')
sc.render.engine='BLENDER_EEVEE';sc.render.filepath=os.path.join(D,'render3_cam.png');bpy.ops.render.render(write_still=True)
print('DONE')
