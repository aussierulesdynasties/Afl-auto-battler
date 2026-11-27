"""Find whole gait cycles in a 100STYLE take, for retarget_bvh.py's START:FRAMES.

  python3 gait_cycles.py STYLE_DIR/Neutral_FW.bvh F|B|S [START STOP] [SWING_M_S]

A cycle runs from one lift of a foot to its next lift, the other foot lifting once between. It
must be straight (the body turns under 10 degrees), carry him the asked way against his facing
(F ahead within 12 degrees, B behind, S side-on within 20), and its first and last poses must
match (every joint's turn between them, mean and largest). The best few are printed:
start, frames, seconds, pose error, pace, turn, way. STOP/START default to the whole take
(100STYLE's Frame_Cuts.csv gives each take's usable span); SWING_M_S is the ankle speed a
lifted foot passes (0.25 for walks, 0.4 for runs).
"""
import sys

import numpy as np
from scipy.spatial.transform import Rotation as Rot


def load(path):
    head, mot = open(path).read().split("MOTION")
    names, parents, offs, chans, stack, last = [], [], [], [], [], -1
    toks = head.split()
    i = 0
    while i < len(toks):
        t = toks[i]
        if t in ("ROOT", "JOINT"):
            names.append(toks[i + 1]); parents.append(stack[-1] if stack else -1); last = len(names) - 1; i += 2
        elif t == "End":
            names.append(names[last] + "_end"); parents.append(stack[-1]); last = len(names) - 1; chans.append([]); i += 2
        elif t == "{":
            stack.append(last); i += 1
        elif t == "}":
            stack.pop(); i += 1
        elif t == "OFFSET":
            offs.append([float(x) for x in toks[i + 1:i + 4]]); i += 4
        elif t == "CHANNELS":
            n = int(toks[i + 1]); chans.append(toks[i + 2:i + 2 + n]); i += 2 + n
        else:
            i += 1
    lines = mot.strip().split("\n")
    nf, ft = int(lines[0].split()[1]), float(lines[1].split()[2])
    data = np.array([[float(x) for x in l.split()] for l in lines[2:2 + nf]])
    return dict(names=names, parents=parents, offs=np.array(offs), chans=chans, data=data, ft=ft)


def fk(b):
    d = b["data"]
    nj, F = len(b["names"]), len(d)
    P, R, c = np.zeros((F, nj, 3)), [None] * nj, 0
    for j in range(nj):
        ch = b["chans"][j]
        p = None
        if ch:
            vals = d[:, c:c + len(ch)]; c += len(ch)
            rc = [k for k in ch if k.endswith("rotation")]
            r = Rot.from_euler("".join(k[0] for k in rc), vals[:, [ch.index(k) for k in rc]], degrees=True)
            pc = [ch.index(k) for k in ch if k.endswith("position")]
            p = vals[:, pc] if pc else None
        else:
            r = Rot.identity(F)
        par = b["parents"][j]
        if par < 0:
            R[j] = r; P[:, j] = p if p is not None else b["offs"][j]
        else:
            P[:, j] = P[:, par] + R[par].apply(b["offs"][j] if p is None else p); R[j] = R[par] * r
    return P


def main():
    path, want = sys.argv[1], sys.argv[2]
    b = load(path)
    P, n, ft = fk(b), b["names"], b["ft"]
    a0 = int(sys.argv[3]) if len(sys.argv) > 4 else 0
    e0 = int(sys.argv[4]) if len(sys.argv) > 4 else len(P) - 1
    thr = float(sys.argv[5]) if len(sys.argv) > 5 else 0.25
    lifts = {}
    for s in ("Left", "Right"):
        A = P[:, n.index(s + "Ankle"), :][:, [0, 2]] / 100
        sp = np.r_[0, np.linalg.norm(np.diff(A, axis=0), axis=1) / ft]
        m = sp > thr
        lifts[s] = [i for i in range(a0 + 1, e0) if m[i] and not m[i - 1]]
    hips = P[:, 0][:, [0, 2]] / 100
    across = P[:, n.index("RightHip")][:, [0, 2]] - P[:, n.index("LeftHip")][:, [0, 2]]
    across /= np.linalg.norm(across, axis=1, keepdims=True)
    fwd = np.stack([-across[:, 1], across[:, 0]], 1)
    toe = P[:, n.index("LeftToe")][:, [0, 2]] - P[:, n.index("LeftAnkle")][:, [0, 2]]
    if np.mean(np.sum(fwd * toe, 1)) < 0:
        fwd = -fwd
    d, c, Q = b["data"], 6, []
    for j in range(1, len(n)):
        ch = b["chans"][j]
        if ch:
            Q.append(Rot.from_euler("".join(x[0] for x in ch), d[:, c:c + 3], degrees=True).as_quat()); c += 3
    Q = np.stack(Q, 1)
    res = []
    for lead, other in (("Left", "Right"), ("Right", "Left")):
        st = lifts[lead]
        for i in range(len(st) - 1):
            s, t = st[i], st[i + 1]
            if not 0.4 < (t - s) * ft < 1.6 or sum(1 for x in lifts[other] if s < x < t) != 1:
                continue
            v, f = hips[t] - hips[s], fwd[s]
            dist = np.linalg.norm(v)
            if dist < 0.1:
                continue
            way = np.degrees(np.arctan2(f[0] * v[1] - f[1] * v[0], f @ v))
            if (want == "S" and abs(abs(way) - 90) > 20) or (want == "F" and abs(way) > 12) \
                    or (want == "B" and abs(abs(way) - 180) > 12):
                continue
            turn = abs(np.degrees(np.angle(np.exp(1j * (np.arctan2(fwd[t, 1], fwd[t, 0]) - np.arctan2(f[1], f[0]))))))
            if turn > 10:
                continue
            seg = np.linalg.norm(np.diff(hips[s:t + 1], axis=0), axis=1) / ft
            err = np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(Q[s] * Q[t], -1)), 0, 1)))
            res.append((err.mean() + turn * 0.3 + seg.std() / seg.mean() * 10, s, t - s, err.mean(), err.max(),
                        dist / ((t - s) * ft), turn, way, lead))
    res.sort()
    for x in res[:6]:
        print("start %d frames %d (%.2f s) pose error mean %.1f max %.1f deg, %.2f m/s, turn %.1f deg, way %+.0f deg, %s foot first"
              % (x[1], x[2], x[2] * ft, x[3], x[4], x[5], x[6], x[7], x[8]))


main()
