"""The north and south frontages of Norwood Oval, modelled one by one (the rest of the suburb is surrounds.py's).

North, between the ground and Beulah Road: the backs of the Beulah Road houses (80, 82, the pale hipped
villa, the tan-roofed villa, the two-storey villas 90 and 92 and the long pale house east of them), the
sheds and houses 1 and 2 between them and the ground, and Norwood Primary School: its synthetic court,
the white flat-roofed block, the small hipped classroom, the white annex and the old school under its
long pale roofs with the bell turret.

South, between the ground and The Parade: Norwood Oval Memorial Gardens (the rotunda, the memorial, the
paths and beds), the backs of The Parade's shops to the west, the Adelaide Presbyterian Church, 81 The
Parade and the buildings east of it, and the block by the south-west corner.

Every outline is traced on Google Earth's top-down tiles (2026-11-23): the frontage mosaics (tiles at
y 155.2 north, -164.8 south, 260 m up; /root/nw/front, never committed) or the ground's own mosaic where
that tile looks more nearly straight down. A roof seen from above leans away from its tile's centre by
its height over 260 m; `lean` takes that out, for the eave height each building is given. Traced edges
are the roof's (overhang included); walls stand `over` inside them. Heights are judged from Google
Earth's angled views (n_000, n_045, n_315): single-storey villas about 3.5 m to the eave, the two-storey
villas about 7 m. Outlines are to about half a metre; window rows on walls that face away from the ground
are not checked against photos.
Plan metres from the centre circle (x east, y north).
"""
import math
import numpy as np
from nwlib import V, add, box3, obox, prism
from north import gable_building
from land import T, LAST, on_land

P = "town_front"
H = 260.0
# the tiles' centres: the frontage mosaics, and the ground's own nine-tile mosaic (plan.png)
TILES = {"north": [(-75.8, 155.2), (4.2, 155.2), (84.2, 155.2)],
         "south": [(-75.8, -164.8), (4.2, -164.8), (84.2, -164.8)],
         "plan": [(-75.8, -84.8), (4.2, -84.8), (84.2, -84.8), (-75.8, -4.8), (84.2, -4.8), (-75.8, 75.2),
                  (4.2, 75.2), (84.2, 75.2), (4.2, -4.8)]}


def lean(x, y, h, src):
    """Where a point seen at (x, y) on a top-down tile really is, at height h."""
    t = min(TILES[src], key=lambda c: math.hypot(x - c[0], (y - c[1]) * 1.6))
    k = 1.0 - h / H
    return (t[0] + (x - t[0]) * k, t[1] + (y - t[1]) * k)


def traced(x0, x1, y0, y1, h, src):
    """A roof outline traced as x0..x1, y0..y1 on a tile, its eave h up: the true outline."""
    a = lean(x0, y0, h, src)
    b = lean(x1, y1, h, src)
    return a[0], b[0], a[1], b[1]


def house(part, rect, src, z_eave, z_ridge, wallmat, roofmat, ns=True, over=0.45, hip=True, windows=None, **kw):
    """A hipped (or gabled) house whose roof is traced as rect = (x0, x1, y0, y1); ns: ridge north-south."""
    with on_land(part):
        x0, x1, y0, y1 = traced(*rect, z_eave, src)
        c = ((x0 + x1) / 2, (y0 + y1) / 2)
        lx, ly = x1 - x0 - 2 * over, y1 - y0 - 2 * over
        if windows is None:
            windows = (1.2, 1.0, 2.6, 3.4) if z_eave < 5.0 else [(1.2, 1.0, 2.8, 3.4), (1.2, 4.0, 5.8, 3.4)]
        if ns:
            gable_building(part, c, math.pi / 2, ly, lx, z_eave, z_ridge, wallmat, roofmat, over=over, windows=windows, hip=hip, **kw)
        else:
            gable_building(part, c, 0.0, lx, ly, z_eave, z_ridge, wallmat, roofmat, over=over, windows=windows, hip=hip, **kw)
        return x0, x1, y0, y1


