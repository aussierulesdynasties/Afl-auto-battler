import bpy,sys,math
O=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+"adelaide_es.glb")
o=bpy.data.objects['hotel'];me=o.data;mw=o.matrix_world;R=mw.to_3x3()
def mat(n,f):
    m=bpy.data.materials.new(n);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(O+f);t.image.pack()
    nt.links.new(t.outputs['Color'],b.inputs['Base Color']);b.inputs['Roughness'].default_value=0.7
    me.materials.append(m);return len(me.materials)-1
hw=mat('hotel_facade','hotel_facade.png');gt=mat('gate_facade','gate_facade.png')
uv=me.uv_layers[0].data;cnt=[0,0]
for p in me.polygons:
    n=R@p.normal
    if abs(n.z)>0.3: continue
    c=mw@p.center; r=math.hypot(c.x,c.y)
    nh=math.hypot(n.x,n.y); 
    tang=(-n.y/nh,n.x/nh)
    az=math.degrees(math.atan2(c.y,c.x)); g=2.0<=az<=20.0; p.material_index=gt if g else hw; cnt[g]+=1
    for li in p.loop_indices:
        w=mw@me.vertices[me.loops[li].vertex_index].co
        uv[li].uv=(math.atan2(w.y,w.x)*130.0/12.0, w.z/21.0)
print("CNT wing,gate",cnt)
bpy.ops.export_scene.gltf(filepath=O+"adelaide_es2.glb",export_format='GLB')
