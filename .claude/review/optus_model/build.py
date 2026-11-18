# Optus Stadium exterior from measured geometry (geom.json). Usage: blender -b --python build.py -- OUTGLB OUTBLEND
import bpy,bmesh,sys,math,json,os
from mathutils import Vector
A=sys.argv[sys.argv.index('--')+1:];dst,blend=A[0],A[1]
here=os.path.dirname(os.path.abspath(__file__))
J=json.load(open(os.path.join(here,'geom.json')));TX=os.path.join(here,'tex');TI=json.load(open(os.path.join(TX,'info.json')));BH=TI['bronze_h_m'];GH=TI['glass_h_m']
bpy.ops.wm.read_factory_settings(use_empty=True)
me=bpy.data.meshes.new('optus');ob=bpy.data.objects.new('optus',me);bpy.context.scene.collection.objects.link(ob)
def mat(name,rough=0.8,metal=0.0):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(os.path.join(TX,name+'.png'))
    nt.links.new(t.outputs['Color'],b.inputs['Base Color']);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    m.use_backface_culling=False;me.materials.append(m);return len(me.materials)-1
MB=mat('bronze',0.55,0.3);MG=mat('glass',0.15,0.2);MS=mat('seats');MR=mat('roof',0.6);MW=mat('white',0.5);MU=mat('under')
MC=mat('concrete');MT=mat('terrace');MP=mat('plaza');MD=mat('deck');MK=mat('clad',0.4,0.4);MF=mat('turf',0.95);MX=mat('dark')
MPW=mat('podwall');MPRN=mat('proof_near');MPRF=mat('proof_far');MLV=mat('louvre',0.5);MBN=mat('bench');MAI=mat('aisle');MRS=mat('riser')
bm=bmesh.new();uv=bm.loops.layers.uv.new('UVMap')
N=J['N'];K=J['K'];NB=J['NB']
V2=lambda p:Vector((p[0],p[1],0))
POD=[V2(p) for p in J['pod']];DR=[V2(p) for p in J['drum']];RF=[V2(p) for p in J['roof']];IN=[V2(p) for p in J['inner']];HB=J['hb'];IZ=J['iz']
def face(vs,mi,uvs=None,want=None):
    f=bm.faces.new(vs);f.material_index=mi;f.normal_update()
    if want is not None and f.normal.dot(want)<0:f.normal_flip()
    if uvs:
        for l in f.loops:l[uv].uv=uvs[vs.index(l.vert)]
    return f
def P(v,z):return bm.verts.new((v.x,v.y,z))
def arcs(R):
    s=[0.0]
    for i in range(N):s.append(s[-1]+(R[(i+1)%N]-R[i]).length)
    return s
def wall(R,z0f,z1f,mi,um,vm,outward=True,ctr=Vector((0,0,0)),sel=None):
    s=arcs(R);lo=[P(R[i],z0f(i)) for i in range(N)];hi=[P(R[i],z1f(i)) for i in range(N)]
    for i in range(N):
        if sel and not sel(i):continue
        j=(i+1)%N;cc=(R[i]+R[j])/2-ctr;w=Vector((cc.x,cc.y,0)).normalized()*(1 if outward else -1)
        face([lo[i],lo[j],hi[j],hi[i]],mi,[(s[i]/um,z0f(i)/vm),(s[i+1]/um,z0f(j)/vm),(s[i+1]/um,z1f(j)/vm),(s[i]/um,z1f(i)/vm)],w)
def flat(Ra,za,Rb,zb,mi,sc=10.0,up=True,sel=None):
    a=[P(Ra[i],za(i)) for i in range(N)];b=[P(Rb[i],zb(i)) for i in range(N)]
    for i in range(N):
        if sel and not sel(i):continue
        j=(i+1)%N;vs=[a[i],a[j],b[j],b[i]];face(vs,mi,[(v.co.x/sc,v.co.y/sc) for v in vs],Vector((0,0,1 if up else -1)))
