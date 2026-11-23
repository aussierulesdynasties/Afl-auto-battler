#!/usr/bin/env python3
"""Follow one footballer through broadcast footage: his 2D joints and a 3D guess, every frame.

MediaPipe (tools/oval3d/mp_roundtrip.py) finds one or two people on a whole broadcast frame and
loses a man who is horizontal or upside down in the air, which is every speccy. RTMW3D (OpenMMLab
RTMPose family, Apache 2.0, run through rtmlib, Apache 2.0) detects everyone in the frame first and
reads each one in his own box, so it holds a jumper through the climb and the fall.

    python3 tools/oval3d/track_broadcast.py detect FRAMES_DIR DET.json [FIRST LAST]
    python3 tools/oval3d/track_broadcast.py follow DET.json TRACK.json HZ FRAME:X,Y [FRAME:X,Y ...]
    python3 tools/oval3d/track_broadcast.py corridor FRAMES_DIR DET.json TRACK.json HZ FRAME:X,Y [...]
    python3 tools/oval3d/track_broadcast.py refine FRAMES_DIR TRACK.json OUT.json FRAME:X,Y [...]
    python3 tools/oval3d/track_broadcast.py lift FRAMES_DIR TRACK.json MODEL.task
    python3 tools/oval3d/track_broadcast.py sheet FRAMES_DIR SHEET.png FIRST:LAST:STEP TRACK.json [...]

detect: every person in frames f_NNNN.png (numbered from 0), COCO-17 joints in pixels, their
scores, and RTMW3D's 3D guess. follow: one man, from a point on him (FRAME:X,Y in pixels; give a
point again after a camera cut or whip), always taking the detection nearest where he was heading.
Writes the mp_fit.py track format: {"hz", "size", "frames": [{"p2", "p3", "vis"} | null]} with J's
joint order, p2 in pixels y up, p3 in metres about his hips (y up, z toward the camera).
sheet: a contact sheet of the followed men drawn on the frames, to check by eye before fitting.

Install: pip install rtmlib (models download on first use, about 400 MB, to ~/.cache/rtmlib).
"""
import glob
import json
import os
import sys

import numpy as np

# mp_fit.py's joint order, and the COCO-17 index of each.
J = ["shoulder_l", "shoulder_r", "elbow_l", "elbow_r", "wrist_l", "wrist_r",
     "hip_l", "hip_r", "knee_l", "knee_r", "ankle_l", "ankle_r"]
COCO = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
TRUNK_M = 0.50     # shoulders' middle to hips' middle on our body, metres: sets the 3D guess's size
Z_SCALE = 1.0      # RTMW3D's depth against its picture coordinates (calibrated: see roundtrip)


def frame_files(d):
    return sorted(glob.glob(os.path.join(d, "f_*.png")))


def detect(frames_dir, out, first=None, last=None):
    import cv2
    from rtmlib import Wholebody3d
    model = Wholebody3d(backend="onnxruntime", device="cpu")
    files = frame_files(frames_dir)
    a = int(first) if first is not None else 0
    b = int(last) if last is not None else len(files)
    res = {}
    for i in range(a, b):
        k3, s, _, k2 = model(cv2.imread(files[i]))
        k3 = np.asarray(k3)[:, :17]
        res[i] = {"k2": np.asarray(k2)[:, :17].tolist(), "k3": k3.tolist(),
                  "s": np.asarray(s)[:, :17].tolist()}
        print(f"DETECT {i}: {len(k3)} people", flush=True)
    json.dump({"frames_dir": frames_dir, "det": res}, open(out, "w"))


def _centre(k2, s):
    k2 = np.asarray(k2)
    trunk = k2[[5, 6, 11, 12]]
    return trunk.mean(0), max(10.0, float(np.linalg.norm(k2[[5, 6]].mean(0) - k2[[11, 12]].mean(0))))


