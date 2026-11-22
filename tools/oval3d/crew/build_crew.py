"""The match-day crew's clothes and kit for the 3D oval, built on the footballer's own body.

python -I build_crew.py BODY.glb OUT.glb          (pip bpy 5.x; or blender -b -P build_crew.py -- BODY OUT)

BODY is the footballer the match draws (assets/oval3d/player_mh.glb or player_average.glb). Every
garment is cut from that body's own surface, smoothed, pushed out to sit off it and given a
cloth thickness, and keeps the body's bone weights, so it moves with him exactly and never sinks
into him. Oval3D puts the garments on the umpire's, trainer's or runner's own skeleton
(Oval3D._crew_dress) and colours them (Oval3D.CREW_KITS). The real 2026 kits (AFL photos,
Regulations 12.17; tools/oval3d/crew/README.md):

  crew_shirt     umpire's short-sleeved shirt: sleeves to mid upper arm, worn out over the shorts
                 (field and boundary) or tucked into the trousers (goal); the runner's pink top
  crew_trousers  goal umpire's long straight trousers, hem on the boot
  crew_belt      goal umpire's black belt over the trousers' waist, with its buckle
  crew_cap       goal umpire's cap: crown fitted to the skull, curved peak
  crew_vest      trainer's AFL vest: a bib over his shirt, open at the sides
  crew_flag      goal umpire's flag: stick and cloth (not skinned; held in the hand)
  crew_bottle    trainer's drink bottle (not skinned; held in the hand)
"""
import math, os, sys
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[-2:]
SRC, OUT = argv[0], argv[1]

SLEEVE = 0.52        # the sleeve's hem, as a fraction of the upper arm from the shoulder joint
SHIRT_OFF = 0.009    # m: the shirt off the body
SLEEVE_FLARE = 0.012 # m: extra at the sleeve's hem (a short sleeve stands off the arm)
TROUSER_OFF = 0.016  # m: trousers at the hip, over the tucked shirt
VEST_OFF = 0.007     # m: the vest over the shirt
CLOTH = 0.0035       # m: cloth thickness
WELD = 0.003         # m: body vertices this close are one point of the cloth (the body splits at its regions)

bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC, bone_heuristic="BLENDER")
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
body = [o for o in bpy.data.objects if o.type == "MESH" and o.vertex_groups][0]
for o in list(bpy.data.objects):
    if o not in (arm, body):
        bpy.data.objects.remove(o)
mats = [m.name for m in body.data.materials]
MAT = {n: i for i, n in enumerate(mats)}
bones = arm.data.bones
groups = {g.index: g.name for g in body.vertex_groups}


def dominant(v):
    best, w = "", 0.0
    for g in v.groups:
        if g.weight > w:
            best, w = groups[g.group], g.weight
    return best


def along(bone, co):
    b = bones[bone]
    d = b.tail_local - b.head_local
    return (co - b.head_local).dot(d) / d.length_squared


def radial(bone, co):
    """co's offset from the bone's line, and the point on the line."""
    b = bones[bone]
    d = (b.tail_local - b.head_local).normalized()
    p = b.head_local + d * (co - b.head_local).dot(d)
    return co - p, p


me = body.data
dom = [dominant(v) for v in me.vertices]
EYE_FRAC = 0.5
gz = [me.vertices[v].co.z for p in me.polygons if p.material_index == MAT["ARD_guernsey"] for v in p.vertices]
neck_z = max(gz)
print("guernsey z", min(gz), neck_z)
eyes = [me.vertices[v].co for p in me.polygons if mats[p.material_index] == "ARD_eye" for v in p.vertices]
_hb = bones["head"].head_local
_hz = [v.co.z for v in me.vertices if dom[v.index] == "head"]
# Eye level when the body has no eyes of its own (the older average body): the eyes sit near
# the middle of the head's height, the brow ridge in front of them.
_eye_guess = min(_hz) + (max(_hz) - min(_hz)) * EYE_FRAC
if eyes:
    eye_z = sum(c.z for c in eyes) / len(eyes)
    eye_y = min(c.y for c in eyes)
else:
    eye_z = _eye_guess
    eye_y = min(v.co.y for v in me.vertices if dom[v.index] == "head" and abs(v.co.z - eye_z) < 0.01
                and abs(v.co.x) > 0.02) + 0.005
print("eye", eye_z, eye_y, "guess", _eye_guess)


def cut(name, keep):
    """A copy of the body holding only the faces keep(poly) passes, with its weights, UVs, colours."""
    ob = body.copy()
    ob.data = body.data.copy()
    ob.name = ob.data.name = name
    bpy.context.collection.objects.link(ob)
    if ob.data.shape_keys:
        ob.shape_key_clear()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    drop = [f for f in bm.faces if not keep(me.polygons[f.index])]
    bmesh.ops.delete(bm, geom=drop, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    # The body is split where one region meets the next (guernsey and skin, shorts and sock):
    # one piece of cloth is joined there, or smoothing would open a gap along every seam.
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=WELD)
    bm.to_mesh(ob.data)
    bm.free()
    for m in ob.modifiers:
        ob.modifiers.remove(m)
    # The body's own split normals and sharp edges belong to its surface, not the cloth's: kept,
    # they would print the body's seams (the knee, the armhole) as creases in the cloth.
    for name in ("custom_normal", "sharp_edge", "sharp_face"):
        if name in ob.data.attributes:
            ob.data.attributes.remove(ob.data.attributes[name])
    return ob


def weld(ob, dist=WELD):
    """Join points that lie together (rows added at a hem meet where they began) and drop
    slivers, so the cloth shades as one surface."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bm.to_mesh(ob.data)
    bm.free()


def apply_mods(ob):
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def smooth(ob, iters, factor=0.6, pin=None, only=None):
    """Laplacian smoothing. An open edge (a hem, the neck, an armhole) is smoothed only along
    itself, so it keeps its line but loses any saw-tooth; pin(co) holds a vertex."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    _smooth_bm(bm, iters, factor, pin, only)
    bm.to_mesh(ob.data)
    bm.free()


