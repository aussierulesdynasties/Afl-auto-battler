# straight-down ortho render of OUT.glb at the satellite's scale: blender -b -P topdown.py -- in.glb out.png
import bpy,sys,json,math
a=sys.argv[sys.argv.index('--')+1:];S=json.load(open('sat.json'))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
import os,bmesh
if os.environ.get('ROOFONLY'):
    keep={'roof','navy','roofunder','yellow'}
    for o in bpy.data.objects:
        if o.type!='MESH':continue
        bm=bmesh.new();bm.from_mesh(o.data);ms=[mm.name.split('.')[0] for mm in o.data.materials]
        bmesh.ops.delete(bm,geom=[f for f in bm.faces if ms[f.material_index] not in keep],context='FACES');bm.to_mesh(o.data);bm.free()
sc=bpy.context.scene;W=1000;sc.render.resolution_x=W;sc.render.resolution_y=W;sc.render.film_transparent=True;sc.render.engine='BLENDER_EEVEE'
cd=bpy.data.cameras.new('c');cd.type='ORTHO';cd.ortho_scale=W*S['mpp'];cd.clip_end=2000;co=bpy.data.objects.new('c',cd);sc.collection.objects.link(co);sc.camera=co
co.location=(0,0,600);co.rotation_euler=(0,0,0)
sd=bpy.data.lights.new('s','SUN');sd.energy=3;so=bpy.data.objects.new('s',sd);sc.collection.objects.link(so);so.rotation_euler=(math.radians(30),0,math.radians(-141))
w=bpy.data.worlds.new('w');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Strength'].default_value=0.6;sc.world=w;sc.view_settings.view_transform='Standard'
import os;sc.render.filepath=os.path.abspath(a[1]);bpy.ops.render.render(write_still=True)
