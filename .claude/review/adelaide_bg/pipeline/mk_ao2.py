"""Newest Adelaide Oval model (origin/main 0499df6cb, PR #1856: PLYs + instanced 3D seats) -> ../glb_new/adelaide.glb (no seats; outline/mask) + adelaide.blend (materials, seat instancing).
blender -b -P mk_ao2.py -- <adelaide dir>"""
import bpy, sys, os
A = sys.argv[sys.argv.index('--') + 1]; RP = os.path.join(A, 'tools', 'render.py')
src = open(RP, encoding='utf-8').read(); src = src[:src.index('# light:')]
sys.argv = [sys.argv[0], '--', 'orbit', 'none']
exec(compile(src, RP, 'exec'), {'__file__': RP, '__name__': 'ao'})
G = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'glb_new')
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.type == 'MESH' and not __import__('re').match(r'seatsd+$', o.name) and not o.hide_render: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(G, 'adelaide.glb'), export_format='GLB', use_selection=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(G, 'adelaide.blend'))
print('AO2', len(bpy.data.objects), [o.name for o in bpy.data.objects][:30])