def flat(part, rect, src, z, wallmat, roofmat, parapet=0.0):
    """A flat-roofed block traced as rect; a parapet (if any) stands round the roof."""
    with on_land(part):
        x0, x1, y0, y1 = traced(*rect, z + parapet, src)
        prism(part, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 0.0, z, wallmat, top=roofmat)
        if parapet:
            for (a, b) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
                box3(part, V(*a, z), V(*b, z), 0.25, parapet, wallmat)
        return x0, x1, y0, y1


def chimney(part, p, z0, z1, mat="brick_terrace", base=None):
    """A chimney stack on a roof; base: the floor level of the building it stands on."""
    with on_land(part, level=base):
        obox(part, p, 0.0, 0.7, 0.5, z0, z1, mat, top=mat)
        obox(part, p, 0.0, 0.86, 0.66, z1 - 0.25, z1 - 0.1, "render_cream", top="render_cream", bottom="render_cream")


def solar(part, roof, z_eave, z_ridge, ya, yb, east=True, over=0.45, cols=(1.0, 3.3), base=None):
    """Rows of solar panels on the east (or west) slope of a north-south ridge, roof = its true outline,
    between y ya and yb, from cols[0] to cols[1] metres in from the roof's edge."""
    x0, x1, y0, y1 = roof
    hw = (x1 - x0) / 2 - over
    rise = z_ridge - z_eave
    edge = x1 if east else x0
    def z(x):
        return z_eave - over * rise / hw + abs(edge - x) * rise / hw + 0.06
    xa, xb = (edge - cols[1], edge - cols[0]) if east else (edge + cols[0], edge + cols[1])
    base = LAST[0] if base is None else base
    with on_land(part, level=base):
        for y in np.arange(ya, yb - 0.98, 1.05):
            q = [V(xb, y, z(xb)), V(xb, y + 0.98, z(xb)), V(xa, y + 0.98, z(xa)), V(xa, y, z(xa))]
            add(part, q if east else q[::-1], "window_dark")


def fence(part, pts, h, every=3.0, mat="steel_dark"):
    """A chain-mesh ball fence on posts along the closed outline pts, h tall (posts and top rail)."""
    for k in range(len(pts)):
        (x0, y0), (x1, y1) = pts[k], pts[(k + 1) % len(pts)]
        L = math.hypot(x1 - x0, y1 - y0)
        for t in np.arange(0.0, L, every):
            x, y = x0 + (x1 - x0) * t / L, y0 + (y1 - y0) * t / L
            box3(part, V(x, y, 0.0), V(x, y, h), 0.06, 0.06, mat)
        box3(part, V(x0, y0, h), V(x1, y1, h), 0.05, 0.05, mat)
        box3(part, V(x0, y0, h * 0.5), V(x1, y1, h * 0.5), 0.04, 0.04, mat)


