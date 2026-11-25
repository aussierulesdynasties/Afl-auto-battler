"""Ground and roof colours measured against Google Earth on graphics-card renders (SCG rebuild, 2026-11-22).

    python3 tools/grounds/scg/colour_cal.py <workdir> <ours_dir>

The cloud's software renderer never sunlights StandardMaterial3D surfaces, so colours are judged only on
renders from a real graphics card (<ours_dir>: tools/visual/ground_look.gd on the PC, the cameras of
qa/measure_views.json in model metres, the straight-down views tilted 9 degrees so Godot's camera has an up).
Each Google Earth shot (<workdir>/ge, measure.py's) and each render is read through its own camera, so the
same piece of ground is sampled in both wherever it falls in the picture:

- the ground, class by class (the surrounds map's palette: roads, paths, paving, the parks' grass, fields),
  at points 3 m and more from any building and off Google Earth's traced canopy, with Google Earth's ground
  at its real height (relief.py's land, Google Earth's own heights; the renders being compared were made
  before ours stood on it, so ours is level);
- the trees' crowns, on Google Earth's traced canopy 8 m up;
- each nearby roof, 2 m and more inside its walls, at its height (hover.json where measured);
- the walls in the obliques, the faces each camera sees, between 1.5 m up and 1.5 m under the eave, by the
  wall colour facades.py gives them (BRICK, SANDSTONE, CREAM, OFFICE: windows and all, as both show them).

For each it prints Google Earth's median colour, ours, and the factor (per channel, in linear light) that
takes ours to Google Earth's: the palette entry times that factor renders as Google Earth shows it.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from shapely.geometry import Point, Polygon
from shapely.prepared import prep

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import gecam                   # noqa: E402
import surrounds as sr        # noqa: E402

CLASSES = ["ASPHALT", "PARKING", "PATH", "PAVED", "CONCOURSE", "LAWN", "PITCH", "BASE", "URBAN", "GOLF", "PLAZA"]


def lin(c):
    c = np.asarray(c, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def terrain(work):
    p = os.path.join(work, "hover.json")
    import relief
    if not os.path.exists(relief.OUT):
        return lambda x, z: np.zeros_like(x)
    L = np.fromfile(relief.OUT, "<f4")[2:].reshape(relief.N, relief.N)
    return lambda x, z: np.array([relief.relief_at(float(a), float(b), L) for a, b in zip(np.ravel(x), np.ravel(z))]).reshape(np.shape(x))


def main(work, ours):
    views = json.load(open(os.path.join(ROOT, "qa", "measure_views.json")))
    mp = np.asarray(Image.open(os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "scg", "surrounds.webp")).convert("RGB")).astype(int)
    canopy = np.asarray(Image.open(os.path.join(ROOT, "canopy_ge.png")).convert("L")) > 0
    S = mp.shape[0]
    pal = {c: np.array(getattr(sr, c)) for c in CLASSES}
    blds = gecam.buildings()
    near = prep(Polygon().union(*[Polygon(q[:-1]).buffer(3.0) for _, q in blds]) if False else
                __import__("shapely.ops", fromlist=["unary_union"]).unary_union([Polygon(q[:-1]).buffer(3.0) for _, q in blds]))
    ter = terrain(work)
    hv = json.load(open(os.path.join(work, "hover.json"))) if os.path.exists(os.path.join(work, "hover.json")) else {}
    import facades as fc
    acc = {c: ([], []) for c in CLASSES + ["CANOPY"]}
    roofs = {}
    for v in views:
        ge_path = os.path.join(work, "ge", v["name"] + ".png")
        on = v["name"].replace("_top", "_t09")
        our_path = os.path.join(ours, on + ".png")
        if not (os.path.exists(ge_path) and os.path.exists(our_path)):
            continue
        Pg = gecam.cam_parts(v, work)
        vo = dict(v, name=on)
        if v["t"] < 3:
            vo.update(t=9.0, h=0)
        Po = gecam.cam_parts(vo, work)
        G = np.asarray(Image.open(ge_path).convert("RGB")).astype(float)
        O = np.asarray(Image.open(our_path).convert("RGB").resize((1280, 720))).astype(float)
        if v["t"] < 3:        # ground classes from the near-overhead views only
            e, n = v["at"][0], v["at"][1]
            xs, zs = np.meshgrid(np.arange(-150, 150, 2.0) + gecam.CX + e, np.arange(-90, 90, 2.0) + gecam.CZ - n)
            xs, zs = xs.ravel(), zs.ravel()
            ix = np.clip((xs + S / 2).astype(int), 0, S - 1)
            iz = np.clip((zs + S / 2).astype(int), 0, S - 1)
            col = mp[iz, ix]
            keep = ~canopy[iz, ix]
            keep &= np.array([not near.contains(Point(x, z)) for x, z in zip(xs, zs)])
            yg = ter(xs, zs)
            ug, wg = Pg(xs, yg, zs)
            uo, wo = Po(xs, np.zeros_like(xs), zs)
            ok = keep & (ug > 0) & (ug < 1279) & (wg > 55) & (wg < 719) & (uo > 0) & (uo < 1279) & (wo > 0) & (wo < 719)
            # the canopy: Google Earth's traced canopy, at 8 m (most of these crowns are 6-12 m up)
            cm = canopy[iz, ix] & (ug > 0) & (ug < 1279) & (wg > 55) & (wg < 719)
            if cm.any():
                ug8, wg8 = Pg(xs[cm], yg[cm] + 8.0, zs[cm])
                uo8, wo8 = Po(xs[cm], np.full(cm.sum(), 8.0), zs[cm])
                k = (ug8 > 0) & (ug8 < 1279) & (wg8 > 55) & (wg8 < 719) & (uo8 > 0) & (uo8 < 1279) & (wo8 > 0) & (wo8 < 719)
                acc["CANOPY"][0].extend(G[wg8[k].astype(int), ug8[k].astype(int)].tolist())
                acc["CANOPY"][1].extend(O[wo8[k].astype(int), uo8[k].astype(int)].tolist())
            for c in CLASSES:
                m = ok & (np.abs(col - pal[c]).max(1) <= 6)
                if m.sum() == 0:
                    continue
                acc[c][0].extend(G[wg[m].astype(int), ug[m].astype(int)].tolist())
                acc[c][1].extend(O[wo[m].astype(int), uo[m].astype(int)].tolist())
            for name, q in blds:
                key = int(name) if name.isdigit() else name
                if key not in fc.SPEC and name not in hv:
                    continue
                inner = Polygon(q[:-1]).buffer(-2.0)
                if inner.is_empty:
                    continue
                x0, z0, x1, z1 = inner.bounds
                gx, gz = np.meshgrid(np.arange(x0, x1, 1.0), np.arange(z0, z1, 1.0))
                gx, gz = gx.ravel(), gz.ravel()
                pin = prep(inner)
                m = np.array([pin.contains(Point(a, b)) for a, b in zip(gx, gz)])
                if m.sum() < 10:
                    continue
                gx, gz = gx[m], gz[m]
                sp = fc.SPEC.get(key)
                ours_h = (sp[0] + (sp[2] / 2 if sp[1] != "flat" else 0)) if sp else 6.0
                if name in hv:
                    r = hv[name]
                    ge_h = r["ground_over_turf"] + (r["eave"] + r["ridge"]) / 2 if r.get("ridge") else r["ground_over_turf"] + r["eave"]
                else:
                    ge_h = ours_h + ter(np.array([gx.mean()]), np.array([gz.mean()]))[0]
                ug, wg = Pg(gx, gx * 0 + ge_h, gz)
                uo, wo = Po(gx, gx * 0 + ours_h, gz)
                ok = (ug > 0) & (ug < 1279) & (wg > 55) & (wg < 719) & (uo > 0) & (uo < 1279) & (wo > 0) & (wo < 719)
                if ok.sum() < 10:
                    continue
                roofs.setdefault(name, ([], []))
                roofs[name][0].extend(G[wg[ok].astype(int), ug[ok].astype(int)].tolist())
                roofs[name][1].extend(O[wo[ok].astype(int), uo[ok].astype(int)].tolist())
    res = {"ground": {}, "roofs": {}, "walls": {}}
    # walls, in the obliques: points over each wall's face from 1.5 m up to 1.5 m under its eave, 1 m in from
    # its ends, on the faces each camera sees; grouped by the wall colour facades.py gives them
    walls = {}
    names = {id(getattr(fc, k)): k for k in ("BRICK", "SANDSTONE", "CREAM", "OFFICE")}
    unm = {"u%d" % e["ge_blob"]: e for e in json.load(open(os.path.join(ROOT, "unmapped.json")))}
    for v in views:
        if v["t"] < 3:
            continue
        ge_path = os.path.join(work, "ge", v["name"] + ".png")
        our_path = os.path.join(ours, v["name"] + ".png")
        if not (os.path.exists(ge_path) and os.path.exists(our_path)):
            continue
        Pg = gecam.cam_parts(v, work)
        Po = gecam.cam_parts(v, work)
        G = np.asarray(Image.open(ge_path).convert("RGB")).astype(float)
        O = np.asarray(Image.open(our_path).convert("RGB").resize((1280, 720))).astype(float)
        hr = math.radians(v["h"])
        look = np.array([math.sin(hr), -math.cos(hr)])          # the camera's view across the ground, model x, z
        for name, q in blds:
            key = int(name) if name.isdigit() else None
            if key in fc.SPEC:
                sp = fc.SPEC[key]
                wname = names.get(id(sp[3]))
            elif name in unm:
                sp = (unm[name]["eave"], unm[name]["roof"], unm[name]["rise"])
                wname = unm[name]["walls"]
            else:
                continue
            if wname is None:
                continue
            r = hv.get(name)
            ge_eave = r["eave"] if r else sp[0]
            g0 = r["ground_over_turf"] if r else float(ter(np.array([q[:-1, 0].mean()]), np.array([q[:-1, 1].mean()]))[0])
            poly = Polygon(q[:-1])
            for k in range(len(q) - 1):
                a, b = q[k], q[k + 1]
                L = np.linalg.norm(b - a)
                if L < 4:
                    continue
                t = (b - a) / L
                nrm = np.array([t[1], -t[0]])
                if poly.contains(Point(*((a + b) / 2 + nrm * 0.3))):
                    nrm = -nrm
                if nrm @ look > -0.3:                    # facing away from this camera, or edge on
                    continue
                s_ = np.arange(1.0, L - 1.0, 0.7)
                for frac_h in np.linspace(0.2, 0.8, 5):
                    pts = a + t * s_[:, None]
                    yo = 1.5 + (sp[0] - 3.0) * frac_h
                    yg = g0 + 1.5 + (ge_eave - 3.0) * frac_h
                    ug, wg = Pg(pts[:, 0], np.full(len(pts), yg), pts[:, 1])
                    uo, wo = Po(pts[:, 0], np.full(len(pts), yo), pts[:, 1])
                    ok = (ug > 0) & (ug < 1279) & (wg > 55) & (wg < 719) & (uo > 0) & (uo < 1279) & (wo > 0) & (wo < 719)
                    if ok.any():
                        walls.setdefault(wname, ([], []))
                        walls[wname][0].extend(G[wg[ok].astype(int), ug[ok].astype(int)].tolist())
                        walls[wname][1].extend(O[wo[ok].astype(int), uo[ok].astype(int)].tolist())
    print("%-10s %6s  %-15s %-15s %s" % ("class", "n", "Google Earth", "ours", "factor (linear)"))
    for c, (g, o) in acc.items():
        if len(g) < 30:
            continue
        g, o = np.median(np.array(g), 0), np.median(np.array(o), 0)
        f = lin(g) / np.maximum(lin(o), 1e-4)
        res["ground"][c] = {"ge": g.tolist(), "ours": o.tolist(), "factor": f.tolist(), "n": len(acc[c][0])}
        print("%-10s %6d  %-15s %-15s %s" % (c, len(acc[c][0]), tuple(int(x) for x in g), tuple(int(x) for x in o), " ".join("%.2f" % x for x in f)))
    for name, (g, o) in sorted(roofs.items()):
        g, o = np.median(np.array(g), 0), np.median(np.array(o), 0)
        f = lin(g) / np.maximum(lin(o), 1e-4)
        res["roofs"][name] = {"ge": g.tolist(), "ours": o.tolist(), "factor": f.tolist(), "n": len(roofs[name][0])}
        print("roof %-5s %6d  %-15s %-15s %s" % (name, len(roofs[name][0]), tuple(int(x) for x in g), tuple(int(x) for x in o), " ".join("%.2f" % x for x in f)))
    for w, (g, o) in sorted(walls.items()):
        n = len(g)
        g, o = np.median(np.array(g), 0), np.median(np.array(o), 0)
        f = lin(g) / np.maximum(lin(o), 1e-4)
        res["walls"][w] = {"ge": g.tolist(), "ours": o.tolist(), "factor": f.tolist(), "n": n}
        print("wall %-9s %6d  %-15s %-15s %s" % (w, n, tuple(int(x) for x in g), tuple(int(x) for x in o), " ".join("%.2f" % x for x in f)))
    json.dump(res, open(os.path.join(work, "colour_cal.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
