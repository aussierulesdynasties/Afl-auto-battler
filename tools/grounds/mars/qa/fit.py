"""Fit Mars Stadium's fence to one smooth closed curve through the Google Earth trace (trace.py), and measure it.

  python3 tools/grounds/mars/qa/fit.py <trace.json> <out curve.json>

The curve is r(t) about the field centre, a Fourier series of K harmonics (K = 6: smooth, no wiggle shorter than a
sixth of the oval), fitted by least squares with misread rays dropped (more than 1 m off the curve: a gate, a
camera on the rail, a player's race, worn turf at the shaded edge); the report counts them. The error is each traced point's distance to the curve
along the curve's normal. Writes the coefficients and the curve every 0.25 deg, which model/build.py reads; every
ring of the bowl is an exact offset of it along its normal."""
import json, math, sys
import numpy as np

FC = (-4.18, -4.88)
K = 8


def design(t, k=K):
    cols = [np.ones_like(t)]
    for j in range(1, k + 1):
        cols += [np.cos(j * t), np.sin(j * t)]
    return np.stack(cols, 1)


def curve(c, t):
    return design(t, (len(c) - 1) // 2) @ c


def dist_to(px, py, cx, cy):
    """distance from each point to the closed polyline (cx, cy) (dense, so point-to-vertex-segment is exact enough)"""
    P = np.stack([px, py], 1); A = np.stack([cx, cy], 1); B = np.roll(A, -1, 0)
    d = np.full(len(P), np.inf)
    for i in range(0, len(A)):
        ab = B[i] - A[i]; ap = P - A[i]
        u = np.clip((ap @ ab) / (ab @ ab), 0, 1)
        d = np.minimum(d, np.hypot(*(ap - u[:, None] * ab).T))
    return d


def main(tr, out):
    T = json.load(open(tr)); p = np.array([q[1:3] for q in T['pts']])
    x, y = p[:, 0] - FC[0], p[:, 1] - FC[1]
    t = np.arctan2(x, y); r = np.hypot(x, y)            # bearing from north, clockwise
    keep = np.ones(len(r), bool)
    for _ in range(6):
        c, *_ = np.linalg.lstsq(design(t[keep]), r[keep], rcond=None)
        res = r - curve(c, t); s = 1.4826 * np.median(np.abs(res[keep]))
        keep = np.abs(res) < 1.0
    tt = np.radians(np.arange(0, 360, 0.25)); rr = curve(c, tt)
    cx, cy = rr * np.sin(tt), rr * np.cos(tt)
    d = dist_to(x[keep], y[keep], cx, cy)
    sgn = np.sign(r[keep] - curve(c, t[keep]))
    # size along the long axis: the longest chord through the centre, and the width across it
    L = rr + np.roll(rr, -720); i = int(np.argmax(L[:720])); W = rr[(i + 360) % 1440] + rr[(i + 1080) % 1440]
    rep = {'points': int(len(r)), 'used': int(keep.sum()), 'dropped': int((~keep).sum()),
           'rms_m': round(float(np.sqrt(np.mean(d ** 2))), 3), 'all_p90_m': round(float(np.percentile(dist_to(x, y, cx, cy), 90)), 3), 'p95_m': round(float(np.percentile(d, 95)), 3),
           'max_m': round(float(d.max()), 3), 'long_m': round(float(L[i]), 2), 'long_bearing': round(float(i * 0.25), 2),
           'wide_m': round(float(W), 2), 'harmonics': K}
    json.dump({'source': T['source'], 'centre': FC, 'coef': [float(v) for v in c], 'fit': rep,
               'bearing_r': [[round(float(b), 2), round(float(v), 3)] for b, v in zip(np.degrees(tt), rr)]}, open(out, 'w'))
    print(json.dumps(rep))
    return c, rep


if __name__ == '__main__':
    main(*sys.argv[1:3])
