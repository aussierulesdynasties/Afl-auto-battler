"""Real facades for the buildings nearest the SCG (SCG rebuild, 2026-11-22).

tools/grounds/scg/surrounds.py extrudes every mapped building as a plain box (buildings.bin), right for
the city a kilometre off. The buildings within NEAR metres of the pitch centre are seen close from the
top of the stands and in a fly-through, and Google Earth shows them as what they are: rows of windows set
into a frame of piers and floor edges. This takes those out of buildings.bin and builds them whole, every
window a real recess, through GroundModels.PARTS:

- a pier standing 0.3 m proud every 3 m along each wall, a floor edge 0.3 m proud at every floor and a
  sill band under each row of windows, dark glass set back in each bay between them;
- a parapet round a flat roof.

    python3 tools/grounds/scg/facades.py        (needs shapely, mapbox_earcut, trimesh)

The first run after surrounds.py moves those buildings into tools/grounds/scg/near_buildings.bin (same
format as buildings.bin) and reads them from there afterwards, so running it again changes nothing.
Writes assets/grounds/scg/facades.bin: triangles, per vertex x, y, z, normal, colour (float32, model metres).

Every other building (buildings.bin, past NEAR) is built too, into assets/grounds/scg/city.glb (a
SURROUNDS model, so Godot's import gives it levels of detail): a band proud of the wall from each floor to
its sill with the windows a recessed ribbon above it, piers at the corners, a parapet and a roof. Nothing
round the SCG is a plain box any more. OpenStreetMap's outline of Allianz Stadium is left out (allianz.py).
"""
import math
import os

import mapbox_earcut as earcut
import numpy as np
from shapely.geometry import LineString, Polygon

ROOT = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "scg")
NEAR_FILE = os.path.join(ROOT, "near_buildings.bin")
PC = np.array([0.94, 11.82])
NEAR = 350.0
ALLIANZ = (25.7, -274.1)     # Allianz Stadium's pitch centre, model metres
FLOOR = 3.2
BAY = 3.0
PROUD = 0.3
PIER_W = 0.5
SILL = 0.9           # the band from each floor up to the window sill
# the same render and brick palette GroundModels draws the plain buildings in
WALLS = [(0.86, 0.84, 0.8), (0.78, 0.76, 0.72), (0.72, 0.6, 0.5), (0.9, 0.88, 0.84), (0.66, 0.66, 0.66)]
GLASS = (0.15, 0.18, 0.21)
TINT = (0.82, 0.79, 0.72)    # warmed: the match light's sky turns pale walls lavender, Google Earth's are cream and grey
# Roofs from Google Earth round the ground, each its own colour, not the wall's: the sheds' beige, pale
# metal, white and grey (Google Earth sRGB (208, 194, 178), (190, 197, 190), (238, 235, 222), (176, 176, 168)),
# Paddington's houses dark grey iron and terracotta. Divided by what the match light adds to a pale
# roof (x1.29, 1.34, 1.54 red, green, blue: a vertex colour of 0.56 renders 0.73-0.79), so they render as sampled.
BIG_ROOFS = [(0.63, 0.57, 0.45), (0.58, 0.58, 0.48), (0.72, 0.69, 0.565), (0.535, 0.515, 0.43)]
SMALL_ROOFS = [(0.535, 0.515, 0.43), (0.36, 0.34, 0.29), (0.58, 0.58, 0.48), (0.45, 0.43, 0.37)]
HOUSE_ROOFS = [(0.36, 0.34, 0.29), (0.42, 0.24, 0.16), (0.45, 0.43, 0.37), (0.42, 0.24, 0.16), (0.535, 0.515, 0.43)]


