# The MCG model as the game ships it (assets/grounds/mcg/mcg.glb): build.py's model without the seats mesh (the game
# draws the seats from seat_tmpl.bin / seats_*.bin), every texture at most 512 px on its long side, WebP in the GLB.
# blender -b --python tools/grounds/mcg/model/ship_mcg.py -- out_dir
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
import build
build.build_all()
argv = sys.argv[sys.argv.index('--') + 1:]; out = argv[0]; os.makedirs(out, exist_ok=True)
for ob in [o for o in bpy.data.objects if o.name == 'seats']:
    bpy.data.objects.remove(ob, do_unlink=True)
for im in bpy.data.images:
    w, h = im.size
    if max(w, h) > 512:
        k = 512.0 / max(w, h); im.scale(max(1, round(w * k)), max(1, round(h * k)))
bpy.ops.export_scene.gltf(filepath=os.path.join(out, 'mcg.glb'), export_format='GLB', export_image_format='WEBP',
                          use_selection=False, export_cameras=False, export_lights=False)
print('shipped', os.path.join(out, 'mcg.glb'))
