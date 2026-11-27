"""Gait loops from the 100STYLE motion capture onto the match footballer's rig (row 198: walk,
backpedal and side-step, so a man moving slowly is not a slow-motion jog).

  python3.11 (bpy 5.0.1) retarget_bvh.py -- OUT.blend NAME=SOURCE.bvh:START:FRAMES[:mirror] ...

Source: 100STYLE (Ian Mason, Daniel Holden, Taku Komura: https://www.ianxmason.com/100style/),
Creative Commons Attribution 4.0 ("For creative or commercial work please credit ... 'The
100STYLE Dataset - Ian Mason'"). The BVH files never go in the repo; only the motion baked onto
our own rig does (gait_clips.glb, made by ../injury/bake_injury_glb.py from OUT.blend).
START and FRAMES pick one whole gait cycle in the 60 fps take (gait_cycles.py finds them: a
straight, steady stretch whose first and last poses match).

How the motion is moved across: as retarget_mixamo.py (rest-aligned, world-space: our bone
points where theirs points and twists as theirs twists; the hips' path scaled by pelvis height).
Then the cycle is made a loop:
- in place: the hips' travel over the cycle (a straight line) and the slow turn of the take are
  taken out, so the match moves him and the feet are read for his pace (Oval3DAnim.loop_speed);
- closed: each bone's turn between the cycle's first and last frame is spread back over the
  cycle, so the last frame runs into the first with no jump;
- the head held level and facing his way, the neck taking half the chest's lean, never the
  capture's: the actor watched the floor of a small studio, and a footballer's eyes are on the
  ball (Oval3DAnim's look-at turns the head there, inside a real neck's range, from level);
- stood on the turf once for the whole cycle (the body's lowest point, the median over the
  cycle, at 0), never frame by frame, so the hips keep their real rise and fall.
:mirror swaps left and right (a side-step the other way).
Printed per clip: frames, the pace it covers at rate 1, the loop's closing error before and after.
"""
import math, os, sys
import bpy, addon_utils
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
RIG_GLB = os.path.join(HERE, "..", "..", "..", "assets", "oval3d", "player_mh.glb")
FPS = 30
SRC_FPS = 60
UPRIGHT = {"neck_01", "head"}   # level, not the capture's (the neck half the chest's lean)

MAP = {"Hips": "pelvis", "Chest": "spine_01", "Chest3": "spine_02", "Chest4": "spine_03",
       "Neck": "neck_01", "Head": "head"}
for s, t in (("Left", "l"), ("Right", "r")):
    MAP.update({s + "Collar": "clavicle_" + t, s + "Shoulder": "upperarm_" + t, s + "Elbow": "lowerarm_" + t,
                s + "Wrist": "hand_" + t, s + "Hip": "thigh_" + t, s + "Knee": "calf_" + t,
                s + "Ankle": "foot_" + t, s + "Toe": "ball_" + t})


def other(n):
    return n.replace("Left", "@").replace("Right", "Left").replace("@", "Right")


def world_rot(arm, m):
    return (arm.matrix_world.to_3x3() @ m.to_3x3()).normalized()


