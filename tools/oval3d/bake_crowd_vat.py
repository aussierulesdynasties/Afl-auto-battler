# Crowd VAT bake (row 202, 2c): one Mixamo body + its clips -> a vertex animation table (build_crowd_set.gd packs them).
#   blender -b --factory-startup --python bake_crowd_vat.py -- BODY OUTDIR TARGET_TRIS FPS name=ACTION_OR_FBX [...]
# BODY: .glb/.fbx with an armature and skinned mesh(es). A clip is an action already in BODY, or a
# skinless .fbx on the same rig (Mixamo: same mixamorig bone names), whose action is put on BODY's rig.
# Out (Godot reads them; Y-up, metres, the body's own facing):
#   mesh.bin  : u32 nverts, u32 nidx, then nverts x (role rgba u8), then nidx x u32 indices
#   pos.bin   : f32 [rows][nverts][3] world positions;  nrm.bin : same, normals
#   meta.json : {verts, tris, rows, clips: [{name, row, frames, fps}]}
# Roles (one-hot in the colour): R top (shirt, jumper), G bottom (pants, shorts), B skin, A hair.
import bpy, os, sys, json, os, struct, time
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
body, out, target, fps = argv[0], argv[1], int(argv[2]), float(argv[3])
specs = [a.split("=", 1) for a in argv[4:]]
os.makedirs(out, exist_ok=True)
t0 = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)


def imp(p):
    before = set(bpy.data.objects)
    if p.lower().endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=p)
    else:
        bpy.ops.import_scene.gltf(filepath=p)
    return [o for o in bpy.data.objects if o not in before]


objs = imp(body)
rig = next(o for o in objs if o.type == "ARMATURE")
meshes = [o for o in objs if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)]
body_actions = {a.name: a for a in bpy.data.actions}
# Mixamo bodies come at any size (Remy stands 3.78 m): scale to BAKE_HEIGHT metres (default 1.78).
from mathutils import Vector
_top = max((o.matrix_world @ Vector(c)).z for o in meshes for c in o.bound_box)
_bot = min((o.matrix_world @ Vector(c)).z for o in meshes for c in o.bound_box)
K = float(os.environ.get("BAKE_HEIGHT", "1.78")) / max(1e-6, _top - _bot)
print("BAKE height %.3f m -> scale %.4f" % (_top - _bot, K))

ROLE = [("none", ("shoe", "sneaker", "boot", "lash", "lass", "eye", "sock")),
        ("top", ("guernsey", "top", "shirt", "jacket", "hood", "sweat", "tshirt", "body_shirt", "cloth", "zipper")),
        ("bottom", ("short", "pant", "bottom", "jean", "trouser", "leg")),
        ("hair", ("hair", "beard", "brow")),
        ("skin", ("skin", "body", "head", "face", "arm", "hand"))]
COL = {"top": (1, 0, 0, 0), "bottom": (0, 1, 0, 0), "skin": (0, 0, 1, 0), "hair": (0, 0, 0, 1), "none": (0, 0, 0, 0)}


def role_of(name):
    n = name.lower()
    for r, keys in ROLE:
        if any(k in n for k in keys):
            return r
    return None


# Eyes, lashes and brows cannot be seen from the stands, and their many tiny pieces would keep
# their vertices through the decimation while the body collapses: drop them.
for o in [o for o in meshes if any(k in o.name.lower() for k in ("lash", "lass", "eye", "brow"))]:
    print("BAKE dropped", o.name)
    meshes.remove(o)
    bpy.data.objects.remove(o, do_unlink=True)
for o in meshes:
    names = [m.name if m else "" for m in o.data.materials]
    # Mixamo's own characters name each part's mesh (Ch22_Shirt) but share one material.
    own = role_of(o.name)
    print("BAKE mats", o.name, own, [(n, role_of(n)) for n in names])
    attr = o.data.color_attributes.new("role", "FLOAT_COLOR", "POINT")
    vrole = {}
    for p in o.data.polygons:
        r = own or (role_of(names[p.material_index]) if p.material_index < len(names) else None) or "none"
        for v in p.vertices:
            # A vertex on a seam goes to the first role that claims it, skin last.
            if v not in vrole or vrole[v] == "skin":
                vrole[v] = r
    for v in range(len(o.data.vertices)):
        attr.data[v].color = COL[vrole.get(v, "none")]

