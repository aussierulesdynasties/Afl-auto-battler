import bpy,os,sys
d=sys.argv[sys.argv.index('--')+1];out=sys.argv[sys.argv.index('--')+2]
for im in bpy.data.images:
    f=os.path.join(d,im.name.replace('/','_')+'.png')
    if os.path.exists(f):
        im.unpack(method='REMOVE') if im.packed_file else None
        im.filepath=f;im.source='FILE';im.reload();im.pack();print('SET',im.name)
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',export_yup=True,export_image_format='AUTO')