def _smooth_bm(bm, iters, factor, pin=None, only=None):
    bm.verts.ensure_lookup_table()
    for _ in range(iters):
        new = {}
        for v in bm.verts:
            if not v.link_edges or (pin and pin(v.co)) or (only and not only(v.co)):
                continue
            if v.is_boundary:
                ns = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
                if len(ns) != 2:
                    continue
            else:
                ns = [e.other_vert(v) for e in v.link_edges]
            avg = sum((u.co for u in ns), Vector()) / len(ns)
            new[v.index] = v.co.lerp(avg, factor)
        for i, co in new.items():
            bm.verts[i].co = co


_tree = None


def body_tree():
    global _tree
    if _tree is None:
        bm = bmesh.new()
        bm.from_mesh(me)
        _tree = BVHTree.FromBMesh(bm)
        bm.free()
    return _tree


def smooth_out(ob, iters, off, extra=None, skip=None, tree=None):
    """Cloth over the body: relaxed (it does not follow every muscle) and held at least `off`
    outside the body, plus extra(co) more (a sleeve's flare), in turns, so it bridges hollows
    and drapes over what stands out instead of being pushed point by point into a saw-tooth.
    Nothing of the body may be outside the cloth, including parts that stand off it (the
    guernsey's hem): each turn also looks outward along the cloth's normal for the body.
    tree: what the cloth lies over, when it is not the body (the vest over the shirt)."""
    tree = tree or body_tree()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()

    def hold():
        bm.normal_update()
        for v in bm.verts:
            if skip and skip(v.co):
                continue
            want = off + (extra(v.co) if extra else 0.0)
            hit, n, _, _ = tree.find_nearest(v.co)
            if hit is not None and (v.co - hit).dot(n) < want:
                v.co = hit + n * want
            vn = v.normal
            if vn.length > 0.5:
                hit, _, _, _ = tree.ray_cast(v.co - vn * 0.002, vn, 0.06)
                if hit is not None:
                    v.co = hit + vn * want
    hold()
    for _ in range(iters * 4):
        _smooth_bm(bm, 1, 0.5)
        hold()
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def trim(ob, co, no, near=None):
    """Cut the garment along the plane through co with normal no and drop what lies on the no
    side, so a hem is a clean line rather than the body's stepped region edge. near(co) limits
    the cut to part of the garment (one sleeve)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    geom = [f for f in bm.faces if near is None or near(f.calc_center_median())]
    gv = {v for f in geom for v in f.verts}
    ge = {e for f in geom for e in f.edges}
    bmesh.ops.bisect_plane(bm, geom=list(gv) + list(ge) + geom, plane_co=co, plane_no=no, dist=1e-5)
    drop = [f for f in bm.faces if (near is None or near(f.calc_center_median()))
            and (f.calc_center_median() - co).dot(no) > 0.0]
    bmesh.ops.delete(bm, geom=drop, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()


def snap_neck(ob, r_front, r_side, z_front, z_back):
    """The neck opening's edge set on a smooth oval round the neck (a crew neck), rising from
    z_front at the throat to z_back at the nape."""
    nb = bones["neck_01"].head_local
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for v in bm.verts:
        if not v.is_boundary or v.co.z < z_front - 0.06:
            continue
        d = Vector((v.co.x - nb.x, v.co.y - nb.y))
        if d.length > 0.16:
            continue
        a = math.atan2(d.x, -d.y)
        back = (1 - math.cos(a)) / 2
        r = 1.0 / math.sqrt((math.sin(a) / r_side) ** 2 + (math.cos(a) / r_front) ** 2)
        v.co.x, v.co.y = nb.x + math.sin(a) * r, nb.y - math.cos(a) * r
        v.co.z = z_front + (z_back - z_front) * back
    bm.to_mesh(ob.data)
    bm.free()


def thicken(ob, t=CLOTH):
    s = ob.modifiers.new("cloth", "SOLIDIFY")
    s.thickness, s.offset, s.use_rim, s.use_even_offset = t, -1.0, True, False
    apply_mods(ob)


def paint(ob, rgba, uv=None):
    """The kit shader's region colour (Color: r guernsey, g shorts) on every corner; uv pins the
    guernsey coordinate (the number and design read it) for faces cut from bare skin."""
    col = ob.data.color_attributes["Color"]
    for c in col.data:
        c.color = rgba
    if uv is not None:
        for layer, val in uv.items():
            for d in ob.data.uv_layers[layer].data:
                d.uv = val


def is_mat(p, n):
    return mats[p.material_index] == n


# The shirt: the guernsey, plus the skin it covers that a guernsey leaves bare: the shoulders and
# the upper arms to the sleeve's hem, never the neck (a crew neck, like the guernsey's).
SHIRT_DROP = 0.07    # m: the shirt hangs this far below where the guernsey ends, over the shorts


def shirt_face(p):
    if is_mat(p, "ARD_guernsey"):
        return True
    if not is_mat(p, "ARD_skin"):
        return False
    for vi in p.vertices:
        v = me.vertices[vi]
        d = dom[vi]
        if d in ("upperarm_l", "upperarm_r"):
            if along(d, v.co) > SLEEVE + 0.15:
                return False
        elif d in ("clavicle_l", "clavicle_r", "spine_03", "spine_02"):
            if v.co.z > neck_z - 0.005 or abs(v.co.x) < 0.075 and v.co.z > neck_z - 0.06:
                return False
        else:
            return False
    return True


def sleeve_extra(co):
    best = 0.0
    for side in ("l", "r"):
        t = along("upperarm_" + side, co)
        r, _ = radial("upperarm_" + side, co)
        if 0.0 < t <= SLEEVE + 0.05 and r.length < 0.09:
            best = max(best, SLEEVE_FLARE * min(1.0, t / SLEEVE) ** 2)
    return best


def extend_hem(ob, drop, off, steps=4):
    """Carry the garment's bottom hem `drop` further down, in `steps` rows, each row sat on the
    body `off` outside it (the new rows take the hem's bone weights)."""
    tree = body_tree()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    hem_top = min(v.co.z for v in bm.verts) + 0.06
    # The bottom hem: open edges below the chest, away from the sleeves.
    def low(v):
        if v.co.z > neck_z - 0.3:
            return False
        for side in ("l", "r"):
            r, _ = radial("upperarm_" + side, v.co)
            if along("upperarm_" + side, v.co) > 0.0 and r.length < 0.08:
                return False
        return True
    edges = [e for e in bm.edges if e.is_boundary and all(low(v) for v in e.verts)]
    for _ in range(steps):
        ret = bmesh.ops.extrude_edge_only(bm, edges=edges)
        verts = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)]
        for v in verts:
            v.co.z -= drop / steps
            hit, n, _, _ = tree.find_nearest(v.co)
            if hit is not None:
                z = v.co.z
                v.co = hit + n * off
                v.co.z = z   # rows stay level, so the hem is a clean line of even quads
        edges = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMEdge) and g.is_boundary
                 and all(v in verts for v in g.verts)]
    bm.to_mesh(ob.data)
    bm.free()


