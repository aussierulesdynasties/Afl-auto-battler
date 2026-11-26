# Real 3D seats (lead 2026-11-20): each painted seat face becomes stepped concrete rows (tread + riser, ~0.8 m deep)
# with one instanced seat per 0.5 m along each row: pan, back and stem, 5 cm gap between seats, radial aisles
# about every 7 m. Teal for 'seat', maroon for 'seatm'. Empty. Exec'd by build_hand.py after the main mesh.
import bmesh,math
from mathutils import Vector
ROWD=0.80;PITCH=0.50;BAY=7.0;AISLE=1.1
def seat_mesh(name,col):
    sm=bpy.data.meshes.new(name);b=bmesh.new()
    def box(x0,x1,y0,y1,z0,z1,tilt=0.0):
        vv=[b.verts.new((x,y+tilt*(z-z0),z)) for z in (z0,z1) for y in (y0,y1) for x in (x0,x1)]
        for f in((0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)):b.faces.new([vv[i] for i in f])
    box(-0.215,0.215,-0.20,0.22,0.40,0.45)          # pan (local +y faces the field)
    box(-0.215,0.215,-0.25,-0.20,0.45,0.82,-0.15)   # back, reclined
    box(-0.03,0.03,-0.12,-0.05,0.0,0.40)            # stem
    bmesh.ops.recalc_face_normals(b,faces=b.faces);b.to_mesh(sm);b.free()
    m=bpy.data.materials.new(name+'_m');m.use_nodes=True;bs=m.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value=(*[(c/255)**2.2 for c in col],1);bs.inputs['Roughness'].default_value=0.45
    sm.materials.append(m);o=bpy.data.objects.new(name,sm);return o
def zlerp(a,b,t):return a+(b-a)*t
sb=bmesh.new();PTS={'seat':[],'seatm':[]};CI=MI['conc']
for m,q in SEATQ:
    q=[Vector(p) for p in q]
    e=[(0,1,3,2),(1,2,0,3)]   # (low0,low1,high0,high1) candidates from the two opposite-edge pairings
    best=None
    for a0,a1,b0,b1 in e:
        for L0,L1,H0,H1 in((q[a0],q[a1],q[b0],q[b1]),(q[b0],q[b1],q[a0],q[a1])):
            dz=(H0.z+H1.z-L0.z-L1.z)/2
            if best is None or dz>best[0]:best=(dz,L0,L1,H0,H1)
    dz,L0,L1,H0,H1=best
    if (L0-H0).length+(L1-H1).length>(L0-H1).length+(L1-H0).length:H0,H1=H1,H0
    h0=(Vector((H0.x,H0.y,0))-Vector((L0.x,L0.y,0))).length;h1=(Vector((H1.x,H1.y,0))-Vector((L1.x,L1.y,0))).length
    n=max(1,int(max(h0,h1)/ROWD));fw=Vector(((L0.x+L1.x-H0.x-H1.x)/2,(L0.y+L1.y-H0.y-H1.y)/2,0))
    if fw.length<1e-6:continue
    fw.normalize();yaw=math.atan2(fw.y,fw.x)-math.pi/2
    # rows measured from the low edge on each side separately, so rows line up across neighbouring strips
    T0=lambda k:1.0 if k>=n else min(1.0,k*ROWD/max(h0,1e-6));T1=lambda k:1.0 if k>=n else min(1.0,k*ROWD/max(h1,1e-6))
    def face(ps,want):
        f=sb.faces.new([sb.verts.new(p) for p in ps]);f.normal_update()
        if f.normal.dot(want)<0:f.normal_flip()
        f.material_index=CI
    for k in range(n):
        a,b_=L0.lerp(H0,T0(k)),L1.lerp(H1,T1(k));d,c=L0.lerp(H0,T0(k+1)),L1.lerp(H1,T1(k+1));za,zb=d.z,c.z
        if T0(k+1)-T0(k)<1e-6 and T1(k+1)-T1(k)<1e-6:continue
        face([Vector((a.x,a.y,za)),Vector((b_.x,b_.y,zb)),Vector((c.x,c.y,zb)),Vector((d.x,d.y,za))],Vector((0,0,1)))
        if za-a.z>0.02 or zb-b_.z>0.02:face([a,b_,Vector((b_.x,b_.y,zb)),Vector((a.x,a.y,za))],fw)
        if (d-a).length<0.6 and (c-b_).length<0.6:continue   # sliver row: no seats
        P0=a.lerp(d,0.55);P1=b_.lerp(c,0.55);P0.z,P1.z=za,zb
        A0=math.atan2(P0.y-PC.y,P0.x-PC.x);A1=math.atan2(P1.y-PC.y,P1.x-PC.x)
        while A1-A0>math.pi:A1-=2*math.pi
        while A1-A0<-math.pi:A1+=2*math.pi
        if A1<A0:A0,A1,P0,P1=A1,A0,P1,P0
        rm=((Vector((P0.x,P0.y,0))-PC).length+(Vector((P1.x,P1.y,0))-PC).length)/2
        bw=BAY/100.0;ai=AISLE/100.0
        for bb in range(math.floor(A0/bw),math.floor(A1/bw)+1):
            Ab=bb*bw+ai;Ae=(bb+1)*bw;j=0
            while True:
                A=Ab+(0.25+j*PITCH)/rm;j+=1
                if A+0.25/rm>Ae:break
                if A<A0 or A>=A1:continue
                u=(A-A0)/(A1-A0) if A1>A0 else 0;PTS[m].append((P0.lerp(P1,u),yaw))
sm_=bpy.data.meshes.new('steps');sb.to_mesh(sm_);sb.free()
for mm in me.materials:sm_.materials.append(mm)
st=bpy.data.objects.new('steps',sm_);bpy.context.scene.collection.objects.link(st)
bpy.ops.object.select_all(action='DESELECT');st.select_set(True);ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.join()
SEATOBJ=[]
for m,col in(('seat',(38,112,108)),('seatm',(112,38,46))):
    proto=seat_mesh('proto_'+m,col);pts=PTS[m]
    pm=bpy.data.meshes.new('pts_'+m);pm.vertices.add(len(pts));pm.vertices.foreach_set('co',[c for p,_ in pts for c in p])
    at=pm.attributes.new('rot','FLOAT_VECTOR','POINT');at.data.foreach_set('vector',[c for _,y in pts for c in (0,0,y)])
    po=bpy.data.objects.new('seats_'+m,pm);bpy.context.scene.collection.objects.link(po)
    bpy.context.scene.collection.objects.link(proto);proto.hide_render=True;proto.hide_viewport=True
    ng=bpy.data.node_groups.new('inst_'+m,'GeometryNodeTree')
    ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    N=ng.nodes;gi=N.new('NodeGroupInput');go=N.new('NodeGroupOutput');ip=N.new('GeometryNodeInstanceOnPoints')
    oi=N.new('GeometryNodeObjectInfo');oi.inputs['Object'].default_value=proto
    na=N.new('GeometryNodeInputNamedAttribute');na.data_type='FLOAT_VECTOR';na.inputs['Name'].default_value='rot'
    L=ng.links;L.new(gi.outputs[0],ip.inputs['Points']);L.new(oi.outputs['Geometry'],ip.inputs['Instance']);L.new(na.outputs['Attribute'],ip.inputs['Rotation']);L.new(ip.outputs['Instances'],go.inputs[0])
    md=po.modifiers.new('inst','NODES');md.node_group=ng
    SEATOBJ.append(po);print('SEATS',m,len(pts))
