"""The match crew's own clips (row 202), keyed on the footballers' skeleton from broadcast reference.

    python -I key_crew_clips.py BODY.glb OUT.glb [PREVIEW_DIR]

BODY is the footballer the match draws (assets/oval3d/player_average.glb or player_mh.glb): its
skeleton and its idle (the stance every clip starts from and returns to). OUT gets the skeleton
and the clips only, no mesh (assets/oval3d/crew_clips.glb); Godot points their tracks at each
umpire's skeleton by bone name, as it does the loops. PREVIEW_DIR, when given, gets front and side
renders of the body at each clip's key poses, for checking against the reference.

The reference (cut from 2025 AFL broadcasts and the AFL's umpiring coaching video, kept on the
director's PC and never shipped; descriptions in its NOTES.md):

  goal_signal  2025 Fox, three takes: both hands come up to the cap, then the right arm goes
               straight forward at shoulder height and the left hand stays at the waist, both
               index fingers pointing. About 0.5 s to the signal; held at least 1 s.
  behind_signal  the AFL coaching video: one arm straight forward, one index finger; the other
               arm down.

Poses are set by where the hands go (a two-bone reach from the shoulder, the elbow toward a
pole) and which way the hand points; the fingers point (index straight, the rest closed) or
rest. Everything else in the body follows the idle, frame for frame.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
BODY, OUT = args[0], args[1]
PREVIEW = args[2] if len(args) > 2 else ""
FPS = 30

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=BODY)
scene = bpy.context.scene
scene.render.fps = FPS
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
body = [o for o in bpy.data.objects if o.type == "MESH" and o.find_armature() == arm]
idle = bpy.data.actions["idle"]
bones = arm.data.bones
pose = arm.pose.bones
# The body faces -Y; his right is -X.
FWD = Vector((0, -1, 0))
UP = Vector((0, 0, 1))


def side_x(s):
    return -1.0 if s == "r" else 1.0


def update():
    bpy.context.view_layer.update()


def set_idle(t):
    """Every bone as the idle has it at t seconds (the idle loops)."""
    arm.animation_data_create()
    arm.animation_data.action = idle
    f0, f1 = idle.frame_range
    span = f1 - f0
    f = f0 + ((t * FPS) % span)
    scene.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
    # Bake what the action gives into the pose, then let go of the action.
    vals = {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy()) for pb in pose}
    arm.animation_data.action = None
    for pb in pose:
        pb.location, pb.rotation_quaternion = vals[pb.name]
    update()


def aim(name, direction, twist=0.0):
    """Turns bone `name` so it points along `direction` (armature space), the least turn from
    its rest, then twisted `twist` degrees about itself."""
    pb = pose[name]
    rest = bones[name].matrix_local.to_3x3()
    d = Vector(direction).normalized()
    q = rest.col[1].normalized().rotation_difference(d)
    m = q.to_matrix() @ rest
    if twist:
        m = Matrix.Rotation(math.radians(twist), 3, d) @ m
    head = pb.head.copy()
    pb.matrix = Matrix.Translation(head) @ m.to_4x4()
    update()


def turn(name, axis, deg):
    """Bone `name` turned `deg` degrees about `axis` (armature space) at its head."""
    pb = pose[name]
    m = Matrix.Rotation(math.radians(deg), 3, Vector(axis).normalized()) @ pb.matrix.to_3x3()
    pb.matrix = Matrix.Translation(pb.head.copy()) @ m.to_4x4()
    update()


def _rest_palm(s):
    """Out of the palm of hand s in the hand bone's own frame, from the rest skeleton (fingers
    straight): the knuckle line and the fingers' line, on the thumb's side."""
    B = bones
    across = (B["index_01_" + s].head_local - B["pinky_01_" + s].head_local).normalized()
    along = (B["middle_02_" + s].head_local - B["middle_01_" + s].head_local).normalized()
    n = across.cross(along).normalized()
    if (B["thumb_02_" + s].head_local - B["middle_01_" + s].head_local).dot(n) < 0:
        n = -n
    return B["hand_" + s].matrix_local.to_3x3().inverted() @ n


def palm_normal(s):
    """Out of the palm of hand s, as the hand bone is posed now (whatever the fingers do)."""
    return (pose["hand_" + s].matrix.to_3x3() @ _rest_palm(s)).normalized()


def roll_palm(s, palm, hand_dir):
    """Rolls arm s's hand about its own line until its palm faces palm (as near as the line
    allows); half the roll in the forearm, as a forearm turns the hand."""
    def need():
        d = pose["hand_" + s].matrix.to_3x3().col[1].normalized()
        want = Vector(palm) - d * Vector(palm).dot(d)
        have = palm_normal(s)
        have = have - d * have.dot(d)
        if want.length < 1e-6 or have.length < 1e-6:
            return d, 0.0
        want.normalize()
        have.normalize()
        ang = math.degrees(have.angle(want))
        return d, (ang if have.cross(want).dot(d) >= 0 else -ang)
    d, ang = need()
    fore = pose["lowerarm_" + s].matrix.to_3x3().col[1].normalized()
    turn("lowerarm_" + s, fore, ang * 0.5)
    aim("hand_" + s, hand_dir)
    d, ang = need()
    turn("hand_" + s, d, ang)


def reach(s, target, pole, hand_dir, twist=0.0, hand_twist=0.0, palm=None):
    """Arm s ('r' or 'l'): the hand's root at target, the elbow toward pole (a direction from
    the shoulder), the hand along hand_dir, its palm toward palm when given."""
    up_n, lo_n, ha_n = "upperarm_" + s, "lowerarm_" + s, "hand_" + s
    a = (bones[up_n].tail_local - bones[up_n].head_local).length
    b = (bones[lo_n].tail_local - bones[lo_n].head_local).length
    sh = pose[up_n].head.copy()
    t = Vector(target)
    d = t - sh
    L = min(d.length, (a + b) * 0.9995)
    d.normalize()
    # Elbow: law of cosines, bent toward the pole.
    cos_a = (a * a + L * L - b * b) / (2 * a * L)
    ang = math.acos(max(-1.0, min(1.0, cos_a)))
    p = Vector(pole).normalized()
    p = (p - d * p.dot(d))
    if p.length < 1e-6:
        p = UP - d * UP.dot(d)
    p.normalize()
    elbow = sh + (d * math.cos(ang) + p * math.sin(ang)) * a
    aim(up_n, elbow - sh, twist)
    wrist = sh + d * L
    aim(lo_n, wrist - pose[lo_n].head, twist)
    aim(ha_n, hand_dir, hand_twist)
    if palm is not None:
        roll_palm(s, palm, hand_dir)


FINGERS = ["index", "middle", "ring", "pinky"]


def curl(s, amounts):
    """Fingers of hand s bent toward the palm from straight: amounts {finger: (base, mid, tip)
    degrees}, thumb included; a finger not named stays straight. (The idle's own hands are
    half closed: every finger starts from its rest, straight.)"""
    for f in FINGERS + ["thumb"]:
        for j in range(3):
            pose["%s_%02d_%s" % (f, j + 1, s)].rotation_quaternion = Quaternion()
    update()
    hand = pose["hand_" + s]
    i1 = pose["index_01_" + s].head
    p1 = pose["pinky_01_" + s].head
    across = (i1 - p1).normalized()
    along = (pose["middle_02_" + s].head - pose["middle_01_" + s].head).normalized()
    n = across.cross(along).normalized()
    if (pose["thumb_02_" + s].head - pose["middle_01_" + s].head).dot(n) < 0:
        n = -n
    # One way of turning for the whole hand (a bone already bent past the palm's line would
    # otherwise pick its way back): the way that takes the fingers toward the palm.
    sign = 1.0 if (Matrix.Rotation(0.1, 3, across) @ along).dot(n) > 0 else -1.0
    thumb_dir = (pose["thumb_03_" + s].head - pose["thumb_01_" + s].head).normalized()
    t_axis = along
    t_sign = 1.0 if (Matrix.Rotation(0.1, 3, t_axis) @ thumb_dir).dot(n) > 0 else -1.0
    for f, angs in amounts.items():
        axis, sg = (t_axis, t_sign) if f == "thumb" else (across, sign)
        for j, deg in enumerate(angs):
            pb = pose["%s_%02d_%s" % (f, j + 1, s)]
            m = Matrix.Rotation(sg * math.radians(deg), 3, axis) @ pb.matrix.to_3x3()
            pb.matrix = Matrix.Translation(pb.head.copy()) @ m.to_4x4()
            update()


POINT = {"middle": (85, 95, 55), "ring": (88, 98, 55), "pinky": (90, 98, 55), "thumb": (25, 35, 25)}
RELAX = {"index": (8, 12, 6), "middle": (12, 16, 8), "ring": (14, 18, 8), "pinky": (16, 20, 10),
         "thumb": (6, 8, 4)}


def shoulder(s):
    return pose["upperarm_" + s].head.copy()


def arm_len(s):
    a = (bones["upperarm_" + s].tail_local - bones["upperarm_" + s].head_local).length
    b = (bones["lowerarm_" + s].tail_local - bones["lowerarm_" + s].head_local).length
    return a + b


# The poses. Each takes the idle's pose at that moment and sets the arms on it.
def p_stand(t):
    set_idle(t)


# Where things are on this body: the cap's crown over the head, his chest and belt.
# (The cap's top is 1.897 m, 5.5 cm forward of the head's line: tools/oval3d/crew/build_crew.py.)
CROWN = Vector((0.0, -0.05, 1.90))


def trunk_to(deg):
    """The trunk turned deg degrees toward his right (the way he points), over the spine."""
    for b in ("spine_01", "spine_02", "spine_03"):
        turn(b, UP, -deg / 3.0)


def p_swing(t):
    """Both arms, nearly straight, swing forward and up toward his right front: hands at chest
    height about 55 cm out (a3 f_013)."""
    set_idle(t)
    trunk_to(5)
    reach("r", Vector((-0.25, -0.55, 1.36)), Vector((-0.6, 0.2, -1)), Vector((-0.2, -0.9, 0.35)),
          palm=Vector((0.6, 0, 0.8)))
    reach("l", Vector((-0.02, -0.56, 1.37)), Vector((0.6, 0.2, -1)), Vector((-0.2, -0.9, 0.35)),
          palm=Vector((-0.6, 0, 0.8)))
    curl("r", RELAX)
    curl("l", RELAX)


def p_over(t):
    """Both hands 15-20 cm above the cap and 20-30 cm in front of the forehead, wrists
    crossed; elbows bent about 120 degrees, out and up (a3 f_014)."""
    set_idle(t)
    trunk_to(3)
    reach("r", Vector((0.03, -0.27, 1.97)), Vector((-1, 0.0, 0.2)), Vector((0.3, -0.45, 0.85)),
          palm=Vector((0, -1, 0)))
    reach("l", Vector((-0.03, -0.25, 1.98)), Vector((1, 0.0, 0.2)), Vector((-0.3, -0.45, 0.85)),
          palm=Vector((0, -1, 0)))
    curl("r", RELAX)
    curl("l", RELAX)


def p_cap(t):
    """Both hands on the top of the cap, palms down: the right over the front of the crown, the
    left at its left rear; elbows high and out at ear height (a3 f_015)."""
    set_idle(t)
    turn("head", Vector((1, 0, 0)), 8)
    # The hand's line lies 2 cm over the cap (the palm's own thickness under it).
    reach("r", CROWN + Vector((-0.11, -0.05, -0.005)), Vector((-1, -0.2, 0.15)), Vector((0.92, 0.1, 0.05)),
          palm=Vector((0, 0, -1)))
    reach("l", CROWN + Vector((0.11, 0.07, -0.015)), Vector((1, 0.1, 0.15)), Vector((-0.92, -0.05, 0.05)),
          palm=Vector((0, 0, -1)))
    curl("r", RELAX)
    curl("l", RELAX)


def p_ears(t):
    """The hands slide down beside the head to cheek height, 10 cm out from it, palms forward
    and in; elbows down and out (a3 f_016)."""
    set_idle(t)
    reach("r", Vector((-0.17, -0.04, 1.62)), Vector((-0.5, 0.2, -1)), Vector((0.1, -0.15, 1.0)),
          palm=Vector((0.5, -0.85, 0)))
    reach("l", Vector((0.17, -0.04, 1.62)), Vector((0.5, 0.2, -1)), Vector((-0.1, -0.15, 1.0)),
          palm=Vector((-0.5, -0.85, 0)))
    curl("r", RELAX)
    curl("l", RELAX)


def p_goal(t):
    """The goal (a3 f_017, held to f_022): right hand at chest height, about 18 cm under the
    shoulder line, 50-55 cm out in line with the right shoulder, elbow 160-165 degrees; left
    hand 5 cm above the belt in front of the belly, 5-10 cm right of his middle, elbow tucked
    by his side; both index fingers out down the ground, thumbs on top, palms in. The trunk
    turned 10-15 degrees toward the point, the head with it, chin a little down."""
    set_idle(t)
    trunk_to(12)
    turn("head", UP, -4)
    turn("head", Vector((1, 0, 0)), 6)
    sh = shoulder("r")
    reach("r", sh + Vector((-0.01, -0.47, -0.16)), Vector((-0.4, 0.1, -1)), Vector((-0.02, -0.96, -0.27)),
          palm=Vector((1, 0, -0.35)))
    curl("r", POINT)
    pel = pose["pelvis"].head
    # Thumb on top as on the right hand, so this palm faces across him, to his right.
    reach("l", Vector((0.01, pel.y - 0.17, pel.z + 0.06)), Vector((1, 0.8, -0.6)), Vector((-0.12, -0.99, -0.05)),
          palm=Vector((-1, 0, -0.35)))
    curl("l", POINT)


def p_behind(t):
    """A behind (a6 f_047): one arm straight forward at chest-to-shoulder height, about 60 cm
    out in line with the shoulder, elbow about 170 degrees, index finger out, palm in; the
    other arm down by his side; the head along the arm. Which arm is not settled by the
    footage: his right, as for the goal."""
    set_idle(t)
    turn("head", Vector((1, 0, 0)), 4)
    sh = shoulder("r")
    reach("r", sh + Vector((-0.01, -0.54, -0.06)), Vector((-0.4, 0.1, -1)), Vector((-0.02, -0.99, -0.1)),
          palm=Vector((1, 0, -0.2)))
    curl("r", POINT)


# The boundary umpire's throw-in (b1, real time): his back to the ground, ball at his chest; up
# overhead; a dip of 0.4 s to the bottom, the ball between his feet 15-25 cm off the turf, knees
# 100-110 degrees, trunk 45-55 degrees forward with a flat back; held 0.2-0.3 s; a drive of 0.45 s
# to let it go straight overhead and a little behind, his feet off the turf, back arched 30-40
# degrees and one leg (the left, as near as the footage shows) kicked up in front; 0.6 s back.
BALL_GRIP = {"index": (18, 16, 8), "middle": (20, 18, 8), "ring": (22, 20, 10), "pinky": (24, 22, 10),
             "thumb": (8, 10, 6)}
LEG = {}


def _rest_feet():
    """Where each foot is in the idle at t, and how it is turned."""
    return {s: (pose["foot_" + s].head.copy(), pose["foot_" + s].matrix.to_3x3().copy()) for s in ("l", "r")}


def leg(s, foot_at, foot_rot=None, pole=Vector((0, -1, 0))):
    """Leg s: the ankle at foot_at, the knee toward pole (forward), the foot turned foot_rot
    (armature space) or as it was."""
    th, ca, fo = "thigh_" + s, "calf_" + s, "foot_" + s
    keep = foot_rot if foot_rot is not None else pose[fo].matrix.to_3x3().copy()
    a = (bones[th].tail_local - bones[th].head_local).length
    b = (bones[ca].tail_local - bones[ca].head_local).length
    hip = pose[th].head.copy()
    d = Vector(foot_at) - hip
    L = min(d.length, (a + b) * 0.9995)
    d.normalize()
    cos_a = (a * a + L * L - b * b) / (2 * a * L)
    ang = math.acos(max(-1.0, min(1.0, cos_a)))
    p = Vector(pole).normalized()
    p = p - d * p.dot(d)
    p.normalize()
    knee = hip + (d * math.cos(ang) + p * math.sin(ang)) * a
    aim(th, knee - hip)
    aim(ca, hip + d * L - pose[ca].head)
    pb = pose[fo]
    pb.matrix = Matrix.Translation(pb.head.copy()) @ keep.to_4x4()
    update()


def hips(drop=0.0, back=0.0, pitch=0.0, bend=0.0, feet=None):
    """The hips dropped `drop` m and moved `back` m behind him, tipped `pitch` degrees forward,
    the spine bent `bend` degrees more forward over its three bones (negative: arched back);
    the feet kept where `feet` has them (planted), when given."""
    pb = pose["pelvis"]
    m = Matrix.Rotation(math.radians(pitch), 3, Vector((1, 0, 0))) @ pb.matrix.to_3x3()
    pb.matrix = Matrix.Translation(pb.head + Vector((0, back, -drop))) @ m.to_4x4()
    update()
    for b in ("spine_01", "spine_02", "spine_03"):
        turn(b, Vector((1, 0, 0)), bend / 3.0)
    if feet:
        for s_, (at, rot) in feet.items():
            leg(s_, at, rot)


def hold_ball(c, hand_dir, spread=0.125, pole_down=True):
    """Both hands either side of a ball at c (its middle), palms in, fingers spread round it."""
    for s_, sx in (("r", -1.0), ("l", 1.0)):
        pole = Vector((sx, 0.3, -1.0)) if pole_down else Vector((sx, 0.0, 0.3))
        reach(s_, c + Vector((sx * spread, 0.04, -0.02)), pole, hand_dir, palm=Vector((-sx, 0, 0)))
        curl(s_, BALL_GRIP)


def p_ti_chest(t):
    """Squared up, back to the ground, the ball at his chest."""
    set_idle(t)
    hold_ball(Vector((0.0, -0.3, 1.24)), Vector((0, -0.85, 0.5)))


def p_ti_over(t):
    """The ball lifted straight up overhead, arms near straight."""
    set_idle(t)
    turn("head", Vector((1, 0, 0)), -6)
    hold_ball(Vector((0.0, -0.14, 2.08)), Vector((0, -0.15, 1)), pole_down=False)


def p_ti_down(t):
    """On the way down: knees starting to give, the ball coming down past his chest."""
    set_idle(t)
    feet = _rest_feet()
    hips(drop=0.1, back=0.06, pitch=8, bend=8, feet=feet)
    hold_ball(Vector((0.0, -0.46, 1.0)), Vector((0, -0.7, -0.7)))


def p_ti_bottom(t):
    """The bottom of the dip: knees about 105 degrees, trunk about 50 degrees forward and flat,
    the ball between his feet about 20 cm off the turf."""
    set_idle(t)
    feet = _rest_feet()
    hips(drop=0.27, back=0.27, pitch=32, bend=30, feet=feet)
    # Shoulders reaching down to the ball.
    for s_ in ("r", "l"):
        c_ = pose["clavicle_" + s_]
        aim("clavicle_" + s_, (c_.tail - c_.head).normalized() + Vector((0, -0.15, -0.45)))
    turn("head", Vector((1, 0, 0)), -24)
    mid = (feet["l"][0] + feet["r"][0]) * 0.5
    hold_ball(Vector((0.0, mid.y - 0.12, 0.22)), Vector((0, -0.25, -1)))


def p_ti_rise(t):
    """Driving up: legs nearly straight, the ball swung up in front of his face."""
    set_idle(t)
    feet = _rest_feet()
    hips(drop=0.05, back=0.03, pitch=4, bend=-4, feet=feet)
    turn("head", Vector((1, 0, 0)), -10)
    hold_ball(Vector((0.0, -0.5, 1.5)), Vector((0, -0.4, 1)))


def p_ti_release(t):
    """Let go: the ball straight overhead and a little behind, back arched about 35 degrees,
    both feet off the turf, the left leg kicked up in front, the right toe pointed."""
    set_idle(t)
    hips(drop=-0.16, back=-0.02, pitch=-10, bend=-25)
    turn("head", Vector((1, 0, 0)), -14)
    hold_ball(Vector((0.0, 0.32, 2.3)), Vector((0, 0.45, 1)), spread=0.13, pole_down=False)
    aim("thigh_l", Vector((0.04, -0.7, -0.72)))
    aim("calf_l", Vector((0.02, -0.05, -1)))
    aim("foot_l", Vector((0, -0.75, -0.66)))
    aim("thigh_r", Vector((-0.04, 0.12, -1)))
    aim("calf_r", Vector((-0.02, 0.3, -1)))
    aim("foot_r", Vector((0, -0.35, -0.94)))


def p_ti_land(t):
    """Down again, knees giving, arms coming down through the follow-through."""
    set_idle(t)
    feet = _rest_feet()
    hips(drop=0.08, back=0.02, pitch=4, bend=-6, feet=feet)
    for s_, sx in (("r", -1.0), ("l", 1.0)):
        reach(s_, Vector((sx * 0.3, 0.05, 1.85)), Vector((sx, 0.2, -0.3)), Vector((sx * 0.3, 0.3, 1)))
        curl(s_, RELAX)


CLIPS = {
    # name: [(seconds, pose)], from the idle's stand and back to it. The goal is formed in
    # 0.6 s, a tenth of a second a step (a3 f_011-017); held 1.6 s (the broadcasts cut away
    # with it still held, at least 0.9 s); the way back is never shown: half a second.
    "goal_signal": [(0.0, p_stand), (0.12, p_swing), (0.24, p_over), (0.36, p_cap), (0.48, p_ears),
                    (0.62, p_goal), (2.2, p_goal), (2.7, p_stand)],
    # Raised in 0.4 s (a6 f_043-047), held 1.5 s.
    "behind_signal": [(0.0, p_stand), (0.4, p_behind), (1.9, p_behind), (2.4, p_stand)],
    # Lifted overhead in 0.35 s (not timed in b1: it opens there); the dip 0.4 s with a key on
    # the way down; held 0.25 s; the drive 0.45 s, through the ball at his face; let go at
    # THROW_REL; landed and back in 0.6 s.
    "throw_in": [(0.0, p_ti_chest), (0.35, p_ti_over), (0.55, p_ti_down), (0.75, p_ti_bottom),
                 (1.0, p_ti_bottom), (1.22, p_ti_rise), (1.45, p_ti_release), (1.72, p_ti_land),
                 (2.05, p_stand)],
}
THROW_REL = 1.45
ONLY = os.environ.get("CREW_ONLY", "")


if os.environ.get("CREW_POSE_DEBUG"):
    # The pointing hand's numbers: the palm's normal, each finger's tip against the palm.
    globals()[os.environ["CREW_POSE_DEBUG"]](0.0)
    for s_ in ("r", "l"):
        n = palm_normal(s_)
        hd = pose["hand_" + s_].matrix.to_3x3().col[1].normalized()
        print("HAND", s_, "dir", tuple(round(x, 2) for x in hd), "palm", tuple(round(x, 2) for x in n))
        for f in FINGERS + ["thumb"]:
            base = pose["%s_01_%s" % (f, s_)].head
            tip = pose["%s_03_%s" % (f, s_)].tail
            v = tip - base
            print("  ", f, "len %.3f tip.palm %.3f tip.dir %.3f" % (v.length, v.dot(n), v.dot(hd)), tuple(round(x, 3) for x in pose["%s_01_%s" % (f, s_)].scale), pose["%s_01_%s" % (f, s_)].rotation_mode)
    sys.exit(0)

def _measure(t, nm):
    """The numbers the reference gives, for checking a throw-in pose: knee angles, the trunk's lean
    from upright (forward +), the ball (between the hands) and the feet's lowest point."""
    def knee(s_):
        a = pose["thigh_" + s_].head - pose["calf_" + s_].head
        b = pose["foot_" + s_].head - pose["calf_" + s_].head
        return math.degrees(a.angle(b))
    tr = pose["neck_01"].head - pose["pelvis"].head
    lean = math.degrees(math.atan2(-tr.y, tr.z))
    ball = (pose["hand_r"].head + pose["hand_l"].head) * 0.5
    low = min(min(pose[n].head.z, pose[n].tail.z) for n in ("foot_l", "ball_l", "foot_r", "ball_r"))
    sh = pose["upperarm_r"].head
    print("  shoulder (%.2f, %.2f, %.2f) arm %.2f to wrist %.2f" % (sh.x, sh.y, sh.z, arm_len("r"), (pose["hand_r"].head - sh).length))
    print("THROW %.2f %-13s knees r %.0f l %.0f  trunk %+.0f  hands mid (%.2f, %.2f, %.2f)  feet low %.3f" % (
        t, nm, knee("r"), knee("l"), lean, ball.x, ball.y, ball.z, low))


