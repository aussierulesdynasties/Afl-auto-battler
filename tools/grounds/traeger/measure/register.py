"""Register a Google Earth straight-down shot (qa/ge_nadir.js, 3D buildings off) to the mosaic (scene/qa/mosaic.py,
0.5 m a pixel, model frame): SIFT matches and a RANSAC similarity. Writes NAME.reg.json: shot pixel -> model east/north.

    python3 register.py SHOT.png MOSAIC.png E N      (E, N: roughly where the shot is centred, model metres)
"""
import json
import sys

import cv2
import numpy as np

R, K = 1300.0, 2.0


def main(shot, mosaic, e0, n0):
    a = cv2.imread(shot, cv2.IMREAD_GRAYSCALE)[95:940]     # GE's toolbar and status bar out
    m = cv2.imread(mosaic, cv2.IMREAD_GRAYSCALE)
    cx, cy = int((e0 + R) * K), int((R - n0) * K)
    h = 450
    crop = m[cy - h:cy + h, cx - h:cx + h]
    sift = cv2.SIFT_create(6000)
    k1, d1 = sift.detectAndCompute(a, None)
    k2, d2 = sift.detectAndCompute(crop, None)
    mt = cv2.BFMatcher().knnMatch(d1, d2, k=2)
    good = [p for p, q in mt if p.distance < 0.75 * q.distance]
    src = np.float32([k1[g.queryIdx].pt for g in good]) + [0, 95]
    dst = np.float32([k2[g.trainIdx].pt for g in good]) + [cx - h, cy - h]
    M, inl = cv2.estimateAffinePartial2D(src, dst, ransacReprojThreshold=2.0, maxIters=20000, confidence=0.999)
    inl = inl.ravel().astype(bool)
    res = cv2.transform(src[inl][None], M)[0] - dst[inl]
    s = float(np.hypot(M[0, 0], M[1, 0]))
    print(shot, "matches", len(good), "inliers", int(inl.sum()), "scale %.4f m/px" % (s / K),
          "rot %.3f deg" % np.degrees(np.arctan2(M[1, 0], M[0, 0])), "rms %.2f mosaic px" % np.sqrt((res ** 2).sum(1).mean()))
    json.dump({"M": M.tolist(), "m_per_px": s / K, "inliers": int(inl.sum()),
               "rms_m": float(np.sqrt((res ** 2).sum(1).mean()) / K)}, open(shot[:-4] + ".reg.json", "w"), indent=1)


def to_model(reg, uv):
    """Shot pixels (N x 2) -> model east, north (N x 2)."""
    M = np.array(reg["M"])
    q = cv2.transform(np.float32(uv)[None], M)[0]
    return np.stack([q[:, 0] / K - R, R - q[:, 1] / K], 1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]))
