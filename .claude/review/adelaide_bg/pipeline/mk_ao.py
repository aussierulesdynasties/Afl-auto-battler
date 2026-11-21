"""Adelaide Oval model (commit 29d16d09f PLYs, copies) -> ../glb/adelaide.glb (geometry for outline/mask) and ../glb/adelaide.blend (its own shade.py materials).
blender -b -P mk_ao.py -- <adelaide dir>"""
import bpy, sys, os, glob, math
A = sys.argv[sys.argv.index('--') + 1]
sys.path.insert(0, os.path.join(A, 'tools')); import shade
bpy.ops.wm.read_factory_settings(use_empty=True)
for f in sorted(glob.glob(os.path.join(A, 'model', '*.ply'))):
    bpy.ops.wm.ply_import(filepath=f)
    o = bpy.context.selected_objects[0]; shade.build(o)
    bpy.context.view_layer.objects.active = o
    try: bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    except Exception as e: print('smooth', e)
H = os.path.dirname(os.path.abspath(__file__)); G = os.path.join(H, '..', 'glb')
bpy.ops.export_scene.gltf(filepath=os.path.join(G, 'adelaide.glb'), export_format='GLB')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(G, 'adelaide.blend'))
print('AO', [o.name for o in bpy.data.objects])