shirt = cut("crew_shirt", shirt_face)
for side in ("l", "r"):
    ub = bones["upperarm_" + side]
    d = (ub.tail_local - ub.head_local)
    trim(shirt, ub.head_local + d * SLEEVE, d.normalized(),
         lambda c, ub=ub: (c - ub.head_local).dot(ub.tail_local - ub.head_local) > 0.0 and abs(c.x) > 0.17)
# The guernsey's own bottom edge is stepped; cut it level a little above, then add the shirt's
# length below in level rows.
HEM_Z = min(gz) - SHIRT_DROP
_top = min(gz) + 0.03
trim(shirt, Vector((0.0, 0.0, _top)), Vector((0.0, 0.0, -1.0)))
weld(shirt)
extend_hem(shirt, _top - HEM_Z, SHIRT_OFF, steps=6)
neck = [me.vertices[v].co for p in me.polygons if is_mat(p, "ARD_guernsey") for v in p.vertices
        if me.vertices[v].co.z > neck_z - 0.05 and abs(me.vertices[v].co.x) < 0.09]
snap_neck(shirt, 0.072, 0.078, neck_z - 0.045, neck_z - 0.005)
smooth_out(shirt, 10, SHIRT_OFF, sleeve_extra)
paint(shirt, (1.0, 0.0, 0.0, 0.0))

# The vest (the trainer's AFL bib): the shirt's shape a little further out, with no sleeves,
# big round armholes leaving 5 cm shoulder straps, a lower round neck, and a hem at the hip.
# Its sides are closed, as the bib is. It carries the guernsey's coordinates, so the kit shader
# draws the trainer's number on its back.
vest = shirt.copy()
vest.data = shirt.data.copy()
vest.name = vest.data.name = "crew_vest"
bpy.context.collection.objects.link(vest)


def armholes(ob):
    """The guernsey's own armholes: drop every face the shirt took from the arms' skin (its
    sleeves), keeping what came from the guernsey. The stepped edge left is smoothed along
    itself when the vest is laid over the shirt."""
    gi = [k for k, m in enumerate(ob.data.materials) if m and m.name.startswith("ARD_guernsey")]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index not in gi], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()