def follow(det_path, out, hz, seeds):
    D = json.load(open(det_path))
    det = {int(k): v for k, v in D["det"].items()}
    import cv2
    files = frame_files(D["frames_dir"])
    h, w = cv2.imread(files[0]).shape[:2]
    seeds = {int(f): np.array([float(v) for v in xy.split(",")]) for f, xy in (s.split(":") for s in seeds)}
    first, last = min(seeds), max(det)
    frames = [None] * (last + 1)
    pos, size, vel = None, 150.0, np.zeros(2)
    lost = 0
    for i in range(first, last + 1):
        if i in seeds:
            pos, vel, lost = seeds[i], np.zeros(2), 0
        if pos is None or i not in det:
            continue
        pred = pos + vel
        best = None
        for n, (k2, s) in enumerate(zip(det[i]["k2"], det[i]["s"])):
            c, sz = _centre(k2, s)
            # Near where he was heading, about his size; a fresh seed trusts the point alone.
            d = np.linalg.norm(c - pred) / (size if i not in seeds else 250.0)
            if i not in seeds:
                d += 0.6 * abs(np.log(sz / size))
            if best is None or d < best[0]:
                best = (d, n, c, sz)
        if best is None or best[0] > 0.9:
            lost += 1
            pos = pred
            if lost > 6:
                pos = None
            continue
        _, n, c, sz = best
        lost = 0
        vel = 0.5 * vel + 0.5 * (c - pos) if i not in seeds else np.zeros(2)
        pos, size = c, (sz if i in seeds else 0.7 * size + 0.3 * sz)
        k2 = np.asarray(det[i]["k2"][n])
        k3 = np.asarray(det[i]["k3"][n])
        s = np.asarray(det[i]["s"][n])
        p2 = np.stack([k2[COCO, 0], -k2[COCO, 1]], 1)
        # RTMW3D's own 3D guess (picture coordinates y up, sized to our trunk; its depth is
        # already about metres). Its depth reads our own clip poorly (wrists and ankles often on
        # the wrong side), so `lift` replaces it with MediaPipe's on an upright crop.
        g = np.stack([k3[COCO, 0], -k3[COCO, 1], np.zeros(len(COCO))], 1)
        trunk = np.linalg.norm(g[[0, 1]].mean(0)[:2] - g[[6, 7]].mean(0)[:2])
        g = (g - g[[6, 7]].mean(0)) * (TRUNK_M / max(1e-6, trunk))
        g[:, 2] = (k3[COCO, 2] - k3[COCO[6:8], 2].mean()) * Z_SCALE
        vis = np.clip(s[COCO] / 10.0, 0.05, 1.0)   # RTMPose scores run about 0-10
        frames[i] = {"p2": p2.tolist(), "p3": g.tolist(), "vis": vis.tolist(), "det": n}
    json.dump({"hz": float(hz), "size": [w, h], "frames": frames}, open(out, "w"))
    got = [i for i, f in enumerate(frames) if f]
    print(f"FOLLOW {len(got)} frames ({got[0] if got else '-'}..{got[-1] if got else '-'}) -> {out}")


RTMPOSE_X = "rtmpose-x_simcc-body7_pt-body7_700e-384x288-71d7b7e9_20230629.onnx"


def _upright_pose(model, img, c, side, ang):
    """RTMPose on a square box about c, the picture first turned by ang degrees about c so his
    trunk stands up; joints mapped back to the picture. A man lying or upside down reads badly
    unless he is turned up first."""
    import cv2
    M = cv2.getRotationMatrix2D((float(c[0]), float(c[1])), float(ang), 1.0)
    rot = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT)
    box = [c[0] - side * 0.5, c[1] - side * 0.5, c[0] + side * 0.5, c[1] + side * 0.5]
    k, sc = model(rot, bboxes=[box])
    Mi = cv2.invertAffineTransform(M)
    k = k[0] @ Mi[:, :2].T + Mi[:, 2]
    return k, sc[0]


def _trunk(k):
    hip, sho = k[[11, 12]].mean(0), k[[5, 6]].mean(0)
    up = sho - hip
    # Degrees to turn the picture (counter-clockwise, cv2) so his trunk points up.
    return hip, np.linalg.norm(up), float(np.degrees(np.arctan2(up[0], -up[1])))


