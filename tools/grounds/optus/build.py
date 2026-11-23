# Optus Stadium exterior from measured geometry (geom.json). Usage: python3 build.py -- OUTGLB OUTBLEND (pip bpy)
# The model's source, moved here from .claude/review/optus/scripts/build.py (#1867) for the rebuild to the MCG standard
# (docs/MCG_STANDARD.md). It still reads that folder's geom.json and hand-painted tex/. Changed for the rebuild:
#  - the bronze ribbon's top (facade.json `top`), measured from 12 Google Earth facade views: tall north and south,
#    dipping to 22 m over the east entrance's tall glass, 29 m in the west (#1867 had it low from south-east to west);
#  - the bronze bows out 1.2 m at mid-height, as it does;
#  - the name signs where the real ones are (facade.json `signs`), each a 32 m drop from the bronze's top, letters near it;
#  - the export leaves the 3D seats out (they ship as seats_*.bin, checked by tools/grounds/seat_check.gd).
import bpy,bmesh,sys,math,json,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector
A=sys.argv[sys.argv.index('--')+1:];dst,blend=A[0],A[1]
me_dir=os.path.dirname(os.path.abspath(__file__))
here=os.path.join(me_dir,'..','..','..','.claude','review','optus','scripts')
J=json.load(open(os.path.join(here,'geom.json')));TX=os.path.join(here,'..','tex');TI=json.load(open(os.path.join(TX,'info.json')));BH=TI['bronze_h_m'];GH=30.0   # glass UV height: one 30 m drop (bronze.py draws the glass), no repeat over the east dip
FJ=json.load(open(os.path.join(me_dir,'facade.json')))
import numpy as _np0
bpy.ops.wm.read_factory_settings(use_empty=True)
me=bpy.data.meshes.new('optus');ob=bpy.data.objects.new('optus',me);bpy.context.scene.collection.objects.link(ob)
def mat(name,rough=0.8,metal=0.0,mr=None):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(os.path.join(TX,name+'.png'))
    nt.links.new(t.outputs['Color'],b.inputs['Base Color']);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    if mr:   # a metal-roughness map (glTF: green roughness, blue metalness), bronze.py
        q=nt.nodes.new('ShaderNodeTexImage');q.image=bpy.data.images.load(os.path.join(TX,mr+'.png'));q.image.colorspace_settings.name='Non-Color'
        sp=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(q.outputs['Color'],sp.inputs['Color'])
        nt.links.new(sp.outputs['Green'],b.inputs['Roughness']);nt.links.new(sp.outputs['Blue'],b.inputs['Metallic'])
    m.use_backface_culling=False;me.materials.append(m);return len(me.materials)-1
MB=mat('bronze',0.55,0.3,'bronze_mr');MG=mat('glass',0.3,0.0);MS=mat('seats');MR=mat('roof',0.6);MW=mat('white',0.5);MU=mat('under')
MC=mat('concrete');MT=mat('terrace');MP=mat('plaza');MD=mat('deck');MK=mat('clad',0.4,0.4);MKL=mat('clad',0.85,0.0);MX=mat('dark')
MPW=mat('podwall');MLV=mat('louvre',0.5);MBN=mat('bench');MAI=mat('aisle');MRS=mat('riser')
bm=bmesh.new();uv=bm.loops.layers.uv.new('UVMap');LEDGE=bm.faces.layers.int.new('ledge')   # fin ledges: shaded as the facade (below)

import shape as SH
V2=lambda p:Vector((p[0],p[1],0))
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
def tube(a,b,r,mi):
    d=(b-a);L=d.length
    if L<1e-3:return
    d.normalize();up=Vector((0,0,1)) if abs(d.z)<0.9 else Vector((1,0,0));x=d.cross(up).normalized()*r;y=d.cross(x).normalized()*r
    ca=[bm.verts.new(a+x*sx+y*sy) for sx,sy in((1,1),(-1,1),(-1,-1),(1,-1))];cb=[bm.verts.new(b+x*sx+y*sy) for sx,sy in((1,1),(-1,1),(-1,-1),(1,-1))]
    for q in range(4):
        r2=(q+1)%4;w=((ca[q].co+ca[r2].co)/2-a).normalized()
        face([ca[q],ca[r2],cb[r2],cb[q]],mi,[(q/4,0),((q+1)/4,0),((q+1)/4,L/4),(q/4,L/4)],w)
def cyl(cx,cy,z0,z1,r,mi,n=12):
    ring=[(cx+r*math.cos(2*math.pi*k/n),cy+r*math.sin(2*math.pi*k/n)) for k in range(n)]
    for k in range(n):
        a_,b_=ring[k],ring[(k+1)%n];w=Vector(((a_[0]+b_[0])/2-cx,(a_[1]+b_[1])/2-cy,0)).normalized()
        face([bm.verts.new((a_[0],a_[1],z0)),bm.verts.new((b_[0],b_[1],z0)),bm.verts.new((b_[0],b_[1],z1)),bm.verts.new((a_[0],a_[1],z1))],mi,[(k/n,0),((k+1)/n,0),((k+1)/n,1),(k/n,1)],w)
MST=mat('steel',0.6,0.0)   # steel.png (bronze.py): light grey; metallic picked up the sky and turned them blue
# ---------------------------------------------------------------------------------------------------------------
# The plan (2026-11-22 rebuild): every ring is an exact offset of ONE smooth curve, the roof's outer edge as traced
# from six calibrated Google Earth nadir shots (shape.py, fit 0.09 m RMS). The ring is cut at the 50 trusses
# (LSAA: fifty cantilevers; found on Google Earth square to the edge) and each bay into K equal arcs, so the
# trusses, the bays and every ring's vertices line up radially. No vertex comes from a hand-traced polygon.
# Heights: the roof edge from Google Earth's own height readout (41-43 m; published "42m-high"), the facade from
# 1,080 Google Earth hover points on 12 oblique views (survey/fac_coef.npy: offset from the edge by height and
# bearing, 0.55 m RMS), the bronze's top from 60 readings off those views (facade.json).
NB=SH.NBAY;K=16;N=NB*K
_ss=[];_ts=[float(SH.truss_s(b)) for b in range(NB)]+[float(SH.truss_s(0))+SH.PERIMETER]
for b in range(NB):
    for k in range(K):_ss.append(_ts[b]+(_ts[b+1]-_ts[b])*k/K)
TH=[float(SH.th_at_s(s)) for s in _ss]
EP=SH.edge_xy(_np0.array(TH));EN=SH.edge_normal(_np0.array(TH))
CP=[(90.0-math.degrees(t))%360.0 for t in TH]   # compass bearing of each vertex
def CI(c):
    """index of the vertex nearest compass bearing c"""
    d=[min(abs(x-c),360-abs(x-c)) for x in CP];return int(_np0.argmin(d))
def ARC(c0,c1):
    """vertex indices from bearing c0 round to c1, in index order (bearing falling, clockwise seen from above)"""
    i=CI(c0);j=CI(c1);out=[i]
    while i!=j:i=(i+1)%N;out.append(i)
    return out
def CIN(c,a,b):
    """bearing c inside the clockwise arc from a down to b (a > b in falling order)"""
    return ((a-c)%360.0)<=((a-b)%360.0)
def RING(d):
    """ring of N points d(i) m outside the roof edge along its normal (negative: inside)"""
    return [Vector((EP[i][0]+d(i)*EN[i][0],EP[i][1]+d(i)*EN[i][1],0.0)) for i in range(N)]
def per(table):
    """periodic linear interpolation of {bearing: value}"""
    k=_np0.array(sorted((float(a),float(v)) for a,v in table.items()));x=_np0.concatenate([k[:,0]-360,k[:,0],k[:,0]+360]);y=_np0.tile(k[:,1],3)
    return lambda c:float(_np0.interp(c,x,y))
# roof edge height and the facade offset surface
ZEDGE=[float(SH.edge_z(t)) for t in TH]
ZF_=[z+0.2 for z in ZEDGE];ZS_=[z-1.2 for z in ZF_];ZGT_=[z-3.4 for z in ZS_]   # fascia top, soffit, glass head
_FC=_np0.load(os.path.join(me_dir,'survey','fac_coef.npy'));_FK=_np0.array([0,5,9,13,17,21,25,29,33,37,41.0])
def FAC(i,h):
    t=TH[i];hat=_np0.clip(1-abs(h-_FK)/4.0,0,None);fs=[1.0]
    for n in range(1,4):fs+=[math.cos(n*t),math.sin(n*t)]
    return float(min(6.0,max(-2.0,(hat[:,None]*_np0.array(fs)[None,:]).ravel()@_FC)))
