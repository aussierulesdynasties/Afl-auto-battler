#!/usr/bin/env python3
"""Prove the video-to-motion tracker on our own motion before it is trusted on broadcast footage.

tools/oval3d/render_clip.gd films a clip and writes the true joints of every frame. This runs
Google's MediaPipe Pose Landmarker (Apache 2.0, model card "BlazePose GHUM 3D") on the frames and
compares the joint angles it reads with the true ones: elbows, knees, hips (trunk to thigh) and
shoulders (trunk to upper arm), each side. A tracker that reads our own clean, single-man film
badly will read a broadcast speccy worse, so this is the floor.

    python3 tools/oval3d/mp_roundtrip.py FRAMES_DIR MODEL.task [OUT.json]

Prints one ROUNDTRIP line per angle (median, p90, worst error in degrees, and the frames where the
tracker swapped his left and right) and writes the tracked world landmarks to OUT.json.
"""
import glob
import json
import math
import os
import sys

import mediapipe as mp
import numpy as np

# MediaPipe landmark ids, and the MetaHuman bones at the same joints.
MP = {"shoulder_l": 11, "shoulder_r": 12, "elbow_l": 13, "elbow_r": 14, "wrist_l": 15, "wrist_r": 16,
      "hip_l": 23, "hip_r": 24, "knee_l": 25, "knee_r": 26, "ankle_l": 27, "ankle_r": 28}
MH = {"shoulder_l": "upperarm_l", "shoulder_r": "upperarm_r", "elbow_l": "lowerarm_l",
      "elbow_r": "lowerarm_r", "wrist_l": "hand_l", "wrist_r": "hand_r", "hip_l": "thigh_l",
      "hip_r": "thigh_r", "knee_l": "calf_l", "knee_r": "calf_r", "ankle_l": "foot_l", "ankle_r": "foot_r"}
ANGLES = {
    "elbow": ("shoulder", "elbow", "wrist"),
    "knee": ("hip", "knee", "ankle"),
    "hip": ("shoulder", "hip", "knee"),
    "shoulder": ("hip", "shoulder", "elbow"),
}


def angle(a, b, c):
    u = np.asarray(a) - np.asarray(b)
    v = np.asarray(c) - np.asarray(b)
    cos = float(np.dot(u, v) / max(1e-9, np.linalg.norm(u) * np.linalg.norm(v)))
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def angles(pts):
    out = {}
    for name, (a, b, c) in ANGLES.items():
        for s in "lr":
            out[f"{name}_{s}"] = angle(pts[f"{a}_{s}"], pts[f"{b}_{s}"], pts[f"{c}_{s}"])
    return out


def main():
    frames_dir, model = sys.argv[1], sys.argv[2]
    out_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(frames_dir, "tracked.json")
    truth = json.load(open(os.path.join(frames_dir, "joints.json")))
    hz = float(truth["hz"])
    files = sorted(glob.glob(os.path.join(frames_dir, "f_*.png")))
    opts = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=model),
        running_mode=mp.tasks.vision.RunningMode.VIDEO, num_poses=1)
    errs = {k: [] for k in angles({k: [0, 0, 0] for k in MP})}
    swaps = 0
    missed = 0
    tracked = []
    with mp.tasks.vision.PoseLandmarker.create_from_options(opts) as lm:
        for n, f in enumerate(files):
            img = mp.Image.create_from_file(f)
            res = lm.detect_for_video(img, int(n * 1000.0 / hz))
            if not res.pose_world_landmarks:
                missed += 1
                tracked.append(None)
                continue
            w = res.pose_world_landmarks[0]
            # MediaPipe's world frame: metres about the hips, y down. Ours: y up.
            pts = {k: [w[i].x, -w[i].y, w[i].z] for k, i in MP.items()}
            tracked.append({k: v for k, v in pts.items()})
            row = truth["frames"][n]
            true_pts = {k: row[b] for k, b in MH.items()}
            ta = angles(true_pts)
            ma = angles(pts)
            # Swapped sides: his left read as his right (the knees, the clearest tell).
            straight = abs(ma["knee_l"] - ta["knee_l"]) + abs(ma["knee_r"] - ta["knee_r"])
            crossed = abs(ma["knee_l"] - ta["knee_r"]) + abs(ma["knee_r"] - ta["knee_l"])
            if crossed + 10.0 < straight:
                swaps += 1
            for k in errs:
                errs[k].append(ma[k] - ta[k])
    json.dump({"hz": hz, "frames": tracked}, open(out_path, "w"))
    print(f"ROUNDTRIP {os.path.basename(frames_dir.rstrip('/'))}: {len(files)} frames, {missed} with no pose, {swaps} with left and right swapped")
    for k, e in errs.items():
        if not e:
            continue
        bias = sum(e) / len(e)
        a = sorted(abs(x) for x in e)
        print(f"ROUNDTRIP {k}: error median {a[len(a) // 2]:.1f} deg, p90 {a[int(len(a) * 0.9)]:.1f}, worst {a[-1]:.1f}; bias {bias:+.1f} (tracked minus true)")


if __name__ == "__main__":
    main()