# Keying straight into a named action each time.
made = []
for name, keys in CLIPS.items():
    act = bpy.data.actions.new(name)
    arm.animation_data_create()
    arm.animation_data.action = act
    for t, fn in keys:
        # Pose with no action driving, then key into act.
        arm.animation_data.action = None
        fn(t)
        if name == "throw_in":
            _measure(t, fn.__name__)
        arm.animation_data.action = act
        f = 1 + t * FPS
        for pb in pose:
            pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
            if pb.name in ("pelvis", "Root"):
                pb.keyframe_insert("location", frame=f, group=pb.name)
    act.use_fake_user = True
    made.append(act)
    print("CLIP", name, act.frame_range[:])

if PREVIEW:
    os.makedirs(PREVIEW, exist_ok=True)
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 8
    scene.cycles.device = "CPU"
    scene.render.resolution_x, scene.render.resolution_y = 300, 420
    scene.world = bpy.data.worlds.new("w")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3
    sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    scene.collection.objects.link(sun)
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    for o in bpy.data.objects:
        if o.type == "MESH" and o not in body:
            o.hide_render = True
    views = {"front": Vector((0.0, -4.2, 1.2)), "side": Vector((-4.2, -0.3, 1.2))}
    for act in made:
        if ONLY and act.name != ONLY:
            continue
        arm.animation_data.action = act
        for t, _ in CLIPS[act.name][1:-1]:
            scene.frame_set(int(round(1 + t * FPS)))
            hr = pose["hand_r"].head.copy()
            hl = pose["hand_l"].head.copy()
            shots = dict(views)
            # The pointing hands close, from his right and from in front.
            shots["hand_r"] = (hr + Vector((-0.45, -0.25, 0.1)), hr + Vector((0, -0.08, 0)))
            shots["hand_l"] = (hl + Vector((-0.15, -0.5, 0.15)), hl + Vector((0, -0.08, 0)))
            for v, at in shots.items():
                look_at = Vector((0, 0, 1.15))
                if isinstance(at, tuple):
                    at, look_at = at
                cam.location = at
                d = look_at - at
                cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
                scene.render.filepath = os.path.join(PREVIEW, "%s_%04.2f_%s.png" % (act.name, t, v))
                bpy.ops.render.render(write_still=True)

# Out: the skeleton and the clips, no mesh.
arm.animation_data.action = None
for o in list(bpy.data.objects):
    if o != arm:
        bpy.data.objects.remove(o)
for a in list(bpy.data.actions):
    if a not in made:
        bpy.data.actions.remove(a)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_animation_mode="ACTIONS",
                          export_force_sampling=True, export_frame_step=1)
print("WROTE", OUT)
