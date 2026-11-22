"""Barossa Park's outlines against the 2026 Google mosaic, top-down, in metres (the shape rule: outlines are smooth
curves fitted to a trace, every ring an exact offset; errors measured, never judged by eye).

    python3 tools/grounds/barossa/satmosaic.py 20 150 0.2 work/z20.png
    python3 tools/grounds/barossa/shape_check.py [--fit]

1. The fence: the grass edge is traced on every half degree (a ray from the plan origin, where 1 m of grass gives
   way to 1.5 m of anything else). Reported: the distance of each traced point from FENCE's ellipse, square to it.
   Points more than 1 m off are counted apart (shadows of towers, stands and vans over the edge). --fit refits the
   ellipse (robust least squares) and prints it.
2. The ring road: the mosaic is unwrapped square to the fence (each row one exact offset), asphalt is picked by its
   Lab colour (sampled on the road at five bearings), runs under 3 m dropped, gaps of cars and lines closed, and the
   road's band taken at each bearing, then a median over 6 degrees. Reported: the model's road edges (RING) against
   it, on the bearings where the road runs clear (not under the north-east stand, 45-60, the clubroom concourse,
   236-334, nor where the road turns away to the car parks).
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plan  # noqa: E402

RES, HALF = 0.2, 150.0
LIMITS = {"fence_rms": 0.5, "fence_p95": 1.0, "road_median": 0.75, "road_p90": 1.5}
CLEAR = [(0, 44), (62, 108), (140, 232)]   # bearings where the road's outer edge runs clear


def mosaic():
    import cv2
    a = cv2.imread(os.path.join(HERE, "work", "z20.png"))
    if a is None:
        raise SystemExit("work/z20.png missing: python3 tools/grounds/barossa/satmosaic.py 20 150 0.2 work/z20.png")
    return a


def sample(a, E, N):
    import cv2
    return cv2.remap(a, ((E + HALF) / RES - 0.5).astype(np.float32), ((HALF - N) / RES - 0.5).astype(np.float32),
                     cv2.INTER_LINEAR)


def ell_dist(p, E, N):
    cx, cy, a1, a2, rot = p
    t = math.radians(rot)
    c, s = math.cos(t), math.sin(t)
    x, y = E - cx, N - cy
    u, v = c * x + s * y, -s * x + c * y
    rho = np.hypot(u / a1, v / a2)
    return (rho - 1) * np.hypot(u, v) / rho


def trace_fence(a):
    import cv2
    bs = np.arange(0, 360, 0.5)
    rs = np.arange(50, 100, 0.1)
    B, R = np.meshgrid(bs, rs)
    pol = sample(a, R * np.sin(np.radians(B)), R * np.cos(np.radians(B)))
    hsv = cv2.cvtColor(pol, cv2.COLOR_BGR2HSV).astype(float)
    grass = (hsv[..., 0] > 28) & (hsv[..., 0] < 80) & (hsv[..., 1] > 60)
    pts = []
    for j, b in enumerate(bs):
        g = grass[:, j]
        for i in range(50, len(rs) - 20):
            if g[i - 10:i].mean() > 0.8 and g[i:i + 15].mean() < 0.3:
                r = rs[i]
                pts.append((r * math.sin(math.radians(b)), r * math.cos(math.radians(b))))
                break
    return np.array(pts)


def trace_road(a):
    import cv2
    bs = np.arange(0, 360, 0.5)
    offs = np.arange(-3, 28, 0.1)
    P = np.array([[plan.polar(b, o) for b in bs] for o in offs])
    pol = sample(a, P[..., 0], P[..., 1])
    lab = cv2.cvtColor(pol, cv2.COLOR_BGR2LAB).astype(float)
    m = ((lab[..., 0] > 70) & (lab[..., 0] < 132) & (lab[..., 1] > 125) & (lab[..., 1] < 139)
         & (lab[..., 2] > 128) & (lab[..., 2] < 141)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 3), np.uint8))
    col = cv2.blur(m.astype(float), (1, 5)) > 0.5
    inn, out = np.full(len(bs), np.nan), np.full(len(bs), np.nan)
    for j in range(len(bs)):
        c = col[:, j]
        i = 0
        while i < len(offs):
            if c[i]:
                k = i
                while k < len(offs) and c[k]:
                    k += 1
                if offs[k - 1] - offs[i] > 3.0 and offs[i] < 16:
                    inn[j], out[j] = offs[i], offs[k - 1]
                    break
                i = k
            else:
                i += 1

    def med(x):
        y = np.full_like(x, np.nan)
        for j in range(len(x)):
            w = x[[(j + k) % len(x) for k in range(-6, 7)]]
            w = w[np.isfinite(w)]
            if len(w) >= 5:
                y[j] = np.median(w)
        return y
    return bs, med(inn), med(out)


def main():
    a = mosaic()
    ok = True
    pts = trace_fence(a)
    d = ell_dist(plan.FENCE, pts[:, 0], pts[:, 1])
    inl = np.abs(d) < 1.0
    rms, p95 = float(np.sqrt(np.mean(d[inl] ** 2))), float(np.percentile(np.abs(d[inl]), 95))
    f_ok = rms <= LIMITS["fence_rms"] and p95 <= LIMITS["fence_p95"]
    ok &= f_ok
    print("FENCE %s: %d of %d traced points within 1 m; rms %.2f m (limit %.2f), 95%% within %.2f m (limit %.2f), "
          "max %.2f m" % ("PASS" if f_ok else "FAIL", inl.sum(), len(d), rms, LIMITS["fence_rms"], p95,
                           LIMITS["fence_p95"], np.abs(d[inl]).max()))
    if "--fit" in sys.argv:
        from scipy.optimize import least_squares
        keep = inl
        p = list(plan.FENCE)
        for _ in range(4):
            f = least_squares(lambda q: ell_dist(q, pts[keep, 0], pts[keep, 1]), p, loss="soft_l1", f_scale=0.3)
            p = f.x
            keep = np.abs(ell_dist(p, pts[:, 0], pts[:, 1])) < 1.0
        print("  refit FENCE =", tuple(round(float(x), 3) for x in p))
    bs, inn, out = trace_road(a)
    model = np.array([plan.interp(plan.RING, b)[2] for b in bs])
    sel = np.zeros(len(bs), bool)
    for b0, b1 in CLEAR:
        sel |= (bs >= b0) & (bs <= b1)
    sel &= np.isfinite(out)
    e = np.abs(model[sel] - out[sel])
    med, p90 = float(np.median(e)), float(np.percentile(e, 90))
    r_ok = med <= LIMITS["road_median"] and p90 <= LIMITS["road_p90"]
    ok &= r_ok
    print("ROAD outer edge %s: %d bearings; median %.2f m (limit %.2f), 90%% within %.2f m (limit %.2f), max %.2f m"
          % ("PASS" if r_ok else "FAIL", sel.sum(), med, LIMITS["road_median"], p90, LIMITS["road_p90"], e.max()))
    for b0, b1 in CLEAR:
        s = sel & (bs >= b0) & (bs <= b1)
        print("   %3d-%3d: mean %+.2f m, max %.2f m" % (b0, b1, np.mean(model[s] - out[s]), np.max(np.abs(model[s] - out[s]))))
    sw = (bs >= 186) & (bs <= 215) & np.isfinite(inn)
    m0 = np.array([plan.interp(plan.RING, b)[1] for b in bs])
    print("ROAD inner edge, south-west (wall side, 186-215): mean %+.2f m, max %.2f m"
          % (np.mean(m0[sw] - inn[sw]), np.max(np.abs(m0[sw] - inn[sw]))))
    print("ALL PASS" if ok else "SOME FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
