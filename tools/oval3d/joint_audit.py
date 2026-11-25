#!/usr/bin/env python3
"""Each clip's joints against a real body (reel feedback 2026-11-22: "strange model contortion").

Reads tools/oval3d/dump_clip_joints.gd's JSON. For every joint and frame, the rotation away from
rest is split into twist (about the bone's own length) and swing (the bone bending off its rest
line). Knees and elbows are hinges: their bend should sit on one axis, the hinge axis found from
the Epic GASP clips (jog, carry, idle, tackles). Prints, per clip, every frame run where a joint
goes past a limit, worst first.

    python3 tools/oval3d/joint_audit.py JOINTS.json [--clip NAME]
"""
import json, math, sys
import numpy as np

# Degrees past which the joint reads as wrong on a body (twist about the bone, bend off the hinge,
# bend backwards past straight). Anatomy: forearm turn is ~80 deg each way but the hand bone alone
# has no forearm twist bones to share it, so the skin wraps at the wrist past ~70; a knee turns
# ~30 deg only when bent; neck turns ~80; a vertebra pair a few deg (spine_0x each carry a third).
LIMITS = {
    "twist": {"hand": 70, "lowerarm": 70, "calf": 35, "foot": 35, "neck_01": 70, "head": 60,
              "spine_01": 35, "spine_02": 35, "spine_03": 35, "upperarm": 100, "thigh": 60},
    "off_hinge": {"calf": 20, "lowerarm": 35},
    "hyper": {"calf": 5, "lowerarm": 10},
    "bend": {"hand": 70, "foot": 60, "neck_01": 70, "head": 60, "spine_01": 40, "spine_02": 40,
             "spine_03": 40, "ball": 60},
}
BASE = lambda n: n in ("jog", "carry", "idle") or n.startswith("tackle_")


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1*x2 + x1*w2 + y1*z2 - z1*y2, w1*y2 - x1*z2 + y1*w2 + z1*x2,
                     w1*z2 + x1*y2 - y1*x2 + z1*w2, w1*w2 - x1*x2 - y1*y2 - z1*z2])


def qinv(q):
    return np.array([-q[0], -q[1], -q[2], q[3]])


def swing_twist(q, axis):
    """q = swing * twist, twist about axis. Returns (twist deg signed, swing quaternion)."""
    v = np.array(q[:3]); p = np.dot(v, axis) * axis
    tw = np.array([p[0], p[1], p[2], q[3]])
    n = np.linalg.norm(tw)
    tw = np.array([0, 0, 0, 1.0]) if n < 1e-9 else tw / n
    ang = 2 * math.degrees(math.atan2(np.dot(tw[:3], axis), tw[3]))
    ang = (ang + 180) % 360 - 180
    sw = qmul(q, qinv(tw))
    return ang, sw


def kind(j):
    for k in ("lowerarm", "upperarm", "calf", "thigh", "hand", "foot", "ball"):
        if j.startswith(k):
            return k
    return j


