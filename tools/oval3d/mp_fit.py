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
     "hip_l", "hip_r", "knee_l", "knee_r", "ankle_l", "ankle_r"]
MP = {"shoulder_l": 11, "shoulder_r": 12, "elbow_l": 13, "elbow_r": 14, "wrist_l": 15, "wrist_r": 16,
      "hip_l": 23, "hip_r": 24, "knee_l": 25, "knee_r": 26, "ankle_l": 27, "ankle_r": 28}
MH = {"shoulder_l": "upperarm_l", "shoulder_r": "upperarm_r", "elbow_l": "lowerarm_l",
      "elbow_r": "lowerarm_r", "wrist_l": "hand_l", "wrist_r": "hand_r", "hip_l": "thigh_l",
      "hip_r": "thigh_r", "knee_l": "calf_l", "knee_r": "calf_r", "ankle_l": "foot_l", "ankle_r": "foot_r"}
BONES = [("shoulder_l", "elbow_l"), ("elbow_l", "wrist_l"), ("shoulder_r", "elbow_r"),
         ("elbow_r", "wrist_r"), ("hip_l", "knee_l"), ("knee_l", "ankle_l"), ("hip_r", "knee_r"),
         ("knee_r", "ankle_r"), ("shoulder_l", "shoulder_r"), ("hip_l", "hip_r"),
         ("shoulder_l", "hip_l"), ("shoulder_r", "hip_r")]
W_PRIOR = 0.15    # pull of the tracker's 3D guess, against 1.0 for the picture
W_SMOOTH = 0.5    # frame-to-frame steadiness
W_BONE = 4.0      # bone lengths held


def bones_from_truth(joints_json):
    t = json.load(open(joints_json))
    out = {}
    for a, b in BONES:
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


def fit(p2, p3, vis, bones):
    keep = [i for i, x in enumerate(p2) if x is not None]
    F = len(keep)
    n = len(J)
    P2 = np.stack([p2[i] for i in keep])
    P3 = np.stack([p3[i] for i in keep])
    V = np.stack([vis[i] for i in keep])
    # Scale and offset of each frame's picture (orthographic camera), from the 2D points' spread
    # against the 3D guess's: a start the solve refines.
    s0 = np.array([np.linalg.norm(P2[f] - P2[f].mean(0)) / max(1e-6, np.linalg.norm(P3[f, :, :2] - P3[f, :, :2].mean(0))) for f in range(F)])
    t0 = P2.mean(1) - s0[:, None] * P3[:, :, :2].mean(1)
    bi = [(J.index(a), J.index(b)) for a, b in BONES]
    # The tracker's points are not the skeleton's joints (its shoulder sits on the skin, ours in
    # the socket), so the clip finds its own bone lengths, one set for all its frames, started
    # from the 3D guess. Held fixed to the skeleton's they bent his knees 30-40 deg too far.
    bl0 = np.array([np.median(np.linalg.norm(P3[:, a] - P3[:, b], axis=1)) for a, b in bi])
    x0 = np.concatenate([P3.reshape(-1), s0, t0.reshape(-1), bl0])
    px = float(np.median(s0))   # pixels per metre, to put the picture's error in metres

    def unpack(x):
        X = x[:F * n * 3].reshape(F, n, 3)
        s = x[F * n * 3:F * n * 3 + F]
        t = x[F * n * 3 + F:F * n * 3 + 3 * F].reshape(F, 2)
        bl = x[F * n * 3 + 3 * F:]
        return X, s, t, bl

    def res(x):
        X, s, t, bl = unpack(x)
        r_img = ((s[:, None, None] * X[:, :, :2] + t[:, None, :] - P2) / px) * np.sqrt(V)[:, :, None]
        # The guess pulls each joint's place about his hips, not his place on the screen.
        Xc = X - X[:, 6:8].mean(1, keepdims=True)
        Pc = P3 - P3[:, 6:8].mean(1, keepdims=True)
        r_pri = (Xc - Pc) * W_PRIOR
        r_bone = np.stack([np.linalg.norm(X[:, a] - X[:, b], axis=1) - bl[k] for k, (a, b) in enumerate(bi)], 1) * W_BONE
        r_sm = (X[1:] - X[:-1]) * W_SMOOTH if F > 1 else np.zeros((0, n, 3))
        # The camera's zoom changes slowly.
        r_s = np.diff(s) / px * 5.0
        return np.concatenate([r_img.ravel(), r_pri.ravel(), r_bone.ravel(), r_sm.ravel(), r_s])

    sol = least_squares(res, x0, method="trf", x_scale="jac", max_nfev=200)
    X, s, t, bl = unpack(sol.x)
    out = [None] * len(p2)
    for k, i in enumerate(keep):
        out[i] = {j: X[k, m].tolist() for m, j in enumerate(J)}
    return out


def main():
    if sys.argv[1] == "--bones":
        print(json.dumps(bones_from_truth(sys.argv[2]), indent=1))
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
