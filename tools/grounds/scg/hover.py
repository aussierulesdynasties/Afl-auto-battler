"""Building heights and walls measured with Google Earth's own 3D readout (SCG rebuild, 2026-11-22).

    python3 tools/grounds/scg/hover.py plan <workdir>      # points to hover -> <workdir>/hover_points.json
    node tools/grounds/ge_hover.js <workdir>/hover_points.json <workdir>/hover
    python3 tools/grounds/scg/hover.py read <workdir>      # -> <workdir>/hover.json and a table

Google Earth's status bar gives the latitude, longitude and height above sea level of whatever is under the
mouse, on its 3D mesh (to 0.01 seconds, about 0.3 m, and to the metre). So no height here is judged from a
picture: each is Google Earth's own number for a point on the roof or the ground. For each nearby building
(near_buildings.bin, unmapped.json), in a straight-down view of Google Earth centred on it:

- roof points: a grid 2 m and more inside its walls;
- a line across each of its four longest walls, at the middle, from 3 m inside to 6 m outside every 0.5 m:
  where the readout drops from roof to ground is where the wall really is, in metres from the mapped wall,
  and the outer points are the ground's height there.

Tried first and dropped (2026-11-22): fitting outlines and heights to the edges in Google Earth's shots, and
stereo between its five views of each patch; both disagreed with themselves by 2-3 m from shot to shot.

read gives each building its ground (the median of the line ends outside, 4-6 m out), its eave (a flat roof:
the median of the roof points; a pitched one: the low quarter of them), its ridge (the highest roof
points' median) and each wall's move; heights are over the ground beside it, and the ground is also given
over the SCG's turf (ge_compare's ge_alt).
"""
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Point, Polygon

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, ".."))
import ge_compare as gc       # noqa: E402
import gecam                   # noqa: E402

LAT0, LON0 = -33.8916, 151.2248
KX, KY = 111320.0 * math.cos(math.radians(LAT0)), 110574.0


def specs():
    import facades as fc
    s = {str(k): v[:3] for k, v in fc.SPEC.items()}
    for e in json.load(open(os.path.join(ROOT, "unmapped.json"))):
        s["u%d" % e["ge_blob"]] = (e["eave"], e["roof"], e["rise"])
    return s


def move_walls(V, d):
    """Closed outline V with wall k moved d[k] m outward along its normal; each corner is where its two moved
    walls cross (a corner between two walls nearly in line just moves with them)."""
    poly = Polygon(V[:-1])
    n = len(V) - 1
    P0, T = [], []
    for k in range(n):
        a, b = V[k], V[k + 1]
        t = (b - a) / max(np.linalg.norm(b - a), 1e-9)
        nrm = np.array([t[1], -t[0]])
        if poly.contains(Point(*((a + b) / 2 + nrm * 0.3))):
            nrm = -nrm
        P0.append(a + nrm * d[k])
        T.append((t, nrm))
    out = []
    for k in range(n):
        (t1, n1), (t2, n2) = T[k - 1], T[k]
        m = np.array([t1, -t2]).T
        if abs(np.linalg.det(m)) < 0.05:
            out.append(V[k] + n2 * d[k])
            continue
        s_ = np.linalg.solve(m, P0[k] - P0[k - 1])
        out.append(P0[k - 1] + t1 * s_[0])
    out.append(out[0])
    return np.array(out)


def walls(q, n=4):
    """The building's n longest walls: (k, a, b, outward normal)."""
    ccw = Polygon(q[:-1]).exterior.is_ccw
    out = []
    for k in range(len(q) - 1):
        a, b = q[k], q[k + 1]
        L = np.linalg.norm(b - a)
        t = (b - a) / max(L, 1e-9)
        nrm = np.array([t[1], -t[0]]) if ccw else np.array([-t[1], t[0]])   # x east, z south: this is outward
        out.append((L, k, a, b, nrm))
    # check the normal really points out
    poly = Polygon(q[:-1])
    fixed = []
    for L, k, a, b, nrm in sorted(out, key=lambda r: -r[0])[:n]:
        m = (a + b) / 2
        if poly.contains(Point(*(m + nrm * 0.5))):
            nrm = -nrm
        fixed.append((k, a, b, nrm))
    return fixed