def corridor(frames_dir, det_path, out, hz, seeds):
    """Follow him along a path of points put on his trunk by eye (FRAME:X,Y every few frames
    through the hard part). Each frame takes the detection whose trunk is nearest the path, if one
    is close; where none is (he is horizontal, or tangled with the stepladder), he is read again in
    a box on the path, turned upright by the trunk angle of the frames either side. Self-driven
    boxes drift onto other players (tried, 2026-11-23); a path set by eye does not."""
    import cv2
    from rtmlib import RTMPose
    D = json.load(open(det_path))
    det = {int(k): v for k, v in D["det"].items()}
    files = frame_files(frames_dir)
    h, w = cv2.imread(files[0]).shape[:2]
    S = sorted((int(f), np.array([float(v) for v in xy.split(",")])) for f, xy in (s.split(":") for s in seeds))
    sf = [f for f, _ in S]
    first, last = sf[0], sf[-1]

    def path(i):
        for (a, pa), (b, pb) in zip(S, S[1:]):
            if a <= i <= b:
                return pa + (pb - pa) * ((i - a) / max(1, b - a))
        return S[0][1] if i < first else S[-1][1]

    frames = [None] * (max(det) + 1)
    got = {}
    for i in range(first, last + 1):
        best = None
        for n, (k2, s) in enumerate(zip(det.get(i, {}).get("k2", []), det.get(i, {}).get("s", []))):
            k2 = np.asarray(k2)
            c, sz = _centre(k2, s)
            d = np.linalg.norm(c - path(i))
            if d < 0.55 * sz and (best is None or d < best[0]):
                best = (d, k2, np.asarray(s))
        if best:
            got[i] = (best[1], best[2])
    model = RTMPose(os.path.join(os.path.expanduser("~/.cache/rtmlib/hub/checkpoints"), RTMPOSE_X),
                    model_input_size=(288, 384), backend="onnxruntime", device="cpu")
    reread = 0
    for i in range(first, last + 1):
        if i in got:
            continue
        # Trunk size and angle from the nearest read frames either side.
        near = sorted(got, key=lambda g: abs(g - i))[:2]
        tl = np.mean([_trunk(got[g][0])[1] for g in near]) if near else 120.0
        angs = [_trunk(got[g][0])[2] for g in near]
        ang = float(np.degrees(np.arctan2(np.mean(np.sin(np.radians(angs))), np.mean(np.cos(np.radians(angs)))))) if angs else 0.0
        img = cv2.imread(files[i])
        k, sc = _upright_pose(model, img, path(i), max(3.4 * tl, 120.0), ang)
        # Read again turned by his own trunk this time.
        _, tl2, ang2 = _trunk(k)
        k, sc = _upright_pose(model, img, k[COCO].mean(0), max(3.4 * tl2, 120.0), ang2)
        got[i] = (k, sc)
        reread += 1
    for i, (k2, s) in got.items():
        p2 = np.stack([k2[COCO, 0], -k2[COCO, 1]], 1)
        frames[i] = {"p2": p2.tolist(), "p3": np.zeros((12, 3)).tolist(),
                     "vis": np.clip(np.asarray(s)[COCO] / 10.0, 0.05, 1.0).tolist()}
    json.dump({"hz": float(hz), "size": [w, h], "frames": frames}, open(out, "w"))
    print(f"CORRIDOR {last - first + 1} frames ({first}..{last}), {reread} read again in a box -> {out}")


