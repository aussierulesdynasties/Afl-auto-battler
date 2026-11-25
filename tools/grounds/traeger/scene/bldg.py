"""Alice Springs' buildings round Traeger Park, stood up from OpenStreetMap footprints.

Each building gets walls, a roof as Alice Springs builds them and, near the ground, real window openings:

- Houses and small buildings: a hipped corrugated-iron roof at 22 degrees over brick or block walls 2.7 m high
  on a 0.3 m slab, the roof running 0.6 m past the walls with a fascia and a soffit under it. An L or T shaped
  house is cut into rectangles, each under its own hip, so the roofs meet in valleys as real ones do.
- Big buildings (over 600 m2): a low 6 degree corrugated roof, 0.3 m eaves, walls 4.5 m (or their storeys).
- Footprints that are not square-cornered: a flat roof behind a 0.5 m parapet.
- Carports and open roofs: a thin roof on posts.
- Within WINDOW_R of the oval every wall gets window openings, 0.12 m deep with their reveals and glass set
  back in them, never a texture.

Roof colours are measured per building off Google Earth's straight-down views (sample.py); wall colours are
Alice Springs' cream and red-brown brick and painted block, in the shares Google Earth's oblique views show.
The corrugations and brick coursing are textures (too small to model); everything with depth is geometry.
"""
import math

import numpy as np

WINDOW_R = 420.0
PITCH = math.radians(22.0)
LOW_PITCH = math.radians(6.0)


class Batch:
    def __init__(self):
        self.P, self.N, self.C, self.UV, self.F = [], [], [], [], []
        self.n = 0

    def quad(self, a, b, c, d, nrm, col, uv=None):
        """a b c d counter-clockwise seen from the normal side."""
        self.P += [a, b, c, d]
        self.N += [nrm] * 4
        self.C += [col] * 4
        self.UV += uv if uv is not None else [(0, 0)] * 4
        k = self.n
        self.F += [(k, k + 1, k + 2), (k, k + 2, k + 3)]
        self.n += 4

    def tri(self, a, b, c, nrm, col, uv=None):
        self.P += [a, b, c]
        self.N += [nrm] * 3
        self.C += [col] * 3
        self.UV += uv if uv is not None else [(0, 0)] * 3
        k = self.n
        self.F.append((k, k + 1, k + 2))
        self.n += 3

    def arrays(self):
        return (np.array(self.P, np.float32).reshape(-1, 3), np.array(self.N, np.float32).reshape(-1, 3),
                np.array(self.F, np.int64).reshape(-1, 3), np.array(self.UV, np.float32).reshape(-1, 2),
                np.array(self.C, np.uint8).reshape(-1, 4))


def X(e, y, n):
    """east/north/up metres to the model's glTF frame (x east, y up, z south)."""
    return (float(e), float(y), float(-n))


def _norm(v):
    v = np.asarray(v, float)
    L = np.linalg.norm(v)
    return tuple(v / L) if L > 0 else (0.0, 1.0, 0.0)


def _face_n(a, b, c):
    return _norm(np.cross(np.subtract(b, a), np.subtract(c, a)))


def clean(p):
    p = [tuple(q) for q in p]
    if p[0] == p[-1]:
        p = p[:-1]
    out = []
    for q in p:
        if not out or math.dist(q, out[-1]) > 0.2:
            out.append(q)
    if len(out) > 2 and math.dist(out[0], out[-1]) < 0.2:
        out.pop()
    a = sum(out[i][0] * out[(i + 1) % len(out)][1] - out[(i + 1) % len(out)][0] * out[i][1] for i in range(len(out)))
    if a < 0:
        out.reverse()
    return out, abs(a) / 2


def orient(p):
    """The angle of the building's longest edge (its grid), and whether every edge keeps to that grid."""
    best, ang = 0, 0.0
    for a, b in zip(p, p[1:] + p[:1]):
        L = math.dist(a, b)
        if L > best:
            best, ang = L, math.atan2(b[1] - a[1], b[0] - a[0])
    ok = True
    for a, b in zip(p, p[1:] + p[:1]):
        L = math.dist(a, b)
        if L < 0.8:
            continue
        t = (math.atan2(b[1] - a[1], b[0] - a[0]) - ang) % (math.pi / 2)
        if min(t, math.pi / 2 - t) > math.radians(9):
            ok = False
    return ang, ok


