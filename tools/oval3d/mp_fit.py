#!/usr/bin/env python3
"""Fit a footballer's skeleton to a tracked film: the joints of every frame in 3D.

MediaPipe's 3D landmarks guess depth from one picture and read our own overhead mark 10-25 deg out
at the elbows and shoulders (tools/oval3d/mp_roundtrip.py), while its 2D points sit within 1-2% of
his height. So the fit trusts the picture and uses the 3D guess only to choose which way a limb
points into the screen:

- each joint, drawn through the film camera (orthographic: the broadcast lens is long, and his
  depth is small next to the distance), lands on its 2D point, weighted by how sure the tracker is;
- every bone keeps its own length (the skeleton's);
- the 3D guess pulls weakly, so depth that the picture cannot tell keeps its guessed side;
- joints move smoothly from frame to frame.

    python3 tools/oval3d/mp_fit.py FRAMES_DIR MODEL.task BONES.json OUT.json
    python3 tools/oval3d/mp_fit.py --track TRACK.json BONES.json OUT.json   (broadcast footage)

BONES.json: {"bone": length_m} for the pairs in BONES below (render_clip.gd's joints.json can give
them: tools/oval3d/mp_fit.py --bones joints.json). OUT.json: {"hz", "frames": [{joint: [x, y, z]}]}
in metres, y up, x across the picture, z toward the camera.
"""
import glob
import json
import os
import sys

import mediapipe as mp
import numpy as np
from scipy.optimize import least_squares
from scipy.sparse import lil_matrix

J = ["shoulder_l", "shoulder_r", "elbow_l", "elbow_r", "wrist_l", "wrist_r",
     "hip_l", "hip_r", "knee_l", "knee_r", "ankle_l", "ankle_r",
     "nose", "ear_l", "ear_r", "toe_l", "heel_l", "toe_r", "heel_r"]
MP = {"shoulder_l": 11, "shoulder_r": 12, "elbow_l": 13, "elbow_r": 14, "wrist_l": 15, "wrist_r": 16,
      "hip_l": 23, "hip_r": 24, "knee_l": 25, "knee_r": 26, "ankle_l": 27, "ankle_r": 28,
      "nose": 0, "ear_l": 7, "ear_r": 8, "toe_l": 31, "heel_l": 29, "toe_r": 32, "heel_r": 30}
MH = {"shoulder_l": "upperarm_l", "shoulder_r": "upperarm_r", "elbow_l": "lowerarm_l",
      "elbow_r": "lowerarm_r", "wrist_l": "hand_l", "wrist_r": "hand_r", "hip_l": "thigh_l",
      "hip_r": "thigh_r", "knee_l": "calf_l", "knee_r": "calf_r", "ankle_l": "foot_l", "ankle_r": "foot_r"}
BONES = [("shoulder_l", "elbow_l"), ("elbow_l", "wrist_l"), ("shoulder_r", "elbow_r"),
         ("elbow_r", "wrist_r"), ("hip_l", "knee_l"), ("knee_l", "ankle_l"), ("hip_r", "knee_r"),
         ("knee_r", "ankle_r"), ("shoulder_l", "shoulder_r"), ("hip_l", "hip_r"),
         ("shoulder_l", "hip_l"), ("shoulder_r", "hip_r"),
         # The head and the feet are rigid: they give the head's turn and the feet's point.
         ("ear_l", "ear_r"), ("nose", "ear_l"), ("nose", "ear_r"),
         ("ankle_l", "heel_l"), ("ankle_l", "toe_l"), ("heel_l", "toe_l"),
         ("ankle_r", "heel_r"), ("ankle_r", "toe_r"), ("heel_r", "toe_r")]
