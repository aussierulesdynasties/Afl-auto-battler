#!/usr/bin/env python3
"""Physics pass for a two-man clip (a speccy): both men as MuJoCo bodies with weight and solid
limbs, their joints driven toward the keyed poses, gravity and contact deciding the rest.

    python3 tools/oval3d/sim_pair.py IN.json OUT.json [--report REPORT.txt]

IN.json comes from export_pair.gd (the keyed clip's body bones, globals per frame). OUT.json has
each man's simulated bone globals per frame at 25 Hz (import_pair.gd writes them back as clips).

The rule that keeps it honest: each man's hips may get a helping force toward the keyed path only
while he touches something, and only what that contact could give. On the ground it is his legs
pushing off the turf (inside a friction cone, never pulling down). On the other man it is a push
or a grip through that contact, inside a friction cone, and the other man takes the equal and
opposite force (so the stepladder carries the jumper's weight). In the air there is no help at
all: he follows the arc his take-off gave him. Limbs never pass through the other man: the solids
collide. Each man's own limbs do not collide with each other (the keyed poses keep them apart).

Options: --launch-until T solves the jumper's take-off (extra launch velocity and spin) so he
arrives at the keyed place and posture at T; --launch " vx,vy,vz,wx,wy,wz" reuses a solved one.
RAGDOLL="M:T0:TP" makes man M go limp at T0 holding the keyed pose of time TP (LIMP x strength).
MARGIN_EXTRA='{"hand": 0.025}' pads a body part further (experiments).

Jurrah 2010 (speccies/jurrah_2010_phys.json, jumper MEL_14 stand-in, stepladder PAD_28):
    key_pair.gd -> export_pair.gd (50 Hz) -> MARGIN_EXTRA='{"hand": 0.025}' RAGDOLL=0:1.5:1.72
    LIMP=0.5 sim_pair.py --launch " 0.18,0.37,-0.1,1.2,0,-0.18" -> import_pair.gd
    -> skin_pair.gd -> check_mesh_pair.py (PASS, 0.0 cm). The fall is chaotic: a small change to
    any setting changes where he lands, so judge every rerun by eye from four sides.
"""
import json
import os
import sys

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation as Rot

SIM_DT = 0.001
OUT_HZ = 25.0
MASS = 76.0          # kg, an AFL body
MU = 1.0             # friction: turf and guernsey grip
SKIP = {"ball_l", "ball_r"}

# Solids in the world at rest (metres; left is +x, front is +z). "seg" runs the bone to its end.
SHAPES = {
    "pelvis": [("capsule", (-0.1, 0.95, 0.02), (0.1, 0.95, 0.02), 0.1)],
    "spine_01": [("capsule", (-0.07, 1.07, 0.03), (0.07, 1.07, 0.03), 0.11)],
    "spine_02": [("capsule", (-0.08, 1.18, 0.04), (0.08, 1.18, 0.04), 0.12)],
    "spine_03": [("capsule", (0.0, 1.25, 0.04), (0.0, 1.40, 0.0), 0.14),
                 ("capsule", (-0.12, 1.44, -0.02), (0.12, 1.44, -0.02), 0.1)],
    "neck_01": [("capsule", (0.0, 1.585, -0.01), (0.0, 1.68, 0.01), 0.055)],
    "head": [("sphere", (0.0, 1.79, 0.03), None, 0.105)],
    "clavicle_l": [("seg", None, None, 0.045)], "clavicle_r": [("seg", None, None, 0.045)],
    "upperarm_l": [("seg", None, None, 0.05)], "upperarm_r": [("seg", None, None, 0.05)],
    "lowerarm_l": [("seg", None, None, 0.04)], "lowerarm_r": [("seg", None, None, 0.04)],
    "hand_l": [("hand", None, None, 0.032)], "hand_r": [("hand", None, None, 0.032)],
    "thigh_l": [("seg", None, None, 0.075)], "thigh_r": [("seg", None, None, 0.075)],
    "calf_l": [("seg", None, None, 0.055)], "calf_r": [("seg", None, None, 0.055)],
    "foot_l": [("foot", None, None, 0.035)], "foot_r": [("foot", None, None, 0.035)],
}
# Joint strength (N m per radian) and the cone each ball joint may bend through (degrees).
GAIN = {"spine": 6000.0, "neck_01": 500.0, "head": 150.0, "clavicle": 1200.0, "upperarm": 900.0,
        "lowerarm": 450.0, "hand": 40.0, "thigh": 8000.0, "calf": 6000.0, "foot": 1200.0}
