import bpy,sys,math,mathutils
a=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0]);sc=bpy.context.scene
for m in bpy.data.materials: m.use_backface_culling=True
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x,sc.render.resolution_y=960,540
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(1,0,1,1)
sd=bpy.data.lights.new('s','SUN');sd.energy=3;so=bpy.data.objects.new('s',sd);sc.collection.objects.link(so);so.rotation_euler=(0.6,0,3.5)
cd=bpy.data.cameras.new('c');cd.clip_end=5000;co=bpy.data.objects.new('c',cd);sc.collection.objects.link(co);sc.camera=co
print('objs',len([o for o in sc.objects if o.type=='MESH']))
for az in (0,90,180,270):
    A=math.radians(az);e=math.radians(20);r=420
    eye=mathutils.Vector((r*math.cos(e)*math.sin(A),r*math.cos(e)*math.cos(A),r*math.sin(e)))
    # glTF is Y-up; importer converts back to Z-up
    co.location=eye;co.rotation_euler=(mathutils.Vector((0,0,5))-eye).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=a[1]+f'_{az:03d}.png';bpy.ops.render.render(write_still=True)