# Skin under the clothes is never seen, and once the clothes are cut down it pokes through them.
# Delete each body vertex that sits behind a clothing surface (inside it, within a few centimetres).
from mathutils.bvhtree import BVHTree
import bmesh
cloth = [o for o in meshes if role_of(o.name) in ("top", "bottom", "none")]
trees = []
for c in cloth:
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bm.transform(c.matrix_world)
    bm.normal_update()
    trees.append(BVHTree.FromBMesh(bm))
    bm.free()
for o in [o for o in meshes if role_of(o.name) == "skin"]:
    mw = o.matrix_world
    hgt = max(o.dimensions)
    reach = float(os.environ.get("HIDE_REACH", "0.06")) * hgt
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.normal_update()
    nm = mw.to_3x3()
    kill = []
    for v in bm.verts:
        w = mw @ v.co
        d = (nm @ v.normal).normalized()
        # Hidden when a ray straight out of the skin meets clothing close by.
        if any(t.ray_cast(w + d * 1e-4 * hgt, d, reach)[0] is not None for t in trees):
            kill.append(v)
    n0 = len(bm.verts)
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(o.data)
    bm.free()
    print("BAKE hid %d of %d skin verts of %s under clothes" % (len(kill), n0, o.name))

# Each part is cut to its own share of the triangles: hair a quarter, the rest by each part's size.
# (Cutting the joined body instead lets hair strands keep their vertices while the body collapses.)
def ntris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)
hair = [o for o in meshes if role_of(o.name) == "hair"]
rest = [o for o in meshes if o not in hair]
tris = sum(ntris(o) for o in meshes)
budget = {}
hair_t = sum(ntris(o) for o in hair)
rest_t = sum(ntris(o) for o in rest)
for o in hair:
    budget[o] = target * 0.25 * ntris(o) / max(1, hair_t)
for o in rest:
    budget[o] = target * (0.75 if hair else 1.0) * ntris(o) / max(1, rest_t)