armholes(vest)
trim(vest, Vector((0.0, 0.0, HEM_Z + 0.05)), Vector((0.0, 0.0, -1.0)))
def scoop(ob, r_front, r_side, z_front, z_back):
    """Cut the neck opening down to a new line before snapping its edge onto it: drop every
    face near the neck that lies above the line at its angle round the neck."""
    nb = bones["neck_01"].head_local
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    drop = []
    for f in bm.faces:
        c = f.calc_center_median()
        d = Vector((c.x - nb.x, c.y - nb.y))
        if d.length > 0.16 or c.z < z_front - 0.03:
            continue
        a = math.atan2(d.x, -d.y)
        back = (1 - math.cos(a)) / 2
        r = 1.0 / math.sqrt((math.sin(a) / r_side) ** 2 + (math.cos(a) / r_front) ** 2)
        if c.z > z_front + (z_back - z_front) * back or d.length < r:
            drop.append(f)
    bmesh.ops.delete(bm, geom=drop, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()
    snap_neck(ob, r_front, r_side, z_front, z_back)


scoop(vest, 0.085, 0.082, neck_z - 0.075, neck_z - 0.02)
# Over the shirt, never through it: laid on the shirt's own surface as the shirt is on the body.
_sb = bmesh.new()
_sb.from_mesh(shirt.data)
smooth_out(vest, 6, VEST_OFF, tree=BVHTree.FromBMesh(_sb))
_sb.free()
paint(vest, (1.0, 0.0, 0.0, 0.0))


def soften_weights(ob, iters=10, bones_near=("clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r")):
    """Spread the bone weights round the shoulders and armpits over the cloth (each point toward
    its neighbours' mix): the cloth there stands off the body and bridges the armpit, and with
    the skin's own sharp weights a raised arm pulled a flap out of it. Only points that some
    shoulder bone moves are touched; the torso and the sleeve's hem keep theirs."""
    me_ = ob.data
    names = [g.name for g in ob.vertex_groups]
    W = [dict((names[g.group], g.weight) for g in v.groups if g.weight > 0.0) for v in me_.vertices]
    nb = [[] for _ in me_.vertices]
    for e in me_.edges:
        a, b = e.vertices
        nb[a].append(b)
        nb[b].append(a)
    live = [any(k in w for k in bones_near) for w in W]
    for _ in range(iters):
        out = []
        for i, w in enumerate(W):
            if not live[i] or not nb[i]:
                out.append(w)
                continue
            acc = {}
            for j in nb[i]:
                for k, x in W[j].items():
                    acc[k] = acc.get(k, 0.0) + x / len(nb[i])
            mix = {k: 0.5 * w.get(k, 0.0) + 0.5 * acc.get(k, 0.0) for k in set(w) | set(acc)}
            top = sorted(mix.items(), key=lambda kv: -kv[1])[:4]
            tot = sum(x for _, x in top) or 1.0
            out.append({k: x / tot for k, x in top})
        W = out
    for g in ob.vertex_groups:
        g.remove(range(len(me_.vertices)))
    for i, w in enumerate(W):
        for k, x in w.items():
            ob.vertex_groups[k].add([i], x, "REPLACE")


soften_weights(shirt)
soften_weights(vest)
thicken(vest, 0.003)
thicken(shirt)

# The trousers' reach: from the shorts' waistband down to the top of the boot.
shorts_top = max(me.vertices[v].co.z for p in me.polygons if is_mat(p, "ARD_shorts") for v in p.vertices)
boot_top = max(me.vertices[v].co.z for p in me.polygons if mats[p.material_index].startswith("ARD_boot")
               for v in p.vertices)
shorts_bottom = min(me.vertices[v].co.z for p in me.polygons if is_mat(p, "ARD_shorts") for v in p.vertices
                    if abs(me.vertices[v].co.x) > 0.06)
# The shorts' legs flare out from the thigh over their lowest few centimetres.
SHORTS_FLARE = {v for p in me.polygons if is_mat(p, "ARD_shorts") for v in p.vertices
                if me.vertices[v].co.z < shorts_bottom + 0.07}


def _leg_line(side):
    """The middle of the body's leg (one side) as a straight line from the boot to the crotch:
    a least-squares fit through the centre of each 1 cm slice of thigh and calf. A straight line,
    because trousers hang straight; the slices' own centres wander (the knee, the inner thigh
    meeting the other leg near the crotch) and a cloth laid round them would wander too."""
    acc = {}
    for v in me.vertices:
        if dom[v.index] in ("thigh_" + side, "calf_" + side) and boot_top < v.co.z < mid_z - 0.05:
            k = int(v.co.z / 0.01)
            sx, sy, sz, n = acc.get(k, (0.0, 0.0, 0.0, 0))
            acc[k] = (sx + v.co.x, sy + v.co.y, sz + v.co.z, n + 1)
    pts = [(sx / n, sy / n, sz / n) for sx, sy, sz, n in acc.values()]
    mz = sum(p[2] for p in pts) / len(pts)
    var = sum((p[2] - mz) ** 2 for p in pts)
    fit = []
    for j in (0, 1):
        m = sum(p[j] for p in pts) / len(pts)
        slope = sum((p[2] - mz) * (p[j] - m) for p in pts) / var
        fit.append((m, slope))
    return mz, fit


mid_z = min(me.vertices[i].co.z for i in range(len(me.vertices))
            if abs(me.vertices[i].co.x) < 0.008 and 0.5 < me.vertices[i].co.z < 1.1)   # the crotch
_LINES = {"l": _leg_line("l"), "r": _leg_line("r")}


def leg_axis(co):
    """The middle of the leg on co's side, level with co."""
    mz, ((mx, sx), (my, sy)) = _LINES["l" if co.x > 0 else "r"]
    return Vector((mx + sx * (co.z - mz), my + sy * (co.z - mz), co.z))


# The trousers are made, not cut from the body: two tubes, one per leg, from the waistband to
# the hem. Each ring of a tube lies round the middle of the body's leg at that height
# (leg_axis), at the furthest the body reaches on that side for each angle (polar_profile) plus
# the cloth's offset; below the crotch the leg widens into a straight tube from the thigh's width
# to a 7 cm hem, so the cloth falls past the knee and calf instead of hugging them. A tube never
# crosses the midline: above the crotch the two meet flat there (the front and back seams), below
# it each leg hangs on its own. Every point takes the bone weights of the body under it, from its
# own side.
from mathutils.kdtree import KDTree
RING = 0.015         # m between rings
NA = 48              # points round a ring
HEM_R = 0.066        # m: the hem's radius (a straight leg about 41 cm round)
MID = 0.003          # m: each leg's cloth stops this far short of the midline
WAIST = shorts_top - 0.012
hem_front = boot_top - 0.015     # the hem rests on the boot, a little lower at the heel
hem_back = boot_top - 0.035
LOWER = ("pelvis", "spine_01", "spine_02", "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r")


def polar_profile(side, dz=0.02):
    """The body on one side (x of that sign), below the waist: for each height step and each of
    NA angles round the leg's middle, the furthest the body reaches; gaps filled, then smoothed
    round the ring and up and down so the cloth has no ripples. at(z, a): a in radians."""
    leg = 1.0 if side == "l" else -1.0
    zs = {}
    for v in me.vertices:
        co = v.co
        if dom[v.index] not in LOWER or co.x * leg < 0.0 or co.z > WAIST + 0.04 or co.z < hem_back - 0.04:
            continue
        if dom[v.index].startswith("foot_"):
            continue   # the boot is under the hem, not inside the leg
        if v.index in SHORTS_FLARE:
            continue   # the shorts' legs stand off the thigh; trousers sit on the thigh itself
        c = leg_axis(Vector((leg * 0.1, 0.0, co.z)))
        r = Vector((co.x - c.x, co.y - c.y))
        k = (int(round(co.z / dz)), int(round((math.atan2(r.x, -r.y) / (2 * math.pi) % 1.0) * NA)) % NA)
        zs[k] = max(zs.get(k, 0.0), r.length)
    z0, z1 = min(k[0] for k in zs), max(k[0] for k in zs)
    grid = [[zs.get((z, a)) for a in range(NA)] for z in range(z0, z1 + 1)]
    # Heights where a direction has nothing (under the shorts' flare): bridge straight from the
    # body above to the body below, as cloth would.
    for a in range(NA):
        col = [g[a] for g in grid]
        known = [i for i, r in enumerate(col) if r is not None]
        for i, r in enumerate(col):
            if r is None and known:
                lo = max((k for k in known if k < i), default=None)
                hi = min((k for k in known if k > i), default=None)
                if lo is None or hi is None:
                    continue
                t = (i - lo) / (hi - lo)
                grid[i][a] = col[lo] * (1 - t) + col[hi] * t
    for row in grid:
        while any(r is None for r in row) and any(r is not None for r in row):
            row[:] = [r if r is not None else next((row[(k + j) % NA] for j in (1, -1, 2, -2, 3, -3)
                                                    if row[(k + j) % NA] is not None), None)
                      for k, r in enumerate(row)]
    for i in range(len(grid)):
        if all(r is None for r in grid[i]):
            grid[i] = list(grid[i - 1])
    n = len(grid)
    # Cloth hangs: in each direction it runs straight from one high point of the body to the next
    # (the seat, the widest of the thigh) and never follows it into a hollow (above the knee, the
    # shin). That is the upper hull of radius against height, direction by direction.
    # The hem stands off the ankle as a round 7 cm opening; the hull then runs the leg straight
    # down to it from the thigh.
    for i in range(n):
        if (z0 + i) * dz < hem_back + 0.02:
            grid[i] = [max(r, HEM_R - TROUSER_OFF) for r in grid[i]]
    # Below the crotch only: above it the cloth follows the seat and hips (a hull from the seat
    # down would hang the whole leg as wide as the seat).
    top = max(i for i in range(n) if (z0 + i) * dz <= mid_z - 0.04)
    for a in range(NA):
        hull = []
        for i in range(top + 1):
            pt = (i, grid[i][a])
            while len(hull) >= 2:
                (x1, y1), (x2, y2) = hull[-2], hull[-1]
                if (x2 - x1) * (pt[1] - y1) - (y2 - y1) * (pt[0] - x1) >= 0.0:
                    hull.pop()
                else:
                    break
            hull.append(pt)
        for (x1, y1), (x2, y2) in zip(hull, hull[1:]):
            for i in range(x1, x2 + 1):
                grid[i][a] = y1 + (y2 - y1) * (i - x1) / (x2 - x1)
    grid = [[max(g[a - 1], g[a], g[(a + 1) % NA]) for a in range(NA)] for g in grid]
    for _ in range(10):
        grid = [[(grid[max(0, i - 1)][a] + 2 * grid[i][a] + grid[min(n - 1, i + 1)][a]) / 4
                 for a in range(NA)] for i in range(n)]
    for _ in range(4):
        grid = [[(g[a - 1] + 2 * g[a] + g[(a + 1) % NA]) / 4 for a in range(NA)] for g in grid]

    def at(z, a):
        f = min(max(z / dz - z0, 0.0), n - 1.0)
        i = int(f)
        j = min(i + 1, n - 1)
        fa = (a / (2 * math.pi) % 1.0) * NA
        k = int(fa) % NA
        k2 = (k + 1) % NA
        ta = fa - int(fa)
        lo = grid[i][k] * (1 - ta) + grid[i][k2] * ta
        hi = grid[j][k] * (1 - ta) + grid[j][k2] * ta
        return lo * (1 - (f - i)) + hi * (f - i)
    return at



def _midline(dz=0.02):
    """Where the two legs' cloth meets (the front and back seams) for each height above the
    crotch: across the body's front (|x| < 5 cm) and across its seat (|x| < 8 cm), so neither
    seam sinks into a hollow."""
    fr, bk = {}, {}
    for v in me.vertices:
        co = v.co
        if dom[v.index] in LOWER and abs(co.x) < 0.08 and mid_z - 0.03 < co.z < WAIST + 0.04:
            k = int(round(co.z / dz))
            if abs(co.x) < 0.05:
                fr[k] = min(fr.get(k, 9.0), co.y)
            # At the back the seam spans the seat from one buttock to the other, not down into
            # the cleft between them.
            bk[k] = max(bk.get(k, -9.0), co.y)
    ks = sorted(fr)
    for d in (fr, bk):
        for _ in range(6):
            d.update({k: (d.get(k - 1, d[k]) + 2 * d[k] + d.get(k + 1, d[k])) / 4 for k in ks})

    def at(z):
        k = min(max(int(round(z / dz)), ks[0]), ks[-1])
        return fr[k] - TROUSER_OFF, bk[k] + TROUSER_OFF
    return at


MIDLINE = _midline()
TAPER = 0.15         # cloth hangs: going down, a leg narrows at most this much (m per m)
N_OUT = 32           # points on a ring's outer side, front seam to back seam
N_IN = 16            # and on its inner side, back to front


def leg_tube(side):
    """One leg of the trousers, waist to hem. Each ring runs from the front seam round the outside
    of the leg to the back seam (N_OUT points), then back along the inside (N_IN). Above the
    crotch the seams sit on the body's midline front and back, shared with the other leg, and the
    inside lies flat on the midline (inside the body, meeting the other leg); below the crotch the
    inside eases onto the inner thigh."""
    leg = 1.0 if side == "l" else -1.0
    prof = polar_profile(side)
    if os.environ.get("CREW_DEBUG"):
        for zi in range(int(hem_back * 100), int(WAIST * 100) + 1, 3):
            z = zi / 100
            c = leg_axis(Vector((leg * 0.1, 0.0, z)))
            print("DBG", side, z, round(c.x, 3), round(c.y, 3),
                  [round(prof(z, math.radians(a)), 3) for a in (0, 90, 180, 270)])
    bm = bmesh.new()
    rings = []
    z = WAIST
    seam = None
    while True:
        last = z <= hem_front + 1e-6
        c = leg_axis(Vector((leg * 0.1, 0.0, z)))
        if z >= mid_z or seam is None:
            yf, yb = MIDLINE(max(z, mid_z))
            af = math.atan2(-c.x, -(yf - c.y)) % (2 * math.pi)   # angle of the front seam from c
            ab = math.atan2(-c.x, -(yb - c.y)) % (2 * math.pi)   # and of the back seam
            seam = (af, ab, yf, yb)
        af, ab, yf, yb = seam
        # Angles measured as in polar_profile: 0 = forward (-y), pi/2 = +x. The outside runs from
        # af to ab through the leg's own side (+x for the left leg).
        if leg > 0:
            span_out = (ab - af) % (2 * math.pi)
            outs = [af + span_out * i / N_OUT for i in range(N_OUT + 1)]
            span_in = 2 * math.pi - span_out
            ins = [ab + span_in * i / N_IN for i in range(1, N_IN)]
        else:
            span_out = (af - ab) % (2 * math.pi)
            outs = [af - span_out * i / N_OUT for i in range(N_OUT + 1)]
            span_in = 2 * math.pi - span_out
            ins = [ab - span_in * i / N_IN for i in range(1, N_IN)]
        above = max(0.0, min(1.0, (z - (mid_z - 0.04)) / 0.04))   # 1 on and above the crotch
        ring = []
        for i, a in enumerate(outs + ins):
            d = Vector((math.sin(a), -math.cos(a), 0.0))
            zz = z
            if last:
                zz = hem_front + (hem_back - hem_front) * max(0.0, min(1.0, d.y + 0.5))
            want = prof(zz, a) + TROUSER_OFF
            p = Vector((c.x, c.y, zz)) + d * want
            inner = i > N_OUT
            if above > 0.0 and (i == 0 or i == N_OUT):
                # The seams: on the midline, shared with the other leg.
                q = Vector((0.0, yf if i == 0 else yb, zz))
                p = p.lerp(q, above)
            elif above > 0.0 and inner:
                # Flat along the midline, from the back seam to the front.
                t = (i - N_OUT) / N_IN
                q = Vector((leg * MID, yb + (yf - yb) * t, zz))
                p = p.lerp(q, above)
            # Below the widest of the seat and thighs the cloth falls: it never draws in under a
            # bulge (the shorts' hem, a thigh muscle) faster than TAPER.
            if rings and not (above > 0.0 and (inner or i == 0 or i == N_OUT)):
                prev = rings[-1][i].co
                c3 = Vector((c.x, c.y, zz))
                least = (prev - c3).to_2d().dot(d.to_2d()) - TAPER * RING
                if (p - c3).to_2d().dot(d.to_2d()) < least:
                    p = c3 + d * least
            if p.x * leg < MID and not (above > 0.0 and (i == 0 or i == N_OUT)):
                p.x = MID * leg
            ring.append(bm.verts.new(p))
        rings.append(ring)
        if last:
            break
        z = max(hem_front, z - RING)
    nr = len(rings[0])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(nr):
            f = bm.faces.new((r0[k], r1[k], r1[(k + 1) % nr], r0[(k + 1) % nr]))
    bm.normal_update()
    # Faces outward: the left leg's outside runs one way round, the right's the other.
    if sum((f.normal.to_2d().dot(f.calc_center_median().to_2d() - leg_axis(f.calc_center_median()).to_2d()))
           for f in bm.faces) < 0.0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    m = bpy.data.meshes.new("leg_" + side)
    bm.to_mesh(m)
    bm.free()
    ob = bpy.data.objects.new("leg_" + side, m)
    bpy.context.collection.objects.link(ob)
    ids = [i for i in range(len(me.vertices)) if dom[i] in LOWER and me.vertices[i].co.x * leg > -0.005]
    t = KDTree(len(ids))
    for i in ids:
        t.insert(me.vertices[i].co, i)
    t.balance()
    for g in body.vertex_groups:
        ob.vertex_groups.new(name=g.name)
    for v in ob.data.vertices:
        _, j, _ = t.find(v.co)
        for g in me.vertices[j].groups:
            ob.vertex_groups[groups[g.group]].add([v.index], g.weight, "REPLACE")
    ob.data.color_attributes.new("Color", "BYTE_COLOR", "CORNER")
    # Each corner takes the coordinates of the body point under it (the kit shader reads the
    # second set for front and back), one value per point so the cloth is not split at every
    # corner as a fresh unwrap would split it.
    near = [t.find(v.co)[1] for v in ob.data.vertices]
    for layer in me.uv_layers:
        per = {}
        for lp, d in zip(me.loops, layer.data):
            per.setdefault(lp.vertex_index, d.uv.copy())
        out = ob.data.uv_layers.new(name=layer.name)
        for lp, d in zip(ob.data.loops, out.data):
            d.uv = per.get(near[lp.vertex_index], (0.0, 0.0))
    return ob


legs = [leg_tube("l"), leg_tube("r")]
bpy.ops.object.select_all(action="DESELECT")
for o in legs:
    o.select_set(True)
bpy.context.view_layer.objects.active = legs[0]
bpy.ops.object.join()
trousers = legs[0]
trousers.name = trousers.data.name = "crew_trousers"
# The two legs' seams are the same points: one piece of cloth.
_b = bmesh.new()
_b.from_mesh(trousers.data)
bmesh.ops.remove_doubles(_b, verts=_b.verts, dist=0.0005)
_b.to_mesh(trousers.data)
_b.free()
# The shirt is tucked in: round the waist the trousers lie over it, never under it.
_sb = bmesh.new()
_sb.from_mesh(shirt.data)
_st = BVHTree.FromBMesh(_sb)
_sb.free()
for v in trousers.data.vertices:
    if v.co.z > HEM_Z - 0.03:
        hit, n, _, _ = _st.find_nearest(v.co)
        # Against the shirt's sides only: near its hem the nearest point is the hem's rim, whose
        # normal points down, and following it would dent the trousers.
        if hit is not None and hit.z > HEM_Z + 0.015 and abs(n.z) < 0.5 and (v.co - hit).dot(n) < 0.004:
            v.co = hit + n * 0.004
paint(trousers, (0.0, 1.0, 0.0, 0.0))
thicken(trousers, 0.004)
tz = [v.co.z for v in trousers.data.vertices]
waist_z = max(tz)
print("trousers", min(tz), waist_z, len(trousers.data.vertices), len(trousers.data.polygons))

# The belt: a 3.5 cm band round the trousers just under their top, 4 mm proud of their outer
# surface (found by a ray in from outside at each of 64 angles, the radii then smoothed round
# the loop so it lies flat), with a 5 x 4 cm buckle at the front.
def belt():
    bm = bmesh.new()
    bm.from_mesh(trousers.data)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    top, depth, n = waist_z - 0.006, 0.035, 64
    c0 = bones["pelvis"].head_local
    rings = []
    for z in (top, top - depth):
        rs = []
        for k in range(n):
            a = 2 * math.pi * k / n
            d = Vector((math.sin(a), -math.cos(a), 0.0))
            o = Vector((c0.x, c0.y, z))
            hit = tree.ray_cast(o + d * 0.4, -d, 0.4)
            rs.append((hit[0] - o).length if hit[0] is not None else None)
        rings.append(rs)
    # One radius per angle, the larger of the two heights (a belt is a straight band), misses
    # filled from the neighbours, then smoothed round the loop.
    rs = [max([r for r in (rings[0][k], rings[1][k]) if r is not None], default=None) for k in range(n)]
    while any(r is None for r in rs):
        rs = [r if r is not None else next((rs[(k + j) % n] for j in (1, -1, 2, -2) if rs[(k + j) % n] is not None), None)
              for k, r in enumerate(rs)]
    for _ in range(2):
        rs = [max(rs[k], (rs[k - 1] + rs[k] + rs[(k + 1) % n]) / 3) for k in range(n)]
    rings = [[(c0.x + math.sin(2 * math.pi * k / n) * (rs[k] + 0.004),
               c0.y - math.cos(2 * math.pi * k / n) * (rs[k] + 0.004), z) for k in range(n)]
             for z in (top, top - depth)]
    out = max(max(Vector(p).to_2d().length for p in r) for r in rings)
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in r] for r in rings]
    for k in range(n):
        bm.faces.new((vs[0][k], vs[0][(k + 1) % n], vs[1][(k + 1) % n], vs[1][k]))
    m = bpy.data.meshes.new("crew_belt")
    bm.to_mesh(m)
    bm.free()
    ob = bpy.data.objects.new("crew_belt", m)
    bpy.context.collection.objects.link(ob)
    thicken(ob, 0.004)
    fy = min(p[1] for p in rings[0] + rings[1])
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(c0.x, fy - 0.004, top - depth / 2))
    bk = bpy.context.active_object
    bk.scale = (0.05, 0.008, 0.04)
    bk.name = "crew_buckle"
    bpy.ops.object.transform_apply(scale=True)
    return ob, bk


