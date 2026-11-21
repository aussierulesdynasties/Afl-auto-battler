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
MS=[mat('jss_sheet','jss_sheet.png'),mat('jss_steel','jss_steel.png',0.7,0.5),mat('jss_fascia','jss_fascia.png')]
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
EDGES=[A0,angv(POLY[1]),angv(POLY[2])];n=13
EDGES+= [EDGES[-1]+(A1-EDGES[-1])*k/n for k in range(1,n+1)]
NBAY=len(EDGES)-1
def zf(an):return 23.6-2.2*(an-A0)/(A1-A0)
for i in range(NBAY):
    a0,a1=EDGES[i],EDGES[i+1];t0,t1=(a0-A0)/(A1-A0),(a1-A0)/(A1-A0)
    ra=rear(a0);rb=rear(a1);rm=0.5*(wr(t0)+wr(t1))
    g=math.degrees(GAP/rm);b0,b1=a0+g/2,a1-g/2;ra=rear(b0);rb=rear(b1)
    ri=0.5*(fr(t0)+fr(t1))+0.8;mw0,mw1=wr(t0),wr(t1)
    fl0=max(zf(a0),ZR+DROP+0.4);fl1=max(zf(a1),ZR+DROP+0.4)
    # inner panel: field edge to the old wall line, saw-tooth (b1 side high)
    tl=[P(b0,ri,fl0),P(b1,ri,fl1+STEP),P(b1,mw1,ZR+DROP+STEP),P(b0,mw0,ZR+DROP)]
    # outer panel: wall line to the straight rear edge, level rear
    to=[P(b0,mw0,ZR+DROP*0.0),P(b1,mw1,ZR+STEP*0.5),P(b1,rb,ZR),P(b0,ra,ZR)]
    for pan in(tl,to):
        L=(pan[3]-pan[0]).length;w0=(pan[1]-pan[0]).length;w1=(pan[2]-pan[3]).length
        def tri(a,b,c,mi,uv=None):
            f=nb.faces.new([nb.verts.new(a),nb.verts.new(b),nb.verts.new(c)]);f.material_index=mi
            if uv:
                for l,u in zip(f.loops,uv):l[uvl].uv=u
        U=[(0,0),(w0/4,0),(w0/4,L/4),(0,L/4)]
        tri(pan[0],pan[2],pan[1],0,[U[0],U[2],U[1]]);tri(pan[0],pan[3],pan[2],0,[U[0],U[3],U[2]])  # top, normals up
        bl=[v-Vector((0,0,TH)) for v in pan];tri(bl[0],bl[1],bl[2],1);tri(bl[0],bl[2],bl[3],1)  # underside, same diagonal
        for j in range(4):quad([pan[j],bl[j],bl[(j+1)%4],pan[(j+1)%4]],1)
    # step faces: bay high side (dark), and inner->outer drop at the wall line
    quad([P(b1,ri,fl1+STEP),P(b1,mw1,ZR+DROP+STEP),P(b1,mw1,ZR-0.3),P(b1,ri,fl1-0.3)],1)
    quad([P(b0,mw0,ZR+DROP),P(b1,mw1,ZR+DROP+STEP),P(b1,mw1,ZR+STEP*0.5-0.3),P(b0,mw0,ZR-0.3)],1)
    # ribs and trusses under both bay edges, field edge to rear edge
    for an,fz,rr,mw in((b0,fl0,ra,mw0),(b1,fl1,rb,mw1)):
        p0=P(an,ri+0.5,fz-TH);pm=P(an,mw,ZR+DROP-TH);p1=P(an,rr-0.8,ZR-TH)
        box(p0,pm,0.3,0.55,1);box(pm,p1,0.3,0.55,1)
        q0=P(an,ri+6,fz-TH-1.7);q1=P(an,mw,ZR+DROP-TH-1.7);box(q0,q1,0.2,0.25,1)
        for k in range(6):
            u0,u1=k/6,(k+1)/6;top=p0.lerp(pm,u0 if k%2 else u1);bot=q0.lerp(q1,u1 if k%2 else u0)
            box(top-Vector((0,0,0.5)),bot,0.12,0.12,1)
# end fascia at the west-stand join (179 deg): close the slot between this roof and the lower west roof
bL=EDGES[-1]-math.degrees(GAP/wr(1.0))/2;riL=fr(1.0)+0.8;fl=max(zf(EDGES[-1]),ZR+DROP+0.4)
for (r0,z0,r1,z1) in((riL-2.5,fl+STEP,wr(1.0),ZR+DROP+STEP),(wr(1.0),ZR+STEP*0.5,rear(bL),ZR)):
    quad([P(bL,r0,17.2),P(bL,r1,17.2),P(bL,r1,z1-TH),P(bL,r0,z0-TH)],2)
# deep level rear fascia along the straight rear edges, with the building facade beneath it
WALL=bpy.data.materials.get('wall')
pts=[POLY[0]]+POLY[1:]
for k in range(len(pts)-1):
    p,q=pts[k],pts[k+1];L=(q-p).length;nseg=max(1,int(L/4));nrm=Vector((-(q-p).y,(q-p).x)).normalized()
    if nrm.dot(p)<0:nrm=-nrm   # outward
    for m in range(nseg):
        u0,u1=m/nseg,(m+1)/nseg;A=p.lerp(q,u0);B=p.lerp(q,u1);U=k*100+m*L/nseg/4
        Ao=A+nrm*0.4;Bo=B+nrm*0.4
        quad([Vector((Ao.x,Ao.y,ZR-FD)),Vector((Bo.x,Bo.y,ZR-FD)),Vector((Bo.x,Bo.y,ZR+0.4)),Vector((Ao.x,Ao.y,ZR+0.4))],2,[(U,0),(U+L/nseg/4,0),(U+L/nseg/4,1),(U,1)])
        quad([Vector((A.x,A.y,ZR+0.4)),Vector((B.x,B.y,ZR+0.4)),Vector((Bo.x,Bo.y,ZR+0.4)),Vector((Ao.x,Ao.y,ZR+0.4))],2)
        quad([Vector((Ao.x,Ao.y,ZR-FD)),Vector((A.x,A.y,ZR-FD)),Vector((B.x,B.y,ZR-FD)),Vector((Bo.x,Bo.y,ZR-FD))],1)
        Ai=A-nrm*1.0;Bi=B-nrm*1.0
        quad([Vector((Ai.x,Ai.y,0)),Vector((Bi.x,Bi.y,0)),Vector((Bi.x,Bi.y,ZR-FD)),Vector((Ai.x,Ai.y,ZR-FD))],3,[(U,0),(U+L/nseg/12,0),(U+L/nseg/12,1),(U,1)])
nb.normal_update()
for f in nb.faces:  # orient: sheet tops up, fascia/facade faces outward from the oval centre
    n=f.normal;c=f.calc_center_median()
    if f.material_index==0 and n.z<0:f.normal_flip()
    elif f.material_index in(2,3) and abs(n.z)<0.5 and (n.x*c.x+n.y*c.y)<0:f.normal_flip()
nm=bpy.data.meshes.new('jss_roof');nb.to_mesh(nm);nb.free()
for m in MS+[bpy.data.materials['wall']]:nm.materials.append(m)
ob=bpy.data.objects.new('jss_roof',nm);bpy.context.scene.collection.objects.link(ob)
bpy.ops.export_scene.gltf(filepath=OUT,export_format='GLB')
print('DONE')