def plan(work):
    """A straight-down view centred on each building (so it sits near the middle, where a roof's height moves
    it least) and the points to hover in it."""
    g = gc.GROUNDS["scg"]
    sp = specs()
    lst, meta = [], {}
    for name, q in gecam.buildings():
        if name not in sp:
            continue
        c = q[:-1].mean(0)
        ext = float(np.max(np.linalg.norm(q[:-1] - c, axis=1))) * 2 + 16.0
        d = max(250.0, ext / 0.42)
        v = {"name": "hv_" + name, "h": 0, "t": 0, "d": d, "at": [c[0] - gecam.CX, gecam.CZ - c[1], 0]}
        lat, lon = gc.latlon(g, v["at"][0], v["at"][1])
        url = "https://earth.google.com/web/@%.7f,%.7f,%.1fa,%.1fd,%gy,0h,0t,0r" % (lat, lon, g["ge_alt"], d, gc.GE_FOV)
        P = gecam.cam_parts(v, work)
        guess = sp[name][0] + 8.0              # the land east of the SCG stands 5-11 m over its turf
        poly = Polygon(q[:-1])
        pts, tags = [], []
        inner = poly.buffer(-2.0)
        if not inner.is_empty:
            x0, z0, x1, z1 = inner.bounds
            sp_ = max(3.0, math.sqrt(inner.area / 12))
            for x in np.arange(x0 + sp_ / 2, x1, sp_):
                for z in np.arange(z0 + sp_ / 2, z1, sp_):
                    if inner.contains(Point(x, z)):
                        pts.append((x, guess, z))
                        tags.append(["roof"])
        for k, a, b, nrm in walls(q):
            m = (a + b) / 2
            for o in np.arange(-3.0, 6.01, 0.5):
                p = m + nrm * o
                pts.append((p[0], guess if o < 0 else guess * 0.5, p[1]))
                tags.append(["wall", int(k), float(o)])
        px = []
        for (x, y, z), t in zip(pts, tags):
            u, w = P(np.array(x), np.array(y), np.array(z))
            if 5 < u < 1275 and 55 < w < 715:
                px.append([float(u), float(w)])
                meta.setdefault(v["name"], []).append([name] + t)
        lst.append([v["name"], url, px])
    json.dump(lst, open(os.path.join(work, "hover_points.json"), "w"))
    json.dump(meta, open(os.path.join(work, "hover_meta.json"), "w"))
    print("%d points in %d views" % (sum(len(p) for _, _, p in lst), len(lst)))


GROUND_CLASSES = ("ASPHALT", "PARKING", "PATH", "PAVED", "CONCOURSE", "LAWN", "PITCH", "GOLF", "BASE", "URBAN")


