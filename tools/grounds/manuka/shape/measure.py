"""Manuka's shape check: the turf edge traced on the aerial photo (trace.py) against the model's fence (build.py's
rf), in metres, and the field against its published size.

    python3 measure.py [--ge GE.png CAM_X CAM_Y CAM_H] [REPORT.json]

Without --ge the trace is on Esri's aerial photo; with it, on a calibrated straight-down Google Earth shot (heading 0,
tilt 0, (CAM_X, CAM_Y) under the camera, CAM_H over the turf: read off Google Earth's status bar).
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fit import ellipse_fit, fourier_fit  # noqa: E402
from trace import trace  # noqa: E402

MODEL = os.path.join(HERE, "..", "model")
LIMIT_RMS, LIMIT_MAX = 0.5, 1.5    # m: the fence against the trace


def model_fence():
    """build.py's fence radius by bearing, without Blender."""
    src = open(os.path.join(MODEL, "build.py")).read()
    i0 = src.index("# ---------------- the frame round the fence")
    i1 = src.index("def pol(")
    g = {"np": np, "math": math, "json": json, "os": os}
    g["D"] = json.load(open(os.path.join(MODEL, "manuka.json")))
    g["G"] = json.load(open(os.path.join(MODEL, "..", "osm", "geo.json")))
    g["C"] = np.array(g["D"]["C"])
    exec(src[i0:i1], g)
    return g["rf"], g["C"]


def main():
    src = None
    if len(sys.argv) > 1 and sys.argv[1] == "--ge":
        from trace import ge_topdown
        src = ge_topdown(sys.argv[2], float(sys.argv[5]), float(sys.argv[3]), float(sys.argv[4]))
        del sys.argv[1:6]
    bs, r, (im, x0, y0, res, keep) = trace(src=src)
    from common import C as TC
    f, coef, ok = fourier_fit(bs, r)
    rf, MC = model_fence()
    assert np.allclose(MC, TC)
    fit_r = f(bs)
    mod_r = np.array([rf(b) for b in bs])
    resid = r - fit_r
    d = mod_r - fit_r       # radial: model fence past the photo's fence (+ = model too big)
    xs = TC[0] + fit_r * np.sin(np.radians(bs)); ys = TC[1] + fit_r * np.cos(np.radians(bs))
    c, a, b, brg = ellipse_fit(xs, ys)
    rep = dict(
        trace=dict(points=int(np.isfinite(r).sum()), kept=int(ok.sum()), fit_rms=float(np.sqrt(np.mean(resid[ok] ** 2)))),
        photo_fence=dict(centre=list(map(float, c)), length=float(2 * a), width=float(2 * b), long_axis_bearing=float(brg)),
        model_vs_photo=dict(rms=float(np.sqrt(np.mean(d ** 2))), max=float(np.abs(d).max()), mean=float(d.mean()),
                            worst_bearing=float(bs[int(np.argmax(np.abs(d)))])),
        limits=dict(rms=LIMIT_RMS, max=LIMIT_MAX),
    )
    rep["pass"] = rep["model_vs_photo"]["rms"] <= LIMIT_RMS and rep["model_vs_photo"]["max"] <= LIMIT_MAX
    xm = TC[0] + mod_r * np.sin(np.radians(bs)); ym = TC[1] + mod_r * np.cos(np.radians(bs))
    c2, a2, b2, brg2 = ellipse_fit(xm, ym)
    rep["model_fence"] = dict(centre=list(map(float, c2)), length=float(2 * a2), width=float(2 * b2), long_axis_bearing=float(brg2))
    rep["by_bearing"] = {int(k): round(float(v), 2) for k, v in zip(bs[::30], d[::30])}
    print(json.dumps(rep, indent=1))
    if len(sys.argv) > 1:
        json.dump(dict(rep, fourier=coef.tolist()), open(sys.argv[1], "w"), indent=1)


if __name__ == "__main__":
    main()
