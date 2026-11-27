"""The two-trainer help-off (knee/ankle): the hurt man hops on his good leg, an arm over each
trainer's shoulders; each trainer has an arm round his back and holds his wrist with the other.
Built on our rig from injured_walk (his base) and crew_walk (theirs), arms placed by IK, baked to
three actions of one shared cycle: helped_off (him), helped_off_l / helped_off_r (the trainer on
his left / right). All three in place, facing -Y; in game they share one transform.

  python bake_helped_off.py -- BASE.blend CREW_CLIPS.glb OUT.blend [N GAP AHEAD K]

BASE.blend: retarget_mixamo.py's file holding injured_walk (Mixamo "Injured Walk", hurt leg the
left); CREW_CLIPS.glb: assets/oval3d/crew_clips.glb (crew_walk). Then bake_injury_glb.py takes
OUT.blend's three actions into injury_clips.glb. Defaults are the shipped ones: a 40-frame cycle
(0.66 m/s at rate 1), trainers 0.5 m to either side and 0.24 m ahead, their strides 0.75 of the
crew walk's (their feet then keep pace with his: printed per run as STANCE dy/frame vs PACE).
"""
import sys, math
import bpy
from mathutils import Matrix, Vector, Quaternion

argv = sys.argv[sys.argv.index("--") + 1:]
base_blend, crew_glb, out = argv[0], argv[1], argv[2]
N = int(argv[3]) if len(argv) > 3 else 40          # frames in the trio's cycle (30 fps)
GAP = float(argv[4]) if len(argv) > 4 else 0.50     # m, his centre to each trainer's
AHEAD = float(argv[5]) if len(argv) > 5 else 0.24   # m the trainers walk ahead of him
LEAN = math.radians(8)

bpy.ops.wm.open_mainfile(filepath=base_blend)
sc = bpy.context.scene
sc.render.fps = 30
H = next(o for o in bpy.data.objects if o.type == "ARMATURE")
for o in list(bpy.data.objects):
    if o.type == "MESH" and o.parent != H:
        bpy.data.objects.remove(o, do_unlink=True)
H.animation_data.action = None
for tr in list(H.animation_data.nla_tracks):
    H.animation_data.nla_tracks.remove(tr)
bpy.ops.import_scene.gltf(filepath=crew_glb)
for o in list(bpy.data.objects):
    if o != H and o.parent != H:
        bpy.data.objects.remove(o, do_unlink=True)
walk_h = bpy.data.actions["injured_walk"]
walk_t = bpy.data.actions["crew_walk"]


def curves(act):
    cb = act.layers[0].strips[0].channelbag(act.slots[0])
    out = {}
    for fc in cb.fcurves:
        if not fc.data_path.startswith('pose.bones["'):
            continue
        bone = fc.data_path.split('"')[1]
        prop = fc.data_path.rsplit(".", 1)[1]
        out.setdefault(bone, {}).setdefault(prop, {})[fc.array_index] = fc
    return out


CH, CT = curves(walk_h), curves(walk_t)
LH, LT = walk_h.frame_range, walk_t.frame_range


def sample(cv, bone, t):
    d = cv.get(bone, {})
    q = d.get("rotation_quaternion")
    rot = Quaternion([q[i].evaluate(t) for i in range(4)]) if q and len(q) == 4 else Quaternion()
    l = d.get("location")
    loc = Vector([l[i].evaluate(t) if i in l else 0.0 for i in range(3)]) if l else Vector()
    return rot.normalized(), loc


def dup(name, x, y):
    r = H.copy(); r.data = H.data.copy(); r.name = name
    sc.collection.objects.link(r)
    for ch in H.children:
        m = ch.copy(); m.parent = r; sc.collection.objects.link(m)
        for md in m.modifiers:
            if md.type == "ARMATURE":
                md.object = r
    r.location = (x, y, 0)
    return r


TL = dup("TL", GAP, -AHEAD)     # on his left (+X)
TR = dup("TR", -GAP, -AHEAD)
for r in (H, TL, TR):
    r.animation_data_create(); r.animation_data.action = None
    for pb in r.pose.bones:
        pb.rotation_mode = "QUATERNION"