# Each near building as Google Earth shows it (OpenStreetMap gives all but one of them a default 8 m and
# no roof shape): (eave height m, roof, roof rise m, walls, roof colour, solid). Roofs: "flat" (a parapet),
# "gable" (a ridge along the long side), "hip", "monitor" (low side roofs and a raised, glazed clerestory
# down the middle, the old Showground halls), "vault" (a curved roof across the short side), "canopy" (a
# slab on posts, Moore Park's bus shelters). Solid walls are the studios' and halls' blank sheds, the rest
# rows of windows. Read from the oblique Google Earth views against a 10 m scale (2026-11-22).
BRICK = (0.5, 0.22, 0.12)         # Google Earth sRGB (150, 80, 60), divided by the match light's lift (bluer in shade)
SANDSTONE = (0.68, 0.55, 0.33)    # (215, 190, 150)
CREAM = (0.68, 0.6, 0.45)         # the sheds' painted walls (225, 215, 195)
OFFICE = (0.7, 0.67, 0.56)        # white render (235, 235, 230)
METAL, BEIGE, GREY, DARK = (0.535, 0.515, 0.43), (0.65, 0.56, 0.4), (0.58, 0.58, 0.48), (0.45, 0.43, 0.37)
TERRACOTTA, PEACH = (0.42, 0.24, 0.16), (0.69, 0.57, 0.43)
SPEC = {
    492: (10.0, "flat", 0.0, OFFICE, GREY, False),         # the Entertainment Quarter's shops and cinemas
    534: (10.0, "hip", 5.0, CREAM, GREY, False),           # hipped, with a raised lantern in the middle
    535: (17.0, "gable", 2.0, CREAM, BEIGE, True),         # Disney's big stages
    536: (12.0, "flat", 0.0, OFFICE, GREY, False),
    537: (10.0, "flat", 0.0, OFFICE, GREY, False),
    538: (9.0, "flat", 0.0, OFFICE, DARK, False),
    539: (14.0, "gable", 6.0, CREAM, METAL, True),         # the Hordern Pavilion
    540: (9.0, "hip", 3.0, CREAM, PEACH, False),
    541: (12.0, "monitor", 5.0, BRICK, METAL, True),       # the old Showground hall by the SCG
    543: (8.0, "vault", 4.0, CREAM, BEIGE, True),
    544: (18.0, "monitor", 4.0, SANDSTONE, METAL, True),   # the Royal Hall of Industries
    546: (15.0, "gable", 2.0, CREAM, BEIGE, True),
    549: (15.0, "flat", 0.0, OFFICE, GREY, False),
    550: (10.0, "flat", 0.0, OFFICE, GREY, False),
    551: (16.0, "gable", 2.0, CREAM, BEIGE, True),
    552: (15.0, "gable", 2.0, CREAM, BEIGE, True),
    555: (8.0, "flat", 0.0, OFFICE, GREY, False),
    556: (14.0, "gable", 2.0, CREAM, BEIGE, True),
    557: (8.0, "hip", 4.0, BRICK, TERRACOTTA, False),      # red brick, terracotta hipped roofs
    558: (16.0, "gable", 2.0, CREAM, BEIGE, True),
    560: (10.0, "gable", 2.0, OFFICE, GREY, False),
    562: (13.0, "gable", 3.0, CREAM, BEIGE, True),
    563: (16.0, "flat", 0.0, SANDSTONE, GREY, False),      # the Showring's sandstone grandstand, its clock tower
    565: (8.0, "flat", 0.0, OFFICE, GREY, False),
    566: (4.0, "canopy", 0.0, OFFICE, (0.72, 0.69, 0.565), False),
    567: (4.0, "canopy", 0.0, OFFICE, (0.72, 0.69, 0.565), False),
    568: (4.0, "canopy", 0.0, OFFICE, (0.72, 0.69, 0.565), False),
}
CLOCK_TOWER = {563: (6.0, 28.0, 5.0)}      # side, height to the cap, the cap's rise (m)

tris = []


def quad(p0, p1, p2, p3, n, col):
    for t in ((p0, p1, p2), (p0, p2, p3)):
        for p in t:
            tris.extend(list(p) + list(n) + list(col))


def inside(pt, poly):
    x, y = pt
    c = False
    for (x0, y0), (x1, y1) in zip(poly, np.roll(poly, -1, 0)):
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


def split(buf):
    out, i = [], 0
    while i + 1 < len(buf):
        n = int(buf[i])
        out.append(buf[i:i + 2 + 2 * n])
        i += 2 + 2 * n
    return out


def strip_box(a, c, out, y0, y1, d0, d1, col, ends=True, front_only=False):
    """A box along wall edge a->c (2D x, z), d0..d1 metres out from the wall, y0..y1 up."""
    t = (c - a) / np.linalg.norm(c - a)
    o = np.array([out[0], out[2]])

    def P(p, d, y):
        q = p + o * d
        return (float(q[0]), y, float(q[1]))
    quad(P(a, d1, y0), P(c, d1, y0), P(c, d1, y1), P(a, d1, y1), out, col)                 # front
    if front_only:
        return
    quad(P(a, d0, y1), P(c, d0, y1), P(c, d1, y1), P(a, d1, y1), (0, 1, 0), col)           # top
    quad(P(a, d0, y0), P(c, d0, y0), P(c, d1, y0), P(a, d1, y0), (0, -1, 0), col)          # underside
    if ends:
        quad(P(a, d0, y0), P(a, d1, y0), P(a, d1, y1), P(a, d0, y1), (-t[0], 0, -t[1]), col)
        quad(P(c, d0, y0), P(c, d1, y0), P(c, d1, y1), P(c, d0, y1), (t[0], 0, t[1]), col)


