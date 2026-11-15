"""Fit downloaded hair packs (Sketchfab, VincentFreelance "Male Fashion Hair", CC-BY) to our
footballer's head and export them for the 3D oval: one GLB, one mesh per cut, on the head bone.

blender --background --python export_sf_hair_glb.py -- BODY_TYPES.json TYPE OUT.glb PREFIX=PACK [...]
PACK: an .fbx or .glb in which each cut is its own mesh, modelled on a MakeHuman body that stands
in the same file (the packs ship one body per cut). Each cut moves from the head of the body
under it to ours: the crown matched, the cranium's width and depth scaled to ours. A cut's "cap"
mesh (hair9cap...) joins its cut. Decimated to ARD_HAIR_TRIS. Meshes come out as hair_PREFIX_NN.
"""
import json, os, re, sys, time
import bpy
from mathutils import Matrix, Vector

PIPE = os.environ.get("ARD_PIPELINE_BLENDER", os.path.join(os.path.dirname(__file__), "..", "..", "..", "ard-asset-pipeline", "tools", "blender"))
sys.path.insert(0, PIPE)
import ard_body

TRIS = int(os.environ.get("ARD_HAIR_TRIS", "2500"))
# The cranium: everything this far below the crown (metres), above the ears and brow.
CRANIUM = 0.12

t0 = time.time()
argv = sys.argv[sys.argv.index("--") + 1:]
presets, body_type, out = json.load(open(argv[0])), argv[1], argv[2]
packs = [a.split("=", 1) for a in argv[3:]]


def world_verts(ob):
    m = ob.matrix_world
    return [m @ v.co for v in ob.data.vertices]


def cranium(verts):
    """Crown height, and the centre and size (x, y) of the cranium below it."""
    top = max(v.z for v in verts)
    near = [v for v in verts if v.z > top - CRANIUM]
    # Only the head: arms in a T pose sit lower than the cranium band, but keep to the middle.
    cx = sorted(v.x for v in near)[len(near) // 2]
    near = [v for v in near if abs(v.x - cx) < 0.15]
    lo = Vector((min(v.x for v in near), min(v.y for v in near)))
    hi = Vector((max(v.x for v in near), max(v.y for v in near)))
    return top, (lo + hi) / 2, hi - lo


bpy.ops.wm.read_homefile(use_empty=True)
basemesh, rig = ard_body.build_body(body_type, presets[body_type]["macros"], targets=presets[body_type].get("targets"))
our_top, our_c, our_s = cranium(world_verts(basemesh))
print(f"OUR head: crown {our_top:.3f} centre {tuple(round(x, 3) for x in our_c)} size {tuple(round(x, 3) for x in our_s)}")
mine = set(bpy.data.objects)

made = []
for prefix, pack in packs:
    before = set(bpy.data.objects)
    if pack.lower().endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=pack)
    else:
        bpy.ops.import_scene.gltf(filepath=pack)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.type == "MESH":
            o.data = o.data.copy() if o.data.users > 1 else o.data
    bpy.context.view_layer.update()
    meshes = [o for o in new if o.type == "MESH"]
    hairs = [o for o in meshes if re.match(r"hair\d", o.name, re.I) and "cap" not in o.name.lower()]
    caps = [o for o in meshes if "cap" in o.name.lower()]
    body_heads = []
    for o in meshes:
        if o in hairs or o in caps or len(o.data.vertices) < 5000:
            continue
        wv = world_verts(o)
        if max(v.z for v in wv) - min(v.z for v in wv) > 1.0:
            body_heads.append((o, cranium(wv)))
    for k, h in enumerate(sorted(hairs, key=lambda o: int(re.match(r"hair(\d+)", o.name, re.I).group(1)))):
        num = int(re.match(r"hair(\d+)", h.name, re.I).group(1))
        hv = world_verts(h)
        hc = sum(hv, Vector()) / len(hv)
        b, (top, c, s) = min(body_heads, key=lambda bh: (Vector((bh[1][1].x, bh[1][1].y)) - hc.xy).length
                             + abs(bh[1][0] - hc.z))
        mine_caps = [cp for cp in caps if int(re.search(r"(\d+)", cp.name).group(1)) == num]
        caps = [cp for cp in caps if cp not in mine_caps]
        parts = [h] + mine_caps
        # Bake every part to world space, then map their head onto ours.
        for p in parts:
            p.data.transform(p.matrix_world)
            p.parent = None
            p.matrix_world = Matrix.Identity(4)
            sx, sy = our_s.x / s.x, our_s.y / s.y
            sz = (sx + sy) / 2
            for v in p.data.vertices:
                v.co = Vector((our_c.x + (v.co.x - c.x) * sx, our_c.y + (v.co.y - c.y) * sy, our_top + (v.co.z - top) * sz))
        bpy.ops.object.select_all(action="DESELECT")
        for p in parts:
            p.select_set(True)
        bpy.context.view_layer.objects.active = h
        if len(parts) > 1:
            bpy.ops.object.join()
        ob = bpy.context.view_layer.objects.active
        n0 = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        if n0 > TRIS:
            dec = ob.modifiers.new("decimate", "DECIMATE")
            dec.ratio = TRIS / n0
            bpy.ops.object.modifier_apply(modifier=dec.name)
        ob.data.materials.clear()
        ob.data.materials.append(bpy.data.materials.new(f"ARD_hair_{prefix}_{num:02d}"))
        for p in ob.data.polygons:
            p.use_smooth = True
        mw = ob.matrix_world.copy()
        ob.parent = rig
        ob.parent_type = "BONE"
        ob.parent_bone = "head"
        ob.matrix_world = mw
        ob.name = ob.data.name = f"hair_{prefix}_{num:02d}"
        n1 = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        print(f"HAIR {ob.name}: {n0} -> {n1} tris (source head crown {top:.3f}, scale {sx:.3f} x {sy:.3f})")
        made.append(ob)
    for o in [o for o in bpy.data.objects if o not in mine and o not in made]:
        bpy.data.objects.remove(o, do_unlink=True)

bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
for ob in made:
    ob.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True,
                          export_animations=False, export_apply=False, export_yup=True)
print(f"EXPORT {out}: {len(made)} cuts in {time.time() - t0:.1f}s")
