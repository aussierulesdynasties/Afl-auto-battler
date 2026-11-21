# Run by reduce.py (exec, its names in scope) when a skyline.json is given: the city's tall buildings
# from OpenStreetMap (osm_skyline.py), extruded from their footprints and stood on the scene's
# terrain, in the scene's own tower materials. A tower the scene already has is not added twice.
import json, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector

def _bvh(names):
    bm = bmesh.new()
    for n in names:
        o = bpy.data.objects.get(n)
        if o is None: continue
        m = o.data.copy(); m.transform(o.matrix_world); bm.from_mesh(m); bpy.data.meshes.remove(m)
    return BVHTree.FromBMesh(bm), bm
TERRAIN, _tbm = _bvh(['bg_near_ground', 'bg_far_terrain'])

def ground_z(x, y):
    hit = TERRAIN.ray_cast(Vector((x, y, 2000.0)), Vector((0, 0, -1)))
    return hit[0].z if hit[0] is not None else 0.0

# the scene's own roofs: a footprint holding one of their centres is already built
_have = []
for n in ('bg_roof_tower_metal', 'bg_roof_block_metal'):
    o = bpy.data.objects.get(n)
    if o is None: continue
    for p in o.data.polygons:
        c = o.matrix_world @ p.center
        if c.z > 20.0: _have.append((c.x, c.y))
_have = np.array(_have) if _have else np.zeros((0, 2))

def _inside(pts, poly):
    x, y = pts[:, 0], pts[:, 1]; c = np.zeros(len(pts), bool)
    for i in range(len(poly)):
        (ax, ay), (bx, by) = poly[i], poly[i - 1]
        m = (ay > y) != (by > y)
        with np.errstate(divide='ignore', invalid='ignore'):
            c ^= m & (x < ax + (bx - ax) * (y - ay) / (by - ay))
    return c

# the scene's tower tints, so the new ones read as the same city
_tw = bpy.data.objects['bg_bld_tower'].data
_tints = sorted({tuple(round(v, 3) for v in d.color) for d in _tw.color_attributes['Col'].data})
_rr = np.random.default_rng(11)

walls = bmesh.new(); roofs = bmesh.new()
wcol = walls.loops.layers.float_color.new('Col'); wuv = walls.loops.layers.uv.new('UVMap')
rcol = roofs.loops.layers.float_color.new('Col'); ruv = roofs.loops.layers.uv.new('UVMap')
added = skipped = 0
for b in json.load(open(SKYLINE)):
    p = b['p']
    cx = sum(q[0] for q in p) / len(p); cy = sum(q[1] for q in p) / len(p)
    if math.hypot(cx, cy) < max(INNER, 300.0): continue
    if len(_have) and _inside(_have, p).any(): skipped += 1; continue
    area2 = sum(p[i - 1][0] * p[i][1] - p[i][0] * p[i - 1][1] for i in range(len(p)))
    if area2 < 0: p = p[::-1]                    # counter-clockwise, so the walls face out
    z0 = min(ground_z(x, y) for x, y in p) - 1.0
    lo, hi = z0 + b['min'], z0 + b['h']
    tint = _tints[_rr.integers(len(_tints))][:3] + (1.0,) if _tints else (0.3, 0.32, 0.33, 1.0)
    vb = [walls.verts.new((x, y, lo)) for x, y in p]; vt = [walls.verts.new((x, y, hi)) for x, y in p]
    u = 0.0
    for i in range(len(p)):
        j = (i + 1) % len(p)
        w = math.hypot(p[j][0] - p[i][0], p[j][1] - p[i][1])
        f = walls.faces.new((vb[i], vb[j], vt[j], vt[i]))
        for l, (uu, vv) in zip(f.loops, ((u, lo), (u + w, lo), (u + w, hi), (u, hi))):
            l[wuv].uv = (uu / 3.0, vv / 3.6); l[wcol] = tint
        u += w
    try:
        f = roofs.faces.new([roofs.verts.new((x, y, hi)) for x, y in p])
        for l in f.loops:
            l[ruv].uv = (l.vert.co.x / 4.0, l.vert.co.y / 4.0); l[rcol] = (0.3, 0.3, 0.28, 1.0)
    except ValueError: pass
    added += 1
bmesh.ops.triangulate(roofs, faces=roofs.faces[:])   # concave footprints
# named as the scene's towers (Blender adds .001), so reduce.py joins them into the scene's
for bm_, name, mat in ((walls, 'bg_bld_tower', 'facade_tower'), (roofs, 'bg_roof_tower_metal', 'roof_tower_metal')):
    me = bpy.data.meshes.new(name); bm_.to_mesh(me); bm_.free()
    me.materials.append(bpy.data.materials[mat])
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
_tbm.free()
print('skyline towers added', added, 'already in the scene', skipped)
