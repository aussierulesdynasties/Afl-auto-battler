"""Manuka against Google Earth from oblique cameras: the roof heights the straight-down checks cannot see.

    python3 oblique.py plan  WORK                 # WORK/views.json: each view's Google Earth url (+ pts.json)
    node    ge_probe.js WORK <name> <url>         # per view: the shot and the status bar under 15 pixels
    python3 oblique.py solve WORK                 # each Google Earth camera solved from what the status bar read
    python3 oblique.py plan_heights WORK          # the pixels over our roofs in each solved view
    sh WORK/probe_heights.sh                      # Google Earth's status bar under each of them
    python3 oblique.py heights WORK               # Google Earth's roof heights against ours
    godot ... preinspect_look.gd -- WORK/ours manuka $(cat WORK/specs.txt)   # optional: ours from the same cameras

solve: the status bar gives the 3D point under each probed pixel (latitude, longitude, height; the turf is 569 m)
and the camera's altitude. The camera (position, heading, tilt, roll) is fitted to them by least squares with the
crop's vertical field of view fixed at 25.58 degrees (cb53de5); the fit's residual in pixels is reported.
heights: Google Earth's own 3D point under pixels aimed at our roofs (bearings every 2 degrees, three depths
across each roof). Pass: median |error| 1.0 m and 90th percentile 2.0 m (the status bar rounds heights to the metre).
"""
import glob
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from matchspace import spec  # noqa: E402
import roofcheck as R  # noqa: E402

LAT0, LON0 = -35.3180995, 149.1345344
TURF = 569.0
FOV = 25.58
W, H = 1280, 720
F = (H / 2) / math.tan(math.radians(FOV / 2))
LIMIT_H_MEDIAN, LIMIT_H_P90 = 1.0, 2.0

# heading (Google Earth's, the way the camera looks), tilt, range: four sides plus two lower corners
VIEWS = [("from_s", 0, 60, 380), ("from_w", 90, 60, 380), ("from_n", 180, 60, 380), ("from_e", 270, 60, 380),
         ("from_sw", 45, 68, 330), ("from_ne", 225, 68, 330)]


def ll(x, y):
    return LAT0 + y / 110574.0, LON0 + x / (111320.0 * math.cos(math.radians(LAT0)))


def xy(lat, lon):
    return (lon - LON0) * 111320.0 * math.cos(math.radians(LAT0)), (lat - LAT0) * 110574.0


def basis(h, t, r):
    h, t, r = map(math.radians, (h, t, r))
    fwd = np.array([math.sin(t) * math.sin(h), math.sin(t) * math.cos(h), -math.cos(t)])
    right = np.array([math.cos(h), -math.sin(h), 0.0])
    up = np.cross(right, fwd)
    right, up = right * math.cos(r) + up * math.sin(r), up * math.cos(r) - right * math.sin(r)
    return right, up, fwd


def project(cam, P):
    """cam = (x, y, z, heading, tilt, roll) in the model frame (z over the turf); P (n, 3) -> (n, 2) pixels, depth"""
    right, up, fwd = basis(*cam[3:])
    d = np.atleast_2d(P) - np.array(cam[:3])
    z = d @ fwd
    return np.c_[W / 2 + F * (d @ right) / z, H / 2 - F * (d @ up) / z], z


def plan(work):
    os.makedirs(work, exist_ok=True)
    pts = [[u, v] for v in (90, 250, 410, 570, 680) for u in (160, 640, 1120)]
    json.dump(pts, open(os.path.join(work, "pts.json"), "w"))
    out = {}
    for name, h, t, rng in VIEWS:
        lat, lon = ll(*R.C)
        out[name] = dict(h=h, t=t, d=rng, url="https://earth.google.com/web/@%.7f,%.7f,%.1fa,%.1fd,35y,%.1fh,%.1ft,0r"
                         % (lat, lon, TURF, rng, h, t))
    json.dump(out, open(os.path.join(work, "views.json"), "w"), indent=1)
    for k, v in out.items():
        print(k, v["url"])