def north_houses():
    """The backs of the Beulah Road houses and the houses and sheds between them and the ground."""
    part = P + "_beulah"
    # 80 and 82: single-storey villas under pale hipped roofs (tile y 155.2)
    r = house(part, (-109.5, -99.0, 124.7, 142.0), "north", 3.6, 6.8, "bluestone", "roof_zinc", quoins="render_cream")
    solar(part, r, 3.6, 6.8, r[2] + 5.4, r[2] + 12.2, cols=(1.6, 3.4))
    house(part, (-96.0, -86.25, 132.0, 144.0), "north", 3.6, 6.6, "bluestone", "roof_pale", quoins="render_cream")
    # the pale hipped villa (two road lots west of the tan roof) and its low skillion at the back
    house(part, (-72.75, -53.25, 135.0, 147.0), "north", 3.6, 6.9, "sandstone", "roof_zinc", ns=False)
    flat(part, (-72.5, -57.0, 131.25, 135.0), "north", 3.0, "render_cream", "roof_zinc")
    # the tan-roofed villa, its ridge north-south
    house(part, (-53.0, -42.75, 129.75, 147.75), "north", 3.6, 6.7, "brick_red", "roof_tan")
    # 90: two-storey, dark slate hipped roofs, a one-storey back under its own roof, a white flat-roofed wing, chimneys
    x0, x1, y0, y1 = house(part, (-41.25, -27.0, 131.0, 146.0), "north", 7.0, 11.4, "sandstone", "roof_grey")
    b90 = LAST[0]
    # its back (the ground side) under a lower roof, one storey (Google Earth n_000)
    house(part, (-41.25, -27.0, 126.5, 131.4), "north", 3.6, 6.0, "sandstone", "roof_grey", ns=False)
    flat(part, (-40.5, -27.5, 123.5, 126.75), "north", 3.3, "render_white", "render_white")
    for p in ((-35.0, 133.0), (-33.3, 133.0), (-39.0, 139.5), (-32.0, 139.5)):
        q = lean(*p, 11.0, "north")
        chimney(part, q, 9.0, 12.4, "render_cream", base=b90)
    # 92: two-storey, grey hipped roofs: the main body and two hipped bays to the back (the ground side),
    # solar panels on the east slope
    x0, x1, y0, y1 = house(part, (-24.0, -10.75, 131.0, 148.0), "north", 7.0, 11.0, "sandstone", "roof_slate_grey")
    b92 = LAST[0]
    for xs in ((-24.0, -17.5), (-17.5, -10.75)):
        house(part, (xs[0], xs[1], 123.25, 131.4), "north", 6.6, 9.6, "sandstone", "roof_slate_grey", ns=True)
    solar(part, (x0, x1, y0, y1), 7.0, 11.0, y0 + 3.6, y1 - 3.6, base=b92)
    # the long single-storey house east of 92: a hipped main roof, a lean-to along its west side
    house(part, (-4.5, 4.0, 121.5, 147.75), "north", 3.7, 6.4, "render_cream", "roof_zinc")
    flat(part, (-9.75, -4.5, 125.0, 147.0), "north", 3.2, "render_cream", "roof_zinc")
    # house 1 (ground's mosaic): a low hipped front block, a hipped rear block and a beige-roofed lean-to
    house(part, (-104.5, -89.5, 102.5, 111.75), "plan", 3.4, 5.6, "render_cream", "roof_pale", ns=False)
    house(part, (-97.0, -87.5, 111.75, 118.5), "plan", 3.4, 6.2, "render_cream", "roof_pale")
    flat(part, (-100.0, -97.0, 112.0, 117.5), "plan", 3.0, "render_cream", "roof_tan")
    flat(part, (-116.0, -112.0, 109.0, 116.5), "plan", 3.0, "render_white", "roof_pale")
    flat(part, (-89.3, -83.3, 99.0, 103.0), "plan", 2.6, "render_white", "roof_pale")
    # house 2: a single-storey villa under a pale hipped roof
    house(part, (-66.75, -55.25, 105.0, 115.25), "plan", 3.5, 6.3, "bluestone", "roof_pale", ns=False,
          quoins="render_cream")
    # the white shed behind the pale villa
    flat(part, (-71.25, -62.25, 119.25, 123.0), "north", 3.0, "render_white", "roof_zinc")
    # the sheds behind the long building north of the ground: red-roofed, white and grey, gables north-south
    house(part, (-32.0, -23.3, 115.3, 122.0), "north", 2.8, 4.4, "brick_red", "roof_red", hip=False, windows=(1.0, 0.9, 2.1, 3.0),
          gable_mat="brick_red")
    house(part, (-33.0, -24.0, 107.0, 114.3), "plan", 2.8, 4.0, "corr_cream", "roof_zinc", hip=False, windows=None,
          gable_mat="corr_cream")
    house(part, (-23.7, -17.0, 107.3, 114.0), "plan", 2.8, 4.0, "corr_bluegrey", "roof_pale", hip=False, windows=None,
          gable_mat="corr_bluegrey")
    house(part, (-20.0, -16.0, 120.7, 123.0), "north", 2.6, 4.0, "render_cream", "roof_slate_grey", windows=None)
    # the small sheds and studios in the back yards (flat or near-flat roofs)
    for rect, wm, rm in (((-90.0, -83.7, 119.3, 122.7), "render_cream", "roof_grey_green"),
                         ((-100.0, -95.7, 119.3, 121.3), "render_white", "roof_pale"),
                         ((-61.3, -58.0, 121.7, 124.3), "render_cream", "roof_slate_grey"),
                         ((-56.7, -52.7, 126.7, 128.3), "render_cream", "roof_grey_green"),
                         ((-51.7, -47.3, 124.7, 128.7), "render_white", "roof_pale")):
        flat(part, rect, "north", 2.6, wm, rm)


