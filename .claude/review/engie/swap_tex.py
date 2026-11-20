# Swap repainted textures into the built glb (build.py needs plan.json, which was never committed).
# blender -b --python swap_tex.py -- in.glb out.glb name1 name2 ...
import bpy,sys,os
a=sys.argv[sys.argv.index('--')+1:];src,dst,names=os.path.abspath(a[0]),os.path.abspath(a[1]),a[2:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
hit=set()
for im in bpy.data.images:
    for n in names:
        if im.name.startswith(n) or os.path.basename(im.filepath or '').startswith(n):
            im.filepath=os.path.abspath(f'tex/{n}.png');im.source='FILE';im.reload();im.pack();hit.add(n)
print('SWAPPED',sorted(hit),'IMAGES',[i.name for i in bpy.data.images][:60])
bpy.ops.export_scene.gltf(filepath=dst,export_format='GLB')
