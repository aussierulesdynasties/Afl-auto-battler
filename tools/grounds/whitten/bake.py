# blender -b w3.blend --python bake.py -- OUT.glb
# Bakes each part's hand-made procedural colour into its own image (fresh non-overlapping UVs),
# swaps in one plain image material per part, drops the inside turf, exports a GLB.
import bpy,sys,os,math
OUT=os.path.abspath(sys.argv[sys.argv.index('--')+1:][0])
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=4
for ob in list(bpy.data.objects):
    if ob.type!='MESH' or 'turf' in ob.name:
        if ob.type=='MESH':bpy.data.objects.remove(ob)
        continue
meshes=[o for o in bpy.data.objects if o.type=='MESH']
TEXEL=0.03  # metres per pixel wanted (3 cm)
for ob in meshes:
    me=ob.data;area=sum(p.area for p in me.polygons)*(ob.matrix_world.to_scale()[0]**2)
    res=int(min(4096,max(512,2**math.ceil(math.log2(math.sqrt(area/0.7)/TEXEL)))))
    uv=me.uv_layers.new(name='bake');me.uv_layers.active=uv
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60),island_margin=2.0/res,scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    img=bpy.data.images.new(ob.name+'_albedo',res,res,alpha=False);img.colorspace_settings.name='sRGB'
    nodes=[]
    for slot in ob.material_slots:
        m=slot.material
        if m is None:continue
        n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=img
        for x in m.node_tree.nodes:x.select=False
        n.select=True;m.node_tree.nodes.active=n;nodes.append((m,n))
    bpy.ops.object.bake(type='DIFFUSE',pass_filter={'COLOR'},margin=4,uv_layer='bake')
    img.filepath_raw=os.path.join(os.path.dirname(OUT),'bake',ob.name+'.png');img.file_format='PNG'
    os.makedirs(os.path.dirname(img.filepath_raw),exist_ok=True);img.save()
    for m,n in nodes:m.node_tree.nodes.remove(n)
    nm=bpy.data.materials.new(ob.name+'_mat');nm.use_nodes=True;bs=nm.node_tree.nodes['Principled BSDF']
    t=nm.node_tree.nodes.new('ShaderNodeTexImage');t.image=img;nm.node_tree.links.new(t.outputs[0],bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value=0.75
    me.materials.clear();me.materials.append(nm)
    for l in [l for l in me.uv_layers if l.name!='bake']:me.uv_layers.remove(l)
    print('baked',ob.name,res,flush=True)
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT,export_format='GLB',use_selection=True,export_image_format='JPEG',export_jpeg_quality=92,export_apply=True,export_cameras=False,export_lights=False)
print('exported',OUT)