def school():
    """Norwood Primary School, north-east of the ground (OSM: amenity school; its building by the ground's
    north-east corner is town.py's)."""
    part = P + "_school"
    # the synthetic court (soccer markings) and its ball fence
    x0, x1, y0, y1 = traced(8.0, 49.7, 133.3, 153.3, 0.0, "north")
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    court = on_land(part, level=float(T.height(cx, cy))).__enter__()   # the court is level, cut into the slope
    obox(part, (cx, cy), 0.0, x1 - x0, y1 - y0, 0.0, 0.04, "court_green", top="court_green")
    obox(part, (cx, y0 - 1.0), 0.0, x1 - x0, 2.0, 0.0, 0.03, "concrete", top="concrete")
    box3(part, V(cx, y0 + 0.6, 0.045), V(cx, y1 - 0.6, 0.045), 0.08, 0.006, "paint_white")
    for k in range(40):
        a0, a1 = 2 * math.pi * k / 40, 2 * math.pi * (k + 1) / 40
        box3(part, V(cx + 3.0 * math.cos(a0), cy + 3.0 * math.sin(a0), 0.045),
             V(cx + 3.0 * math.cos(a1), cy + 3.0 * math.sin(a1), 0.045), 0.08, 0.006, "paint_white")
    # the boxes as painted (traced): one west of halfway, two side by side to its east
    for bx0, bx1, by0, by1 in ((15.3, 20.7, 136.3, 146.0), (38.0, 43.3, 137.7, 147.7), (43.3, 48.7, 137.7, 147.7)):
        for (a, b) in (((bx0, by0), (bx1, by0)), ((bx1, by0), (bx1, by1)), ((bx1, by1), (bx0, by1)), ((bx0, by1), (bx0, by0))):
            box3(part, V(*a, 0.045), V(*b, 0.045), 0.08, 0.006, "paint_white")
    for (a, b) in (((x0 + 0.6, y0 + 0.6), (x1 - 0.6, y0 + 0.6)), ((x1 - 0.6, y0 + 0.6), (x1 - 0.6, y1 - 0.6)),
                   ((x1 - 0.6, y1 - 0.6), (x0 + 0.6, y1 - 0.6)), ((x0 + 0.6, y1 - 0.6), (x0 + 0.6, y0 + 0.6))):
        box3(part, V(*a, 0.045), V(*b, 0.045), 0.08, 0.006, "paint_white")
    fence(part, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 3.0)
    court.__exit__(None, None, None)
    # the flat-roofed block facing the ground, the out of school hours care (Google Earth n_000, n_045,
    # n_180: red brick, one tall storey, a parapet),
    # its east end under a pale hipped roof
    flat(part, (10.0, 32.5, 110.5, 129.3), "north", 4.0, "brick_red", "roof_zinc", parapet=0.5)
    house(part, (32.0, 35.5, 112.0, 129.0), "north", 4.0, 5.6, "render_white", "roof_pale", windows=None)
    # the small hipped classroom east of it
    house(part, (39.7, 48.7, 117.3, 130.0), "north", 3.4, 6.0, "brick_red", "roof_grey")
    # the white annex and its lower pale wing
    flat(part, (64.3, 76.7, 116.7, 125.0), "north", 3.8, "render_white", "render_white", parapet=0.3)
    flat(part, (65.0, 69.0, 110.0, 116.7), "north", 3.0, "render_white", "roof_pale")
    # the old school (Google Earth sN_tur, 2026-11-26): rubble-stone walls with red-brick quoins and
    # dressings, pointed (Gothic) windows, steep pale corrugated roofs with gables (west wing and east wing
    # north-south, the main range east-west between them), a chimney and the slate spire
    w = [(1.2, 1.2, 3.4, 3.2, "pointed")]
    kw = dict(windows=w, hip=False, quoins="brick_red", dress="brick_red")
    house(part, (49.3, 58.7, 130.7, 155.0), "north", 5.2, 10.4, "rubble_stone", "roof_zinc", **kw)
    house(part, (58.0, 97.0, 138.5, 155.0), "north", 5.2, 10.6, "rubble_stone", "roof_zinc", ns=False, **kw)
    house(part, (96.7, 106.7, 134.3, 156.5), "north", 5.2, 10.4, "rubble_stone", "roof_zinc", **kw)
    flat(part, (93.0, 103.0, 134.0, 140.0), "north", 3.4, "brick_red", "roof_pale")
    bs = LAST[0]
    q = lean(76.75, 154.0, 12.0, "north")
    turret = on_land(part, level=bs).__enter__()
    obox(part, q, 0.0, 3.4, 3.0, 0.0, 12.5, "rubble_stone", top="rubble_stone")
    tip = V(q[0], q[1], 17.0)
    c = [V(q[0] + dx, q[1] + dy, 12.5) for dx, dy in ((-1.9, -1.7), (1.9, -1.7), (1.9, 1.7), (-1.9, 1.7))]
    for k in range(4):
        add(part, [c[k], c[(k + 1) % 4], tip], "roof_slate_grey")
    turret.__exit__(None, None, None)
    chimney(part, lean(71.0, 141.5, 10.0, "north"), 8.0, 11.8, "brick_red", base=bs)