RANGE = {"spine": 50, "neck_01": 70, "head": 70, "clavicle": 30, "upperarm": 179, "lowerarm": 165,
         "hand": 90, "thigh": 150, "calf": 165, "foot": 75}
MARGIN = {"pelvis": 0.06, "spine": 0.06, "thigh": 0.05, "neck_01": 0.01, "head": 0.0,
          "calf": 0.02, "upperarm": 0.02, "lowerarm": 0.02, "hand": 0.015}
MARGIN.update(json.loads(os.environ.get("MARGIN_EXTRA", "{}")))  # experiments: {"hand": 0.03}
ROOT_KP, ROOT_KD = 60.0, 14.0         # 1/s^2, 1/s: the hips' pull toward the keyed path
ROOT_ROT_KP, ROOT_ROT_KD = 50.0, 12.0
import os
# RAGDOLL="0:1.36": from that time the man goes limp (holding the pose he had then, at LIMP of his
# strength, with no help at the hips): a fall decided by the fall itself.
# A third field holds the keyed joint pose of that time instead ("0:1.3:1.72": limp from 1.3 s,
# curled as he is keyed at 1.72 s: a tuck, which a falling player holds).
RAGDOLL = {int(x.split(":")[0]): float(x.split(":")[1]) for x in os.environ.get("RAGDOLL", "").split(",") if x}
RAG_POSE = {int(x.split(":")[0]): float(x.split(":")[2]) for x in os.environ.get("RAGDOLL", "").split(",") if x.count(":") == 2}
LIMP = float(os.environ.get("LIMP", "0.25"))
DEBUG = os.environ.get("SIM_DEBUG", "") != ""
DEBUG_MAN = int(os.environ.get("SIM_DEBUG", "0") or 0)
ROOT_TORQUE_CAP = 1000.0              # N m


def kind(name):
    for k in ("spine", "clavicle", "upperarm", "lowerarm", "hand", "thigh", "calf", "foot"):
        if name.startswith(k):
            return k
    return name


def q_wxyz(q):   # [x,y,z,w] -> mujoco's [w,x,y,z]
    return [q[3], q[0], q[1], q[2]]


def R(q):        # [x,y,z,w]
    return Rot.from_quat(q)


def build(bones):
    """MJCF for two men, each bone a body whose frame is that bone's rest frame (so a body's
    world orientation is the bone's global pose basis)."""
    keep = [i for i, b in enumerate(bones) if b["name"] not in SKIP]
    vol = 0.0
    for i in keep:
        for s in SHAPES[bones[i]["name"]]:
            r = s[3]
            if s[0] == "sphere":
                vol += 4 / 3 * np.pi * r ** 3
            else:
                a, b = _ends(bones[i], s)
                vol += np.pi * r * r * np.linalg.norm(np.array(b) - np.array(a)) + 4 / 3 * np.pi * r ** 3
    density = MASS / vol
    xml = ['<mujoco model="pair"><compiler angle="radian"/>',
           '<option timestep="%g" gravity="0 -9.81 0" integrator="implicitfast"><flag/></option>' % SIM_DT,
           '<default><geom friction="%g 0.02 0.002" condim="3" solref="0.004 1" solimp="0.95 0.99 0.001"/>'
           '<joint damping="0" armature="0.02"/></default><worldbody>' % MU,
           '<geom name="ground" type="plane" size="30 30 0.1" quat="0.7071068 -0.7071068 0 0" contype="4" conaffinity="3"/>']
    for m in range(2):
        xml.append(_body(bones, keep, 0, -1, m, density, top=True))
    xml.append('</worldbody></mujoco>')
    return "\n".join(xml)


def _ends(bone, s):
    p = np.array(bone["rest_pos"])
    e = np.array(bone["end"])
    if s[0] == "seg":
        return p, e
    if s[0] == "hand":
        d = e - p
        d /= np.linalg.norm(d)
        return p + d * 0.02, p + d * 0.17
    if s[0] == "foot":
        x = p[0]
        return np.array([x, 0.045, 0.02]), np.array([x, 0.035, 0.22])
    return np.array(s[1]), np.array(s[2])


