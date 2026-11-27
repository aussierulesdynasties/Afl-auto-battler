"""Mesh helpers for the Norwood Oval model (pure numpy, no Blender): every part is a list of faces in
metres, x east, y north, z up, origin the centre circle at field level. build.py turns them into meshes.

A face is (points, material, uv): uv None means the material's own metre grid (build.py projects the
face onto its plane), else one (u, v) per point in metres. Nothing here is painted geometry: openings are
cut, reveals and sills are faces with depth."""
import math
import numpy as np

PARTS = {}


def V(*a):
    return np.array(a, float)


def add(part, pts, mat, uv=None):
    pts = [np.asarray(p, float) for p in pts]
    if len(pts) < 3:
        return
    PARTS.setdefault(part, []).append((pts, mat, uv))


def quad(part, a, b, c, d, mat, uv=None):
    add(part, [a, b, c, d], mat, uv)


def unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def perp(d):
    """The left normal of a plan direction (x, y)."""
    return np.array([-d[1], d[0]])


def prism(part, poly, z0, z1, wall, top=None, bottom=None):
    """A vertical extrusion of a plan polygon (either winding; walls always face out)."""
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
               for i in range(len(poly)))
    if area < 0:
        poly = list(reversed(poly))
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        add(part, [(x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)], wall)
    if top:
        add(part, [(x, y, z1) for x, y in poly], top)
    if bottom:
        add(part, [(x, y, z0) for x, y in reversed(poly)], bottom)


def obox(part, c, ang, w, d, z0, z1, wall, top=None, bottom=None):
    """A box centred on plan point c, its width w along bearing ang (rad from +x), depth d across."""
    u = np.array([math.cos(ang), math.sin(ang)])
    v = perp(u)
    c = np.asarray(c, float)
    pts = [c - u * w / 2 - v * d / 2, c + u * w / 2 - v * d / 2, c + u * w / 2 + v * d / 2, c - u * w / 2 + v * d / 2]
    prism(part, [tuple(p) for p in pts], z0, z1, wall, top, bottom)


def box3(part, p0, p1, w, h, mat, up=(0, 0, 1)):
    """A square-section member from p0 to p1 (w wide, h tall), e.g. a beam or a post."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    a = unit(p1 - p0)
    upv = np.asarray(up, float)
    if abs(np.dot(a, upv)) > 0.98:
        upv = np.array([1.0, 0, 0])
    s = unit(np.cross(a, upv))
    t = unit(np.cross(s, a))
    cs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    r0 = [p0 + s * w / 2 * i + t * h / 2 * j for i, j in cs]
    r1 = [p1 + s * w / 2 * i + t * h / 2 * j for i, j in cs]
    for k in range(4):
        add(part, [r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k]], mat)
    add(part, list(reversed(r0)), mat)
    add(part, r1, mat)


def cyl(part, c, z0, z1, r0, r1, mat, n=12, cap=None):
    x, y = c
    for i in range(n):
        t0, t1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        add(part, [(x + r0 * math.cos(t0), y + r0 * math.sin(t0), z0), (x + r0 * math.cos(t1), y + r0 * math.sin(t1), z0),
                   (x + r1 * math.cos(t1), y + r1 * math.sin(t1), z1), (x + r1 * math.cos(t0), y + r1 * math.sin(t0), z1)], mat)
    if cap:
        add(part, [(x + r1 * math.cos(2 * math.pi * i / n), y + r1 * math.sin(2 * math.pi * i / n), z1) for i in range(n)], cap)


def tube(part, p0, p1, r, mat, n=8):
    """A round member from p0 to p1."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    a = unit(p1 - p0)
    s = unit(np.cross(a, [0, 0, 1.0] if abs(a[2]) < 0.95 else [1.0, 0, 0]))
    t = np.cross(a, s)
    ring = [s * math.cos(2 * math.pi * i / n) * r + t * math.sin(2 * math.pi * i / n) * r for i in range(n)]
    for i in range(n):
        add(part, [p0 + ring[i], p0 + ring[(i + 1) % n], p1 + ring[(i + 1) % n], p1 + ring[i]], mat)


