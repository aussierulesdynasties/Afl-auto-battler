"""Manuka's landmark buildings, modelled by hand from Google Earth 3D (looked at, not copied) for town.py:
the churches with their gabled naves and bell towers, and the corrections to buildings the general rules get
wrong (Manuka Pool's white walls, the brick of the churches). REPLACES lists the footprints these replace.

Each church: its OpenStreetMap footprint split into rectangles (town.rects_of); the biggest is the nave under a
steep gabled roof, the others aisles and transepts under lower gables; walls of tall lancet windows set into the
brick; a square bell tower stood at the corner Google Earth shows it, with its louvred belfry openings recessed
and a pyramid or parapet cap.
"""
import math

import numpy as np

import town as T

CHURCHES = {
    # St Christopher's Cathedral, Forrest (1939): pale ochre brick, terracotta tiles, a tall square campanile at its
    # south-west corner with a pyramid roof.
    "220590159": dict(wall=(198, 164, 116), roof=(168, 84, 60), eave=9.0, pitch=38.0, tower=(225.0, 6.0, 30.0, "pyramid")),
    # St Paul's Anglican, Manuka (1939): red-brown brick, a square tower at its north-east corner with a flat
    # parapet top.
    "770539336": dict(wall=(150, 74, 54), roof=(132, 70, 56), eave=7.5, pitch=40.0, tower=(45.0, 5.0, 22.0, "parapet")),
    # Canberra Baptist Church, Kingston (1929): red brick, gabled, a short square tower.
    "220589428": dict(wall=(156, 80, 60), roof=(120, 90, 76), eave=6.5, pitch=40.0, tower=(315.0, 4.0, 15.0, "parapet")),
    # St Andrew's Presbyterian, Forrest (1934): cream stone, a tall square tower with corner pinnacles.
    "1245948292": dict(wall=(206, 196, 172), roof=(136, 132, 124), eave=10.0, pitch=40.0, tower=(135.0, 7.0, 36.0, "parapet")),
}
OVERRIDES = {
    # Manuka Pool (1931): white-rendered pavilions along the pool, the entry under a terracotta hip.
    "220575608": dict(wall=(236, 232, 220), roof="flat", levels=1),
    "220575661": dict(wall=(236, 232, 220), roof="flat", levels=1),
    "220575609": dict(wall=(236, 232, 220), roof="hipped", roof_colour=(176, 86, 62), levels=1),
}
REPLACES = list(CHURCHES)


def gable(acc, key, c, u, v, hu, hv, z, pitch, col, wall, over=0.35):
    """A gabled roof along u over a rectangle, the gable ends walled in the building's brick."""
    if hv > hu:
        u, v, hu, hv = v, -u, hv, hu
    u, v = np.asarray(u, float), np.asarray(v, float)
    c = np.asarray(c, float)
    rise = hv * math.tan(math.radians(pitch))
    def P(a, b, zz):
        p = c + u * a + v * b
        return (p[0], p[1], zz)
    H, W = hu + over, hv + over
    zr = z + rise
    zo = z - over * math.tan(math.radians(pitch))
    acc.quad(key, P(-H, -W, zo), P(H, -W, zo), P(H, 0, zr), P(-H, 0, zr), col)
    acc.quad(key, P(H, W, zo), P(-H, W, zo), P(-H, 0, zr), P(H, 0, zr), T.shade(col, 0.9))
    for s in (-1, 1):
        acc.tri(key, P(s * hu, -hv, z), P(s * hu, hv, z), P(s * hu, 0, zr - 0.05), T.shade(wall, 0.95))
        acc.quad(key, P(s * H, -W, zo - 0.25), P(s * H, 0, zr - 0.25), P(s * H, 0, zr), P(s * H, -W, zo), T.FASCIA)
        acc.quad(key, P(s * H, 0, zr - 0.25), P(s * H, W, zo - 0.25), P(s * H, W, zo), P(s * H, 0, zr), T.FASCIA)


