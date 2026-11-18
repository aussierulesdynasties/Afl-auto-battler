import bpy,os,sys
out=sys.argv[-1]
for o in [o for o in bpy.data.objects if o.name.startswith('east_shelter')]:print('DEL',o.name);bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,'traeger.blend'),relative_remap=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(out,'traeger.glb'),export_format='GLB',export_cameras=False,export_lights=False);print('SAVED10')
