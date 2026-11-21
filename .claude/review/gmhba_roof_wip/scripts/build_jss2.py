# GMHBA Joel Selwood Stand roof (NW sector): remove the smooth draped sheet, build saw-tooth flat bays on steel ribs/trusses
import bpy,bmesh,sys,math
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:];SRC,OUT,TEX=a[0],a[1],a[2]
A0,A1,NB=129.0,179.0,16          # sector (deg, from +x toward +y), bays
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=SRC)
o=[o for o in bpy.data.objects if o.type=='MESH'][0];me=o.data;M=o.matrix_world
names=[s.material.name for s in o.material_slots]
ROOF={'roof','roofd','roofg','fascia','under'}
def ang(v):
    x=math.degrees(math.atan2(v.y,v.x));return x+360 if x<0 else x
# measure the back wall radius per bay before removal
bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table()
wallr={};frontr={}
for f in bm.faces:
    c=M@f.calc_center_median();an=ang(c);r=math.hypot(c.x,c.y);n=names[f.material_index]
    if not(A0-3<an<A1+3):continue
    k=round((an-A0)/(A1-A0)*NB*2)
    if n=='wall' and c.z>12 and r>95:wallr[k]=max(wallr.get(k,0),r)
    if n=='fascia' and r<90:frontr[k]=min(frontr.get(k,1e9),r)
dele=[]
for f in bm.faces:
    c=M@f.calc_center_median();an=ang(c);r=math.hypot(c.x,c.y);n=names[f.material_index]
    if A0<=an<=A1 and r>76 and (n in ROOF or (r>wallr.get(round((an-A0)/(A1-A0)*NB*2),112)+1 and n not in('pave','turf','cream'))):dele.append(f)
for f in bm.faces:
    c=M@f.calc_center_median();an=ang(c);r=math.hypot(c.x,c.y);n=(M.to_3x3()@f.normal).normalized()
    if A0-2<=an<=A1+2 and names[f.material_index]=='wall' and r>98 and 0.1<abs(n.z)<0.9 and f not in dele:dele.append(f)
print('DELETE',len(dele))
import statistics
wallr={k:v for k,v in wallr.items() if abs(v-statistics.median([wallr[j] for j in wallr if abs(j-k)<=3]))<3}
bmesh.ops.delete(bm,geom=dele,context='FACES');bm.to_mesh(me);bm.free()
def fr(t):
    x=t*NB*2;k=min(frontr,key=lambda j:abs(j-x));return frontr[k]
def wr(t):  # interpolated wall radius at fraction t (0..1) across the sector
    ks=sorted(wallr);x=t*NB*2
    lo=max([k for k in ks if k<=x],default=ks[0]);hi=min([k for k in ks if k>=x],default=ks[-1])
    return wallr[lo] if hi==lo else wallr[lo]+(wallr[hi]-wallr[lo])*(x-lo)/(hi-lo)
print('WALLR',{k:round(v,1) for k,v in sorted(wallr.items())});print('FRONTR',{k:round(v,1) for k,v in sorted(frontr.items())})
def mat(n,img,rough=0.85,metal=0.3):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes['Principled BSDF']
    t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(TEX+img)
    m.node_tree.links.new(t.outputs['Color'],b.inputs['Base Color']);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    return m
MS=[mat('jss_sheet','jss_sheet.png'),mat('jss_steel','jss_steel.png',0.7,0.5),mat('jss_fascia','jss_fascia.png'),mat('jss_white','jss_white.png',0.6,0.2)]
nb=bmesh.new();uvl=nb.loops.layers.uv.new()
def P(an,r,z):a_=math.radians(an);return Vector((r*math.cos(a_),r*math.sin(a_),z))
def quad(vs,mi,uvs=None):
    vv=[nb.verts.new(v) for v in vs];f=nb.faces.new(vv);f.material_index=mi
    if uvs is None:  # planar box UV in metres/4 using dominant axes
        n=(vs[1]-vs[0]).cross(vs[2]-vs[0]);ax=max(range(3),key=lambda i:abs(n[i]))
        uvs=[(v[(ax+1)%3]/4,v[(ax+2)%3]/4) for v in vs]
    for l,u in zip(f.loops,uvs):l[uvl].uv=u
    return f
