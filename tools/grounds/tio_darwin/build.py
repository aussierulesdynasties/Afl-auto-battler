# blender -b --python build.py -- OUTDIR [params.json]
# TIO Stadium (Marrara Oval, Darwin) as it is today (2025 photos). Frame: origin = OSM pitch centroid, x east, y north, z up, metres.
# Plan from straight-down sources only: OSM outlines (osm_m.json) and the Esri z19 satellite (roof traces in roofs.json / PAUSE.md).
# Heights from the camera fits (params.json, written by fit.py). Stadium only: field, posts, nets, crowd, ads, temporary stands left out.
import bpy,bmesh,json,math,sys,os
from mathutils import Vector,Matrix
HERE=os.path.dirname(os.path.abspath(__file__))
A=sys.argv[sys.argv.index('--')+1:];OUT=os.path.abspath(A[0]);os.makedirs(OUT,exist_ok=True)
PJ=json.load(open(A[1])) if len(A)>1 else {}
def p(k,d):return PJ.get(k,d)
TJ=json.load(open(os.path.join(HERE,'tex','tex.json')));TILE=TJ['TILE']
OSM=json.load(open(os.path.join(HERE,'osm_m.json')))
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
M={}
ALPHA=('chainlink','palisade','rail_orange')
def mat(n):
    if n in M:return M[n]
    m=bpy.data.materials.new(n);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF'];b.inputs['Roughness'].default_value=0.85
    f=os.path.join(HERE,'tex',n+'.png')
    if os.path.exists(f):
        t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(f);nt.links.new(t.outputs['Color'],b.inputs['Base Color'])
        if n in ALPHA:
            nt.links.new(t.outputs['Alpha'],b.inputs['Alpha'])
            if hasattr(m,'surface_render_method'):m.surface_render_method='BLENDED'
            m.use_backface_culling=False
    else:
        b.inputs['Base Color'].default_value={'lamp':(0.85,0.86,0.84,1),'white':(0.9,0.9,0.88,1)}.get(n,(1,0,1,1))
    if n.startswith('glass'):b.inputs['Roughness'].default_value=0.25;b.inputs['Specular IOR Level'].default_value=0.6
    if n.startswith('steel'):b.inputs['Metallic'].default_value=0.3;b.inputs['Roughness'].default_value=0.5
    M[n]=m;return m
cols={}
def coll(n):
    if n not in cols:
        c=bpy.data.collections.new(n);sc.collection.children.link(c);cols[n]=c
    return cols[n]
def world_uv(bm,m):
    tu,tv=TILE.get(m,[4,4]);ul=bm.loops.layers.uv.new('UV')
    for fa in bm.faces:
        n=fa.normal
        if abs(n.z)>=max(abs(n.x),abs(n.y)):
            for l in fa.loops:co=l.vert.co;l[ul].uv=(co.x/tu,co.y/tv)
        else:   # walls: u along the wall's own horizontal direction, v = height
            h=Vector((-n.y,n.x,0)).normalized()
            for l in fa.loops:co=l.vert.co;l[ul].uv=((co.x*h.x+co.y*h.y)/tu,co.z/tv)
def mk(name,V,F,m,UV=None,c='model'):
    me=bpy.data.meshes.new(name);bm=bmesh.new();vs=[bm.verts.new(v) for v in V]
    uvl=bm.loops.layers.uv.new('UV') if UV else None
    for i,f in enumerate(F):
        try:fa=bm.faces.new([vs[j] for j in f])
        except ValueError:continue
        if UV:
            for l,uv in zip(fa.loops,UV[i]):l[uvl].uv=uv
    bm.normal_update()
    if not UV:world_uv(bm,m)
    bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(name,me);coll(c).objects.link(o);me.materials.append(mat(m));return o
class Acc:   # collects many faces into one object per material
    def __init__(s,name,m,uv=False):s.n=name;s.m=m;s.V=[];s.F=[];s.UV=[] if uv else None
    def face(s,pts,uv=None):
        o=len(s.V);s.V+=[tuple(q) for q in pts];s.F.append(tuple(range(o,o+len(pts))))
        if s.UV is not None:s.UV.append(uv)
    def quad2(s,pts,uv=None):   # two-sided
        s.face(pts,uv);s.face(pts[::-1],uv[::-1] if uv else None)
    def done(s,c='model'):
        if s.F:return mk(s.n,s.V,s.F,s.m,s.UV,c)
def prism(name,fp,z0,z1,wall,top=None,bottom=False):
    n=len(fp);V=[(x,y,z0) for x,y in fp]+[(x,y,z1) for x,y in fp]
    F=[(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)]
    if bottom:F.append(tuple(range(n-1,-1,-1)))
    if top is None:F.append(tuple(range(n,2*n)))
    o=mk(name,V,F,wall)
    if top:mk(name+'_top',[(x,y,z1) for x,y in fp],[tuple(range(n))],top)
    return o
def cyl(name,c,r,z0,z1,m,seg=24,cap=True):
    V=[(c[0]+r*math.cos(2*math.pi*i/seg),c[1]+r*math.sin(2*math.pi*i/seg),z) for z in (z0,z1) for i in range(seg)]
    F=[(i,(i+1)%seg,seg+(i+1)%seg,seg+i) for i in range(seg)]
    if cap:F.append(tuple(range(seg,2*seg)));F.append(tuple(range(seg-1,-1,-1)))
    return mk(name,V,F,m)