def frame(foot):
    """The footprint's smallest enclosing rectangle: its centre, long axis u, short axis v, half length
    L and half width W. Pitched roofs are laid on it (s along u, t along v)."""
    r = Polygon(foot).minimum_rotated_rectangle
    c = np.array(r.exterior.coords)[:4]
    e1, e2 = c[1] - c[0], c[2] - c[1]
    if np.linalg.norm(e1) < np.linalg.norm(e2):
        e1, e2 = e2, e1
    u = e1 / np.linalg.norm(e1)
    v = np.array([-u[1], u[0]])
    return c.mean(0), u, v, np.linalg.norm(e1) / 2, np.linalg.norm(e2) / 2


def planes(kind, L, W, rise):
    """The roof as planar pieces over the frame: [(polygon in s, t; (a, b, c) with height a s + b t + c
    above the eave)], plus the lines (in s, t) of the monitor's clerestory glazing (t, y0, y1)."""
    big = L + W + 50.0
    if kind == "gable":
        return [(Polygon([(-big, 0), (big, 0), (big, big), (-big, big)]), (0.0, -rise / W, rise)),
                (Polygon([(-big, 0), (big, 0), (big, -big), (-big, -big)]), (0.0, rise / W, rise))], []
    if kind == "hip":
        k = rise / W
        d = max(L - W, 0.0)
        return [(Polygon([(-d, 0), (d, 0), (big + d, big), (-big - d, big)]), (0.0, -k, rise)),
                (Polygon([(-d, 0), (d, 0), (big + d, -big), (-big - d, -big)]), (0.0, k, rise)),
                (Polygon([(d, 0), (big + d, big), (big + d, -big)]), (-k, 0.0, k * L)),
                (Polygon([(-d, 0), (-big - d, big), (-big - d, -big)]), (k, 0.0, k * L))], []
    if kind == "monitor":
        wc, r1, gl = W / 3.0, 1.0, 3.0
        r2 = max(0.5, rise - r1)
        out = [(Polygon([(-big, wc), (big, wc), (big, big), (-big, big)]), (0.0, -r1 / (W - wc), r1 * W / (W - wc))),
               (Polygon([(-big, -wc), (big, -wc), (big, -big), (-big, -big)]), (0.0, r1 / (W - wc), r1 * W / (W - wc))),
               (Polygon([(-big, 0), (big, 0), (big, wc), (-big, wc)]), (0.0, -r2 / wc, r1 + gl + r2)),
               (Polygon([(-big, 0), (big, 0), (big, -wc), (-big, -wc)]), (0.0, r2 / wc, r1 + gl + r2))]
        return out, [(wc, r1, r1 + gl), (-wc, r1, r1 + gl)]
    if kind == "vault":
        n = 10
        ts = np.linspace(-W, W, n + 1)
        zs = rise * np.sqrt(np.maximum(0.0, 1.0 - (ts / W) ** 2))
        out = []
        for k in range(n):
            t0, t1 = (-big if k == 0 else ts[k]), (big if k == n - 1 else ts[k + 1])
            b = (zs[k + 1] - zs[k]) / (ts[k + 1] - ts[k])
            out.append((Polygon([(-big, t0), (big, t0), (big, t1), (-big, t1)]), (0.0, b, zs[k] - b * ts[k])))
        return out, []
    return [], []


