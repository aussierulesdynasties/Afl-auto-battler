"""The ground round the turf: the white picket fence on the grass edge, the concrete apron, the low terraces
with their benches (east and north), the asphalt walk, the venue's outer edge, and the four light towers.

The fence line is OpenStreetMap's pitch outline (way 190682898, the grass edge) as a 6-term Fourier radius,
moved 0.5 m west and 2.0 m north onto Google Earth's grass edge (checked on the top-down mosaic)."""
import json
import math
import os
import numpy as np
from nwlib import V, add, box3, cyl, tube, obox, unit, perp, offset_poly

HERE = os.path.dirname(os.path.abspath(__file__))
FC = np.array(json.load(open(os.path.join(HERE, "fence_fourier.json"))))
SHIFT = np.array([-0.5, 2.0])
P = "arena"


def r_fence(t):
    m = np.array([1] + [f(j * t) for j in range(1, 7) for f in (math.cos, math.sin)])
    return float(m @ FC)


def fence_pt(deg):
    t = math.radians(deg)
    r = r_fence(t)
    return np.array([r * math.cos(t), r * math.sin(t)]) + SHIFT


N = 720
LOOP = [fence_pt(360.0 * i / N) for i in range(N)]


_NRM = []


def rp(d, i):
    """Point i of the fence line offset d metres outward (the loop runs anticlockwise: outward is the right)."""
    if not _NRM:
        for k in range(N):
            a, b, c = LOOP[k - 1], LOOP[k], LOOP[(k + 1) % N]
            n0 = -perp(unit(b - a))
            n1 = -perp(unit(c - b))
            m = unit(n0 + n1)
            _NRM.append(m / max(0.5, float(np.dot(m, n0))))
    i %= N
    return LOOP[i] + _NRM[i] * d


class _Ring:
    def __init__(self, d):
        self.d = d

    def __getitem__(self, i):
        return rp(self.d, i)


def ring(d):
    return _Ring(d)


def deg_of(i):
    return 360.0 * i / N


# Terraces by bearing from the centre (deg, anticlockwise from east): how many low steps rise behind the
# apron. East and north-east: three; the north end: two; the north-west and the stands: none; the south-east:
# two (AFLW 2025 photos 01, 03, 24; Google Earth's east and north views).
TERR = [(0, 3), (60, 3), (80, 2), (120, 2), (140, 0), (290, 0), (300, 2), (330, 3), (360, 3)]
# The flat concourse width behind the terraces to the venue's edge, by bearing (top-down mosaic).
WALK = [(0, 2.4), (30, 2.6), (60, 4.0), (90, 9.0), (120, 9.0), (140, 6.0), (165, 2.5), (205, 2.5), (230, 5.0),
        (250, 9.5), (290, 10.0), (310, 6.0), (330, 3.0), (360, 2.4)]
APRON = 1.3
TREAD, RISE = 0.85, 0.28


def interp(tab, deg):
    return float(np.interp(deg % 360, [a for a, _ in tab], [b for _, b in tab]))