def main():
    data = json.load(open(sys.argv[1]))
    only = sys.argv[sys.argv.index("--clip") + 1] if "--clip" in sys.argv else None
    joints = data["joints"]
    # Per joint: the rotation off rest, frame by frame, as (twist, swing axis*angle) in bone space.
    def measures(frames, j):
        rest = np.array(joints[j]["rest"]); axis = np.array(joints[j]["dir"]); axis /= np.linalg.norm(axis)
        out = []
        for f in frames:
            q = qmul(qinv(rest), np.array(f[j]))
            if q[3] < 0: q = -q
            tw, sw = swing_twist(q, axis)
            s_ang = 2 * math.degrees(math.acos(min(1.0, abs(sw[3]))))
            s_ax = sw[:3] / (np.linalg.norm(sw[:3]) + 1e-12) * (1 if sw[3] >= 0 else -1)
            out.append((tw, s_ang, s_ax))
        return out
    # Hinge axes from GASP: the swing axis of its bigger bends, averaged.
    hinge = {}
    for j in joints:
        if kind(j) not in LIMITS["off_hinge"]:
            continue
        acc = np.zeros(3)
        for n, c in data["clips"].items():
            if not BASE(n):
                continue
            for tw, a, ax in measures(c["frames"], j):
                if a > 30:
                    acc += ax * a
        hinge[j] = acc / (np.linalg.norm(acc) + 1e-12)
    # The rest pose's own bend of each hinge (the MetaHuman rest has its elbows and knees a little
    # bent): the parent bone's line, seen from the hinge bone, against the hinge bone's line.
    PARENT = {"lowerarm_l": "upperarm_l", "lowerarm_r": "upperarm_r", "calf_l": "thigh_l", "calf_r": "thigh_r"}
    def rot(q, v):
        p = qmul(qmul(q, np.array([v[0], v[1], v[2], 0.0])), qinv(q))
        return p[:3]
    rest_bend = {}
    for j in hinge:
        up = np.array(joints[PARENT[j]]["dir"]); up /= np.linalg.norm(up)
        in_j = rot(qinv(np.array(joints[j]["rest"])), up)
        own = np.array(joints[j]["dir"]); own /= np.linalg.norm(own)
        cr = np.cross(in_j, own)
        ang = math.degrees(math.atan2(np.linalg.norm(cr), float(np.dot(in_j, own))))
        rest_bend[j] = ang * (1 if float(np.dot(cr, hinge[j])) >= 0 else -1)
    rows = []
    stats = {}
    for n, c in data["clips"].items():
        if only and n != only:
            continue
        for j in joints:
            k = kind(j)
            m = measures(c["frames"], j)
            bad = []
            for fi, (tw, a, ax) in enumerate(m):
                why = []
                lt = LIMITS["twist"].get(k, LIMITS["twist"].get(j))
                if lt and abs(tw) > lt:
                    why.append(("twist", abs(tw), lt))
                if j in hinge:
                    signed = a * float(np.dot(ax, hinge[j]))
                    off = math.degrees(math.acos(max(-1, min(1, abs(float(np.dot(ax, hinge[j])))))))
                    off_deg = a * math.sin(math.radians(off))
                    if off_deg > LIMITS["off_hinge"][k]:
                        why.append(("off-hinge", off_deg, LIMITS["off_hinge"][k]))
                    straight = -(signed + rest_bend[j])
                    if straight > LIMITS["hyper"][k]:
                        why.append(("hyper", straight, LIMITS["hyper"][k]))
                lb = LIMITS["bend"].get(k, LIMITS["bend"].get(j))
                if lb and a > lb:
                    why.append(("bend", a, lb))
                for w in why:
                    bad.append((fi, w))
            key = (n, j)
            st = stats.setdefault(key, {})
            for fi, (what, v, lim) in bad:
                s = st.setdefault(what, [0, 0.0, -1, lim])
                s[0] += 1
                if v > s[1]:
                    s[1] = v; s[2] = fi
    for (n, j), st in stats.items():
        for what, (cnt, worst, fi, lim) in st.items():
            nf = len(data["clips"][n]["frames"])
            rows.append((worst / lim, n, j, what, worst, lim, cnt, nf, fi / data["clips"][n]["hz"]))
    rows.sort(reverse=True)
    print("ratio  clip                          joint        fault      worst  limit  frames      at s")
    for r in rows:
        tag = " (GASP)" if BASE(r[1]) else ""
        print(f"{r[0]:5.2f}  {r[1]+tag:30s} {r[2]:12s} {r[3]:10s} {r[4]:6.0f} {r[5]:6.0f} {r[6]:4d}/{r[7]:<4d} {r[8]:6.2f}")
    print("rest bends", {j: round(v, 1) for j, v in rest_bend.items()})
    print("hinge axes", {j: [round(float(x), 2) for x in v] for j, v in hinge.items()})


main()