def pitched_roof(foot, h, kind, rise, roof, wall, ccw):
    """A pitched roof over the footprint, the wall's gable ends filled up to it, and a monitor's
    clerestory glazed. Exact: each plane is clipped to the footprint and triangulated."""
    c, u, v, L, W = frame(foot)
    loc = np.c_[(foot - c) @ u, (foot - c) @ v]
    fp = Polygon(loc).buffer(0)
    pieces, glaze = planes(kind, L, W, rise)

    def world(s_, t_, y):
        q = c + u * s_ + v * t_
        return (float(q[0]), float(y), float(q[1]))

    for poly, (a, b, cc) in pieces:
        g = fp.intersection(poly)
        for part in getattr(g, "geoms", [g]):
            if part.is_empty or part.geom_type != "Polygon" or part.area < 0.05:
                continue
            rings = [np.array(part.exterior.coords)[:-1]] + [np.array(r.coords)[:-1] for r in part.interiors]
            pts = np.concatenate(rings)
            idx = earcut.triangulate_float64(pts, np.cumsum([len(r) for r in rings]).astype(np.uint32))
            for q in range(0, len(idx), 3):
                tri = [world(pts[i][0], pts[i][1], h + a * pts[i][0] + b * pts[i][1] + cc) for i in idx[q:q + 3]]
                n = np.cross(np.subtract(tri[1], tri[0]), np.subtract(tri[2], tri[0]))
                if np.linalg.norm(n) < 1e-9:
                    continue
                n = n / np.linalg.norm(n)
                if n[1] < 0:
                    n = -n
                for p_ in tri:
                    tris.extend(list(p_) + [float(x) for x in n] + list(roof))
    # the walls from the eave up to the roof: each edge split where it crosses a plane's edge
    cuts = [poly.exterior for poly, _ in pieces]
    for k in range(len(loc)):
        a2, c2 = loc[k], loc[(k + 1) % len(loc)]
        seg = LineString([a2, c2])
        ts_ = {0.0, 1.0}
        for e in cuts:
            x = seg.intersection(e)
            for g in getattr(x, "geoms", [x]):
                if g.geom_type == "Point":
                    ts_.add(seg.project(g, normalized=True))
        ts_ = sorted(ts_)
        L2 = float(np.linalg.norm(c2 - a2))
        if L2 < 0.05:
            continue
        o2 = (c2 - a2) / L2
        nrm = (o2[1], -o2[0]) if ccw > 0 else (-o2[1], o2[0])
        nw = u * nrm[0] + v * nrm[1]
        o = (float(nw[0]), 0.0, float(nw[1]))
        for t0, t1 in zip(ts_[:-1], ts_[1:]):
            if t1 - t0 < 1e-6:
                continue
            p0, p1 = a2 + (c2 - a2) * t0, a2 + (c2 - a2) * t1
            mid = Polygon([tuple(p0), tuple(p1), tuple((p0 + p1) / 2 - np.array(nrm) * 0.01)]).centroid
            for poly, (a, b, cc) in pieces:
                if poly.contains(mid):
                    y0, y1 = h + a * p0[0] + b * p0[1] + cc, h + a * p1[0] + b * p1[1] + cc
                    break
            else:
                continue
            if max(y0, y1) - h < 0.02:
                continue
            quad(world(p0[0], p0[1], h), world(p1[0], p1[1], h), world(p1[0], p1[1], y1), world(p0[0], p0[1], y0), o, wall)
    # a monitor's clerestory: glass from the side roofs up to the middle's eave
    for t_, y0, y1 in glaze:
        ln = fp.intersection(LineString([(-L - 5, t_), (L + 5, t_)]))
        for g in getattr(ln, "geoms", [ln]):
            if g.geom_type != "LineString" or g.length < 0.5:
                continue
            (s0, _), (s1, _) = g.coords[0], g.coords[-1]
            nw = v * np.sign(t_)
            quad(world(s0, t_, h + y0), world(s1, t_, h + y0), world(s1, t_, h + y1), world(s0, t_, h + y1),
                 (float(nw[0]), 0.0, float(nw[1])), GLASS)