def rod(acc,p,q,r,seg=6):
    p=Vector(p);q=Vector(q);d=(q-p);rot=d.to_track_quat('Z','Y').to_matrix();L=d.length
    ring=[[tuple(p+rot@Vector((r*math.cos(2*math.pi*i/seg),r*math.sin(2*math.pi*i/seg),z))) for i in range(seg)] for z in (0,L)]
    for i in range(seg):j=(i+1)%seg;acc.face([ring[0][i],ring[0][j],ring[1][j],ring[1][i]])
def box(acc,c,u,v,w,hu,hv,hw):   # oriented box: centre c, unit axes u,v,w, half sizes
    c=Vector(c);P=[c+u*a*hu+v*b*hv+w*e*hw for a in(-1,1) for b in(-1,1) for e in(-1,1)]
    for f in ((0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)):acc.face([tuple(P[i]) for i in f])
def board(name,a,b,z0,z1,m,two=False):
    V=[(a[0],a[1],z0),(b[0],b[1],z0),(b[0],b[1],z1),(a[0],a[1],z1)];F=[(0,1,2,3)];UV=[[(0,0),(1,0),(1,1),(0,1)]]
    if two:F.append((1,0,3,2));UV.append([(0,0),(1,0),(1,1),(0,1)])
    return mk(name,V,F,m,UV)
# ---------------- boundary fence: OSM pitch outline, galvanised chain-link about 1.1 m (07, 10, 18)
pitch=OSM['pitch']
if pitch[0]==pitch[-1]:pitch=pitch[:-1]
FH=p('fence_h',1.1);fz=Acc('boundary_fence','chainlink',True);s=0;tu=TILE['chainlink'][0]
for i in range(len(pitch)):
    a=pitch[i];b=pitch[(i+1)%len(pitch)];L=math.dist(a,b)
    fz.quad2([(a[0],a[1],0),(b[0],b[1],0),(b[0],b[1],FH),(a[0],a[1],FH)],[(s/tu,0),((s+L)/tu,0),((s+L)/tu,1),(s/tu,1)]);s+=L
fz.done()
# ---------------- Maurice Rioli Stand (west). Front line: ellipse a=76, b=93 about the pitch centre (sits 4 m behind the boundary,
# the walkway in 10/11; it lies on the satellite roof front within ~1.5 m). Depth d is measured out along the ellipse normal.
EA,EB=p('ea',76.0),p('eb',93.0)
def E(t):return Vector((-EA*math.cos(t),EB*math.sin(t),0))
def Nrm(t):x,y=-EA*math.cos(t),EB*math.sin(t);n=Vector((x/EA**2,y/EB**2,0));return n.normalized()
def P(t,d,z):q=E(t)+Nrm(t)*d;return (q.x,q.y,z)
TC=math.asin(30/EB);TN=math.asin(p('north_end_y',65.0)/EB);TS=-math.asin(p('south_end_y',68.8)/EB)
NROW=p('rows',16);ROWD=0.8;Z0=p('rake_z0',1.3);RISE=p('rise',0.325);DR=0.6     # rake starts 0.6 m behind the front wall
ZB=Z0+NROW*RISE;DB=DR+NROW*ROWD                                                # back of the rake
def tsteps(t0,t1,step=2.5):
    L=abs(t1-t0)*0.5*(EA+EB);n=max(2,int(L/step));return [t0+(t1-t0)*i/n for i in range(n+1)]
steps=Acc('stand_steps','concrete');conc=Acc('stand_concrete','concrete');soff=Acc('stand_rake_soffit','concrete')
# real 3D tip-up seats, empty, in the 2025 mosaic (10, 11, 15, 16, 17): 0.5 m pitch, 1.2 m aisle every 12 m; colour runs of 2-7 seats,
# 55 % of seats take the colour of the seat in front (the blocky patches in the photos). No crowd.
import random;SR=random.Random(7);SEATW=0.5;AISLE=1.2;BAY=12.0
SPAL=['seat_blue','seat_orange','seat_purple','seat_red','seat_teal'];SW=[0.27,0.31,0.42,0.0,0.0]   # photo 17: blue, orange, purple only
SACC={k:Acc('stand_'+k,k) for k in SPAL};SROW={};SPREV={};steelA=Acc('seat_pedestal','steel_dark')
# photo 17: clean diagonal bands; each row repeats the row below shifted one seat, band widths in seats (blue 9, orange 5, purple 3 of 17)
BANDS=[(0,4),(1,3),(0,3),(2,3),(0,2),(1,2)];BSEQ=[k for k,n in BANDS for _ in range(n)]
def seat_colour(r,q):return SPAL[BSEQ[(int(round(q/SEATW))-r)%len(BSEQ)]]
# one empty tip-up seat, pan folded up (photo 17), as two closed solid shells: local x across, y back from the riser edge, z up
def _slab(f,N,M,T):
    Q=[];xs=[k/N for k in range(N+1)];vs=[k/M for k in range(M+1)]
    for a in range(N):
        for b in range(M):
            Q.append([f(xs[a],vs[b],0),f(xs[a+1],vs[b],0),f(xs[a+1],vs[b+1],0),f(xs[a],vs[b+1],0)])
            Q.append([f(xs[a],vs[b],T),f(xs[a],vs[b+1],T),f(xs[a+1],vs[b+1],T),f(xs[a+1],vs[b],T)])
    for a in range(N):
        for v in (0,1):
            q=[f(xs[a],v,0),f(xs[a+1],v,0),f(xs[a+1],v,T),f(xs[a],v,T)];Q.append(q if v==0 else q[::-1])
    for b in range(M):
        for u in (0,1):
            q=[f(u,vs[b],0),f(u,vs[b],T),f(u,vs[b+1],T),f(u,vs[b+1],0)];Q.append(q if u==0 else q[::-1])
    return Q