W_PRIOR = 0.15    # pull of the tracker's 3D guess, against 1.0 for the picture
W_SMOOTH = 0.5    # frame-to-frame steadiness (on acceleration)
W_BONE = 4.0      # bone lengths held
W_SIZE = float(os.environ.get("FIT_W_SIZE", "0"))
W_PEN = 6.0       # two men's limbs kept from passing through each other
FIT_UNIT = float(os.environ.get("FIT_UNIT", "1.29"))   # metres per fit unit (the bake's BAKE_SCALE)
# Each man's body as capsules for the pair's no-passing-through term: (joint ends, radius in
# metres). The trunk runs from the shoulders' middle to the hips'; the head is a ball at the ears'
# middle. Radii are a footballer's flesh, kit included.
CAPS = [((("shoulder_l", "shoulder_r"), ("hip_l", "hip_r")), 0.14),
        ((("ear_l", "ear_r"), ("ear_l", "ear_r")), 0.11),
        ((("hip_l",), ("knee_l",)), 0.08), ((("hip_r",), ("knee_r",)), 0.08),
        ((("knee_l",), ("ankle_l",)), 0.055), ((("knee_r",), ("ankle_r",)), 0.055),
        ((("shoulder_l",), ("elbow_l",)), 0.05), ((("shoulder_r",), ("elbow_r",)), 0.05),
        ((("elbow_l",), ("wrist_l",)), 0.04), ((("elbow_r",), ("wrist_r",)), 0.04)]
KNEE_ON_BACK = 0.02   # metres of kit squashed where the knee rests on the back   # each man's bones together held to BONES.json


def bones_from_truth(joints_json):
    t = json.load(open(joints_json))
    out = {}
    for a, b in BONES:
        if a not in MH or b not in MH:
            continue
        ls = [np.linalg.norm(np.array(f[MH[a]]) - np.array(f[MH[b]])) for f in t["frames"]]
        out[f"{a}-{b}"] = float(np.median(ls))
    return out


def track(frames_dir, model, hz):
    files = sorted(glob.glob(os.path.join(frames_dir, "f_*.png")))
    opts = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=model),
        running_mode=mp.tasks.vision.RunningMode.VIDEO, num_poses=1)
    p2, p3, vis = [], [], []
    size = None
    with mp.tasks.vision.PoseLandmarker.create_from_options(opts) as lm:
        for n, f in enumerate(files):
            img = mp.Image.create_from_file(f)
            size = (img.width, img.height)
            r = lm.detect_for_video(img, int(n * 1000.0 / hz))
            if not r.pose_landmarks:
                p2.append(None); p3.append(None); vis.append(None)
                continue
            a = r.pose_landmarks[0]
            w = r.pose_world_landmarks[0]
            # Pixels, y up; the 3D guess with y up and z toward the camera.
            p2.append(np.array([[a[MP[j]].x * img.width, -a[MP[j]].y * img.height] for j in J]))
            p3.append(np.array([[w[MP[j]].x, -w[MP[j]].y, -w[MP[j]].z] for j in J]))
            vis.append(np.array([max(0.05, a[MP[j]].visibility) for j in J]))
    return p2, p3, vis, size


