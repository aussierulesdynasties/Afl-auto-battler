"""Every stand's roof against Google Earth, bearing by bearing: the front and back edges and the ends, measured on a
calibrated straight-down Google Earth shot unwrapped round the fence, against manuka.json's values (which build.py
builds exactly: every ring is an offset from the fitted fence).

    python3 roofcheck.py GE.png CAM_X CAM_Y CAM_H RES [UNWRAP.png]

GE.png is a 1280 x 720 crop, heading 0, tilt 0; (CAM_X, CAM_Y) the point under the camera and CAM_H its height over
the turf (both read off Google Earth's status bar: see the shape README), RES metres a pixel on the turf.
Lean is taken out per roof: a point h m up is unwrapped where it shows, cam + (p - cam) * H / (H - h).
On each bearing the edge is the strongest step in colour within WINDOW m of our value with the expected sign
(concourse to roof at the front, roof to shadow at the back); a bearing with no clear step is left out and counted.
Ends: row by row across the roof, where the colour crosses half-way from the roof's to what lies beyond.
Pass: median |error| <= 0.5 m and 90th percentile <= 1.5 m over every edge, and each end's median within 1 m.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "..", "model", "manuka.json")))
C = np.array(D["C"])
FC = np.array(D["fence"]["fourier"])
K = np.arange(1, (len(FC) - 1) // 2 + 1)
WINDOW = 3.0
LIMIT_MEDIAN, LIMIT_P90, LIMIT_END = 0.5, 1.5, 1.0
STEP = 0.25


def rf(b):
    a = np.radians(np.atleast_1d(b))
    return FC[0] + np.cos(np.outer(a, K)) @ FC[1::2] + np.sin(np.outer(a, K)) @ FC[2::2]


def fence_pt(b):
    a = np.radians(np.atleast_1d(b)); r = rf(b)
    return np.c_[C[0] + r * np.sin(a), C[1] + r * np.cos(a)]


def normal(b):
    b = np.atleast_1d(b)
    t = fence_pt(b + 0.01) - fence_pt(b - 0.01); t /= np.linalg.norm(t, axis=1)[:, None]
    return np.c_[-t[:, 1], t[:, 0]]


class Unwrap:
    """The shot resampled to (d past the fence, bearing) for points h m up."""
    def __init__(self, im, cam, res):
        self.im = im.astype(float); self.cam = cam; self.res = res
        self.bs = np.arange(0, 360, STEP); self.ds = np.arange(-4, 46, STEP)
        self.F = fence_pt(self.bs); self.N = normal(self.bs); self.cache = {}

    def at(self, h):
        if h not in self.cache:
            X = self.F[:, 0][None] + self.ds[:, None] * self.N[:, 0][None]
            Y = self.F[:, 1][None] + self.ds[:, None] * self.N[:, 1][None]
            cx, cy, H = self.cam
            k = H / (H - h)
            u = self.im.shape[1] / 2 + (cx + (X - cx) * k - cx) / self.res
            v = self.im.shape[0] / 2 - (cy + (Y - cy) * k - cy) / self.res
            self.cache[h] = np.stack([nd.map_coordinates(self.im[..., c], [v, u], order=1, cval=np.nan) for c in range(3)], -1)
        return self.cache[h]


def radial_edge(U, uw, b, d0, sign):
    """the d of the strongest colour step within WINDOW of d0 on bearing b; sign +1 = brighter to darker outward"""
    j = int(round((b % 360) / STEP)) % len(uw.bs)
    cols = [(j + o) % len(uw.bs) for o in (-1, 0, 1)]
    prof = nd.gaussian_filter1d(U[:, cols].mean(1), 1.0, axis=0)
    lum = prof.mean(1)
    g = np.gradient(lum)
    s = (uw.ds >= d0 - WINDOW) & (uw.ds <= d0 + WINDOW)
    cand = np.where(s)[0]
    if not len(cand) or not np.all(np.isfinite(lum[cand])):
        return None
    gg = -g[cand] * sign
    k = cand[int(np.argmax(gg))]
    if gg.max() < 4.0 or k in (cand[0], cand[-1]):     # no step inside the window (the strongest is past its edge)
        return None
    return float(uw.ds[k] + STEP / 2)


def end_rows(U, uw, end_fn, ds, inward):
    """per row d: where the colour crosses half-way from the roof's own (1 to 2.5 degrees inside our end) to what lies
    beyond (1 to 2.5 degrees outside), searched within 2 degrees of our end end_fn(d); the error in bearing degrees"""
    out = []
    for d in ds:
        e = end_fn(d)
        rows = (uw.ds >= d - 0.5) & (uw.ds <= d + 0.5)
        col = lambda b: U[rows][:, int(round((b % 360) / STEP)) % len(uw.bs)].mean(0)
        roof = np.median([col(e + inward * o) for o in np.arange(1.0, 2.51, STEP)], 0)
        far = np.median([col(e - inward * o) for o in np.arange(1.0, 2.51, STEP)], 0)
        if not (np.all(np.isfinite(roof)) and np.all(np.isfinite(far))) or np.linalg.norm(far - roof) < 25:
            continue
        bs = np.arange(e - 2.0, e + 2.001, STEP / 2)
        t = np.array([np.linalg.norm(col(b) - roof) / np.linalg.norm(far - roof) for b in bs])
        k = np.where(np.diff(np.sign(t - 0.5)) != 0)[0]
        if not len(k):
            continue
        k = k[np.argmin(abs(bs[k] - e))]
        b = bs[k] + (0.5 - t[k]) / (t[k + 1] - t[k] + 1e-9) * (bs[k + 1] - bs[k])
        out.append(b - e)
    return out


def RB(S, b):
    """build.py's RB: the roof's back edge at bearing b"""
    t = S.get("rb_at")
    if not t:
        return S["rb"]
    xs = [x for x, _ in t]; bu = b if b >= xs[0] - 1e-6 else b + 360
    return float(np.interp(bu, xs, [y for _, y in t]))


def roofs():
    """(name, b0, b1, front d, back d, height for the unwrap, ends checked)"""
    out = []
    for k, S in D["astands"].items():
        if k.startswith("_"):
            continue
        r0, r1 = S.get("roof_b0", S["b0"]), S.get("roof_b1", S["b1"])
        out.append(("stand " + k, r0, r1, S["rf"], lambda b, S=S: RB(S, b), 0.5 * (S["rfz"] + S["rbz"])))
    for c in D["canopies"]["list"]:
        S = D["astands"][c["of"]]
        out.append(("canopy " + c["of"], c["b0"], c["b1"], c["rf"], lambda b, c=c: c["rb"], 0.5 * (S["rfz"] + S["rbz"]) + 0.6))
    M = D["media"]; O = M["deck_outline"]
    mid = 0.5 * (O[0][0] + O[1][0]); dmax = max(d for _, d in O) - 0.5     # the ends: outline points off the back
    west = sorted([(d, b) for b, d in O if b > mid and d < dmax]); east = sorted([(d, b) for b, d in O if b < mid and d < dmax])
    out.append(("media deck", O[0][0], O[1][0], M["deck_front"],
                lambda b: float(np.interp(b, *zip(*M["roof_back_at"]))), M["z_roof"],
                (lambda d: float(np.interp(d, *zip(*east))), lambda d: float(np.interp(d, *zip(*west))))))
    B = D["bradman"]
    out.append(("bradman", B["b0"], B["b1"], B["roof_front"], lambda b: B["back"], B["roof_top"]))
    return out


def main():
    im = np.asarray(Image.open(sys.argv[1]).convert("RGB"))
    cam = tuple(map(float, sys.argv[2:5])); res = float(sys.argv[5])
    uw = Unwrap(im, cam, res)
    rep = {"limits": {"median_abs_m": LIMIT_MEDIAN, "p90_abs_m": LIMIT_P90, "end_abs_m": LIMIT_END}, "roofs": {}}
    allerr = []; ends_ok = True
    for rec in roofs():
        name, b0, b1, df, db, h = rec[:6]
        U = uw.at(round(h, 1))
        ef, eb, miss = [], [], 0
        for b in np.arange(b0 + 1.0, b1 - 1.0 + 1e-9, 0.5):
            f = radial_edge(U, uw, b, df, -1)      # front: concourse or seats to the roof, either way a step
            if f is None:
                f = radial_edge(U, uw, b, df, +1)
            k = radial_edge(U, uw, b, db(b), +1)   # back: the roof to its shadow
            if f is None: miss += 1
            else: ef.append(f - df)
            if k is None: miss += 1
            else: eb.append(k - db(b))
        ends = rec[6] if len(rec) > 6 else (lambda d: b0, lambda d: b1)
        rows_ = np.arange(df + 1.0, db(0.5 * (b0 + b1)) - 0.9, 1.0)
        mid = 0.5 * (df + db(0.5 * (b0 + b1)))
        end_m = []
        for f, inward, bb in ((ends[0], +1, b0), (ends[1], -1, b1)):
            errs = end_rows(U, uw, f, rows_, inward)
            mpd = float(np.linalg.norm(fence_pt(bb + 0.5) + mid * normal(bb + 0.5) - fence_pt(bb - 0.5) - mid * normal(bb - 0.5)))
            end_m.append(None if len(errs) < 3 else dict(median=round(float(np.median(errs)) * mpd, 2),
                                                          max_abs=round(float(np.max(np.abs(errs))) * mpd, 2), rows=len(errs)))
        ends_ok &= all(e is not None and abs(e["median"]) <= LIMIT_END for e in end_m)
        a = np.abs(np.r_[ef, eb])
        allerr += list(a)
        rep["roofs"][name] = dict(front=dict(median=round(float(np.median(ef)), 2) if ef else None,
                                             p90_abs=round(float(np.percentile(np.abs(ef), 90)), 2) if ef else None),
                                  back=dict(median=round(float(np.median(eb)), 2) if eb else None,
                                            p90_abs=round(float(np.percentile(np.abs(eb), 90)), 2) if eb else None),
                                  ends_m=end_m, unclear=miss, n=len(a))
    a = np.array(allerr)
    rep["all"] = dict(n=int(len(a)), median_abs=round(float(np.median(a)), 2), p90_abs=round(float(np.percentile(a, 90)), 2))
    rep["pass"] = bool(rep["all"]["median_abs"] <= LIMIT_MEDIAN and rep["all"]["p90_abs"] <= LIMIT_P90 and ends_ok)
    print(json.dumps(rep, indent=1))
    if len(sys.argv) > 6:
        U = uw.at(10.0)
        Image.fromarray(np.clip(np.nan_to_num(U[::-1]), 0, 255).astype(np.uint8)).save(sys.argv[6])


if __name__ == "__main__":
    main()
