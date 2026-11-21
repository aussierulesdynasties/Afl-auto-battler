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
MC=mat('concrete');MT=mat('terrace');MP=mat('plaza');MD=mat('deck');MK=mat('clad',0.4,0.4);MKL=mat('clad',0.85,0.0);MX=mat('dark')
MPW=mat('podwall');MLV=mat('louvre',0.5);MBN=mat('bench');MAI=mat('aisle');MRS=mat('riser')
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
MEN=mat('entrance',0.12,0.1);MCO=mat('column',0.5)
# plaza apron, podium wall, terrace
pass
wall(POD,c(0.0),c(6.4),MPW,TI['podwall_m'][0],TI['podwall_m'][1],sel=vis)
flat(POD,c(6.4),DR,c(6.4),MT,TI['terrace_m'],sel=vis)
# bronze screen, ledge, glass band
# bronze screen: from 8.0 m up to the measured top; UV = real metres, top-anchored (texture spans 2 bays x 22 m)
BAY2=2*arcs(DR)[N]/NB;sD=arcs(DR);ZB=8.0
ZE=7.0;zv=lambda i:ZE if HS<i<HE else ZB      # bronze comes down to the clerestory head on the entrance side
# o2 (2026-11-19): from segment 53 westward a dark glazed strip runs under the bronze: bronze ends 12.5 m at 57, 13.5 m from 63
ZGK=[(52,ZB),(57,12.5),(63,13.5),(143,13.5)];import numpy as _np
ZG=lambda i:float(_np.interp(i,[k[0] for k in ZGK],[k[1] for k in ZGK])) if 52<=i<=143 else (ZE if HS<i<HE else ZB)
MXG=mat('dark',0.2,0.1)
for i in range(52,144):   # 143->144 too: the strip closes the bronze's drop to 8 m at the hidden-arc start (was a see-through triangle)
    j=i+1;w=Vector((DR[i].x+DR[j].x,DR[i].y+DR[j].y,0)).normalized()
    vs_=[P(DR[i],zv(i)),P(DR[j],zv(j))]+([P(DR[j],ZG(j))] if ZG(j)>zv(j)+1e-6 else [])+[P(DR[i],ZG(i))]
    face(vs_,MXG,[(0,0),(0.4,0),(0.4,0.4),(0,0.4)],w)
_zv=zv;zv=lambda i:max(_zv(i),ZG(i))
for a_,b_ in ((HS,HS+1),(HE-1,HE)):            # entrance-side ends: bronze bottom steps 8 m <-> 7 m in one segment over a 7 m soffit; close the triangle
    w=Vector((DR[a_].x+DR[b_].x,DR[a_].y+DR[b_].y,0)).normalized()
    vs_=[P(DR[a_],ZE),P(DR[b_],ZE)]+([P(DR[b_],zv(b_))] if zv(b_)>ZE+1e-6 else [])+([P(DR[a_],zv(a_))] if zv(a_)>ZE+1e-6 else [])
    if len(vs_)>=3:face(vs_,MX,[(0,0),(0.4,0),(0.4,0.4),(0,0.4)][:len(vs_)],w)
lo=[P(DR[i],zv(i)) for i in range(N)];hi=[P(DR[i],HB[i]) for i in range(N)]
SG=TI.get('signs',{});SM={k:mat(k,0.55,0.3) for k in SG}
for i in range(N):
    j=(i+1)%N;w=Vector((DR[i].x+DR[j].x,DR[i].y+DR[j].y,0)).normalized()
    sg=[k for k,(a0,a1,z0,z1) in SG.items() if a0<=i<a1]
    if sg:                                       # ground name signs (texture pass): own map, u along the sign, v=(z-z0)/(z1-z0)
        a0,a1,z0,z1=SG[sg[0]];u0,u1=(sD[i]-sD[a0])/(sD[a1]-sD[a0]),(sD[i+1]-sD[a0])/(sD[a1]-sD[a0]);vz=lambda z:(z-z0)/(z1-z0)
        face([lo[i],lo[j],hi[j],hi[i]],SM[sg[0]],[(u0,vz(zv(i))),(u1,vz(zv(j))),(u1,vz(HB[j])),(u0,vz(HB[i]))],w);continue
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
        j=(i+1)%N;vs=[a[i],a[j],b[j],b[i]];face(vs,MP,[(v.co.x/TI['plaza_m'],v.co.y/TI['plaza_m']) for v in vs],Vector((0,0,1)))   # street apron: plain paving (texture pass)
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
# true frame (camL level fit): deck on the bronze top, glass storey set back 4.5 m, soffit 44.4, white fascia to the
# roof edge at 46.55, membrane falling to the inner edge IZ
ZS,ZF=44.4,46.55
# west 166-250 (r2/westfix.py): the band moved out to o2's line; glass, columns and braces stay on the old drum (drum0)
DR0=[V2(p) for p in J.get('drum0',J['drum'])]
GL=[V2(p) for p in J['glass']] if 'glass' in J else [DR0[i]-Vector((DR0[i].x,DR0[i].y,0)).normalized()*4.5 for i in range(N)]  # west glass from o2 (r2/westfix.py)
flat(DR,lambda i:HB[i],GL,lambda i:HB[i],MD,TI['plaza_m'])
sR=arcs(RF);BAYR=2*sR[N]/NB;sGL=arcs(GL);BAYG=2*sGL[N]/NB
for i in range(N):
    j=(i+1)%N;w=Vector((GL[i].x+GL[j].x,GL[i].y+GL[j].y,0)).normalized()
    face([P(GL[i],HB[i]),P(GL[j],HB[j]),P(GL[j],ZS),P(GL[i],ZS)],MG,[(sGL[i]/BAYG,1-(ZS-HB[i])/GH),(sGL[i+1]/BAYG,1-(ZS-HB[j])/GH),(sGL[i+1]/BAYG,1.0),(sGL[i]/BAYG,1.0)],w)