def fence():
    """White timber pickets on two rails between square posts, 1.1 m (photos 03, 23, 24)."""
    L = LOOP + [LOOP[0]]
    acc = 0.0
    post_every = 2.4
    for i in range(N):
        a, b = L[i], L[i + 1]
        seg = float(np.linalg.norm(b - a))
        u = unit(b - a)
        n = -perp(u)
        # rails
        for z in (0.25, 0.85):
            box3(P + "_fence", (a[0] - n[0] * 0.05, a[1] - n[1] * 0.05, z), (b[0] - n[0] * 0.05, b[1] - n[1] * 0.05, z), 0.04, 0.09, "paint_white")
        s = (-acc) % 0.13
        while s < seg:
            p = a + u * s
            q = p + n * 0.0
            # a picket with a pointed top: four sides and two sloped caps
            w, t = 0.075, 0.022
            c0 = np.array([q[0], q[1]])
            pts = [c0 - u * w / 2, c0 + u * w / 2, c0 + u * w / 2 + n * t, c0 - u * w / 2 + n * t]
            h0, h1 = 0.06, 1.02
            for k in range(4):
                p0, p1 = pts[k], pts[(k + 1) % 4]
                add(P + "_fence", [(p0[0], p0[1], h0), (p1[0], p1[1], h0), (p1[0], p1[1], h1), (p0[0], p0[1], h1)], "paint_white")
            tip = c0 + n * t / 2
            add(P + "_fence", [(pts[3][0], pts[3][1], h1), (pts[2][0], pts[2][1], h1), (tip[0], tip[1], h1 + 0.07)], "paint_white")
            add(P + "_fence", [(pts[1][0], pts[1][1], h1), (pts[0][0], pts[0][1], h1), (tip[0], tip[1], h1 + 0.07)], "paint_white")
            add(P + "_fence", [(pts[0][0], pts[0][1], h1), (pts[3][0], pts[3][1], h1), (tip[0], tip[1], h1 + 0.07)], "paint_white")
            add(P + "_fence", [(pts[2][0], pts[2][1], h1), (pts[1][0], pts[1][1], h1), (tip[0], tip[1], h1 + 0.07)], "paint_white")
            s += 0.13
        acc = (acc + seg) % 0.13
    # posts
    total = sum(float(np.linalg.norm(L[i + 1] - L[i])) for i in range(N))
    s, i, run = 0.0, 0, 0.0
    while i < N:
        a, b = L[i], L[i + 1]
        seg = float(np.linalg.norm(b - a))
        while s < run + seg:
            p = a + (b - a) * (s - run) / seg
            u = unit(b - a)
            n = -perp(u)
            q = p - n * 0.06
            obox(P + "_fence", q, math.atan2(u[1], u[0]), 0.1, 0.1, 0.0, 1.15, "paint_white", top="paint_white")
            s += post_every
        run += seg
        i += 1


def surfaces():
    """Apron, terraces, walk: strips round the loop, each strip's height from its bearing's step count."""
    for i in range(N):
        j = (i + 1) % N
        d0, d1 = deg_of(i), deg_of(i + 0.5)
        nst = int(round(interp(TERR, d1)))
        walk = interp(WALK, d1)
        def strip(r0, r1, z, mat):
            a0, b0 = RINGS[r0][i], RINGS[r0][j]
            a1, b1 = RINGS[r1][i], RINGS[r1][j]
            add(P + "_ground", [(a0[0], a0[1], z), (b0[0], b0[1], z), (b1[0], b1[1], z), (a1[0], a1[1], z)], mat)
        def riser(r, z0, z1, mat):
            a, b = RINGS[r][i], RINGS[r][j]
            add(P + "_ground", [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], mat)
        strip(0.0, APRON, 0.0, "concrete")
        r = APRON
        z = 0.0
        for k in range(nst):
            riser(r, z, z + RISE, "concrete_riser")
            z += RISE
            strip(r, r + TREAD, z, "concrete")
            r += TREAD
        rw = r + walk
        strip(r, rw, z, "asphalt")
        if z > 0:
            # the back of the terrace drops to the street behind it
            a, b = RINGS[rw][i], RINGS[rw][j]
            add(P + "_ground", [(b[0], b[1], 0.0), (a[0], a[1], 0.0), (a[0], a[1], z), (b[0], b[1], z)], "concrete_riser")
        strip(rw, rw + 6.0, 0.0, "asphalt")