def _body(bones, keep, i, parent, m, density, top=False):
    b = bones[i]
    name = b["name"]
    rp = np.array(b["rest_pos"])
    rq = R(b["rest_quat"])
    if parent < 0:
        pos, quat = rp, rq.as_quat()
    else:
        pp = np.array(bones[parent]["rest_pos"])
        pq = R(bones[parent]["rest_quat"])
        pos = pq.inv().apply(rp - pp)
        quat = (pq.inv() * rq).as_quat()
    s = ['<body name="m%d_%s" pos="%g %g %g" quat="%g %g %g %g">' % ((m, name) + tuple(pos) + tuple(q_wxyz(quat)))]
    if top:
        s.append('<freejoint name="m%d_root"/>' % m)
    else:
        k = kind(name)
        # The joint's damping is in the model, so the solver treats it implicitly (stable at any gain).
        s.append('<joint name="m%d_%s" type="ball" range="0 %g" limited="true" damping="%g"/>'
                 % (m, name, np.radians(RANGE[k]), GAIN[k] / 18.0))
    ct, ca = (1, 2 | 4) if m == 0 else (2, 1 | 4)
    # The capsules sit inside the real body (flesh, muscle, kit): padded out by this much (mass
    # kept), so the skinned meshes meet instead of passing through (check_mesh_pair.py).
    pad = MARGIN.get(kind(name), 0.0)
    for sh in SHAPES[name]:
        if sh[0] == "sphere":
            c = rq.inv().apply(np.array(sh[1]) - rp)
            s.append('<geom type="sphere" pos="%g %g %g" size="%g" density="%g" contype="%d" conaffinity="%d"/>'
                     % (tuple(c) + (sh[3] + pad, density * (sh[3] / (sh[3] + pad)) ** 3, ct, ca)))
        else:
            a, e = _ends(b, sh)
            a = rq.inv().apply(np.array(a) - rp)
            e = rq.inv().apply(np.array(e) - rp)
            s.append('<geom type="capsule" fromto="%g %g %g %g %g %g" size="%g" density="%g" contype="%d" conaffinity="%d"/>'
                     % (tuple(a) + tuple(e) + (sh[3] + pad, density * (sh[3] / (sh[3] + pad)) ** 2, ct, ca)))
    for j in keep:
        if bones[j]["parent"] == i:
            s.append(_body(bones, keep, j, i, m, density))
    s.append('</body>')
    return "\n".join(s)