def _seat_template(HW=0.22):
    def back(u,v,t):   # curved shell, sides wrap forward, slight lean back
        x=(2*u-1)*HW*(1-0.08*v);return (x,0.36+0.10*v-0.06*(2*u-1)**2+t,0.40+0.42*v)
    def pan(u,v,t):    # folded pan standing in front of the back
        x=(2*u-1)*HW*0.92;return (x,0.27+0.04*v-0.04*(2*u-1)**2-t,0.30+0.36*v)
    return _slab(back,6,4,0.045)+_slab(pan,6,3,0.04)
SEATQ=_seat_template()
SIDX={}
def rake(ts,s0=0.0):
    s=s0
    for i in range(len(ts)-1):
        t0,t1=ts[i],ts[i+1];L=math.dist(P(t0,0,0)[:2],P(t1,0,0)[:2])
        # front wall
        conc.face([P(t0,0,0),P(t1,0,0),P(t1,0,Z0),P(t0,0,Z0)][::-1]);conc.face([P(t0,0,Z0),P(t1,0,Z0),P(t1,DR,Z0),P(t0,DR,Z0)][::-1])
        for r in range(NROW):
            d0=DR+r*ROWD;z0=Z0+r*RISE;z1=z0+RISE;v=r/NROW
            steps.face([P(t0,d0,z0),P(t0,d0,z1),P(t1,d0,z1),P(t1,d0,z0)])              # riser
            steps.face([P(t0,d0,z1),P(t0,d0+ROWD,z1),P(t1,d0+ROWD,z1),P(t1,d0,z1)])  # tread
            a0=Vector(P(t0,d0,z1));a1=Vector(P(t1,d0,z1));b0=Vector(P(t0,d0+ROWD,z1));al=(a1-a0).normalized();bk=((b0-a0)-al*al.dot(b0-a0)).normalized();up=Vector((0,0,1))
            q=math.ceil(s/SEATW-1e-6)*SEATW
            while q+SEATW<=s+L+1e-6:
                if (q%BAY)>=AISLE-1e-6:
                    i=SIDX.get(r,0);SIDX[r]=i+1;acc=SACC[seat_colour(r,q)];c=a0+al*(q-s+SEATW/2)
                    for qd in SEATQ:acc.face([c+al*x+bk*y+up*z for x,y,z in qd])   # bucket seat template (photo 17)
                    box(steelA,c+bk*0.38+up*0.20,al,bk,up,0.03,0.03,0.20)   # pedestal under the shell
                q+=SEATW
        soff.face([P(t0,0.3,0),P(t1,0.3,0),P(t1,DB,ZB-0.6),P(t0,DB,ZB-0.6)])   # underside seen from the back (06)
        s+=L
    return s