def plan_terrain(work, step=50.0, half=650.0):
    """The land's height: a point every `step` m over the surrounds, each moved (up to 15 m) onto open ground
    (a road, path, paving or grass in the surrounds map, off Google Earth's canopy, 8 m and more from any
    building), hovered in six straight-down views from 1,000 m."""
    import surrounds as sr
    g = gc.GROUNDS["scg"]
    mp = np.asarray(Image.open(os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "scg", "surrounds.webp")).convert("RGB")).astype(np.int16)
    canopy = np.asarray(Image.open(os.path.join(ROOT, "canopy_ge.png")).convert("L")) > 0
    S = mp.shape[0]
    pal = np.array([getattr(sr, c) for c in GROUND_CLASSES], np.int16)
    # open ground on the map's grid (1 m a pixel, model 0, 0 in the middle)
    ok = np.zeros(mp.shape[:2], bool)
    for c in pal:
        ok |= np.abs(mp - c).max(-1) <= 6
    ok &= ~canopy
    blk = Image.new("1", (S, S), 0)
    d = ImageDraw.Draw(blk)
    raw = np.fromfile(os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "scg", "buildings.bin"), "<f4")
    i = 0
    outlines = []
    while i < len(raw):                    # buildings.bin: n, height, then n corners (x, z)
        n = int(raw[i])
        outlines.append(raw[i + 2:i + 2 + 2 * n].reshape(-1, 2))
        i += 2 + 2 * n
    outlines += [q for _, q in gecam.buildings()]
    for q in outlines:
        if len(q) >= 3:
            d.polygon([(x + S / 2, z + S / 2) for x, z in q], fill=1, outline=1)
    from scipy import ndimage as nd
    near_b = nd.binary_dilation(np.asarray(blk, bool), iterations=8)
    ok &= ~near_b
    nodes = []
    for x in np.arange(-half, half + 0.1, step):
        for z in np.arange(-half, half + 0.1, step):
            ix, iz = int(x + S / 2), int(z + S / 2)
            w = ok[max(iz - 15, 0):iz + 16, max(ix - 15, 0):ix + 16]
            if not w.any():
                continue
            zz, xx = np.nonzero(w)
            zz, xx = zz + max(iz - 15, 0), xx + max(ix - 15, 0)
            k = int(np.argmin((zz - iz) ** 2 + (xx - ix) ** 2))
            nodes.append((xx[k] - S / 2 + 0.5, zz[k] - S / 2 + 0.5))
    lst, meta = [], {}
    k = 0
    for cx in (-300.0, 300.0):
        for cz in (-430.0, 0.0, 430.0):
            v = {"name": "tv_%d" % k, "h": 0, "t": 0, "d": 1000.0, "at": [cx - gecam.CX, gecam.CZ - cz, 0]}
            k += 1
            lat, lon = gc.latlon(g, v["at"][0], v["at"][1])
            url = "https://earth.google.com/web/@%.7f,%.7f,%.1fa,%.1fd,%gy,0h,0t,0r" % (lat, lon, g["ge_alt"], v["d"], gc.GE_FOV)
            P = gecam.cam_parts(v, work)
            px = []
            for x, z in nodes:
                if not (cx - 300 <= x < cx + 300 and cz - 215 <= z < cz + 215):
                    continue
                u, w = P(np.array(x), np.array(5.0), np.array(z))
                if 5 < u < 1275 and 55 < w < 715:
                    px.append([float(u), float(w)])
                    meta.setdefault(v["name"], []).append(["terrain", float(x), float(z)])
            lst.append([v["name"], url, px])
    json.dump(lst, open(os.path.join(work, "terrain_points.json"), "w"))
    json.dump(meta, open(os.path.join(work, "terrain_meta.json"), "w"))
    print("%d terrain points (of %d nodes) in %d views" % (sum(len(p) for _, _, p in lst), len(nodes), len(lst)))


_CACHE = {}


def parse(path):
    """(x, z model metres, height above sea level m) from one status-bar strip, or None. Remembered beside the
    strips (parsed.json) so a re-read doesn't run tesseract again."""
    d = os.path.dirname(path)
    if d not in _CACHE:
        f = os.path.join(d, "parsed.json")
        _CACHE[d] = json.load(open(f)) if os.path.exists(f) else {}
    key = os.path.basename(path)
    if key not in _CACHE[d]:
        _CACHE[d][key] = _parse(path)
        if len(_CACHE[d]) % 100 == 0:
            save_cache()
    return _CACHE[d][key]


def save_cache():
    for d, c in _CACHE.items():
        json.dump(c, open(os.path.join(d, "parsed.json"), "w"))


def _parse(path):
    im = Image.open(path).convert("L")
    big = path[:-4] + "_x4.png"
    im.resize((im.width * 4, im.height * 4), Image.LANCZOS).save(big)
    txt = subprocess.run(["tesseract", big, "-", "--psm", "7"], capture_output=True, text=True).stdout
    os.remove(big)
    m = re.search(r"(\d+)\D+(\d+)'\s*([\d.]+)\"?\s*S\s+(\d+)\D+(\d+)'\s*([\d.]+)\"?\s*E\s+(-?\d+)\s*m", txt)
    if not m:
        return None
    g = [float(x) for x in m.groups()]
    lat = -(g[0] + g[1] / 60 + g[2] / 3600)
    lon = g[3] + g[4] / 60 + g[5] / 3600
    return (lon - LON0) * KX, -(lat - LAT0) * KY, g[6]