for o in meshes:
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    # Split seams stop the collapse: weld duplicate vertices first (a thousandth of the part's size).
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.001 * max(o.dimensions))
    bpy.ops.object.mode_set(mode="OBJECT")
    if o.data.shape_keys:
        # Children's faces carry shape keys; modifiers cannot be applied over them.
        bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
    if role_of(o.name) == "hair" and "brow" not in o.name.lower():
        # Hair cards are see-through strips: drawn solid and cut down they read as shards.
        # Make them one solid shape (voxel remesh), then copy the skin weights back from the cards.
        src = o.copy()
        src.data = o.data.copy()
        bpy.context.collection.objects.link(src)
        vs = [v.co for v in o.data.vertices]
        size = max(max(c[i] for c in vs) - min(c[i] for c in vs) for i in range(3))
        rm = o.modifiers.new("rm", "REMESH")
        rm.mode = "VOXEL"
        rm.voxel_size = size / float(os.environ.get("HAIR_VOX", "28"))
        while o.modifiers[0] != rm:
            bpy.ops.object.modifier_move_up(modifier="rm")
        bpy.ops.object.modifier_apply(modifier="rm")
        dt = o.modifiers.new("dt", "DATA_TRANSFER")
        dt.object = src
        dt.use_vert_data = True
        dt.data_types_verts = {"VGROUP_WEIGHTS"}
        dt.vert_mapping = "POLYINTERP_NEAREST"
        dt.layers_vgroup_select_src = "ALL"
        dt.layers_vgroup_select_dst = "NAME"
        while o.modifiers[0] != dt:
            bpy.ops.object.modifier_move_up(modifier="dt")
        bpy.ops.object.datalayout_transfer(modifier="dt")
        bpy.ops.object.modifier_apply(modifier="dt")
        bpy.data.objects.remove(src, do_unlink=True)
        # The remesh drops the role colours: mark every new vertex as hair again.
        for a in list(o.data.color_attributes):
            if a.name == "role":
                o.data.color_attributes.remove(a)
        attr = o.data.color_attributes.new("role", "FLOAT_COLOR", "POINT")
        for v in range(len(o.data.vertices)):
            attr.data[v].color = COL["hair"]
        print("BAKE solid hair %s %d tris" % (o.name, ntris(o)))
    if role_of(o.name) == "none" and ntris(o) > budget[o] * 2:
        # Shoes: many small pieces (laces, soles) that never collapse. Keep the two biggest shells.
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(o.data)
        seen, isles = set(), []
        for f0 in bm.faces:
            if f0.index in seen:
                continue
            stack, isle = [f0], []
            seen.add(f0.index)
            while stack:
                f = stack.pop()
                isle.append(f)
                for e in f.edges:
                    for g in e.link_faces:
                        if g.index not in seen:
                            seen.add(g.index)
                            stack.append(g)
            isles.append(isle)
        isles.sort(key=len, reverse=True)
        kill = [f for isle in isles[2:] for f in isle]
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        bm.to_mesh(o.data)
        bm.free()
        print("BAKE kept 2 of %d pieces of %s" % (len(isles), o.name))
    for _ in range(4):
        if ntris(o) <= budget[o] * 1.15:
            break
        dec = o.modifiers.new("dec", "DECIMATE")
        dec.ratio = min(1.0, budget[o] / max(1, ntris(o)))
        while o.modifiers[0] != dec:
            bpy.ops.object.modifier_move_up(modifier="dec")
        bpy.ops.object.modifier_apply(modifier="dec")
    print("BAKE part %s budget %d -> %d tris" % (o.name, budget[o], ntris(o)))
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
print("BAKE body", ob.name, "tris", tris, "->", ntris(ob), "load %.1fs" % (time.time() - t0))

scene = bpy.context.scene
src_fps = scene.render.fps / scene.render.fps_base


def action_for(src):
    if src in body_actions:
        return body_actions[src]
    new = imp(src)
    acts = [o.animation_data.action for o in new if o.animation_data and o.animation_data.action]
    a = acts[0]
    # A Mixamo clip keys every bone's position with the bone lengths of the character it was
    # downloaded on. Keep only the rotations, and the hips' movement scaled to this body's height.
    crig = next((o for o in new if o.type == "ARMATURE"), None)
    ratio = 1.0
    hb = next((b for b in rig.data.bones if b.name.endswith("Hips")), None)
    # Mixamo numbers its rigs' bone prefixes (mixamorig:, mixamorig9:): rename the clip's to the body's.
    ch = next((b for b in crig.data.bones if b.name.endswith("Hips")), None) if crig is not None else None
    if ch is not None and hb is not None:
        ratio = hb.head_local.length / max(1e-6, ch.head_local.length)
        bp, cp = hb.name[:-4], ch.name[:-4]
        if bp != cp:
            for fc in fcurves_of(a):
                fc.data_path = fc.data_path.replace('"%s' % cp, '"%s' % bp)
            print("BAKE renamed clip bones %r -> %r" % (cp, bp))
    for fc in list(fcurves_of(a)):
        dp = fc.data_path
        if dp.endswith(".location") or dp.endswith(".scale"):
            if dp.endswith(".location") and hb is not None and '"%s"' % hb.name in dp:
                for k in fc.keyframe_points:
                    k.co[1] *= ratio
                    k.handle_left[1] *= ratio
                    k.handle_right[1] *= ratio
            else:
                remove_fcurve(a, fc)
    print("BAKE clip rig hips ratio %.3f" % ratio)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    return a


