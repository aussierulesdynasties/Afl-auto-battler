"""Moore Park's footbridges over Anzac Parade (SCG rebuild, 2026-11-22).

The Albert 'Tibby' Cotter Bridge (OpenStreetMap ways 333342001 and 333341998) and the Dr Agnes Bennett
Footbridge (759506929, 759506931) cross Anzac Parade west of the SCG. surrounds.py leaves bridges out of the
map, so they were missing. This builds them along OpenStreetMap's centre lines, as a PART
(assets/grounds/scg/bridges.bin: triangles, per vertex x, y, z, normal, colour; float32, model metres):

- the Cotter bridge's deck 6 m wide (Arup, Wikipedia) on its two steel box beams, one under each edge;
- the Bennett footbridge's deck 3.5 m wide on one box beam;
- each deck at DECK m over the road, ramping down at RAMP (1 in 14, an accessible ramp) to the ground at
  each end; concrete columns every PIER_GAP m wherever the deck is over 2 m up;
- railings each side: posts every 3 m, a top rail at 1.8 m and a mid rail (the Cotter bridge's Webnet mesh
  between them is under a pixel from the ground's cameras).

Not published, and so estimated: the height over the road (7 m to the walking surface, a road bridge's
5.3 m clearance plus the beams) and where the ramps meet the ground (each chain's ends).

    python3 tools/grounds/scg/bridges.py        (reads the OpenStreetMap tiles surrounds.py fetched)
"""
import glob
import math
import os
import xml.etree.ElementTree as ET

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "scg")
BRIDGES = [(("333341998", "333342001"), 6.0, 2), (("759506929", "759506931", "1282349597", "1282349600"), 3.5, 1)]
DECK = 7.0
RAMP = 1.0 / 14.0
PIER_GAP = 20.0
CONCRETE = (0.6, 0.57, 0.5)
STEEL = (0.42, 0.42, 0.41)
RAIL = (0.55, 0.55, 0.52)
tris = []


def quad(p0, p1, p2, p3, col):
    n = np.cross(np.subtract(p1, p0), np.subtract(p3, p0))
    ln = np.linalg.norm(n)
    if ln < 1e-9:
        return
    n = n / ln
    for t in ((p0, p1, p2), (p0, p2, p3)):
        for p in t:
            tris.extend([float(x) for x in p] + [float(x) for x in n] + list(col))


def prism(path_lo, path_hi, col):
    """A box swept along a path: path_lo/hi are lists of (left, right) points at the bottom and top."""
    for k in range(len(path_lo) - 1):
        (l0, r0), (l1, r1) = path_lo[k], path_lo[k + 1]
        (L0, R0), (L1, R1) = path_hi[k], path_hi[k + 1]
        quad(L0, R0, R1, L1, col)           # top
        quad(l0, l1, r1, r0, col)           # underside
        quad(l0, L0, L1, l1, col)           # left side
        quad(r0, r1, R1, R0, col)           # right side
    for (l, r), (L, R), s in ((path_lo[0], path_hi[0], 1), (path_lo[-1], path_hi[-1], -1)):
        quad(l, r, R, L, col) if s > 0 else quad(r, l, L, R, col)


def post(x, z, y0, y1, w, col):
    lo = [((x - w, y0, z - w), (x + w, y0, z - w))]
    c = [(x - w, z - w), (x + w, z - w), (x + w, z + w), (x - w, z + w)]
    for k in range(4):
        (ax, az), (bx, bz) = c[k], c[(k + 1) % 4]
        quad((ax, y0, az), (bx, y0, bz), (bx, y1, bz), (ax, y1, az), col)
    quad((c[0][0], y1, c[0][1]), (c[3][0], y1, c[3][1]), (c[2][0], y1, c[2][1]), (c[1][0], y1, c[1][1]), col)


def chain(ways):
    """Joins ways that share end nodes into one line of node ids."""
    segs = [list(w) for w in ways if len(w) > 1]
    line = segs.pop(0)
    while segs:
        for i, s in enumerate(segs):
            if s[0] == line[-1]:
                line += s[1:]
            elif s[-1] == line[-1]:
                line += s[::-1][1:]
            elif s[-1] == line[0]:
                line = s[:-1] + line
            elif s[0] == line[0]:
                line = s[::-1][:-1] + line
            else:
                continue
            segs.pop(i)
            break
        else:
            break
    return line


