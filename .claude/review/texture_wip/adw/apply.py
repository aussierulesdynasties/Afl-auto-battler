import bpy,sys,math,bmesh
O=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+"orig.glb")
o=bpy.data.objects['stands'];me=o.data;mw=o.matrix_world
m=bpy.data.materials.new('west_back');m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(O+"west_back.png");t.image.pack()
nt.links.new(t.outputs['Color'],b.inputs['Base Color']);nt.links.new(t.outputs['Alpha'],b.inputs['Alpha']);m.blend_method='CLIP' if hasattr(m,'blend_method') else None;
try: m.surface_render_method='DITHERED'
except Exception: pass
b.inputs['Metallic'].default_value=0;b.inputs['Roughness'].default_value=0.85
me.materials.append(m);mi=len(me.materials)-1
sel=[]
for p in me.polygons:
    if abs(p.normal.z)>0.2: continue
    c=mw@p.center; az=math.degrees(math.atan2(c.y,c.x)); r=math.hypot(c.x,c.y)
    if (p.normal.x*c.x+p.normal.y*c.y)>0 and r>90 and -115<az<-20 and c.z>8: sel.append(p.index)
# local top per azimuth (1 deg bins, +-3 deg)
top={}
for i in sel:
    for v in me.polygons[i].vertices:
        w=mw@me.vertices[v].co; k=round(math.degrees(math.atan2(w.y,w.x))); top[k]=max(top.get(k,0),w.z)
ks=sorted(top); print('TOP',min(top.values()),max(top.values()))
def T0(a): return max(top.get(k,0) for k in range(a-3,a+4))
SM={a:sum(T0(b) for b in range(a-12,a+13) if min(ks)<=b<=max(ks))/max(1,sum(1 for b in range(a-12,a+13) if min(ks)<=b<=max(ks))) for a in range(min(ks)-2,max(ks)+3)}
def T(az):  # smoothed wall top, linear between degrees: no kink in the struts (bugfix)
    a=math.floor(az); t=az-a; return SM.get(a,SM[min(SM)])*(1-t)+SM.get(a+1,SM[max(SM)])*t
uv=me.uv_layers['UVMap'].data
for i in sel:
    p=me.polygons[i]; p.material_index=mi
    for li in p.loop_indices:
        w=mw@me.vertices[me.loops[li].vertex_index].co; az=math.atan2(w.y,w.x); r=math.hypot(w.x,w.y)
        uv[li].uv=(az*135.0/36.0, w.z/39.72)  # fixed metres: no stretch where the wall top drops
print("FACES",len(sel))
# concourse behind the arches: copy the wall, keep below 7.5 m, push 4 m inward, add a ceiling back to the wall
import bmesh
bm=bmesh.new(); bm.from_mesh(me); bm.transform(mw)
keep=set(sel); bm.faces.ensure_lookup_table()
dl=[f for f in bm.faces if f.index not in keep]; bmesh.ops.delete(bm,geom=dl,context='FACES')
g=bm.verts[:]+bm.edges[:]+bm.faces[:]
r=bmesh.ops.bisect_plane(bm,geom=g,plane_co=(0,0,7.5),plane_no=(0,0,1),clear_outer=True)
top=[e for e in bm.edges if all(abs(v.co.z-7.5)<1e-3 for v in e.verts)]
ex=bmesh.ops.extrude_edge_only(bm,edges=top); nv=[v for v in ex['geom'] if isinstance(v,bmesh.types.BMVert)]
for v in bm.verts:
    if v in nv: continue
    import mathutils; d=mathutils.Vector((v.co.x,v.co.y,0)).normalized(); v.co-=d*4.0
bmesh.ops.reverse_faces(bm,faces=bm.faces[:])
cm=bpy.data.meshes.new('west_concourse'); bm.to_mesh(cm)
c=bpy.data.materials.new('west_concourse'); c.use_nodes=True; pb=c.node_tree.nodes['Principled BSDF']
pb.inputs['Base Color'].default_value=(0.16,0.16,0.17,1); pb.inputs['Roughness'].default_value=0.9; pb.inputs['Metallic'].default_value=0
cm.materials.append(c); ob=bpy.data.objects.new('west_concourse',cm); bpy.context.scene.collection.objects.link(ob)
print("CONC",len(cm.polygons))
bpy.ops.export_scene.gltf(filepath=O+"adelaide_westback.glb",export_format='GLB')
