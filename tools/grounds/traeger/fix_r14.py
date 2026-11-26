"""r14 patch on the game model (assets/grounds/traeger/traeger.glb, made by join_for_game.py).

Roof and soffit pairs that lie in one plane: club.py lays each clubroom roof's soffit on the roof itself
(blue_soffit under green_roof_b, 239 m2 over the green clubrooms north of the grandstand). Both materials
are double-sided, so the game drew whichever won the depth test: the pale soffit showed on top and the
teal roof Google Earth shows read cream. Every face that lies within 2 cm of an opposite-facing face of
another part, and faces down, is moved 0.08 m down along its normal (a soffit hangs under its roof).

    python fix_r14.py -- in.glb out.glb        (Blender's Python module, bpy 5.2)
"""
import sys

import bpy  # noqa: I001  (bpy first: it puts bmesh and mathutils on the path)
import bmesh
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
objs = [o for o in bpy.data.objects if o.type == 'MESH']
trees = []
for o in objs:
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.transform(o.matrix_world)
    bm.normal_update()
    trees.append((BVHTree.FromBMesh(bm), [f.normal.copy() for f in bm.faces]))
    bm.free()
move = {}
for k, o in enumerate(objs):
    mw = o.matrix_world
    nm = mw.to_3x3().inverted().transposed()
    for f in o.data.polygons:
        n = (nm @ f.normal).normalized()
        if n.z > -0.3:                   # only a face that looks down (Blender z up) is moved
            continue
        c = mw @ f.center
        for k2, (t, normals) in enumerate(trees):
            if k2 == k:
                continue
            hit = t.ray_cast(c + n * 0.02, -n, 0.04)
            if hit[0] is not None and normals[hit[2]].dot(n) < -0.95:
                move.setdefault(k, set()).add(f.index)
                break
total = 0
for k, fis in move.items():
    o = objs[k]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.faces.ensure_lookup_table()
    inv = o.matrix_world.to_3x3().inverted()
    verts = {}
    for fi in fis:
        f = bm.faces[fi]
        wn = (o.matrix_world.to_3x3().inverted().transposed() @ f.normal).normalized()
        for v in f.verts:
            verts[v.index] = inv @ (wn * 0.08)
    bm.verts.ensure_lookup_table()
    for vi, off in verts.items():
        bm.verts[vi].co += off
    bm.to_mesh(o.data)
    bm.free()
    total += len(fis)
    print('moved', o.name, len(fis), 'faces')
print('faces moved', total)
bpy.ops.export_scene.gltf(filepath=a[1], export_format='GLB', export_apply=True, export_yup=True)