def lancet(part, c, w, z0, z1, dress, glass="window_dark"):
    """A tall pointed window on a north-facing gable wall at plan c: glass from z0 to z1 (the arch's apex),
    framed in its dressings, standing a hand proud of the wall."""
    def outline(e, y):
        r = w + 2 * e
        h = z1 - r * math.sin(math.pi / 3)          # the springing line
        pts = [V(c[0] + w / 2 + e, y, z0 - e), V(c[0] + w / 2 + e, y, h)]
        for t in np.linspace(0.0, math.pi / 3, 7)[1:]:
            pts.append(V(c[0] - w / 2 - e + r * math.cos(t), y, h + r * math.sin(t)))
        for t in np.linspace(math.pi / 3, 0.0, 7)[1:]:
            pts.append(V(c[0] + w / 2 + e - r * math.cos(t), y, h + r * math.sin(t)))
        pts.append(V(c[0] - w / 2 - e, y, z0 - e))
        return pts
    for e, y, mat in ((0.22, c[1] + 0.012, dress), (0.0, c[1] + 0.024, glass)):
        o = outline(e, y)
        ctr = V(c[0], y, (z0 + z1) / 2)
        for k in range(len(o)):
            add(part, [ctr, o[(k + 1) % len(o)], o[k]], mat)