class Pair:
    def __init__(self, data_in):
        self.bones = data_in["bones"]
        self.hz = float(data_in["hz"])
        self.keep = [i for i, b in enumerate(self.bones) if b["name"] not in SKIP]
        self.model = mujoco.MjModel.from_xml_string(build(self.bones))
        self.d = mujoco.MjData(self.model)
        mo = self.model
        self.men = []
        for m in range(2):
            fr = data_in["men"][m]["frames"]
            man = {"pos": np.array([[f["pos"][i] for i in range(len(self.bones))] for f in fr]),
                   "quat": np.array([[f["quat"][i] for i in range(len(self.bones))] for f in fr]),
                   "body": {}, "jq": {}, "jv": {}, "geoms": set()}
            for i in self.keep:
                n = self.bones[i]["name"]
                bid = mujoco.mj_name2id(mo, mujoco.mjtObj.mjOBJ_BODY, "m%d_%s" % (m, n))
                man["body"][i] = bid
                if self.bones[i]["parent"] >= 0:
                    jid = mujoco.mj_name2id(mo, mujoco.mjtObj.mjOBJ_JOINT, "m%d_%s" % (m, n))
                    man["jq"][i] = mo.jnt_qposadr[jid]
                    man["jv"][i] = mo.jnt_dofadr[jid]
            rj = mujoco.mj_name2id(mo, mujoco.mjtObj.mjOBJ_JOINT, "m%d_root" % m)
            man["rq"] = mo.jnt_qposadr[rj]
            man["rv"] = mo.jnt_dofadr[rj]
            man["bodies"] = set(man["body"].values())
            man["mass"] = sum(mo.body_mass[b] for b in man["bodies"])
            self.men.append(man)
        self.ground = mujoco.mj_name2id(mo, mujoco.mjtObj.mjOBJ_GEOM, "ground")
        self.nframes = len(self.men[0]["pos"])
        self.length = (self.nframes - 1) / self.hz
        print("MASS %.1f %.1f kg" % (self.men[0]["mass"], self.men[1]["mass"]))

    # The keyed pose at time t: per bone global rotation, pelvis position (interpolated).
    def target(self, m, t):
        f = min(max(t * self.hz, 0.0), self.nframes - 1.0001)
        i = int(f)
        u = f - i
        man = self.men[m]
        pos = man["pos"][i] * (1 - u) + man["pos"][i + 1] * u
        quats = []
        for b in range(len(self.bones)):
            q0, q1 = man["quat"][i][b], man["quat"][i + 1][b]
            if np.dot(q0, q1) < 0:
                q1 = -q1
            q = q0 * (1 - u) + q1 * u
            quats.append(q / np.linalg.norm(q))
        return pos, np.array(quats)

    def local_target(self, quats, b):
        """The ball joint's rotation (child frame) that gives bone b its keyed global rotation,
        given its parent's keyed global rotation."""
        p = self.bones[b]["parent"]
        rest_rel = R(self.bones[p]["rest_quat"]).inv() * R(self.bones[b]["rest_quat"])
        pose_rel = R(quats[p]).inv() * R(quats[b])
        return rest_rel.inv() * pose_rel

    def place(self, t, dt=0.02):
        """Set both men to the keyed pose at t, with the keyed velocities."""
        d = self.d
        for m, man in enumerate(self.men):
            pos, q = self.target(m, t)
            pos2, q2 = self.target(m, t + dt)
            d.qpos[man["rq"]:man["rq"] + 3] = pos[0]
            d.qpos[man["rq"] + 3:man["rq"] + 7] = q_wxyz(q[0])
            d.qvel[man["rv"]:man["rv"] + 3] = (pos2[0] - pos[0]) / dt
            # Free joint angular velocity is in the body's local frame.
            w = (R(q[0]).inv() * R(q2[0])).as_rotvec() / dt
            d.qvel[man["rv"] + 3:man["rv"] + 6] = w
            for b, a in man["jq"].items():
                lt = self.local_target(q, b)
                lt2 = self.local_target(q2, b)
                d.qpos[a:a + 4] = q_wxyz(lt.as_quat())
                d.qvel[man["jv"][b]:man["jv"][b] + 3] = (lt.inv() * lt2).as_rotvec() / dt
        mujoco.mj_forward(self.model, d)

    def man_of(self, geom):
        b = self.model.geom_bodyid[geom]
        for m, man in enumerate(self.men):
            if b in man["bodies"]:
                return m
        return -1

    def run(self, report, until=None, launch=None):
        mo, d = self.model, self.d
        self.place(0.0)
        if launch is not None:
            # The jumper's take-off: extra speed (world) and spin (world axes) on top of the keyed.
            man = self.men[0]
            d.qvel[man["rv"]:man["rv"] + 3] += launch[:3]
            pel = man["body"][0]
            cur = Rot.from_quat([d.xquat[pel][1], d.xquat[pel][2], d.xquat[pel][3], d.xquat[pel][0]])
            d.qvel[man["rv"] + 3:man["rv"] + 6] += cur.inv().apply(launch[3:6])
        out = [[], []]
        steps = int(round(self.length / SIM_DT))
        every = int(round(1.0 / OUT_HZ / SIM_DT))
        log = {"pen": [], "help": [[], []], "air": [[], []], "err": [[], []]}
        for s in range(steps + 1):
            t = s * SIM_DT
            if until is not None and t >= until:
                man = self.men[0]
                pel = man["body"][0]
                pos, q = self.target(0, t)
                cur = Rot.from_quat([d.xquat[pel][1], d.xquat[pel][2], d.xquat[pel][3], d.xquat[pel][0]])
                ang = np.linalg.norm((cur.inv() * R(q[0])).as_rotvec())
                # The spine too: the chest's turn from the keyed one.
                ch = man["body"][3]
                cc = Rot.from_quat([d.xquat[ch][1], d.xquat[ch][2], d.xquat[ch][3], d.xquat[ch][0]])
                ang2 = np.linalg.norm((cc.inv() * R(q[3])).as_rotvec())
                return float(np.linalg.norm(d.xpos[pel] - pos[0]) + 0.3 * ang + 0.3 * ang2)
            d.xfrc_applied[:] = 0
            d.qfrc_applied[:] = 0
            contacts = self.contacts()
            for m, man in enumerate(self.men):
                rag = RAGDOLL.get(m)
                limp = rag is not None and t >= rag
                if limp and not man.get("limp"):
                    man["limp"] = True
                    for b, v in man["jv"].items():
                        mo.dof_damping[v:v + 3] *= LIMP
                pos, q = self.target(m, RAG_POSE.get(m, rag) if limp else t)
                pos2, q2 = (pos, q) if limp else self.target(m, t + 0.01)
                # Joints: pull each toward its keyed rotation (and keyed turning speed).
                for b, a in man["jq"].items():
                    cur = Rot.from_quat([d.qpos[a + 1], d.qpos[a + 2], d.qpos[a + 3], d.qpos[a]])
                    lt = self.local_target(q, b)
                    lt2 = self.local_target(q2, b)
                    err = (cur.inv() * lt).as_rotvec()
                    wv = (lt.inv() * lt2).as_rotvec() / 0.01
                    v = d.qvel[man["jv"][b]:man["jv"][b] + 3]
                    k = GAIN[kind(self.bones[b]["name"])] * (LIMP if limp else 1.0)
                    d.qfrc_applied[man["jv"][b]:man["jv"][b] + 3] = k * err + (k / 18.0) * wv
                if limp:
                    log["help"][m].append(0.0)
                else:
                    self.help(m, man, pos, q, pos2, q2, contacts[m], log)
            if s % every == 0:
                for m, man in enumerate(self.men):
                    fr = {"pos": [], "quat": []}
                    for i in self.keep:
                        bid = man["body"][i]
                        fr["pos"].append(d.xpos[bid].tolist())
                        w, x, y, z = d.xquat[bid]
                        fr["quat"].append([x, y, z, w])
                    out[m].append(fr)
                    pos, q = self.target(m, t)
                    log["err"][m].append(float(np.linalg.norm(d.xpos[man["body"][0]] - pos[0])))
                    log["air"][m].append(not contacts[m]["ground"] and not contacts[m]["other"])
                pen = 0.0
                for c in range(d.ncon):
                    con = d.contact[c]
                    ma, mb = self.man_of(con.geom1), self.man_of(con.geom2)
                    if ma >= 0 and mb >= 0 and ma != mb:
                        pen = min(pen, con.dist)
                log["pen"].append(pen)
            mujoco.mj_step(mo, d)
        self.report(log, report)
        return {"hz": OUT_HZ, "bones": [self.bones[i]["name"] for i in self.keep], "men": [{"frames": o} for o in out]}

    def contacts(self):
        d = self.d
        res = [{"ground": [], "other": []}, {"ground": [], "other": []}]
        for c in range(d.ncon):
            con = d.contact[c]
            n = np.array(con.frame[:3])   # from geom1 to geom2
            g1, g2 = con.geom1, con.geom2
            m1, m2 = self.man_of(g1), self.man_of(g2)
            for (ma, mb, gb, sign) in ((m1, m2, g2, -1.0), (m2, m1, g1, 1.0)):
                # sign: the normal pointing into man ma (away from what he touches).
                if ma < 0:
                    continue
                if mb < 0:
                    res[ma]["ground"].append((np.array(con.pos), n * sign))
                elif mb != ma:
                    res[ma]["other"].append((np.array(con.pos), n * sign, self.model.geom_bodyid[gb]))
        return res

    def help(self, m, man, pos, q, pos2, q2, con, log):
        """The contact-backed help at his hips (see the module note)."""
        d = self.d
        pel = man["body"][0]
        if not con["ground"] and not con["other"]:
            log["help"][m].append(0.0)
            return
        mass = man["mass"]
        p = d.xpos[pel]
        v = d.cvel[pel][3:] if False else d.qvel[man["rv"]:man["rv"] + 3]
        vt = (pos2[0] - pos[0]) / 0.01
        want = mass * (ROOT_KP * (pos[0] - p) + ROOT_KD * (vt - v) + np.array([0.0, 9.81, 0.0]))
        normals = [c[1] for c in con["ground"]] + [c[1] for c in con["other"]]
        n = np.sum(normals, axis=0)
        n /= max(np.linalg.norm(n), 1e-9)
        # Inside the friction cone about the contacts' normal; never pulling into the contact.
        fn = float(np.dot(want, n))
        if fn <= 0.0:
            log["help"][m].append(0.0)
            return
        ft = want - fn * n
        lim = MU * fn
        if np.linalg.norm(ft) > lim:
            ft *= lim / np.linalg.norm(ft)
        f = fn * n + ft
        # Off the ground he can push on the other man about one and a half times his weight
        # (legs driving, a grip); from the turf, his legs can push far harder.
        cap = (2.6 if con["ground"] else 1.4) * mass * 9.81
        if np.linalg.norm(f) > cap:
            f *= cap / np.linalg.norm(f)
        cur = Rot.from_quat([d.xquat[pel][1], d.xquat[pel][2], d.xquat[pel][3], d.xquat[pel][0]])
        w = (R(q[0]).inv() * R(q2[0])).as_rotvec() / 0.01
        wcur = d.qvel[man["rv"] + 3:man["rv"] + 6]
        tl = (ROOT_ROT_KP * (cur.inv() * R(q[0])).as_rotvec() + ROOT_ROT_KD * (w - wcur)) * mass * 0.3
        tau = cur.apply(tl)
        if np.linalg.norm(tau) > ROOT_TORQUE_CAP:
            tau *= ROOT_TORQUE_CAP / np.linalg.norm(tau)
        d.xfrc_applied[pel][:3] += f
        d.xfrc_applied[pel][3:] += tau
        log["help"][m].append(float(np.linalg.norm(f)))
        if DEBUG and m == DEBUG_MAN and int(round(self.d.time * 1000)) % 40 == 0:
            print("DBG t=%.2f ang_err=%.0f deg tau=%.0f f=%.0f want=%.0f n=%s other=%d ground=%d" % (
                self.d.time, np.degrees(np.linalg.norm((cur.inv() * R(q[0])).as_rotvec())), np.linalg.norm(tau),
                np.linalg.norm(f), np.linalg.norm(want), np.round(n, 2), len(con["other"]), len(con["ground"])))
        # The other man takes the equal and opposite push, shared over the bodies touched,
        # at the touching points (ground contacts push the earth, which does not move).
        share = len(con["other"]) / float(len(con["other"]) + len(con["ground"]))
        if con["other"]:
            k = len(con["other"])
            for (pt, nn, body) in con["other"]:
                fb = -f * share / k
                d.xfrc_applied[body][:3] += fb
                d.xfrc_applied[body][3:] += np.cross(pt - d.xipos[body], fb) - tau * share / k

    def report(self, log, path):
        lines = []
        pen = np.array(log["pen"])
        lines.append("deepest overlap between the men: %.1f cm (frame %d)" % (-100 * pen.min(), int(pen.argmin())))
        for m in range(2):
            air = log["air"][m]
            runs = []
            st = None
            for i, a in enumerate(air + [False]):
                if a and st is None:
                    st = i
                if not a and st is not None:
                    runs.append((st, i - 1))
                    st = None
            err = np.array(log["err"][m])
            lines.append("man %d: in the air frames %s; hips off the keyed path: mean %.1f cm, worst %.1f cm (frame %d)"
                         % (m, runs, 100 * err.mean(), 100 * err.max(), int(err.argmax())))
        txt = "\n".join(lines)
        print(txt)
        if path:
            open(path, "w").write(txt + "\n")