def rects(p, ang):
    """An orthogonal footprint cut into rectangles (in the building's own frame), and the frame."""
    c, s = math.cos(-ang), math.sin(-ang)
    q = [(x * c - y * s, x * s + y * c) for x, y in p]
    # snap each edge to its axis
    xs = sorted(set(round(v[0], 1) for v in q))
    ys = sorted(set(round(v[1], 1) for v in q))
    xs = _merge(xs)
    ys = _merge(ys)
    cells = np.zeros((len(ys) - 1, len(xs) - 1), bool)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            cells[j, i] = _inside(q, ((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2))
    out = []
    used = np.zeros_like(cells)
    for j in range(cells.shape[0]):
        i = 0
        while i < cells.shape[1]:
            if cells[j, i] and not used[j, i]:
                i1 = i
                while i1 + 1 < cells.shape[1] and cells[j, i1 + 1] and not used[j, i1 + 1]:
                    i1 += 1
                j1 = j
                while j1 + 1 < cells.shape[0] and cells[j1 + 1, i:i1 + 1].all() and not used[j1 + 1, i:i1 + 1].any():
                    j1 += 1
                used[j:j1 + 1, i:i1 + 1] = True
                out.append((xs[i], ys[j], xs[i1 + 1], ys[j1 + 1]))
                i = i1 + 1
            else:
                i += 1
    return [r for r in out if r[2] - r[0] > 1.2 and r[3] - r[1] > 1.2]


def _merge(v):
    out = [v[0]]
    for x in v[1:]:
        if x - out[-1] > 0.6:
            out.append(x)
    return out


class Builder:
    def __init__(self):
        self.walls = {"facade_brick": Batch(), "facade_render": Batch()}
        self.roof = Batch()      # roof_corr: corrugated iron
        self.trim = Batch()      # fascias, soffits, sills, posts: plain paint
        self.glass = Batch()
        self.count = 0

    def add(self, p_en, y0, kind, roof_col, wall_col, wall_mat, storeys=1, r=1e9):
        p, area = clean(p_en)
        if len(p) < 3 or area < 6:
            return
        self.count += 1
        if kind in ("carport", "roof"):
            self._carport(p, y0, roof_col)
            return
        big = area > 600
        H = y0 + 0.3 + (4.5 if big and storeys == 1 else 3.2 * storeys - 0.3 + (0.0 if storeys == 1 else 0.3))
        ang, ortho = orient(p)
        self._walls(p, y0, H, wall_col, wall_mat, windows=r < WINDOW_R, storeys=storeys, big=big)
        if ortho:
            rs = rects(p, ang)
            if rs:
                eave = 0.3 if big else 0.6
                pitch = LOW_PITCH if big else PITCH
                for rc in rs:
                    self._hip(rc, ang, H, eave, pitch, roof_col)
                return
        self._flat(p, H, roof_col, wall_col)

    # -- walls -------------------------------------------------------------------------------
    def _walls(self, p, y0, H, col, mat, windows, storeys, big):
        """Walls storey by storey (a band 3.2 m high each, the top one up to the eaves), each band with
        its own window openings."""
        b = self.walls[mat]
        n = len(p)
        bands = []
        z = y0
        for s_ in range(storeys):
            top = H if s_ == storeys - 1 else y0 + 0.3 + 3.2 * (s_ + 1)
            bands.append((z, top, z if s_ else y0 + 0.3))
            z = top
        for k in range(n):
            a, c = p[k], p[(k + 1) % n]
            L = math.dist(a, c)
            if L < 0.05:
                continue
            d = ((c[0] - a[0]) / L, (c[1] - a[1]) / L)
            out = (d[1], -d[0])                      # CCW footprint: outward is to the right
            nrm = _norm(X(out[0], 0, out[1]))
            ops = self._openings(L, big) if windows else []
            for zb, zt, floor in bands:
                u = 0.0
                for (o0, o1, s0, s1) in ops + [(L, L, 0, 0)]:
                    if o0 > u:
                        self._panel(b, a, d, u, o0, zb, zt, nrm, col)
                    if o1 > o0:
                        lo, hi = floor + s0, min(floor + s1, zt - 0.15)
                        self._panel(b, a, d, o0, o1, zb, lo, nrm, col)
                        self._panel(b, a, d, o0, o1, hi, zt, nrm, col)
                        self._opening(a, d, out, o0, o1, lo, hi, col)
                    u = max(u, o1)

    def _openings(self, L, big):
        """Windows along a wall: 1.8 m wide on a 3.6 m rhythm (2.4 on 4.2 for big buildings), sill 0.9 m
        and head 2.1 m above the floor."""
        if L < 2.6:
            return []
        w, pitch = (1.8, 3.6) if not big else (2.4, 4.2)
        k = max(1, int((L - 0.8) // pitch))
        if k * pitch > L - 0.4:
            w = min(w, (L - 0.8) / k - 0.6)
            if w < 0.6:
                return []
        start = (L - k * pitch) / 2 + (pitch - w) / 2
        return [(start + i * pitch, start + i * pitch + w, 0.9, 2.1 + (0.4 if big else 0.0)) for i in range(k)]

    def _panel(self, b, a, d, u0, u1, z0, z1, nrm, col):
        if z1 - z0 < 0.01 or u1 - u0 < 0.01:
            return
        p0 = X(a[0] + d[0] * u0, z0, a[1] + d[1] * u0)
        p1 = X(a[0] + d[0] * u1, z0, a[1] + d[1] * u1)
        p2 = X(a[0] + d[0] * u1, z1, a[1] + d[1] * u1)
        p3 = X(a[0] + d[0] * u0, z1, a[1] + d[1] * u0)
        uv = [(u0, -z0), (u1, -z0), (u1, -z1), (u0, -z1)]
        b.quad(p0, p1, p2, p3, nrm, col, uv)

    def _opening(self, a, d, out, u0, u1, z0, z1, wall_col):
        dep = 0.12
        inn = (-out[0] * dep, -out[1] * dep)
        def P(u, z, deep=False):
            e = a[0] + d[0] * u + (inn[0] if deep else 0)
            n = a[1] + d[1] * u + (inn[1] if deep else 0)
            return X(e, z, n)
        t = self.trim
        frame = (226, 224, 218, 255)
        # reveals: left, right, sill (facing up), head (facing down)
        t.quad(P(u0, z0), P(u0, z0, True), P(u0, z1, True), P(u0, z1), _norm(X(d[0], 0, d[1])), wall_col)
        t.quad(P(u1, z0, True), P(u1, z0), P(u1, z1), P(u1, z1, True), _norm(X(-d[0], 0, -d[1])), wall_col)
        t.quad(P(u0, z0), P(u1, z0), P(u1, z0, True), P(u0, z0, True), (0.0, 1.0, 0.0), frame)
        t.quad(P(u0, z1, True), P(u1, z1, True), P(u1, z1), P(u0, z1), (0.0, -1.0, 0.0), wall_col)
        g = self.glass
        nrm = _norm(X(out[0], 0, out[1]))
        g.quad(P(u0, z0, True), P(u1, z0, True), P(u1, z1, True), P(u0, z1, True), nrm, (255, 255, 255, 255))
        # a mullion down the middle of wide windows, standing proud of the glass
        if u1 - u0 > 1.4:
            m = (u0 + u1) / 2
            w = 0.03
            q = lambda u, z: X(a[0] + d[0] * u + inn[0] * 0.5, z, a[1] + d[1] * u + inn[1] * 0.5)
            t.quad(q(m - w, z0), q(m + w, z0), q(m + w, z1), q(m - w, z1), nrm, frame)

    # -- roofs ---------------------------------------------------------------------------------
    def _hip(self, rc, ang, H, eave, pitch, col):
        x0, y0, x1, y1 = rc[0] - eave, rc[1] - eave, rc[2] + eave, rc[3] + eave
        c, s = math.cos(ang), math.sin(ang)
        W = lambda x, y, z: X(x * c - y * s, z, x * s + y * c)
        along_x = (x1 - x0) >= (y1 - y0)
        half = ((y1 - y0) if along_x else (x1 - x0)) / 2
        rise = half * math.tan(pitch)
        zt = H + rise
        if along_x:
            ym = (y0 + y1) / 2
            r0, r1 = (x0 + half, ym), (x1 - half, ym)
        else:
            xm = (x0 + x1) / 2
            r0, r1 = (xm, y0 + half), (xm, y1 - half)
        A, B, C, D = W(x0, y0, H), W(x1, y0, H), W(x1, y1, H), W(x0, y1, H)
        R0, R1 = W(r0[0], r0[1], zt), W(r1[0], r1[1], zt)
        rb = self.roof
        if along_x:
            faces = [(A, B, R1, R0), (C, D, R0, R1)]
            tris = [(B, C, R1), (D, A, R0)]
        else:
            faces = [(B, C, R1, R0), (D, A, R0, R1)]
            tris = [(A, B, R0), (C, D, R1)]
        for f in faces:
            n = _face_n(f[0], f[1], f[2])
            uv = _roof_uv(f, n)
            rb.quad(*f, n, col, uv)
        for f in tris:
            n = _face_n(*f)
            rb.tri(*f, n, col, _roof_uv(f, n))
        # soffit under the eaves and a 0.2 m fascia round the edge
        fas = (232, 230, 224, 255)
        sof = (200, 196, 188, 255)
        ring = [A, B, C, D]
        for i in range(4):
            p, q = ring[i], ring[(i + 1) % 4]
            pd, qd = (p[0], p[1] - 0.2, p[2]), (q[0], q[1] - 0.2, q[2])
            n = _face_n(pd, qd, q)
            self.trim.quad(pd, qd, q, p, n, fas)
        inset = [W(*v) for v in ((rc[0], rc[1], H - 0.2), (rc[2], rc[1], H - 0.2), (rc[2], rc[3], H - 0.2),
                                 (rc[0], rc[3], H - 0.2))]
        ringd = [(v[0], v[1] - 0.2, v[2]) for v in ring]
        for i in range(4):
            p, q = ringd[i], ringd[(i + 1) % 4]
            pi_, qi = inset[i], inset[(i + 1) % 4]
            self.trim.quad(q, p, pi_, qi, (0.0, -1.0, 0.0), sof)

    def _flat(self, p, H, col, wall_col):
        """A flat (low) roof behind a parapet: the walls run on 0.5 m, capped, the roof deck inside."""
        n = len(p)
        rb = self.roof
        cap = (210, 206, 198, 255)
        for k in range(n):
            a, c = p[k], p[(k + 1) % n]
            L = math.dist(a, c)
            if L < 0.05:
                continue
            d = ((c[0] - a[0]) / L, (c[1] - a[1]) / L)
            out = (d[1], -d[0])
            nrm = _norm(X(out[0], 0, out[1]))
            self._panel(self.walls["facade_render"], a, d, 0, L, H, H + 0.5, nrm, wall_col)
            # inner face and cap
            ia, ic = (a[0] - out[0] * 0.2, a[1] - out[1] * 0.2), (c[0] - out[0] * 0.2, c[1] - out[1] * 0.2)
            self.trim.quad(X(ic[0], H, ic[1]), X(ia[0], H, ia[1]), X(ia[0], H + 0.5, ia[1]), X(ic[0], H + 0.5, ic[1]),
                           _norm(X(-out[0], 0, -out[1])), cap)
            self.trim.quad(X(a[0], H + 0.5, a[1]), X(c[0], H + 0.5, c[1]), X(ic[0], H + 0.5, ic[1]),
                           X(ia[0], H + 0.5, ia[1]), (0.0, 1.0, 0.0), cap)
        tri = _triangulate(p)
        for i, j, k in tri:
            f = (X(p[i][0], H + 0.05, p[i][1]), X(p[j][0], H + 0.05, p[j][1]), X(p[k][0], H + 0.05, p[k][1]))
            rb.tri(*f, (0.0, 1.0, 0.0), col, [(q[0], q[2]) for q in f])

    def _carport(self, p, y0, col):
        H = y0 + 2.4
        tri = _triangulate(p)
        for i, j, k in tri:
            f = (X(p[i][0], H, p[i][1]), X(p[j][0], H, p[j][1]), X(p[k][0], H, p[k][1]))
            self.roof.tri(*f, (0.0, 1.0, 0.0), col, [(q[0], q[2]) for q in f])
            self.trim.tri(f[2], f[1], f[0], (0.0, -1.0, 0.0), (150, 148, 142, 255))
        post = (220, 218, 212, 255)
        for q in p:
            _post(self.trim, q, y0, H, 0.05, post)


def _post(b, q, y0, y1, r, col):
    e, n = q
    c = [(e - r, n - r), (e + r, n - r), (e + r, n + r), (e - r, n + r)]
    for i in range(4):
        a, d = c[i], c[(i + 1) % 4]
        out = ((d[1] - a[1]), -(d[0] - a[0]))
        b.quad(X(a[0], y0, a[1]), X(d[0], y0, d[1]), X(d[0], y1, d[1]), X(a[0], y1, a[1]), _norm(X(out[0], 0, out[1])), col)


def _triangulate(p):
    """Ear clipping of a simple CCW polygon (east/north)."""
    idx = list(range(len(p)))
    out = []
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        for k in range(len(idx)):
            i, j, l = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = p[i], p[j], p[l]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-9:
                continue
            if any(_in_tri(p[m], a, b, c) for m in idx if m not in (i, j, l)):
                continue
            out.append((i, j, l))
            idx.pop(k)
            break
        else:
            break
    if len(idx) == 3:
        out.append(tuple(idx))
    return out


def _in_tri(q, a, b, c):
    def s(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    d1, d2, d3 = s(q, a, b), s(q, b, c), s(q, c, a)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))


def _roof_uv(f, n):
    """u along the face's eave (the ribs run down the slope), v down the slope; 1 unit a metre."""
    nn = np.array(n)
    down = np.array([0.0, -1.0, 0.0]) - nn * (-nn[1])
    L = np.linalg.norm(down)
    down = down / L if L > 1e-6 else np.array([1.0, 0.0, 0.0])
    side = np.cross(nn, down)
    return [(float(np.dot(q, side)), float(np.dot(q, down))) for q in f]


def _inside(poly, q):
    x, y = q
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c