wall(RF,c(ZS),c(ZF),MW,1e6,1e6)
# roof membrane: barrel vault per bay
NC=5;SUB=6;T=NC*SUB;rows=[]
for k in range(T+1):
    t=k/T;row=[]
    for i in range(N):
        p=RF[i].lerp(IN[i],t);zb=ZF+(IZ-ZF)*t;w=(k%SUB)/SUB
        bul=1.1*math.sin(math.pi*(i%K)/K)*math.sin(math.pi*w)
        row.append(bm.verts.new((p.x,p.y,zb+bul)))
    rows.append(row)
for k in range(T):
    for i in range(N):
        j=(i+1)%N;vs=[rows[k][i],rows[k][j],rows[k+1][j],rows[k+1][i]]
        a=RF[i].lerp(IN[i],k/T);b=RF[j].lerp(IN[j],k/T);a2=RF[i].lerp(IN[i],(k+1)/T)
        u0=arcs(RF)[i]/8.0;u1=arcs(RF)[i+1]/8.0;rl=(RF[i]-IN[i]).length
        face(vs,MR,[(u0,k/T*rl/8),(u1,k/T*rl/8),(u1,(k+1)/T*rl/8),(u0,(k+1)/T*rl/8)],Vector((0,0,1)))
flat(RF,c(ZS),IN,c(IZ-1.0),MU,10,up=False)
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
# o2 west: a white canopy over the wide terrace at 22.5 m, glass line out to the measured edge, posts on the terrace
CJ=J.get('canopy');CS=set(k for k,_ in CJ['r']) if CJ else set()
if CJ:
    ZCN=CJ['z'];CR={k:r for k,r in CJ['r']};OC2=Vector((J['oc'][0],J['oc'][1],0))
    CO=[(OC2+(DR[i]-OC2).normalized()*CR[i]) if i in CR else GL[i] for i in range(N)]
    csel=lambda i:i in CS and (i+1)%N in CS
    flat(GL,c(ZCN),CO,c(ZCN),MW,1e6,sel=csel);flat(GL,c(ZCN-0.35),CO,c(ZCN-0.35),MW,1e6,up=False,sel=csel)
    wall(CO,c(ZCN-0.35),c(ZCN),MW,1e6,1e6,sel=csel)
    for i in sorted(CS)[::K//2]:
        q=CO[i]-(CO[i]-OC2).normalized()*0.4;tube(Vector((q.x,q.y,HB[i])),Vector((q.x,q.y,ZCN-0.35)),0.12,MW)
for bi in range(NB):
    i=bi*K;o=RF[i];n=IN[i]
    def at(t,dz=0.0,o=o,n=n):
        p=o.lerp(n,t);return Vector((p.x,p.y,ZF+(IZ-ZF)*t+dz))
    top=lambda t:(2.8*min(t/0.35,1.0) if t<0.35 else 2.8-2.0*(t-0.35)/0.65)
    nseg=12
    for s_ in range(nseg):
        t0,t1=s_/nseg,(s_+1)/nseg
        tube(at(t0,top(t0)),at(t1,top(t1)),0.32,MW);tube(at(t0,0.2),at(t1,0.2),0.22,MW)
        if s_%2==0:tube(at(t0,0.2),at(t1,top(t1)),0.16,MW)
        else:tube(at(t0,top(t0)),at(t1,0.2),0.16,MW)
    tube(at(0,0.2),at(0,top(0)+0.01),0.2,MW);tube(at(1,0.2),at(1,top(1)),0.2,MW)
    d_=DR0[i];ZC=8+(29.0-8)*1.478
    tube(Vector((d_.x,d_.y,HB[i])),Vector((d_.x,d_.y,ZC)),0.42,MW)
    a1=RF[(i-2)%N];a2=RF[(i+2)%N]
    tube(Vector((d_.x,d_.y,ZC)),Vector((a1.x,a1.y,ZS-0.2)),0.28,MW);tube(Vector((d_.x,d_.y,ZC)),Vector((a2.x,a2.y,ZS-0.2)),0.28,MW)
# bowl seating inside, turf
FE=J['fence'];oc=Vector((FE['c'][0],FE['c'][1],0));ang=FE['ang'];U=Vector((math.cos(ang),math.sin(ang),0));Vv=Vector((-math.sin(ang),math.cos(ang),0))   # bowl front = measured fence oval
U=Vector((math.cos(ang),math.sin(ang),0));Vv=Vector((-math.sin(ang),math.cos(ang),0))
def ell(d,a=82.2,b=64.05):
    du,dv=d.dot(U),d.dot(Vv);k=1/math.sqrt((du/a)**2+(dv/b)**2);return oc+d*k
L0=[ell((RF[i]-oc).normalized(),FE['a'],FE['b']) for i in range(N)];ZK=1.36   # tier heights x camL level fit
L1=[L0[i].lerp(RF[i],0.42) for i in range(N)];L3=[L0[i].lerp(RF[i],0.97) for i in range(N)]
# bowl: stand texture = one real seating bay (063), u once per bay along the ring, v by height through the three tiers
SL=arcs(L0);BAYL=SL[N]/NB
SU=[SL[i]/BAYL for i in range(N+1)]
KN=[(0,1.0),(1.6*ZK,0.95),(12*ZK,0.71),(15*ZK,0.667),(31.5*ZK,0.0)]
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
swall(L0,0.0,1.6*ZK)
rake(L0,1.6*ZK,L1,12.0*ZK,24)
swall(L1,12.0*ZK,15.0*ZK)
rake(L1,15.0*ZK,L3,31.5*ZK,30)
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
# True frame (camL on o2, checked on Esri z19): the head is on the deck at 6.4 m to the south, the foot on the plaza
# to the north. T1-B1 is the lift side (east), T2-B2 the curved-building side (west).
def SP(a,t):return T1.lerp(T2,a).lerp(B1.lerp(B2,a),t)
AX=(T2-T1).normalized();DX=(B1-T1).normalized();WD=(T2-T1).length;PWU,PWV=TI['podwall_m']
ws=1.0/WD;ZT=6.4
# o2: 2D FFT of three 32 px patches on the flight gives a slat period of 2.38-2.51 photo px (44 steps rendered 3.0-3.2 px)
# -> 58 steps (0.110 m rise), which renders the photo's period.
# Two light cross walkways, partial as o2: t 0.31-0.36 for a 0.15-0.43 and 0.62-0.88; t 0.70-0.75 for a 0.15-0.80.
ns=58
WALKS=[(0.27,0.33,[(0.10,1.0)]),(0.585,0.645,[(0.0,1.0)])]   # o2 luminance profiles up the flight: upper u 0.10-1, lower full width (dark spot mid = people)
def walk_spans(t):
    for t0,t1,sp in WALKS:
        if t0<=t<t1:return sp
    return []
for s_ in range(ns):
    t0,t1=s_/ns,(s_+1)/ns;z=ZT*(1-t0);z2=ZT*(1-t1);sp=walk_spans((t0+t1)/2)
    cuts=sorted(set([ws,1-ws]+[v for ab in sp for v in ab]))
    for a0,a1 in zip(cuts,cuts[1:]):
        am=(a0+a1)/2;isw=any(lo<=am<hi for lo,hi in sp);ua,ub=a0*WD/2.4,a1*WD/2.4
        face([P(SP(a0,t0),z),P(SP(a1,t0),z),P(SP(a1,t1),z),P(SP(a0,t1),z)],MAI if isw else MBN,[(ua,1),(ub,1),(ub,0),(ua,0)],Vector((0,0,1)))
    ua,ub=ws*WD/2.4,(1-ws)*WD/2.4
    face([P(SP(ws,t1),z),P(SP(1-ws,t1),z),P(SP(1-ws,t1),z2),P(SP(ws,t1),z2)],MRS,[(ua,1),(ub,1),(ub,0),(ua,0)],DX)
def sidewall(edge_in,edge_out,nst,wout):
    # stepped sandstone wall between two lines; each step's top drops with the flight
    for j in range(nst):
        t0,t1=j/nst,(j+1)/nst;zt=ZT*(1-t0);q=[edge_in(t0),edge_out(t0),edge_out(t1),edge_in(t1)]
        face([P(v,zt) for v in q],MPW,[(v.x/PWU,v.y/PWU) for v in q],Vector((0,0,1)))
        L=(q[2]-q[3]).length;face([P(q[3],0),P(q[2],0),P(q[2],zt),P(q[3],zt)],MPW,[(0,0),(L/PWU,0),(L/PWU,zt/PWV),(0,zt/PWV)],DX)
        for pa,pb,w in ((q[0],q[3],-wout),(q[1],q[2],wout)):
            L=(pb-pa).length;s0=(pa-T1).dot(DX)/PWU
            face([P(pa,0),P(pb,0),P(pb,zt),P(pa,zt)],MPW,[(s0,0),(s0+L/PWU,0),(s0+L/PWU,zt/PWV),(s0,zt/PWV)],w)
# o2 + OSM 695799455: the curved-building-side wall widens from the flight's foot corner to the building's north tip
OT=Vector((-186.6,46.4,0));OB=Vector((B2.x,B2.y,0))
def OL(t):return OT.lerp(OB,t)
sidewall(lambda t:SP(ws,t),lambda t:SP(0,t),6,-AX)        # lift side: 6 big steps (o2)
sidewall(lambda t:SP(1-ws,t),OL,6,AX)                      # curved-building side: 6 steps (o2)
# lift: a tall clad box, roof corners read on o2 at 11.3 m (1097,867 / 1120,865 / 1129,878 / 1106,879); rises from the plaza
LZ=11.3;cs=[Vector((-162.02,50.35,0)),Vector((-162.77,47.08,0)),Vector((-166.92,48.04,0)),Vector((-166.17,51.31,0))]  # rectangle fitted to o2 roof corners NW(1097,867) F(1120,864) E(1131,877) N(1114,881), <=2 px
lc=sum(cs,Vector())/4;lx,ly=lc.x,lc.y
lo=[P(v,0.0) for v in cs];hi=[P(v,LZ) for v in cs]
for i in range(4):
    j=(i+1)%4;w=((cs[i]+cs[j])/2-lc);w.z=0;w.normalize();face([lo[i],lo[j],hi[j],hi[i]],MKL,[(i,0),(i+1,0),(i+1,LZ/4),(i,LZ/4)],w)
face(hi,MKL,[(v.co.x/4,v.co.y/4) for v in hi],Vector((0,0,1)))
# deck at 6.4 m from the podium edge out to the stair head, west to the curved building's east wall (OSM 695799455,
# x -181.3), south to y 17.5 (Esri: light paving between the podium and that building). Lamps along the head (o2).
D0,D1=50,66
dp=[POD[D0],cs[0],cs[2],T1,T2,Vector((-183.4,45.7,0)),Vector((-181.3,43.2,0)),Vector((-181.3,17.5,0))]+[POD[i] for i in range(D1,D0,-1)]
dp=[Vector((v.x,v.y,0)) for v in dp]
dk=bm.faces.new([P(v,ZT) for v in dp]);dk.normal_update()
if dk.normal.z<0:dk.normal_flip()
for f in bmesh.ops.triangulate(bm,faces=[dk])['faces']:
    f.material_index=MT
    for l in f.loops:l[uv].uv=(l.vert.co.x/TI['terrace_m'],l.vert.co.y/TI['terrace_m'])
for a_,b_ in ((POD[D0],cs[0]),(T2,dp[5]),(dp[5],dp[6]),(dp[6],dp[7]),(dp[7],POD[D1])):
    a_=Vector((a_.x,a_.y,0));b_=Vector((b_.x,b_.y,0));L=(b_-a_).length
    if L<1e-3:continue
    w=(b_-a_).cross(Vector((0,0,-1)))
    face([P(a_,0),P(b_,0),P(b_,ZT),P(a_,ZT)],MPW,[(0,0),(L/PWU,0),(L/PWU,ZT/PWV),(0,ZT/PWV)],w)
DECK_I=set(range(D0,D1))
HEADL=[Vector((-167.94,43.51,0)),Vector((-174.21,44.42,0)),Vector((-180.82,46.09,0))]   # o2 lamp bases at 6.4 m
HEADL=[v-DX*0.5 for v in HEADL]
MGR=mat('grille',0.6)
import math as _m
def _ang(v):return _m.atan2(v.y,v.x)
MPL=mat('plouvre',0.5);MPG=mat('pglass',0.15,0.1)
for op in J.get('openings',[]):
    a,b,h,k=op[:4];z0=op[4] if len(op)>4 else 0.02
    a=Vector((a[0],a[1],0));b=Vector((b[0],b[1],0));t0,t1=sorted([_ang(a),_ang(b)])
    mi={'grille':MGR,'dark':MX,'clad':MK,'plouvre':MPL,'pglass':MPG}[k]
    # walk the podium outline between the two angles (wall follows the curve)
    pts=[a if _ang(a)==t0 else b]+[p for p in POD if t0<_ang(p)<t1]+[b if _ang(a)==t0 else a]
    pts.sort(key=_ang);s0=0.0
    for p,q in zip(pts,pts[1:]):
        wp=Vector((p.x,p.y,0)).normalized()*0.25;wq=Vector((q.x,q.y,0)).normalized()*0.25
        pp=Vector((p.x,p.y,0))+wp;qq=Vector((q.x,q.y,0))+wq;L=(qq-pp).length
        if L<1e-3:continue
        face([P(pp,z0),P(qq,z0),P(qq,h),P(pp,h)],mi,[(s0/4,z0/4),((s0+L)/4,z0/4),((s0+L)/4,h/4),(s0/4,h/4)],wp+wq);s0+=L
# --- o2 rails and lamps: balustrade on the podium edge, lamp posts on the terrace, dark railing at the stair foot
MRL=mat('rail',0.45,0.6);MLP=mat('lamp',0.45,0.6)
mm=bpy.data.materials.new('mesh');mm.use_nodes=True;nt=mm.node_tree;bs=nt.nodes['Principled BSDF'];tx_=nt.nodes.new('ShaderNodeTexImage')
tx_.image=bpy.data.images.load(os.path.join(TX,'mesh.png'));nt.links.new(tx_.outputs['Color'],bs.inputs['Base Color']);nt.links.new(tx_.outputs['Alpha'],bs.inputs['Alpha'])
bs.inputs['Metallic'].default_value=0.5;bs.inputs['Roughness'].default_value=0.5;mm.use_backface_culling=False
try:mm.surface_render_method='BLENDED'
except Exception:pass
me.materials.append(mm);MMS=len(me.materials)-1
def sweep(pts,z0,z1,w,mi,um=1.0,vm=1.0,sa=None):
    # rectangular rail swept along a polyline: shared verts at every bend, so the pieces meet with no gap
    n=len(pts);rs=[]
    for k in range(n):
        a=pts[max(k-1,0)];b=pts[min(k+1,n-1)];t=(b-a);t.z=0;t.normalize();nn=Vector((-t.y,t.x,0))*(w/2)
        rs.append([P(pts[k]+nn,z0),P(pts[k]-nn,z0),P(pts[k]-nn,z1),P(pts[k]+nn,z1)])
    if sa is None:
        sa=[0.0]
        for a,b in zip(pts,pts[1:]):sa.append(sa[-1]+(b-a).length)
    for k in range(n-1):
        for q in range(4):
            r2=(q+1)%4;c0=(rs[k][q].co+rs[k][r2].co)/2;cm=(rs[k][0].co+rs[k][2].co)/2
            za,zb=rs[k][q].co.z,rs[k][r2].co.z
            if abs(za-zb)<1e-6:za,zb=za,za+w   # top/bottom faces: v runs across the width, not smeared
            face([rs[k][q],rs[k][r2],rs[k+1][r2],rs[k+1][q]],mi,[(sa[k]/um,za/vm),(sa[k]/um,zb/vm),(sa[k+1]/um,zb/vm),(sa[k+1]/um,za/vm)],c0-cm)
    for k,sg in ((0,-1),(n-1,1)):
        t=(pts[min(k+1,n-1)]-pts[max(k-1,0)]);t.z=0;face(rs[k],mi,[(0,0),(1,0),(1,1),(0,1)],t.normalized()*sg)
def boxp(c,hw,z0,z1,mi):
    cs=[c+Vector((sx*hw,sy*hw,0)) for sx,sy in((-1,-1),(1,-1),(1,1),(-1,1))];lo=[P(v,z0) for v in cs];hi=[P(v,z1) for v in cs]
    for q in range(4):
        r2=(q+1)%4;face([lo[q],lo[r2],hi[r2],hi[q]],mi,[(0,0),(1,0),(1,1),(0,1)],(cs[q]+cs[r2])/2-c)
    face(hi,mi,[(0,0),(1,0),(1,1),(0,1)],Vector((0,0,1)))
inw=lambda i:-Vector((POD[i].x,POD[i].y,0)).normalized()
# stair head: the balustrade and lamps stop where the stair leaves the terrace (T1..T2) and round the lift
def near_stair(v):
    d=(v-T1);ax=(T2-T1);s=d.dot(ax.normalized());return -1.0<=s<=ax.length+1.0 and abs(d.cross(ax.normalized()).z)<4.0
runs=[];cur=[]
for i in list(range(HE,N))+list(range(0,HS+1)):
    if i in DECK_I:
        if cur:runs.append(cur);cur=[]
        continue
    cur.append(i)
if cur:runs.append(cur)
BZ0,BZ1=6.4,7.5                                            # o2: low see-through mesh balustrade, ~1.1 m, steel top rail
# o2: the west/north edge has the mesh balustrade; past the east pavilion (seg 72 on) it is a solid sandstone parapet
PAR=72
mruns=[];pruns=[]
for run in runs:
    a_=[i for i in run if not (PAR<=i<HS+1)];b_=[i for i in run if PAR<=i<HS+1]
    if a_:mruns.append(a_+([b_[0]] if b_ and a_[-1]==PAR-1 else []))
    if b_:pruns.append(b_)
for run in pruns:
    AR=arcs(POD)   # parapet face shares the podium wall's u, so its block joints run straight up from the wall's
    sweep([POD[i]+inw(i)*0.15 for i in run],6.4,7.5,0.3,MPW,TI['podwall_m'][0],TI['podwall_m'][1],sa=[AR[i] for i in run])
for run in mruns:
    pts=[POD[i]+inw(i)*0.12 for i in run];sP=[0.0]
    for a_,b_ in zip(pts,pts[1:]):sP.append(sP[-1]+(b_-a_).length)
    lo=[P(p,BZ0+0.08) for p in pts];hi=[P(p,BZ1-0.05) for p in pts]
    for k in range(len(pts)-1):
        face([lo[k],lo[k+1],hi[k+1],hi[k]],MMS,[(sP[k],0),(sP[k+1],0),(sP[k+1],1.0),(sP[k],1.0)],-inw(run[k]))
    sweep([Vector((p.x,p.y,0)) for p in pts],BZ1-0.05,BZ1,0.07,MLP)       # top rail
    sweep([Vector((p.x,p.y,0)) for p in pts],BZ0,BZ0+0.08,0.07,MLP)       # foot rail
    nxt=0.0
    for k,p in enumerate(pts):                                             # posts every ~1.8 m and at both ends
        if sP[k]>=nxt or k==len(pts)-1:boxp(p,0.035,BZ0,BZ1,MLP);nxt=sP[k]+1.8
# lamp posts: o2 measures 3.5-3.75 m poles every ~7.2 m, standing just inside the balustrade (first one at seg 29)
LH=3.7;LS=7.2;s0=0.0;sp=[0.0]
order=list(range(HE,N))+list(range(0,HS+1))
for a_,b_ in zip(order,order[1:]):sp.append(sp[-1]+(POD[b_]-POD[a_]).length)
ph=sp[order.index(29)]%LS;t=ph
while t<sp[-1]-1.0:
    k=max(q for q in range(len(sp)) if sp[q]<=t);i=order[k];j=order[min(k+1,len(order)-1)]
    f=(t-sp[k])/max(sp[min(k+1,len(sp)-1)]-sp[k],1e-6);e=POD[i].lerp(POD[j],f);c_=e+inw(i)*0.6
    if i not in DECK_I and j not in DECK_I and (c_-Vector((lx,ly,0))).length>4.0 and not (64<=i<HS+1):   # o2: no lamps east of the pavilion
        cyl(c_.x,c_.y,6.4,6.4+LH,0.07,MLP,8)
        boxp(c_,0.16,6.4+LH,6.4+LH+0.14,MLP)                                # lamp head
    t+=LS
for c_ in HEADL:                                                           # o2: lamps along the stair head
    cyl(c_.x,c_.y,ZT,ZT+LH,0.07,MLP,8);boxp(c_,0.16,ZT+LH,ZT+LH+0.14,MLP)
# o2: handrail down the curved-building edge of the flight, posts every ~2 m
hr=[SP(1-ws*0.5,k/10) for k in range(11)]
for k in range(10):
    a_,b_=hr[k],hr[k+1];za=ZT*(1-k/10)+1.0;zb=ZT*(1-(k+1)/10)+1.0
    tube(Vector((a_.x,a_.y,za)),Vector((b_.x,b_.y,zb)),0.03,MLP)
for k in range(11):
    zt=ZT*(1-k/10);boxp(hr[k],0.03,zt,zt+1.0,MLP)
# dark steel railing on the plaza at the stair foot: posts every ~2.2 m, 1.9 m tall, top/mid/bottom rails (o2 back-projected)
R0=OB;R1=Vector((-178.2,78.9,0));RL=(R1-R0).length;nr=max(1,round(RL/2.2))   # o2 back-projected on the plaza
rp=[R0.lerp(R1,k/nr) for k in range(nr+1)]
for zz in (0.12,0.95,1.86):sweep(rp,zz,zz+0.05,0.05,MRL)
for p in rp:boxp(p,0.035,0.0,1.91,MRL)
bm.to_mesh(me);bm.free()
# ---------- real seats: pan + back per seat (0.44 m wide, 0.5 m pitch, 6 cm gap), on every row of both tiers.
# Aisles and the vomitory stay where the stand texture paints them (bay metres 0 and 7.4, upper tier offset 3.7).
# Colours: paint_tex's tier colours, each seat pushed toward grey-blue or tan, half each (Commons 032, 005).
import numpy as np,random as _rnd
_R=_rnd.Random(7)
_TC={'lo':(216,208,203),'mid':(246,221,191),'up':(178,182,188)};_AX=np.array((0.70,0.76,0.82))-np.array((0.86,0.79,0.66));_AX/=np.linalg.norm(_AX)
def _bx(x0,x1,y0,y1,z0,z1):
    return [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
_BF=[[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]
# pan, back, and two side standards from tread to pan (stadium seats stand on side frames, not a centre stalk)
_T=np.array(_bx(-0.22,0.22,-0.22,0.20,0.40,0.46)+_bx(-0.22,0.22,-0.30,-0.24,0.46,0.86)+_bx(-0.25,-0.21,-0.22,0.04,0.0,0.40)+_bx(0.21,0.25,-0.22,0.04,0.0,0.40))
_TF=[[f+o for f in ff] for o in (0,8,16,24) for ff in _BF]
SEAT=[];SMAT=[];_depth=[];AST=[]
def _seats(Ra,za,Rb,zb,rowsn,tier_of,aoff,vom):
    for r in range(1,rowsn+1):
        t0=(r-1)/rowsn;t1=r/rowsn;pz=za+(zb-za)*t0
        Rf=[Ra[i].lerp(Rb[i],t0) for i in range(N)];Rk=[Ra[i].lerp(Rb[i],t1) for i in range(N)]
        R=[Rf[i]+(Rk[i]-Rf[i])*(1-0.38/max((Rk[i]-Rf[i]).length,0.5)) for i in range(N)];_depth.append((Rk[0]-Rf[0]).length)   # seat back 8 cm off the riser behind
        cs=np.array(arcs(R));sc_=cs[N]/SL[N];tn=tier_of(r-1);bayv=np.array(SU)*14.8
        # gaps along this row (aisles every 7.4 bay metres, the vomitory on the top rows), then each block between two
        # gaps is packed edge to edge, centred, so every block ends on the same radial line in every row
        gaps=[]
        for c in np.arange(aoff-7.4,bayv[-1]+7.5,7.4):gaps.append((np.interp(c-0.6,bayv,cs),np.interp(c+0.6,bayv,cs)))
        if r>1:   # aisle stairs: a half step on each row's tread (the rows rise ~0.6 m, so a real aisle has two steps per row)
            for c in np.arange(aoff,bayv[-1]-0.1,7.4):
                s=float(np.interp(c,bayv,cs));i=int(min(N-1,max(0,np.searchsorted(cs,s,side='right')-1)));f=(s-cs[i])/max(cs[i+1]-cs[i],1e-9);j=(i+1)%N
                AST.append((Rf[i].lerp(Rf[j],f),Rk[i].lerp(Rk[j],f),pz,(zb-za)/rowsn,0.6*sc_))
        if vom and pz+0.01>=10.2*ZK:
            for b0 in np.arange(0,bayv[-1],14.8):gaps.append((np.interp(b0+3.2,bayv,cs),np.interp(b0+5.0,bayv,cs)))
        gaps=sorted((max(0.0,a),min(cs[N],b)) for a,b in gaps if b>0 and a<cs[N])
        edges=[0.0]+[x for g in gaps for x in g]+[cs[N]]
        for a,b in zip(edges[0::2],edges[1::2]):
            L=b-a-0.04;n=int((L+0.06)//0.5)
            for k in range(n):
                s=(a+b)/2+(k-(n-1)/2)*0.5;i=int(min(N-1,max(0,np.searchsorted(cs,s,side='right')-1)));f=(s-cs[i])/max(cs[i+1]-cs[i],1e-9)
                j=(i+1)%N;p=R[i].lerp(R[j],f);fw=-(p-oc);fw.z=0;fw.normalize()
                SEAT.append((p.x,p.y,pz,fw.x,fw.y))
                c=np.array(_TC[tn])/255*(1.0 if (r-1)%2 else 0.96)+(1 if _R.random()<0.5 else -1)*0.075*_R.uniform(0.7,1.0)*_AX
                SMAT.append(c)
_seats(L0,1.6*ZK,L1,12.0*ZK,24,lambda r:'lo' if 1.6+10.4*(r+1)/24<=6.4+0.01 else 'mid',0.0,True)
_seats(L1,15.0*ZK,L3,31.5*ZK,30,lambda r:'up',3.7,False)
print('seats',len(SEAT),'tread depth min/max %.2f %.2f'%(min(_depth),max(_depth)))
# drop any seat whose spot is taken by other structure (roof columns, walls): ray down from 1.2 m over the pan's
# back, middle and front must land on the seat's own tread
from mathutils.bvhtree import BVHTree
_bv=BVHTree.FromObject(ob,bpy.context.evaluated_depsgraph_get());_keep=[]
for x,y,z,fx,fy in SEAT:
    ok=True
    for d in (-0.28,0.0,0.18):
        for sx in (-0.2,0.2):
            q=Vector((x+fx*d+fy*sx,y+fy*d-fx*sx,z+1.2));h=_bv.ray_cast(q,Vector((0,0,-1)),2.0)
            if h[0] is None or abs(h[0].z-z)>0.02:ok=False
    _keep.append(ok)
print('seats dropped (spot taken)',_keep.count(False))
SEAT=[s for s,k in zip(SEAT,_keep) if k];SMAT=[s for s,k in zip(SMAT,_keep) if k]
SE=np.array(SEAT,float);SC=np.clip(np.array(SMAT),0,1)
# six plastics: each tier colour pushed grey-blue or tan (mean of its seats), so the export stays plain materials
_TL=[];_TLc=[]
for tn,base in _TC.items():
    b=np.array(base)/255
    for sgn in (1,-1):_TL.append((tn,sgn));_TLc.append(b+sgn*0.075*0.85*_AX)
_TLc=np.clip(np.array(_TLc),0,1)
mi=np.argmin(((SC[:,None,:]-_TLc[None,:,:])**2).sum(2),1)
fwd=np.c_[SE[:,3:5],np.zeros(len(SE))];side=np.c_[fwd[:,1],-fwd[:,0],np.zeros(len(SE))]
V=(SE[:,None,:3]+_T[None,:,0,None]*side[:,None,:]+_T[None,:,1,None]*fwd[:,None,:]+_T[None,:,2,None]*np.array([0,0,1.0])).reshape(-1,3)
# block ends: a seat with no neighbour 0.5 m to one side gets that leg moved in 3 cm, flush with the pan
import mathutils as _mu
_kd=_mu.kdtree.KDTree(len(SE))
for i,p in enumerate(SE[:,:3]):_kd.insert(p,i)
_kd.balance();V=V.reshape(len(SE),len(_T),3)
for i in range(len(SE)):
    for sgn,box in ((-1,2),(1,3)):
        q=SE[i,:3]+sgn*0.5*side[i]
        if _kd.find(q)[2]>0.1:V[i,box*8:box*8+8]-=sgn*0.03*side[i]
V=V.reshape(-1,3)
nT=len(_T);F=(np.array(_TF)[None,:,:]+(np.arange(len(SE))*nT)[:,None,None]).reshape(-1,4)
sme=bpy.data.meshes.new('seats3d');sme.vertices.add(len(V));sme.vertices.foreach_set('co',V.ravel())
sme.loops.add(F.size);sme.loops.foreach_set('vertex_index',F.ravel());sme.polygons.add(len(F))
sme.polygons.foreach_set('loop_start',np.arange(0,F.size,4));sme.polygons.foreach_set('material_index',np.where(np.tile(np.arange(len(_TF))>=len(_TF)//2,len(SE)),len(_TL),np.repeat(mi,len(_TF))))
sme.update();sme.validate()
for (tn,sgn),c in zip(_TL,_TLc):
    sm=bpy.data.materials.new('seat_%s_%s'%(tn,'blue' if sgn>0 else 'tan'));sm.use_nodes=True;sb=sm.node_tree.nodes['Principled BSDF']
    sb.inputs['Base Color'].default_value=(*[float(x)**2.2 for x in c],1);sb.inputs['Roughness'].default_value=0.55;sme.materials.append(sm)
sm=bpy.data.materials.new('seat_legs_steel');sm.use_nodes=True;sb=sm.node_tree.nodes['Principled BSDF'];sb.inputs['Base Color'].default_value=(0.24,0.25,0.26,1);sb.inputs['Metallic'].default_value=0.6;sb.inputs['Roughness'].default_value=0.45;sme.materials.append(sm)
sob=bpy.data.objects.new('seats3d',sme);bpy.context.scene.collection.objects.link(sob)
# aisle half steps: box from mid-tread to the riser, half a riser high, 1.2 m wide (bay scale), concrete
AV=[];AF=[]
for fr,bk,z0,h,w in AST:
    fw=bk-fr;fw.z=0;d=fw.length;fw.normalize();sd=Vector((fw.y,-fw.x,0));m=fr+fw*(d*0.5)
    o=len(AV);AV+=[tuple(v) for v in _bx(-w,w,0,d*0.5,0,h*0.5)]
    for k in range(o,o+8):
        x,y,z=AV[k];q=m+sd*x+fw*y;AV[k]=(q.x,q.y,z0+z)
    AF+=[[f+o for f in ff] for ff in _BF]
ame=bpy.data.meshes.new('aisle_steps');ame.from_pydata(AV,[],AF);ame.update()
am=bpy.data.materials.new('aisle_step');am.use_nodes=True;ab=am.node_tree.nodes['Principled BSDF']
ab.inputs['Base Color'].default_value=(*[(c/255)**2.2 for c in (196,190,182)],1);ab.inputs['Roughness'].default_value=0.85;ame.materials.append(am)
bpy.context.scene.collection.objects.link(bpy.data.objects.new('aisle_steps',ame));print('aisle steps',len(AST))
json.dump({'n':len(SEAT),'seats':[[round(float(x),3) for x in s] for s in SEAT[::50]]},open(os.path.join(here,'seats_sample.json'),'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=os.path.abspath(dst),export_format='GLB')
print('tris',sum(len(p.vertices)-2 for p in me.polygons))