def FP(i,h,dd=0.0):
    d=FAC(i,h)+dd;return Vector((EP[i][0]+d*EN[i][0],EP[i][1]+d*EN[i][1],h))
RF=RING(lambda i:0.0)
# the bronze's top (facade.json `top`, 60 Google Earth readings) and foot
_top=per(FJ['top']);HB=[_top(c) for c in CP]
# the bronze's foot (Google Earth facade views): low on the street side north and north-east, lifted over the
# east lobby's tall glass, over a dark glazed storey on the podium west and south
_zv=per({0:6.0,30:6.5,46:7.0,100:7.5,130:8.5,160:9.0,190:10.0,220:10.5,250:11.0,280:13.0,300:13.0,320:10.0,340:7.0})
_lb=FJ['lobby'];LOB=[max(0.0,min(1.0,(_lb['half_deg']+_lb['ramp_deg']-min(abs(c-_lb['centre']),360-abs(c-_lb['centre'])))/_lb['ramp_deg'])) for c in CP]
ZV=[_zv(c)+(_lb['top_m']-_zv(c))*LOB[i] for i,c in enumerate(CP)]
# podium: deck edge and height by bearing from 784 Google Earth hovers (survey/podium.json): ~7 m from the
# south-east (100) round the south and west, 6 m north-west, falling to 3.5 m at 340; the north and east stand at
# street level
PJ=json.load(open(os.path.join(me_dir,'survey','podium.json')))
PODB,PODA=float(PJ['arc'][0]),float(PJ['arc'][1])
_pe=per({k:v[0] for k,v in PJ['edge'].items()});_zd=per({k:v[1] for k,v in PJ['edge'].items()})
ZD=[_zd(c) if CIN(c,PODA,PODB) else 0.0 for c in CP]
POD=RING(lambda i:_pe(CP[i]))
INPOD=[CIN(c,PODA,PODB) for c in CP]
NAMES=FJ['signs']
def _sign_at(c,w):
    i0=CI(c);return (i0-w//2)%N,(i0-w//2)%N+w
SG={'sign_a_%d'%k:_sign_at(float(c),FJ['sign_segments']*2) for k,c in enumerate(NAMES)}
TI['signs']=SG
c=lambda z:(lambda i:z)
MEN=mat('entrance',0.12,0.1);MCO=mat('column',0.5);MXG=mat('storey',0.2,0.1);SMA=mat('sign_a',0.55,0.3,'sign_a_mr')
def quad_strip(A,B,mi,uvA,uvB,want,sel=None):
    """faces between two rows of verts A[i], B[i] (closed ring)"""
    for i in range(N):
        if sel and not sel(i):continue
        j=(i+1)%N;face([A[i],A[j],B[j],B[i]],mi,[uvA(i),uvA(j,True),uvB(j,True),uvB(i)],want(i))
OUT=lambda i:Vector((EN[i][0]+EN[(i+1)%N][0],EN[i][1]+EN[(i+1)%N][1],0)).normalized()
sF=arcs([FP(i,20.0) for i in range(N)]);BAY2=2*sF[N]/NB
# --- podium: wall from the ground to the deck, deck out to the facade's foot
podsel=lambda i:INPOD[i] and INPOD[(i+1)%N]
wall(POD,c(0.0),lambda i:ZD[i],MPW,TI['podwall_m'][0],TI['podwall_m'][1],sel=podsel)
flat(POD,lambda i:ZD[i],[FP(i,ZD[i]) for i in range(N)],lambda i:ZD[i],MT,TI['terrace_m'],sel=podsel)
for e in (CI(PODA),CI(PODB)):   # end walls where the podium stops
    t=Vector((-EN[e][1],EN[e][0],0));a_=POD[e];b_=FP(e,0.0)
    face([P(a_,0),P(b_,0),P(b_,ZD[e]),P(a_,ZD[e])],MPW,[(0,0),(1,0),(1,1.6),(0,1.6)],t)
# --- the storey under the bronze: dark glazing with white posts from the deck (or street) to the bronze's foot,
# set 0.6 m back; on the east lobby the tall entrance glass, 1.1 m back (Google Earth hover: -1.1 m)
BASE=[ZD[i] for i in range(N)]
GLb=[P(FP(i,BASE[i],-0.6-0.5*LOB[i]),BASE[i]) for i in range(N)]
GLt=[P(FP(i,ZV[i],-0.6-0.5*LOB[i]),ZV[i]) for i in range(N)]
for i in range(N):
    j=(i+1)%N;mi=MEN if LOB[i]>0.5 else MXG;h0,h1=(16.0,0.0) if mi==MEN else (6.0,0.0)
    face([GLb[i],GLb[j],GLt[j],GLt[i]],mi,[(sF[i]/BAY2,BASE[i]/h0),(sF[i+1]/BAY2,BASE[j]/h0),(sF[i+1]/BAY2,ZV[j]/h0),(sF[i]/BAY2,ZV[i]/h0)],OUT(i))
# soffit under the bronze's foot, from the storey glass out to the bronze
BF=[P(FP(i,ZV[i]),ZV[i]) for i in range(N)]
for i in range(N):
    j=(i+1)%N;face([GLt[i],GLt[j],BF[j],BF[i]],MX,[(0,0),(1,0),(1,1),(0,1)],Vector((0,0,-1)))
for i in range(0,N,K//2):   # posts every half bay in the storey (Google Earth: white posts under the bronze)
    o_=-0.6-0.5*LOB[i]+(0.22 if LOB[i]<0.5 else 0.3)   # in front of the glass all the way up: the facade leans
    tube(FP(i,BASE[i],o_),FP(i,ZV[i],o_),0.18 if LOB[i]<0.5 else 0.25,MCO)
# --- bronze: BROWS rows from its foot to its top, each vertex on the measured facade surface
BROWS=14
BR=[[P(FP(i,ZV[i]+(HB[i]-ZV[i])*k/BROWS),ZV[i]+(HB[i]-ZV[i])*k/BROWS) for i in range(N)] for k in range(BROWS+1)]
BR[0]=BF
_inside=lambda a0,a1,i:(a0<=i<a1) or (a0<=i+N<a1)
# The bronze's horizontal anodised fins, as geometry: one fin every FIN_P down from the bronze's top (the texture's
# rows, bronze.py ROWS), each a blade leaning FIN_D out to its top edge with a level ledge back to the wall, so every
# fin throws its own shadow line. Every second facade vertex (3.1 m chords, 9 mm sag on the drum), plus the signs' ends.
FIN_P=BH/66;FIN_D=0.07
_fi=sorted(set(range(0,N,2))|{a%N for ab in SG.values() for a in ab})
NFR=int(math.ceil(max(HB[i]-ZV[i] for i in range(N))/FIN_P))+1
_fz=lambda m,i:max(ZV[i],HB[i]-m*FIN_P)
FIN=[{i:(P(FP(i,_fz(m,i)),_fz(m,i)),P(FP(i,_fz(m,i),FIN_D),_fz(m,i))) for i in _fi} for m in range(NFR+1)]
def _fuv(i,z,sg):
    if not sg:return (sF[i]/BAY2 if i or sg else 0.0,1-(HB[i]-z)/BH)
    a0,a1=SG[sg];ii=i if i>=a0 else i+N;return ((ii-a0)/(a1-a0),1-(HB[i]-z)/FJ['sign_drop_m'])
for q in range(len(_fi)):
    i=_fi[q];j=_fi[(q+1)%len(_fi)];jn=j if j>i else N   # arclength index for the wrap
    sg=[k for k,(a0,a1) in SG.items() if _inside(a0,a1,i)];sg=sg[0] if sg else None
    w=OUT(i);mi=SMA if sg else MB
    def uv_(ix,z):
        u,v=_fuv(ix%N,z,sg)
        if not sg and ix==N:u=sF[N]/BAY2
        return (u,v)
    for m in range(NFR):
        zli,zlj,zhi,zhj=_fz(m+1,i),_fz(m+1,j),_fz(m,i),_fz(m,j)
        if zhi-zli<1e-4 and zhj-zlj<1e-4:continue
        lo,hi=FIN[m+1],FIN[m]
        face([lo[i][0],lo[j][0],hi[j][1],hi[i][1]],mi,[uv_(i,zli),uv_(jn,zlj),uv_(jn,zhj),uv_(i,zhi)],w)
        # The ledge's UVs sit inside its own fin's row (not on the row boundary, where half its pixels took the row
        # above), with a real height so the texture's mip level is chosen right.
        _l=face([hi[i][1],hi[j][1],hi[j][0],hi[i][0]],mi,[uv_(i,zhi-0.06*FIN_P),uv_(jn,zhj-0.06*FIN_P),uv_(jn,zhj-0.25*FIN_P),uv_(i,zhi-0.25*FIN_P)],Vector((0,0,1)))
        _l[LEDGE]=i+1   # which facade segment, for its outward normal
# --- glass band from the bronze's top to the glass head, on the same surface
GROWS=10
GR=[BR[BROWS]]+[[P(FP(i,HB[i]+(ZGT_[i]-HB[i])*k/GROWS),HB[i]+(ZGT_[i]-HB[i])*k/GROWS) for i in range(N)] for k in range(1,GROWS+1)]
sGL=arcs([FP(i,30.0) for i in range(N)]);BAYG=2*sGL[N]/NB
for i in range(N):
    j=(i+1)%N;w=OUT(i)
    for k in range(GROWS):
        za=lambda q,kk:HB[q]+(ZGT_[q]-HB[q])*kk/GROWS
        face([GR[k][i],GR[k][j],GR[k+1][j],GR[k+1][i]],MG,[(sGL[i]/BAYG,1-(ZS_[i]-za(i,k))/GH),(sGL[i+1]/BAYG,1-(ZS_[j]-za(j,k))/GH),(sGL[i+1]/BAYG,1-(ZS_[j]-za(j,k+1))/GH),(sGL[i]/BAYG,1-(ZS_[i]-za(i,k+1))/GH)],w)
# --- the dark open strip under the fascia: glass head ledge back to a dark wall 5 m behind the roof's edge,
# white posts at the trusses (Google Earth: slim white posts in a dark strip between the glass and the fascia).
# Depth: 53 oblique hover hits at 37-41 m inside the strip read d -2.5 to -7.3 m, median -4.8 (2026-11-22).
REC=RING(lambda i:-5.0)
ga=GR[GROWS];ra=[P(REC[i],ZGT_[i]) for i in range(N)];rb=[P(REC[i],ZS_[i]) for i in range(N)];fa=[P(RF[i],ZS_[i]) for i in range(N)]
for i in range(N):
    j=(i+1)%N
    face([ga[i],ga[j],ra[j],ra[i]],MW,[(0,0),(1,0),(1,1),(0,1)],Vector((0,0,1)))
    face([ra[i],ra[j],rb[j],rb[i]],MX,[(0,0),(1,0),(1,1),(0,1)],OUT(i))
    face([rb[i],rb[j],fa[j],fa[i]],MX,[(0,0),(1,0),(1,1),(0,1)],Vector((0,0,-1)))
for b in range(NB):
    i=b*K;q=FP(i,ZGT_[i],-0.2);q2=Vector((EP[i][0]-0.4*EN[i][0],EP[i][1]-0.4*EN[i][1],0))
    tube(Vector((q.x,q.y,ZGT_[i])),Vector((q2.x,q2.y,ZS_[i])),0.22,MW)
wall(RF,lambda i:ZS_[i],lambda i:ZF_[i],MW,1e6,1e6)
# --- glazing frames as geometry; the glass textures (bronze.py glass, storey, entrance) carry only the glass's tone.
# Glass band over the bronze: a white head rail under the glass head, a pale louvre band at the foot of each 2.2 m
# floor and mullions every 1.63 m (Google Earth 060/000), all standing proud of the glass. Storey under the bronze:
# a head rail and mullions every 2.0 m in front of the dark glass. East lobby: transoms every 2.5 m.
import bisect as _bis
def _mullions(zlo,zhi,off,step,r,mi,sel=lambda i:True,nseg=3):
    t=step/2
    while t<sF[N]:
        i=min(N-1,_bis.bisect(sF,t)-1);j=(i+1)%N;f=(t-sF[i])/max(1e-9,sF[i+1]-sF[i])
        if sel(i):
            pts=[]
            for q in range(nseg+1):
                z=(zlo(i)+(zhi(i)-zlo(i))*q/nseg)*(1-f)+(zlo(j)+(zhi(j)-zlo(j))*q/nseg)*f
                pts.append(FP(i,z,off(i)).lerp(FP(j,z,off(j)),f))
            for a_,b_ in zip(pts,pts[1:]):tube(a_,b_,r,mi)
        t+=step
def _hband(z0f,z1f,back,front,mi,sel):
    """A band between z0f(i) and z1f(i) standing from offset back(i) out to front(i): face, top and underside."""
    fb=[P(FP(i,z0f(i),front(i)),z0f(i)) for i in range(N)];ft=[P(FP(i,z1f(i),front(i)),z1f(i)) for i in range(N)]
    bb=[P(FP(i,z0f(i),back(i)),z0f(i)) for i in range(N)];bt=[P(FP(i,z1f(i),back(i)),z1f(i)) for i in range(N)]
    for i in range(N):
        j=(i+1)%N
        if not sel(i):continue
        face([fb[i],fb[j],ft[j],ft[i]],mi,[(0,0),(1,0),(1,1),(0,1)],OUT(i))
        face([ft[i],ft[j],bt[j],bt[i]],mi,[(0,0),(1,0),(1,1),(0,1)],Vector((0,0,1)))
        face([bb[i],bb[j],fb[j],fb[i]],mi,[(0,0),(1,0),(1,1),(0,1)],Vector((0,0,-1)))
_g0=lambda i:0.0;_gf=lambda i:0.12
_hband(lambda i:ZGT_[i]-0.4,lambda i:ZGT_[i],_g0,_gf,MW,lambda i:True)                 # head rail
for m in range(1,12):                                                                   # louvre band at each floor foot
    zf=lambda i,m=m:ZGT_[i]-0.4-2.2*m
    _hband(zf,lambda i,m=m:ZGT_[i]-0.4-2.2*m+0.44,_g0,_gf,MST,lambda i,m=m:zf(i)>HB[i]+0.15 and zf((i+1)%N)>HB[(i+1)%N]+0.15)
_mullions(lambda i:HB[i],lambda i:ZGT_[i]-0.4,lambda i:0.05,1.625,0.05,MST)
_st=lambda i:LOB[i]<=0.5 and LOB[(i+1)%N]<=0.5
_sb=lambda i:-0.6-0.5*LOB[i]
_hband(lambda i:ZV[i]-0.25,lambda i:ZV[i],_sb,lambda i:_sb(i)+0.1,MW,_st)              # storey head rail
_mullions(lambda i:BASE[i],lambda i:ZV[i]-0.25,lambda i:_sb(i)+0.05,2.03,0.04,MST,_st,1)
for m in range(1,7):                                                                    # east lobby transoms
    _hband(lambda i,m=m:2.5*m-0.06,lambda i,m=m:2.5*m+0.06,_sb,lambda i:_sb(i)+0.1,MW,
           lambda i,m=m:not _st(i) and 2.5*m+0.1<ZV[i] and 2.5*m+0.1<ZV[(i+1)%N] and 2.5*m>BASE[i]+0.1)
# --- west canopy (Google Earth views 180/210: a white ledge at ~25 m over a terrace, bearings 238-280)
# --- the west bronze volume (survey/west_volume.json, 720 Google Earth hovers): bronze face out to 16 m from the roof
# edge between 12.5 m and its flat top at 24.2 m, white canopy round the top edge, a glazed storey 2.5 m back below
WJ=json.load(open(os.path.join(me_dir,'survey','west_volume.json')))
_wf=per({k:v for k,v in WJ['face'].items()});_wk=sorted(float(k) for k in WJ['face'])
_wsi=per({k:v for k,v in WJ['storey_in_by_bearing'].items()})   # the storey's set-back, measured by bearing
ZW0,ZW1=WJ['z_storey'],WJ['z_top']
WSEL=[CIN(c,_wk[-1],_wk[0]) and _wf(c)>FAC(i,18.0)+0.3 for i,c in enumerate(CP)]
WV=[i for i in ARC(_wk[-1],_wk[0]) if WSEL[i]]
def _wp(i,d,z):return Vector((EP[i][0]+d*EN[i][0],EP[i][1]+d*EN[i][1],z))
_ws=_np0.concatenate([[0.0],_np0.cumsum([(_wp(a,_wf(CP[a]),0)-_wp(b,_wf(CP[b]),0)).length for a,b in zip(WV,WV[1:])])])
for k,(a,b) in enumerate(zip(WV,WV[1:])):
    da,db=_wf(CP[a]),_wf(CP[b]);ua,ub=_ws[k]/BAY2,_ws[k+1]/BAY2   # bronze texture at the facade's scale (BAY2 wide, BH high)
    n_=OUT(a)
    face([P(_wp(a,da,0),ZW0),P(_wp(b,db,0),ZW0),P(_wp(b,db,0),ZW1),P(_wp(a,da,0),ZW1)],MB,[(ua,0),(ub,0),(ub,(ZW1-ZW0)/BH),(ua,(ZW1-ZW0)/BH)],n_)
    sa,sb=_wsi(CP[a]),_wsi(CP[b]);za,zb=ZD[a],ZD[b]
    face([P(_wp(a,da-sa,0),za),P(_wp(b,db-sb,0),zb),P(_wp(b,db-sb,0),ZW0),P(_wp(a,da-sa,0),ZW0)],MXG,[(ua,0),(ub,0),(ub,1),(ua,1)],n_)
    face([P(_wp(a,da-sa,0),ZW0),P(_wp(b,db-sb,0),ZW0),P(_wp(b,db,0),ZW0),P(_wp(a,da,0),ZW0)],MX,[(0,0),(1,0),(1,1),(0,1)],Vector((0,0,-1)))
    fa,fb=FP(a,ZW1),FP(b,ZW1)
    face([P(fa,ZW1),P(_wp(a,da,0),ZW1),P(_wp(b,db,0),ZW1),P(fb,ZW1)],MD,[(0,0),(1,0),(1,1),(0,1)],Vector((0,0,1)))
    co,ct=WJ['canopy_out'],WJ['canopy_t']
    A0,B0,A1,B1=_wp(a,da-0.3,0),_wp(b,db-0.3,0),_wp(a,da+co,0),_wp(b,db+co,0)
    face([P(A0,ZW1+ct),P(B0,ZW1+ct),P(B1,ZW1+ct),P(A1,ZW1+ct)],MW,[(0,0),(1,0),(1,1),(0,1)],Vector((0,0,1)))
    face([P(A1,ZW1-0.1),P(B1,ZW1-0.1),P(B0,ZW1-0.1),P(A0,ZW1-0.1)],MW,[(0,0),(1,0),(1,1),(0,1)],Vector((0,0,-1)))
    face([P(A1,ZW1-0.1),P(B1,ZW1-0.1),P(B1,ZW1+ct),P(A1,ZW1+ct)],MW,[(0,0),(1,0),(1,1),(0,1)],n_)
for e in (WV[0],WV[-1]):   # end returns back to the facade
    d=_wf(CP[e]);f0=FAC(e,18.0);t=Vector((-EN[e][1],EN[e][0],0))
    face([P(_wp(e,f0,0),ZW0),P(_wp(e,d,0),ZW0),P(_wp(e,d,0),ZW1),P(_wp(e,f0,0),ZW1)],MB,[(0,0),(1,0),(1,1),(0,1)],t)
print('west volume',len(WV),'vertices, bearings %.1f-%.1f'%(CP[WV[0]],CP[WV[-1]]))
# --- the two riverside pavilions on the west podium (survey/pavilions.json): outlines traced straight down off Google
# Earth and checked against 180 roof hovers, faces standing vertical from 0 m (river-side hovers), a white roof rim,
# storeys and openings from the low river-side views. Every opening is cut back into the wall, not painted.
PVJ=json.load(open(os.path.join(me_dir,'survey','pavilions.json')))
MPVG=mat('pav_glass',0.12,0.2);MPVD=mat('pav_dark',0.7);MPVB=mat('pav_base',0.8)   # flat colours: every frame and slot is geometry
# the roofs: pale blue-grey with orange paint (Google Earth straight down, lit: roof 126,147,153, paint 177,123,90)
MPVR=mat('pav_roof',0.85);MPVP=mat('pav_paint',0.8)
def _chaikin(L,n=3):
    for _ in range(n):
        M=[]
        for k in range(len(L)):
            a=L[k];b=L[(k+1)%len(L)]
            M+=[(0.75*a[0]+0.25*b[0],0.75*a[1]+0.25*b[1]),(0.25*a[0]+0.75*b[0],0.25*a[1]+0.75*b[1])]
        L=M
    return L
def _resample(L,step,cuts=()):
    """Split every segment longer than step into equal pieces, and add a vertex at each arclength in cuts."""
    out=[]
    for k in range(len(L)):
        a=L[k];b=L[(k+1)%len(L)];m=max(1,int(math.ceil(math.hypot(b[0]-a[0],b[1]-a[1])/step)))
        out+=[(a[0]+(b[0]-a[0])*q/m,a[1]+(b[1]-a[1])*q/m) for q in range(m)]
    if cuts:
        S=[0.0]
        for k in range(len(out)):a=out[k];b=out[(k+1)%len(out)];S.append(S[-1]+math.hypot(b[0]-a[0],b[1]-a[1]))
        res=[];cs=sorted(cuts);ci=0
        for k in range(len(out)):
            res.append(out[k]);a=out[k];b=out[(k+1)%len(out)]
            while ci<len(cs) and cs[ci]<S[k+1]:
                if cs[ci]>S[k]+0.02 and cs[ci]<S[k+1]-0.02:
                    f=(cs[ci]-S[k])/(S[k+1]-S[k]);res.append((a[0]+f*(b[0]-a[0]),a[1]+f*(b[1]-a[1])))
                ci+=1
        out=res
    return out
def _ccw(L):
    a=sum(L[k][0]*L[(k+1)%len(L)][1]-L[(k+1)%len(L)][0]*L[k][1] for k in range(len(L)))
    return L if a>0 else L[::-1]
def _vn(L):   # outward vertex normals of a counter-clockwise loop
    out=[]
    for k in range(len(L)):
        a=L[k-1];b=L[(k+1)%len(L)];t=(b[0]-a[0],b[1]-a[1]);l=math.hypot(*t);out.append((t[1]/l,-t[0]/l))
    return out
def _off(L,d):return [(p[0]+d*n[0],p[1]+d*n[1]) for p,n in zip(L,_vn(L))]
def _clip(L,a,b):   # the part of loop L left of the line a->b (Sutherland-Hodgman)
    s=lambda p:(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]);out=[]
    for k in range(len(L)):
        p=L[k];q=L[(k+1)%len(L)];sp,sq=s(p),s(q)
        if sp>=0:out.append(p)
        if (sp>=0)!=(sq>=0):t=sp/(sp-sq);out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
    return out
def _fill(L,z,mi,up=True,sc=4.0):
    vs=[bm.verts.new((x,y,z)) for x,y in L];es=[bm.edges.new((vs[k],vs[(k+1)%len(vs)])) for k in range(len(vs))]
    r=bmesh.ops.triangle_fill(bm,use_beauty=True,use_dissolve=False,edges=es)
    for f in r['geom']:
        if isinstance(f,bmesh.types.BMFace):
            f.material_index=mi;f.normal_update()
            if (f.normal.z<0)==up:f.normal_flip()
            for l in f.loops:l[uv].uv=(l.vert.co.x/sc,l.vert.co.y/sc)
def _q(a,b,z0,z1,mi,n,s0=0.0,um=4.0):
    l=math.hypot(b[0]-a[0],b[1]-a[1])
    face([bm.verts.new((a[0],a[1],z0)),bm.verts.new((b[0],b[1],z0)),bm.verts.new((b[0],b[1],z1)),bm.verts.new((a[0],a[1],z1))],mi,
         [(s0/um,z0/um),((s0+l)/um,z0/um),((s0+l)/um,z1/um),(s0/um,z1/um)],n)
def _pband(L,z0,z1,mi,sel=None,inset=0.0,solid=None,mull=None,only=None):
    """One horizontal band of a pavilion's wall over the segments only(k) picks (all by default). Segments that sel(k)
    picks are cut back by inset, with a soffit, a sill, side jambs and mullions every mull metres; the rest stay flush."""
    n=len(L);Li=_off(L,-inset) if inset else L;S=[0.0]
    for k in range(n):a=L[k];b=L[(k+1)%n];S.append(S[-1]+math.hypot(b[0]-a[0],b[1]-a[1]))
    on=[bool(only(k)) if only else True for k in range(n)]
    rec=[on[k] and inset>0 and (bool(sel(k)) if sel else True) for k in range(n)]
    for k in range(n):
        if not on[k]:continue
        j=(k+1)%n;nn=Vector((L[j][1]-L[k][1],-(L[j][0]-L[k][0]),0)).normalized();tg=Vector((L[j][0]-L[k][0],L[j][1]-L[k][1],0)).normalized()
        if not rec[k]:_q(L[k],L[j],z0,z1,solid if (solid is not None and sel is not None) else mi,nn,S[k]);continue
        _q(Li[k],Li[j],z0,z1,mi,nn,S[k])
        face([bm.verts.new((L[k][0],L[k][1],z1)),bm.verts.new((L[j][0],L[j][1],z1)),bm.verts.new((Li[j][0],Li[j][1],z1)),bm.verts.new((Li[k][0],Li[k][1],z1))],MPVD,[(0,0),(1,0),(1,1),(0,1)],Vector((0,0,-1)))
        face([bm.verts.new((L[k][0],L[k][1],z0)),bm.verts.new((L[j][0],L[j][1],z0)),bm.verts.new((Li[j][0],Li[j][1],z0)),bm.verts.new((Li[k][0],Li[k][1],z0))],MC,[(0,0),(1,0),(1,1),(0,1)],Vector((0,0,1)))
        if not rec[k-1]:_q(L[k],Li[k],z0,z1,solid if solid is not None else MPVD,tg)
        if not rec[j]:_q(L[j],Li[j],z0,z1,solid if solid is not None else MPVD,-tg)
        if mull:
            for m in range(int(S[k]//mull)+1,int(S[k+1]//mull)+1):
                f=(m*mull-S[k])/max(1e-9,S[k+1]-S[k]);p=(Li[k][0]+f*(Li[j][0]-Li[k][0]),Li[k][1]+f*(Li[j][1]-Li[k][1]))
                tube(Vector((p[0]+0.06*nn.x,p[1]+0.06*nn.y,z0)),Vector((p[0]+0.06*nn.x,p[1]+0.06*nn.y,z1)),0.05,MST)
    return S
def _rim(L,z0,z1,out=0.15):
    Lo=_off(L,out);n=len(L)
    for k in range(n):
        j=(k+1)%n;nn=Vector((L[j][1]-L[k][1],-(L[j][0]-L[k][0]),0)).normalized();_q(Lo[k],Lo[j],z0,z1,MW,nn)
        face([bm.verts.new((L[k][0],L[k][1],z0)),bm.verts.new((L[j][0],L[j][1],z0)),bm.verts.new((Lo[j][0],Lo[j][1],z0)),bm.verts.new((Lo[k][0],Lo[k][1],z0))],MW,[(0,0),(1,0),(1,1),(0,1)],Vector((0,0,-1)))
    return Lo
def _lines(L,p0,d,offs):   # chords of loop L along direction d through p0+o*perp(d), for each offset o
    pr=(-d[1],d[0]);out=[]
    for o in offs:
        c=(p0[0]+o*pr[0],p0[1]+o*pr[1]);ts=[]
        for k in range(len(L)):
            a=L[k];b=L[(k+1)%len(L)];e=(b[0]-a[0],b[1]-a[1]);den=d[0]*e[1]-d[1]*e[0]
            if abs(den)<1e-12:continue
            w=(a[0]-c[0],a[1]-c[1]);t=(w[0]*e[1]-w[1]*e[0])/den;u_=(w[0]*d[1]-w[1]*d[0])/den
            if 0<=u_<1:ts.append(t)
        ts.sort()
        for q in range(0,len(ts)-1,2):out.append(((c[0]+ts[q]*d[0],c[1]+ts[q]*d[1]),(c[0]+ts[q+1]*d[0],c[1]+ts[q+1]*d[1])))
    return out
# north pavilion: solid walls; on the river face south of y 15, a glazed band and two dark slots cut 0.3-0.6 m back
_pn=PVJ['north'];LN=_ccw(_resample(_chaikin([tuple(p) for p in _pn['outline']]),1.0));ZNT=_pn['roof'];ZNR=ZNT-_pn['rim']
_sl=_pn['slots'];_mid=lambda L,k:((L[k][0]+L[(k+1)%len(L)][0])/2,(L[k][1]+L[(k+1)%len(L)][1])/2)
def _nsel(yf):   # segments of the river face south of y yf
    def f(k):
        a=LN[k];b=LN[(k+1)%len(LN)];return (b[1]-a[1])<0 and abs(b[1]-a[1])>0.7*math.hypot(b[0]-a[0],b[1]-a[1]) and _mid(LN,k)[1]<yf
    return f
_sg,(_s1,_s0)=_sl['glass'],sorted(_sl['bands'],key=lambda d:d['z'][0])
_pband(LN,0.0,_pn['base'],MC)
_pband(LN,_sg['z'][0],_sg['z'][1],MPVG,_nsel(_sg['y_from']),0.3,MPW,_sl['pitch'])
_pband(LN,_sg['z'][1],_s1['z'][0],MPW)
_pband(LN,_s1['z'][0],_s1['z'][1],MPVD,_nsel(_s1['y_from']),0.6,MPW)
_pband(LN,_s1['z'][1],_s0['z'][0],MPW)
_pband(LN,_s0['z'][0],_s0['z'][1],MPVD,_nsel(_s0['y_from']),0.6,MPW)
_pband(LN,_s0['z'][1],ZNR,MPW)
LNo=_rim(LN,ZNR,ZNT)
_la=_pn['lattice'];_A,_B=tuple(_la['a']),tuple(_la['b'])
_fill(_clip(LNo,_B,_A),ZNT,MPVR)                      # the open roof deck, south of the lattice
for _pp in _pn.get('roof_paint',[]):_fill([tuple(q) for q in _pp],ZNT+0.02,MPVP)   # its orange paint (survey/roof_paint.py)
_LL=_clip(LNo,_A,_B);_fill(_LL,ZNT-0.25,MPVG)           # the glazed north end, under a grid of steel beams
_d=(_B[0]-_A[0],_B[1]-_A[1]);_dl=math.hypot(*_d);_d=(_d[0]/_dl,_d[1]/_dl);_pr=(-_d[1],_d[0])
_ext=max(((p[0]-_A[0])*_pr[0]+(p[1]-_A[1])*_pr[1]) for p in _LL)
_bw,_bl=_la['bays']
for (_pa,_pb) in _lines(_LL,_A,_d,[_ext*q/_bl for q in range(1,_bl)])+_lines(_LL,_A,_pr,[-_dl*q/_bw for q in range(1,_bw)]):
    tube(Vector((_pa[0],_pa[1],ZNT-0.1)),Vector((_pb[0],_pb[1],ZNT-0.1)),0.15,MST)
_pband(_LL,ZNT-0.25,ZNT,MW)
# south pavilion: a dark ground storey with paired windows, a concrete slab band, an upper storey glazed 0.6 m back
# from the rim (solid with three louvre slots at the north-west end), the white rim
_ps=PVJ['south'];LS=_ccw(_resample(_chaikin([tuple(p) for p in _ps['outline']]),1.0));ZST=_ps['roof'];ZSR=ZST-_ps['rim']
_a0,_a1=_ps['axis'];_t=((_a1[0]-_a0[0]),(_a1[1]-_a0[1]));_tl=math.hypot(*_t);_t=(_t[0]/_tl,_t[1]/_tl);_nsw=(-_t[1],_t[0]) if (-_t[1])<0 else (_t[1],-_t[0])
_Up=lambda p:(p[0]-_a0[0])*_t[0]+(p[1]-_a0[1])*_t[1]
def _snrm(k,L=None):
    L=L or LS;a=L[k];b=L[(k+1)%len(L)];l=math.hypot(b[0]-a[0],b[1]-a[1]);return ((b[1]-a[1])/l,-(b[0]-a[0])/l)
_sw=lambda k,L=None:_snrm(k,L)[0]*_nsw[0]+_snrm(k,L)[1]*_nsw[1]
def _river_at(us,L):   # (segment, fraction, arclength) where the river face crosses each axis position in us
    S=[0.0]
    for k in range(len(L)):a=L[k];b=L[(k+1)%len(L)];S.append(S[-1]+math.hypot(b[0]-a[0],b[1]-a[1]))
    out=[]
    for u in us:
        for k in range(len(L)):
            ua,ub=_Up(L[k]),_Up(L[(k+1)%len(L)])
            if _sw(k,L)>0.7 and min(ua,ub)<=u<max(ua,ub):f=(u-ua)/(ub-ua);out.append((k,f,S[k]+f*(S[k+1]-S[k])));break
    return out
_gw=_ps['ground_windows'];_cp=_ps['column_pitch'];_cu=[_ps['column_u0']+m*_cp for m in range(-4,6)]
_wu=[];_h0=_gw['pair_gap']/2
for _c in _cu:_wu+=[(_c+_cp/2-_h0-_gw['w'],_c+_cp/2-_h0),(_c+_cp/2+_h0,_c+_cp/2+_h0+_gw['w'])]
LS=_resample(LS,1.0,[r[2] for r in _river_at([u for w in _wu for u in w],LS)])
_U=lambda k:_Up(_mid(LS,k))
_sout=lambda k:_sw(k)>-0.3   # every face but the one against the podium
def _win(k):return _sw(k)>0.7 and any(a<_U(k)<b for a,b in _wu)
_pband(LS,0.0,_gw['z'][0],MPVB)
_pband(LS,_gw['z'][0],_gw['z'][1],MPVG,_win,0.25,MPVB)
_pband(LS,_gw['z'][1],_ps['slab'][0],MPVB)
_pband(LS,_ps['slab'][0],_ps['slab'][1],MC)
_gsel=lambda k:_sout(k) and _U(k)>_ps['glass_from_u']
_z7,_z11=_ps['upper']
_pband(LS,_z7,_z11,MPVG,None,0.6,MPW,_ps['mullion_pitch'],only=_gsel)
for _k,_f,_ in _river_at([u for u in _cu if u>_ps['glass_from_u']],LS):   # columns standing in front of the glass
    _j=(_k+1)%len(LS);_p=(LS[_k][0]+_f*(LS[_j][0]-LS[_k][0]),LS[_k][1]+_f*(LS[_j][1]-LS[_k][1]));_nn=_snrm(_k)
    tube(Vector((_p[0]-0.3*_nn[0],_p[1]-0.3*_nn[1],_z7)),Vector((_p[0]-0.3*_nn[0],_p[1]-0.3*_nn[1],_z11)),0.18,MW)
_lsel=lambda k:_sout(k) and _U(k)<=_ps['glass_from_u']
_pband(LS,_z7,_z11,MPW,only=lambda k:not _gsel(k) and not _lsel(k))   # the face against the podium
_zz=[_z7]+[z for zs in _ps['louvre_slots'] for z in zs]+[_z11]
for _qq in range(len(_zz)-1):   # the north-west end: solid, with three louvre slots cut 0.4 m in
    _pband(LS,_zz[_qq],_zz[_qq+1],MPVD if _qq%2 else MPW,(lambda k:True) if _qq%2 else None,0.4 if _qq%2 else 0.0,MPW,only=_lsel)
LSo=_rim(LS,ZSR,ZST);_fill(LSo,ZST,MPVR)
for _pp in _ps.get('roof_paint',[]):_fill([tuple(q) for q in _pp],ZST+0.02,MPVP)
_fill(LN,0.05,MC,False);_fill(LS,0.05,MC,False)
print('pavilions: north',len(LN),'south',len(LS),'segments')
# --- roof: the inner edge is its own measured curve (survey/inner_c.json), met by each truss line square to the edge
_IC=_np0.array(json.load(open(os.path.join(me_dir,'survey','inner_c.json'))));IZ=float(json.load(open(os.path.join(me_dir,'survey','inner_z.json')))['z'])
def _inner_hit(i):
    o=_np0.array(EP[i]);n=_np0.array(EN[i]);t=40.0
    for _ in range(40):
        p=o-n*t;a=math.atan2(p[1]-SH.OC[1],p[0]-SH.OC[0]);r=float(SH.fourier(_IC,a));t+=(_np0.hypot(*(p-SH.OC))-r)*0.9
    p=o-n*t;return Vector((p[0],p[1],0))
IN=[_inner_hit(i) for i in range(N)]

# roof membrane: one barrel vault a bay (LSAA: "a conventional barrel vault supported by three arches"), from the
# fascia to the inner edge, scalloped back between the trusses' tips. The scallop is centred on the measured curve
# (its mean offset is zero), so the edge Google Earth traces sits on inner_c: tips 0.5 m in front, mid-bay 0.3 m behind.
SCAL=0.8
_ro=lambda i:(RF[i]-IN[i]).normalized()
INS=[IN[i]+_ro(i)*SCAL*(math.sin(math.pi*(i%K)/K)-2/math.pi) for i in range(N)]
T=14;rows=[]
_env=lambda t:min(1.0,t/0.1,(1.0-t)/0.25)
# the membrane's dip below the fascia-to-inner-edge line, along the trusses (DIP) and mid-bay (DIPM), measured by
# 260 straight-down Google Earth hovers (survey/roof_profile.json): it falls ~2 m within 8 m of the edge, and each
# bay's vault rises up to 1 m over the valleys in the inner half
RPJ=json.load(open(os.path.join(me_dir,'survey','roof_profile.json')))
DIP=lambda t:float(_np0.interp(t,RPJ['t'],RPJ['valley']));DIPM=lambda t:float(_np0.interp(t,RPJ['t'],RPJ['mid']))
ZR=lambda i,t:ZF_[i]+(IZ-ZF_[i])*t-DIP(t)
for k in range(T+1):
    t=k/T;row=[]
    for i in range(N):
        p=RF[i].lerp(INS[i],t)
        bul=(DIP(t)-DIPM(t))*math.sin(math.pi*(i%K)/K)**0.6
        row.append(bm.verts.new((p.x,p.y,ZR(i,t)+bul)))
    rows.append(row)
for k in range(T):
    for i in range(N):
        j=(i+1)%N;vs=[rows[k][i],rows[k][j],rows[k+1][j],rows[k+1][i]]
        u0=(i%K)/K;u1=(i%K+1)/K
        face(vs,MR,[(u0,1-k/T),(u1,1-k/T),(u1,1-(k+1)/T),(u0,1-(k+1)/T)],Vector((0,0,1)))
_ur=[[bm.verts.new((RF[i].lerp(INS[i],k/T).x,RF[i].lerp(INS[i],k/T).y,ZR(i,k/T)-1.0-0.2*(1-k/T))) for i in range(N)] for k in range(T+1)]
for k in range(T):   # underside: 1.0-1.2 m under the membrane's valley line, following its dip
    for i in range(N):
        j=(i+1)%N;face([_ur[k][i],_ur[k+1][i],_ur[k+1][j],_ur[k][j]],MU,[(0,0),(1,0),(1,1),(0,1)],Vector((0,0,-1)))
oc=Vector((SH.OC[0],SH.OC[1],0))
wall(INS,c(IZ-1.0),c(IZ+0.2),MW,1e6,1e6,outward=False,ctr=oc)
_ring=lambda R,z,r,m:[tube(Vector((R[i].x,R[i].y,z(i))),Vector((R[(i+1)%N].x,R[(i+1)%N].y,z((i+1)%N))),r,m) for i in range(N)]
for bi in range(NB):   # a floodlight bank under each truss's tip
    i=bi*K;q=IN[i]+_ro(i)*0.8;d=_ro(i);sd=Vector((-d.y,d.x,0))
    pts=[q+d*a_+sd*b_ for a_,b_ in((-0.5,-1.6),(0.5,-1.6),(0.5,1.6),(-0.5,1.6))]
    lo4=[P(p_,IZ-2.4) for p_ in pts];hi4=[P(p_,IZ-1.0) for p_ in pts]
    for e in range(4):
        f_=(e+1)%4;nn=((pts[e]+pts[f_])/2-q).normalized()
        face([lo4[e],lo4[f_],hi4[f_],hi4[e]],MST,[(0,0),(1,0),(1,1),(0,1)],nn)
    face(lo4[::-1],MW,[(0,0),(1,0),(1,1),(0,1)],Vector((0,0,-1)))
# primary trusses: a triangular lattice in each valley, square to the edge, ending at the membrane's tip (Google Earth
# close views: the lattice stops at the gutter line, 2026-11-22 overlay)
for bi in range(NB):
    i=bi*K;o=RF[i];n=INS[i];sd=Vector((-EN[i][1],EN[i][0],0))
    def at(t,dz=0.0,off=0.0,o=o,n=n,sd=sd,i=i):
        p=o.lerp(n,t)+sd*off;return Vector((p.x,p.y,ZF_[i]+(IZ-ZF_[i])*t-DIP(t)+dz))
    top=lambda t:(0.6+2.6*min(t/0.3,1.0) if t<0.3 else 3.2-2.3*(t-0.3)/0.7)
    nseg=16;HW=1.2
    for s_ in range(nseg):
        t0,t1=s_/nseg,(s_+1)/nseg;tm=(t0+t1)/2
        for sg in(-1,1):
            tube(at(t0,top(t0),sg*HW),at(t1,top(t1),sg*HW),0.3,MST)
            tube(at(t0,top(t0),sg*HW),at(tm,0.25),0.13,MST);tube(at(tm,0.25),at(t1,top(t1),sg*HW),0.13,MST)
        tube(at(t0,0.25),at(t1,0.25),0.3,MST)
        tube(at(t0,top(t0),-HW),at(t0,top(t0),HW),0.12,MST)
        tube(at(t0,top(t0),-HW if s_%2 else HW),at(t1,top(t1),HW if s_%2 else -HW),0.11,MST)
    tube(at(1,top(1),-HW),at(1,top(1),HW),0.08,MST)
    for sg in(-1,1):tube(at(0,0.0,sg*HW),at(0,top(0),sg*HW),0.15,MST);tube(at(1,0.0,sg*HW*0.5),at(1,top(1),sg*HW),0.15,MST)
_ring(INS,lambda i:IZ+0.9,0.35,MST)
_GT=[RF[i].lerp(INS[i],0.05) for i in range(N)]
_ring(_GT,lambda i:ZF_[i]+(IZ-ZF_[i])*0.05-DIP(0.05)+0.35,0.18,MW)

# --- HALO, the rooftop climb's platform on the west roof (survey/halo.json, traced off the straight-down Google Earth
# shot): a deck whose outline is the hull of the lean-out ring and the half-round lookout, an open centre in the ring,
# an oval opening in the deck, glass rails round every edge, a lift/stair drum.
HJ=json.load(open(os.path.join(me_dir,'survey','halo.json')))
def _circ(c,r,n=48,a0=0.0):return [(c[0]+r*math.cos(a0+2*math.pi*k/n),c[1]+r*math.sin(a0+2*math.pi*k/n)) for k in range(n)]
def _hull(pts):
    pts=sorted(set(pts));cr=lambda o,a,b:(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]);lo=[];hi=[]
    for q in pts:
        while len(lo)>=2 and cr(lo[-2],lo[-1],q)<=0:lo.pop()
        lo.append(q)
    for q in reversed(pts):
        while len(hi)>=2 and cr(hi[-2],hi[-1],q)<=0:hi.pop()
        hi.append(q)
    return lo[:-1]+hi[:-1]
def _caps(a,b,r,n=24):
    ang=math.atan2(b[1]-a[1],b[0]-a[0])
    return [(b[0]+r*math.cos(ang-math.pi/2+math.pi*k/n),b[1]+r*math.sin(ang-math.pi/2+math.pi*k/n)) for k in range(n+1)]+\
           [(a[0]+r*math.cos(ang+math.pi/2+math.pi*k/n),a[1]+r*math.sin(ang+math.pi/2+math.pi*k/n)) for k in range(n+1)]
_hr=HJ['ring'];_he=HJ['end'];_ho=HJ['opening'];ZH=HJ['deck_top'];ZH0=ZH-HJ['deck_thick']
_out=_hull(_circ(_hr['c'],_hr['r_out'],96)+_circ(_he['c'],_he['r'],96))
_holes=[_circ(_hr['c'],_hr['r_in'],72),_caps(_ho['a'],_ho['b'],_ho['r'])]
def _loopfill(loops,z,up):
    es=[]
    for L in loops:
        vs=[bm.verts.new((x,y,z)) for x,y in L]
        es+=[bm.edges.new((vs[k],vs[(k+1)%len(vs)])) for k in range(len(vs))]
    r=bmesh.ops.triangle_fill(bm,use_beauty=True,use_dissolve=False,edges=es)
    for f in r['geom']:
        if isinstance(f,bmesh.types.BMFace):
            f.material_index=MST;f.normal_update()
            if (f.normal.z<0)==up:f.normal_flip()
_loopfill([_out]+_holes,ZH,True);_loopfill([_out]+_holes,ZH0,False)
def _band(L,z0,z1,mi,inside=False):
    for k in range(len(L)):
        a=L[k];b=L[(k+1)%len(L)];vs=[P(Vector((a[0],a[1],0)),z0),P(Vector((b[0],b[1],0)),z0),P(Vector((b[0],b[1],0)),z1),P(Vector((a[0],a[1],0)),z1)]
        n=Vector((b[1]-a[1],-(b[0]-a[0]),0)).normalized()*(-1 if inside else 1)
        face(vs,mi,[(0,0),(1,0),(1,1),(0,1)],n)
_band(_out,ZH0,ZH,MST)
for L in _holes:_band(L,ZH0,ZH,MST,inside=True)
for L in [_out]+_holes:
    _band(L,ZH,ZH+HJ["rail_h"],MG)
    for k in range(len(L)):
        a=L[k];b=L[(k+1)%len(L)];tube(Vector((a[0],a[1],ZH+HJ['rail_h'])),Vector((b[0],b[1],ZH+HJ['rail_h'])),0.05,MST)
_hd=HJ['drum'];_dc=_circ(_hd['c'],_hd['r'],32);_band(_dc,ZH,ZH+_hd['h'],MW)
face([P(Vector((x,y,0)),ZH+_hd['h']) for x,y in _dc],MW,[(0,0)]*len(_dc),Vector((0,0,1)))

    # Google Earth (east and north close views): no white Y columns outside the glass, only slim white posts in the
    # dark open strip between the glass's head and the roof's fascia (drawn in the glass texture, bronze.py).
# bowl seating inside, turf
FE=J['fence'];oc=Vector((FE['c'][0],FE['c'][1],0));ang=FE['ang'];U=Vector((math.cos(ang),math.sin(ang),0));Vv=Vector((-math.sin(ang),math.cos(ang),0))   # bowl front = measured fence oval
U=Vector((math.cos(ang),math.sin(ang),0));Vv=Vector((-math.sin(ang),math.cos(ang),0))
def ell(d,a=82.2,b=64.05):
    du,dv=d.dot(U),d.dot(Vv);k=1/math.sqrt((du/a)**2+(dv/b)**2);return oc+d*k
L0=[ell((RF[i]-oc).normalized(),FE['a'],FE['b']) for i in range(N)]
# The bowl's three visible rakes, each an offset of the roof edge that moves out 1.3-2.8 m a metre of height.
# survey/tier_fit.json is fitted to 312 Google Earth hovers from four cameras inside the bowl (tierfit.py):
# d = c0 + c1 cos th + c2 sin th + slope*h, rms 1.1 m (upper), 1.1 m (middle), 1.6 m (lower), 1 m height readouts.
# The upper tier's front overhangs the middle tier by ~6 m. Published: five tiers (worldconstructionnetwork).
TF=json.load(open(os.path.join(me_dir,'survey','tier_fit.json')))
def RT(nm,h):
    c=TF[nm]['c'];return RING(lambda i:c[0]+c[1]*math.cos(TH[i])+c[2]*math.sin(TH[i])+TF[nm]['slope']*h)
ZL0,ZL1,ZM0,ZM1,ZU0,ZU1=2.0,6.5,8.0,17.5,19.5,33.5
LA=RT('lower',ZL0);LB=RT('lower',ZL1);LC=RT('mid',ZM0);LD=RT('mid',ZM1);LE=RT('upper',ZU0);LF=RT('upper',ZU1)
_gap=[((LA[i]-oc).length-(L0[i]-oc).length) for i in range(N)]
print('bowl front behind the match fence: min %.1f max %.1f m'%(min(_gap),max(_gap)))
# bowl: stand texture = one real seating bay (063), u once per bay along the ring, v by height through the three tiers
SL=arcs(L0);BAYL=SL[N]/NB
SU=[SL[i]/BAYL for i in range(N+1)]
KN=[(0,1.0),(ZL0,0.95),(ZM1,0.71),(ZU0,0.667),(ZU1,0.0)]
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
swall(LA,0.0,ZL0)
rake(LA,ZL0,LB,ZL1,15)
flat(LB,c(ZL1),LC,c(ZL1),MC)            # the walkway in front of the middle tier, then its 1.5 m front wall
swall(LC,ZL1,ZM0)
rake(LC,ZM0,LD,ZM1,19)
# under the upper tier: its slab follows the rake 1 m below the treads, over the middle tier's back rows
def _hu(i,d):
    c_=TF['upper']['c'];return (d-(c_[0]+c_[1]*math.cos(TH[i])+c_[2]*math.sin(TH[i])))/TF['upper']['slope']
_dLD=[TF['mid']['c'][0]+TF['mid']['c'][1]*math.cos(TH[i])+TF['mid']['c'][2]*math.sin(TH[i])+TF['mid']['slope']*ZM1 for i in range(N)]
ZUB=[_hu(i,_dLD[i])-1.0 for i in range(N)]
wall(LD,lambda i:ZM1,lambda i:ZUB[i],MC,1e6,1e6,outward=False,ctr=oc)   # back of the middle tier
flat(LD,lambda i:ZUB[i],LE,c(ZU0-0.9),MU,up=False)
swall(LE,ZU0-0.9,ZU0)                   # the upper tier's balcony front
rake(LE,ZU0,LF,ZU1,23)
swall(LF,ZU1,ZU1+3.5)
# no turf inside the bowl and no plaza beyond the podium edge: the game draws the turf (director: "Leave field out")
def prism(pts,h,roofmi,wallmi,glassband=False,louvre_from=None):
    pts=[Vector((p[0],p[1],0)) for p in pts];n=len(pts);cc=sum(pts,Vector())/n
    lo=[P(p,0.0) for p in pts];mid=[P(p,h-2.2) for p in pts];mi2=[P(p,h-0.7) for p in pts];hi=[P(p,h) for p in pts]
    s0=0.0
    for i in range(n):
        j=(i+1)%n;w=((pts[i]+pts[j])/2-cc).normalized();L=(pts[j]-pts[i]).length;ua,ub=s0/4,(s0+L)/4;s0+=L
        q=lambda z0,z1,sc=4.0:[(ua,z0/sc),(ub,z0/sc),(ub,z1/sc),(ua,z1/sc)]
        face([lo[i],lo[j],mid[j],mid[i]],wallmi,q(0,h-2.2),w)
        if glassband:face([mid[i],mid[j],mi2[j],mi2[i]],MG,[(s0/BAYR-L/BAYR,1-9.5/GH),(s0/BAYR,1-9.5/GH),(s0/BAYR,1-8.0/GH),(s0/BAYR-L/BAYR,1-8.0/GH)],w)
        else:face([mid[i],mid[j],mi2[j],mi2[i]],wallmi,q(h-2.2,h-0.7),w)
        face([mi2[i],mi2[j],hi[j],hi[i]],MW,q(h-0.7,h),w)
    top=bm.faces.new(hi);top.normal_update()
    if top.normal.z<0:top.normal_flip()
    res=bmesh.ops.triangulate(bm,faces=[top])
    for f in res['faces']:
        f.material_index=roofmi
        if louvre_from is not None and f.calc_center_median().y>louvre_from:f.material_index=MLV
        for l in f.loops:l[uv].uv=((l.vert.co.x-cc.x)/TI['proof_span_m']+0.5,(l.vert.co.y-cc.y)/TI['proof_span_m']+0.5)
# (the two orange-roof riverside pavilions are modelled from survey/pavilions.json, after the west volume above)
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
D0,D1=CI(294.8),CI(281.0)   # the stair head's deck, by bearing (was segments 50-66 of the old ring)
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
for i in ARC(PODA,PODB):
    if i in DECK_I:
        if cur:runs.append(cur);cur=[]
        continue
    cur.append(i)
if cur:runs.append(cur)
BZ0,BZ1=6.4,7.5                                            # o2: low see-through mesh balustrade, ~1.1 m, steel top rail
# o2: the west/north edge has the mesh balustrade; past the east pavilion (seg 72 on) it is a solid sandstone parapet
PAR=set(ARC(275.7,PODB))   # bearings 276 round to the podium's south-east end: solid parapet
mruns=[];pruns=[]
for run in runs:
    a_=[i for i in run if i not in PAR];b_=[i for i in run if i in PAR]
    if a_:mruns.append(a_+([b_[0]] if b_ else []))
    if b_:pruns.append(b_)
for run in pruns:
    AR=arcs(POD)   # parapet face shares the podium wall's u, so its block joints run straight up from the wall's
    for a_,b_ in zip(run,run[1:]):sweep([POD[a_]+inw(a_)*0.15,POD[b_]+inw(b_)*0.15],ZD[a_],ZD[a_]+1.1,0.3,MPW,TI['podwall_m'][0],TI['podwall_m'][1],sa=[AR[a_],AR[a_]+(POD[b_]-POD[a_]).length])
for run in mruns:
    pts=[POD[i]+inw(i)*0.12 for i in run];sP=[0.0]
    for a_,b_ in zip(pts,pts[1:]):sP.append(sP[-1]+(b_-a_).length)
    zr=[ZD[i] for i in run];lo=[P(p,z+0.08) for p,z in zip(pts,zr)];hi=[P(p,z+1.05) for p,z in zip(pts,zr)]
    for k in range(len(pts)-1):
        face([lo[k],lo[k+1],hi[k+1],hi[k]],MMS,[(sP[k],0),(sP[k+1],0),(sP[k+1],1.0),(sP[k],1.0)],-inw(run[k]))
    for k in range(len(pts)-1):
        q0=Vector((pts[k].x,pts[k].y,0));q1=Vector((pts[k+1].x,pts[k+1].y,0))
        sweep([q0,q1],zr[k]+1.05,zr[k]+1.1,0.07,MLP);sweep([q0,q1],zr[k],zr[k]+0.08,0.07,MLP)   # top and foot rails
    nxt=0.0
    for k,p in enumerate(pts):                                             # posts every ~1.8 m and at both ends
        if sP[k]>=nxt or k==len(pts)-1:boxp(p,0.035,zr[k],zr[k]+1.1,MLP);nxt=sP[k]+1.8
# lamp posts: o2 measures 3.5-3.75 m poles every ~7.2 m, standing just inside the balustrade (first one at seg 29)
LH=3.7;LS=7.2;s0=0.0;sp=[0.0]
order=ARC(PODA,PODB);NOLAMP=set(ARC(282.7,210.6))
for a_,b_ in zip(order,order[1:]):sp.append(sp[-1]+(POD[b_]-POD[a_]).length)
ph=sp[order.index(CI(313.0))]%LS;t=ph
while t<sp[-1]-1.0:
    k=max(q for q in range(len(sp)) if sp[q]<=t);i=order[k];j=order[min(k+1,len(order)-1)]
    f=(t-sp[k])/max(sp[min(k+1,len(sp)-1)]-sp[k],1e-6);e=POD[i].lerp(POD[j],f);c_=e+inw(i)*0.6
    if i not in DECK_I and j not in DECK_I and (c_-Vector((lx,ly,0))).length>4.0 and i not in NOLAMP:   # o2: no lamps by the west pavilion
        cyl(c_.x,c_.y,ZD[i],ZD[i]+LH,0.07,MLP,8)
        boxp(c_,0.16,ZD[i]+LH,ZD[i]+LH+0.14,MLP)                                # lamp head
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
# The fins' 7 cm ledges face the sky; at range each is under a pixel, and their bright rows against the darker blades
# shimmered into moire rings (2x supersampling removes them; the texture alone does not cause them). They keep their
# shape (silhouette, shadow) but are lit as the facade face beside them: their normal is the facade's, out and level.
_la=me.attributes.get('ledge')
if _la is not None:
    _ln=[]
    for _p in me.polygons:
        if _la.data[_p.index].value:_n=OUT(_la.data[_p.index].value-1)
        else:_n=_p.normal
        _ln+=[tuple(_n)]*_p.loop_total
    me.normals_split_custom_set(_ln)
    me.attributes.remove(me.attributes['ledge'])
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
                AST.append((Rf[i].lerp(Rf[j],f),Rk[i].lerp(Rk[j],f),pz,(zb-za)/rowsn,0.5*float(np.interp(c+0.6,bayv,cs)-np.interp(c-0.6,bayv,cs))-0.02))   # the gap's own local width
        if vom and pz+0.01>=ZM0+0.6*(ZM1-ZM0):
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
_seats(LA,ZL0,LB,ZL1,15,lambda r:'lo',0.0,False)
_seats(LC,ZM0,LD,ZM1,19,lambda r:'mid',0.0,True)
_seats(LE,ZU0,LF,ZU1,23,lambda r:'up',3.7,False)
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
print('seats dropped (spot taken)',_keep.count(False),'by tier lo/mid/up',[sum(1 for (x,y,z,a_,b_),k in zip(SEAT,_keep) if not k and lo_<=z<hi_) for lo_,hi_ in ((0,ZL1+0.1),(ZM0-0.1,ZM1+0.1),(ZU0-0.1,99))])
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
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend))
for o in bpy.data.objects:o.select_set(o.name!='seats3d')
bpy.ops.export_scene.gltf(filepath=os.path.abspath(dst),export_format='GLB',use_selection=True)
print('tris',sum(len(p.vertices)-2 for p in me.polygons))
