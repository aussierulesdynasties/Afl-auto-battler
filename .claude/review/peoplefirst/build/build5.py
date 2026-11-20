# People First Stadium exterior. blender -b -P build.py -- OUT.glb RENDER.png
import bpy,bmesh,sys,math,json,os
from mathutils import Vector,Matrix
sys.path.insert(0,os.getcwd())
out,rpng=sys.argv[sys.argv.index('--')+1:][:2]
D=json.load(open(os.environ.get('GEO','geo_build.json')));CAM=json.load(open('cam.json'))['p']
RG,RIN,ROUT=D['RG'],D['rin'],D['rout']
def lerp_arr(A,a):
    f=(a%360)*4;i=int(f)%1440;t=f-int(f);return A[i]*(1-t)+A[(i+1)%1440]*t
rg=lambda a:lerp_arr(RG,a);rin=lambda a:lerp_arr(RIN,a);rout=lambda a:lerp_arr(ROUT,a)
def cf(c,a):r=math.radians(a);return c[0]+c[1]*math.cos(r)+c[2]*math.sin(r)
hin=lambda a:cf(D['hin'],a);hout=lambda a:cf(D['hout'],a)+(lerp_arr(D['hout_dz'],a) if 'hout_dz' in D else 0.0)
A0,A1=D['a0'],D['a1']
bpy.ops.wm.read_factory_settings(use_empty=True)
me=bpy.data.meshes.new('pf');ob=bpy.data.objects.new('PeopleFirstStadium',me);bpy.context.scene.collection.objects.link(ob)
bm=bmesh.new();uv=bm.loops.layers.uv.new()
TEX=json.load(open('htex/tex.json'))
MT={}
def mat(name,col,tex=None,rough=0.85,metal=0.0):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(*[(c/255)**2.2 for c in col],1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    if tex:
        t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(os.path.abspath('htex/'+tex+'.png'));t.interpolation='Linear'
        nt.links.new(t.outputs['Color'],b.inputs['Base Color'])
    me.materials.append(m);i=len(me.materials)-1;MT[i]=TEX[tex] if tex else [4.0,4.0];return i
GROUND=mat('ground',(150,150,140),None,0.95);APRON=mat('apron',(165,165,160),'apron');FENCE=mat('fence',(40,48,80),'led',0.5);FENCEL=mat('fencelow',(236,236,233),'fencelow',0.6)
SEAT=mat('seats',(214,74,62),'seat_low');SEATU=mat('seats_up',(214,74,62),'seat_up');AIS=mat('aisle',(200,200,196),'aisle_low');AISU=mat('aisle_up',(200,200,196),'aisle_up')
WALK=mat('walk',(170,170,165),'walk');NAVY=mat('navy',(52,60,88),'navy',0.5)
GLASS=mat('glass',(45,52,70),'glass',0.25);CONC=mat('concrete',(190,188,182),'concrete');ROOF=mat('roof',(246,246,244),'roof',0.6)
UNDER=mat('roofunder',(215,215,212),'roofunder',0.7);YEL=mat('yellow',(238,190,40),'yellow',0.5,0.2);TW=mat('tower',(244,244,244),'tower',0.5)
LAMP=mat('lamps',(235,235,235),'lamps',0.4);SCR=mat('screen',(25,30,45),'screen',0.3);STR=mat('stripes',(200,120,80),'stripes',0.6)
SBF=mat('scorefront',(28,32,42),'scorefront',0.35);SBP=mat('scorepost',(250,249,248),'scorepost');RSG=mat('redsign',(243,56,59),'redsign',0.5)
POD=mat('podroof',(232,230,226),'podroof');DARK=mat('darkblock',(62,68,82),'dark',0.5);RED=mat('red',(205,40,40),'red',0.5);GRASS=mat('grass',(98,132,62),'grass',0.95);VBLUE=mat('vomblue',(10,125,200),None,0.5);PFS=mat('pfsign',(10,8,66),'pfsign',0.5);WHITE=mat('white',(236,236,236),'white')
UVSET=set()
def face(vs,mi,uvs=None):
    try:f=bm.faces.new(vs)
    except ValueError:return None
    f.material_index=mi
    if uvs:
        tw,th=MT[mi]
        for l,u in zip(f.loops,uvs):l[uv].uv=(u[0]/tw,u[1]/th)
        UVSET.add(f)
    return f
def P(a,d,z,base=None):
    r=(rg(a) if base is None else base(a))+d;t=math.radians(a);return Vector((r*math.cos(t),r*math.sin(t),z))
def sweep(angles,prof,base=None,uscale=None,mfun=None,pf=None):
    angles=sorted(set(round(a,4) for a in angles))
    rows=[[bm.verts.new(P(a,*(pf(a,k) if pf else (d,z)),base)) for a in angles] for k,(d,z,_,_) in enumerate(prof)]
    vacc=0.0
    for k in range(1,len(prof)):
        mi=prof[k][2];L=math.hypot(prof[k][0]-prof[k-1][0],prof[k][1]-prof[k-1][1])
        cum=[0.0]
        for i in range(1,len(angles)):cum.append(cum[-1]+(rows[k][i].co-rows[k][i-1].co).length)
        for i in range(len(angles)-1):
            m2=mfun(k,(angles[i]+angles[i+1])/2,mi) if mfun else mi
            if m2 is None:continue
            face([rows[k-1][i],rows[k-1][i+1],rows[k][i+1],rows[k][i]],m2,[(cum[i],vacc),(cum[i+1],vacc),(cum[i+1],vacc+L),(cum[i],vacc+L)])
        vacc+=L
    return rows
def arange(a,b,s):
    n=max(2,int(round((b-a)/s))+1);return [a+(b-a)*i/(n-1) for i in range(n)]
MK=json.load(open('marks_final.json'))
VOMS=list(MK['voms'])
while VOMS[0]-6.65>A0+3:VOMS.insert(0,VOMS[0]-6.65)
def inint(a,c,hw):
    d=(a-c+180)%360-180;return abs(d)<=hw
def low_m(k,a,mi):
    if mi is not SEAT:return mi
    for o0,o1 in MK['low_openings']:
        if o0<=a%360<=o1:return CONC
    for c in MK['low_aisles']:
        if inint(a,c,math.degrees(0.55/(rg(a)+4))):return AIS
    return SEAT
NEARW=(126.0,199.0)  # near side under the roof edge where the photo shows short vertical posts (photo x 400-1100)
POSTL=6.6  # post length below the roof edge (postz.py: photo posts 6.5-7.1 m)
def up_m(k,a,mi):
    # near side outer wall, copied from the photo (lead 2026-11-20): bands measured on the wall line through cam_j
    # (wallz.py): dark band from the roof down to 18.4 m, red board 15.0-18.4 m (130 deg to photo x 848 = 176.6 deg,
    # navy beyond), grey 12.9-15.0 m, light concrete base down to the podium deck
    if k in (14,15,16,17) and NEARW[0]<=a%360<=NEARW[1]:
        return (DARK,RED if 130.0<=a%360<=176.6 else NAVY,WALK,CONC)[k-14]
    # vom openings: the seat slope is cut away over each tunnel mouth, one row above the walkway, 4 rows tall, inside a
    # light concrete frame 0.6 m wide with one row of frame above and below (photo, far stand: ~10x16 px opening, pale surround)
    if k in (6,7,8,9,10):
        for c in VOMS:
            if inint(a,c,math.degrees(VHW/(rg(a)+11))):return None if k in (7,8) else CONC
            if inint(a,c,math.degrees((VHW+VFR)/(rg(a)+11))):return CONC
    if mi is not SEAT:return mi
    if k==6:return SEATU
    for c in VOMS:
        if inint(a,c,math.degrees(0.55/(rg(a)+13))):return AISU
    return SEATU
def edges(lst,dr,hwm):
    out=[]
    for c in lst:
        hw=math.degrees(hwm/(rg(c)+dr));out+=[c-hw,c+hw]
    return out
LOWE=edges(MK['low_aisles'],4,0.55)+[x for o in MK['low_openings'] for x in o]
VHW=1.1  # half-width of a vom mouth (photo: ~10 px wide on the far stand = 2.2 m)
VFR=0.6  # vom frame width each side
UPE=edges(VOMS,13,0.55)+edges(VOMS,11,VHW)+edges(VOMS,11,VHW+VFR)
# no ground beyond the stadium (director 2026-11-18: background scene is a later pass)
# lower bowl all round
# north end (no roof): seats run back to the satellite's seat edge (north_db, per degree), same rake as the stands' lower tier
NDB=D['north_db']
def ndb(a):
    a=a%360
    if not (A1-360<=a<=A0):return 6.5
    return float(__import__('numpy').interp(a,[t[0] for t in NDB],[t[1] for t in NDB]))
RAKE=0.18  # photo (cam_j): seat back edge vs satellite depth, median of 48-72 deg
GAP=(88.0,95.5)  # today's ground (satellite 2019-2026): grass strip behind the goals, no seats
ingap=lambda a:GAP[0]<=a%360<=GAP[1]
def low_pf(a,k):
    db=ndb(a);zb=1.0+RAKE*(db-1.5)
    if ingap(a):return [(0,0.02),(1.5,0.02),(1.5,0.03),(db,0.03),(db,zb)][k]
    return [(0,0.02),(1.5,0.02),(1.5,1.0),(db,zb),(db+2.0,zb)][k]
def low_mn(k,a,mi):
    if ingap(a):return [None,APRON,None,GRASS,CONC][k]
    return low_m(k,a,mi)
NA=arange(A1-360,A0,0.5)
sweep(arange(A0,A1,0.5)+[e for e in [x%360 for x in LOWE]+[x%360+360 for x in LOWE] if A0<e<A1],[(0,0.02,None,0),(1.5,0.02,APRON,1),(1.5,1.0,FENCEL,1),(6.5,4.0,SEAT,1.0),(8.5,4.0,WALK,1)],mfun=low_m)
sweep(NA+list(GAP)+[e%360 for e in LOWE if A1-360<e%360<A0],[(0,0.02,None,0),(1.5,0.02,APRON,1),(1.5,1.0,FENCEL,1),(6.5,4.0,SEAT,1.0),(8.5,4.0,WALK,1)],mfun=low_mn,pf=low_pf)
span=arange(A0,A1,0.5)
SPROF=[(6.5,4.0),(6.5,6.9),(6.8,6.9),(6.8,6.0),(9.0,6.0),(9.0,6.4),(10.226,7.265),(11.2,7.952),(12.9,9.151),(14.3,10.139),(15.1,10.703),(24.0,16.98),(24.0,21.0),(25.0,21.0),(25.0,18.4),(25.0,15.0),(25.0,12.9),(25.0,8.0),(26.0,8.0),(26.0,7.0),(16.0,7.0),(16.0,0.0)];SMAT=[None,FENCE,WHITE,CONC,WALK,CONC,SEAT,SEAT,SEAT,SEAT,SEAT,SEAT,NAVY,CONC,NAVY,NAVY,NAVY,NAVY,WALK,WALK,UNDER,DARK]
sweep(span+[e for e in UPE if A0<e<A1],[(d,z,SMAT[i],1) for i,(d,z) in enumerate(SPROF)],mfun=up_m)
# 3D seats (lead 2026-11-20, director "Seats + underside": each seat its own back, pan and gap, in rows, empty).
# Every seat slope is stepped: one riser + tread per row at the old texture's row pitch (lower 0.70 m, upper 0.86 m
# along the slope), and on each tread a seat every 0.5 m: pan 0.40 deep at 0.44 m, back 0.40 tall leaning back 0.06 m,
# 0.44 wide (0.06 m gap), on a centre stem. Colours from the old seat texture (photo swatches): red 242,92,74, light
# grey 214,208,202 (upper tier 22% grey, lower all red). Aisles, voms and openings keep their steps but get no seats.
import random as _rnd
SRED=mat('seat_red',(242,92,74),None,0.45);SGRY=mat('seat_grey',(214,208,202),None,0.45);TRD=mat('tread',(196,186,180),None,0.9)
_SEATN=[0]
def _nv(p):return bm.verts.new(p)
def _q(a,b,c,d,m):face([_nv(a),_nv(b),_nv(c),_nv(d)],m)
def tiers(alist,segfun,pitch,mf,kfun,seatmats,grey,seed):
    A=sorted(set(round(x,4) for x in alist));rr=_rnd.Random(seed)
    nrow=lambda a:(lambda s:max(1,int(round(math.hypot(s[2]-s[0],s[3]-s[1])/pitch))))(segfun(a))
    def row(a,i,n):
        d0,z0,d1,z1=segfun(a);return (d0+(d1-d0)*i/n,z0+(z1-z0)*i/n)
    # risers and treads
    for a0,a1 in zip(A,A[1:]):
        am=(a0+a1)/2;n=nrow(am)
        for i in range(n):
            dm=row(am,i+0.5,n)[0];m=mf(kfun(dm),am,seatmats[0])
            if m is None or m==GRASS:continue
            tm=CONC if m==CONC else TRD
            (e0,f0),(e1,f1)=row(a0,i,n),row(a0,i+1,n);(g0,h0),(g1,h1)=row(a1,i,n),row(a1,i+1,n)
            _q(P(a0,e0,f0),P(a1,g0,h0),P(a1,g0,h1),P(a0,e0,f1),tm)
            _q(P(a0,e0,f1),P(a1,g0,h1),P(a1,g1,h1),P(a0,e1,f1),tm)
    # seats along each row, every 0.5 m of arc
    nmax=max(nrow(a) for a in A)
    for i in range(nmax):
        acc=0.25;prev=None;a=A[0]
        while a<=A[-1]:
            n=nrow(a)
            if i<n:
                dr,zt=row(a,i+1,n);p=P(a,dr,zt)
                if prev is not None:acc+=(p-prev).length
                prev=p
                if acc>=0.5:
                    acc-=0.5;df,_=row(a,i,n);dm=(df+dr)/2;m=mf(kfun(dm),a,seatmats[0])
                    if m in seatmats:
                        col=SGRY if rr.random()<grey else SRED;_seat(a,dr,zt,col);_SEATN[0]+=1
            else:prev=None
            a+=0.04
def _seat(a,dr,zt,col):
    o=P(a,dr,zt);rad=(P(a,dr+1,zt)-o);rad.z=0;rad.normalize();tg=Vector((-rad.y,rad.x,0));up=Vector((0,0,1))
    w=0.22;X=lambda d,u,z:o+rad*d+tg*u+up*z
    # pan (top + front), back (front, top, rear), stem
    _q(X(-0.50,-w,0.44),X(-0.50,w,0.44),X(-0.10,w,0.44),X(-0.10,-w,0.44),col)
    _q(X(-0.50,-w,0.39),X(-0.50,w,0.39),X(-0.50,w,0.44),X(-0.50,-w,0.44),col)
    _q(X(-0.12,-w,0.44),X(-0.12,w,0.44),X(-0.06,w,0.84),X(-0.06,-w,0.84),col)
    _q(X(-0.06,-w,0.84),X(-0.06,w,0.84),X(-0.02,w,0.84),X(-0.02,-w,0.84),col)
    _q(X(-0.08,-w,0.44),X(-0.08,w,0.44),X(-0.02,w,0.84),X(-0.02,-w,0.84),col)
    _q(X(-0.32,-0.04,0.0),X(-0.32,0.04,0.0),X(-0.32,0.04,0.40),X(-0.32,-0.04,0.40),DARK)
_NOR=lambda a:A1-360<=a%360<=A0 or A1-360<=a-360<=A0
def _lowseg(a):
    if (A1-360)<=a<=A0:
        (d0,z0),(d1,z1)=low_pf(a,2),low_pf(a,3);return (d0,z0,d1,z1)
    return (1.5,1.0,6.5,4.0)
def _lowmf(k,a,mi):return low_mn(3,a,mi) if (A1-360)<=a<=A0 else low_m(3,a,mi)
tiers(arange(A1-360,A1,1.0)+[e for e in [x%360 for x in LOWE]+[x%360+360 for x in LOWE]+[x%360-360 for x in LOWE] if A1-360<e<A1],_lowseg,0.70,_lowmf,lambda d:3,(SEAT,),0.0,1)
_SK=[(10.226,6),(11.2,7),(12.9,8),(14.3,9),(15.1,10),(99,11)]
tiers(arange(A0,A1,1.0)+[e for e in UPE if A0<e<A1],lambda a:(9.0,6.4,24.0,16.98),0.86,up_m,lambda d:next(k for x,k in _SK if d<=x),(SEATU,SEAT),0.22,2)
print('SEATS',_SEATN[0])
sweep(span,[(26.0,8.0,None,0),(26.0,9.1,YEL,1)])
def nc_pf(a,k):
    db=ndb(a);zb=1.0+RAKE*(db-1.5);w=max(14.0,db+5.5)
    return [(db if ingap(a) else db+2.0,zb),(w,zb),(w,0.0)][k]
sweep(NA+list(GAP),[(8.5,4.0,None,0),(14.0,4.0,WALK,1),(14.0,0.0,CONC,1)],pf=nc_pf)
# the stands' own end walls (below) close the deeper north seats
for a,flip in((A0,False),(A1,True)):
    for poly in ([(6.5,0),(6.5,4.0),(6.5,6.0),(9.0,6.0),(9.0,6.4),(24,16.98),(24,21),(25,21),(25,8),(16,7),(16,0)],[(25,8),(26,8),(26,7),(16,7)]):
        vs=[bm.verts.new(P(a,d,z)) for d,z in poly];face(vs[::-1] if flip else vs,CONC)
# roof panels between ridges (inward points of the outer scallop line), gaps filled at the median spacing
V=sorted(D['valleys']);med=sorted(V[i+1]-V[i] for i in range(len(V)-1))[len(V)//2]
R=[A0]
for v in V+[A1]:
    while v-R[-1]>1.5*med:R.append(R[-1]+med)
    if v-R[-1]>0.4*med:R.append(v)
R[-1]=A1
# near (west) side: lobe ribs read off the photo's white ribs (x 578-1408), angles by projecting each rib onto the roof
RIBS_NEAR=[128.89,135.5,142.12,149.52,157.89,167.8,177.6,186.6,193.5,200.0,206.4,213.0,219.2,228.9,237.2,243.9,250.5]
if not os.environ.get('SATRIBS'):R=sorted([r for r in R if not (126.0<r<252.5)]+RIBS_NEAR)  # SATRIBS: ribs from the satellite valleys (top-down plan)
print('R near',[round(r,1) for r in R if 115<r<265])
# FARRIBS=file.json: [[inner_deg,outer_deg],...] read off the photo for the far roof (lead 2026-11-19: copy the photo's ribs);
# replaces the satellite ribs between the first and last inner angle. A rib runs from its inner angle (s=0) to its outer angle (s=1).
RI=list(R);RO=list(R)
if os.environ.get('FARRIBS'):
    FR=sorted(json.load(open(os.environ['FARRIBS'])));lo,hi=min(min(p) for p in FR)-0.5,max(max(p) for p in FR)+0.5
    keep=[r for r in R if not lo<r<hi];RI=sorted(keep+[p[0] for p in FR]);RO=sorted(keep+[p[1] for p in FR])
    print('FARRIBS',FR)
def ribat(i,s):return RI[i]+(RO[i]-RI[i])*s
def phase(a,s=0.0):
    for i in range(len(RI)-1):
        r0,r1=ribat(i,s),ribat(i+1,s)
        if r0<=a<=r1:return (a-r0)/(r1-r0)
    return 0.0
# Far roof outer edge from the photo (lead 2026-11-19: deep round scallops, sharp valleys), plan from the satellite.
# FARVR=file.json [[photo valley deg, satellite notch radius m],...]: the plan V at each photo outer valley sits on the
# satellite's measured notch radius; each lobe keeps the satellite crest radius (largest over its middle half):
# r = v(t) + (crest - v(t))*sqrt(sin(pi*t)). FARDZ=m: the outer edge drops by up to FARDZ at each valley (s^2 from the
# inner edge), sized on the photo silhouette.
_FZ=None
if os.environ.get('FARRIBS') and os.environ.get('FARVR'):
    _VR=dict((round(x,2),y) for x,y in json.load(open(os.environ['FARVR'])));_rsat=rout
    _i0=RO.index(min(p[1] for p in FR))-1;_i1=RO.index(max(p[1] for p in FR))+1
    _CR={i:max(_rsat(RO[i]+(RO[i+1]-RO[i])*k/40) for k in range(10,31)) for i in range(_i0,_i1)}
    def _vr(i):return _VR.get(round(RO[i],2),_rsat(RO[i]))
    def rout(a,_r=_rsat):
        for i in range(_i0,_i1):
            if RO[i]<=a<=RO[i+1]:
                t=(a-RO[i])/(RO[i+1]-RO[i]);v=_vr(i)+(_vr(i+1)-_vr(i))*t;return v+(_CR[i]-v)*math.sqrt(max(0.0,math.sin(math.pi*t)))
        return _r(a)
    _FZ=(_i0,_i1,float(os.environ.get('FARDZ',0)))
    print('FARVR',[(round(RO[i],2),round(_vr(i),2),round(_CR[i],2)) for i in range(_i0,_i1)],'FARDZ',_FZ[2])
NEARDZ=float(os.environ.get('NEARDZ',0))
def fardz(a,s,inzone=0):
    if not _FZ:return 0.0
    i0,i1,dz=_FZ
    if not ribat(i0,s)<=a<=ribat(i1,s):return 0.0 if inzone else -NEARDZ*(1-math.sqrt(max(0.0,math.sin(math.pi*phase(a,s)))))*s*s  # rest of the roof: dips at the ribs, depth fitted on the director's photo (director_roof_wave_ref)
    if inzone:return 1.0
    return -dz*(1-math.sqrt(max(0.0,math.sin(math.pi*phase(a,s)))))*s*s
SR=[0,0.03,0.06,0.09,0.12,0.15,0.18,0.21,0.24,0.28,0.32,0.36,0.40,0.45,0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.84,0.88,0.92,0.95,0.975,0.99,1.0]  # dense rows: slanted far ribs cut diagonally across them
NAVYW=5.25  # navy glazed strip inside the white membrane, measured on the photo (near side 5.75, far side 4.5 m)
LOBE_IN=float(os.environ.get('LOBE_IN',0.35));LOBE_OUT=float(os.environ.get('LOBE_OUT',1.1));CAP0=float(os.environ.get('CAP0',0.94));LOBEP=float(os.environ.get('LOBEP',1.5))
LOBE_FAR=float(os.environ.get('LOBE_FAR',LOBE_OUT));FARPOW=float(os.environ.get('FARPOW',1.0))
ra=arange(A0,A1,0.125)
def rp(a,s,dz=0.0):
    ph=phase(a,s);ri=rin(a)-NAVYW+0.8-1.6*math.sin(math.pi*phase(a));ro=rout(a);r=ri+(ro-ri)*s;z=hin(a)+(hout(a)-hin(a))*s
    # inflated tube lobe: round cross-section (sqrt of sine), height grows outward, domed cap at the outer end
    A=LOBE_IN+(LOBE_FAR-LOBE_IN)*s**FARPOW if fardz(a,s,1) else LOBE_IN+(LOBE_OUT-LOBE_IN)*s  # far zone: LOBE_FAR, height kept near the outer edge (photo: flat inner membrane)
    cap=math.sqrt(max(0.0,1-((s-CAP0)/(1-CAP0))**2)) if s>CAP0 else 1.0
    z+=A*max(0.0,math.sin(math.pi*ph))**LOBEP*cap+dz+fardz(a,s)
    t=math.radians(a);return Vector((r*math.cos(t)+SH[0],r*math.sin(t)+SH[1],z))
SH=D.get('roofshift',[0,0])
# navy/white edge: row 7 of every column sits exactly on that column's navy line, so the edge is one smooth line
NBULGE=float(os.environ.get('NBULGE',0.2));NBULGE_NEAR=float(os.environ.get('NBN',-0.8))
def SC(a):
    # navy line on its own radius: rin+0.6 at the ribs, bulging outward mid-lobe (photo, east end: rounded navy lobe ends)
    ph=phase(a);ri=rin(a)-NAVYW+0.8-1.6*math.sin(math.pi*ph);ro=rout(a)
    nb=NBULGE_NEAR if 126.0<a%360<252.5 else NBULGE  # near side: band keeps its width along the scallop (photo)
    nf=(rin(a)+0.6+nb*math.sin(math.pi*ph)-ri)/max(1.0,ro-ri);nf=min(max(nf,0.14),0.40);c=list(SR)
    for j,d in zip(range(5,10),(-0.05,-0.025,0.0,0.025,0.05)):c[j]=nf+d
    for j in range(10,len(c)-1):c[j]=max(c[j],c[j-1]+0.015)  # keep rows in order past the navy rows
    return c
SCA=[SC(a) for a in ra]
top=[[bm.verts.new(rp(a,SCA[i][k])) for i,a in enumerate(ra)] for k in range(len(SR))];bot=[[bm.verts.new(rp(a,SCA[i][k],-0.6)) for i,a in enumerate(ra)] for k in range(len(SR))]
def gridcum(G):
    U=[[0.0]+[0.0]*(len(ra)-1) for _ in SR];Vv=[[0.0]*len(ra) for _ in SR]
    km=len(SR)//2  # one shared U per column (arc length along the middle ring): per-ring U drifted metres apart over 270 deg and sheared the texture into wavy lines
    for i in range(1,len(ra)):U[km][i]=U[km][i-1]+(G[km][i].co-G[km][i-1].co).length
    for k in range(len(SR)):U[k]=list(U[km])
    for k in range(1,len(SR)):
        for i in range(len(ra)):Vv[k][i]=Vv[k-1][i]+(G[k][i].co-G[k-1][i].co).length
    return U,Vv
TU,TV=gridcum(top);BU,BV=gridcum(bot)
for k in range(len(SR)-1):
    for i in range(len(ra)-1):
        sc=(SR[k]+SR[k+1])/2;ph=phase((ra[i]+ra[i+1])/2)
        q=[(k,i),(k,i+1),(k+1,i+1),(k+1,i)]
        am=(ra[i]+ra[i+1])/2;nf=NAVYW/max(1.0,rout(am)-rin(am)+NAVYW)
        face([top[a][b] for a,b in q],NAVY if k<7 else ROOF,[(TU[a][b],TV[a][b]) for a,b in q])
        q=[(k,i+1),(k,i),(k+1,i),(k+1,i+1)]
        face([bot[a][b] for a,b in q],UNDER,[(BU[a][b],BV[a][b]) for a,b in q])
for i in range(len(ra)-1):
    face([top[0][i],bot[0][i],bot[0][i+1],top[0][i+1]],YEL)
    n=len(SR)-1;face([top[n][i+1],bot[n][i+1],bot[n][i],top[n][i]],YEL)
for i in (0,len(ra)-1):
    for k in range(len(SR)-1):face([top[k][i],top[k+1][i],bot[k+1][i],bot[k][i]] if i==0 else [top[k+1][i],top[k][i],bot[k][i],bot[k+1][i]],YEL)
def prism(poly,z0,z1,mside,mtop,uscale=4.0):
    b=[bm.verts.new((x,y,z0)) for x,y in poly];t=[bm.verts.new((x,y,z1)) for x,y in poly];n=len(poly);acc=0
    for i in range(n):
        j=(i+1)%n;L=(Vector(poly[j])-Vector(poly[i])).length
        face([b[i],b[j],t[j],t[i]],mside,[(acc,0),(acc+L,0),(acc+L,z1-z0),(acc,z1-z0)]);acc+=L
    face(t,mtop);face(b[::-1],mtop)
def cyl(p0,p1,r0,r1,mi,n=12):
    p0,p1=Vector(p0),Vector(p1);ax=(p1-p0).normalized();q=ax.orthogonal().normalized();w=ax.cross(q);Ln=(p1-p0).length
    a=[bm.verts.new(p0+(q*math.cos(2*math.pi*i/n)+w*math.sin(2*math.pi*i/n))*r0) for i in range(n)]
    b=[bm.verts.new(p1+(q*math.cos(2*math.pi*i/n)+w*math.sin(2*math.pi*i/n))*r1) for i in range(n)]
    C=2*math.pi*(r0+r1)/2;tw,th=MT[mi]
    for i in range(n):face([a[i],a[(i+1)%n],b[(i+1)%n],b[i]],mi,[(C*i/n,0),(C*(i+1)/n,0),(C*(i+1)/n,Ln),(C*i/n,Ln)])
    def cap(vs,c):return [((v.co-c).dot(q)+0.5*tw,(v.co-c).dot(w)+0.5*th) for v in vs]
    face(b,mi,cap(b,p1));face(a[::-1],mi,cap(a[::-1],p0))
def obox(c,ex,ey,ez,ang,mi,tilt=0.0,front=None,fullfront=False,allsides=False):
    ca,sa=math.cos(ang),math.sin(ang);ux=Vector((ca,sa,0));uy=Vector((-sa,ca,0));uz=Vector((0,0,1))
    rot=Matrix.Rotation(tilt,3,ux);uy2=rot@uy;uz2=rot@uz;C=Vector(c);vs=[]
    for sx,sy,sz in((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)):
        vs.append(bm.verts.new(C+ux*sx*ex+uy2*sy*ey+uz2*sz*ez))
    for fi,m_ in [((0,3,2,1),mi),((4,5,6,7),mi),((0,1,5,4),front if front is not None else mi),((1,2,6,5),mi),((2,3,7,6),mi),((3,0,4,7),mi)]:
        sc_=MT[m_] if ((fullfront and fi==(0,1,5,4)) or (allsides and fi not in((0,3,2,1),(4,5,6,7)))) else (1,1)
        face([vs[i] for i in fi],m_,[(0,0),(sc_[0],0),(sc_[0],sc_[1]),(0,sc_[1])])

def lamphead(x,y,h,ang,HDROP=3.5,HS=1.0,WS=1.0,HF=0.0):
    # deep lattice cage measured from the photo: front frame of lamp shelves, back frame 3 m behind with
    # cross-braced bays, depth members at every shelf; sits 3.5 m lower than before (photo grid, 4 heads)
    fwd=Vector((math.cos(ang),math.sin(ang),0));side=Vector((-math.sin(ang),math.cos(ang),0));up=Vector((0,0,1))
    tl=math.radians(20);fz=fwd*math.cos(tl)-up*math.sin(tl);uz=up*math.cos(tl)+fwd*math.sin(tl)
    C=Vector((x,y,h-5.5-HDROP))+fwd*(0.9+HF)
    def pt(sx,sz,sd=0.0):return C+side*sx+uz*sz+fz*sd
    def bar(a,b,r=0.13,m=TW):cyl(a,b,r,r,m,6)
    H2=5.4*HS;wt,wb=7.4*WS,6.0*WS;DEP=3.0
    hw=lambda z:wb+(wt-wb)*(z+H2)/(2*H2)
    NS=6;zs=[-H2+k*(2*H2)/NS for k in range(NS+1)]
    for sd in (0.0,-DEP):
        bar(pt(-wb,-H2,sd),pt(-wt,H2,sd),0.18);bar(pt(wb,-H2,sd),pt(wt,H2,sd),0.18)
        for z in zs:bar(pt(-hw(z),z,sd),pt(hw(z),z,sd),0.15 if sd==0.0 else 0.13)
    # back face: 4 verticals and X-bracing in every bay
    fr=[-1,-0.5,0,0.5,1]
    for f_ in fr[1:-1]:bar(pt(f_*wb,-H2,-DEP),pt(f_*wt,H2,-DEP))
    for k in range(NS):
        z0,z1=zs[k],zs[k+1]
        for j in range(len(fr)-1):
            a0,a1=fr[j],fr[j+1]
            bar(pt(a0*hw(z0),z0,-DEP),pt(a1*hw(z1),z1,-DEP),0.1);bar(pt(a1*hw(z0),z0,-DEP),pt(a0*hw(z1),z1,-DEP),0.1)
    # depth members at every shelf end and the middle, diagonals on the two sides
    for z in zs:
        for f_ in (-1,0,1):bar(pt(f_*hw(z),z,0),pt(f_*hw(z),z,-DEP),0.11)
    for k in range(NS):
        for sx in (-1,1):bar(pt(sx*hw(zs[k]),zs[k],0),pt(sx*hw(zs[k+1]),zs[k+1],-DEP),0.09)
    for i in range(NS):
        z=(zs[i]+zs[i+1])/2;w=hw(z)-0.3
        obox(pt(0,zs[i]+0.1,-0.9),w,0.9,0.07,ang+math.pi/2,TW,tilt=-tl)
        n=8 if i<2 else 10
        for j in range(n):
            sx=-w+0.45+j*(2*w-0.9)/(n-1);p0=pt(sx,z,-1.2);p1=pt(sx,z,0.25)
            cyl(p0,p1,0.36,0.42,LAMP,10)
# per-tower head drop (m) and head height scale, each read off that tower on the photo grid
THD={(93.8,72.4):(1.1,0.88,0.82,0),(92.3,-36.1):(0.4,0.88,0.84,0),(-92.8,36.1):(3.5,1.0,1.0,0),(-90.7,-78.7):(3.5,1.0,1.0,0),(-26.8,112.5):(4.6,1.1,1.0,2.5),(38.8,-123.7):(5.2,1.2,1.0,0)}
# towers: thick white shafts (photo grid: 3.1-3.5 m across), lamp cage on top; measured base for the S1 tower
TPOS={(-92.8,36.1):(-92.8,34.2),(92.3,-36.1):(92.58,-39.13),(-26.8,112.5):(-26.96,113.97)}
for x,y,h in D['towers']:
    hd,hs,ws,hf=THD[(x,y)];x,y=TPOS.get((x,y),(x,y))
    ang=math.atan2(-y,-x);hb=h-5.5-hd;cyl((x,y,0),(x+hf*math.cos(ang),y+hf*math.sin(ang),hb),1.75,1.25,TW,20);cyl((x,y,0),(x,y,2.0),2.3,2.2,CONC,20)
    ang=math.atan2(-y,-x);lamphead(x,y,h,ang,hd,hs,ws,hf)
# scoreboard (north end)
L,Rr,zb,zt=D['scoreboard'];L=Vector((*L,0));Rr=Vector((*Rr,0));mid=(L+Rr)/2;ang=math.atan2(Rr.y-L.y,Rr.x-L.x);half=(Rr-L).length/2
obox((mid.x,mid.y,(zb+zt)/2),half+2.0,0.7,(zt-zb)/2,ang,NAVY,front=SBF,fullfront=True)  # board runs over the end posts (photo grid: corners ~6 px past L/R)
for e in (L,Rr):
    # end posts measured on the photo grid: outer face flush with the board end, 1.2 m thick, 3.4 m deep
    # (end face spans x425-440 at 4.5 px/m: from 0.5 m behind the board line to 2.9 m in front), top 12.2 m
    d=(e-mid).normalized();uyp=Vector((-math.sin(ang),math.cos(ang),0));o=e+d*2.0-d*0.6-uyp*1.2;obox((o.x,o.y,6.1),0.6,1.7,6.1,ang,SBP,allsides=True)
# legs and the red sign under the board (positions along the board measured on the photo grid: legs 0.37/0.71, sign 0.40-0.68)
ux_=(Rr-L).normalized();uy_=Vector((-ux_.y,ux_.x,0))
for f_ in (0.37,0.71):
    p_=L+ux_*(2*half*f_);cyl((p_.x,p_.y,0),(p_.x,p_.y,zb),0.35,0.35,WHITE,10)
p_=L+ux_*(2*half*0.54)-uy_*1.5;obox((p_.x,p_.y,1.3),4.15,0.25,1.3,ang,WHITE,front=RSG,fullfront=True)
# west podium (striped facade, flat roof) from the satellite footprint, plus the dark entrance block
POLY=[(-103,45),(-128,20.5),(-132.5,15.5),(-135,11),(-134.5,7),(-131,2),(-97,-39),(-90,-39),(-90,45)]
prism(POLY,0,10.6,STR,POD,uscale=12.0)
prism([(-105.2,46.1),(-99.7,60.1),(-86,56),(-92,40)],10.6,21.5,DARK,DARK)
prism([(-105.2,46.1),(-99.7,60.1),(-86,56),(-90.1,45.3),(-103,45.3)],0,10.6,DARK,DARK)
# lower front-right wing of the dark block on the podium roof, carrying the S1 tower (photo corners unprojected at z 10.6/16)
prism([(-105.2,46.1),(-96.5,29.2),(-90.7,27.0),(-91.5,40.0)],10.6,16.0,DARK,DARK)
# rooftop plant on the dark block (positions read off the photo grid, unprojected at z 21.5): units, ducts, parapet
for (px_,py_,ex,ey,ez,a_) in [(-91.4,56.0,1.6,1.1,0.9,0.37),(-97.0,50.0,2.4,1.3,1.0,0.37),(-93.6,46.0,1.8,1.2,0.8,0.37),
                             (-100.6,53.0,1.4,1.0,0.7,0.37),(-96.0,44.0,1.2,0.9,1.1,0.37),(-99.8,47.8,1.0,1.0,0.6,0.37)]:
    obox((px_,py_,21.5+ez),ex,ey,ez,a_,CONC)
cyl((-95.5,57.5,21.5),(-95.5,57.5,23.2),0.9,0.9,CONC,12);cyl((-89.5,50.5,21.5),(-89.5,50.5,22.8),0.7,0.7,CONC,12)
cyl((-98.5,55.0,22.3),(-92.0,48.0,22.3),0.35,0.35,CONC,8);cyl((-101.0,51.0,22.0),(-95.0,45.0,22.0),0.3,0.3,CONC,8)
prism([(-63,86.5),(-86,63.5),(-84,61.5),(-61.5,84.5)],0,10.3,STR,DARK,uscale=12.0)

# buildings under the near roof, measured from the photo (white, flat roofs), the tank and the red drum on the podium
# SE outbuildings, roofs read off the photo grid and unprojected at z 3 (photo: low flat-roofed blocks, ~3 m)
prism([(-93.5,-46.3),(-84.7,-68.6),(-92.5,-77.7),(-105.5,-78.0),(-110.8,-69.5),(-111.6,-62.2),(-99.1,-61.2),(-98.3,-68.7),(-110.8,-69.5)][:6]+[(-112.6,-48.1)],0,3.0,WHITE,WHITE)
obox((-105.2,-65.6,3.6),3.2,2.6,0.6,math.radians(-80),DARK)
prism([(-66.7,-93.0),(-65.1,-108.0),(-74.8,-116.1),(-79.7,-113.4),(-81.3,-99.2),(-74.8,-93.9)],0,3.0,WHITE,WHITE)
cyl((-66.0,-112.5,0),(-66.0,-112.5,5.0),2.2,2.2,DARK,24)
# white fabric-roof building: dark walls to 3 m, domed membrane to 6.5 m (outline unprojected at z 3)
DOME=[(-100.8,-99.7),(-94.9,-104.9),(-93.9,-113.7),(-98.6,-119.1),(-109.3,-120.3),(-116.3,-110.8),(-114.7,-104.8),(-106.9,-100.0)]
prism(DOME,0,3.0,DARK,DARK)
dc=Vector((sum(p[0] for p in DOME)/8,sum(p[1] for p in DOME)/8,0));rings=[]
for k in range(6):
    t=k/5;rr_=math.cos(t*math.pi/2);zz=3.0+3.5*math.sin(t*math.pi/2)
    rings.append([bm.verts.new((dc.x+(p[0]-dc.x)*rr_,dc.y+(p[1]-dc.y)*rr_,zz)) for p in DOME])
for k in range(5):
    for j in range(8):face([rings[k][j],rings[k][(j+1)%8],rings[k+1][(j+1)%8],rings[k+1][j]][::-1],ROOF)
dr=[];cx,cy_,rr=-97.5,-14.4,5.6
for i in range(13):
    t=math.radians(90+180*i/12);dr.append((cx+rr*math.cos(t),cy_+rr*math.sin(t)))
prism(dr,10.6,21.0,RED,DARK,uscale=40.0)
# white ribs across the navy strip at every lobe dip
for i in range(1,len(RI)-1):
    a=RI[i];nf=SC(a)[7];cyl(rp(a,0.0,0.08),rp(ribat(i,nf),nf,0.08),0.14,0.14,WHITE,6)
# yellow raking columns under the west and south-west roof edge, one per ridge
# near side: flat dark underside 1.0 m below the roof edge, from the edge in to the stand's outer wall, and the wall face
# carried up to meet it (lead 2026-11-20 "Seats + underside"; photo: dark band just under the gutter; lower, it hid the red board)
UNDZ=1.0
_UA=arange(NEARW[0],NEARW[1],0.125)  # same step as the roof grid, so no slice spans a rib cusp
for _a0,_a1 in zip(_UA,_UA[1:]):
    _q2=[]
    for _a in (_a0,_a1):
        _e=rp(_a,1.0,0.0);_zl=hout(_a)-UNDZ;_w=P(_a,25.0,0.0)
        # inner end: never above the roof's under-surface at the wall line (r34 poked through the membrane there)
        _ri=rin(_a)-NAVYW+0.8-1.6*math.sin(math.pi*phase(_a));_sw=min(1.0,max(0.0,((_w-Vector((SH[0],SH[1],0))).length-_ri)/max(1.0,rout(_a)-_ri)))
        _zi=min(_zl,min(rp(_a,_sw+d,-0.6).z for d in (-0.06,-0.03,0.0,0.03,0.06) if 0<=_sw+d<=1)-0.4);_zl=min(_zl,rp(_a,0.97,-0.6).z-0.4)
        _q2.append((Vector((_e.x,_e.y,_zl)),P(_a,25.0,_zi),P(_a,25.0,21.0),_zi,_sw))
    # split edge-to-wall into 8 strips, each kept 0.4 m under the roof's under-surface (the rib dips sag below a straight chord)
    _rows=[]
    for _j,(_e2,_w2,_,_zi2,_sw2) in enumerate(_q2):
        _a=(_a0,_a1)[_j];_r=[]
        for _k in range(9):
            _u=_k/8;_v=_e2.lerp(_w2,_u);_s=1.0-(1.0-_sw2)*_u
            _dv=Vector((_v.x-SH[0],_v.y-SH[1],0));_av=math.degrees(math.atan2(_dv.y,_dv.x))%360
            _ri2=rin(_av)-NAVYW+0.8-1.6*math.sin(math.pi*phase(_av));_s=(_dv.length-_ri2)/max(1.0,rout(_av)-_ri2)  # the roof point straight above this one
            _r.append(Vector((_v.x,_v.y,min(_v.z,min(rp(_av+da,min(1.0,max(0.0,_s+d)),-0.6).z for d in (-0.03,0.0,0.03) for da in (-0.1,0.0,0.1))-0.4))))
        _rows.append(_r)
    for _k in range(8):face([bm.verts.new(v) for v in (_rows[0][_k],_rows[1][_k],_rows[1][_k+1],_rows[0][_k+1])],DARK)
    if _q2[0][3]>21.0 and _q2[1][3]>21.0:face([bm.verts.new(v) for v in (_q2[0][1],_q2[1][1],_q2[1][2],_q2[0][2])],DARK)
R=RO  # columns and later rib users stand under the outer rib ends
for i in range(1,len(R)-1):
    a=R[i]
    if NEARW[0]<=a%360<=NEARW[1]:
        tp=rp(a,1.0,-0.3);cyl(tp,Vector((tp.x,tp.y,hout(a)-POSTL)),0.35,0.35,YEL,8);continue
    t=math.radians(a);ro=rout(a)-9;g0=Vector((ro*math.cos(t)+SH[0],ro*math.sin(t)+SH[1],0));fk=Vector((g0.x,g0.y,9.0))
    cyl(g0,fk,0.45,0.4,YEL,8)
    for da in (-0.32,0.32):
        a2=a+da*(R[i+1]-R[i] if da>0 else R[i]-R[i-1]);cyl(fk,rp(a2,0.93,-0.6),0.35,0.3,YEL,8)
# the ground's own sign, People First Stadium (current photo, drone from the south): a flat navy panel hung on the
# yellow columns behind the south-end stand (2.4 m out from the column feet, in front of the raking arms, as in the photo), centred on the 250 deg rib, 39 m wide, 7.33:1, bottom 8.75 m above the ground (just above the
# concourse slab). Lettering hand-painted in handtex.py.
ci=min(range(1,len(R)-1),key=lambda i:abs(R[i]-250.0));a=R[ci];t=math.radians(a)
ro=rout(a)-9;cb=Vector((ro*math.cos(t)+SH[0],ro*math.sin(t)+SH[1],0));n_=Vector((math.cos(t),math.sin(t),0));tg=Vector((-math.sin(t),math.cos(t),0))
sw_=39.0;sh_=sw_/7.33;c_=cb+n_*2.4;z0_=8.75  # width and bottom fitted with the photo's camera (c6cam.py: sign corners + three V-column feet, 1.6 px)
print('sign rib',round(a,2),'width',round(sw_,1),'height',round(sh_,2))
vs=[bm.verts.new(c_+tg*(sx*sw_/2)+Vector((0,0,z))) for sx,z in ((-1,z0_),(1,z0_),(1,z0_+sh_),(-1,z0_+sh_))]
tw_,th_=MT[PFS];face(vs,PFS,[(0,0),(tw_,0),(tw_,th_),(0,th_)])
vs=[bm.verts.new(c_+tg*(sx*sw_/2)-n_*0.15+Vector((0,0,z))) for sx,z in ((-1,z0_),(1,z0_),(1,z0_+sh_),(-1,z0_+sh_))];face(vs[::-1],NAVY)
# vomitories: opening in the upper tier at each measured angle, 2.4 m wide, front 1.5 m up the slope, hood over 3 m
def T(a,sl,dz=0.0):
    t=sl/11.62;d=9.0+9.5*t;z=6.4+6.7*t+dz;r=rg(a)+d;th=math.radians(a);return Vector((r*math.cos(th),r*math.sin(th),z))
VPROF=[(9.0,6.0),(9.0,6.4),(10.226,7.265),(11.2,7.952)]
for c in VOMS:
    if not (A0<c<A1):continue
    hw=math.degrees(VHW/(rg(c)+11));al,ar=c-hw,c+hw
    # floor of the tunnel (dark), side walls along the cut seat line (concrete), back wall dark under a red cap
    z0,dB,zT=7.265,14.3,10.139
    face([bm.verts.new(v) for v in (P(al,10.226,z0),P(ar,10.226,z0),P(ar,dB,z0),P(al,dB,z0))][::-1],DARK)
    for aa,fl in ((al,False),(ar,True)):
        vs=[bm.verts.new(P(aa,d,z)) for d,z in [(10.226,z0),(11.2,7.952),(dB,zT),(dB,z0)]];face(vs[::-1] if fl else vs,VBLUE)
    zc=zT-0.8
    face([bm.verts.new(v) for v in (P(al,dB,z0),P(ar,dB,z0),P(ar,dB,zc),P(al,dB,zc))],DARK)
    face([bm.verts.new(v) for v in (P(al,dB,zc),P(ar,dB,zc),P(ar,dB,zT),P(al,dB,zT))],RED)
bm.normal_update()
for f in bm.faces:
    if f in UVSET:continue
    n=f.normal;tw,th=MT[f.material_index]
    if abs(n.z)>0.7:co=[(l.vert.co.x,l.vert.co.y) for l in f.loops]
    else:
        t=Vector((-n.y,n.x,0));t=t.normalized() if t.length>1e-6 else Vector((1,0,0));co=[(l.vert.co.dot(t),l.vert.co.z) for l in f.loops]
    for l,c in zip(f.loops,co):l[uv].uv=(c[0]/tw,c[1]/th)
bm.to_mesh(me);bm.free()
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out),export_format='GLB')
if os.environ.get('SAVEBLEND'):bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.environ['SAVEBLEND']))
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=2000;sc.render.resolution_y=1333;sc.render.film_transparent=True
cd=bpy.data.cameras.new('cam');cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=CAM[6]*36/2000;cd.clip_end=5000;cd.clip_start=50
co=bpy.data.objects.new('cam',cd);sc.collection.objects.link(co);sc.camera=co
def RR(yaw,p_,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(p_),math.sin(p_);cr,sr=math.cos(roll),math.sin(roll)
    f=Vector((cy*cp,sy*cp,sp));r=Vector((sy,-cy,0.0));u=r.cross(f)
    return [cr*r+sr*u,-sr*r+cr*u,f]
M=RR(*CAM[3:6])
Mb=Matrix(((M[0][0],M[1][0],-M[2][0]),(M[0][1],M[1][1],-M[2][1]),(M[0][2],M[1][2],-M[2][2])))
co.matrix_world=Matrix.Translation(Vector(CAM[:3]))@Mb.to_4x4()
sd=bpy.data.lights.new('sun','SUN');sd.energy=2.7;so=bpy.data.objects.new('sun',sd);sc.collection.objects.link(so)
so.rotation_euler=(math.radians(40),0,math.radians(-141))
w=bpy.data.worlds.new('w');w.use_nodes=True;bg=w.node_tree.nodes['Background'];bg.inputs['Color'].default_value=(0.55,0.6,0.68,1);bg.inputs['Strength'].default_value=0.55;sc.world=w
sc.view_settings.view_transform='Standard'
sc.render.filepath=os.path.abspath(rpng);bpy.ops.render.render(write_still=True)
