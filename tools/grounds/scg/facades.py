"""Real facades for the buildings nearest the SCG (SCG rebuild, 2026-11-22).

tools/grounds/scg/surrounds.py extrudes every mapped building as a plain box (buildings.bin), right for
the city a kilometre off. The buildings within NEAR metres of the pitch centre are seen close from the
top of the stands and in a fly-through, and Google Earth shows them as what they are: rows of windows set
into a frame of piers and floor edges. This takes those out of buildings.bin and builds them whole, every
window a real recess, through GroundModels.PARTS:

- a pier standing 0.3 m proud every 3 m along each wall, a floor edge 0.3 m proud at every floor and a
  sill band under each row of windows, dark glass set back in each bay between them;
- a parapet round a flat roof.

    python3 tools/grounds/scg/facades.py

The first run moves those buildings into tools/grounds/scg/near_buildings.bin (same format as
buildings.bin) and reads them from there afterwards, so running it again changes nothing.
Writes assets/grounds/scg/facades.bin: triangles, per vertex x, y, z, normal, colour (float32, model metres).
"""
import math
import os

import mapbox_earcut as earcut
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "scg")
NEAR_FILE = os.path.join(ROOT, "near_buildings.bin")
PC = np.array([0.94, 11.82])
NEAR = 350.0
FLOOR = 3.2
BAY = 3.0
PROUD = 0.3
PIER_W = 0.5
SILL = 0.9           # the band from each floor up to the window sill
# the same render and brick palette GroundModels draws the plain buildings in
WALLS = [(0.86, 0.84, 0.8), (0.78, 0.76, 0.72), (0.72, 0.6, 0.5), (0.9, 0.88, 0.84), (0.66, 0.66, 0.66)]
GLASS = (0.15, 0.18, 0.21)
TINT = (0.8, 0.8, 0.78)      # GroundModels' building_tint for the SCG, so near and far match

tris = []


def quad(p0, p1, p2, p3, n, col):
    for t in ((p0, p1, p2), (p0, p2, p3)):
        for p in t:
            tris.extend(list(p) + list(n) + list(col))


def split(buf):
    out, i = [], 0
    while i + 1 < len(buf):
        n = int(buf[i])
        out.append(buf[i:i + 2 + 2 * n])
        i += 2 + 2 * n
    return out


def strip_box(a, c, out, y0, y1, d0, d1, col, ends=True):
    """A box along wall edge a->c (2D x, z), d0..d1 metres out from the wall, y0..y1 up."""
    t = (c - a) / np.linalg.norm(c - a)
    o = np.array([out[0], out[2]])

    def P(p, d, y):
        q = p + o * d
        return (float(q[0]), y, float(q[1]))
    quad(P(a, d1, y0), P(c, d1, y0), P(c, d1, y1), P(a, d1, y1), out, col)                 # front
    quad(P(a, d0, y1), P(c, d0, y1), P(c, d1, y1), P(a, d1, y1), (0, 1, 0), col)           # top
    quad(P(a, d0, y0), P(c, d0, y0), P(c, d1, y0), P(a, d1, y0), (0, -1, 0), col)          # underside
    if ends:
        quad(P(a, d0, y0), P(a, d1, y0), P(a, d1, y1), P(a, d0, y1), (-t[0], 0, -t[1]), col)
        quad(P(c, d0, y0), P(c, d1, y0), P(c, d1, y1), P(c, d0, y1), (t[0], 0, t[1]), col)


def building(rec, b):
    n, h = int(rec[0]), float(rec[1])
    foot = rec[2:2 + 2 * n].reshape(-1, 2).astype(float)
    if np.allclose(foot[0], foot[-1]):
        foot = foot[:-1]
    wall = tuple(w * t for w, t in zip(WALLS[(b + 1) % len(WALLS)], TINT))
    roof = tuple(c * 0.82 for c in wall)
    ccw = sum(foot[k, 0] * foot[(k + 1) % len(foot), 1] - foot[k, 1] * foot[(k + 1) % len(foot), 0] for k in range(len(foot)))
    floors = max(1, int(round((h - 1.0) / FLOOR)))
    fh = (h - 1.0) / floors
    for k in range(len(foot)):
        a, c = foot[k], foot[(k + 1) % len(foot)]
        L = float(np.linalg.norm(c - a))
        if L < 0.3:
            continue
        o = np.array([c[1] - a[1], 0.0, a[0] - c[0]]) / L * (1.0 if ccw > 0 else -1.0)
        o = tuple(float(x) for x in o)
        # the wall plane: glass, with the frame proud of it
        quad((a[0], 0.0, a[1]), (c[0], 0.0, c[1]), (c[0], h, c[1]), (a[0], h, a[1]), o, GLASS)
        if L < 1.5:
            strip_box(a, c, o, 0.0, h, 0.0, PROUD, wall, ends=False)
            continue
        for f in range(floors):
            y = f * fh
            strip_box(a, c, o, y, y + (0.35 if f else SILL), 0.0, PROUD, wall, ends=False)
            if f:
                strip_box(a, c, o, y + 0.35, y + SILL, 0.0, PROUD * 0.6, wall, ends=False)
        strip_box(a, c, o, h - 1.0, h + 0.5, 0.0, PROUD, wall, ends=False)        # parapet band
        bays = max(1, int(round(L / BAY)))
        t = (c - a) / L
        for j in range(bays + 1):
            m = a + t * (L * j / bays)
            w = PIER_W / 2
            p0 = m - t * (0 if j == 0 else w)
            p1 = m + t * (0 if j == bays else w)
            strip_box(p0, p1, o, 0.0, h + 0.5, 0.0, PROUD + 0.02, wall, ends=0 < j < bays)
    # the roof, a little under the parapet's top
    idx = earcut.triangulate_float64(foot, np.array([len(foot)], np.uint32))
    for q in range(0, len(idx), 3):
        p = [foot[idx[q + r]] for r in range(3)]
        for v in p:
            tris.extend([float(v[0]), h - 0.1, float(v[1]), 0.0, 1.0, 0.0] + list(roof))


def main():
    path = os.path.join(DIR, "buildings.bin")
    recs = split(np.fromfile(path, "<f4"))
    near_first = not os.path.exists(NEAR_FILE)
    if near_first:
        keep, near = [], []
        for b, r in enumerate(recs):
            n = int(r[0])
            ctr = r[2:2 + 2 * n].reshape(-1, 2).mean(0)
            (near if np.hypot(*(ctr - PC)) < NEAR and r[1] >= 5.0 else keep).append((b, r))
        np.concatenate([r for _b, r in keep]).astype("<f4").tofile(path)
        np.concatenate([np.r_[b, r] for b, r in near]).astype("<f4").tofile(NEAR_FILE)
    raw = np.fromfile(NEAR_FILE, "<f4")
    i, near = 0, []
    while i < len(raw):
        b, n = int(raw[i]), int(raw[i + 1])
        near.append((b, raw[i + 1:i + 3 + 2 * n]))
        i += 3 + 2 * n
    for b, r in near:
        building(r, b)
    arr = np.array(tris, "<f4")
    arr.tofile(os.path.join(DIR, "facades.bin"))
    print("%d buildings with facades (%s), %d triangles" % (len(near), "moved out of buildings.bin" if near_first else "from near_buildings.bin", len(arr) // 27))


if __name__ == "__main__":
    main()
