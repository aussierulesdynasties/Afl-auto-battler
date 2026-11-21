import bpy,sys,math,collections
O=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+"adelaide_westback.glb")
o=bpy.data.objects['stands'];me=o.data;mw=o.matrix_world;R=mw.to_3x3()
m=bpy.data.materials.new('es_facade');m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(O+"es_facade.png");t.image.pack()
nt.links.new(t.outputs['Color'],b.inputs['Base Color']);b.inputs['Roughness'].default_value=0.8;b.inputs['Metallic'].default_value=0
me.materials.append(m);mi=len(me.materials)-1;src=[i for i,s in enumerate(me.materials) if s and s.name=='stands'][0]
cand=[];rmax=collections.defaultdict(float)
for p in me.polygons:
    if p.material_index!=src: continue
    n=R@p.normal
    c=mw@p.center
    if abs(n.z)>0.2 and not (c.z>14 and -0.95<n.z<0.75): continue
    if n.x*c.x+n.y*c.y<=0: continue
    r=math.hypot(c.x,c.y); k=int(math.degrees(math.atan2(c.y,c.x))//4)
    cand.append((p.index,r,k)); rmax[k]=max(rmax[k],r)
sel=[i for i,r,k in cand if r>rmax[k]-8 and r>78]
uv=me.uv_layers[0].data
for i in sel:
    p=me.polygons[i]; p.material_index=mi
    for li in p.loop_indices:
        w=mw@me.vertices[me.loops[li].vertex_index].co; az=math.atan2(w.y,w.x)
        uv[li].uv=(az*125.0/36.0, w.z/27.0)
print("SEL",len(sel),"of",len(cand))
bpy.ops.export_scene.gltf(filepath=O+"adelaide_es.glb",export_format='GLB')