def box(p0,p1,w,h,mi):  # beam from p0 to p1 (top centreline), width w, depth h
    d=(p1-p0).normalized();s=d.cross(Vector((0,0,1))).normalized()*w/2;dn=Vector((0,0,-h))
    c=[p0-s,p0+s,p1+s,p1-s];b=[v+dn for v in c]
    for q in([c[0],c[1],c[2],c[3]],[b[3],b[2],b[1],b[0]],[c[0],c[3],b[3],b[0]],[c[1],b[1],b[2],c[2]],[c[0],b[0],b[1],c[1]],[c[3],c[2],b[2],b[3]]):quad(q,mi)
ZR=21.2            # level rear edge
STEP=2.0           # saw-tooth rise across a bay (inner panels)
DROP=0.8           # step down from inner to outer panels at the old wall line
GAP=0.6            # dark gap between bays (m)
TH=0.18            # sheet thickness
FD=3.6             # rear fascia depth
# rear edge in plan, traced from the current aerial (x east, y north, m): north-stand join, NW diagonal, straight west edge
POLY=[Vector((-69.2,85.5)),Vector((-86.6,92.4)),Vector((-116.0,106.5)),Vector((-116.0,-8.0))]
def rear(an):
    d=Vector((math.cos(math.radians(an)),math.sin(math.radians(an))));best=None
    for k in range(len(POLY)-1):
        p,q=POLY[k],POLY[k+1];e=q-p;den=d.x*e.y-d.y*e.x
        if abs(den)<1e-9:continue
        t=(p.x*e.y-p.y*e.x)/den;u=(p.x*d.y-p.y*d.x)/den
        if t>0 and -1e-6<=u<=1+1e-6 and (best is None or t<best):best=t
    return best
def angv(v):return math.degrees(math.atan2(v.y,v.x))
# 15 bays of equal length along the rear edge (measured 166 m, about 11 m a bay as in the Gate 1 photo)
_S=[A0+(A1-A0)*k/3000 for k in range(3001)];_L=[0.0]
for k in range(1,3001):
    p=P(_S[k-1],rear(_S[k-1]),0);q=P(_S[k],rear(_S[k]),0);_L.append(_L[-1]+(q-p).length)
EDGES=[];n=15
for k in range(n+1):
    tgt=_L[-1]*k/n;j=min(range(3001),key=lambda m:abs(_L[m]-tgt));EDGES.append(_S[j])
print('BAYLEN',round(_L[-1]/n,2),'REAR',round(_L[-1],1))
NBAY=len(EDGES)-1
def zf(an):return 23.6-2.2*(an-A0)/(A1-A0)
PK=7.0     # beak rise above the valleys (photo: peak rise ~0.65 x bay width ~11 m)
OVH=6.0    # beak overhang past the facade line in plan
ZFI=1.0    # facade inset behind the roof valley line
SB=11.0    # strut base height on the facade (top of the white fin band)
def tri(a,b,c,mi,up=True,uvs=None):
    if ((b-a).cross(c-a).z>0)!=up:b,c=c,b
    f=nb.faces.new([nb.verts.new(a),nb.verts.new(b),nb.verts.new(c)]);f.material_index=mi
    for l,v in zip(f.loops,[a,b,c]):l[uvl].uv=uvs(v) if uvs else (v.x/4,v.y/4)
def tube(p0,p1,rad,mi,n=8):
    d=(p1-p0).normalized();s=d.cross(Vector((0,0,1)));s=s.normalized() if s.length>1e-6 else Vector((1,0,0));t=d.cross(s)
    ring=lambda p:[p+(s*math.cos(2*math.pi*k/n)+t*math.sin(2*math.pi*k/n))*rad for k in range(n)]
    A=ring(p0);B=ring(p1)
    for k in range(n):quad([B[k],B[(k+1)%n],A[(k+1)%n],A[k]],mi)
