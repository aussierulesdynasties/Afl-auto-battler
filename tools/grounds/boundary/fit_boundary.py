"""Fit each traced ground's boundary line to the smooth curve the match plays on.

Input: tools/grounds/boundary/traced/<slug>.json, one per ground, traced from Google Earth by the ground
threads, in the model's own metres (the glb x/z frame GroundModels.FIT uses):
  line   [[x, z], ...]  the middle of the painted boundary line, all the way round
  goals  [[x, z], [x, z]]  the middle of each goal line
  centre [x, z]  the centre circle (optional; checked against the goals' midpoint)
  fence  [[x, z], ...]  the fence or grass edge (optional)

The match's frame (MatchMotion): origin the midpoint of the two goals, x along the line through them,
y across (the glb's z after the turn). By the Laws the centre circle is midway between the goals, so the
goals alone fix the frame; a measured centre is reported against it, never used.

The curve: r(t) = a0 + sum_k (a_k cos kt + b_k sin kt), t from +x towards +y, about that origin. A polar
Fourier series is smooth everywhere and closed by construction; it is fitted by least squares with the
smallest order whose fit is within ORDER_SLACK of the best order up to MAX_ORDER (so a gap in the trace
is never filled with a wiggle). Its error is measured as each traced point's distance to the curve,
not along the ray.

Output: data/ground_boundaries.json, read by GroundModels.shape_for. Run: python3 tools/grounds/boundary/fit_boundary.py
"""
import glob
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "data", "ground_boundaries.json")
MAX_ORDER = 16
ORDER_SLACK = 0.03   # m of rms: a higher order must buy more than this to be used
MAX_UNSEEN_DEG = 25.0  # a longer unseen stretch of the line would be the fit guessing: the ground is held
OUTLIER = 1.0        # m: a traced point this far off the first fit is left out (fit)
DENSE = 7200         # samples of the fitted curve when measuring distance to it


def fit_angles():
    """GroundModels.FIT's long-axis angle per slug (degrees, +x towards +z), so a ground keeps its ends."""
    src = open(os.path.join(ROOT, "scripts", "ui", "match", "GroundModels.gd"), encoding="utf-8").read()
    block = src[src.index("const FIT := {"):]
    block = block[:block.index("\n}")]
    out = {}
    for m in re.finditer(r'"(\w+)":\s*\[([^\]]+)\]', block):
        vals = [float(v) for v in m.group(2).split(",")]
        out[m.group(1)] = vals[3]
    return out


def design(t, order):
    cols = [np.ones_like(t)]
    for k in range(1, order + 1):
        cols += [np.cos(k * t), np.sin(k * t)]
    return np.stack(cols, axis=1)


