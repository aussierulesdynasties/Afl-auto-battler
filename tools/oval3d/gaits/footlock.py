"""Lock the planted feet of in-place loops in a retarget .blend (NLA strips per clip on the rig).

While a foot is down (its ball bone within DOWN of its lowest in the loop), its ball is held at the
contact point carried on at the loop's ground speed (median ball velocity while down); the correction
fades out over FADE frames after lift. Done with an IK target on each calf (chain 2), baked to keys.

  python footlock.py -- IN.blend OUT.blend NAME [NAME ...]

The sprint (assets/oval3d/sprint_clips.glb, kept private: Mixamo raw file, docs/EPIC_ASSETS.md) is
rebuilt from Mixamo's "Sprint" FBX (In Place off, 30 fps, 17 frames; frames 0-16 are one stride) with:

  GAIT_FPS=60 python retarget_bvh.py -- sprints60.blend sprint=PATH/mixamo_sprint.fbx:0:16
  python footlock.py -- sprints60.blend sprints60_lock.blend sprint
  python ../injury/bake_injury_glb.py -- sprints60_lock.blend assets/oval3d/sprint_clips.glb sprint
  tools/epic_assets.sh publish "why" assets/oval3d/sprint_clips.glb

(each run with a Python that has Blender's bpy module). It prints a LOCK line:
the clip's ground speed, the worst correction and the slip left.
"""
import sys, math
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
src, out, names = argv[0], argv[1], argv[2:]
bpy.ops.wm.open_mainfile(filepath=src)
rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
sc = bpy.context.scene
DOWN = 0.045
FADE = 3

def wpos(bone):
    return rig.matrix_world @ rig.pose.bones[bone].head

for name in names:
    act = bpy.data.actions[name]
    ad = rig.animation_data
    for tr in ad.nla_tracks:
        tr.mute = True
    ad.action = act
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    frames = list(range(f0, f1 + 1))
    n = len(frames)
    ball = {s: [] for s in "lr"}
    ank = {s: [] for s in "lr"}
    for f in frames:
        sc.frame_set(f)
        for s in "lr":
            ball[s].append(wpos("ball_" + s).copy()); ank[s].append(wpos("foot_" + s).copy())
    # contact per foot and the loop's ground speed (median ball velocity while down)
    lo = {s: min(p.z for p in ball[s]) for s in "lr"}
    down = {s: [ball[s][k].z < lo[s] + DOWN for k in range(n)] for s in "lr"}
    vs = []
    for s in "lr":
        for k in range(n):
            if down[s][k] and down[s][(k + 1) % n]:
                d = ball[s][(k + 1) % n] - ball[s][k]
                vs.append(Vector((d.x, d.y, 0)))
    vx = sorted(v.x for v in vs)[len(vs) // 2]; vy = sorted(v.y for v in vs)[len(vs) // 2]
    vel = Vector((vx, vy, 0))   # per frame
    # target corrections (horizontal) per foot per frame; loop wraps
    corr = {s: [Vector()] * n for s in "lr"}
    worst_before = 0.0
    for s in "lr":
        k = 0
        # start at a frame where foot is up so contact runs are whole (wrapping)
        start = next((k for k in range(n) if not down[s][k]), 0)
        order = [(start + j) % n for j in range(n)]
        run = None
        last = Vector()
        since = 99
        for k in order:
            if down[s][k]:
                if run is None:
                    run = (k, ball[s][k].copy())
                k0, p0 = run
                steps = (k - k0) % n
                want = p0 + vel * steps
                d = want - ball[s][k]
                d.z = 0
                worst_before = max(worst_before, d.length)
                corr[s][k] = d
                last = d; since = 0
            else:
                run = None
                since += 1
                w = max(0.0, 1.0 - since / FADE)
                corr[s][k] = last * w
    # IK targets
    targets = {}
    for s in "lr":
        e = bpy.data.objects.new("lock_" + s, None)
        sc.collection.objects.link(e)
        for i, f in enumerate(frames):
            e.location = ank[s][i] + corr[s][i]
            e.keyframe_insert("location", frame=f)
        pb = rig.pose.bones["calf_" + s]
        c = pb.constraints.new("IK")
        c.target = e
        c.chain_count = 2
        c.use_stretch = False
        targets[s] = (e, c)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    for b in rig.pose.bones:
        b.select = b.name in ("thigh_l", "calf_l", "thigh_r", "calf_r")
    bpy.ops.nla.bake(frame_start=f0, frame_end=f1, only_selected=True, visual_keying=True,
                     clear_constraints=True, use_current_action=True, bake_types={"POSE"})
    bpy.ops.object.mode_set(mode="OBJECT")
    for s in "lr":
        bpy.data.objects.remove(targets[s][0], do_unlink=True)
    # measure after
    ad.action = act
    worst_after = 0.0; med = []
    for s in "lr":
        bl = []
        for f in frames:
            sc.frame_set(f); bl.append(wpos("ball_" + s).copy())
        for k in range(n - 1):
            if down[s][k] and down[s][k + 1]:
                d = (bl[k + 1] - bl[k]) - vel
                d.z = 0
                med.append(d.length)
    med.sort()
    print(f"LOCK {name}: frames {n}, ground speed {vel.length * sc.render.fps:.2f} m/s, worst fix {worst_before*100:.1f} cm, after: per-frame slip median {med[len(med)//2]*100:.2f} cm max {med[-1]*100:.2f} cm")
    ad.action = None
    for tr in ad.nla_tracks:
        tr.mute = False
bpy.ops.wm.save_as_mainfile(filepath=out)