def canopy(foot, h, roof, post):
    """A shelter: a 0.4 m roof slab on 0.3 m posts every 6 m round its edge."""
    idx = earcut.triangulate_float64(foot, np.array([len(foot)], np.uint32))
    for y, ny in ((h, 1.0), (h - 0.4, -1.0)):
        for q in range(0, len(idx), 3):
            for i in idx[q:q + 3]:
                tris.extend([float(foot[i][0]), y, float(foot[i][1]), 0.0, ny, 0.0] + list(roof))
    ccw = sum(foot[k, 0] * foot[(k + 1) % len(foot), 1] - foot[k, 1] * foot[(k + 1) % len(foot), 0] for k in range(len(foot)))
    for k in range(len(foot)):
        a, c = foot[k], foot[(k + 1) % len(foot)]
        L = float(np.linalg.norm(c - a))
        if L < 0.05:
            continue
        o = np.array([c[1] - a[1], 0.0, a[0] - c[0]]) / L * (1.0 if ccw > 0 else -1.0)
        quad((a[0], h - 0.4, a[1]), (c[0], h - 0.4, c[1]), (c[0], h, c[1]), (a[0], h, a[1]), tuple(o), roof)
        t = (c - a) / L
        for j in range(max(1, int(L // 6.0)) + 1):
            m = a + t * min(L, j * 6.0) - np.array([o[0], o[2]]) * 0.3
            box(m, 0.15, 0.0, h - 0.4, post)


def box(m, r, y0, y1, col, cap=0.0):
    """A square post or tower round m, r either side, with a pyramid cap of `cap` metres."""
    cs = [m + np.array(d) * r for d in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for k in range(4):
        a, c = cs[k], cs[(k + 1) % 4]
        mid = (a + c) / 2 - m
        o = (float(mid[0] / r), 0.0, float(mid[1] / r))
        quad((a[0], y0, a[1]), (c[0], y0, c[1]), (c[0], y1, c[1]), (a[0], y1, a[1]), o, col)
        if cap > 0.0:
            top = (float(m[0]), y1 + cap, float(m[1]))
            n = np.cross(np.subtract(top, (a[0], y1, a[1])), np.subtract((c[0], y1, c[1]), (a[0], y1, a[1])))
            n = n / np.linalg.norm(n) * (1 if n[1] > 0 else -1)
            for p_ in ((a[0], y1, a[1]), (c[0], y1, c[1]), top):
                tris.extend([float(x) for x in p_] + [float(x) for x in n] + [0.36, 0.34, 0.29])
    if cap <= 0.0:
        for p_ in (cs[0], cs[1], cs[2], cs[0], cs[2], cs[3]):
            tris.extend([float(p_[0]), y1, float(p_[1]), 0.0, 1.0, 0.0] + list(col))


def building(rec, b, far=False):
    n, h = int(rec[0]), float(rec[1])
    foot = rec[2:2 + 2 * n].reshape(-1, 2).astype(float)
    if np.allclose(foot[0], foot[-1]):
        foot = foot[:-1]
    wall = tuple(w * t for w, t in zip(WALLS[(b + 1) % len(WALLS)], TINT))
    area = abs(sum(foot[k, 0] * foot[(k + 1) % len(foot), 1] - foot[k, 1] * foot[(k + 1) % len(foot), 0]
                   for k in range(len(foot)))) / 2
    roofs = BIG_ROOFS if area > 1500.0 else SMALL_ROOFS if area > 300.0 else HOUSE_ROOFS
    roof = roofs[(b * 7 + 3) % len(roofs)]
    kind, rise, solid = "flat", 0.0, False
    if not far and b in SPEC:
        h, kind, rise, wall, roof, solid = SPEC[b]
    if kind == "canopy":
        canopy(foot, h, roof, wall)
        return
    pitched = kind != "flat"
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
        if solid:
            # a shed's blank wall, pilasters every 6 m and a band under the eave
            quad((a[0], 0.0, a[1]), (c[0], 0.0, c[1]), (c[0], h, c[1]), (a[0], h, a[1]), o, wall)
            strip_box(a, c, o, h - 0.8, h, 0.0, PROUD, wall, ends=False)
            strip_box(a, c, o, 0.0, 0.6, 0.0, PROUD * 0.5, tuple(x * 0.8 for x in wall), ends=False)
            t = (c - a) / L
            for j in range(1, int(L // 6.0) + 1):
                m = a + t * min(L - 0.25, j * 6.0)
                strip_box(m - t * 0.25, m + t * 0.25, o, 0.0, h - 0.8, 0.0, PROUD * 0.8, wall, ends=True)
            continue
        # the wall plane: glass, with the frame proud of it
        quad((a[0], 0.0, a[1]), (c[0], 0.0, c[1]), (c[0], h, c[1]), (a[0], h, a[1]), o, GLASS)
        if L < 1.5:
            strip_box(a, c, o, 0.0, h, 0.0, PROUD, wall, ends=False)
            continue
        for f in range(floors):
            y = f * fh
            if far:
                # past NEAR: one band proud from each floor to its sill, the windows a recessed ribbon
                # (its front face only: its 0.3 m top and underside are under a pixel from past NEAR)
                strip_box(a, c, o, y, y + SILL, 0.0, PROUD, wall, ends=False, front_only=True)
                continue
            strip_box(a, c, o, y, y + (0.35 if f else SILL), 0.0, PROUD, wall, ends=False)
            if f:
                strip_box(a, c, o, y + 0.35, y + SILL, 0.0, PROUD * 0.6, wall, ends=False)
        top = h if pitched else h + 0.5
        strip_box(a, c, o, h - 1.0, top, 0.0, PROUD, wall, ends=False, front_only=far)    # parapet band, or eave band
        bays = 1 if far else max(1, int(round(L / BAY)))      # far: piers at the corners only
        t = (c - a) / L
        for j in range(bays + 1):
            m = a + t * (L * j / bays)
            w = PIER_W / 2
            p0 = m - t * (0 if j == 0 else w)
            p1 = m + t * (0 if j == bays else w)
            strip_box(p0, p1, o, 0.0, top, 0.0, PROUD + 0.02, wall, ends=0 < j < bays)
    if pitched:
        pitched_roof(foot, h, kind, rise, roof, wall, ccw)
        return
    if not far and b in CLOCK_TOWER:
        # the tower stands in the building, at its nearest point to the middle of its curve
        from shapely.ops import nearest_points
        side, top, cap = CLOCK_TOWER[b]
        fp = Polygon(foot)
        m = np.array(nearest_points(fp.buffer(-side / 2), fp.centroid)[0].coords[0])
        box(m, side / 2, 0.0, top, wall, cap=cap)
    # the roof, a little under the parapet's top
    idx = earcut.triangulate_float64(foot, np.array([len(foot)], np.uint32))
    for q in range(0, len(idx), 3):
        p = [foot[idx[q + r]] for r in range(3)]
        for v in p:
            tris.extend([float(v[0]), h - 0.1, float(v[1]), 0.0, 1.0, 0.0] + list(roof))


def write_glb(path):
    """tris as a glb, one mesh per colour (glTF colours are linear), for the city past NEAR: Godot's import
    gives it levels of detail, so it costs little where it is small on screen."""
    import trimesh
    a = np.array(tris, "<f4").reshape(-1, 9)
    scene = trimesh.Scene()
    cols = np.round(a[:, 6:9], 3)
    keys, inv = np.unique(cols, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    for i, k in enumerate(keys):
        sel = np.flatnonzero(inv == i)
        sel = sel[: len(sel) // 3 * 3]
        v = a[sel, :3].astype(float)
        f = np.arange(len(v)).reshape(-1, 3)
        # wind every triangle to face the way its normal says (the quads were written either way round)
        nrm = a[sel, 3:6].reshape(-1, 3, 3)[:, 0]
        fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
        back = (fn * nrm).sum(1) < 0
        f[back] = f[back][:, ::-1]
        m = trimesh.Trimesh(vertices=v, faces=f, vertex_normals=a[sel, 3:6].astype(float), process=False)
        m.merge_vertices(merge_tex=True, merge_norm=False)      # corners shared only where the normals agree
        glass = np.allclose(k, GLASS, atol=0.002)
        m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
            name="city_%d" % i, baseColorFactor=[float(x) ** 2.2 for x in k] + [1.0], metallicFactor=0.0,
            roughnessFactor=0.4 if glass else 0.95, doubleSided=False))
        scene.add_geometry(m, node_name="city_%d" % i, geom_name="city_%d" % i)
    scene.export(path, include_normals=True)


def main():
    path = os.path.join(DIR, "buildings.bin")
    recs = split(np.fromfile(path, "<f4"))
    # surrounds.py writes every building to buildings.bin: split it again whenever it holds near ones
    near_first = not os.path.exists(NEAR_FILE) or any(
        np.hypot(*(r[2:2 + 2 * int(r[0])].reshape(-1, 2).mean(0) - PC)) < NEAR and r[1] >= 5.0 for r in recs)
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
        n = int(r[0])
        if inside(ALLIANZ, r[2:2 + 2 * n].reshape(-1, 2)):
            continue        # OpenStreetMap's outline of Allianz Stadium: allianz.py builds the stadium itself
        building(r, b)
    arr = np.array(tris, "<f4")
    arr.tofile(os.path.join(DIR, "facades.bin"))
    tris.clear()
    for b, r in enumerate(split(np.fromfile(path, "<f4"))):
        n = int(r[0])
        if not inside(ALLIANZ, r[2:2 + 2 * n].reshape(-1, 2)):
            building(r, b, far=True)
    write_glb(os.path.join(DIR, "city.glb"))
    print("city.glb: %d buildings past %d m, %d triangles" % (len(split(np.fromfile(path, "<f4"))), NEAR, len(tris) // 27))
    print("%d buildings (less Allianz's outline) with facades (%s), %d triangles" % (len(near), "moved out of buildings.bin" if near_first else "from near_buildings.bin", len(arr) // 27))


if __name__ == "__main__":
    main()