def fcurves_of(a):
    if hasattr(a, "layers") and len(a.layers):
        out = []
        for ly in a.layers:
            for st in ly.strips:
                for cb in st.channelbags:
                    out.extend(cb.fcurves)
        return out
    return a.fcurves


def remove_fcurve(a, fc):
    if hasattr(a, "layers") and len(a.layers):
        for ly in a.layers:
            for st in ly.strips:
                for cb in st.channelbags:
                    if fc in list(cb.fcurves):
                        cb.fcurves.remove(fc)
                        return
    a.fcurves.remove(fc)


def grab():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    m = ev.to_mesh()
    n = len(m.vertices)
    co = np.empty(n * 3, np.float32)
    m.vertices.foreach_get("co", co)
    no = np.empty(n * 3, np.float32)
    m.vertices.foreach_get("normal", no)
    mw = np.array(ob.matrix_world, np.float32)
    co = (co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]) * K
    no = no.reshape(-1, 3) @ mw[:3, :3].T
    no /= np.linalg.norm(no, axis=1, keepdims=True) + 1e-9
    roles = None
    if "role" in m.color_attributes:
        rc = np.empty(n * 4, np.float32)
        m.color_attributes["role"].data.foreach_get("color", rc)
        roles = rc.reshape(-1, 4)
    idx = []
    m.calc_loop_triangles()
    tri = np.empty(len(m.loop_triangles) * 3, np.int32)
    m.loop_triangles.foreach_get("vertices", tri)
    ev.to_mesh_clear()
    # Blender Z-up -> Godot Y-up: (x, y, z) -> (x, z, -y)
    g = lambda a: np.stack([a[:, 0], a[:, 2], -a[:, 1]], 1)
    return g(co), g(no), roles, tri


pos, nrm, clips = [], [], []
first = None
for name, src in specs:
    a = action_for(src)
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = a
    if hasattr(rig.animation_data, "action_slot") and a.slots:
        rig.animation_data.action_slot = a.slots[0]
    f0, f1 = a.frame_range
    n = max(1, int(round((f1 - f0) / src_fps * fps)) + 1)
    clips.append({"name": name, "row": len(pos), "frames": n, "fps": fps})
    t1 = time.time()
    for i in range(n):
        f = f0 + i * src_fps / fps
        scene.frame_set(int(f), subframe=f - int(f))
        co, no, roles, tri = grab()
        if first is None:
            first = (roles, tri, len(co))
        assert len(co) == first[2], "vertex count changed between frames"
        pos.append(co)
        nrm.append(no)
    print("BAKE clip %s from %s: %d frames %.2fs/frame" % (name, src, n, (time.time() - t1) / n))

roles, tri, nv = first
# Only the vertices the triangles use (decimation leaves loose ones), renumbered.
used = np.unique(tri)
remap = np.full(nv, -1, np.int64)
remap[used] = np.arange(len(used))
tri = remap[tri]
roles = roles[used]
pos = [p[used] for p in pos]
nrm = [n[used] for n in nrm]
nv = len(used)
with open(os.path.join(out, "mesh.bin"), "wb") as f:
    f.write(struct.pack("<II", nv, len(tri)))
    f.write((np.clip(roles, 0, 1) * 255).round().astype(np.uint8).tobytes())
    f.write(tri.astype(np.uint32).tobytes())
np.stack(pos).astype(np.float32).tofile(os.path.join(out, "pos.bin"))
np.stack(nrm).astype(np.float32).tofile(os.path.join(out, "nrm.bin"))
p = np.stack(pos)
json.dump({"verts": nv, "tris": len(tri) // 3, "rows": len(pos), "clips": clips,
           "min": p.reshape(-1, 3).min(0).tolist(), "max": p.reshape(-1, 3).max(0).tolist()},
          open(os.path.join(out, "meta.json"), "w"), indent=1)
print("BAKE done verts %d tris %d rows %d total %.1fs" % (nv, len(tri) // 3, len(pos), time.time() - t0))