def refine(frames_dir, track, out, seeds):
    """Read him again in a box that follows him, turned upright, every frame from the first seed
    to the last: holds him where the detector loses him (horizontal, or tangled with the
    stepladder). Seeds FRAME:X,Y put the box on him (after a cut, or where it drifted)."""
    import cv2
    from rtmlib import RTMPose
    model = RTMPose(os.path.join(os.path.expanduser("~/.cache/rtmlib/hub/checkpoints"), RTMPOSE_X),
                    model_input_size=(288, 384), backend="onnxruntime", device="cpu")
    T = json.load(open(track))
    files = frame_files(frames_dir)
    seeds = {int(f): np.array([float(v) for v in xy.split(",")]) for f, xy in (s.split(":") for s in seeds)}
    prev = None    # (hip, trunk length, angle, centre)
    vel = np.zeros(2)
    n_out = 0
    first, last = min(seeds), max(seeds)
    for i in range(first, last + 1):
        f = T["frames"][i] if i < len(T["frames"]) else None
        img = cv2.imread(files[i])
        if i in seeds:
            # Start from the detector's reading if it is on him, else a standing man of the
            # last size at the seed.
            c = seeds[i]
            if f and np.linalg.norm(np.array(f["p2"])[[6, 7]].mean(0) * [1, -1] - c) < 200:
                k = np.zeros((17, 2))
                k[COCO] = np.array(f["p2"]) * [1, -1]
                hip, tl, ang = _trunk(k)
                c = k[COCO].mean(0)
            else:
                tl, ang = (prev[1] if prev else 120.0), (prev[2] if prev else 0.0)
            vel = np.zeros(2)
        elif prev is None:
            continue
        else:
            c = prev[3] + vel
            tl, ang = prev[1], prev[2]
        k = None
        for _ in range(2):    # read, then read again in the box the first reading gives
            side = max(3.4 * tl, 120.0)
            k, sc = _upright_pose(model, img, c, side, ang)
            hip, tl2, ang2 = _trunk(k)
            good = sc[COCO] > 3.0
            c2 = k[COCO][good].mean(0) if good.sum() >= 4 else c
            c, tl, ang = c2, 0.5 * tl + 0.5 * tl2, ang2
        vel = 0.6 * vel + 0.4 * (c - prev[3]) if prev is not None and i not in seeds else np.zeros(2)
        prev = (hip, tl, ang, c)
        while len(T["frames"]) <= i:
            T["frames"].append(None)
        p2 = np.stack([k[COCO, 0], -k[COCO, 1]], 1)
        old = T["frames"][i] or {}
        T["frames"][i] = {"p2": p2.tolist(), "p3": old.get("p3", np.zeros((12, 3)).tolist()),
                          "vis": np.clip(sc[COCO] / 10.0, 0.05, 1.0).tolist(), "refined": True}
        n_out += 1
    # Frames outside the seeded span are dropped: the refined span is the clip.
    for i in range(len(T["frames"])):
        if i < first or i > last:
            T["frames"][i] = None
    json.dump(T, open(out, "w"))
    print(f"REFINE {n_out} frames ({first}..{last}) -> {out}")