# The trainers' legs: shorter steps than the crew walk (they shuffle at his pace). Mean pose per bone.
LEG = [b + s for b in ("thigh_", "calf_", "foot_", "ball_") for s in ("l", "r")]
K = float(argv[6]) if len(argv) > 6 else 0.75
mean = {}
for b in LEG:
    acc = Vector((0, 0, 0, 0)); ref = None
    for i in range(int(LT[0]), int(LT[1])):
        q, _ = sample(CT, b, i)
        if ref is None: ref = q
        if q.dot(ref) < 0: q = -q
        acc += Vector((q.w, q.x, q.y, q.z))
    mean[b] = Quaternion((acc[0], acc[1], acc[2], acc[3])).normalized()  # (Vector.normalize ignores a 4D w)

# Drift of his walk (removed so he walks on the spot).
_, p0 = sample(CH, "pelvis", LH[0]); _, p1 = sample(CH, "pelvis", LH[1])
DRIFT = p1 - p0


def empty(name, parent, bone, off, at=None, off2=None):
    e = bpy.data.objects.new(name, None); sc.collection.objects.link(e)
    e.parent = parent; e.parent_type = "BONE"; e.parent_bone = bone
    pb = parent.pose.bones[at or bone]
    if off2 is not None: off = off2
    # bone-parented empties sit at the bone's tail; off is in armature space from the bone head
    e.matrix_world = parent.matrix_world @ Matrix.Translation(pb.head + Vector(off))
    return e


def ik(rig, bone, target, pole, pole_angle=0.0, chain=2):
    c = rig.pose.bones[bone].constraints.new("IK")
    c.target = target; c.chain_count = chain
    if pole is not None:
        c.pole_target = pole; c.pole_angle = pole_angle
    return c




def set_pose(t):
    """Base poses at trio phase t in [0,1)."""
    th = LH[0] + t * (LH[1] - LH[0]); tt = LT[0] + t * (LT[1] - LT[0])
    for pb in H.pose.bones:
        q, l = sample(CH, pb.name, th)
        if pb.name == "pelvis":
            l = l - DRIFT * t
        pb.rotation_quaternion = q; pb.location = l
    for r in (TL, TR):
        for pb in r.pose.bones:
            q, l = sample(CT, pb.name, tt)
            if pb.name in mean:
                m = mean[pb.name]
                if q.dot(m) < 0: q = -q
                q = m.slerp(q, K)
            pb.rotation_quaternion = q; pb.location = l


set_pose(0.0)
bpy.context.view_layer.update()
# Targets (placed at phase 0, then ride their bones).
# His hurt left leg held up behind him, knee bent.
leg_t = empty("leg_t", H, "pelvis", (0.13, 0.22, -0.52))
leg_p = empty("leg_p", H, "pelvis", (0.15, -0.8, -0.3))
ik(H, "calf_l", leg_t, leg_p, math.radians(-90))
# His arms over their shoulders: the upper arm reaches up over the trainer's near shoulder to
# behind his neck, the forearm drapes across his upper back to the front of his far shoulder.
def track(rig, bone, target):
    c = rig.pose.bones[bone].constraints.new("DAMPED_TRACK")
    c.target = target; c.track_axis = "TRACK_Y"
    return c


el = empty("el", TL, "neck_01", None, "neck_01", (-0.02, 0.15, 0.08))
er = empty("er", TR, "neck_01", None, "neck_01", (0.02, 0.15, 0.08))
hl = empty("hl", TL, "clavicle_l", None, "upperarm_l", (0.0, -0.10, 0.04))
hr = empty("hr", TR, "clavicle_r", None, "upperarm_r", (0.0, -0.10, 0.04))
track(H, "upperarm_l", el); track(H, "lowerarm_l", hl)
track(H, "upperarm_r", er); track(H, "lowerarm_r", hr)
# Each trainer's inner arm round his back, hand on his far side's belt.
bl = empty("bl", H, "spine_03", (-0.08, 0.15, 0.04))
br = empty("br", H, "spine_03", (0.08, 0.15, 0.04))
blp = empty("blp", TL, "spine_03", (-0.2, 0.8, -0.2))
brp = empty("brp", TR, "spine_03", (0.2, 0.8, -0.2))
ik(TL, "lowerarm_r", bl, blp, math.radians(-90), 2)
ik(TR, "lowerarm_l", br, brp, math.radians(-90), 2)
# Their outer hand holds his wrist.
wl = empty("wl", H, "hand_l", (0.0, -0.04, -0.06))
wr = empty("wr", H, "hand_r", (0.0, -0.04, -0.06))
wlp = empty("wlp", TL, "spine_03", (0.6, -0.1, -0.6))
wrp = empty("wrp", TR, "spine_03", (-0.6, -0.1, -0.6))
ik(TL, "lowerarm_l", wl, wlp, math.radians(-90), 2)
ik(TR, "lowerarm_r", wr, wrp, math.radians(-90), 2)