c=lambda z:(lambda i:z)
# o2 sees podium segments 382..415,0..123. Segments 144..367 (two bays inside the hidden arc, on bay boundaries) get
# the street-level glazed entrance storey of close-ups 092/192 and c5 instead of the raised podium.
HS,HE=144,368;hid=lambda i:HS<=i<HE;vis=lambda i:not hid(i)
MGD=mat('ground');GB=TI['ground_box'];MEN=mat('entrance',0.12,0.1);MCO=mat('column',0.5)
# plaza apron, podium wall, terrace
pass
wall(POD,c(0.0),c(6.4),MPW,TI['podwall_m'][0],TI['podwall_m'][1],sel=vis)
flat(POD,c(6.4),DR,c(6.4),MT,TI['terrace_m'],sel=vis)
# bronze screen, ledge, glass band
# bronze screen: from 8.0 m up to the measured top; UV = real metres, top-anchored (texture spans 2 bays x 22 m)
BAY2=2*arcs(DR)[N]/NB;sD=arcs(DR);ZB=8.0
ZE=7.0;zv=lambda i:ZE if HS<i<HE else ZB      # bronze comes down to the clerestory head on the entrance side
lo=[P(DR[i],zv(i)) for i in range(N)];hi=[P(DR[i],HB[i]) for i in range(N)]
for i in range(N):
    j=(i+1)%N;w=Vector((DR[i].x+DR[j].x,DR[i].y+DR[j].y,0)).normalized()
    face([lo[i],lo[j],hi[j],hi[i]],MB,[(sD[i]/BAY2,1-(HB[i]-zv(i))/BH),(sD[i+1]/BAY2,1-(HB[j]-zv(j))/BH),(sD[i+1]/BAY2,1.0),(sD[i]/BAY2,1.0)],w)
# shadowed recess under the screen with posts every half bay (o2: dark strip and white posts under the bronze)
DRI=[DR[i]-Vector((DR[i].x,DR[i].y,0)).normalized()*1.2 for i in range(N)]
wall(DRI,c(6.4),c(ZB),MX,4,4,sel=vis)
flat(DR,c(6.4),DRI,c(6.4),MT,TI['plaza_m'],sel=vis)  # deck floor under the recess (was a see-through gap)
flat(DR,c(ZB),DRI,c(ZB),MX,4,up=False,sel=vis)
# --- entrance side: plaza at street level up to a glazed storey 1.5 m under the bronze, white columns under its edge
DRG=[DR[i]-Vector((DR[i].x,DR[i].y,0)).normalized()*1.5 for i in range(N)];sG=arcs(DRG);EB=TI['entrance_bay_m']*sG[N]/sD[N]
def gflat(Ra,Rb,z,sel):
    a=[P(Ra[i],z) for i in range(N)];b=[P(Rb[i],z) for i in range(N)]
    for i in range(N):
        if not sel(i):continue
        j=(i+1)%N;vs=[a[i],a[j],b[j],b[i]];face(vs,MGD,[((v.co.x-GB[0])/GB[2],(v.co.y-GB[1])/GB[2]) for v in vs],Vector((0,0,1)))
gflat(POD,DRG,0.0,hid)
lo_=[P(DRG[i],0.0) for i in range(N)];hi_=[P(DRG[i],ZE) for i in range(N)]
for i in range(HS,HE):
    j=i+1;w=Vector((DRG[i].x+DRG[j].x,DRG[i].y+DRG[j].y,0)).normalized()
    face([lo_[i],lo_[j],hi_[j],hi_[i]],MEN,[(sG[i]/EB,0),(sG[j]/EB,0),(sG[j]/EB,1),(sG[i]/EB,1)],w)
flat(DR,c(ZE),DRG,c(ZE),MX,4,up=False,sel=hid)
for e,sg in ((HS,1),(HE,-1)):                 # close the two ends where the podium stops (podium, recess, soffit)
    t=(POD[(e+1)%N]-POD[e]).normalized()*sg
    face([P(POD[e],0),P(DRG[e],0),P(DRG[e],6.4),P(POD[e],6.4)],MPW,[(0,0),(1,0),(1,1.6),(0,1.6)],t)
    face([P(DR[e],6.4),P(DRG[e],6.4),P(DRG[e],ZB),P(DR[e],ZB)],MX,[(0,0),(0.4,0),(0.4,0.4),(0,0.4)],t)
