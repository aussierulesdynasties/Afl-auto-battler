import bpy,os,sys
out=sys.argv[sys.argv.index('--')+1];os.makedirs(out,exist_ok=True)
n=0
for im in bpy.data.images:
    if im.filepath:im.reload();n+=1
print('RELOADED',n)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,'traeger.blend'),relative_remap=True)
for im in bpy.data.images:
    if im.filepath and not os.path.exists(bpy.path.abspath(im.filepath)):print('MISSING',im.filepath)
bpy.ops.export_scene.gltf(filepath=os.path.join(out,'traeger.glb'),export_format='GLB',export_cameras=False,export_lights=False);print('SAVED12')