def main():
    a = sys.argv[1:]
    report = a[a.index("--report") + 1] if "--report" in a else ""
    data_in = json.load(open(a[0]))
    p = Pair(data_in)
    launch = None
    if "--launch" in a:
        # A take-off solved before (LAUNCH BEST's six numbers), to skip solving it again.
        launch = np.array([float(v) for v in a[a.index("--launch") + 1].split(",")])
    elif "--launch-until" in a:
        # Solve the jumper's take-off (speed and spin) so he arrives at the keyed place and
        # posture just before he first touches the stepladder: what a real take-off chooses.
        from scipy.optimize import minimize
        until = float(a[a.index("--launch-until") + 1])

        def cost(x):
            p.d = mujoco.MjData(p.model)
            c = p.run("", until=until, launch=np.array([x[0], x[1], x[2], x[3], 0.0, x[4]]))
            print("LAUNCH %s -> %.3f" % (np.round(x, 2), c), flush=True)
            return c
        r = minimize(cost, np.zeros(5), method="Nelder-Mead",
                     options={"maxfev": int(os.environ.get("LAUNCH_EVALS", "45")), "initial_simplex": np.vstack([np.zeros(5), np.diag([0.8, 0.8, 0.8, 2.5, 2.5])]), "xatol": 0.05, "fatol": 0.005})
        launch = np.array([r.x[0], r.x[1], r.x[2], r.x[3], 0.0, r.x[4]])
        print("LAUNCH BEST %s cost %.3f" % (np.round(launch, 2), r.fun))
        p.d = mujoco.MjData(p.model)
    out = p.run(report, launch=launch)
    json.dump(out, open(a[1], "w"))


if __name__ == "__main__":
    main()