def read(work):
    meta = json.load(open(os.path.join(work, "hover_meta.json")))
    turf = gc.GROUNDS["scg"]["ge_alt"]
    sp = specs()
    rec = {}
    stale = 0
    for vn, tags in meta.items():
        prev = None
        for i, t in enumerate(tags):
            f = os.path.join(work, "hover", "%s_%d.png" % (vn, i))
            if not os.path.exists(f):
                continue
            r = parse(f)
            if r is None:
                continue
            if prev is not None and abs(r[0] - prev[0]) < 0.05 and abs(r[1] - prev[1]) < 0.05:
                stale += 1               # the status bar hadn't caught up with the mouse: the last point's readout
                continue
            prev = r
            rec.setdefault(t[0], []).append((t[1:], r))
    save_cache()
    print("%d readouts dropped as stale" % stale)
    blds = dict(gecam.buildings())
    out = {}
    gpts = []
    print("%-5s %-7s %7s %6s %6s %6s  %-11s %s" % ("bldg", "kind", "ground", "eave", "ridge", "n", "was e/r", "walls: moved m (outward +)"))
    for name, rows in rec.items():
        q = blds[name]
        poly = Polygon(q[:-1])
        roof = [r[2] for t, r in rows if t[0] == "roof" and poly.buffer(-1.0).contains(Point(r[0], r[1]))]
        ground = []
        wall = {}
        for t, r in rows:
            if t[0] != "wall":
                continue
            wall.setdefault(t[1], []).append((t[2], r))
            if t[2] >= 4.0:
                ground.append(r[2])
                gpts.append([r[0], r[1], r[2] - turf])
        if not roof or not ground:
            print("%-5s too few readouts (roof %d, ground %d)" % (name, len(roof), len(ground)))
            continue
        g = float(np.median(ground))
        roof = np.array(roof) - g
        kind = sp[name][1]
        if kind in ("gable", "hip", "monitor", "vault"):
            eave = float(np.percentile(roof, 20))
            ridge = float(np.median(np.sort(roof)[-max(1, len(roof) // 4):]))
        else:
            eave, ridge = float(np.median(roof)), None
        moves = {}
        for k, lst in wall.items():
            # where the readout crosses halfway from the ground to the roof, measured along the line by the
            # readout's own lat/lon (from the mapped wall, outward +)
            a, b = q[k], q[k + 1]
            tt = (b - a) / np.linalg.norm(b - a)
            nrm = np.array([tt[1], -tt[0]])
            if poly.contains(Point(*((a + b) / 2 + nrm * 0.5))):
                nrm = -nrm
            prof = sorted((float((np.array(r[:2]) - (a + b) / 2) @ nrm), r[2] - g) for _, r in lst)
            half = (eave if eave > 2 else max(roof)) / 2
            cross = None
            for (d0, h0), (d1, h1) in zip(prof[:-1], prof[1:]):
                if h0 >= half > h1:
                    cross = d0 + (d1 - d0) * (h0 - half) / max(h0 - h1, 1e-6)
            moves[int(k)] = None if cross is None else round(cross, 2)
        d = np.zeros(len(q) - 1)
        for k, m in moves.items():
            if m is not None:
                d[k] = m
        outline = move_walls(q, d)
        out[name] = {"outline": np.round(outline, 2).tolist(), "ground_over_turf": g - turf, "eave": eave, "ridge": ridge, "roof_points": len(roof),
                     "roof_spread": float(np.percentile(roof, 75) - np.percentile(roof, 25)), "wall_moves": moves,
                     "spec": list(sp[name])}
        print("%-5s %-7s %+6.0f %6.1f %6s %6d  %4.1f/%-6.1f %s" % (
            name, kind, g - turf, eave, "-" if ridge is None else "%.1f" % ridge, len(roof), sp[name][0], sp[name][2],
            " ".join("%d:%s" % (k, "-" if m is None else "%+.1f" % m) for k, m in sorted(moves.items()))))
    json.dump(out, open(os.path.join(work, "hover.json"), "w"), indent=1)
    # the land: the walls' outer readouts and the terrain grid's (plan_terrain), over the SCG's turf
    tm = os.path.join(work, "terrain_meta.json")
    if os.path.exists(tm):
        for vn, tags in json.load(open(tm)).items():
            for i, t in enumerate(tags):
                f = os.path.join(work, "terrain", "%s_%d.png" % (vn, i))
                r = parse(f) if os.path.exists(f) else None
                if r is not None:
                    gpts.append([r[0], r[1], r[2] - turf])
        save_cache()
    json.dump(gpts, open(os.path.join(work, "hover_ground.json"), "w"))
    print("%d ground readouts" % len(gpts))


if __name__ == "__main__":
    {"plan": plan, "read": read, "plan_terrain": plan_terrain}[sys.argv[1]](sys.argv[2])