def ocr(png):
    im = Image.open(png)
    im = im.resize((im.width * 3, im.height * 3), Image.LANCZOS)
    tmp = png + ".x.png"
    im.save(tmp)
    s = subprocess.run(["tesseract", tmp, "-", "--psm", "7"], capture_output=True, text=True).stdout
    os.remove(tmp)
    cam = re.search(r"Camera:\s*([\d,]+)\s*m", s)
    pt = re.search(r"(\d+)°(\d+)'([\d.]+)\"S\s+(\d+)°(\d+)'([\d.]+)\"E\s+([\d,]+)\s*m", s)
    if not (cam and pt):
        return None
    g = [float(x) for x in pt.groups()[:6]]
    lat = -(g[0] + g[1] / 60 + g[2] / 3600); lon = g[3] + g[4] / 60 + g[5] / 3600
    return float(cam.group(1).replace(",", "")), lat, lon, float(pt.group(7).replace(",", ""))


def solve(work):
    views = json.load(open(os.path.join(work, "views.json")))
    pts = json.load(open(os.path.join(work, "pts.json")))
    specs = []
    for name, v in views.items():
        if not os.path.exists(os.path.join(work, name + ".png")):
            continue
        uv, P, cams = [], [], []
        for i, p in enumerate(pts):
            f = os.path.join(work, "%s_%d.png" % (name, i))
            r = ocr(f) if os.path.exists(f) else None
            if r is None:
                continue
            cams.append(r[0] - TURF)
            uv.append(p); P.append([*xy(r[1], r[2]), r[3] - TURF])
        uv, P = np.array(uv, float), np.array(P)
        hc = float(np.median(cams))
        t = math.radians(v["t"]); h = math.radians(v["h"])
        x0 = [R.C[0] - v["d"] * math.sin(t) * math.sin(h), R.C[1] - v["d"] * math.sin(t) * math.cos(h), hc, v["h"], v["t"], 0.0]

        def res(c):
            q, _ = project(c, P)
            return np.r_[(q - uv).ravel(), (c[2] - hc) / 0.5 * 0.2]   # the status bar's camera altitude, to the metre
        for _ in range(2):                                            # drop a probe that missed (OCR or the sky)
            s = least_squares(res, x0, loss="soft_l1", f_scale=3.0)
            q, _ = project(s.x, P); e = np.linalg.norm(q - uv, axis=1)
            keep = e < max(6.0, 3 * np.median(e))
            uv, P = uv[keep], P[keep]; x0 = s.x
        q, _ = project(s.x, P); e = np.linalg.norm(q - uv, axis=1)
        v["cam"] = [round(float(c), 3) for c in s.x]
        v["solve"] = dict(points=int(len(P)), rms_px=round(float(np.sqrt((e ** 2).mean())), 2),
                          max_px=round(float(e.max()), 2), status_bar_cam_m=hc)
        print(name, v["cam"], v["solve"])
        c = np.array(s.x[:3]); _, _, fwd = basis(*s.x[3:])
        look = c + fwd * 100.0
        if abs(s.x[5]) > 0.3:
            print("  roll %.2f deg: our render has none" % s.x[5])
        specs.append(spec(name, c, look, FOV))
    json.dump(views, open(os.path.join(work, "views.json"), "w"), indent=1)
    open(os.path.join(work, "specs.txt"), "w").write(" ".join(specs) + "\n")


def roof_samples():
    """(roof, b, d, our roof's top z there) over every roof: bearings every 2 degrees, three depths across"""
    out = []
    for rec in R.roofs():
        name, b0, b1, df, db, h = rec[:6]
        for b in np.arange(b0 + 1.5, b1 - 1.4, 2.0):
            for f in (0.2, 0.5, 0.8):
                d = df + 1.0 + f * (db(b) - df - 2.0)
                z = roof_z(name, b, d)
                out.append((name, float(b), float(d), float(z)))
    return out


def roof_z(name, b, d):
    if name.startswith("stand ") or name.startswith("canopy "):
        S = R.D["astands"][name.split()[1]]; dz = 0.6 if name.startswith("canopy") else 0.0
        return S["rfz"] + (S["rbz"] - S["rfz"]) * (d - S["rf"]) / (R.RB(S, b) - S["rf"]) + dz
    if name == "media deck":
        return R.D["media"]["z_roof"] + 0.1
    return R.D["bradman"]["roof_top"]


