"""Trace Mars Stadium's grass edge (the fence line) from Google Earth's straight-down tiles, in model metres.

  python3 tools/grounds/mars/qa/trace.py <workdir> <out.json> [overlay_dir]

Reads the trace_* shots compare.py planned and ge_shoot.js took (330 m straight down, 35 deg vertical field of view
over the 1000 px window, so 0.2081 m a pixel at the turf, which Google Earth puts at 452 m). From the field centre a
ray every 0.5 deg runs out over each tile; the fence is the centre of the first thin white run (the rail's cap,
under 0.8 m) no more than 4 m past the last grass pixel. In the north and east the turf runs straight into the stands' shaded
front wall, which is the fence there (close oblique views fence_* show it): the edge is where the turf stops. A tile's ray counts only where it stays clear of the frame's edge and the
Dismiss banner. Writes [[bearing, east, north], ...] (the median over the tiles that see that bearing). Only
numbers leave this script: no imagery is kept."""
import json, math, os, sys
import numpy as np
from PIL import Image

LAT0, LON0 = -37.539307, 143.848166
FC = (-4.18, -4.88)                 # the rays' origin, east/north m (near the field centre; the curve does not depend on it)
S = 2 * 330 * math.tan(math.radians(17.5)) / 1000.0


def white(rgb):
    r, g, b = [rgb[..., k].astype(float) for k in range(3)]
    mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b)
    return (mx > 165) & (mx - mn < 45)                                  # the fence's white rail


def grass(rgb):
    r, g, b = [rgb[..., k].astype(float) for k in range(3)]
    return (g > r * 0.98) & (g > b * 1.12) & (g > 45) & (g < 200)     # turf greens (and the worn yellow-greens)


def tile(work, name):
    urls = json.load(open(os.path.join(work, 'urls.json')))
    url = [u for p, u in urls if p.endswith('/' + name + '.png')][0]
    lat, lon = [float(x) for x in url.split('@')[1].split(',')[:2]]
    e = (lon - LON0) * 111320.0 * math.cos(math.radians(LAT0)); n = (lat - LAT0) * 110574.0
    im = np.asarray(Image.open(os.path.join(work, 'ge', name + '.png')).convert('RGB'))
    ok = np.ones(im.shape[:2], bool); ok[:8] = ok[-8:] = False; ok[:, :8] = ok[:, -8:] = False
    ok[0:60, 660:1125] = False      # Dismiss banner
    return e, n, grass(im), ok, white(im), im.max(axis=2).astype(float)


def ray(t, b):
    """the fence's distance from the field centre along bearing b on one tile, and how it was read, or None"""
    e0, n0, G, ok, Wt, L = t
    a = math.radians(b); st = 0.05
    rs = np.arange(30.0, 110.0, st)
    E = FC[0] + rs * math.sin(a); N = FC[1] + rs * math.cos(a)
    u = np.round(640 + (E - e0) / S).astype(int); v = np.round(500 - (N - n0) / S - 140).astype(int)
    inside = (u >= 0) & (u < G.shape[1]) & (v >= 0) & (v < G.shape[0])
    if not inside.all() or not all(ok[v[k], u[k]] for k in range(len(rs)) if 55 < rs[k] < 100):
        return None                 # the ray leaves the usable frame
    g = G[v, u]; w = Wt[v, u]; l = L[v, u]
    last = None
    for k in range(len(rs)):
        if g[k]:
            last = k; continue
        if last is None or rs[k] < 55:
            continue
        if (k - last) * st > 4.0:
            return None
        if w[k]:
            # a white run: the rail when it is thin (the rail's cap, under 0.8 m); a wide one is a roof or paving
            j = k
            while j < len(rs) and w[j]: j += 1
            return ((rs[k] + rs[j - 1]) / 2, 'rail') if (j - k) * st <= 0.8 else None
        if l[k] < 70 and (k - last) * st < 0.6:
            # the turf runs straight into a shaded stand front (north and east): there the fence is the stand's front
            # wall, so the edge is where the turf stops (Google Earth's close oblique views fence_10/40/80 show it)
            j = k + int(1.0 / st)
            return (float(rs[k]), 'turf edge') if j < len(rs) and (l[k:j] < 70).all() else None
    return None


def main(work, out, ov=None):
    names = sorted(f[:-4] for f in os.listdir(os.path.join(work, 'ge')) if f.startswith('trace_') and f.endswith('.png') and '_cam' not in f)
    tiles = {n: tile(work, n) for n in names}
    hits = {b: [h for h in (ray(t, b) for t in tiles.values()) if h is not None] for b in np.arange(0, 360, 0.5)}
    pts = []
    for b, hh in hits.items():
        R = [r for r, k in hh if k == 'rail']
        rr, src = (R, 'rail') if R else ([r for r, k in hh if k == 'turf edge'], 'turf edge')
        if rr:
            r = float(np.median(rr)); a = math.radians(b)
            pts.append([float(b), FC[0] + r * math.sin(a), FC[1] + r * math.cos(a), len(rr), float(np.ptp(rr)), src])
    json.dump({'source': 'Google Earth straight-down tiles, 330 m, ge_alt 452 (qa/views.json trace_*)',
               'pts': [[round(p[0], 1), round(p[1], 3), round(p[2], 3)] for p in pts],
               'tiles_seen': [p[3] for p in pts], 'tile_spread_m': [round(p[4], 3) for p in pts],
               'from': [p[5] for p in pts]}, open(out, 'w'))
    sp = [p[4] for p in pts if p[3] > 1]
    print('%d bearings read where the turf meets a shaded stand front' % sum(p[5] == 'turf edge' for p in pts))
    print('%d of 720 bearings traced; tiles agree within %.2f m median, %.2f m worst' % (len(pts), np.median(sp), max(sp)))
    if ov:
        os.makedirs(ov, exist_ok=True)
        for n, (e0, n0, G, ok, _, _) in tiles.items():
            im = Image.open(os.path.join(work, 'ge', n + '.png')).convert('RGB'); px = im.load()
            for p in pts:
                u = int(round(640 + (p[1] - e0) / S)); v = int(round(500 - (p[2] - n0) / S - 140))
                for du in (-1, 0, 1):
                    for dv in (-1, 0, 1):
                        if 0 <= u + du < im.width and 0 <= v + dv < im.height:
                            px[u + du, v + dv] = (255, 0, 255)
            im.save(os.path.join(ov, n + '.png'))


if __name__ == '__main__':
    main(*sys.argv[1:4])