def lift(frames_dir, track, model_path):
    """The 3D guess from MediaPipe's world landmarks, read on a crop of the man turned so his trunk
    stands up (MediaPipe loses a man lying or upside down, and reads him well upright), then
    turned back. Its 2D points are only used to pick the right man in the crop."""
    import mediapipe as mp
    from PIL import Image
    T = json.load(open(track))
    files = frame_files(frames_dir)
    opts = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
        running_mode=mp.tasks.vision.RunningMode.IMAGE, num_poses=3,
        min_pose_detection_confidence=0.2, min_pose_presence_confidence=0.2)
    MPI = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
    got = 0
    with mp.tasks.vision.PoseLandmarker.create_from_options(opts) as lm:
        for i, f in enumerate(T["frames"]):
            if not f:
                continue
            p = np.array([(x, -y) for x, y in f["p2"]])   # pixels, y down
            hip, sho = p[[6, 7]].mean(0), p[[0, 1]].mean(0)
            up = sho - hip
            ang = np.degrees(np.arctan2(up[0], -up[1]))   # trunk lean from upright, clockwise
            side = 1.6 * max(np.ptp(p[:, 0]), np.ptp(p[:, 1]), 2.5 * np.linalg.norm(up))
            c = (p.min(0) + p.max(0)) * 0.5
            im = np.asarray(Image.open(files[i]).convert("RGB")).astype(np.float32)
            # Grey out everyone else: MediaPipe reads one man, and takes the clearest one in the
            # crop, often the stepladder. Kept: pixels near his own bones, and his head.
            tl = max(10.0, np.linalg.norm(up))
            head = sho + up * 0.55
            segs = [(p[a], p[b]) for a, b in ((0, 2), (2, 4), (1, 3), (3, 5), (0, 1), (6, 7), (0, 6), (1, 7),
                                              (6, 8), (8, 10), (7, 9), (9, 11))] + [(sho, head)]
            x0, y0 = int(c[0] - side / 2), int(c[1] - side / 2)
            yy, xx = np.mgrid[y0:y0 + int(side), x0:x0 + int(side)]
            P = np.stack([xx, yy], -1).astype(np.float32)
            dmin = np.full(xx.shape, 1e9, np.float32)
            for a, b in segs:
                ab = b - a
                t = np.clip(((P - a) @ ab) / max(1e-6, ab @ ab), 0, 1)
                dmin = np.minimum(dmin, np.linalg.norm(P - (a + t[..., None] * ab), axis=-1))
            hgt, wid = im.shape[:2]
            crop = np.full((int(side), int(side), 3), 128.0, np.float32)
            ys, xs = np.clip(yy, 0, hgt - 1), np.clip(xx, 0, wid - 1)
            inside = (yy >= 0) & (yy < hgt) & (xx >= 0) & (xx < wid)
            keep = np.clip(1.0 - (dmin - 0.35 * tl) / (0.15 * tl), 0, 1) * inside
            crop = crop * (1 - keep[..., None]) + im[ys, xs] * keep[..., None]
            crop = Image.fromarray(crop.astype(np.uint8))
            crop = crop.resize((512, 512), Image.BICUBIC).rotate(ang, resample=Image.BILINEAR)
            r = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(np.asarray(crop))))
            th = np.radians(ang)
            rot = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
            best = None
            for a2, w in zip(r.pose_landmarks, r.pose_world_landmarks):
                q = np.array([[a2[k].x - 0.5, a2[k].y - 0.5] for k in MPI]) * 512
                q = (q @ rot.T) * (side / 512) + c
                err = np.median(np.linalg.norm(q - p, axis=1)) / max(10.0, np.linalg.norm(up))
                if best is None or err < best[0]:
                    best = (err, w)
            if best is None or best[0] > 0.5:
                f["lift"] = None
                continue
            w = best[1]
            g = np.array([[w[k].x, w[k].y, w[k].z] for k in MPI])
            g[:, :2] = g[:, :2] @ rot.T        # back to the picture's own up
            g = np.stack([g[:, 0], -g[:, 1], -g[:, 2]], 1)
            f["p3"] = (g - g[[6, 7]].mean(0)).tolist()
            f["lift"] = float(best[0])
            got += 1
    json.dump(T, open(track, "w"))
    print(f"LIFT {got} of {sum(1 for f in T['frames'] if f)} frames -> {track}")


def sheet(frames_dir, out, rng, tracks):
    from PIL import Image, ImageDraw
    a, b, st = map(int, rng.split(":"))
    files = frame_files(frames_dir)
    T = [json.load(open(t))["frames"] for t in tracks]
    E = [(0, 2), (2, 4), (1, 3), (3, 5), (0, 1), (6, 7), (0, 6), (1, 7), (6, 8), (8, 10), (7, 9), (9, 11)]
    cols = [((0, 255, 255), (255, 80, 0)), ((255, 255, 0), (255, 0, 255))]
    idx = list(range(a, b, st))
    W, H = 480, 270
    sh = Image.new("RGB", (W * 4, H * ((len(idx) + 3) // 4)))
    for k, i in enumerate(idx):
        im = Image.open(files[i]).convert("RGB")
        d = ImageDraw.Draw(im)
        for n, fr in enumerate(T):
            f = fr[i] if i < len(fr) else None
            if not f:
                continue
            p = [(x, -y) for x, y in f["p2"]]
            for x, y in E:
                # Left side (even index) in the first colour, right in the second.
                d.line((*p[x], *p[y]), fill=cols[n % 2][x % 2], width=6)
        im = im.resize((W, H))
        ImageDraw.Draw(im).text((5, 5), str(i), fill="white")
        sh.paste(im, ((k % 4) * W, (k // 4) * H))
    sh.save(out)


def main():
    cmd = sys.argv[1]
    if cmd == "detect":
        detect(*sys.argv[2:])
    elif cmd == "follow":
        follow(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
    elif cmd == "corridor":
        corridor(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6:])
    elif cmd == "refine":
        refine(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
    elif cmd == "lift":
        lift(*sys.argv[2:5])
    elif cmd == "sheet":
        sheet(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])


if __name__ == "__main__":
    main()