belt_ob, buckle = belt()
for ob in (belt_ob, buckle):
    vg = ob.vertex_groups.new(name="pelvis")
    vg.add(range(len(ob.data.vertices)), 1.0, "REPLACE")
    ob.data.color_attributes.new("Color", "BYTE_COLOR", "CORNER")

# The cap: a crown fitted to the skull a centimetre off it, its band level with the forehead
# about 3 cm above the eyes, and a curved peak.
head_b = bones["head"]
hv = [me.vertices[i].co for i in range(len(me.vertices)) if dom[i] in ("head",) and me.vertices[i].co.z > eye_z]
cx = sum(c.x for c in hv) / len(hv)
cy = sum(c.y for c in hv) / len(hv)
top_z = max(c.z for c in hv)
band_front = eye_z + 0.03
band_back = eye_z - 0.025
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=0.16)
bm.to_mesh(m := bpy.data.meshes.new("crew_cap"))
bm.free()
cap = bpy.data.objects.new("crew_cap", m)
bpy.context.collection.objects.link(cap)
cap.location = (cx, cy, top_z - 0.08)
bpy.ops.object.select_all(action="DESELECT")
cap.select_set(True)
bpy.context.view_layer.objects.active = cap
bpy.ops.object.transform_apply(location=True)
bm = bmesh.new()
bm.from_mesh(me)
tree = BVHTree.FromBMesh(bm)
bm.free()
ys = [c.y for c in hv]
y_front, y_back = min(ys), max(ys)


