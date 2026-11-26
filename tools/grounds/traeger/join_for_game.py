"""The Traeger Park model for the match view: its 2,444 parts joined into one per material (about
50 draws instead of 2,444); the big screen's face stays its own part (Oval3DScreens finds it by name).
   python join_for_game.py -- in.glb out.glb      (Blender's Python module, bpy 5.2)
"""
import bpy, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
groups = {}
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    if 'screen' in o.name.lower() or len(o.data.materials) != 1: continue
    groups.setdefault(o.data.materials[0].name, []).append(o)
for objs in groups.values():
    if len(objs) < 2: continue
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
        if o.parent is not None:   # world transforms kept when unparented
            mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
print('mesh objects', len([o for o in bpy.data.objects if o.type == 'MESH']))
bpy.ops.export_scene.gltf(filepath=a[1], export_format='GLB', export_apply=True, export_yup=True)
