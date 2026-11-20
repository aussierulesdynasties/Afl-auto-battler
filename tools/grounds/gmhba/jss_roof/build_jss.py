# GMHBA Joel Selwood Stand roof, west facade and supports, copied from the aerial (zoom 19, 0.235 m/px) and the
# Populous elevation photos (S5_014, Gate 1, Facade_011/019). Also repairs two source faults in this sector:
# the sagging upper-tier seat rake (136-152 deg) and the cream box / wedge leftovers outside the facade.
import bpy,bmesh,sys,math,statistics
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:];SRC,OUT,TEX=a[0],a[1],a[2]
A0,A1=129.0,179.0
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=SRC)
o=[o for o in bpy.data.objects if o.type=='MESH'][0];me=o.data;M=o.matrix_world;MI=M.inverted()
names=[s.material.name for s in o.material_slots]
ROOF={'roof','roofd','roofg','fascia','under'}
def ang(v):
    x=math.degrees(math.atan2(v.y,v.x));return x+360 if x<0 else x
bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table();uvl0=bm.loops.layers.uv.active
# ---- measured front edge radius per half-degree (old fascia), and old wall radius
frontr={};wallr={};NB=16
for f in bm.faces:
    c=M@f.calc_center_median();an=ang(c);r=math.hypot(c.x,c.y);n=names[f.material_index]
    if not(A0-3<an<A1+3):continue
    k=round((an-A0)/(A1-A0)*NB*2)
    if n=='wall' and c.z>12 and r>95:wallr[k]=max(wallr.get(k,0),r)
    if n=='fascia' and r<90:frontr[k]=min(frontr.get(k,1e9),r)
wallr={k:v for k,v in wallr.items() if abs(v-statistics.median([wallr[j] for j in wallr if abs(j-k)<=3]))<3}
def fr_an(an):
    x=(an-A0)/(A1-A0)*NB*2;k=min(frontr,key=lambda j:abs(j-x));return frontr[k]
# ---- seat rake repair: upper tier 134.2-152.5 deg rebuilt from the healthy bay 124.5-134.2 (same rows, same radii)
SEAT={'tread','seatback','seatpan','aisle'}
def upper(f):
    c=M@f.calc_center_median();r=math.hypot(c.x,c.y);return names[f.material_index] in SEAT and 80.3<r<99.5 and c.z>8.3,ang(c)
src=[];dip=[]
for f in bm.faces:
    u,an=upper(f)
    if not u:continue
    if 124.5<=an<134.2:src.append(f)
    elif 134.2<=an<152.5:dip.append(f)
print('SEAT src',len(src),'dip',len(dip))
copies=[]
for (b0,b1) in((134.2,143.5),(143.5,152.5)):
    s=(b1-b0)/(134.2-124.5)
    for f in src:
        vs=[]
        for l in f.loops:
            w=M@l.vert.co;an=ang(w);r=math.hypot(w.x,w.y);na=math.radians(b0+(an-124.5)*s)
            vs.append((MI@Vector((r*math.cos(na),r*math.sin(na),w.z)),l[uvl0].uv.copy()))
        copies.append((vs,f.material_index))
# ---- faces to delete
dele=set(dip)
for f in bm.faces:
    c=M@f.calc_center_median();an=ang(c);r=math.hypot(c.x,c.y);n=names[f.material_index]
    if c.x<-108.6 and 33.5<c.y<62 and c.z<14 and n not in('wedge','wedgef'):continue  # keep the passed exterior's glazed entry and canopy north of the block (f08)
    if A0<=an<=A1 and r>76 and (n in ROOF or (r>wallr.get(round((an-A0)/(A1-A0)*NB*2),112)+1 and n not in('pave','turf','cream'))):dele.add(f)
    if A1<an<=180.3 and r>76 and n in ROOF:dele.add(f)
    nn=(M.to_3x3()@f.normal).normalized()
    if A0-2<=an<=A1+2 and n=='wall' and r>98 and 0.1<abs(nn.z)<0.9:dele.add(f)
    if n in('wedge','wedgef') and 170<an<182 and r>110:dele.add(f)               # crumpled wedge leftovers at the join
    if 166<an<178 and 114<r<131 and c.z>0.3 and n not in('pave','turf'):dele.add(f)  # cream box on a column (no real counterpart)
    if 129<an<180 and c.z>0.3 and n not in('pave','turf') and c.x<-108.6 and c.y>-3:dele.add(f)  # anything poking out past the new facade
    if 129<an<180 and c.z>13.7 and n not in('pave','turf') and c.x<-101.2 and c.y>-3:dele.add(f)  # source leftovers behind the struts, above the glazing