def band_z(y):
    f = (y - y_front) / max(1e-4, y_back - y_front)
    return band_front + (band_back - band_front) * f


cb = bmesh.new()
cb.from_mesh(cap.data)
bmesh.ops.delete(cb, geom=[v for v in cb.verts if v.co.z < band_z(v.co.y) - 0.02], context="VERTS")
for v in cb.verts:
    hit, n, _, _ = tree.find_nearest(v.co)
    if hit is not None:
        v.co = hit + n * 0.011
    if v.co.z < band_z(v.co.y):
        v.co.z = band_z(v.co.y)
cb.to_mesh(cap.data)
cb.free()
sm = cap.modifiers.new("s", "SMOOTH")
sm.factor, sm.iterations = 0.5, 4
apply_mods(cap)
thicken(cap, 0.003)
# The peak: from the crown's own band round the front (62 degrees either side of straight
# ahead), out 7.5 cm at the middle and nothing at its ends, tilting down a little as it goes out
# and curving down more at its sides, as a worn cap's bill does. Its inner edge is found on the
# crown (a ray in from outside at band height), so peak and crown meet with no gap.
_cb = bmesh.new()
_cb.from_mesh(cap.data)
_ct = BVHTree.FromBMesh(_cb)
_cb.free()
pk = bmesh.new()
rows, cols = 6, 30
grid = []
for j in range(cols + 1):
    u = -1.0 + 2.0 * j / cols
    a = u * math.radians(62.0)
    d = Vector((math.sin(a), -math.cos(a), 0.0))
    # The crown's lowest edge in this direction: the first height a ray in from outside meets it.
    hit = None
    zb = band_z(y_front) - 0.03
    while hit is None and zb < band_z(y_front) + 0.08:
        zb += 0.002
        hit = _ct.ray_cast(Vector((cx, cy, zb)) + d * 0.3, -d, 0.3)[0]
    p0 = hit if hit is not None else Vector((cx, cy, zb)) + d * 0.1
    reach = 0.075 * math.sqrt(max(0.0, 1.0 - u * u))
    if os.environ.get("CREW_DEBUG"):
        print("PEAK", round(u, 2), hit is not None, round((p0 - Vector((cx, cy, zb))).length, 3), round(reach, 3))
    col = []
    for i in range(rows + 1):
        t = i / rows
        q = p0 + d * reach * t
        q.z -= reach * t * math.tan(math.radians(12.0)) + 0.012 * u * u * t
        col.append(pk.verts.new(q))
    grid.append(col)