def main():
    lat0, lon0 = -33.8916, 151.2248
    kx, ky = 111320.0 * math.cos(math.radians(lat0)), 110574.0
    roots = [ET.parse(f).getroot() for f in sorted(glob.glob("/tmp/scg_surrounds_*.osm"))]
    nodes, ways = {}, {}
    for r in roots:
        for n in r.findall("node"):
            nodes[n.get("id")] = ((float(n.get("lon")) - lon0) * kx, -(float(n.get("lat")) - lat0) * ky)
        for w in r.findall("way"):
            ways[w.get("id")] = [x.get("ref") for x in w.findall("nd")]
    for ids, width, beams in BRIDGES:
        line = chain([ways[i] for i in ids if i in ways])
        p = np.array([nodes[i] for i in line if i in nodes])
        # densify to 2 m so the ramps bend smoothly
        d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
        s = np.linspace(0, d[-1], max(2, int(d[-1] / 2.0)))
        p = np.c_[np.interp(s, d, p[:, 0]), np.interp(s, d, p[:, 1])]
        y = np.minimum(DECK, np.minimum(s, s[-1] - s) * RAMP) + 0.05
        t = np.gradient(p, axis=0)
        t /= np.linalg.norm(t, axis=1)[:, None]
        nrm = np.c_[-t[:, 1], t[:, 0]]
        hw = width / 2

        def side(off, dy):
            return [((q[0] + n[0] * -off, yy + dy, q[1] + n[1] * -off), (q[0] + n[0] * off, yy + dy, q[1] + n[1] * off))
                    for q, n, yy in zip(p, nrm, y)]

        def strip(o0, o1, y0, y1, col):
            lo = [((q[0] + n[0] * o0, yy + y0, q[1] + n[1] * o0), (q[0] + n[0] * o1, yy + y0, q[1] + n[1] * o1))
                  for q, n, yy in zip(p, nrm, y)]
            hi = [((a[0], a[1] - y0 + y1, a[2]), (b[0], b[1] - y0 + y1, b[2])) for a, b in lo]
            prism(lo, hi, col)
        strip(-hw, hw, -0.3, 0.0, CONCRETE)                                  # the deck
        offs = (-hw + 0.5, hw - 0.5) if beams == 2 else (0.0,)
        for o in offs:                                                       # box beams under it
            strip(o - 0.4, o + 0.4, -1.5, -0.3, STEEL)
        for o in (-hw + 0.05, hw - 0.05):                                    # railings
            strip(o - 0.04, o + 0.04, 1.72, 1.8, RAIL)
            strip(o - 0.03, o + 0.03, 0.9, 0.95, RAIL)
            for k in range(0, len(p), 2):     # posts every 3-4 m (the line is in 2 m steps)
                q = p[k] + nrm[k] * o
                post(q[0], q[1], y[k], y[k] + 1.8, 0.04, RAIL)
        for k in range(len(p)):                                              # columns
            if y[k] > 2.0 and (s[k] % PIER_GAP) < (s[1] - s[0]):
                for o in offs:
                    q = p[k] + nrm[k] * o
                    post(q[0], q[1], 0.0, y[k] - 1.5, 0.4, CONCRETE)
        print("bridge %s: %.0f m, %.1f m wide" % (ids[0], s[-1], width))
    # stood on the land (relief.py): each vertex lifted by the land's height under it, so the ramps meet the
    # ground and the decks keep their DECK m over the road
    import relief
    a = np.array(tris, "<f4").reshape(-1, 9)
    if os.path.exists(relief.OUT):
        G = np.fromfile(relief.OUT, "<f4")[2:].reshape(relief.N, relief.N)
        a[:, 1] += [relief.relief_at(float(x), float(z), G) for x, z in a[:, [0, 2]]]
    a.tofile(os.path.join(DIR, "bridges.bin"))
    print("%d triangles" % (len(tris) // 27))


if __name__ == "__main__":
    main()
