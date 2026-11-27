"""Mixamo clips onto the match footballer's rig (assets/oval3d/player_mh.glb), for the in-match
injury scenes (row 202 2e: the hurt man going down, lying hurt, getting up, limping off).

  python3.11 -c 'import bpy' environment (bpy 5.0.1):
  python retarget_mixamo.py OUT.blend NAME=SOURCE.fbx [NAME=SOURCE.fbx ...]

Mixamo's terms allow its motion in games; the downloaded FBX never goes in the repo, only the
motion baked onto our own rig (injury_clips.glb, made by bake_injury_glb.py from OUT.blend).

How the motion is moved across (rest-aligned, world-space):
- The two rigs stand differently at rest (Mixamo's T-pose, our A-pose) and face opposite ways.
  For every mapped bone, R = the turn that lays Mixamo's rest bone along ours. Our bone's world
  turn at a frame is D * R^-1 * T, where D is how far Mixamo's bone has turned from its rest and
  T our bone's rest: our bone points where theirs points, and twists as theirs twists.
- The hips' path is scaled by our pelvis height over theirs.
- Every frame is then stood on the turf: the body's lowest point (the skinned mesh, sampled) is put
  at height 0. Mixamo grounds its own character; ours has other proportions, so without this a
  man lying hurt sinks into the turf or hovers over it. Printed per clip: the shift's range.
"""
import math, os, sys
import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
RIG_GLB = os.path.join(HERE, "..", "..", "..", "assets", "oval3d", "player_mh.glb")
FPS = 30

MAP = {"Hips": "pelvis", "Spine": "spine_01", "Spine1": "spine_02", "Spine2": "spine_03",
       "Neck": "neck_01", "Head": "head"}
for s, t in (("Left", "l"), ("Right", "r")):
    MAP.update({s + "Shoulder": "clavicle_" + t, s + "Arm": "upperarm_" + t, s + "ForeArm": "lowerarm_" + t,
                s + "Hand": "hand_" + t, s + "UpLeg": "thigh_" + t, s + "Leg": "calf_" + t,
                s + "Foot": "foot_" + t, s + "ToeBase": "ball_" + t})
    for f, g in (("Index", "index"), ("Middle", "middle"), ("Ring", "ring"), ("Pinky", "pinky"), ("Thumb", "thumb")):
        for i in (1, 2, 3):
            MAP[f"{s}Hand{f}{i}"] = f"{g}_0{i}_{t}"


def strip(n):
    return n.split(":", 1)[1] if ":" in n else n