for j in range(cols):
    for i in range(rows):
        pk.faces.new((grid[j][i], grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1]))
bmesh.ops.remove_doubles(pk, verts=pk.verts, dist=1e-5)
pm = bpy.data.meshes.new("crew_peak")
pk.to_mesh(pm)
peak = bpy.data.objects.new("crew_peak", pm)
bpy.context.collection.objects.link(peak)
thicken(peak, 0.004)
bpy.ops.object.select_all(action="DESELECT")
for o in (cap, peak):
    o.select_set(True)
bpy.context.view_layer.objects.active = cap
bpy.ops.object.join()
cap.data.color_attributes.new("Color", "BYTE_COLOR", "CORNER")
paint(cap, (1.0, 0.0, 0.0, 0.0))   # the kit shader draws it in the kit's colour
vg = cap.vertex_groups.new(name="head")
vg.add(range(len(cap.data.vertices)), 1.0, "REPLACE")

# The body's shape keys (the MetaHuman's builds: short, tall, light, heavy, and the face
# shapes) carried onto every piece: each garment vertex moves as the body under it moves, so a
# heavy or tall build wears the same clothes. Oval3D sets the garments' blend shapes to the
# body's.
from mathutils.kdtree import KDTree
KEYS = []
if body.data.shape_keys:
    kb = body.data.shape_keys.key_blocks
    KEYS = [k.name for k in kb[1:]]
    kd = KDTree(len(me.vertices))
    for v in me.vertices:
        kd.insert(kb[0].data[v.index].co, v.index)
    kd.balance()