def tower(acc, key, p, u, w, z0, h, cap, wall, roof):
    u = np.asarray(u, float)
    v = np.array([-u[1], u[0]])
    p = np.asarray(p, float)
    pts = [p - u * w / 2 - v * w / 2, p + u * w / 2 - v * w / 2, p + u * w / 2 + v * w / 2, p - u * w / 2 + v * w / 2]
    top = z0 + h
    bz0, bz1 = top - 5.5, top - 1.4          # the belfry's louvred openings
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        L = float(np.hypot(*(b - a)))
        wins = [(L / 2 - 0.9, L / 2 + 0.9, bz0, bz1)]
        if h > 18:
            wins.append((L / 2 - 0.35, L / 2 + 0.35, z0 + h * 0.35, z0 + h * 0.35 + 2.6))
        T.wall(acc, key, a, b, z0 - 0.3, top, wall, wins, None)
        # A string course under the belfry, standing 0.12 m proud.
        n = np.array([(b - a)[1], -(b - a)[0]]) / L
        a2, b2 = a + n * 0.12, b + n * 0.12
        for zz in (bz0 - 0.6, top - 0.3):
            acc.quad(key, (a2[0], a2[1], zz), (b2[0], b2[1], zz), (b2[0], b2[1], zz + 0.3), (a2[0], a2[1], zz + 0.3),
                     T.shade(wall, 1.08))
            acc.quad(key, (a[0], a[1], zz + 0.3), (b[0], b[1], zz + 0.3), (b2[0], b2[1], zz + 0.3), (a2[0], a2[1], zz + 0.3),
                     T.shade(wall, 1.12))
    if cap == "pyramid":
        apex = (p[0], p[1], top + w * 0.9)
        for i in range(4):
            a, b = pts[i], pts[(i + 1) % 4]
            acc.tri(key, (a[0], a[1], top), (b[0], b[1], top), apex, T.shade(roof, 0.9 + 0.05 * i))
    else:
        T.flat_roof(acc, key, [tuple(q) for q in pts], top, (120, 118, 112), wall, False, 0)
        if cap == "parapet":
            for q in pts:   # corner pinnacles
                T.box(acc, key, q, u, 0.7, 0.7, top + 0.7, top + 2.0, T.shade(wall, 1.05))


def church(acc, b, spec, land):
    ring = T.simplify(T.ccw_ring([tuple(p) for p in b["ring"]]))
    P = np.asarray(ring)
    cx, cy = P.mean(0)
    key = (T.block_of(cx, cy), "wall")
    rkey = (T.block_of(cx, cy), "roof")
    zg = land.z(P[:, 0], P[:, 1])
    floor = float(zg.max()) + 0.4
    base = float(zg.min()) - 0.4
    eave = floor + spec["eave"]
    wall = spec["wall"]
    for i in range(len(ring)):
        p0, p1 = ring[i], ring[(i + 1) % len(ring)]
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        wins = []
        n = int((L - 2.0) / 3.6)
        for k in range(n):
            c = (k + 0.5) * L / n
            wins.append((c - 0.45, c + 0.45, floor + 2.2, floor + min(spec["eave"] - 1.4, 6.0)))
        T.wall(acc, key, p0, p1, base, eave, wall, wins, None)
    rs = T.rects_of(ring, 1.0)
    rs.sort(key=lambda r: -r[3] * r[4])
    for k, (c, u, v, hu, hv) in enumerate(rs):
        gable(acc, rkey, c, u, v, hu, hv, eave if k == 0 else eave - 1.2, spec["pitch"], spec["roof"], wall)
    brg, w, h, cap = spec["tower"]
    # The tower stands at the footprint's corner nearest the given bearing.
    a = math.radians(brg)
    d = P @ np.array([math.sin(a), math.cos(a)])
    corner = P[int(np.argmax(d))]
    u = rs[0][1] if rs else np.array([1.0, 0.0])
    inward = np.array([cx, cy]) - corner
    inward /= np.linalg.norm(inward)
    tp = corner + inward * w * 0.5
    tower(acc, key, tp, u, w, base, h + (floor - base), cap, wall, spec["roof"])


def apply_overrides(buildings):
    for b in buildings:
        if b["id"] in OVERRIDES:
            b.update(OVERRIDES[b["id"]])


def build(acc, land, buildings):
    for b in buildings:
        if b["id"] in CHURCHES:
            church(acc, b, CHURCHES[b["id"]], land)
