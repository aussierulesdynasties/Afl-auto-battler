import bpy, collections
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r'D:/Temp/claude/14b1484a65bfbd74/76476bc6-b87c-4245-8ecb-61de5d49956b/scratchpad/glb/optus.glb')
for o in bpy.context.scene.objects:
    if o.type != 'MESH': continue
    me = o.data; M = o.matrix_world; c = collections.Counter(); ex = {}
    for p in me.polygons:
        w = M @ p.center
        if w.z < 1.5 and abs(p.normal.z) > 0.9:
            m = me.materials[p.material_index].name if me.materials else '-'
            c[m] += p.area; e = ex.setdefault(m, [1e9, -1e9, 1e9, -1e9])
            e[0] = min(e[0], w.x); e[1] = max(e[1], w.x); e[2] = min(e[2], w.y); e[3] = max(e[3], w.y)
    for m, a in c.most_common(): print('LOW', o.name, m, round(a), [round(v) for v in ex[m]])