def cyl(cx,cy,z0,z1,r,mi,n=12):
    ring=[(cx+r*math.cos(2*math.pi*k/n),cy+r*math.sin(2*math.pi*k/n)) for k in range(n)]
    for k in range(n):
        a_,b_=ring[k],ring[(k+1)%n];w=Vector(((a_[0]+b_[0])/2-cx,(a_[1]+b_[1])/2-cy,0)).normalized()
        face([bm.verts.new((a_[0],a_[1],z0)),bm.verts.new((b_[0],b_[1],z0)),bm.verts.new((b_[0],b_[1],z1)),bm.verts.new((a_[0],a_[1],z1))],mi,[(k/n,0),((k+1)/n,0),((k+1)/n,1),(k/n,1)],w)
for i in range(HS+K//2,HE,K//2):              # columns every half bay, front face under the bronze edge
    q=DR[i]-Vector((DR[i].x,DR[i].y,0)).normalized()*0.55;cyl(q.x,q.y,0.0,ZE,0.45,MCO)
flat(DR,lambda i:HB[i],RF,lambda i:HB[i],MD,TI['plaza_m'])
sR=arcs(RF);BAYR=2*sR[N]/NB
for i in range(N):
    j=(i+1)%N;w=Vector((RF[i].x+RF[j].x,RF[i].y+RF[j].y,0)).normalized()
    face([P(RF[i],HB[i]),P(RF[j],HB[j]),P(RF[j],33.0),P(RF[i],33.0)],MG,[(sR[i]/BAYR,1-(33-HB[i])/GH),(sR[i+1]/BAYR,1-(33-HB[j])/GH),(sR[i+1]/BAYR,1.0),(sR[i]/BAYR,1.0)],w)
wall(RF,c(32.6),c(34.4),MW,1e6,1e6)
# roof membrane: barrel vault per bay
NC=5;SUB=6;T=NC*SUB;rows=[]
for k in range(T+1):
    t=k/T;row=[]
    for i in range(N):
        p=RF[i].lerp(IN[i],t);zb=34.4+(IZ-34.4)*t;w=(k%SUB)/SUB
        bul=1.1*math.sin(math.pi*(i%K)/K)*math.sin(math.pi*w)
        row.append(bm.verts.new((p.x,p.y,zb+bul)))
    rows.append(row)
for k in range(T):
    for i in range(N):
        j=(i+1)%N;vs=[rows[k][i],rows[k][j],rows[k+1][j],rows[k+1][i]]
        a=RF[i].lerp(IN[i],k/T);b=RF[j].lerp(IN[j],k/T);a2=RF[i].lerp(IN[i],(k+1)/T)
        u0=arcs(RF)[i]/8.0;u1=arcs(RF)[i+1]/8.0;rl=(RF[i]-IN[i]).length
        face(vs,MR,[(u0,k/T*rl/8),(u1,k/T*rl/8),(u1,(k+1)/T*rl/8),(u0,(k+1)/T*rl/8)],Vector((0,0,1)))
flat(RF,c(32.6),IN,c(IZ-1.0),MU,10,up=False)
oc=Vector((J['oc'][0],J['oc'][1],0))
wall(IN,c(IZ-1.0),c(IZ+0.2),MW,1e6,1e6,outward=False,ctr=oc)
def tube(a,b,r,mi):
    d=(b-a);L=d.length
    if L<1e-3:return
    d.normalize();up=Vector((0,0,1)) if abs(d.z)<0.9 else Vector((1,0,0));x=d.cross(up).normalized()*r;y=d.cross(x).normalized()*r
    ca=[bm.verts.new(a+x*sx+y*sy) for sx,sy in((1,1),(-1,1),(-1,-1),(1,-1))];cb=[bm.verts.new(b+x*sx+y*sy) for sx,sy in((1,1),(-1,1),(-1,-1),(1,-1))]
    for q in range(4):
        r2=(q+1)%4;w=((ca[q].co+ca[r2].co)/2-a).normalized()
        face([ca[q],ca[r2],cb[r2],cb[q]],mi,[(q/4,0),((q+1)/4,0),((q+1)/4,L/4),(q/4,L/4)],w)
for bi in range(NB):
    i=bi*K;o=RF[i];n=IN[i]
    def at(t,dz=0.0,o=o,n=n):
        p=o.lerp(n,t);return Vector((p.x,p.y,34.4+(IZ-34.4)*t+dz))
    top=lambda t:(2.8*min(t/0.35,1.0) if t<0.35 else 2.8-2.0*(t-0.35)/0.65)
    nseg=12
    for s_ in range(nseg):
        t0,t1=s_/nseg,(s_+1)/nseg
        tube(at(t0,top(t0)),at(t1,top(t1)),0.32,MW);tube(at(t0,0.2),at(t1,0.2),0.22,MW)
        if s_%2==0:tube(at(t0,0.2),at(t1,top(t1)),0.16,MW)
        else:tube(at(t0,top(t0)),at(t1,0.2),0.16,MW)
    tube(at(0,0.2),at(0,top(0)+0.01),0.2,MW);tube(at(1,0.2),at(1,top(1)),0.2,MW)
    tube(Vector((o.x,o.y,HB[i])),Vector((o.x,o.y,29.0)),0.42,MW)
    a1=RF[(i-2)%N];a2=RF[(i+2)%N]
    tube(Vector((o.x,o.y,29.0)),Vector((a1.x,a1.y,32.8)),0.28,MW);tube(Vector((o.x,o.y,29.0)),Vector((a2.x,a2.y,32.8)),0.28,MW)
# bowl seating inside, turf
ang=math.radians(-170.5);U=Vector((math.cos(ang),math.sin(ang),0));Vv=Vector((-math.sin(ang),math.cos(ang),0))
def ell(d,a=82.2,b=64.05):
    du,dv=d.dot(U),d.dot(Vv);k=1/math.sqrt((du/a)**2+(dv/b)**2);return oc+d*k
L0=[ell((RF[i]-oc).normalized(),82.2*1.07,64.05*1.09) for i in range(N)]
L1=[L0[i].lerp(RF[i],0.42) for i in range(N)];L3=[L0[i].lerp(RF[i],0.97) for i in range(N)]
# bowl: stand texture = one real seating bay (063), u once per bay along the ring, v by height through the three tiers
SL=arcs(L0);BAYL=SL[N]/NB
SU=[SL[i]/BAYL for i in range(N+1)]
KN=[(0,1.0),(1.6,0.95),(12,0.71),(15,0.667),(31.5,0.0)]
def VZ(z):
    for (z0,f0),(z1,f1) in zip(KN,KN[1:]):
        if z<=z1:return 1-(f0+(f1-f0)*(z-z0)/(z1-z0))
    return 1.0
def rake(Ra,za,Rb,zb,rowsn):
    pr=None
    for r_ in range(rowsn+1):
        t=r_/rowsn;z=za+(zb-za)*t;R_=[Ra[i].lerp(Rb[i],t) for i in range(N)]
        cur=[P(R_[i],z) for i in range(N)]
        if pr is not None:
            low=[P(R_[i],pz) for i in range(N)];zm=pz+0.6*(z-pz)
            for i in range(N):
                j=(i+1)%N;cc=(Ra[i]+Ra[j])/2-oc;cc.z=0;inw=-cc.normalized()
                face([pr[i],pr[j],low[j],low[i]],MS,[(SU[i],VZ(pz)),(SU[i+1],VZ(pz)),(SU[i+1],VZ(zm)),(SU[i],VZ(zm))],Vector((0,0,1)))
                face([low[i],low[j],cur[j],cur[i]],MS,[(SU[i],VZ(zm)),(SU[i+1],VZ(zm)),(SU[i+1],VZ(z)),(SU[i],VZ(z))],inw)
        pr=cur;pz=z
def swall(R,z0,z1):
    lo=[P(R[i],z0) for i in range(N)];hi=[P(R[i],z1) for i in range(N)]
    for i in range(N):
        j=(i+1)%N;cc=(R[i]+R[j])/2-oc;cc.z=0
        face([lo[i],lo[j],hi[j],hi[i]],MS,[(SU[i],VZ(z0)),(SU[i+1],VZ(z0)),(SU[i+1],VZ(z1)),(SU[i],VZ(z1))],-cc.normalized())
swall(L0,0.0,1.6)
rake(L0,1.6,L1,12.0,24)
swall(L1,12.0,15.0)
rake(L1,15.0,L3,31.5,30)
# no turf inside the bowl and no plaza beyond the podium edge: the game draws the turf (director: "Leave field out")
def prism(pts,h,roofmi,wallmi,glassband=False,louvre_from=None):
    pts=[Vector((p[0],p[1],0)) for p in pts];n=len(pts);cc=sum(pts,Vector())/n
    lo=[P(p,0.0) for p in pts];mid=[P(p,h-2.2) for p in pts];mi2=[P(p,h-0.7) for p in pts];hi=[P(p,h) for p in pts]
    s0=0.0
    for i in range(n):
        j=(i+1)%n;w=((pts[i]+pts[j])/2-cc).normalized();L=(pts[j]-pts[i]).length;ua,ub=s0/4,(s0+L)/4;s0+=L
        q=lambda z0,z1,sc=4.0:[(ua,z0/sc),(ub,z0/sc),(ub,z1/sc),(ua,z1/sc)]
        face([lo[i],lo[j],mid[j],mid[i]],wallmi,q(0,h-2.2),w)
        if glassband:face([mid[i],mid[j],mi2[j],mi2[i]],MG,[(s0/BAYR-L/BAYR,1-3.5/GH),(s0/BAYR,1-3.5/GH),(s0/BAYR,1-2.0/GH),(s0/BAYR-L/BAYR,1-2.0/GH)],w)
        else:face([mid[i],mid[j],mi2[j],mi2[i]],wallmi,q(h-2.2,h-0.7),w)
        face([mi2[i],mi2[j],hi[j],hi[i]],MW,q(h-0.7,h),w)
    top=bm.faces.new(hi);top.normal_update()
    if top.normal.z<0:top.normal_flip()
    res=bmesh.ops.triangulate(bm,faces=[top])
    for f in res['faces']:
        f.material_index=roofmi
        if louvre_from is not None and f.calc_center_median().y>louvre_from:f.material_index=MLV
        for l in f.loops:l[uv].uv=((l.vert.co.x-cc.x)/TI['proof_span_m']+0.5,(l.vert.co.y-cc.y)/TI['proof_span_m']+0.5)
# the two orange-roof pavilions are left out: they stand apart from the bowl (director: stadium only)
S=J['stair'];T1,T2,B1,B2=[Vector((S[k][0],S[k][1],0)) for k in ('T1','T2','B1','B2')]
# o2: stepped sandstone side walls (6 big steps), three bench blocks, two concrete aisles with white handrails
def SP(a,t):return T1.lerp(T2,a).lerp(B1.lerp(B2,a),t)
AX=(T2-T1).normalized();DX=(B1-T1).normalized();WD=(T2-T1).length;PWU,PWV=TI['podwall_m']
ws=1.0/WD;bk=(1-2*ws)*0.25/0.9;ai=(1-2*ws)*0.075/0.9
seg=[(ws,ws+bk,'b'),(ws+bk,ws+bk+ai,'a'),(ws+bk+ai,ws+2*bk+ai,'b'),(ws+2*bk+ai,ws+2*bk+2*ai,'a'),(ws+2*bk+2*ai,1-ws,'b')]
ns=16
for s_ in range(ns):
    t0,t1=s_/ns,(s_+1)/ns;z=6.4*(1-t0);z2=6.4*(1-t1)
    for a0,a1,k in seg:
        ua,ub=a0*WD/2.4,a1*WD/2.4
        face([P(SP(a0,t0),z),P(SP(a1,t0),z),P(SP(a1,t1),z),P(SP(a0,t1),z)],MBN if k=='b' else MAI,[(ua,1),(ub,1),(ub,0),(ua,0)],Vector((0,0,1)))
        face([P(SP(a0,t1),z),P(SP(a1,t1),z),P(SP(a1,t1),z2),P(SP(a0,t1),z2)],MRS,[(ua,1),(ub,1),(ub,0),(ua,0)],DX)
def sidewall(a0,a1):
    for j in range(6):
        t0,t1=j/6,(j+1)/6;zt=6.4*(1-j/6);q=[SP(a0,t0),SP(a1,t0),SP(a1,t1),SP(a0,t1)]
        face([P(v,zt) for v in q],MPW,[(v.x/PWU,v.y/PWU) for v in q],Vector((0,0,1)))
        L=(q[2]-q[3]).length;face([P(q[3],0),P(q[2],0),P(q[2],zt),P(q[3],zt)],MPW,[(0,0),(L/PWU,0),(L/PWU,zt/PWV),(0,zt/PWV)],DX)
        for pa,pb,w in ((q[0],q[3],-AX),(q[1],q[2],AX)):
            L=(pb-pa).length;s0=(pa-T1).dot(DX)/PWU
            face([P(pa,0),P(pb,0),P(pb,zt),P(pa,zt)],MPW,[(s0,0),(s0+L/PWU,0),(s0+L/PWU,zt/PWV),(s0,zt/PWV)],w)
sidewall(0,ws);sidewall(1-ws,1)
def bar(p,q,r,mi):
    d=(q-p).normalized();x=d.cross(Vector((0,0,1)))
    if x.length<1e-3:x=Vector((1,0,0))
    x.normalize();y=d.cross(x).normalized();cs=[x*r+y*r,-x*r+y*r,-x*r-y*r,x*r-y*r]
    for i in range(4):
        j=(i+1)%4;face([bm.verts.new(p+cs[i]),bm.verts.new(p+cs[j]),bm.verts.new(q+cs[j]),bm.verts.new(q+cs[i])],mi,[(0,0),(1,0),(1,1),(0,1)],cs[i]+cs[j])
for a0,a1,k in seg:
    if k!='a':continue
    ac=(a0+a1)/2;RH=0.95
    p=SP(ac,0.0);q=SP(ac,1.0);bar(Vector((p.x,p.y,6.4+RH)),Vector((q.x,q.y,RH)),0.05,MW)
    for s_ in range(0,ns+1,4):
        t=min(s_/ns,1-0.5/ns);v=SP(ac,t);z=6.4*(1-s_/ns) if s_<ns else 6.4*(0.5/ns)
        bar(Vector((v.x,v.y,6.4*(1-t))),Vector((v.x,v.y,6.4*(1-t)+RH)),0.04,MW)
lx,ly,lh=J["lift"];hw=2.0
cs=[Vector((lx-hw,ly-hw,0)),Vector((lx+hw,ly-hw,0)),Vector((lx+hw,ly+hw,0)),Vector((lx-hw,ly+hw,0))]
lo=[P(p,6.4) for p in cs];hi=[P(p,lh) for p in cs]
for i in range(4):
    j=(i+1)%4;w=((cs[i]+cs[j])/2-Vector((lx,ly,0))).normalized();face([lo[i],lo[j],hi[j],hi[i]],MK,[(i,6.4/4),(i+1,6.4/4),(i+1,lh/4),(i,lh/4)],w)
face(hi,MK,[(v.co.x/4,v.co.y/4) for v in hi],Vector((0,0,1)))
MGR=mat('grille',0.6)
import math as _m
def _ang(v):return _m.atan2(v.y,v.x)
for a,b,h,k in J.get('openings',[]):
    a=Vector((a[0],a[1],0));b=Vector((b[0],b[1],0));t0,t1=sorted([_ang(a),_ang(b)])
    mi={'grille':MGR,'dark':MX,'clad':MK}[k]
    # walk the podium outline between the two angles (wall follows the curve)
    pts=[a if _ang(a)==t0 else b]+[p for p in POD if t0<_ang(p)<t1]+[b if _ang(a)==t0 else a]
    pts.sort(key=_ang);s0=0.0
    for p,q in zip(pts,pts[1:]):
        wp=Vector((p.x,p.y,0)).normalized()*0.25;wq=Vector((q.x,q.y,0)).normalized()*0.25
        pp=Vector((p.x,p.y,0))+wp;qq=Vector((q.x,q.y,0))+wq;L=(qq-pp).length
        if L<1e-3:continue
        face([P(pp,0.02),P(qq,0.02),P(qq,h),P(pp,h)],mi,[(s0/4,0),((s0+L)/4,0),((s0+L)/4,h/4),(s0/4,h/4)],wp+wq);s0+=L
bm.to_mesh(me);bm.free()
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=os.path.abspath(dst),export_format='GLB')
print('tris',sum(len(p.vertices)-2 for p in me.polygons))