def world_rot(arm, m):
    return (arm.matrix_world.to_3x3() @ m.to_3x3()).normalized()


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out, jobs = argv[0], [a.split("=", 1) for a in argv[1:]]
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.context.scene.render.fps = FPS
    bpy.ops.import_scene.gltf(filepath=RIG_GLB)
    rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    body = max((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    rig.animation_data_create()
    for tr in list(rig.animation_data.nla_tracks):
        rig.animation_data.nla_tracks.remove(tr)
    # Our rig: forward is -Y (the feet point that way), up +Z.
    tb = rig.data.bones
    T_rest = {b.name: world_rot(rig, b.matrix_local) for b in tb}
    T_dir = {b.name: (rig.matrix_world.to_3x3() @ (b.tail_local - b.head_local)).normalized() for b in tb}
    t_hips = (rig.matrix_world @ tb["pelvis"].head_local)
    order = [b.name for b in tb]  # parents before children (glTF import keeps hierarchy order)
    order.sort(key=lambda n: len(tb[n].parent_recursive))
    sample = range(0, len(body.data.vertices), 7)
    for name, fbx in jobs:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=fbx, automatic_bone_orientation=False)
        new = [o for o in bpy.data.objects if o not in before]
        src = next(o for o in new if o.type == "ARMATURE")
        sb = {strip(b.name): b for b in src.data.bones}
        sp = {strip(p.name): p for p in src.pose.bones}
        act_src = src.animation_data.action
        lo, hi = (int(v) for v in act_src.frame_range)
        bpy.context.scene.frame_set(lo)
        # Their facing: the feet point forward. Turn theirs onto ours about Z.
        def fwd(arm, foot):
            b = arm.data.bones[foot]
            d = arm.matrix_world.to_3x3() @ (b.tail_local - b.head_local)
            return Vector((d.x, d.y, 0.0)).normalized()
        s_fwd = fwd(src, sb["LeftFoot"].name)
        t_fwd = fwd(rig, "foot_l")
        G = s_fwd.rotation_difference(t_fwd).to_matrix()
        S_rest = {k: G @ world_rot(src, b.matrix_local) for k, b in sb.items()}
        S_dir = {k: (G @ src.matrix_world.to_3x3() @ (b.tail_local - b.head_local)).normalized() for k, b in sb.items()}
        s_hips = G @ (src.matrix_world @ sb["Hips"].head_local)
        scale = t_hips.z / s_hips.z
        R_inv = {}
        for s, t in MAP.items():
            if s in sb and t in tb:
                R_inv[t] = S_dir[s].rotation_difference(T_dir[t]).to_matrix().inverted()
        inv_map = {t: s for s, t in MAP.items() if s in sb and t in tb}
        act = bpy.data.actions.new(name)
        rig.animation_data.action = act
        rw_inv = rig.matrix_world.inverted()
        rw3_inv = rig.matrix_world.to_3x3().inverted()
        shifts = []
        frames = list(range(lo, hi + 1))
        for fi in frames:
            bpy.context.scene.frame_set(fi)
            want = {}   # bone -> armature-space 3x3
            for t in order:
                if t not in inv_map:
                    continue
                s = inv_map[t]
                S_a = G @ world_rot(src, sp[s].matrix)
                D = S_a @ S_rest[s].inverted()
                want[t] = rw3_inv @ (D @ R_inv[t] @ T_rest[t])
            # Local basis per bone, parents first: L = (P_rest^-1 B_rest)^-1 P_M^-1 M.
            M_arm = {}
            for t in order:
                b = tb[t]
                pb = rig.pose.bones[t]
                rest_rel = b.matrix_local if b.parent is None else b.parent.matrix_local.inverted() @ b.matrix_local
                P_M = Matrix.Identity(4) if b.parent is None else M_arm[b.parent.name]
                if t in want:
                    head = (P_M @ rest_rel).translation
                    if t == "pelvis":
                        h = G @ (src.matrix_world @ sp["Hips"].head)
                        h = Vector((h.x * scale, h.y * scale, h.z * scale))
                        head = rw_inv @ h
                    M = want[t].to_4x4()
                    M.translation = head
                else:
                    M = P_M @ rest_rel
                L = rest_rel.inverted() @ P_M.inverted() @ M
                M_arm[t] = M
                pb.rotation_mode = "QUATERNION"
                loc, rot, _ = L.decompose()
                pb.rotation_quaternion = rot
                pb.location = loc if t == "pelvis" else Vector()
                pb.keyframe_insert("rotation_quaternion", frame=fi - lo + 1)
                pb.keyframe_insert("location", frame=fi - lo + 1)
        # Stand every frame on the turf (the body's lowest point at 0).
        dg = bpy.context.evaluated_depsgraph_get()
        pel = rig.pose.bones["pelvis"]
        zs = []
        for fi in range(1, len(frames) + 1):
            bpy.context.scene.frame_set(fi)
            ev = body.evaluated_get(dg)
            mw = body.matrix_world
            vs = ev.data.vertices
            zs.append(min((mw @ vs[i].co).z for i in sample))
        # Smooth over 5 frames so a vertex swap never jerks the body.
        sm = [sum(zs[max(0, i - 2):i + 3]) / len(zs[max(0, i - 2):i + 3]) for i in range(len(zs))]
        for i, z in enumerate(sm):
            fi = i + 1
            bpy.context.scene.frame_set(fi)
            # A world shift down by z, in the pelvis's local frame.
            pm = rig.matrix_world @ pel.matrix
            local_dir = (pel.bone.matrix_local.inverted().to_3x3() @ rw3_inv @ Vector((0, 0, -z)))
            pel.location = pel.location + local_dir
            pel.keyframe_insert("location", frame=fi)
        shifts = (min(sm), max(sm))
        rig.animation_data.action = None
        tr = rig.animation_data.nla_tracks.new()
        tr.name = name
        tr.strips.new(name, 1, act)
        act.use_fake_user = True
        print(f"CLIP {name}: {len(frames)} frames ({len(frames) / FPS:.2f} s) from {os.path.basename(fbx)}, "
              f"scale {scale:.3f}, ground shift {shifts[0]:+.3f}..{shifts[1]:+.3f} m")
        for o in new:
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.actions.remove(act_src)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))


main()