def fit(p2, p3, vis, bones, contact=None, multi=False, stable=False):
    """Fit one man (p2, p3, vis: per frame, or None) or several filmed together (lists of those,
    one per man): the men share each frame's camera, so where they stand against each other comes
    from the picture. contact: (frames, weight) pulling the first man's knees to the depth of the
    second man's trunk in those frames (a speccy's knee in the back)."""
    men = list(zip(p2, p3, vis)) if multi else [(p2, p3, vis)]
    Pn = len(men)
    nfr = len(men[0][0])
    keep = [i for i in range(nfr) if all(m[0][i] is not None for m in men)]
    F = len(keep)
    n = len(J)
    N = Pn * n
    P2 = np.concatenate([np.stack([m[0][i] for i in keep]) for m in men], 1)
    # Frames with no 3D guess (the broadcast lift can miss) start from the nearest frame's guess
    # and get no pull from it: their depth comes from their neighbours and the bone lengths.
    P3s, M3s = [], []
    for m in men:
        has3 = [i for i in keep if m[1][i] is not None]
        P3s.append(np.stack([m[1][i] if m[1][i] is not None else m[1][min(has3, key=lambda h: abs(h - i))] for i in keep]))
        M3s.append(np.array([1.0 if m[1][i] is not None else 0.0 for i in keep]))
    V = np.concatenate([np.stack([m[2][i] for i in keep]) for m in men], 1)
    # Scale and offset of each frame's picture (orthographic camera), from the first man's 2D
    # spread against his 3D guess's: a start the solve refines.
    A2, A3 = P2[:, :n], P3s[0]
    s0 = np.array([np.linalg.norm(A2[f] - A2[f].mean(0)) / max(1e-6, np.linalg.norm(A3[f, :, :2] - A3[f, :, :2].mean(0))) for f in range(F)])
    # Each man starts where the picture puts his hips, at the same depth.
    X0 = []
    for k, P3 in enumerate(P3s):
        hip2 = P2[:, k * n + 6:k * n + 8].mean(1)
        X0.append(P3 - P3[:, 6:8].mean(1, keepdims=True) + np.concatenate([hip2 / s0[:, None], np.zeros((F, 1))], 1)[:, None, :])
    X0 = np.concatenate(X0, 1)
    t0 = np.zeros((F, 2))
    bi = [(J.index(a), J.index(b)) for a, b in BONES]
    nb = len(bi)
    # The tracker's points are not the skeleton's joints (its shoulder sits on the skin, ours in
    # the socket), so each man finds his own bone lengths, one set for all his frames, started
    # from the 3D guess. Held fixed to the skeleton's they bent his knees 30-40 deg too far.
    bl0 = np.concatenate([[np.median(np.linalg.norm(P3[:, a] - P3[:, b], axis=1)) for a, b in bi] for P3 in P3s])
    # Overall size: the picture cannot tell a big man far off from a small one near, and the
    # steadiness terms favour shrinking him, so each man's bones together are held to our body's
    # (BONES.json) or, without it, to the 3D guess's.
    ref = np.array([bones.get(f"{a}-{b}", bl0[q]) for q, (a, b) in enumerate(BONES)]) if bones else bl0[:nb]
    bl0 = np.concatenate([bl0[k * nb:(k + 1) * nb] * (ref.sum() / max(1e-6, bl0[k * nb:(k + 1) * nb].sum())) for k in range(Pn)])
    x0 = np.concatenate([X0.reshape(-1), s0, t0.reshape(-1), bl0])
    px = float(np.median(s0))   # pixels per metre, to put the picture's error in metres
    Pc = np.concatenate([P3 - P3[:, 6:8].mean(1, keepdims=True) for P3 in P3s], 1)
    M3 = np.stack(M3s, 1)     # (F, men)
    cf = np.zeros(F)
    if contact:
        frs, wc = contact
        for k, i in enumerate(keep):
            if i in frs:
                cf[k] = wc

    def unpack(x):
        X = x[:F * N * 3].reshape(F, N, 3)
        s = x[F * N * 3:F * N * 3 + F]
        t = x[F * N * 3 + F:F * N * 3 + 3 * F].reshape(F, 2)
        bl = x[F * N * 3 + 3 * F:]
        return X, s, t, bl

    def res(x):
        X, s, t, bl = unpack(x)
        r_img = ((s[:, None, None] * X[:, :, :2] + t[:, None, :] - P2) / px) * np.sqrt(V)[:, :, None]
        # The guess pulls each joint's place about his own hips, not his place on the screen.
        Xc = np.concatenate([X[:, k * n:(k + 1) * n] - X[:, k * n + 6:k * n + 8].mean(1, keepdims=True) for k in range(Pn)], 1)
        r_pri = (Xc - Pc) * W_PRIOR * np.repeat(M3, n, 1)[:, :, None]
        r_bone = np.stack([np.linalg.norm(X[:, k * n + a] - X[:, k * n + b], axis=1) - bl[k * nb + q]
                           for k in range(Pn) for q, (a, b) in enumerate(bi)], 1) * W_BONE
        # Steadiness on acceleration, not speed: a pull on speed holds him still and shrinks
        # him (a smaller man moves less), which bent his limbs into the screen to keep their length.
        r_sm = (X[2:] - 2 * X[1:-1] + X[:-2]) * W_SMOOTH if F > 2 else np.zeros((0, N, 3))
        # The camera's zoom changes slowly.
        r_s = np.diff(s) / px * 5.0
        if stable:
            # Picture already steadied (track_broadcast.py stabilize): one camera for the clip,
            # so his travel and his leap stay his, not the camera's.
            r_s = np.concatenate([np.diff(s) / px * 200.0, np.diff(t, axis=0).ravel() / px * 200.0])
        r_size = np.array([bl[k * nb:(k + 1) * nb].sum() - ref.sum() for k in range(Pn)]) * W_SIZE
        out = [r_img.ravel(), r_pri.ravel(), r_bone.ravel(), r_sm.ravel(), r_s, r_size]
        if Pn > 1:
            # No limb of one man through the other's (capsules, sampled along each).
            ends = lambda k, e: X[:, [k * n + J.index(j) for j in e]].mean(1)
            seg = [[(ends(k, a), ends(k, b), r / FIT_UNIT) for (a, b), r in CAPS] for k in range(2)]
            u = np.linspace(0.0, 1.0, 5)[None, :, None]
            for a0, a1, ra in seg[0]:
                pa = a0[:, None] + (a1 - a0)[:, None] * u
                for b0, b1, rb in seg[1]:
                    pb = b0[:, None] + (b1 - b0)[:, None] * u
                    d = np.linalg.norm(pa[:, :, None] - pb[:, None], axis=3).min((1, 2))
                    out.append(np.maximum(0.0, ra + rb - d) * W_PEN)
            # In the contact frames his nearer knee rests on the other man's back: on the trunk's
            # skin, not in it.
            t0_, t1_, rt = seg[1][0]
            ax = t1_ - t0_
            dk = [np.linalg.norm((X[:, kn] - t0_) - ax * np.clip(((X[:, kn] - t0_) * ax).sum(1) / np.maximum(1e-9, (ax * ax).sum(1)), 0, 1)[:, None], axis=1) for kn in (8, 9)]
            out.append((np.minimum(dk[0], dk[1]) - (rt + (0.055 - KNEE_ON_BACK) / FIT_UNIT)) * cf)
        return np.concatenate(out)

    # Which unknowns each residual touches: without it the solver differences every unknown for
    # every residual, and a 70-frame broadcast clip takes over ten minutes.
    nX = F * N * 3
    xi = lambda f, j, c: (f * N + j) * 3 + c
    si = lambda f: nX + f
    ti = lambda f, c: nX + F + f * 2 + c
    bli = lambda k: nX + 3 * F + k
    rows = []
    for f in range(F):
        for j in range(N):
            for c in range(2):
                rows.append([xi(f, j, c), si(f), ti(f, c)])
    for f in range(F):
        for j in range(N):
            h = (j // n) * n
            for c in range(3):
                rows.append([xi(f, j, c), xi(f, h + 6, c), xi(f, h + 7, c)])
    for f in range(F):
        for k in range(Pn):
            for q, (a, b) in enumerate(bi):
                rows.append([xi(f, k * n + a, c) for c in range(3)] + [xi(f, k * n + b, c) for c in range(3)] + [bli(k * nb + q)])
    for f in range(F - 2):
        for j in range(N):
            for c in range(3):
                rows.append([xi(f, j, c), xi(f + 1, j, c), xi(f + 2, j, c)])
    for f in range(F - 1):
        rows.append([si(f), si(f + 1)])
    if stable:
        for f in range(F - 1):
            for c in range(2):
                rows.append([ti(f, c), ti(f + 1, c)])
    for k in range(Pn):
        rows.append([bli(k * nb + q) for q in range(nb)])
    if Pn > 1:
        jl = lambda k, e: [xi(f, k * n + J.index(j), c) for j in e for c in range(3)]
        for (a, b), _ in CAPS:
            for (c_, d_), _ in CAPS:
                for f in range(F):
                    rows.append(jl(0, a) + jl(0, b) + jl(1, c_) + jl(1, d_))
        for f in range(F):
            rows.append([xi(f, kn, c) for kn in (8, 9) for c in range(3)] + jl(1, ("shoulder_l", "shoulder_r", "hip_l", "hip_r")))
    sp = lil_matrix((len(rows), len(x0)), dtype=int)
    for r, cols in enumerate(rows):
        for c in cols:
            sp[r, c] = 1
    sol = least_squares(res, x0, method="trf", x_scale="jac", max_nfev=200, jac_sparsity=sp)
    X, s, t, bl = unpack(sol.x)
    outs = []
    for k in range(Pn):
        out = [None] * nfr
        for q, i in enumerate(keep):
            out[i] = {j: X[q, k * n + m].tolist() for m, j in enumerate(J)}
        outs.append(out)
    return outs[0] if not multi else outs


def from_track(path):
    """A track from tools/oval3d/track_broadcast.py (follow, then lift) in track()'s form."""
    T = json.load(open(path))
    p2, p3, vis = [], [], []
    for f in T["frames"]:
        p2.append(np.array(f["p2"]) if f else None)
        p3.append(np.array(f["p3"]) if f and f.get("lift", 1.0) is not None else None)
        vis.append(np.array(f["vis"]) if f else None)
    return p2, p3, vis, float(T["hz"])


def main():
    if sys.argv[1] == "--bones":
        print(json.dumps(bones_from_truth(sys.argv[2]), indent=1))
        return
    global BONES_BODY
    BONES_BODY = None
    if sys.argv[1] == "--pair" and os.environ.get("FIT_BONES"):
        BONES_BODY = json.load(open(os.environ["FIT_BONES"]))
    if sys.argv[1] == "--pair":
        # FIT_BONES=BONES.json python3 tools/oval3d/mp_fit.py --pair JUMPER.json STEPLADDER.json OUT.json [FIRST:LAST]
        # Both men in one solve, sharing the camera; FIRST:LAST: frames where his knee is in the
        # other's back.
        a, b = from_track(sys.argv[2]), from_track(sys.argv[3])
        # Where both tracks took the same man (they cross at the contact), the one who jumped
        # furthest from his own neighbouring frames is the wrong one: his frame is filled from
        # those neighbours and trusted little.
        for i in range(1, len(a[0]) - 1):
            pa, pb = a[0][i], b[0][i]
            if pa is None or pb is None:
                continue
            trunk = np.linalg.norm(pa[[0, 1]].mean(0) - pa[[6, 7]].mean(0))
            if np.median(np.linalg.norm(pa[:12] - pb[:12], axis=1)) > 0.25 * trunk:
                continue
            for m in (a, b):
                if m[0][i - 1] is None or m[0][i + 1] is None:
                    continue
            jump = [np.linalg.norm(m[0][i][6:8].mean(0) - (m[0][i - 1][6:8].mean(0) + m[0][i + 1][6:8].mean(0)) / 2)
                    if m[0][i - 1] is not None and m[0][i + 1] is not None else 0.0 for m in (a, b)]
            m = (a, b)[int(np.argmax(jump))]
            m[0][i] = (m[0][i - 1] + m[0][i + 1]) / 2
            m[2][i] = np.full(len(J), 0.05)
            print(f"FIT pair: frame {i}, both tracks on one man; {'jumper' if m is a else 'stepladder'} filled in")
        contact = None
        if len(sys.argv) > 5:
            c0, c1 = map(int, sys.argv[5].split(":"))
            contact = (set(range(c0, c1 + 1)), 2.0)
        stable = json.load(open(sys.argv[2])).get("stable", False)
        fj, fs = fit((a[0], b[0]), (a[1], b[1]), (a[2], b[2]), BONES_BODY, contact=contact, multi=True, stable=stable)
        json.dump({"hz": a[3], "frames": fj, "stepladder": fs}, open(sys.argv[4], "w"))
        print(f"FIT pair {len([f for f in fj if f])} frames -> {sys.argv[4]}")
        return
    if sys.argv[1] == "--track":
        # python3 tools/oval3d/mp_fit.py --track TRACK.json BONES.json OUT.json
        p2, p3, vis, hz = from_track(sys.argv[2])
        frames = fit(p2, p3, vis, json.load(open(sys.argv[3])))
        json.dump({"hz": hz, "frames": frames}, open(sys.argv[4], "w"))
        print(f"FIT {len([f for f in frames if f])} of {len(frames)} frames -> {sys.argv[4]}")
        return
    frames_dir, model, bones_path, out_path = sys.argv[1:5]
    hz = 30.0
    jj = os.path.join(frames_dir, "joints.json")
    if os.path.exists(jj):
        hz = float(json.load(open(jj))["hz"])
    p2, p3, vis, _ = track(frames_dir, model, hz)
    frames = fit(p2, p3, vis, json.load(open(bones_path)))
    json.dump({"hz": hz, "frames": frames}, open(out_path, "w"))
    print(f"FIT {len([f for f in frames if f])} of {len(frames)} frames -> {out_path}")


if __name__ == "__main__":
    main()