def flat(v):
    return Vector((v.x, v.y, 0.0)).normalized()


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out, jobs = argv[0], [a.split("=", 1) for a in argv[1:]]
    addon_utils.enable("io_anim_bvh", default_set=True)
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=RIG_GLB)
    rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    body = max((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    rig.animation_data_create()
    for tr in list(rig.animation_data.nla_tracks):
        rig.animation_data.nla_tracks.remove(tr)
    tb = rig.data.bones
    T_rest = {b.name: world_rot(rig, b.matrix_local) for b in tb}
    T_dir = {b.name: (rig.matrix_world.to_3x3() @ (b.tail_local - b.head_local)).normalized() for b in tb}
    t_hips = rig.matrix_world @ tb["pelvis"].head_local
    order = sorted((b.name for b in tb), key=lambda n: len(tb[n].parent_recursive))
    sample = range(0, len(body.data.vertices), 7)
    t_fwd = Vector((0.0, -1.0, 0.0))  # our rig faces -Y
    MX = Matrix.Diagonal((-1.0, 1.0, 1.0))  # left-right mirror in the world (after G, X is his side)
    for name, spec in jobs:
        parts = spec.split(":")
        path, start, length = parts[0], int(parts[1]), int(parts[2])
        mirror = len(parts) > 3 and parts[3] == "mirror"
        before = set(bpy.data.objects)
        sc.render.fps = SRC_FPS
        bpy.ops.import_anim.bvh(filepath=path, global_scale=0.01, frame_start=1, use_fps_scale=False,
                                update_scene_fps=False, rotate_mode="NATIVE", axis_forward="-Z", axis_up="Y")
        src = next(o for o in bpy.data.objects if o not in before and o.type == "ARMATURE")
        sb = {b.name: b for b in src.data.bones}
        sp = {p.name: p for p in src.pose.bones}
        f0 = start + 1   # BVH frame k is Blender frame k + 1
        f1 = f0 + length

        def facing(fr):
            sc.frame_set(int(fr), subframe=fr - int(fr))
            mw = src.matrix_world
            across = flat(mw @ sp["RightHip"].head - mw @ sp["LeftHip"].head)
            f = Vector((0, 0, 1)).cross(across).normalized()
            toe = flat(mw @ sp["LeftToe"].head - mw @ sp["LeftAnkle"].head)
            return f if f.dot(toe) > 0 else -f

        def hips_at(fr):
            sc.frame_set(int(fr), subframe=fr - int(fr))
            return src.matrix_world @ sp["Hips"].head

        fa, fb = facing(f0), facing(f1)
        yaw0 = math.atan2(fa.y, fa.x)
        dyaw = math.atan2(fa.x * fb.y - fa.y * fb.x, fa.dot(fb))
        h0, h1 = hips_at(f0), hips_at(f1)
        S_rest = {k: world_rot(src, b.matrix_local) for k, b in sb.items()}
        S_dir = {k: (src.matrix_world.to_3x3() @ (b.tail_local - b.head_local)).normalized() for k, b in sb.items()}
        # Rest alignment is taken with both rigs facing forward: their rest faces the take's
        # start facing turned onto ours (G0), so R maps their rest bone onto ours.
        n_out = max(2, round(length * FPS / SRC_FPS))
        # Their standing hip height: the rest legs (hip to ankle) plus the ankle height in the take.
        leg_s = (sb["LeftHip"].head_local - sb["LeftAnkle"].head_local).length
        leg_t = (tb["thigh_l"].head_local - tb["foot_l"].head_local).length
        scale = leg_t / leg_s
        act = bpy.data.actions.new(name)
        rig.animation_data.action = act
        rw_inv = rig.matrix_world.inverted()
        rw3_inv = rig.matrix_world.to_3x3().inverted()
        frames_L = []   # per output frame: {bone: local quaternion}, pelvis local location
        # Their rest pose faces +? : read it from their rest feet.
        rest_fwd = flat(src.matrix_world.to_3x3() @ (sb["LeftToe"].head_local - sb["LeftAnkle"].head_local))
        Grest = rest_fwd.rotation_difference(t_fwd).to_matrix()
        R_inv = {}
        for s, t in MAP.items():
            if s in sb and t in tb:
                d = Grest @ S_dir[s]
                if mirror:
                    d = MX @ Grest @ S_dir[other(s)]
                R_inv[t] = d.rotation_difference(T_dir[t]).to_matrix().inverted()
        inv_map = {t: s for s, t in MAP.items() if s in sb and t in tb}
        for i in range(n_out + 1):
            fr = f0 + length * i / n_out
            u = i / n_out
            # His heading at this point of the cycle, with the take's slow turn taken out.
            yaw = yaw0 + dyaw * u
            G = Quaternion((0, 0, 1), -yaw).to_matrix()   # their heading onto +X
            G = Quaternion((0, 0, 1), math.atan2(t_fwd.y, t_fwd.x)).to_matrix() @ G
            sc.frame_set(int(fr), subframe=fr - int(fr))
            want = {}
            Dchest = Matrix.Identity(3)
            for t in order:
                if t not in inv_map:
                    continue
                s = inv_map[t]
                if t in UPRIGHT:
                    # Level: the head as at rest (facing his way), the neck halfway from the chest.
                    D = Matrix.Identity(3) if t == "head" else Quaternion().slerp(Dchest.to_quaternion(), 0.5).to_matrix()
                elif mirror:
                    s2 = other(s)
                    D = MX @ (G @ world_rot(src, sp[s2].matrix)) @ (Grest @ S_rest[s2]).inverted() @ MX
                else:
                    D = (G @ world_rot(src, sp[s].matrix)) @ (Grest @ S_rest[s]).inverted()
                if t == "spine_03":
                    Dchest = D
                want[t] = rw3_inv @ (D @ R_inv[t] @ T_rest[t])
            # The hips: the take's path less the straight line from cycle start to end, turned
            # into his heading and scaled.
            h = src.matrix_world @ sp["Hips"].head
            line = h0.lerp(h1, u)
            off = Vector((h.x - line.x, h.y - line.y, h.z))
            off = G @ off
            if mirror:
                off.x = -off.x
            hips = Vector((t_hips.x + off.x * scale, t_hips.y + off.y * scale, off.z * scale))
            M_arm = {}
            Ls = {}
            for t in order:
                b = tb[t]
                rest_rel = b.matrix_local if b.parent is None else b.parent.matrix_local.inverted() @ b.matrix_local
                P_M = Matrix.Identity(4) if b.parent is None else M_arm[b.parent.name]
                if t in want:
                    head = (P_M @ rest_rel).translation
                    if t == "pelvis":
                        head = rw_inv @ hips
                    M = want[t].to_4x4()
                    M.translation = head
                else:
                    M = P_M @ rest_rel
                L = rest_rel.inverted() @ P_M.inverted() @ M
                M_arm[t] = M
                loc, rot, _ = L.decompose()
                Ls[t] = (loc, rot)
            frames_L.append(Ls)
        # Close the loop: spread each bone's first-to-last difference back over the cycle.
        first, last = frames_L[0], frames_L[-1]
        err0 = max(math.degrees(first[t][1].rotation_difference(last[t][1]).angle) for t in inv_map)
        n = len(frames_L) - 1
        for i, Ls in enumerate(frames_L):
            u = i / n
            for t, (loc, rot) in Ls.items():
                dq = last[t][1].rotation_difference(first[t][1])   # last @ dq == first
                if dq.w < 0.0:
                    dq.negate()   # the short way round
                Ls[t] = (loc + (first[t][0] - last[t][0]) * u, rot @ Quaternion().slerp(dq, u))
        # Key every frame but the last (it is the first again: the loop plays LOOP_LINEAR).
        for i, Ls in enumerate(frames_L[:-1]):
            for t, (loc, rot) in Ls.items():
                pb = rig.pose.bones[t]
                pb.rotation_mode = "QUATERNION"
                pb.rotation_quaternion = rot
                pb.location = loc if t == "pelvis" else Vector()
                pb.keyframe_insert("rotation_quaternion", frame=i + 1)
                pb.keyframe_insert("location", frame=i + 1)
        # The closure, checked: the step from the last keyed frame round to the first, against the
        # cycle's largest frame-to-frame step (each the largest over the bones).
        def step(a, b):
            return max(math.degrees(a[t][1].rotation_difference(b[t][1]).angle) for t in inv_map)
        wrap = step(frames_L[-2], frames_L[0])
        steps = sorted(step(frames_L[i], frames_L[i + 1]) for i in range(len(frames_L) - 2))
        worst = max(inv_map, key=lambda t: frames_L[-2][t][1].rotation_difference(frames_L[0][t][1]).angle)
        if os.environ.get("GAIT_DEBUG"):
            for t in inv_map:
                print("  wrap", t, round(math.degrees(frames_L[-2][t][1].rotation_difference(frames_L[0][t][1]).angle), 1),
                      "last step", round(math.degrees(frames_L[-3][t][1].rotation_difference(frames_L[-2][t][1]).angle), 1))
        # Stand the cycle on the turf: the body's lowest point, the median over the cycle, at 0.
        sc.render.fps = FPS
        dg = bpy.context.evaluated_depsgraph_get()
        zs = []
        for i in range(n):
            sc.frame_set(i + 1)
            ev = body.evaluated_get(dg)
            mw = body.matrix_world
            zs.append(min((mw @ ev.data.vertices[k].co).z for k in sample))
        zs_sorted = sorted(zs)
        z = zs_sorted[len(zs) // 2]
        pel = rig.pose.bones["pelvis"]
        for i in range(n):
            sc.frame_set(i + 1)
            local_dir = pel.bone.matrix_local.inverted().to_3x3() @ rw3_inv @ Vector((0, 0, -z))
            pel.location = pel.location + local_dir
            pel.keyframe_insert("location", frame=i + 1)
        travel = (h1 - h0)
        pace = Vector((travel.x, travel.y, 0)).length * scale / (length / SRC_FPS)
        # Which way the cycle carries him, in his own frame (he faces -Y; his right is -X).
        g0 = Quaternion((0, 0, 1), math.atan2(t_fwd.y, t_fwd.x)).to_matrix() @ Quaternion((0, 0, 1), -yaw0).to_matrix()
        tv = g0 @ Vector((travel.x, travel.y, 0.0))
        if mirror:
            tv.x = -tv.x
        way = math.degrees(math.atan2(-tv.x, -tv.y))   # 0 ahead, +90 to his right, 180 back
        act["gait_pace"] = pace
        act["gait_way"] = way
        rig.animation_data.action = None
        tr = rig.animation_data.nla_tracks.new()
        tr.name = name
        tr.strips.new(name, 1, act)
        act.use_fake_user = True
        print(f"CLIP {name}: {n} frames ({n / FPS:.2f} s) from {os.path.basename(path)} {start}+{length}"
              f"{' mirrored' if mirror else ''}, scale {scale:.3f}, pace at rate 1 {pace:.2f} m/s heading {way:+.0f} deg (0 ahead, +90 his right),"
              f" turn taken out {math.degrees(dyaw):+.1f} deg, loop jump {err0:.1f} deg, closed: wrap step {wrap:.1f} deg vs steps {steps[len(steps) // 2]:.1f} median, {steps[-1]:.1f} max,"
              f" stood {-z:+.3f} m (lowest point range {zs_sorted[0] - z:+.3f}..{zs_sorted[-1] - z:+.3f})")
        for o in [o for o in bpy.data.objects if o not in before]:
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))


main()