# ---- wings: deck behind the rake, kiosk wall under it, roof in three steps down toward each end (09, 10, 11)
WDECK=p('wing_deck',3.5);WROOF_D=p('wing_roof_d',17.0);RZ=p('wing_roof_z',[13.8,13.0,12.2]);RTH=0.5
deck=Acc('wing_deck','concrete');kiosk=Acc('wing_kiosk','clad_grey');rail=Acc('wing_rail','rail_orange',True)
rf=Acc('wing_roof','roof_white');ru=Acc('wing_roof_under','roof_under');fas=Acc('wing_fascia','clad_cream');stl=Acc('wing_steel','steel_dark')
def wing(t_in,t_end):
    ts=tsteps(t_in,t_end);rake(ts)
    for i in range(len(ts)-1):
        t0,t1=ts[i],ts[i+1];D2=DB+WDECK
        deck.face([P(t0,DB,ZB),P(t0,D2,ZB),P(t1,D2,ZB),P(t1,DB,ZB)][::-1] if t1<t0 else [P(t0,DB,ZB),P(t1,DB,ZB),P(t1,D2,ZB),P(t0,D2,ZB)])
        deck.face([P(t0,D2,ZB),P(t1,D2,ZB),P(t1,D2,ZB-0.4),P(t0,D2,ZB-0.4)])
        L=math.dist(P(t0,D2,0)[:2],P(t1,D2,0)[:2])
        rail.quad2([P(t0,D2,ZB),P(t1,D2,ZB),P(t1,D2,ZB+1.1),P(t0,D2,ZB+1.1)],[(0,0),(L/2,0),(L/2,1),(0,1)])
        kiosk.quad2([P(t0,DB-1.5,0),P(t1,DB-1.5,0),P(t1,DB-1.5,ZB-0.9),P(t0,DB-1.5,ZB-0.9)])
    # roof steps: three equal segments from the inner end to the outer end
    n=len(ts)-1;seg=[ts[:n//3+1],ts[n//3:2*n//3+1],ts[2*n//3:]]
    for k,tt in enumerate(seg):
        z=RZ[k];zb=z-p('roof_fall',1.6)
        for i in range(len(tt)-1):
            t0,t1=tt[i],tt[i+1];q=[P(t0,-0.5,z),P(t1,-0.5,z),P(t1,WROOF_D,zb),P(t0,WROOF_D,zb)]
            if t1<t0:q=q[::-1]
            rf.face(q);ru.face([(a[0],a[1],a[2]-RTH) for a in q[::-1]])
            fas.quad2([P(t0,-0.5,z-RTH-0.6),P(t1,-0.5,z-RTH-0.6),P(t1,-0.5,z),P(t0,-0.5,z)])
            fas.quad2([P(t0,WROOF_D,zb-RTH),P(t1,WROOF_D,zb-RTH),P(t1,WROOF_D,zb),P(t0,WROOF_D,zb)])
        # step face at the segment's end and the columns carrying the roof (one per 9 m at the deck's back edge)
        te=tt[-1];zn=RZ[k+1] if k<2 else 0
        a,b=P(te,-0.5,0),P(te,WROOF_D,0)
        fas.quad2([(a[0],a[1],max(zn,z-RTH-0.6)),(b[0],b[1],max(zn,zb-RTH)-(1.6 if k==2 else 0)),(b[0],b[1],zb),(a[0],a[1],z)])
        for t in tt[::4]:
            c=P(t,DB+WDECK-0.6,0);rod(stl,(c[0],c[1],0),(c[0],c[1],zb-RTH-0.1),0.22,8)
            # raking strut from the column head to the front third of the roof (10, 11 show the black trusses)
            f2=P(t,4,0);rod(stl,(c[0],c[1],zb-RTH-0.3),(f2[0],f2[1],z-RTH-0.2-(z-zb)*4/WROOF_D),0.12,6)
wing(TC,TN);wing(-TC,TS)
# ---- centre: rake, Rioli band, glass boxes, rear building to the straight back wall at x=-111.5 (satellite), grey roof
cts=tsteps(-TC,TC);rake(cts)
CB=Acc('centre_band','clad_dark');GB=Acc('centre_boxes','glass_box',False);CF=Acc('centre_floor','concrete')
BOXD=p('box_d',4.5);ZBAND=p('box_z',[9.8,12.1])[0];ZBOX=p('box_z',[9.8,12.1])[1]   # 2016 front photo: glass 9.8-12.1 m
for i in range(len(cts)-1):
    t0,t1=cts[i],cts[i+1]
    CB.face([P(t0,DB,ZB),P(t1,DB,ZB),P(t1,DB,ZBAND),P(t0,DB,ZBAND)][::-1])
    GB.face([P(t0,DB+0.3,ZBAND),P(t1,DB+0.3,ZBAND),P(t1,DB+0.3,ZBOX),P(t0,DB+0.3,ZBOX)][::-1])
    CB.face([P(t0,DB+0.3,ZBOX),P(t1,DB+0.3,ZBOX),P(t1,DB+0.3,ZBOX+0.9),P(t0,DB+0.3,ZBOX+0.9)][::-1])
    CF.face([P(t0,DB,ZBAND),P(t1,DB,ZBAND),P(t1,DB+0.3,ZBAND),P(t0,DB+0.3,ZBAND)])
CB.done();GB.done();CF.done()
# Rioli lettering on the band behind the back row (17), centred on the stand's middle
SW=TILE['sign_rioli'][0];tm=0;half=SW/2/EB
a=P(tm-half,DB-0.05,0);b=P(tm+half,DB-0.05,0);board('sign_rioli',a,b,ZB+0.1,ZB+1.3,'sign_rioli')
XR=p('rear_x',-111.5);ZR=p('rear_z',13.5);CRZ=p('centre_roof',[17.5,15.5])
# rear building: from the box line to the back wall; plan from the satellite roof (x -111.5, y -30..24)
yN,yS=p('rear_yn',24.0),p('rear_ys',-30.0)
fp=[P(t,DB+BOXD,0)[:2] for t in tsteps(math.asin(yS/EB),math.asin(yN/EB))]
fp=fp+[(XR+3.5,yN),(XR+3.5,yS)]
prism('rear_building',fp,0,ZR,'clad_grey',top='concrete_dark')
# rear facade (14, 04): glass bands on two upper floors, balconies with orange rails, tall white columns to the roof
gl=Acc('rear_glass','glass');bal=Acc('rear_balcony','concrete');rr=Acc('rear_rail','rail_orange',True);col=Acc('rear_columns','white')
xf=XR+3.45
for z0,z1 in ((4.6,7.8),(9.0,12.6)):gl.face([(xf,yS,z0),(xf,yN,z0),(xf,yN,z1),(xf,yS,z1)][::-1])
for zb in (4.3,8.7):
    bal.face([(xf,yS,zb),(XR,yS,zb),(XR,yN,zb),(xf,yN,zb)][::-1]);bal.face([(XR,yS,zb-0.35),(XR,yN,zb-0.35),(XR,yN,zb),(XR,yS,zb)])
    rr.quad2([(XR,yS,zb),(XR,yN,zb),(XR,yN,zb+1.1),(XR,yS,zb+1.1)],[(0,0),((yN-yS)/2,0),((yN-yS)/2,1),(0,1)])
y=yS+2
while y<yN-1:
    rod(col,(XR+0.4,y,0),(XR+0.4,y,CRZ[1]-0.3),0.32,10);y+=7.0
gl.done();bal.done();rr.done();col.done()
# centre roof: front on the ellipse at d=-0.5, back straight at x=XR (satellite), front higher than back (09, 10)
cr=Acc('centre_roof','roof_grey');cu=Acc('centre_roof_under','roof_under');cfa=Acc('centre_fascia','clad_cream')
ct2=tsteps(math.asin(-30/EB),math.asin(26/EB))
for i in range(len(ct2)-1):
    t0,t1=ct2[i],ct2[i+1];a0,a1=P(t0,-0.5,CRZ[0]),P(t1,-0.5,CRZ[0]);b0,b1=(XR,a0[1],CRZ[1]),(XR,a1[1],CRZ[1])
    cr.face([a0,b0,b1,a1]);cu.face([(q[0],q[1],q[2]-RTH) for q in (a1,b1,b0,a0)])
    cfa.quad2([(a0[0],a0[1],CRZ[0]-RTH-0.8),(a1[0],a1[1],CRZ[0]-RTH-0.8),a1,a0])
for yy in (ct2[0],ct2[-1]):
    a=P(yy,-0.5,CRZ[0]);cfa.quad2([(a[0],a[1],CRZ[0]-RTH),(XR,a[1],CRZ[1]-RTH),(XR,a[1],CRZ[1]),a])
cfa.quad2([(XR,P(ct2[0],0,0)[1],CRZ[1]-RTH-0.6),(XR,P(ct2[-1],0,0)[1],CRZ[1]-RTH-0.6),(XR,P(ct2[-1],0,0)[1],CRZ[1]),(XR,P(ct2[0],0,0)[1],CRZ[1])])
for t in ct2[1:-1:3]:   # centre roof columns on the box line (17)
    c=P(t,DB+BOXD-0.5,0);rod(stl,(c[0],c[1],ZBOX),(c[0],c[1],CRZ[0]-RTH-0.2-(CRZ[0]-CRZ[1])*0.4),0.25,8)
for o in list(SACC.values())+[steelA,steps,conc,soff,deck,kiosk,rail,rf,ru,fas,stl,cr,cu,cfa]:o.done()
# ---- orange stair drums at the centre/wing joins, white disc canopies on a column (04, 05, 14; satellite circles)
for nm,c in (('drum_n',p('drum_n',(-107.0,30.0))),('drum_s',p('drum_s',(-92.4,-31.0)))):
    cyl(nm,c,3.0,0,p('drum_h',8.5),'orange',32);cyl(nm+'_post',c,0.35,8.5,p('disc_z',14.0),'white',12)
    cyl(nm+'_disc',c,4.2,p('disc_z',14.0),p('disc_z',14.0)+0.35,'white',32)
# ---------------- Michael Long Centre (north): OSM way 477647201, two storeys of dark glass and timber (18, 09)
mlc=OSM['buildings']['477647201']
if mlc[0]==mlc[-1]:mlc=mlc[:-1]
MZ=p('mlc_h',9.6)
# walls: dark glass on the long south face, timber elsewhere; per-edge objects keep the materials apart
gm=Acc('mlc_glass','glass_mlc');tw=Acc('mlc_timber','timber');mc=Acc('mlc_render','clad_cream')   # end and back walls cream render, copper only on the narrow step panels (18)
area=sum(mlc[i][0]*mlc[(i+1)%len(mlc)][1]-mlc[(i+1)%len(mlc)][0]*mlc[i][1] for i in range(len(mlc)))
for i in range(len(mlc)):
    a=mlc[i];b=mlc[(i+1)%len(mlc)]
    if area<0:a,b=b,a
    q=[(a[0],a[1],0),(b[0],b[1],0),(b[0],b[1],MZ),(a[0],a[1],MZ)]
    dx,dy=b[0]-a[0],b[1]-a[1];nx,ny=dy,-dx   # outward for a CCW ring
    (gm if ny<-0.5*math.hypot(nx,ny) else tw if math.hypot(nx,ny)<6 else mc).face(q)
    if ny<-0.5*math.hypot(nx,ny):   # roof overhang 2 m out over the glass (18)
        L_=math.hypot(nx,ny);ox,oy=nx/L_*2.0,ny/L_*2.0
        prism('mlc_eave_%d'%i,[(a[0],a[1]),(a[0]+ox,a[1]+oy),(b[0]+ox,b[1]+oy),(b[0],b[1])],MZ-0.35,MZ,'steel_dark',top='roof_mlc',bottom=True)
gm.done();tw.done();mc.done()
bm=bmesh.new();vs=[bm.verts.new((x,y,MZ)) for x,y in (mlc if area>0 else mlc[::-1])];bm.faces.new(vs)
me=bpy.data.meshes.new('mlc_roof');bm.normal_update();world_uv(bm,'roof_mlc');bm.to_mesh(me);bm.free()
o=bpy.data.objects.new('mlc_roof',me);coll('model').objects.link(o);me.materials.append(mat('roof_mlc'))
# white terrace and steps in front of the centre, down to the boundary walkway (18)
ter=p('mlc_terrace',[-40,35,90.5,96.8,1.4])
prism('mlc_terrace',[(ter[0],ter[2]),(ter[1],ter[2]),(ter[1],ter[3]),(ter[0],ter[3])],0,ter[4],'concrete',top='concrete')
# ---------------- light towers: white lattice, four legs tapering, X-braced, lamp frame on top facing the centre, TIO panel (07, 19, 20)
# Bases: satellite smear axis (base = NW end; head leans to the SE) crossed with the photo bearings; SE triangulated on 07 + 15.
# Two designs: NE/SE/NW/SW twin towers with a round-lamp head; E has a wider block head. Heights: photos 15 (14 mm) and 19
# (24 mm, camera resected from the NE/E/SE bearings) agree: twin lamp tops ~42 m, E ~45 m. All three photos agree on the
# proportions (lamp top = 2.4 x panel top); photo 07's camera refits to the same heights (cam07h).
TW=p('towers',{'NW':[-54.5,80.0],'NE':[54.3,78.6],'SW':[-56.5,-75.5],'SE':[49.7,-74.5],'E':[101.3,2.3]})
#           lattice top, head w, head h, foot, waist, top width, lamps (cols x rows), panel (bottom, w, h) or None
TD=p('tower_design',{'twin':[35.3,8.4,6.7,6.0,3.1,3.8,[6,5],[12.4,6.2,5.8]],'E':[37.5,9.7,7.5,6.6,3.2,4.2,[4,3],[13.7,5.2,5.4]]})
PANELS=p('tower_panels',['NE','SE','E'])   # TIO Stadium panels on 07/15; NW/SW carry sponsor boards (left off); INPEX boards left off
lat=Acc('tower_lattice','steel_white');lamps=Acc('tower_lamps','lamp');hd=Acc('tower_heads','steel_white')
for k,(bx,by) in TW.items():
    TH,HW,HH,FW,WW,TWd,(nc,nr),PN=TD['E' if k=='E' else 'twin']
    f=Vector((-bx,-by,0)).normalized();sd=Vector((-f.y,f.x,0));up=Vector((0,0,1));B=Vector((bx,by,0))
    w0,w1,w2=FW/2,WW/2,TWd/2;zw=TH*0.78
    segs=[(0,zw,w0,w1),(zw,TH,w1,w2)]
    for (za,zb,wa,wb) in segs:
        leg=[(B+(f*a+sd*b)*wa+up*za,B+(f*a+sd*b)*wb+up*zb) for a in(-1,1) for b in(-1,1)]
        order=[0,1,3,2]
        for i in range(4):rod(lat,leg[i][0],leg[i][1],0.16,6)
        nb=max(1,int((zb-za)/4.0))
        def at(i,t):pa,pb=leg[i];return pa+(pb-pa)*t
        for s_ in range(nb):
            t0,t1=s_/nb,(s_+1)/nb
            for j in range(4):
                a_,b_=order[j],order[(j+1)%4]
                rod(lat,at(a_,t0),at(b_,t1),0.06,4);rod(lat,at(b_,t0),at(a_,t1),0.06,4);rod(lat,at(a_,t1),at(b_,t1),0.07,4)
    # lamp frame tilted 10 deg toward the field, lamps in a grid on its face
    tilt=math.radians(10);nrm=(f*math.cos(tilt)-up*math.sin(tilt));vv=up*math.cos(tilt)+f*math.sin(tilt)
    C=B+up*(TH+HH/2)+f*0.4
    box(hd,C-nrm*0.35,sd,vv,nrm,HW/2,HH/2,0.15)
    cw,rh=HW/nc,HH/nr
    for i in range(nc):
        for j in range(nr):box(lamps,C+sd*(-HW/2+cw*(i+0.5))+vv*(-HH/2+rh*(j+0.5))+nrm*0.1,sd,vv,nrm,cw*0.38,rh*0.39,0.3)
    box(hd,B+up*(TH+0.1),f,sd,up,w2+0.6,w2+0.8,0.12)   # service platform
    if k in PANELS:
        pz,pw,ph=PN;wl=w0+(w1-w0)*(pz+ph/2)/zw+0.1   # flush on the lattice face (07)
        a=B+f*wl-sd*pw/2;b=B+f*wl+sd*pw/2
        board('tower_panel_'+k,(a.x,a.y),(b.x,b.y),pz,pz+ph,'sign_tower')
lat.done();lamps.done();hd.done()
# ---------------- NE big screen on its frame: OSM way 1549614585 (blank, no content)
sc_fp=OSM['buildings']['1549614585'][:4]
xs=sorted(sc_fp,key=lambda q:q[0]);a=Vector((72.4,57.3,0));b=Vector((78.2,46.0,0))   # satellite top of the box less the image lean (~1.7 m S), photos 15 and 19 put it 2.3-4.6 m S of the old line: 2.5 m S
sk=Acc('screen_frame','steel_dark');ZS0,ZS1=p('screen_z',[4.6,12.7])   # photo 15
board('screen_face',(a.x,a.y),(b.x,b.y),ZS0,ZS1,'screen')
bk=b+(Vector((1,0.45,0)).normalized()*3.0);ak=a+(Vector((1,0.45,0)).normalized()*3.0)   # satellite: box 3 m deep, white top
board('screen_back',(bk.x,bk.y),(ak.x,ak.y),ZS0,ZS1,'screen_back')
mk('screen_top',[(a.x,a.y,ZS1),(b.x,b.y,ZS1),(bk.x,bk.y,ZS1),(ak.x,ak.y,ZS1)],[(0,1,2,3)],'roof_white',[[(0,0),(1,0),(1,1),(0,1)]])
board('screen_end_a',(ak.x,ak.y),(a.x,a.y),ZS0,ZS1,'screen_back',True);board('screen_end_b',(b.x,b.y),(bk.x,bk.y),ZS0,ZS1,'screen_back',True)
for t in (0.05,0.35,0.65,0.95):
    q=a+(b-a)*t;qk=ak+(bk-ak)*t;q=q+(qk-q).normalized()*0.3   # front legs stop under the screen, behind the face (19)
    rod(sk,(q.x,q.y,0),(q.x,q.y,ZS0),0.2,8);rod(sk,(qk.x,qk.y,0),(qk.x,qk.y,ZS1),0.2,8);rod(sk,(q.x,q.y,ZS0-0.2),(qk.x,qk.y,ZS0-0.2),0.12,6)
sk.done()
# ---------------- east building: OSM way 477648585, single storey, white roof
eb=OSM['buildings']['477648585'];eb=eb[:-1] if eb[0]==eb[-1] else eb
prism('east_building',eb,0,p('east_h',4.2),'wall_east',top='roof_white')   # cream walls, dark window band (07, 15, 19)
# ---------------- main scoreboard at the east end (07, 15): sits in the OSM notch of the east building, face along x about 79.
# Heights: top 10.7 and legs from photo 07; splits from photo 19 (screen 0.67, band 0.13, banner 0.20 of the face): screen 4.0-8.5, band 8.5-9.4, banner 9.4-10.7.
sa=Vector(p('sb_a',(79.5,-8.0)));sb_=Vector(p('sb_b',(78.8,-16.6)));sdv=sb_-sa;wn=Vector((sdv.y,-sdv.x)).normalized()   # wn faces west; satellite top strip x 79.5-78.6, ends from photo 07 (front face 8.6 m)
SBD=p('sb_depth',1.6);ka=sa-wn*SBD;kb=sb_-wn*SBD   # satellite: box top 79.5-81.0
mb=Acc('scoreboard_box','clad_grey')
for (p0,p1) in ((sa,ka),(ka,kb),(kb,sb_)):mb.face([(p0.x,p0.y,3.8),(p1.x,p1.y,3.8),(p1.x,p1.y,10.7),(p0.x,p0.y,10.7)])
mb.face([(sa.x,sa.y,10.7),(sb_.x,sb_.y,10.7),(kb.x,kb.y,10.7),(ka.x,ka.y,10.7)][::-1]);mb.face([(sa.x,sa.y,3.8),(sb_.x,sb_.y,3.8),(kb.x,kb.y,3.8),(ka.x,ka.y,3.8)])
mb.face([(sa.x,sa.y,3.8),(sb_.x,sb_.y,3.8),(sb_.x,sb_.y,10.7),(sa.x,sa.y,10.7)]);mb.done()
o_=wn*0.04
board('scoreboard_screen',tuple((sa+o_).xy),tuple((sb_+o_).xy),4.0,8.5,'screen')
board('scoreboard_band',tuple((sa+o_).xy),tuple((sb_+o_).xy),8.5,9.4,'sign_sb_band')
board('scoreboard_banner',tuple((sa+o_*2+sdv.normalized()*0.0).xy),tuple((sb_+o_*2).xy),9.4,10.7,'sign_sb_banner')
lg=Acc('scoreboard_legs','steel_rust')
for t in (0.03,0.5,0.97):
    for q in (sa+sdv*t+wn*0.3,ka+sdv*t+wn*0.3):rod(lg,(q.x,q.y,0),(q.x,q.y,3.8),0.15,8)
    q0=sa+sdv*t+wn*0.3;q1=ka+sdv*t+wn*0.3;rod(lg,(q0.x,q0.y,0.2),(q1.x,q1.y,3.7),0.07,6)
for t0,t1 in ((0.03,0.5),(0.5,0.97)):
    q0=sa+sdv*t0+wn*0.3;q1=sa+sdv*t1+wn*0.3;rod(lg,(q0.x,q0.y,0.3),(q1.x,q1.y,3.7),0.07,6);rod(lg,(q1.x,q1.y,0.3),(q0.x,q0.y,3.7),0.07,6)
lg.done()
# small buildings inside the ground (satellite roofs 15, 16 and OSM 1549614584)
for nm,fp_,h in (('nw_kiosk',[(-61.7,84.0),(-57.6,88.6),(-61.1,92.1),(-64.9,88.6)],3.6),('ne_building',[(45.1,79.9),(52.9,85.4),(46.8,94.5),(39.2,89.8)],4.2)):
    prism(nm,fp_,0,h,'clad_grey',top='roof_white')
nb2=OSM['buildings']['1549614584'];nb2=nb2[:-1] if nb2[0]==nb2[-1] else nb2;prism('ne_shed',nb2,0,3.6,'clad_grey',top='roof_white')
# ---------------- gate houses (03, 12): navy blockwork, blue welcome band on top, gate name in white letters
def gate(nm,fp_,face_a,face_b,signname,h=p('gate_h',4.6),welcome='sign_welcome'):
    prism(nm,fp_,0,h,'block_navy',top='concrete_dark')
    a=Vector(face_a);b=Vector(face_b);d=(b-a);n=Vector((d.y,-d.x)).normalized()*0.06   # board normal = (dy,-dx): face_a->face_b runs left to right for a viewer outside
    board(nm+'_welcome',tuple(a+n),tuple(b+n),h-0.1,h+1.5,welcome)
    if signname.endswith('_front'):   # whole painted front (openings, windows, name), flush on the wall
        board(nm+'_front',tuple(a+n),tuple(b+n),0,h-0.1,signname);return
    m_=(a+b)/2;dd=d.normalized()*min(d.length*0.45,TILE[signname][0]/2)
    board(nm+'_name',tuple(m_-dd+n*1.5),tuple(m_+dd+n*1.5),h-1.9,h-0.5,signname)
gate('gate_ahmat',[(-117.4,55.0),(-102.6,55.0),(-102.6,63.8),(-117.4,63.8)],(-102.6,63.85),(-117.4,63.85),'gate_ahmat_front')   # faces north to the path (02, 03)
gate('gate_bonson',[(-138.9,-48.4),(-134.3,-43.2),(-125.0,-51.1),(-129.6,-59.2)],(-138.95,-48.45),(-129.6,-59.25),'gate_bonson_front',welcome='sign_welcome_tan')   # faces south-west (12)
# outer palisade fence between the gates along the plaza's west edge (dark line on the satellite at x about -125)
pal=p('palisade',[(-117.4,57.0),(-125.0,57.0),(-125.5,0.0),(-126.8,-25.0),(-126.5,-44.6)])
pf=Acc('outer_fence','palisade',True);s=0
for i in range(len(pal)-1):
    a,b=pal[i],pal[i+1];L=math.dist(a,b);pf.quad2([(a[0],a[1],0),(b[0],b[1],0),(b[0],b[1],2.1),(a[0],a[1],2.1)],[(s/2.5,0),((s+L)/2.5,0),((s+L)/2.5,1),(s/2.5,1)]);s+=L
pf.done()
# ---------------- ground: grass apron from the boundary fence out to the site edge; paving behind the stand and in front of the MLC
X0,X1,Y0,Y1=-140,112,-100,146
cx=sum(q[0] for q in pitch)/len(pitch);cy=sum(q[1] for q in pitch)/len(pitch)
def ray_box(q):
    dx,dy=q[0]-cx,q[1]-cy;ts=[]
    for v,lo,hi,d_,o in ((X0,Y0,Y1,dx,cx),(X1,Y0,Y1,dx,cx)):
        if d_:t=(v-o)/d_;ts.append(t) if t>0 and lo<=cy+t*dy<=hi else 0
    for v,lo,hi,d_,o in ((Y0,X0,X1,dy,cy),(Y1,X0,X1,dy,cy)):
        if d_:t=(v-o)/d_;ts.append(t) if t>0 and lo<=cx+t*dx<=hi else 0
    t=min(ts);return (cx+t*dx,cy+t*dy)
V=[];F=[];n=len(pitch)
for q in pitch:V.append((q[0],q[1],-0.02))
for q in pitch:o=ray_box(q);V.append((o[0],o[1],-0.02))
for i in range(n):j=(i+1)%n;F.append((i,j,n+j,n+i))
mk('ground_apron',V,F,'grass_out',c='ground')
wk=Acc('walkway','walkway')
for t0,t1 in zip(*(lambda ts:(ts[:-1],ts[1:]))(tsteps(TS,TN))):
    a0=(-72*math.cos(t0),89.5*math.sin(t0));a1=(-72*math.cos(t1),89.5*math.sin(t1))
    wk.face([(a0[0],a0[1],0.0),(a1[0],a1[1],0.0),P(t1,0,0.0),P(t0,0,0.0)][::-1])
wk.done('ground')
prism('plaza',[(-125,57),(-100,57),(-95,45),(-92,30),(-111.5,26),(-111.5,-31),(-92,-31),(-88,-45),(-100,-60),(-126.5,-44.6)],-0.02,0.01,'paving',top='paving')
for o in bpy.data.objects:
    if o.name.startswith('plaza'):coll('ground').objects.link(o);coll('model').objects.unlink(o)
# ---------------- tidy normals, light, export (glTF: Blender +Y becomes glTF -Z, so north = -Z as tools/grounds/mcg)
for o in coll('model').objects:
    if o.data.materials and o.data.materials[0].name in ALPHA:continue
    if o.name in ('sign_rioli',) or o.name.startswith(('tower_panel','gate_','screen_')):continue
    b2=bmesh.new();b2.from_mesh(o.data);bmesh.ops.recalc_face_normals(b2,faces=b2.faces[:]);b2.to_mesh(o.data);b2.free()
cd=bpy.data.cameras.new('cam');cam=bpy.data.objects.new('cam',cd);sc.collection.objects.link(cam);sc.camera=cam
cam.location=(160,-200,120);cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=30;cd.clip_end=3000
sd=bpy.data.lights.new('sun','SUN');sd.energy=4.0;sd.color=(1.0,0.9,0.78);sun=bpy.data.objects.new('sun',sd);sc.collection.objects.link(sun)
sun.rotation_euler=Vector((0.8,0.3,-0.55)).normalized().to_track_quat('-Z','Y').to_euler()   # late afternoon from the west (2025 photos)
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True
w.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.66,0.85,1);w.node_tree.nodes['Background'].inputs[1].default_value=0.9
for e in('BLENDER_EEVEE_NEXT','BLENDER_EEVEE'):
    try:sc.render.engine=e;break
    except TypeError:pass
sc.view_settings.view_transform='Standard';sc.render.resolution_x=1600;sc.render.resolution_y=1000
sc.render.filepath=os.path.join(OUT,'overview.png');bpy.ops.render.render(write_still=True)
bpy.data.objects.remove(bpy.data.objects['ground_apron'])   # rule: no turf in the model (preview only)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'tio_darwin.glb'),export_format='GLB',export_cameras=False,export_lights=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'tio_darwin.blend'))
tri=sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH')
print('DONE objects',len(bpy.data.objects),'faces',tri)