def carry_keys(ob, faces=False):
    """The body's build keys (short, tall, light, heavy) on a garment, each point moving as the
    body point under it does; the face keys only on what sits on the head (the cap)."""
    keys = [k for k in KEYS if faces or not k.startswith("face_")]
    if not keys:
        return
    kb = body.data.shape_keys.key_blocks
    near = [kd.find(v.co)[1] for v in ob.data.vertices]
    ob.shape_key_add(name="Basis")
    for name in keys:
        k = ob.shape_key_add(name=name, from_mix=False)
        base, dst = kb[0].data, kb[name].data
        for i, v in enumerate(ob.data.vertices):
            j = near[i]
            k.data[i].co = v.co + (dst[j].co - base[j].co)


# Skinned pieces ride the armature.
for ob in (shirt, trousers, vest, belt_ob, buckle, cap):
    carry_keys(ob, ob is cap)
    ob.parent = arm
    mod = ob.modifiers.new("arm", "ARMATURE")
    mod.object = arm
    ob.data.materials.clear()
    ob.data.materials.append(bpy.data.materials.new(ob.name))

# The flag: a 62 cm stick (2 cm thick) with its 54 x 42 cm sailcloth along the top 42 cm (the
# goal umpire's manual: flags "approx. 420 x 540 mm"). Origin at the grip, 8 cm up the stick;
# the stick runs up +Z, the cloth out along +X. The cloth's UV: u from the stick (0) to the fly
# (1), v up the stick: the flag shader flaps it by u.
def flag():
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.01, depth=0.62, location=(0, 0, 0.31 - 0.08))
    stick = bpy.context.active_object
    stick.name = "crew_flag_stick"
    cl = bmesh.new()
    nu, nv = 12, 8
    vs = [[cl.verts.new((0.012 + 0.54 * i / nu, 0.0, 0.62 - 0.08 - 0.42 + 0.42 * j / nv)) for j in range(nv + 1)]
          for i in range(nu + 1)]
    uvl = cl.loops.layers.uv.new("UVMap")
    for i in range(nu):
        for j in range(nv):
            f = cl.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
            for lp in f.loops:
                lp[uvl].uv = ((lp.vert.co.x - 0.012) / 0.54, (lp.vert.co.z - 0.12) / 0.42)
    cm = bpy.data.meshes.new("crew_flag_cloth")
    cl.to_mesh(cm)
    cloth = bpy.data.objects.new("crew_flag_cloth", cm)
    bpy.context.collection.objects.link(cloth)
    for o in (stick, cloth):
        o.data.materials.append(bpy.data.materials.new(o.name))
    return stick, cloth


flag()

# The drink bottle: a 750 ml squeeze bottle, 7.5 cm across and 24 cm tall to its cap, with a
# push-pull spout. Origin at its middle, up +Z.
def bottle():
    bm = bmesh.new()
    prof = [(0.0, -0.12), (0.034, -0.12), (0.0375, -0.115), (0.0375, 0.07), (0.033, 0.09), (0.03, 0.095),
            (0.03, 0.115), (0.014, 0.12), (0.012, 0.135), (0.006, 0.145), (0.0, 0.145)]
    n = 24
    rings = []
    for r, z in prof:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n), z))
                      for k in range(n)])
    for a, b in zip(rings, rings[1:]):
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    m = bpy.data.meshes.new("crew_bottle")
    bm.to_mesh(m)
    ob = bpy.data.objects.new("crew_bottle", m)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(bpy.data.materials.new("crew_bottle"))
    for p in ob.data.polygons:
        p.use_smooth = True


bottle()
bpy.data.objects.remove(body)
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.startswith("crew_"):
        for p in o.data.polygons:
            p.use_smooth = True
        # Every piece carries texture coordinates (the engine builds tangents from them); a
        # piece with no pattern of its own holds one value, so its points are not split.
        if not o.data.uv_layers:
            uv = o.data.uv_layers.new(name="UVMap")
            for d in uv.data:
                d.uv = (0.0, 0.0)
bpy.ops.export_scene.gltf(filepath=OUT, export_animations=True, export_skins=True, export_apply=False,
                          export_attributes=True, export_vertex_color="ACTIVE", export_all_vertex_colors=True)
print("WROTE", OUT)