def lean(r, bone, ang, axis="X"):
    pb = r.pose.bones[bone]
    h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(ang, 4, axis) @ Matrix.Translation(-h) @ pb.matrix


def ground(r):
    P = r.pose.bones
    lo = min(min(P["foot_" + s].head.z - r.data.bones["foot_" + s].head_local.z,
                 P["ball_" + s].head.z - r.data.bones["ball_" + s].head_local.z) for s in "lr")
    return lo


BAKE = {r.name: [] for r in (H, TL, TR)}
STAT = []
for f in range(N):
    t = f / N
    set_pose(t)
    bpy.context.view_layer.update()
    # He leans forward onto them (the spine), head down a touch.
    lean(H, "spine_01", -LEAN * 0.5); bpy.context.view_layer.update()
    lean(H, "spine_02", -LEAN * 0.5); bpy.context.view_layer.update()
    for r in (TL, TR):
        g = ground(r)
        pb = r.pose.bones["pelvis"]
        m = pb.matrix.copy(); m.translation.z -= g; pb.matrix = m
    bpy.context.view_layer.update()
    for r in (H, TL, TR):
        mats = {}
        for pb in r.pose.bones:
            mats[pb.name] = r.convert_space(pose_bone=pb, matrix=pb.matrix, from_space="POSE", to_space="LOCAL")
        BAKE[r.name].append(mats)
    P = H.pose.bones
    STAT.append((f, [round(x, 3) for x in (H.matrix_world @ P["hand_l"].head)],
                 [round(x, 3) for x in (TL.matrix_world @ TL.pose.bones["upperarm_l"].head)],
                 round((TL.matrix_world @ TL.pose.bones["foot_l"].head).y, 3),
                 round((TL.matrix_world @ TL.pose.bones["foot_l"].head).z, 3),
                 round((H.matrix_world @ P["foot_r"].head).y, 3), round((H.matrix_world @ P["foot_r"].head).z, 3)))
for s in STAT[::4]:
    print("ST", s)
# Foot slide: trainer L left ankle while near the turf, y step per frame vs the trio's pace.
pace = DRIFT.length / N
print("PACE m/frame", round(pace, 4), "m/s", round(pace * 30, 3))
ys = [(s[3], s[4]) for s in STAT]
st = [ys[i + 1][0] - ys[i][0] for i in range(N - 1) if ys[i][1] < 0.115 and ys[i + 1][1] < 0.115]
print("TRAINER STANCE dy/frame", [round(x, 4) for x in st])
hs = [(s[5], s[6]) for s in STAT]
st = [hs[i + 1][0] - hs[i][0] for i in range(N - 1) if hs[i][1] < 0.115 and hs[i + 1][1] < 0.115]
print("HIM STANCE dy/frame", [round(x, 4) for x in st])

# Strip constraints and empties; write the baked actions.
for r in (H, TL, TR):
    for pb in r.pose.bones:
        for c in list(pb.constraints):
            pb.constraints.remove(c)
for o in list(bpy.data.objects):
    if o.type == "EMPTY":
        bpy.data.objects.remove(o, do_unlink=True)
names = {"H": "helped_off", "TL": "helped_off_l", "TR": "helped_off_r"}
for r in (H, TL, TR):
    key = r.name if r != H else "H"
    a = bpy.data.actions.new(names[key]); a.use_fake_user = True
    r.animation_data.action = a
    for f, mats in enumerate(BAKE[r.name]):
        for pb in r.pose.bones:
            m = mats[pb.name]
            pb.rotation_quaternion = m.to_quaternion(); pb.location = m.translation
            pb.keyframe_insert("rotation_quaternion", frame=f + 1)
            pb.keyframe_insert("location", frame=f + 1)
    # close the loop: frame N+1 = frame 1
    for pb in r.pose.bones:
        m = BAKE[r.name][0][pb.name]
        pb.rotation_quaternion = m.to_quaternion(); pb.location = m.translation
        pb.keyframe_insert("rotation_quaternion", frame=N + 1)
        pb.keyframe_insert("location", frame=N + 1)
H.name = "average.rig.001"
bpy.ops.wm.save_as_mainfile(filepath=out)
print("SAVED", out)
