import bpy, sys
p = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=p)
rows = []
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    xs = [ (o.matrix_world @ v.co) for v in o.data.vertices ]
    if not xs: continue
    dx = max(v.x for v in xs) - min(v.x for v in xs); dy = max(v.y for v in xs) - min(v.y for v in xs); dz = max(v.z for v in xs) - min(v.z for v in xs)
    if dx > 60:
        for m in o.data.materials:
            col = None; tex = None
            if m and m.use_nodes:
                b = m.node_tree.nodes.get('Principled BSDF')
                if b:
                    col = tuple(round(c, 3) for c in b.inputs['Base Color'].default_value[:3])
                    for l in b.inputs['Base Color'].links: tex = l.from_node.bl_idname
            rows.append((o.name, round(dx), round(dy), round(dz, 2), m.name if m else None, col, tex))
for r in rows: print('APRON', r)