def path(part, a, b, w, mat="concrete", z=0.03):
    """A paved path from a to b, w wide, a few centimetres proud of the grass."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    ang = math.atan2(d[1], d[0])
    L = float(np.linalg.norm(d))
    k = max(1, int(L / 4.0))
    for i in range(k):            # in 4 m pieces, each on the land under it
        c = a + d * (i + 0.5) / k
        with on_land(part, level=float(T.height(*c))):
            obox(part, c, ang, L / k + 0.02, w, 0.0, z, mat, top=mat)


def rotunda(part, c, r, z_eave, z_apex, n=8):
    """An octagonal rotunda: a raised floor, posts, a frieze and a red pyramid roof."""
    obox(part, c, 0.0, 2 * r * 0.95, 2 * r * 0.95, 0.0, 0.45, "brick_red", top="concrete")
    pts = [V(c[0] + r * math.cos(2 * math.pi * (k + 0.5) / n), c[1] + r * math.sin(2 * math.pi * (k + 0.5) / n), 0) for k in range(n)]
    rr = r + 0.35
    eave = [V(c[0] + rr * math.cos(2 * math.pi * (k + 0.5) / n), c[1] + rr * math.sin(2 * math.pi * (k + 0.5) / n), z_eave - 0.2) for k in range(n)]
    tip = V(c[0], c[1], z_apex)
    for k in range(n):
        p = pts[k]
        box3(part, V(p[0], p[1], 0.45), V(p[0], p[1], z_eave - 0.3), 0.16, 0.16, "timber_white")
        q = pts[(k + 1) % n]
        box3(part, V(p[0], p[1], z_eave - 0.45), V(q[0], q[1], z_eave - 0.45), 0.12, 0.3, "timber_white")
        box3(part, V(p[0], p[1], 1.2), V(q[0], q[1], 1.2), 0.06, 0.08, "timber_white")
        add(part, [eave[k], eave[(k + 1) % n], tip], "roof_red")
        add(part, [eave[(k + 1) % n], eave[k], V(c[0], c[1], z_eave - 0.2)], "underside")
    box3(part, tip, tip + V(0, 0, 0.9), 0.06, 0.06, "steel_dark")


def gardens():
    """Norwood Oval Memorial Gardens, south of the ground: the rotunda, the memorial at the crossing, the two
    diagonal paths and the round beds (Google Earth top-down, tile y -164.8; trees are surrounds.py's)."""
    part = P + "_gardens"
    with on_land(part):
        rotunda(part, lean(-26.5, -142.0, 4.0, "south"), 3.6, 3.2, 5.6)
    path(part, (-60.0, -135.0), (-5.0, -162.0), 2.0)
    path(part, (-6.0, -140.0), (-48.0, -160.0), 2.0)
    with on_land(part):
        obox(part, (-27.0, -149.0), 0.0, 1.2, 1.2, 0.0, 1.6, "sandstone", top="sandstone")
    for c in ((-45.0, -149.7), (-15.7, -149.3)):
      with on_land(part):
        prism(part, [(c[0] + 1.6 * math.cos(a), c[1] + 1.6 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 17)[:-1]],
              0.0, 0.25, "sandstone", top="timber_dark")


def south_buildings():
    """South of the ground: the backs of The Parade's shops (west), the church and its neighbours (east),
    and the sheds by the ground's south-west corner (Google Earth top-down; heights from n_180, ses_180)."""
    part = P + "_parade"
    # west: The Parade's shops run back from the street in long flat-roofed blocks
    for rect, z, wm, rm in (((-118.0, -109.0, -147.3, -116.3), 7.0, "render_white", "roof_zinc"),
                            ((-118.0, -108.0, -170.0, -147.3), 4.5, "render_white", "roof_pale"),
                            ((-107.3, -94.7, -165.3, -157.3), 4.0, "render_white", "roof_pale"),
                            ((-93.0, -74.3, -129.0, -116.3), 7.0, "brick_red", "roof_zinc"),
                            ((-93.0, -81.7, -160.7, -129.0), 7.5, "brick_red", "roof_pale"),
                            ((-81.7, -73.3, -166.7, -148.7), 4.0, "render_white", "roof_pale"),
                            ((-73.3, -67.3, -168.0, -158.0), 3.5, "render_white", "roof_pale")):
        flat(part, rect, "south", z, wm, rm, parapet=0.4)
    house(part, (-90.0, -81.7, -169.0, -160.7), "south", 4.0, 5.8, "render_white", "roof_pale", windows=None)
    # the block behind the car park: a gabled roof, ridge east-west, its north slope under solar panels
    x0, x1, y0, y1 = house(part, (-107.3, -94.7, -157.3, -142.7), "south", 4.0, 6.6, "render_white", "roof_pale",
                           ns=False, hip=False, windows=None)
    bb = LAST[0]
    hw, rise, over = (y1 - y0) / 2 - 0.45, 2.6, 0.45
    def zn(y):                        # the north slope, from the north eave (y1) up to the ridge
        return 4.0 - over * rise / hw + (y1 - y) * rise / hw + 0.06
    for xa in np.arange(x0 + 0.8, x1 - 1.8, 1.05):
      with on_land(part, level=bb):
        ya, yb = y1 - 3.0, y1 - 1.0
        add(part, [V(xa, yb, zn(yb)), V(xa + 0.98, yb, zn(yb)), V(xa + 0.98, ya, zn(ya)), V(xa, ya, zn(ya))], "window_dark")
        add(part, [V(xa, ya - 0.1, zn(ya - 0.1)), V(xa + 0.98, ya - 0.1, zn(ya - 0.1)), V(xa + 0.98, ya - 2.1, zn(ya - 2.1)),
                   V(xa, ya - 2.1, zn(ya - 2.1))][::-1], "window_dark")
    # the white flat-roofed block by the south-west corner (ground's mosaic; ses_180: plant on its roof)
    flat(part, (-100.7, -89.0, -111.0, -95.0), "plan", 4.4, "render_white", "roof_zinc", parapet=0.3)
    # the small low building south of the stand
    flat(part, (20.0, 33.3, -116.7, -109.0), "plan", 3.0, "render_cream", "roof_pale")
    # 75: a small single-storey building under a brown roof, west of the church
    flat(part, (1.3, 10.3, -145.0, -141.0), "south", 3.0, "brick_red", "roof_red")
    # the Adelaide Presbyterian Church: a tall nave, its stone gable to the ground, slate roof, ridge north-south
    # (Google Earth c180, ses_180; west of it the top-down shows only its shadow and trees)
    # (steep: eave 4.8 m, ridge 12.5 m, measured against the stand's roof in ses_180), a white-roofed porch
    # across its north end
    # (sS_ch, 2026-11-26: grey rubble stone, sandstone dressings, lancet windows, a tall lancet in the gable)
    x0, x1, y0, y1 = house(part, (37.3, 52.0, -150.0, -131.7), "south", 4.8, 12.5, "church_stone", "roof_slate_grey",
                           hip=False, windows=(1.0, 1.2, 3.6, 3.0, "pointed"), quoins="sandstone", dress="sandstone")
    with on_land(part, level=LAST[0]):
        lancet(part, ((x0 + x1) / 2, y1 - 0.45), 1.5, 4.0, 8.2, "sandstone")
    px0, px1, py0, py1 = flat(part, (38.0, 51.3, -131.7, -129.3), "south", 3.4, "church_stone", "roof_zinc")
    with on_land(part, level=LAST[0]):     # its pointed doorway
        lancet(part, ((px0 + px1) / 2, py1), 1.4, 0.0, 2.9, "sandstone", glass="timber_dark")
    # 81 The Parade: a two-storey red-brick house under a pale hipped roof, and the white block east of it
    house(part, (56.3, 71.3, -150.0, -130.3), "south", 7.0, 10.0, "brick_red", "roof_pale", quoins="render_cream")
    flat(part, (72.0, 83.0, -158.7, -132.3), "south", 7.0, "render_white", "roof_zinc", parapet=0.4)
    flat(part, (72.0, 83.0, -161.3, -158.7), "south", 3.5, "brick_red", "roof_grey")
    # the long building with its pale grey roof, ridge east-west
    house(part, (84.3, 112.0, -156.0, -138.0), "south", 4.0, 6.5, "render_cream", "roof_pale", ns=False, hip=False)


def build():
    north_houses()
    school()
    gardens()
    south_buildings()
    return {}