def curve(coef, n=DENSE):
    t = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    r = design(t, (len(coef) - 1) // 2) @ coef
    return np.stack([r * np.cos(t), r * np.sin(t)], axis=1)


def distances(pts, coef):
    """Each point's distance to the closed curve (dense polyline, point-to-segment)."""
    c = curve(coef)
    a, b = c, np.roll(c, -1, axis=0)
    ab = b - a
    ab2 = np.maximum((ab * ab).sum(1), 1e-12)
    out = np.empty(len(pts))
    for i, p in enumerate(pts):
        # Only the segments near this point's bearing matter; search a window round it.
        k = int(round((math.atan2(p[1], p[0]) % (2 * math.pi)) / (2 * math.pi) * len(c)))
        idx = np.arange(k - 200, k + 200) % len(c)
        ap = p - a[idx]
        s = np.clip((ap * ab[idx]).sum(1) / ab2[idx], 0.0, 1.0)
        q = a[idx] + ab[idx] * s[:, None]
        out[i] = np.sqrt(((p - q) ** 2).sum(1)).min()
    return out


def fit(pts):
    """The fit, then once more without any point further than OUTLIER from it (a misread window: a real
    painted line has no 1 m step in it). The points left out are reported with their bearings."""
    coef, order, stats = _fit(pts)
    d = distances(pts, coef)
    bad = d > max(OUTLIER, 4.0 * stats["rms_m"])
    if bad.any() and (~bad).sum() >= 0.9 * len(pts):
        coef, order, stats = _fit(pts[~bad])
        stats["left_out"] = [{"at": [round(float(q[0]), 1), round(float(q[1]), 1)], "off_m": round(float(o), 2)}
                             for q, o in zip(pts[bad], d[bad])]
    return coef, order, stats


def _fit(pts):
    t = np.arctan2(pts[:, 1], pts[:, 0])
    r = np.hypot(pts[:, 0], pts[:, 1])
    best = {}
    for order in range(2, MAX_ORDER + 1):
        coef, *_ = np.linalg.lstsq(design(t, order), r, rcond=None)
        best[order] = (coef, float(np.sqrt(np.mean((design(t, order) @ coef - r) ** 2))))
    floor = min(v[1] for v in best.values())
    order = min(o for o, v in best.items() if v[1] <= floor + ORDER_SLACK)
    coef = best[order][0]
    d = distances(pts, coef)
    return coef, order, {"n": int(len(pts)), "order": order, "rms_m": round(float(np.sqrt(np.mean(d * d))), 3),
                         "p95_m": round(float(np.percentile(d, 95)), 3), "max_m": round(float(d.max()), 3)}


def largest_gap_deg(pts):
    t = np.sort(np.degrees(np.arctan2(pts[:, 1], pts[:, 0])) % 360.0)
    gaps = np.diff(np.concatenate([t, [t[0] + 360.0]]))
    return round(float(gaps.max()), 2)


def r_at(coef, t):
    return float((design(np.array([t]), (len(coef) - 1) // 2) @ coef)[0])


def main():
    angles = fit_angles()
    out = {}
    report = []
    for path in sorted(glob.glob(os.path.join(HERE, "traced", "*.json"))):
        d = json.load(open(path, encoding="utf-8"))
        slug = d.get("slug") or os.path.splitext(os.path.basename(path))[0]
        g0, g1 = np.array(d["goals"][0], float), np.array(d["goals"][1], float)
        mid = (g0 + g1) / 2.0
        a = math.atan2(g1[1] - g0[1], g1[0] - g0[0])
        # Keep the ground's +x end where its FIT row has it (sun, wind and the stands are laid that way).
        if slug in angles:
            want = math.radians(angles[slug])
            if math.cos(a - want) < 0.0:
                a += math.pi
        a = math.atan2(math.sin(a), math.cos(a))
        u = np.array([math.cos(a), math.sin(a)])
        v = np.array([-math.sin(a), math.cos(a)])

        def frame(p):
            p = np.asarray(p, float) - mid
            return np.stack([p @ u, p @ v], axis=-1)

        line = frame(d["line"])
        # Only the painted line actually seen counts; a stretch the trace bridged is not a measurement.
        if "line_seen" in d:
            line = line[np.array(d["line_seen"], bool)]
        gap = largest_gap_deg(line)
        if gap > MAX_UNSEEN_DEG:
            report.append("%-10s HELD: %.0f deg of the line unseen in one stretch (most allowed %.0f)" % (slug, gap, MAX_UNSEEN_DEG))
            continue
        coef, order, stats = fit(line)
        goal_x = float(np.linalg.norm(g1 - g0) / 2.0)
        entry = {
            "frame": [round(float(mid[0]), 3), round(float(mid[1]), 3), round(math.degrees(a), 3)],
            "goal_x": round(goal_x, 3),
            "boundary": [round(float(c), 4) for c in coef],
            "boundary_fit": stats | {"largest_gap_deg": largest_gap_deg(line)},
            # Where the curve crosses the line through the goals, against the goal lines themselves:
            # the goal line is the boundary between the behind posts.
            "ends_vs_goal_lines_m": [round(r_at(coef, 0.0) - goal_x, 3), round(r_at(coef, math.pi) - goal_x, 3)],
            "source": d.get("source", ""),
            "trace_error": d.get("error_m"),
        }
        if d.get("centre") is not None:
            c = frame(d["centre"])
            entry["centre_vs_goals_mid_m"] = [round(float(c[0]), 3), round(float(c[1]), 3)]
        if d.get("fence"):
            fence = frame(d["fence"])
            fcoef, _, fstats = fit(fence)
            entry["fence"] = [round(float(c), 4) for c in fcoef]
            entry["fence_fit"] = fstats | {"largest_gap_deg": largest_gap_deg(fence)}
            # The run-off between the line and the fence, every 10 degrees round from the +x goal.
            tt = np.radians(np.arange(0, 360, 10))
            gap = design(tt, (len(fcoef) - 1) // 2) @ fcoef - design(tt, order) @ coef
            entry["runoff_m"] = {"min": round(float(gap.min()), 2), "max": round(float(gap.max()), 2)}
        out[slug] = entry
        report.append("%-10s goals %.1f m apart, order %d, line fit rms %.2f m p95 %.2f max %.2f (n %d, gap %.1f deg); "
                      "ends vs goal lines %s" % (slug, 2 * goal_x, order, stats["rms_m"], stats["p95_m"], stats["max_m"],
                                                 stats["n"], entry["boundary_fit"]["largest_gap_deg"],
                                                 entry["ends_vs_goal_lines_m"]))
    doc = {"_about": "Each traced ground's boundary line as the match plays it (tools/grounds/boundary/fit_boundary.py). "
                     "frame: [x, z, degrees] in the model's glb metres: the goals' midpoint and the line through them. "
                     "boundary/fence: r(t) = a0 + sum(a_k cos kt + b_k sin kt) about that midpoint, t from the +x goal "
                     "towards +y (the glb's +z after the turn).",
           "grounds": out}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    print("\n".join(report))
    print("wrote", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    sys.exit(main())