def rp(an,dr=0.0,z=0.0):r=rear(an);return P(an,r+dr,z)
VAL=[];PEAK=[]
for i in range(NBAY):
    b0,b1=EDGES[i],EDGES[i+1];bm=0.5*(b0+b1);t0,t1,tm=[(x-A0)/(A1-A0) for x in(b0,b1,bm)]
    F0=P(b0,fr(t0)+0.8,zf(b0));F1=P(b1,fr(t1)+0.8,zf(b1));Fm=P(bm,fr(tm)+0.8,zf(bm))
    R0=rp(b0,0,ZR);R1=rp(b1,0,ZR);Rp=rp(bm,OVH,ZR+PK)
    for (a,b,c) in((F0,Fm,R0),(Fm,Rp,R0),(Fm,F1,R1),(Fm,R1,Rp)):
        tri(a,b,c,0,True);dz=Vector((0,0,-TH));tri(a+dz,b+dz,c+dz,0,False)
    for (p,q) in((R0,Rp),(Rp,R1),(F0,Fm),(Fm,F1)):box(p+Vector((0,0,0.05)),q+Vector((0,0,0.05)),0.35,0.55,3)   # white edge trims
    for (p,q) in((Fm,Rp),(F0,R0)):box(p-Vector((0,0,TH+0.45)),q-Vector((0,0,TH+0.45)),0.3,0.7,1)   # ridge and valley ribs under the sheet
    VAL.append(b0);PEAK.append((bm,Rp))
VAL.append(EDGES[-1])
# white tubular supports: under each peak a raking column, from each valley foot two V-struts to the neighbouring peaks
for bm,Rp in PEAK:
    foot=rp(bm,-ZFI,SB);tube(foot,Rp-Vector((0,0,0.6)),0.38,3)
for k,b in enumerate(VAL):
    foot=rp(b,-ZFI,SB)
    for j in(k-1,k):
        if 0<=j<len(PEAK):tube(foot,PEAK[j][1]-Vector((0,0,0.6)),0.3,3)
# end closure at the west-stand join (179 deg)
b=EDGES[-1];t=1.0
quad([P(b,fr(t)-1.7,17.2),rp(b,0,17.2),rp(b,0,ZR-TH),P(b,fr(t)+0.8,zf(b)-TH)],2)
# seam cover: the last valley sheet tucks down 2.5 deg under the neighbour roof so no gap opens at the join
b2=b+2.5;za=zf(b)+0.05
G0=P(b,fr(t)+0.8,za);G1=P(b2,fr(t)+0.8,18.6);H0=rp(b,0,ZR+0.05);H1=rp(b2,0,18.6)
for (a,c,d) in((G0,G1,H1),(G0,H1,H0)):
    tri(a,c,d,0,True);dz=Vector((0,0,-TH));tri(a+dz,c+dz,d+dz,0,False)
pass
# facade under the roof along the straight rear edges: white fin band below, grey cladding up to the valleys
WALL=bpy.data.materials.get('wall')
for k in range(len(POLY)-1):
    p,q=POLY[k],POLY[k+1];L=(q-p).length;nseg=max(1,int(L/4));nrm=Vector((-(q-p).y,(q-p).x)).normalized()
    if nrm.dot(p)<0:nrm=-nrm
    for m in range(nseg):
        A=p.lerp(q,m/nseg)-nrm*ZFI;B=p.lerp(q,(m+1)/nseg)-nrm*ZFI;U=k*100+m*L/nseg/4
        quad([Vector((A.x,A.y,0)),Vector((B.x,B.y,0)),Vector((B.x,B.y,SB)),Vector((A.x,A.y,SB))],4,[(U/3,0),(U/3+L/nseg/12,0),(U/3+L/nseg/12,1),(U/3,1)])
        quad([Vector((A.x,A.y,SB)),Vector((B.x,B.y,SB)),Vector((B.x,B.y,ZR-TH)),Vector((A.x,A.y,ZR-TH))],1,[(U,0),(U+L/nseg/4,0),(U+L/nseg/4,2.5),(U,2.5)])
nb.normal_update()
for f in nb.faces:  # vertical walls face outward from the oval centre
    n=f.normal;c=f.calc_center_median()
    if f.material_index in(1,2,4) and abs(n.z)<0.3 and len(f.verts)==4 and (n.x*c.x+n.y*c.y)<0 and c.z<ZR and math.hypot(c.x,c.y)>100:f.normal_flip()
nm=bpy.data.meshes.new('jss_roof');nb.to_mesh(nm);nb.free()
for m in MS+[bpy.data.materials['wall']]:nm.materials.append(m)
ob=bpy.data.objects.new('jss_roof',nm);bpy.context.scene.collection.objects.link(ob)
bpy.ops.export_scene.gltf(filepath=OUT,export_format='GLB')
print('DONE')