print('DELETE',len(dele))
bmesh.ops.delete(bm,geom=list(dele),context='FACES')
for vs,mi in copies:
    vv=[bm.verts.new(p) for p,_ in vs]
    try:f=bm.faces.new(vv)
    except ValueError:continue
    f.material_index=mi
    for l,(_,uv) in zip(f.loops,vs):l[uvl0].uv=uv
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=0.002)
bm.to_mesh(me);bm.free()
# ---- materials
def mat(n,img,rough=0.85,metal=0.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes['Principled BSDF']
    t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(TEX+img)
    m.node_tree.links.new(t.outputs['Color'],b.inputs['Base Color']);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    if img=='jss_sign.png':
        m.node_tree.links.new(t.outputs['Alpha'],b.inputs['Alpha']);m.blend_method='CLIP' if hasattr(m,'blend_method') else None
    return m
MS=[mat('jss_top','jss_top.png',0.8,0.2),mat('jss_steel','jss_steel.png',0.7,0.4),mat('jss_fascia','jss_fascia.png'),
    mat('jss_white','jss_white.png',0.5,0.1),mat('jss_soffit','jss_soffit.png'),mat('jss_sky','jss_sky.png',0.4),
    mat('jss_fins','jss_fins.png',0.6),mat('jss_brick','jss_brick.png',0.9),mat('jss_glass','jss_glass.png',0.15,0.3),
    mat('jss_clad','jss_clad.png',0.7,0.3),mat('jss_block','jss_block.png',0.6,0.3),mat('jss_sign','jss_sign.png',0.6,0.2),mat('jss_conc','jss_conc.png',0.9),mat('jss_hclad','jss_hclad.png',0.7,0.3),mat('jss_canopy','jss_canopy.png',0.6,0.4)]
TOP,STEEL,FASC,WHITE,SOFF,SKY,FINS,BRICK,GLASS,CLAD,BLK,SIGN,CONC,HCLAD,CAN=range(15)
nb=bmesh.new();uvl=nb.loops.layers.uv.new()
def P(an,r,z):a_=math.radians(an);return Vector((r*math.cos(a_),r*math.sin(a_),z))
def face(vs,mi,uvs):
    f=nb.faces.new([nb.verts.new(v) for v in vs]);f.material_index=mi
    for l,u in zip(f.loops,uvs):l[uvl].uv=u
    return f
def quad(vs,mi):
    n=(vs[1]-vs[0]).cross(vs[2]-vs[0]);ax=max(range(3),key=lambda i:abs(n[i]))
    return face(vs,mi,[(v[(ax+1)%3]/4,v[(ax+2)%3]/4) for v in vs])
def tube(p0,p1,rad,mi,n=12):
    d=(p1-p0).normalized();s=d.cross(Vector((0,0,1)));s=s.normalized() if s.length>1e-6 else Vector((1,0,0));t=d.cross(s)
    ring=lambda p:[p+(s*math.cos(2*math.pi*k/n)+t*math.sin(2*math.pi*k/n))*rad for k in range(n)]
    A=ring(p0);B=ring(p1);L=(p1-p0).length
    for k in range(n):face([B[k],B[(k+1)%n],A[(k+1)%n],A[k]],mi,[(k/n,L/4),((k+1)/n,L/4),((k+1)/n,0),(k/n,0)])
def collar(p,d,rad,mi):
    d=d.normalized();tube(p-d*0.35,p+d*0.35,rad,mi)
TH=0.20
TOPTRI=[]
def plate(a,b,c,mi_top,dirv):
    """top sheet + underside liner; ribs run along dirv (plan direction of the plate)"""
    L=Vector((-dirv.y,dirv.x,0));D=Vector((dirv.x,dirv.y,0))
    uv=lambda v:(v.dot(L)/4,v.dot(D)/4)
    t=[a,b,c]
    if (b-a).cross(c-a).z<0:t=[a,c,b]
    face(t,mi_top,[uv(v) for v in t]);TOPTRI.append(tuple(t))
    dz=Vector((0,0,-TH));u=[t[0]+dz,t[2]+dz,t[1]+dz];face(u,SOFF,[uv(v) for v in u])
def trim(p,q,w=0.30,h=0.45):  # white edge trim on top of a fold line
    d=(q-p).normalized();s=d.cross(Vector((0,0,1)));s=(s.normalized() if s.length>1e-6 else Vector((1,0,0)))*w/2;up=Vector((0,0,0.05));dn=Vector((0,0,-h))
    c=[p-s+up,p+s+up,q+s+up,q-s+up];b=[v+dn for v in c]
    for qd in([c[0],c[1],c[2],c[3]],[c[0],c[3],b[3],b[0]],[c[1],b[1],b[2],c[2]]):quad(qd,WHITE)
# ---- measured layout (model frame: x east, y north, metres; aerial origin = oval centre)
XE=-112.8                  # beak tips / straight west roof edge (aerial)
OVH=5.2                    # beak overhang past the facade (Facade_011 close-up)
XF=XE+OVH                  # facade plane
YC=108.2                   # NW corner of the roof (aerial)
PITCH=12.2                 # peak pitch along the west edge (aerial column tops at y 96/84/71/59)
YP=[96.0-PITCH*k for k in range(8)]                 # 8 beak peaks
YV=[YP[0]+PITCH/2-PITCH*k for k in range(9)]        # 9 valleys 102.1 .. 4.5
ZR=21.5                    # valley height at the rear edge (S5_014: valley 11.0 m above the fin top)
PK=8.0                     # beak rise above the valleys (S5_014: 0.66 x pitch)
SB=11.0                    # top of the white fin band
YS=-0.7                    # neighbouring west-stand roof starts here on the edge line (180.35 deg)
DIAG=[Vector((-69.2,85.5)),Vector((-88.0,92.4)),Vector((XE,YC))]   # NW diagonal rear edge (no beaks), aerial
def zf(an):return 23.6-2.2*(an-A0)/(A1-A0)
def front(R,w):
    """front-edge point for rear point R: plates run between radial (w=0) and due east (w=1)"""
    rad=Vector((-R.x,-R.y));rad.normalize();d=(rad*(1-w)+Vector((1,0))*w).normalized()
    an=ang(R);x=R.to_2d()
    for _ in range(4):
        rf=fr_an(an)+0.8;b=x.dot(d);c=x.dot(x)-rf*rf;t=-b-math.sqrt(max(0,b*b-c));p=x+d*t;an=ang(p)
    return Vector((p.x,p.y,zf(an))),d
# rear points (plan) in order from the north-stand join to the west-stand join, with rear height and blend
REAR=[]
for k in range(2):
    p,q=DIAG[k],DIAG[k+1];n=max(1,round((q-p).length/12.35))
    for m in range(n):REAR.append((p.lerp(q,m/n),ZR,0.0,'flat'))
REAR.append((Vector((XE,YC)),ZR,0.25,'flat'))
for k,yv in enumerate(YV):
    REAR.append((Vector((XE,yv)),ZR,0.5,'valley'))
    if k<len(YP):REAR.append((Vector((XE,YP[k])),ZR+PK,0.5,'peak'))
REAR.append((Vector((XE,YS)),None,0.5,'end'))
# neighbour roof height at the join, sampled on its edge so the last sheet butts onto it with no fold
dg=bpy.context.evaluated_depsgraph_get()
def hit_z(x,y):
    ok,loc,nrm,idx,ob,mx=bpy.context.scene.ray_cast(dg,Vector((x,y,60)),Vector((0,0,-1)))
    return loc.z if ok else None
# ---- roof plates
FR={}
def fpt(i):
    if i not in FR:
        R,z,w,kind=REAR[i];FR[i]=front(Vector((R.x,R.y,0)),w)
    return FR[i]
def R3(i):
    R,z,w,kind=REAR[i];return Vector((R.x,R.y,z))
VNODE=[];PEAKS=[]
i=0
while i<len(REAR)-1:
    R,z,w,kind=REAR[i]
    if kind=='valley' and i+2<len(REAR) and REAR[i+1][3]=='peak':
        V0,Pk,V1=R3(i),R3(i+1),R3(i+2);F0,d0=fpt(i);Fp,dp=fpt(i+1);F1,d1=fpt(i+2)
        Q=Fp+(Pk-Fp)*0.30                      # apex of the white skylight triangle on the ridge
        plate(F0,F1,Q,SKY,dp)
        plate(F0,Q,V0,TOP,dp);plate(Q,Pk,V0,TOP,dp);plate(Q,F1,V1,TOP,dp);plate(Q,V1,Pk,TOP,dp)
        for (p,q) in((V0,Pk),(Pk,V1),(F0,Q),(Q,F1),(Q,Pk)):trim(p,q)
        PEAKS.append((Q,Pk));i+=2;continue
    if kind=='end':break
    # flat-rear bay (diagonal and corner strip): skylight triangle + two plates, rear at valley height
    A_,B_=R3(i),(R3(i+1) if REAR[i+1][3]!='end' else None)
    if B_ is None:
        # last strip to the west-stand roof: butt onto its sampled height
        Rn=REAR[i+1][0];zn=[hit_z(*(Rn+(fpt(i)[0].to_2d()-Rn)*s)) for s in(0.05,0.5,0.95)]
        zn=[z_ for z_ in zn if z_ is not None] or [19.0]
        B_=Vector((Rn.x,Rn.y,max(zn[0],15)));
        F0,d0=fpt(i);an1=180.35;F1=Vector((fr_an(179)+0.8,0,0));F1=P(an1,fr_an(179)+0.8,zf(A1))
        plate(F0,F1,B_,TOP,d0);plate(F0,B_,A_,TOP,d0);trim(A_,B_);break
    F0,d0=fpt(i);F1,d1=fpt(i+1);M_=(A_+B_)/2;FM=(F0+F1)/2;Q=FM+(M_-FM)*0.30;Q.z+=0.6
    plate(F0,F1,Q,SKY,d0);plate(F0,Q,A_,TOP,d0);plate(Q,B_,A_,TOP,d0);plate(Q,F1,B_,TOP,d0)
    for (p,q) in((A_,B_),(F0,Q),(Q,F1)):trim(p,q)
    i+=1
def plate_z(x,y):
    best=None
    for t in TOPTRI:
        a_,b_,c_=t;v0=b_-a_;v1=c_-a_;v2=Vector((x,y,0))-a_
        d00=v0.x*v0.x+v0.y*v0.y;d01=v0.x*v1.x+v0.y*v1.y;d11=v1.x*v1.x+v1.y*v1.y;d20=v2.x*v0.x+v2.y*v0.y;d21=v2.x*v1.x+v2.y*v1.y
        den=d00*d11-d01*d01
        if abs(den)<1e-9:continue
        v=(d11*d20-d01*d21)/den;w_=(d00*d21-d01*d20)/den
        if v>=-1e-4 and w_>=-1e-4 and v+w_<=1+1e-4:
            z=a_.z+v*v0.z+w_*v1.z;best=z if best is None else max(best,z)
    return best
# ---- white tube supports (S5_014): a raking column under each peak, a node at valley height with arms out to
# the valley nodes (the tie line), and V-struts from each column foot up to the neighbouring valley nodes
RC,RD,RA=0.34,0.27,0.22     # radii: column 0.68 m, struts 0.54 m, arms 0.44 m (S5_014: 9/7/6 px of a 160 px pitch)
ZN=ZR-0.9
cols=[]
for k,(Q,Pk) in enumerate(PEAKS):
    yp=YP[k];C0=Vector((XF-0.6,yp,SB));
    T=Q+(Pk-Q)*0.82;T.z-=TH+0.25
    s=(ZN-C0.z)/(T.z-C0.z);N=C0.lerp(T,s);cols.append((C0,N,T))
    tube(C0,T,RC,WHITE);collar(C0,T-C0,RC*1.35,WHITE);collar(N,T-C0,RC*1.35,WHITE);collar(T,T-C0,RC*1.3,WHITE)
for k,yv in enumerate(YV):
    xs=[c[1].x for c in cols];xn=sum(xs)/len(xs);Vn=Vector((xn,yv,ZN))
    zt=plate_z(Vn.x,Vn.y)
    if zt:tube(Vn,Vector((Vn.x,Vn.y,zt-TH)),RA,WHITE)
    collar(Vn,Vector((0,1,0)),RA*1.45,WHITE)
    for j in(k-1,k):
        if 0<=j<len(cols):
            C0,N,T=cols[j];tube(N,Vn,RA,WHITE);tube(C0,Vn,RD,WHITE)
# ---- facade under the west beaks and the diagonal: brick base, white fin band, glazing strip, dark cladding
def wall_strip(p,q,z0,z1,mi,tile_w=4.0,tile_h=4.0,flip=False):
    L=(q-p).length
    vs=[Vector((p.x,p.y,z0)),Vector((q.x,q.y,z0)),Vector((q.x,q.y,z1)),Vector((p.x,p.y,z1))]
    uv=[(0,z0/tile_h),(L/tile_w,z0/tile_h),(L/tile_w,z1/tile_h),(0,z1/tile_h)]
    if flip:vs=vs[::-1];uv=uv[::-1]
    face(vs,mi,uv)
def facade_line(p,q,zclad_top):
    n=max(1,int((q-p).length/0.5))
    for m in range(n):
        a_=p.lerp(q,m/n);b_=p.lerp(q,(m+1)/n)
        za,zb=max(14.0,min(ZN+0.4,zclad_top(a_))),max(14.0,min(ZN+0.4,zclad_top(b_)));L=(b_-a_).length;u0=m*L/4
        wall_strip(a_,b_,0,3.5,BRICK);wall_strip(a_,b_,3.5,SB,FINS,4.0,8.0);wall_strip(a_,b_,SB,13.7,GLASS)
        face([Vector((a_.x,a_.y,13.7)),Vector((b_.x,b_.y,13.7)),Vector((b_.x,b_.y,zb)),Vector((a_.x,a_.y,za))],CLAD,[(u0,13.7/4),(u0+L/4,13.7/4),(u0+L/4,zb/4),(u0,za/4)])
def ztop_at(p):
    z=plate_z(p.x,p.y);return (z-TH-0.05) if z else ZR-0.5
facade_line(Vector((XF,YC-1.0)),Vector((XF,YS)),ztop_at)
SET=6.0;n_=int((YC-1.0-YS)/0.5)
for m in range(n_):
    y0=YC-1.0-m*0.5;y1=y0-0.5;xb=XF+SET
    za=ztop_at(Vector((xb,y0)));zb=ztop_at(Vector((xb,y1)))
    face([Vector((XF,y0,ZN+0.4)),Vector((XF,y1,ZN+0.4)),Vector((xb,y1,ZN+0.4)),Vector((xb,y0,ZN+0.4))],CLAD,[(0,0),(0.125,0),(0.125,1.5),(0,1.5)])
    face([Vector((xb,y0,ZN+0.4)),Vector((xb,y1,ZN+0.4)),Vector((xb,y1,max(zb,ZN+0.5))),Vector((xb,y0,max(za,ZN+0.5)))],CLAD,[(y0/4,0),(y1/4,0),(y1/4,zb/4),(y0/4,za/4)])
for k in range(2):
    p,q=DIAG[k],DIAG[k+1];nrm=Vector((-(q-p).y,(q-p).x)).normalized()
    if nrm.dot(p)<0:nrm=-nrm
    facade_line(p-nrm*1.0,q-nrm*1.0,ztop_at)
facade_line(Vector((XE,YC))+Vector((1.0,-1.0)),Vector((XF,YC-1.0)),ztop_at)
# Gate 1 Polly Farmer glazed entry box (S5_014: between peaks 2-3 and 4-5, 0-10.2 m, projecting 1.2 m)
G0,G1,GX=53.3,78.1,XF-1.2
for (p,q) in((Vector((GX,G1)),Vector((GX,G0))),(Vector((XF,G1)),Vector((GX,G1))),(Vector((GX,G0)),Vector((XF,G0)))):
    wall_strip(p,q,0.0,10.2,GLASS,3.0,5.1)
face([Vector((XF,G0,10.2)),Vector((GX,G0,10.2)),Vector((GX,G1,10.2)),Vector((XF,G1,10.2))],FASC,[(0,0),(0.3,0),(0.3,6),(0,6)])
# GMHBA STADIUM corner block (f08 vs the Cats wall, 41.4 m = 735 px): top edge 25.6 m at z 22.7,
# leaning face down to a point 3.6 m in from the Cats wall at z 6.4, box behind 11 m deep
V=Vector;BY0,BY1,BZT,BZB,BXF,BXB,BXP=-3.4,33.5,23.1,9.3,-126.0,-115.0,-122.0
# corners solved through the f08 camera (cam08.npy) onto the x=-126 face plane
T0,T1,PT=V((BXF,-1.3,22.9)),V((BXF,21.7,22.9)),V((BXP,4.7,9.7))  # local f08 camera (cam08_local.npy), Cats corners 6-9 px
quad([T1,T0,PT,PT+V((0,0.01,0))],BLK) if False else face([T0,T1,PT],BLK,[(T0.y/4,T0.z/4),(T1.y/4,T1.z/4),(PT.y/4,PT.z/4)])
B=lambda x,y,z:V((x,y,z))
# lower facet below the T1-PT fold, down to the entry (f08 back-projected: y 27.3 z 4.6 / y 7.8 z 8.4)
FB0,FB1=V((-124.0,17.8,10.7)),V((-124.0,7.8,8.4))
face([T1,FB0,FB1,PT],BLK,[(T1.y/4,T1.z/4),(FB0.y/4,FB0.z/4),(FB1.y/4,FB1.z/4),(PT.y/4,PT.z/4)])
BK=1.2  # wedge plate thickness
T0b,T1b,PTb=T0+V((BK,0,0)),T1+V((BK,0,0)),PT+V((BK,0,0))
face([T1b,T0b,PTb][::-1],BLK,[(0,0),(1,0),(1,1)])
for p_,q_,pb,qb in((T0,T1,T0b,T1b),(T1,PT,T1b,PTb),(PT,T0,PTb,T0b)):
    face([p_,q_,qb,pb],BLK,[(0,0),((q_-p_).length/4,0),((q_-p_).length/4,0.3),(0,0.3)])
SY=BY0+8.9  # south service box: concrete side from the Cats wall (-3.4) to the wedge's lower point (5.5)
for vs in([B(BXP,BY0,0),B(BXB,BY0,0),B(BXB,BY0,BZT),B(BXP,BY0,BZT)],[B(BXB,SY,0),B(BXP+1.2,SY,0),B(BXP+1.2,SY,BZT),B(BXB,SY,BZT)],
          [B(BXP+1.2,BY0,0),B(BXP+1.2,SY,0),B(BXP+1.2,SY,BZT),B(BXP+1.2,BY0,BZT)]):
    face(vs,CONC,[(v.y/4+v.x/4,v.z/4) for v in vs])
# plant storey behind/above the wedge (f08: dark horizontal cladding, concrete parapet, roof plant)
def box(x0,x1,y0,y1,z0,z1,mi,top=None):
    P8=lambda x,y,z:V((x,y,z))
    for vs in([P8(x0,y0,z0),P8(x0,y1,z0),P8(x0,y1,z1),P8(x0,y0,z1)],[P8(x1,y1,z0),P8(x1,y0,z0),P8(x1,y0,z1),P8(x1,y1,z1)],
              [P8(x1,y0,z0),P8(x0,y0,z0),P8(x0,y0,z1),P8(x1,y0,z1)],[P8(x0,y1,z0),P8(x1,y1,z0),P8(x1,y1,z1),P8(x0,y1,z1)]):
        face(vs,mi,[((v.x+v.y)/4,v.z/4) for v in vs])
    face([P8(x0,y0,z1),P8(x0,y1,z1),P8(x1,y1,z1),P8(x1,y0,z1)],top if top is not None else mi,[(x0/4,y0/4),(x0/4,y1/4),(x1/4,y1/4),(x1/4,y0/4)])
# storey front x -119.2, y 5.5..33.5 (f08 solved camera back-projection)
box(-119.2,-110.0,3.8,20.5,19.6,26.4,HCLAD,STEEL)
box(-114.0,-110.0,BY0-3.0,BY0+1.0,0,25.2,CONC)  # concrete tower top 25.2 (f08)          # parapet band
for (yy,xx) in((9,-116),(15,-114),(21,-117),(27,-114)):box(xx-1.6,xx+1.6,yy-1.6,yy+1.6,25.5,27.3,STEEL)  # roof plant
# glazed entry under the wedge, set back to the old glazing line
for y0 in [5.5+k*3.0 for k in range(10)]:
    wall_strip(V((-118.0,min(y0+3.0,BY1))),V((-118.0,y0)),0.0,9.0,GLASS,3.0,4.5)
# sign decal: f08 corners back-projected through the solved camera onto the leaning face
NF=(T1-T0).cross(PT-T0)
def onf(y,z):x=T0.x-(NF.y*(y-T0.y)+NF.z*(z-T0.z))/NF.x;return V((x-0.06,y,z))
sf=face([onf(17.0,14.9),onf(5.2,14.9),onf(5.2,18.9),onf(17.0,18.9)],SIGN,[(0,0),(1,0),(1,1),(0,1)])
# entrance canopy: plan from Esri Wayback 2026-11-18 (west edge x -122.6..-121.4, NW tip), top 21.0 (level with block top in sv_w_h90), 4 soffit folds (sv_w_h90, sv_nw_h130)
CZ,CF=21.7,20.2
CP=[V((-112.8,31.0,CZ)),V((-122.6,31.0,CZ)),V((-122.6,44.0,CZ)),V((-121.4,92.0,CZ)),V((-121.0,104.5,CZ)),V((-112.0,109.0,CZ))]
face(CP[::-1],BLK,[(v.x/4,v.y/4) for v in CP[::-1]])
for a_,b_ in zip(CP[1:5],CP[2:6]):
    face([V((a_.x,a_.y,CF)),V((b_.x,b_.y,CF)),b_,a_],BLK,[(0,0),((b_-a_).length/4,0),((b_-a_).length/4,0.4),(0,0.4)])
def wx(y):return -122.6 if y<44 else -122.6+(y-44)/48*1.2
FY=[44.0+k*15.0 for k in range(5)]
for y0,y1 in zip(FY[:-1],FY[1:]):
    # h95 ray: underside meets the back wall at z 21.96 (y 109.3) .. 18.11 (y 62.3); valleys at the back, straight outer edge
    ym=(y0+y1)/2;zv=21.96+(ym-109.26)*0.08205;A,Bq,M=V((wx(y0),y0,CF)),V((wx(y1),y1,CF)),V((-112.8,ym,zv));Ab,Bb=V((-112.8,y0,CF)),V((-112.8,y1,CF))
    face([A,Bq,M][::-1],CAN,[(0,0),(1,0),(0.5,1)]);face([A,M,Ab][::-1],CAN,[(0,0),(1,0.5),(0,1)]);face([M,Bq,Bb][::-1],CAN,[(1,0.5),(0,0),(0,1)])
face([V((-122.6,31.0,CF)),V((-122.6,44.0,CF)),V((-112.8,44.0,CF)),V((-112.8,31.0,CF))],CAN,[(0,0),(1,0),(1,1),(0,1)])
wall_strip(V((-114.0,104.0)),V((-114.0,31.0)),0.0,CF,GLASS,3.0,4.5)
nb.normal_update()
for f in nb.faces:   # walls face outward (west / away from the oval)
    if f.material_index in(BRICK,FINS,GLASS,CLAD) and abs(f.normal.z)<0.3:
        c=f.calc_center_median();n=f.normal
        if n.x*c.x+n.y*c.y<0:f.normal_flip()
nm=bpy.data.meshes.new('jss_roof');nb.to_mesh(nm);nb.free()
for m in MS:nm.materials.append(m)
ob=bpy.data.objects.new('jss_roof',nm);bpy.context.scene.collection.objects.link(ob)
print('PEAKS',len(PEAKS),'VALLEYS',len(YV),'REAR',len(REAR))
bpy.ops.export_scene.gltf(filepath=OUT,export_format='GLB')
print('DONE')