def wall(part, a, b, z0, z1, mat, openings=(), depth=0.25, reveal=None, glass=None, sill=None, sill_out=0.06,
         thick=None, back=None, head=None, bars=None, dress=None):
    """A wall face from plan a to plan b (outside on the right of a->b, i.e. facing perp(b-a) * -1 ...
    the face's normal is the right-hand normal of a->b), z0..z1, with rectangular openings cut through.

    openings: (s0, s1, h0, h1) in metres along the wall from a and up from z0. Each opening gets four
    reveal faces `depth` deep, a recessed glass (or dark void) pane, a sill standing proud `sill_out` with
    its top and ends, and optionally a head (lintel) band standing proud.
    An opening with a fifth item "pointed" gets a Gothic head: an equilateral pointed arch of glass over it,
    framed in `dress` (the brick or stone dressings round it). bars: the sash's glazing bars and meeting
    rail (timber), on openings under 1.8 m wide."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    L = float(np.linalg.norm(b - a))
    u = (b - a) / L
    nrm = -perp(u)            # the right-hand side faces out
    def P(s, h, off=0.0):
        q = a + u * s + nrm * off
        return np.array([q[0], q[1], z0 + h])
    H = z1 - z0
    kinds = {tuple(o[:4]): (o[4] if len(o) > 4 else None) for o in openings}
    ops = sorted([tuple(o[:4]) for o in openings if o[1] > o[0] and o[3] > o[2]])
    # Split the face into vertical strips at every opening edge; in each strip, solid bands between the openings.
    xs = sorted(set([0.0, L] + [o[0] for o in ops] + [o[1] for o in ops]))
    for i in range(len(xs) - 1):
        s0, s1 = xs[i], xs[i + 1]
        if s1 - s0 < 1e-6:
            continue
        mid = (s0 + s1) / 2
        holes = sorted([(o[2], o[3]) for o in ops if o[0] <= mid <= o[1]])
        h = 0.0
        for h0, h1 in holes + [(H, H)]:
            if h0 > h + 1e-6:
                add(part, [P(s0, h), P(s1, h), P(s1, min(h0, H)), P(s0, min(h0, H))], mat)
            h = max(h, h1)
    rv = reveal or mat
    for s0, s1, h0, h1 in ops:
        d = depth
        # reveals: jambs, head soffit, sill floor
        add(part, [P(s0, h0), P(s0, h1), P(s0, h1, -d), P(s0, h0, -d)], rv)
        add(part, [P(s1, h1), P(s1, h0), P(s1, h0, -d), P(s1, h1, -d)], rv)
        add(part, [P(s0, h1), P(s1, h1), P(s1, h1, -d), P(s0, h1, -d)], rv)
        add(part, [P(s1, h0), P(s0, h0), P(s0, h0, -d), P(s1, h0, -d)], rv)
        if glass:
            add(part, [P(s0, h0, -d), P(s1, h0, -d), P(s1, h1, -d), P(s0, h1, -d)], glass,
                uv=[(0, 0), (s1 - s0, 0), (s1 - s0, h1 - h0), (0, h1 - h0)])
        if bars and s1 - s0 < 1.8 and h1 - h0 > 0.9:
            bo, bw = -d + 0.04, 0.035
            m = (s0 + s1) / 2
            add(part, [P(m - bw, h0, bo), P(m + bw, h0, bo), P(m + bw, h1, bo), P(m - bw, h1, bo)], bars)
            hm = (h0 + h1) / 2 if kinds.get((s0, s1, h0, h1)) != "pointed" else h0 + (h1 - h0) * 0.62
            add(part, [P(s0, hm - bw, bo), P(s1, hm - bw, bo), P(s1, hm + bw, bo), P(s0, hm + bw, bo)], bars)
        if kinds.get((s0, s1, h0, h1)) == "pointed":
            w, m = s1 - s0, (s0 + s1) / 2
            def arch(e, off):     # the arch's outline, widened by e, standing off proud of the face
                pts = [P(s0 - e, h1, off)]
                for t in np.linspace(0.0, math.pi / 3, 7)[1:]:
                    pts.append(P(s1 + e - (w + 2 * e) * math.cos(t), h1 + (w + 2 * e) * math.sin(t), off))
                for t in np.linspace(math.pi / 3, 0.0, 7)[1:]:
                    pts.append(P(s0 - e + (w + 2 * e) * math.cos(t), h1 + (w + 2 * e) * math.sin(t), off))
                return pts
            if dress:
                o = arch(0.2, 0.012)
                for k in range(len(o) - 1):
                    add(part, [P(m, h1 - 0.001, 0.012), o[k], o[k + 1]][::-1], dress)
                for e0, e1 in ((s0 - 0.2, s0), (s1, s1 + 0.2)):     # the dressed jambs
                    add(part, [P(e0, h0, 0.012), P(e1, h0, 0.012), P(e1, h1, 0.012), P(e0, h1, 0.012)], dress)
            g = arch(0.0, 0.02)
            for k in range(len(g) - 1):
                add(part, [P(m, h1 - 0.001, 0.02), g[k], g[k + 1]][::-1], glass or "window_dark")
        if sill and h0 > 0.05:
            so, st = sill_out, 0.07
            e0, e1 = s0 - 0.08, s1 + 0.08
            add(part, [P(e0, h0 - st, so), P(e1, h0 - st, so), P(e1, h0, so), P(e0, h0, so)], sill)
            add(part, [P(e0, h0, so), P(e1, h0, so), P(e1, h0, 0), P(e0, h0, 0)], sill)
            add(part, [P(e0, h0 - st, 0), P(e1, h0 - st, 0), P(e1, h0 - st, so), P(e0, h0 - st, so)], sill)
            add(part, [P(e0, h0 - st, 0), P(e0, h0 - st, so), P(e0, h0, so), P(e0, h0, 0)], sill)
            add(part, [P(e1, h0 - st, so), P(e1, h0 - st, 0), P(e1, h0, 0), P(e1, h0, so)], sill)
        if head:
            ho, ht = 0.05, 0.22
            e0, e1 = s0 - 0.12, s1 + 0.12
            add(part, [P(e0, h1, ho), P(e1, h1, ho), P(e1, h1 + ht, ho), P(e0, h1 + ht, ho)], head)
            add(part, [P(e0, h1 + ht, ho), P(e1, h1 + ht, ho), P(e1, h1 + ht, 0), P(e0, h1 + ht, 0)], head)
            add(part, [P(e1, h1, 0), P(e0, h1, 0), P(e0, h1, ho), P(e1, h1, ho)], head)
            add(part, [P(e0, h1, 0), P(e0, h1, ho), P(e0, h1 + ht, ho), P(e0, h1 + ht, 0)], head)
            add(part, [P(e1, h1, ho), P(e1, h1, 0), P(e1, h1 + ht, 0), P(e1, h1 + ht, ho)], head)
    if back:   # the wall's inner face (where it can be seen from behind), plain
        add(part, [P(L, 0, -(thick or depth)), P(0, 0, -(thick or depth)), P(0, H, -(thick or depth)), P(L, H, -(thick or depth))], back)


def band(part, a, b, z0, z1, out, mat, ends=True):
    """A string course / band standing `out` proud of the wall line a->b (outside on the right)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    u = unit(b - a)
    n = -perp(u)
    A, B = a + n * out, b + n * out
    add(part, [(A[0], A[1], z0), (B[0], B[1], z0), (B[0], B[1], z1), (A[0], A[1], z1)], mat)
    add(part, [(A[0], A[1], z1), (B[0], B[1], z1), (b[0], b[1], z1), (a[0], a[1], z1)], mat)
    add(part, [(B[0], B[1], z0), (A[0], A[1], z0), (a[0], a[1], z0), (b[0], b[1], z0)], mat)
    if ends:
        add(part, [(a[0], a[1], z0), (A[0], A[1], z0), (A[0], A[1], z1), (a[0], a[1], z1)], mat)
        add(part, [(B[0], B[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (B[0], B[1], z1)], mat)


def offset_poly(pts, d):
    """Offset an open plan polyline by d to its left, mitred at the joints."""
    pts = [np.asarray(p, float) for p in pts]
    out = []
    for i in range(len(pts)):
        if i == 0:
            n = perp(unit(pts[1] - pts[0]))
            out.append(pts[0] + n * d)
        elif i == len(pts) - 1:
            n = perp(unit(pts[-1] - pts[-2]))
            out.append(pts[-1] + n * d)
        else:
            n0 = perp(unit(pts[i] - pts[i - 1]))
            n1 = perp(unit(pts[i + 1] - pts[i]))
            m = unit(n0 + n1)
            out.append(pts[i] + m * d / max(0.3, float(np.dot(m, n0))))
    return out


def along(pts, s):
    """The point and direction at distance s along a polyline."""
    pts = [np.asarray(p, float) for p in pts]
    for i in range(len(pts) - 1):
        L = float(np.linalg.norm(pts[i + 1] - pts[i]))
        if s <= L or i == len(pts) - 2:
            u = (pts[i + 1] - pts[i]) / L
            return pts[i] + u * min(s, L), u
        s -= L
    return pts[-1], unit(pts[-1] - pts[-2])


def length(pts):
    return sum(float(np.linalg.norm(np.asarray(pts[i + 1], float) - np.asarray(pts[i], float))) for i in range(len(pts) - 1))