def benches():
    """Aluminium bench seats on the terraces, every 4.8 m, with gaps at the stairs."""
    for i in range(0, N, 4):
        d = deg_of(i)
        nst = int(round(interp(TERR, d)))
        if nst == 0 or (i // 4) % 3 == 2:
            continue
        for k in range(nst):
            r = APRON + k * TREAD + 0.55
            z = (k + 1) * RISE
            a, b = RINGS_B[(k, 0)][i], RINGS_B[(k, 0)][(i + 4) % N]
            u = unit(b - a)
            n = -perp(u)
            a1, b1 = a + u * 0.2, b - u * 0.2
            for off, zz, w, h in ((0.0, z + 0.42, 0.36, 0.05), (0.22, z + 0.72, 0.05, 0.28)):
                p0, p1 = a1 + n * off, b1 + n * off
                box3(P + "_benches", (p0[0], p0[1], zz), (p1[0], p1[1], zz), w, h, "alu")
            for s in (0.15, 0.85):
                p = a1 + (b1 - a1) * s
                box3(P + "_benches", (p[0], p[1], z), (p[0], p[1], z + 0.42), 0.05, 0.05, "alu")


RINGS = {}
RINGS_B = {}


def towers():
    """Four light towers (NW, NE, SE, SW): white tapered poles, a lattice head of lamps tilted to the field
    (photos 19, AFLW 01, 24). Bases on the top-down mosaic (the poles' feet beside the shadows)."""
    H = 38.0
    for name, (x, y) in {"nw": (-57.0, 54.5), "ne": (54.0, 59.3), "se": (58.5, -56.0), "sw": (-47.0, -64.5)}.items():
        part = P + "_tower_" + name
        cyl(part, (x, y), 0.0, 0.6, 0.75, 0.75, "concrete", n=16, cap="concrete")
        cyl(part, (x, y), 0.6, H - 1.5, 0.48, 0.3, "paint_white", n=16)
        to = unit(np.array([-x, -y]))
        side = perp(to)
        c = np.array([x, y, H]) + np.append(to, 0) * 0.8
        tilt = math.radians(30)
        up = np.append(-to, 0) * math.sin(tilt) + V(0, 0, 1) * math.cos(tilt)
        fw = np.cross(np.append(side, 0), up)
        hw, hh = 3.2, 2.0
        # the frame: a rectangle of square steel, three rows of eight lamps (box housings, glass faces)
        corners = [c - np.append(side, 0) * hw - up * hh, c + np.append(side, 0) * hw - up * hh,
                   c + np.append(side, 0) * hw + up * hh, c - np.append(side, 0) * hw + up * hh]
        for k in range(4):
            box3(part, corners[k], corners[(k + 1) % 4], 0.14, 0.14, "paint_white")
        for k in range(1, 3):
            a = corners[0] + (corners[3] - corners[0]) * k / 3
            b = corners[1] + (corners[2] - corners[1]) * k / 3
            box3(part, a, b, 0.1, 0.1, "paint_white")
        box3(part, (x, y, H - 1.6), c - up * hh * 0.2, 0.4, 0.4, "paint_white")
        for row in range(3):
            for col in range(8):
                p = c + np.append(side, 0) * (-hw + 0.4 + col * (2 * hw - 0.8) / 7) + up * (-hh + 0.65 + row * (2 * hh - 1.3) / 2)
                # a lamp: a 0.55 x 0.45 box 0.3 deep, its face toward the field
                for s0, s1, mat in ((0.0, 0.3, "lamp_body"),):
                    pass
                q = [p + np.append(side, 0) * sx * 0.27 + up * sy * 0.22 for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                qf = [v + fw * 0.12 for v in q]
                qb = [v - fw * 0.22 for v in q]
                add(part, qf, "lamp_glass")
                add(part, list(reversed(qb)), "lamp_body")
                for k in range(4):
                    add(part, [qb[k], qb[(k + 1) % 4], qf[(k + 1) % 4], qf[k]], "lamp_body")


def grass():
    """Grass inside the fence, a hand under the match's own turf: it shows only where the real ground's
    squarer corners reach past the match's elliptical turf, and in the fly-through."""
    c = np.array([1.97, -0.53, -0.04])
    for i in range(N):
        a, b = LOOP[i], LOOP[(i + 1) % N]
        add(P + "_grass", [c, (a[0], a[1], -0.04), (b[0], b[1], -0.04)], "grass")


def build():
    global RINGS
    for d in sorted(set([0.0, APRON] + [APRON + k * TREAD for k in range(1, 4)])):
        RINGS[d] = ring(d)
    for k in range(4):
        RINGS_B[(k, 0)] = ring(APRON + k * TREAD + 0.5)
    class Lazy(dict):
        def __missing__(self, d):
            return ring(d)
    RINGS = Lazy(RINGS)
    fence()
    grass()
    surfaces()
    benches()
    towers()
    return {}