def roof_at(x, y):
    """(roof, our top z) for a plan point at least 0.75 m inside one of our roofs, else None"""
    b = math.degrees(math.atan2(x - R.C[0], y - R.C[1])) % 360
    for _ in range(3):                                   # the normal through (x, y) meets the fence at bearing b
        f = R.fence_pt(b)[0]; n = R.normal(b)[0]; t = np.array([n[1], -n[0]])
        b -= float(np.dot(np.array([x, y]) - f, t)) / max(1e-6, float(np.linalg.norm(R.fence_pt(b + 0.5)[0] - R.fence_pt(b - 0.5)[0])))
    d = float(np.dot(np.array([x, y]) - R.fence_pt(b)[0], R.normal(b)[0]))
    for rec in R.roofs():
        name, b0, b1, df, db = rec[:5]
        bb = b if b >= b0 - 1e-6 else b + 360
        if b0 + 0.5 <= bb <= b1 - 0.5 and df + 0.75 <= d <= db(bb) - 0.75:
            return name, roof_z(name, bb, d)
    return None


def plan_heights(work):
    """per solved view, the pixels over our roofs (pts_<view>.json) and a script to probe them"""
    views = json.load(open(os.path.join(work, "views.json")))
    sh = []
    for name, v in views.items():
        if "cam" not in v:
            continue
        S = roof_samples()
        P = np.array([[*(R.fence_pt(b)[0] + d * R.normal(b)[0]), z] for _, b, d, z in S])
        q, z = project(v["cam"], P)
        keep = [i for i in range(len(S)) if z[i] > 0 and 30 <= q[i][0] < W - 30 and 30 <= q[i][1] < H - 30]
        d = os.path.join(work, "h_" + name); os.makedirs(d, exist_ok=True)
        json.dump([[round(float(q[i][0]), 1), round(float(q[i][1]), 1)] for i in keep], open(os.path.join(d, "pts.json"), "w"))
        json.dump([S[i] for i in keep], open(os.path.join(d, "samples.json"), "w"))
        sh.append('node %s %s %s "%s"' % (os.path.join(HERE, "ge_probe.js"), d, name, v["url"]))
    open(os.path.join(work, "probe_heights.sh"), "w").write("\n".join(sh) + "\n")
    print("\n".join(sh))


def heights(work):
    """Google Earth's own height under each probed pixel against our roof's top at the point Google Earth hit (so a
    roof that is too high or low, which moves the hit along the ray, is still compared where it was hit). A probe whose
    point is not on the roof we aimed at, at least 0.75 m in from its edges, hit something else first (a tower, a
    tree, the roof below) and is left out and counted; so is a hit more than 8 m over our roof (a light tower's
    head between the camera and the roof)."""
    views = json.load(open(os.path.join(work, "views.json")))
    rep = {"limits": {"median_abs_m": LIMIT_H_MEDIAN, "p90_abs_m": LIMIT_H_P90,
                      "note": "the status bar gives heights to the whole metre"}, "roofs": {}}
    per, allz, off, over = {}, [], 0, 0
    for name in views:
        d = os.path.join(work, "h_" + name)
        if not os.path.exists(os.path.join(d, "samples.json")):
            continue
        S = json.load(open(os.path.join(d, "samples.json")))
        for i, (roof, b, dd, z) in enumerate(S):
            f = os.path.join(d, "%s_%d.png" % (name, i))
            r = ocr(f) if os.path.exists(f) else None
            if r is None:
                off += 1; continue
            hit = roof_at(*xy(r[1], r[2]))
            if hit is None or hit[0] != roof:
                off += 1; continue
            e = (r[3] - TURF) - hit[1]
            if e > 8.0:                  # something standing over the roof hit first (a light tower's head)
                over += 1; continue
            per.setdefault(roof, []).append(e); allz.append(abs(e))
    for k, a in per.items():
        rep["roofs"][k] = dict(n=len(a), median=round(float(np.median(a)), 2), p90_abs=round(float(np.percentile(np.abs(a), 90)), 2))
    a = np.array(allz)
    rep["all"] = dict(n=int(len(a)), left_out=off, over_the_roof=over, median_abs=round(float(np.median(a)), 2),
                      p90_abs=round(float(np.percentile(a, 90)), 2))
    rep["pass"] = bool(rep["all"]["median_abs"] <= LIMIT_H_MEDIAN and rep["all"]["p90_abs"] <= LIMIT_H_P90)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    cmd, work = sys.argv[1], sys.argv[2]
    {"plan": lambda: plan(work), "solve": lambda: solve(work),
     "plan_heights": lambda: plan_heights(work), "heights": lambda: heights(work)}[cmd]()
