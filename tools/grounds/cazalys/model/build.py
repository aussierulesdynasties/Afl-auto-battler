# Cazaly's Stadium (Cairns, 2022-24), built from model/cazalys.json. Runs inside Blender: import build; build.build_all().
# Local frame: x east, y north, z up from the field, metres; bearings clockwise from north.
# The fence is the ellipse fitted to the OSM pitch outline (work/fence_osm.py): at Cazaly's the grass runs on past the fence.
# The west side is polar (sections every 0.5 deg along the fence): open terraces either side of the roofed grandstand.
# Everything else is a straight piece placed from the Esri tile / OSM outlines.
import bpy, math, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from mb import MB, TILE, earclip, ccw, rect, Frame, roof
D = json.load(open(os.path.join(HERE, 'cazalys.json')))
FE = json.load(open(os.path.join(SP, 'work', 'fence.json')))['ell']   # x0, y0, a1, a2, rot(deg)
OSM = json.load(open(os.path.join(SP, 'work', 'osm_xy.json')))
UP = np.array([0, 0, 1.0])


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


def pol(b, r):
    a = math.radians(b); return (r * math.sin(a), r * math.cos(a))


def fence_r(b):
    """radius from the origin to the fence ellipse along bearing b"""
    x0, y0, a1, a2, rot = FE; t = math.radians(rot); d = np.array(pol(b, 1.0))
    c, s = math.cos(t), math.sin(t)
    def tr(p): return np.array([c * p[0] + s * p[1], -s * p[0] + c * p[1]])
    p = tr(np.array([-x0, -y0])); q = tr(d)
    A = (q[0] / a1) ** 2 + (q[1] / a2) ** 2; B = 2 * (p[0] * q[0] / a1 ** 2 + p[1] * q[1] / a2 ** 2)
    C = (p[0] / a1) ** 2 + (p[1] / a2) ** 2 - 1
    return (-B + math.sqrt(B * B - 4 * A * C)) / (2 * A)


def interp(tab, b):
    t = np.array(tab, float); return [float(np.interp(b, t[:, 0], t[:, k])) for k in range(1, t.shape[1])]


def oriented(mb, q, m, out, uv=None):
    """add quad/poly q with its normal turned toward 'out' (a 3-vector)"""
    q = [np.array(p, float) for p in q]
    n = np.cross(q[1] - q[0], q[2] - q[0])
    if np.linalg.norm(n) < 1e-9 and len(q) > 3:
        n = np.cross(q[2] - q[0], q[3] - q[0])
    if np.dot(n, out) < 0:
        q = q[::-1]; uv = uv[::-1] if uv else None
    mb.face([tuple(p) for p in q], m, uv=uv)


def both(mb, q, m, uv=None):
    """a thin sheet seen from both sides (fabric, sails)"""
    mb.face([tuple(p) for p in q], m, uv=uv); mb.face([tuple(p) for p in q[::-1]], m, uv=uv[::-1] if uv else None)


def P3(b, r, z):
    x, y = pol(b, r); return (x, y, z)


def strip(mb, bs, prof, mats, rdir_out):
    """prof(b) -> list of (r, z); mats[k] = material of segment k->k+1"""
    for i in range(len(bs) - 1):
        A, B = prof(bs[i]), prof(bs[i + 1]); ba, bb = bs[i], bs[i + 1]
        for k in range(len(A) - 1):
            m = mats[k]
            if m is None: continue
            (r0, z0), (r1, z1) = A[k], A[k + 1]; (s0, w0), (s1, w1) = B[k], B[k + 1]
            dr, dz = r1 - r0, z1 - z0; L = math.hypot(dr, dz)
            if L < 1e-6 and math.hypot(s1 - s0, w1 - w0) < 1e-6: continue
            bm = math.radians(0.5 * (ba + bb)); rad = np.array([math.sin(bm), math.cos(bm), 0.0])
            out = rdir_out * (-dz * rad + np.array([0, 0, dr]))
            tu, tv = TILE.get(m, (1, 1)); rm = 0.5 * (r0 + r1) if L > 1e-6 else r0
            ua = math.radians(ba) * rm / tu; ub = math.radians(bb) * rm / tu
            uv = [(ua, 0), (ub, 0), (ub, L / tv), (ua, L / tv)]
            if dz < -1e-6: uv = [(ua, L / tv), (ub, L / tv), (ub, 0), (ua, 0)]
            oriented(mb, [P3(ba, r0, z0), P3(bb, s0, w0), P3(bb, s1, w1), P3(ba, r1, z1)], m, out, uv)


# ---------------- 3D seats ----------------
SEATS = {}        # colour -> MB of seat shells (proof renders only; the GLB instances them)
POSTS = None      # MB for the seat pedestals (exported in the GLB)
SEAT_XF = []      # (P, t, o, z, colour) per seat, for the instanced seat files
AISLES = []       # aisle-stair bearings (for the seat-height proof)
ROW = 0.8
RNG = np.random.default_rng(7)


def pick(pal):
    P = D['palettes'].get(pal)
    if P is None: return pal                     # a single colour
    names = [p[0] for p in P]; w = np.array([p[1] for p in P], float); return names[RNG.choice(len(names), p=w / w.sum())]


def stepped(p0, p1, n):
    (r0, z0), (r1, z1) = p0, p1; pts = [(r0, z0)]
    for k in range(n):
        zk = z0 + (z1 - z0) * k / (n - 1) if n > 1 else z0; rk = r0 + (r1 - r0) * (k + 1) / n
        if k > 0: pts.append((pts[-1][0], zk))
        pts.append((rk, zk))
    return pts


def terrace(prof, mats, segs):
    def p2(b):
        P = prof(b)
        for k, n in sorted(segs, reverse=True): P = P[:k] + stepped(P[k], P[k + 1], n) + P[k + 2:]
        return P
    M = list(mats)
    for k, n in sorted(segs, reverse=True): M = M[:k] + ['conc_tread'] * (2 * n - 1) + M[k + 1:]
    return p2, M


def nrows(prof, bs, k):
    P = prof(0.5 * (bs[0] + bs[-1])); return max(1, int(round((P[k + 1][0] - P[k][0]) / ROW)))


SHELL = [(-0.66, 0.40), (-0.58, 0.45), (-0.36, 0.44), (-0.25, 0.52), (-0.19, 0.70), (-0.16, 0.82), (-0.165, 0.87)]


def seat(P, t, o, z, col, shell=None, post=True):
    """one empty moulded plastic shell: pan and back one curved piece, dished across its width, a rolled top edge;
    P = xy of the back of its tread, t = along the row, o = away from the pitch, z = tread top. Centre pedestal."""
    tmpl = shell is not None
    if not tmpl:
        SEAT_XF.append((tuple(P), tuple(t), tuple(o), z, col))
        if col not in SEATS: SEATS[col] = MB('seats_' + col); SEATS[col].smooth = True
        shell = SEATS[col]
    P = np.array(P, float); t = np.array(t, float); o = np.array(o, float); hw = 0.22
    def X(a, d, h):
        q = P + t * a + o * d; return np.array((q[0], q[1], z + h))
    o3 = np.array([*o, 0.0])
    def V(i, j):
        d, h = SHELL[i]; w = min(1.0, max(0.0, (h - 0.45) / 0.2)); c = 1 - abs(j)
        return X(j * hw * (1 - 0.35 * max(0.0, (h - 0.74) / 0.13) ** 2), d + 0.07 * c * w, h - 0.05 * c * (1 - w) + 0.02 * c * (h > 0.86))
    for i in range(len(SHELL) - 1):
        dd, dh = SHELL[i + 1][0] - SHELL[i][0], SHELL[i + 1][1] - SHELL[i][1]
        out = -dh * o3 + dd * UP
        for j in (-1, 0):
            oriented(shell, [V(i, j), V(i, j + 1), V(i + 1, j + 1), V(i + 1, j)], 'seat', out,
                     [((j + 1) / 2, i / 6), ((j + 2) / 2, i / 6), ((j + 2) / 2, (i + 1) / 6), ((j + 1) / 2, (i + 1) / 6)])
    if tmpl or not post: return
    oriented(POSTS, [X(-0.04, -0.45, 0.0), X(0.04, -0.45, 0.0), X(0.04, -0.45, 0.38), X(-0.04, -0.45, 0.38)], 'steel_galv', -o3)


def seat_rows(bs, prof, k, n, pal, aisle=12.0, gap=1.1):
    """3D seats on the n treads of seat segment k of a polar stand: one every 0.5 m, an aisle stair every 12 m"""
    b0, b1 = bs[0], bs[-1]; rf = prof(0.5 * (b0 + b1))[k][0]
    ab = []; s = aisle / 2
    while True:
        b = b0 + math.degrees(s / rf)
        if b > b1 - math.degrees(2 / rf): break
        ab.append(b); s += aisle
    AISLES.extend(ab)
    for j in range(n):
        b = b0 + math.degrees(0.6 / rf)
        while True:
            P = prof(b); (r0, z0), (r1, z1) = P[k], P[k + 1]
            rr = r0 + (r1 - r0) * (j + 1) / n; zz = z0 + (z1 - z0) * j / (n - 1) if n > 1 else z0
            if b > b1 - math.degrees(0.6 / rr): break
            if all(abs(math.radians(b - a)) * rr > gap / 2 + 0.25 for a in ab):
                a = math.radians(b); o = (math.sin(a), math.cos(a)); t = (math.cos(a), -math.sin(a))
                seat(pol(b, rr), t, o, zz, pick(pal))
            b += math.degrees(0.5 / rr)
    return ab


def aisle_stairs(mb, ab, prof, k, n):
    """a light handrail up each aisle (Fosnez photo: white rails between the seat blocks)"""
    for b in ab:
        P = prof(b); (r0, z0), (r1, z1) = P[k], P[k + 1]
        mb.beam(P3(b, r0, z0 + 1.0), P3(b, r1, z1 + 1.0), 0.05, 0.05, 'steel_white')
        for f in (0.0, 0.5, 1.0):
            r = r0 + (r1 - r0) * f; z = z0 + (z1 - z0) * f
            mb.beam(P3(b, r, z), P3(b, r, z + 1.0), 0.05, 0.05, 'steel_white')


def endcap(mb, b, pts, m, sign):
    P = [(r, z) for r, z in pts]
    a = math.radians(b); tan = np.array([math.cos(a), -math.sin(a), 0.0]) * sign
    for tri in earclip(ccw2(P)):
        oriented(mb, [P3(b, r, z) for r, z in tri], m, tan,
                 uv=[(r / TILE.get(m, (1, 1))[0], z / TILE.get(m, (1, 1))[1]) for r, z in tri])


def ccw2(P):
    s = sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1] for i in range(len(P)))
    return P if s > 0 else P[::-1]


def brange(b0, b1):
    n = max(2, int(round((b1 - b0) / D.get('step', 0.5))) + 1); return list(np.linspace(b0, b1, n))


# ---------------- west side: open terraces and the roofed grandstand ----------------
def open_terrace(S, mb):
    bs = brange(S['b0'], S['b1']); zs0, zs1 = S['z_seat']
    def prof(b):
        rs0 = fence_r(b % 360) + S['front']; rb = interp(S['back'], b)[0]
        return [(rs0, 0.0), (rs0, zs0), (rb - 0.4, zs1), (rb - 0.4, zs1 + 1.1), (rb, zs1 + 1.1), (rb, 0.0)]
    n = nrows(prof, bs, 1); tp, tm = terrace(prof, ['conc_wall', 'seat', 'conc_wall', 'conc_wall', 'conc_wall'], [(1, n)])
    strip(mb, bs, tp, tm, -1); ab = seat_rows(bs, prof, 1, n, S['pal']); aisle_stairs(mb, ab, prof, 1, n)
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        endcap(mb, b, tp(b), 'conc_wall', sg)


def grandstand(G, mb, mr):
    """lower terrace from the fence, a walkway, the upper tier under a flat white cantilever roof, the glazed corporate
    level at the back of the upper tier, the concourse building behind; four pyramid masts on the roof (Fosnez photo)"""
    bs = brange(G['b0'], G['b1']); zl0, zl1 = G['z_lower']; zu0, zu1 = G['z_upper']; zg = G['z_glaze']
    def geo(b):
        rs0 = fence_r(b % 360) + G['front']; ru0 = interp(G['upper_front'], b)[0]; ru1 = interp(G['upper_back'], b)[0]
        rr = interp(G['rear'], b)[0]; return rs0, ru0, ru1, rr
    def prof(b):
        rs0, ru0, ru1, rr = geo(b)
        return [(rs0, 0.0), (rs0, zl0), (ru0 - 1.6, zl1), (ru0, zl1), (ru0, zu0), (ru1, zu1), (ru1, zg), (rr, zg), (rr, 0.0)]
    n1, n4 = nrows(prof, bs, 1), nrows(prof, bs, 4)
    tp, tm = terrace(prof, ['conc_wall', 'seat', 'conc_tread', 'conc_wall', 'seat', 'gstand_back', 'roof_grey', 'clad_grey'],
                     [(1, n1), (4, n4)])
    strip(mb, bs, tp, tm, -1)
    for k, n in ((1, n1), (4, n4)):
        ab = seat_rows(bs, prof, k, n, G['pal']); aisle_stairs(mb, ab, prof, k, n)
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        endcap(mb, b, tp(b), 'conc_wall', sg)
    # roof: deck from the upper-tier front (less the overhang) to the rear, rising 1 m; fascia 1.2 m deep all round
    zr0, zr1 = G['z_roof']; th = 0.4
    def deck(b):
        rs0, ru0, ru1, rr = geo(b); return ru0 - G['roof_over'], rr + 0.4
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]; (ria, roa), (rib, rob) = deck(ba), deck(bb)
        tu, tv = TILE['roof_white']; rm = 0.5 * (ria + roa); ua, ub = math.radians(ba) * rm / tu, math.radians(bb) * rm / tu
        oriented(mr, [P3(ba, ria, zr0), P3(bb, rib, zr0), P3(bb, rob, zr1), P3(ba, roa, zr1)], 'roof_white', UP,
                 [(ua, ria / tv), (ub, rib / tv), (ub, rob / tv), (ua, roa / tv)])
        oriented(mr, [P3(ba, ria, zr0 - th), P3(bb, rib, zr0 - th), P3(bb, rob, zr1 - th), P3(ba, roa, zr1 - th)], 'roof_soffit', -UP,
                 [(ua, ria / tv), (ub, rib / tv), (ub, rob / tv), (ua, roa / tv)])
        bm = math.radians(0.5 * (ba + bb)); rad = np.array([math.sin(bm), math.cos(bm), 0.0])
        oriented(mr, [P3(ba, ria, zr0 - 1.2), P3(bb, rib, zr0 - 1.2), P3(bb, rib, zr0 + 0.05), P3(ba, ria, zr0 + 0.05)], 'fascia', -rad)
        oriented(mr, [P3(ba, ria, zr0 - 1.2), P3(bb, rib, zr0 - 1.2), P3(bb, rib - 0.3, zr0 - th), P3(ba, ria - 0.3, zr0 - th)], 'fascia', -UP)
        oriented(mr, [P3(ba, roa, zr1 - 0.8), P3(bb, rob, zr1 - 0.8), P3(bb, rob, zr1), P3(ba, roa, zr1)], 'fascia', rad)
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        ri, ro = deck(b); a = math.radians(b); tan = np.array([math.cos(a), -math.sin(a), 0.0]) * sg
        oriented(mr, [P3(b, ri, zr0 - 1.2), P3(b, ro, zr1 - 0.8), P3(b, ro, zr1), P3(b, ri, zr0 + 0.05)], 'fascia', tan)
    # front columns on the walkway every ~6 deg, up to the roof soffit
    b = bs[0] + 1.0
    while b < bs[-1] - 0.5:
        rs0, ru0, ru1, rr = geo(b); mr.beam(P3(b, ru0 - 0.4, zl1), P3(b, ru0 - 0.4, zr0 - th), 0.3, 0.3, 'steel_white'); b += 6.6
    # pyramid masts: four legs from the roof to an apex mast_h above, two stays from the apex to the front fascia
    for M in G['masts']:
        b = M['b']; rs0, ru0, ru1, rr = geo(b); rc = ru0 + 9.0; zc = zr0 + (zr1 - zr0) * (rc - deck(b)[0]) / (deck(b)[1] - deck(b)[0])
        apex = P3(b, rc, zc + G['mast_h']); db = math.degrees(4.0 / rc)
        for bb_, rr_ in ((b - db, rc - 4), (b + db, rc - 4), (b - db, rc + 4), (b + db, rc + 4)):
            mr.beam(P3(bb_, rr_, zc), apex, 0.28, 0.28, 'steel_white')
        mr.beam(P3(b - db, rc - 4, zc + 0.2), P3(b + db, rc - 4, zc + 0.2), 0.2, 0.2, 'steel_white')
        mr.beam(P3(b - db, rc + 4, zc + 0.2), P3(b + db, rc + 4, zc + 0.2), 0.2, 0.2, 'steel_white')
        dbf = math.degrees(7.0 / ru0); rf_ = deck(b)[0] + 0.3
        for bb_ in (b - dbf, b + dbf):
            mr.beam(apex, P3(bb_, rf_, zr0 + 0.05), 0.08, 0.08, 'steel_galv')


# ---------------- straight pieces ----------------
def axes(poly):
    """long axis u, short axis v (pointing to the pitch), centre, length, width of a thin OSM outline"""
    P = np.array(poly, float)
    if np.allclose(P[0], P[-1]): P = P[:-1]
    best = None
    for i in range(len(P)):
        e = P[(i + 1) % len(P)] - P[i]
        if best is None or np.linalg.norm(e) > np.linalg.norm(best): best = e
    u = best / np.linalg.norm(best); v = np.array([-u[1], u[0]])
    pu, pv = P @ u, P @ v; c = u * (pu.min() + pu.max()) / 2 + v * (pv.min() + pv.max()) / 2
    if np.dot(v, -c) < 0: v = -v
    return u, v, c, pu.max() - pu.min(), pv.max() - pv.min()


def building(B, mb):
    P = [tuple(p) for p in np.array(OSM[B['osm']], float)]
    if np.allclose(P[0], P[-1]): P = P[:-1]
    if B.get('replace'):   # satellite-traced edge replacing a run of OSM points (first..last, inclusive)
        f, l, R_ = B['replace']; i = min(range(len(P)), key=lambda k: math.dist(P[k], f)); j = min(range(len(P)), key=lambda k: math.dist(P[k], l))
        P = P[:i] + [tuple(q) for q in R_] + P[j + 1:]
    if B.get('setback'):   # the club: pitch-front points pushed back; the strip in front takes the sails and a terrace
        P = [(x, y - B['setback']) if y > -99.5 else (x, y) for x, y in P]
    if B.get('low'):   # Street View pano wvECTX (Feb 2025): the club's SW corner past the west box is a low white wing
        X, Y, hl, wl = B['low']; w = clip(P, 0, X, -1)   # wl: the low wing's wall (photo: plain white render, no windows)
        parts = [(clip(P, 0, X, 1), B['h'], B['wall']), (clip(w, 1, Y, 1), B['h'], B['wall']), (clip(w, 1, Y, -1), hl, wl)]
    else: parts = [(P, B['h'], B['wall'])]
    for P, h, wm in parts:
        if len(P) >= 3: prism_cap(mb, dict(B, wall=wm), P, h)


def clip(P, ax, v, sg):   # Sutherland-Hodgman: keep the side where sg*(p[ax]-v) >= 0
    out = []
    for i in range(len(P)):
        p, q = P[i], P[(i + 1) % len(P)]; fp, fq = sg * (p[ax] - v), sg * (q[ax] - v)
        if fp >= 0: out.append(p)
        if fp * fq < 0: t = fp / (fp - fq); out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def prism_cap(mb, B, P, h):
    B = dict(B, h=h)
    mb.prism(P, 0.0, B['h'], B['wall'], top=B['roof'])
    poly = ccw(P)   # parapet: a 0.5 m white cap all round the roof edge
    for i in range(len(poly)):
        p, q = np.array(poly[i]), np.array(poly[(i + 1) % len(poly)]); n = np.array([q[1] - p[1], p[0] - q[0]]); n /= np.linalg.norm(n)
        a, b_ = p - n * 0.25, q - n * 0.25
        oriented(mb, [(*a, B['h']), (*b_, B['h']), (*b_, B['h'] + 0.5), (*a, B['h'] + 0.5)], 'fascia', np.array([*(-n), 0]))
        oriented(mb, [(*p, B['h'] + 0.5), (*q, B['h'] + 0.5), (*b_, B['h'] + 0.5), (*a, B['h'] + 0.5)], 'paint_white', UP)
        oriented(mb, [(*p, B['h']), (*q, B['h']), (*q, B['h'] + 0.5), (*p, B['h'] + 0.5)], 'fascia', np.array([*n, 0]))


def front_path(F, smooth=False):
    """arc-length frame along a facade polyline (CCW building, so outward is to the right of travel)"""
    F = np.array(F, float)
    if smooth and len(F) > 2:   # Catmull-Rom through the traced points, ~1 m steps: the glazing curves round instead of kinking
        G = np.vstack([2 * F[0] - F[1], F, 2 * F[-1] - F[-2]]); out = []
        for i in range(1, len(G) - 2):
            p0, p1, p2, p3 = G[i - 1:i + 3]; n_ = max(2, int(np.linalg.norm(p2 - p1)))
            for t in np.linspace(0, 1, n_, endpoint=False):
                out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        F = np.array(out + [F[-1]])
    seg = np.diff(F, axis=0); Ls = np.linalg.norm(seg, axis=1); cum = np.concatenate([[0], np.cumsum(Ls)])
    def at(s):
        i = int(np.clip(np.searchsorted(cum, s, 'right') - 1, 0, len(Ls) - 1)); d = seg[i] / Ls[i]
        return F[i] + d * (s - cum[i]), d, np.array([d[1], -d[0]])
    def Q(s, o, z):
        p, d, n = at(s); return (*(p + n * o), z)
    def runs(s0, s1):   # split [s0, s1] at the polyline corners
        cuts = [s0] + [c for c in cum[1:-1] if s0 < c < s1] + [s1]; return list(zip(cuts[:-1], cuts[1:]))
    return at, Q, runs, cum[-1]


def club_front(C, mb):
    """club entrance (Commons photo 12, Kerry Raymond 2018 photo, Andrew Watson 2013 set): on the club's east face by the
    Mulgrave Rd corner. A flat white entrance canopy on three cream posts (outer two rise through it), the tilted brown
    'Cazalys' sign on the canopy, a covered walkway along the grey shopfront with ClubsLink poster bays, a sloped glazed
    upper floor with cream mullions curving round to the north-east, yellow bollards on the kerb, a concrete drive and a
    palm garden island"""
    at, Q, runs, L = front_path(C['front'], True); at0, Q0, runs0 = at, Q, runs
    ch = front_path(C['chamfer']); cat, cQ, cruns, cL = ch; GF, AWz, AWt, AWo = C['gf'], C['aw_z'], C['aw_t'], C['aw_o']
    Hg = C['glaze_top']; c0, c1, co, cz, ct = C['canopy']
    def piece(s0, s1, o, z0, z1, m, tu=None):
        for a, b in runs(s0, s1):
            _, _, n = at(0.5 * (a + b))
            uv = None if tu is None else [(a / tu[0], z0 / tu[1]), (b / tu[0], z0 / tu[1]), (b / tu[0], z1 / tu[1]), (a / tu[0], z1 / tu[1])]
            oriented(mb, [Q(a, o, z0), Q(b, o, z0), Q(b, o, z1), Q(a, o, z1)], m, np.array([*n, 0]), uv)
    def slab(s0, s1, o0, o1, z0, z1, top, side, fr=None):
        at, Q, runs = fr or (at0, Q0, runs0)
        for a, b in runs(s0, s1):
            _, _, n = at(0.5 * (a + b))
            q = [Q(a, o0, z0), Q(b, o0, z0), Q(b, o1, z0), Q(a, o1, z0)]
            oriented(mb, q, 'soffit_white', np.array([0, 0, -1.0]), [(p[0] / 3.0, p[1] / 3.0) for p in q]); oriented(mb, [(x, y, z1) for x, y, _ in q], top, UP)
            oriented(mb, [Q(a, o1, z0), Q(b, o1, z0), Q(b, o1, z1), Q(a, o1, z1)], side, np.array([*n, 0]))
        for s_, sg in ((s0, -1), (s1, 1)):
            _, d, _ = at(s_); oriented(mb, [Q(s_, o0, z0), Q(s_, o1, z0), Q(s_, o1, z1), Q(s_, o0, z1)], side, np.array([*(d * sg), 0]))
    # ground floor: grey shopfront the whole way
    piece(0.0, L, 0.06, 0.0, GF, 'clubw_gf', (6.0, 4.2))
    mb.prism([tuple(q) for q in C['lobby']['poly']], 0.0, C['lobby']['h'], 'club', top='roof_white')   # the low white block at the corner (photo 12: sky above the canopy)
    # upper floor right of the canopy: glazing leaning out (foot 1.2 m in, head 0.4 m out), cream mullions, white head band
    g0 = 0.0
    for a, b in runs(g0, L):
        _, _, n = at(0.5 * (a + b))
        oriented(mb, [Q(a, -1.2, AWz + AWt), Q(b, -1.2, AWz + AWt), Q(b, 0.4, Hg), Q(a, 0.4, Hg)], 'clubw_glass', np.array([*n, 0.4]),
                 [(a / 3.0, 0), (b / 3.0, 0), (b / 3.0, 1), (a / 3.0, 1)])
        oriented(mb, [Q(a, 0.4, Hg), Q(b, 0.4, Hg), Q(b, 0.4, Hg + 0.4), Q(a, 0.4, Hg + 0.4)], 'paint_white', np.array([*n, 0]))
    for s_ in np.arange(g0 + 0.1, L, C['mullion']):
        mb.beam(Q(s_, -1.0, AWz + AWt), Q(s_, 0.5, Hg), 0.14, 0.14, 'paint_cream')
    _, d1, _ = at(L)
    oriented(mb, [Q(L, -1.2, AWz + AWt), Q(L, 0.4, AWz + AWt), Q(L, 0.4, Hg + 0.4), Q(L, -1.2, Hg + 0.4)], 'paint_white', np.array([*d1, 0]))
    # covered walkway along the shopfront: flat white soffit, thin white fascia
    slab(0.0, L, 0.0, AWo, AWz, AWz + AWt, 'roof_white', 'paint_white')
    # entrance canopy: flat wedge off the cut-off corner (lobby doors face south-east), a touch higher than the walkway
    # photo 12: a flat wedge, deep at the right (south) end and tapering to a point at the left; polygon in chamfer (s, o)
    W_ = ccw([tuple(cQ(s_, o_, 0)[:2]) for s_, o_ in C['canopy_poly']])
    for t in earclip(W_):
        oriented(mb, [(x, y, cz) for x, y in t], 'soffit_white', np.array([0, 0, -1.0]), [(x / 3.0, y / 3.0) for x, y in t])
        oriented(mb, [(x, y, cz + ct) for x, y in t], 'roof_white', UP)
    for i in range(len(W_)):
        (x0, y0), (x1, y1) = W_[i], W_[(i + 1) % len(W_)]; nn = np.array([y1 - y0, -(x1 - x0), 0]); nn /= np.linalg.norm(nn) + 1e-9
        oriented(mb, [(x0, y0, cz), (x1, y1, cz), (x1, y1, cz + ct), (x0, y0, cz + ct)], 'paint_white', nn)
    for s_, top in C['posts']:
        mb.beam(cQ(s_, co - 0.7, 0), cQ(s_ - 0.04 * top, co - 0.7, top), 0.32, 0.32, 'paint_cream', tube=True)   # photo 12: every post leans a little to the south-west
    # the tilted sign on the canopy: inverted trapezoid, tipped back, turned toward the Mulgrave Rd approach
    sc, so, sw0, sw1, sh, tb, turn = C['sign']; z0 = cz + ct; z1 = z0 + sh
    p0, d, n = cat(sc); ts = math.radians(turn); ds = d * math.cos(ts) + n * math.sin(ts); ns = n * math.cos(ts) - d * math.sin(ts)
    cc = p0 + n * so; F_ = lambda a, b, z: (*(cc + ds * a + ns * b), z)
    fr = [F_(-sw0 / 2, 0, z0), F_(sw0 / 2, 0, z0), F_(sw1 / 2, -tb, z1), F_(-sw1 / 2, -tb, z1)]
    e = (sw1 - sw0) / 2 / sw1
    oriented(mb, fr, 'sign_clubw', np.array([*ns, 0]), [(e, 0), (1 - e, 0), (1, 1), (0, 1)])
    bk = [tuple(np.array(p) - np.array([*ns, 0]) * 0.25) for p in fr]
    oriented(mb, bk, 'paint_brown', np.array([*(-ns), 0]))
    for i in range(4):
        j = (i + 1) % 4; mb.face([fr[i], fr[j], bk[j], bk[i]], 'paint_brown'); mb.face([fr[i], bk[i], bk[j], fr[j]], 'paint_brown')
    # poster bays: ClubsLink bays of three posters, a grey pilaster before each bay
    for s_ in C['bays']:
        for a, b in runs(s_, s_ + 3.3):
            _, _, n = at(0.5 * (a + b))
            oriented(mb, [Q(a, 0.09, 0.4), Q(b, 0.09, 0.4), Q(b, 0.09, 3.4), Q(a, 0.09, 3.4)], 'posters_w', np.array([*n, 0]),
                     [((a - s_) / 3.3, 0), ((b - s_) / 3.3, 0), ((b - s_) / 3.3, 1), ((a - s_) / 3.3, 1)])
        p, d, n = at(s_ - 0.6); mb.box(tuple(p + n * 0.15), 0.5, 0.3, GF, math.degrees(math.atan2(d[1], d[0])), 'paint_grey')
    # footpath under the walkway and canopy: raised concrete, kerb at the drive edge, yellow bollards along the kerb
    for a, b in runs(0.0, L):
        q = [Q(a, 0.06, 0.15), Q(b, 0.06, 0.15), Q(b, AWo + 0.3, 0.15), Q(a, AWo + 0.3, 0.15)]
        oriented(mb, q, 'paving', UP, [(p[0] / 2.4, p[1] / 2.4) for p in q])
    piece(0.0, L, AWo + 0.3, 0.0, 0.15, 'conc_kerb')
    do = C.get('door_o', 0.08); oriented(mb, [cQ(0, do, 0), cQ(cL, do, 0), cQ(cL, do, GF), cQ(0, do, GF)], 'clubw_gf', np.array([*cat(1)[2], 0]), [(0, 0), (cL / 6.0, 0), (cL / 6.0, 1), (0, 1)])   # entrance doors under the canopy
    q = [cQ(c0, 0.06, 0.15), cQ(c1, 0.06, 0.15), cQ(c1, co + 0.3, 0.15), cQ(c0, co + 0.3, 0.15)]   # paving under the canopy
    oriented(mb, q, 'paving', UP, [(p[0] / 2.4, p[1] / 2.4) for p in q])
    for a, b in cruns(c0, c1):
        _, _, n = cat(0.5 * (a + b)); oriented(mb, [cQ(a, co + 0.3, 0), cQ(b, co + 0.3, 0), cQ(b, co + 0.3, 0.15), cQ(a, co + 0.3, 0.15)], 'conc_kerb', np.array([*n, 0]))
    for s_ in C['bollards']:
        mb.cyl(Q(s_, AWo, 0.15)[:2], 0.09, 0.15, 1.15, 'bollard', n=10, top='bollard')
    # drive, garden island and car park sit outside the stadium fence: background scene (stadium-only rule)



def south_front(S, mb):
    """club's Mulgrave Rd (south) face, from Street View pano dxiQEa8tBLbzx8OQGPV1oA (Feb 2025): glazed ground floor under a
    continuous white awning on cream posts, grey upper wall with glazing runs and white struts leaning west, and the white
    skillion box at the east end beside the entrance. Distances 'a' are metres west of the SE corner"""
    at, Q, runs, L = front_path(S['path']); A = lambda a: L - a
    GF, AWo = S['gf'], S['aw_o']; E = S['eave']
    def quad(a0, a1, o, z0, z1, m, tu=None):
        for s0, s1 in runs(A(a1), A(a0)):
            _, _, n = at(0.5 * (s0 + s1))
            uv = None if tu is None else [(s0 / tu[0], z0 / tu[1]), (s1 / tu[0], z0 / tu[1]), (s1 / tu[0], z1 / tu[1]), (s0 / tu[0], z1 / tu[1])]
            oriented(mb, [Q(s0, o, z0), Q(s1, o, z0), Q(s1, o, z1), Q(s0, o, z1)], m, np.array([*n, 0]), uv)
    def decal(a0, a1, o, z0, z1, m):   # one texture stretched over [a0, a1], left edge at the west end
        sw, se = A(a1), A(a0)
        for s0, s1 in runs(sw, se):
            _, _, n = at(0.5 * (s0 + s1)); u0, u1 = (s0 - sw) / (se - sw), (s1 - sw) / (se - sw)
            oriented(mb, [Q(s0, o, z0), Q(s1, o, z0), Q(s1, o, z1), Q(s0, o, z1)], m, np.array([*n, 0]), [(u0, 0), (u1, 0), (u1, 1), (u0, 1)])
    for k, m in (('lettering', 'sign_cafl'), ('logo', 'sign_clublogo')):   # Street View zoomed: gold caps on the glass, club logo on the wall
        a0, a1, o, z0, z1 = S[k]; decal(a0, a1, o, z0, z1, m)
    quad(0.0, L, 0.06, 0.0, GF, 'clubw_glass', (1.5, GF))   # Street View: dark glass shopfront the full height, mullions ~1.5 m
    W_ = S['west']; r0, r1 = W_['recess']
    quad(0.0, r0, 0.04, GF, E, 'paint_grey'); quad(r1, L, 0.04, GF, E, 'paint_grey')
    # west wing (pano mIsaus, Feb 2025): recessed upper bay, red-brown wall behind cream mullions
    rd = W_['recess_d']; quad(r0, r1, -rd, GF, E, 'paint_rust')
    for a in (r0, r1):
        p, d, n = at(A(a)); oriented(mb, [(*(p + n * 0.04), GF), (*(p - n * rd), GF), (*(p - n * rd), E), (*(p + n * 0.04), E)], 'paint_grey', np.array([*d, 0]))
    for a in np.arange(r0 + W_['mull'], r1 - 0.2, W_['mull']):
        mb.beam(Q(A(a), -rd + 0.1, GF), Q(A(a), -rd + 0.1, E), 0.14, 0.14, 'paint_cream')
    for a0, a1 in W_['upper_glass']:
        quad(a0, a1, 0.08, GF + 0.6, E - 0.35, 'clubw_glass', (3.0, E - GF - 0.95))
    a0, a1, o, z0, z1 = W_['logo']; decal(a0, a1, o, z0, z1, 'sign_clublogo2')
    # west end: white glazed box under a raised white skillion roof
    c0, c1, zr0, zr1, cd = W_['box']; quad(c0, min(c1, L), 0.1, GF + 0.3, GF + 2.0, 'clubw_glass', (3.0, 1.7)); quad(c0, min(c1, L), 0.1, GF + 2.0, zr0 - 0.6, 'render_white')
    zs2 = lambda s_: zr1 + (zr0 - zr1) * (s_ - A(min(c1, L))) / (min(c1, L) - c0)
    for s0, s1 in runs(A(min(c1, L)), A(c0)):   # follows the wrap round the SW corner (aerial)
        bo = W_['box_o']; q = [Q(s0, bo, zs2(s0)), Q(s1, bo, zs2(s1)), Q(s1, -cd, zs2(s1)), Q(s0, -cd, zs2(s0))]
        oriented(mb, [(x, y, z + 0.3) for x, y, z in q], 'roof_white', UP); oriented(mb, q, 'soffit_white', np.array([0, 0, -1.0]))
        _, _, n = at(0.5 * (s0 + s1))
        oriented(mb, [q[0], q[1], (*q[1][:2], q[1][2] + 0.3), (*q[0][:2], q[0][2] + 0.3)], 'render_white', np.array([*n, 0]))
        oriented(mb, [Q(s0, 0.1, zr0 - 0.6), Q(s1, 0.1, zr0 - 0.6), Q(s1, 0.1, zs2(s1)), Q(s0, 0.1, zs2(s0))], 'render_white', np.array([*n, 0]))
    for af, ah in W_.get('fan', []):   # wvEC (Feb 2025): nine cream raking struts fanned on the box's white wall, counted one by one
        af, ah = min(af, L - 0.2), min(ah, L - 0.2)
        mb.beam(Q(A(af), 0.3, GF + 2.3), Q(A(ah), 0.3, zs2(A(ah)) - 0.05), 0.18, 0.18, 'paint_cream')
    for a0, a1 in S['upper_glass']:
        quad(a0, a1, 0.08, GF + 0.6, E - 0.35, 'clubw_glass', (3.0, E - GF - 0.95))
    for s0, s1 in runs(0.0, L):   # awning: flat white soffit, thin white fascia; stepped up west of the recess
        _, _, n = at(0.5 * (s0 + s1)); z0 = GF + (S['west']['aw_dz'] if 0.5 * (s0 + s1) < A(S['west']['recess'][0]) else 0.0); z1 = z0 + 0.3
        q = [Q(s0, 0, z0), Q(s1, 0, z0), Q(s1, AWo, z0), Q(s0, AWo, z0)]
        oriented(mb, q, 'soffit_white', np.array([0, 0, -1.0]), [(p[0] / 3.0, p[1] / 3.0) for p in q]); oriented(mb, [(x, y, z1) for x, y, _ in q], 'roof_white', UP)
        oriented(mb, [Q(s0, AWo, z0), Q(s1, AWo, z0), Q(s1, AWo, z1), Q(s0, AWo, z1)], 'render_white', np.array([*n, 0]))
        q = [Q(s0, 0.06, 0.15), Q(s1, 0.06, 0.15), Q(s1, AWo + 0.3, 0.15), Q(s0, AWo + 0.3, 0.15)]
        oriented(mb, q, 'paving', UP, [(p[0] / 2.4, p[1] / 2.4) for p in q])
        oriented(mb, [Q(s0, AWo + 0.3, 0), Q(s1, AWo + 0.3, 0), Q(s1, AWo + 0.3, 0.15), Q(s0, AWo + 0.3, 0.15)], 'conc_kerb', np.array([*n, 0]))
    for a in S['posts']:
        mb.beam(Q(A(a), AWo - 0.3, 0.15), Q(A(a), AWo - 0.3, GF), 0.2, 0.2, 'paint_cream', tube=True)
    eo = S['eave_o']
    for a in S['struts']:   # cream raking struts: foot on the wall at the awning, head out under the eave edge (pano solve)
        mb.beam(Q(A(a), 0.12, GF + 0.3), Q(A(a + S['strut_lean']), eo - 0.15, E), 0.16, 0.16, 'paint_cream')
    for s0, s1 in runs(A(W_['box'][0]), L):   # eave: roof edge overhang (none over the west box: wvEC photo)
        _, _, n = at(0.5 * (s0 + s1))
        oriented(mb, [Q(s0, 0, E), Q(s1, 0, E), Q(s1, eo, E), Q(s0, eo, E)], 'soffit_white', np.array([0, 0, -1.0]))
        oriented(mb, [Q(s0, eo, E), Q(s1, eo, E), Q(s1, eo, E + 0.35), Q(s0, eo, E + 0.35)], 'paint_white', np.array([*n, 0]))
    # the white skillion box at the east end: glass band over the awning, white upper wall, roof rising to the east
    b0, b1, zw, ze, bd = S['box']; zg = S['box_glaze']; ow, oe = S['box_overhang']   # photo-solved: glass to 7.4, roof past both ends
    quad(b0, b1, 0.1, GF + 0.3, zg, 'clubw_glass', (3.0, zg - GF))
    zs = lambda s: zw + (ze - zw) * (s - A(b1)) / (b1 - b0)
    for s0, s1 in runs(A(b1), A(b0)):
        _, _, n = at(0.5 * (s0 + s1))
        oriented(mb, [Q(s0, 0.1, zg), Q(s1, 0.1, zg), Q(s1, 0.1, zs(s1)), Q(s0, 0.1, zs(s0))], 'paint_white', np.array([*n, 0]))
    for s0, s1 in [(A(b1 + ow), A(b0 - oe))]:
        _, _, n = at(0.5 * (s0 + s1))
        q = [Q(s0, 1.0, zs(s0)), Q(s1, 1.0, zs(s1)), Q(s1, -bd, zs(s1)), Q(s0, -bd, zs(s0))]
        oriented(mb, [(x, y, z + 0.3) for x, y, z in q], 'roof_white', UP); oriented(mb, q, 'soffit_white', np.array([0, 0, -1.0]))
        oriented(mb, [Q(s0, 1.0, zs(s0)), Q(s1, 1.0, zs(s1)), Q(s1, 1.0, zs(s1) + 0.3), Q(s0, 1.0, zs(s0) + 0.3)], 'paint_white', np.array([*n, 0]))
    for a, z in ((b1, zw), (b0, ze)):
        p, d, n = at(A(a)); sg = 1 if a == b0 else -1
        oriented(mb, [(*(p + n * 0.1), E), (*(p - n * bd), E), (*(p - n * bd), z), (*(p + n * 0.1), z)], 'paint_white', np.array([*(d * sg), 0]))


def shelter(S, mb):
    """covered player/coach bench along the fence (OSM strip): back wall, side walls, skillion roof, two rows of seats"""
    u, v, c, L, W = axes(OSM[S['osm']]); h = S['h']; W = max(W, 2.6)
    Q = lambda a, d, z: (*(c + u * a - v * d), z)          # d = distance back from the pitch-side edge centre line
    f = W / 2
    oriented(mb, [Q(-L / 2, f, 0), Q(L / 2, f, 0), Q(L / 2, f, h), Q(-L / 2, f, h)], 'clad_grey', np.array([*(-v), 0]))
    oriented(mb, [Q(-L / 2, f - 0.15, 0), Q(L / 2, f - 0.15, 0), Q(L / 2, f - 0.15, h), Q(-L / 2, f - 0.15, h)], 'clad_grey', np.array([*v, 0]))
    for s_ in (-1, 1):
        oriented(mb, [Q(s_ * L / 2, -f, 0), Q(s_ * L / 2, f, 0), Q(s_ * L / 2, f, h), Q(s_ * L / 2, -f, h - 0.3)], 'clad_grey', np.array([*(u * s_), 0]))
        oriented(mb, [Q(s_ * L / 2, -f, 0), Q(s_ * L / 2, f, 0), Q(s_ * L / 2, f, h), Q(s_ * L / 2, -f, h - 0.3)], 'clad_grey', np.array([*(-u * s_), 0]))
    o = 0.5
    T = [Q(-L / 2 - 0.2, -f - o, h - 0.35), Q(L / 2 + 0.2, -f - o, h - 0.35), Q(L / 2 + 0.2, f + 0.2, h), Q(-L / 2 - 0.2, f + 0.2, h)]
    oriented(mb, T, 'roof_grey', UP); oriented(mb, [(x, y, z - 0.15) for x, y, z in T], 'roof_soffit', -UP)
    oriented(mb, [T[0], T[1], (T[1][0], T[1][1], T[1][2] - 0.15), (T[0][0], T[0][1], T[0][2] - 0.15)], 'fascia', np.array([*v, 0]))
    oriented(mb, [Q(-L / 2, -f, 0.02), Q(L / 2, -f, 0.02), Q(L / 2, f, 0.02), Q(-L / 2, f, 0.02)], 'conc_tread', UP)
    a = -L / 2 + 0.6
    while a < L / 2 - 0.4:
        mb.beam(Q(a, -f + 0.1, 0), Q(a, -f + 0.1, h - 0.4), 0.08, 0.08, 'steel_white') if abs((a + L / 2) % 4.0) < 0.5 else None
        for r in range(S['rows']):
            d = f - 0.3 - r * 0.85; z = 0.0 if r == S['rows'] - 1 else 0.35 * (S['rows'] - 1 - r)
            if r < S['rows'] - 1:
                mb.box(tuple(c + u * a - v * (d - 0.4)), 0.5, 0.85, z, math.degrees(math.atan2(u[1], u[0])), 'conc_tread')
            seat(tuple(c + u * a - v * d), tuple(u), tuple(-v), z, pick(S['pal']))
        a += 0.5


def tent(T, mb):
    """white marquee: gable (walled, NW function tents) or tensile peaks (open, posts at the bay corners)"""
    F = Frame(T); L, W = T['L'], T['W']
    if T['kind'] == 'gable':
        P = [F.P(-L / 2, -W / 2), F.P(L / 2, -W / 2), F.P(L / 2, W / 2), F.P(-L / 2, W / 2)]
        mb.prism(P, 0.0, T['eave'], 'tent')
        roof(mb, F, -L / 2, L / 2, -W / 2, W / 2, 'gable', T['eave'], T['ridge'], 'tent', over=0.2, gm='tent', soffit='tent', fascia='paint_white')
        return
    nu, nv = T['nu'], T['nv']; du, dv = L / nu, W / nv; e, r = T['eave'], T['ridge']
    def S(u, v):   # fabric height: peaks at the bay centres, catenary dips along the edges between the corner posts
        iu = min(nu - 1, int((u + L / 2) / du)); iv = min(nv - 1, int((v + W / 2) / dv))
        cu = -L / 2 + (iu + 0.5) * du; cv = -W / 2 + (iv + 0.5) * dv
        q = max(abs(u - cu) / (du / 2), abs(v - cv) / (dv / 2)); q = min(q, 1.0)
        eu = abs(abs(u - cu) - du / 2) < 1e-6; ev = abs(abs(v - cv) - dv / 2) < 1e-6
        z = e + (r - e) * (1 - q) ** 1.6
        if q >= 1.0 - 1e-6:   # on a bay edge: sag between corners
            s = (v - (cv - dv / 2)) / dv if eu else (u - (cu - du / 2)) / du
            z = e - 0.35 * math.sin(math.pi * s)
        return z
    k = 8; tu, tv = TILE['tent']
    for iu in range(nu):
        for iv in range(nv):
            u0, v0 = -L / 2 + iu * du, -W / 2 + iv * dv
            for a in range(k):
                for b_ in range(k):
                    us = [u0 + du * (a + x) / k for x in (0, 1, 1, 0)]; vs = [v0 + dv * (b_ + y) / k for y in (0, 0, 1, 1)]
                    q = [(*F.P(uu, vv), S(uu, vv)) for uu, vv in zip(us, vs)]
                    both(mb, q, 'tent', [(uu / tu, vv / tv) for uu, vv in zip(us, vs)])
    for iu in range(nu + 1):
        for iv in range(nv + 1):
            p = F.P(-L / 2 + iu * du, -W / 2 + iv * dv); mb.beam((*p, 0), (*p, e), 0.14, 0.14, 'steel_white')
    for iu in range(nu):
        for iv in range(nv):
            p = F.P(-L / 2 + (iu + 0.5) * du, -W / 2 + (iv + 0.5) * dv); mb.beam((*p, 0), (*p, r - 0.15), 0.12, 0.12, 'steel_white')


def bleacher(B, mb):
    """aluminium bleacher (GE n290): plank seats and footboards on galvanised raking frames, rails at the back and ends"""
    p0, p1 = np.array(B['front'], float); u = (p1 - p0) / np.linalg.norm(p1 - p0); L = np.linalg.norm(p1 - p0)
    v = np.array([-u[1], u[0]]); v = v if np.dot(v, -(p0 + p1) / 2) < 0 else -v          # v: away from the pitch
    n, z0, rise = B['rows'], B['z0'], B['rise']; step = B['depth'] / n; ang = math.degrees(math.atan2(u[1], u[0]))
    Q = lambda a, d: p0 + u * a + v * d
    for k in range(n):
        d = 0.35 + k * step; z = z0 + k * rise
        mb.box(tuple(Q(L / 2, d + 0.12)), L, 0.32, 0.05, ang, 'alu', z0=z + 0.42)            # seat plank
        mb.box(tuple(Q(L / 2, d - 0.22)), L, 0.26, 0.04, ang, 'alu', z0=z)                   # footboard
        mb.box(tuple(Q(L / 2, d + 0.3)), L, 0.03, 0.42, ang, 'alu', z0=z)                    # riser plate
    zt = z0 + (n - 1) * rise; dt = 0.35 + (n - 1) * step + 0.4
    a = 0.0
    while a <= L + 1e-6:
        mb.beam((*Q(a, 0.1), 0), (*Q(a, dt), zt + 0.45), 0.12, 0.2, 'steel_galv')
        mb.beam((*Q(a, dt), 0), (*Q(a, dt), zt + 1.5), 0.1, 0.1, 'steel_galv')
        mb.beam((*Q(a, 0.1), 0), (*Q(a, 0.1), z0 + 0.4), 0.1, 0.1, 'steel_galv')
        mb.beam((*Q(a, dt * 0.5), 0), (*Q(a, dt * 0.5), z0 + 0.5 * (zt - z0) + 0.4), 0.1, 0.1, 'steel_galv')
        a += L / max(1, round(L / 3.0))
    mb.beam((*Q(0, dt), zt + 1.5), (*Q(L, dt), zt + 1.5), 0.06, 0.06, 'steel_galv')
    mb.beam((*Q(0, dt), zt + 1.0), (*Q(L, dt), zt + 1.0), 0.05, 0.05, 'steel_galv')
    for a in (0.0, L):
        mb.beam((*Q(a, 0.1), z0 + 1.3), (*Q(a, dt), zt + 1.5), 0.05, 0.05, 'steel_galv')


def sails(Sd, mb):
    """white shade sails along the club's pitch front: twisted squares on white posts, a low terrace of seats beneath"""
    a, b_ = np.array(Sd['from'], float), np.array(Sd['to'], float); n = Sd['n']; dep = Sd['depth']
    u = (b_ - a) / np.linalg.norm(b_ - a); v = np.array([-u[1], u[0]]); v = v if np.dot(v, -(a + b_) / 2) < 0 else -v
    Lt = np.linalg.norm(b_ - a); w = Lt / n; k = 6; tu, tv = TILE['tent']
    for i in range(n):
        c0 = a + u * w * i
        Z = [Sd['hi'], Sd['lo'], Sd['hi'], Sd['lo']] if i % 2 == 0 else [Sd['lo'], Sd['hi'], Sd['lo'], Sd['hi']]
        corner = [c0 + u * 0.3, c0 + u * (w - 0.3), c0 + u * (w - 0.3) + v * dep, c0 + u * 0.3 + v * dep]
        def S(s, t):
            p = (1 - s) * (1 - t) * corner[0] + s * (1 - t) * corner[1] + s * t * corner[2] + (1 - s) * t * corner[3]
            z = (1 - s) * (1 - t) * Z[0] + s * (1 - t) * Z[1] + s * t * Z[2] + (1 - s) * t * Z[3]
            return (*p, z)
        for x in range(k):
            for y in range(k):
                ss = [(x + p) / k for p in (0, 1, 1, 0)]; tt = [(y + p) / k for p in (0, 0, 1, 1)]
                both(mb, [S(s, t) for s, t in zip(ss, tt)], 'tent', [(s * w / tu, t * dep / tv) for s, t in zip(ss, tt)])
        for j in range(4):
            mb.beam((*corner[j], 0), (*corner[j], Z[j] + 0.3), 0.18, 0.18, 'steel_white')
    # terrace under the sails: four rows stepping up toward the club
    ang = math.degrees(math.atan2(u[1], u[0]))
    for r in range(4):
        d = 1.0 + r * 1.0; z = 0.35 * r
        mb.box(tuple(a + u * Lt / 2 + v * (d + 0.5)), Lt, 1.0, z + 0.001, ang, 'conc_tread')
        s = 0.8
        while s < Lt - 0.6:
            if (s % 12.0) > 1.2: seat(tuple(a + u * s + v * (d + 0.9)), tuple(u), tuple(v), z, pick('gstand'))
            s += 0.5


def scoreboard(Sb, mb):
    c = np.array(Sb['c'], float); u = np.array(Sb['u'], float); u /= np.linalg.norm(u); n_in = np.array([-u[1], u[0]])
    if np.dot(n_in, -c) < 0: n_in = -n_in
    w, dp, top = Sb['w'], Sb['depth'], Sb['top']; ang = math.degrees(math.atan2(u[1], u[0]))
    z0 = Sb['faces'][0][0] - 0.25
    mb.box(tuple(c), w, dp, top - z0, ang, 'paint_black', z0=z0)
    for k in (-1, 1):   # two square legs, outside the frame, down to concrete pads
        p = c + u * k * (w / 2 + 0.3) - n_in * 0.1; mb.box(tuple(p), 0.5, 0.6, 6.9, ang, 'steel_galv')   # galvanised legs to the mid band (photo 07)
        mb.box(tuple(p), 1.2, 1.2, 0.15, ang, 'conc_wall', z0=-0.05)
    for f0, f1, m in Sb['faces']:
        p = c + n_in * (dp / 2 + 0.02); A = p - u * (w / 2 - 0.25); Bq = p + u * (w / 2 - 0.25); tu, tv = TILE.get(m, (1, 1))
        uv = [(0, 0), (1, 0), (1, 1), (0, 1)] if m.startswith('sign') else [(0, 0), ((w - 0.5) / tu, 0), ((w - 0.5) / tu, (f1 - f0) / tv), (0, (f1 - f0) / tv)]
        oriented(mb, [(*A, f0), (*Bq, f0), (*Bq, f1), (*A, f1)], m, np.array([*n_in, 0.0]), uv)
    # small script name on the top band, a ladder and two service platforms on the west side (photo 07)
    p = c + n_in * (dp / 2 + 0.02); A = p - u * 2.2; Bq = p + u * 2.2
    oriented(mb, [(*A, 11.5), (*Bq, 11.5), (*Bq, 12.15), (*A, 12.15)], 'sign_cazalys', np.array([*n_in, 0.0]), [(0.14, 0.08), (0.86, 0.08), (0.86, 0.92), (0.14, 0.92)])
    s = c - u * (w / 2 + 0.9)
    for zz in (6.5, 11.4):
        mb.box(tuple(s), 1.2, 1.4, 0.08, ang, 'steel_galv', z0=zz)
        for k in (-1, 1): mb.beam((*(s + n_in * 0.7 * k - u * 0.6), zz), (*(s + n_in * 0.7 * k - u * 0.6), zz + 1.1), 0.05, 0.05, 'steel_galv')
        mb.beam((*(s - n_in * 0.7 - u * 0.6), zz + 1.1), (*(s + n_in * 0.7 - u * 0.6), zz + 1.1), 0.05, 0.05, 'steel_galv')
    for k in (-1, 1): mb.beam((*(s + n_in * 0.25 * k - u * 0.5), 0.8), (*(s + n_in * 0.25 * k - u * 0.5), 12.4), 0.05, 0.05, 'steel_galv')
    z = 1.0
    while z < 12.3:
        mb.beam((*(s - n_in * 0.25 - u * 0.5), z), (*(s + n_in * 0.25 - u * 0.5), z), 0.03, 0.03, 'steel_galv'); z += 0.3


def coach_box(C, mb):
    c = np.array(C['c'], float); n_in = -c / np.linalg.norm(c); ang = math.degrees(math.atan2(-n_in[0], n_in[1]))
    mb.box(tuple(c), C['L'], C['W'], C['h'], ang, 'box_black', mtop='paint_black')
    mb.box(tuple(c), C['L'] + 0.3, C['W'] + 0.3, 0.12, ang, 'roof_grey', z0=C['h'])


def tower(mb, x, y, zt):
    """galvanised pole tapering to a 6 x 5 floodlight head facing the centre, tilted 15 deg down"""
    hh, w = 5.0, 7.0; zb = zt - hh; n = 12; r0, r1 = 0.85, 0.42
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        p = lambda a, r, z: (x + r * math.cos(a), y + r * math.sin(a), z)
        oriented(mb, [p(a0, r0, 0), p(a1, r0, 0), p(a1, r1, zb + 1), p(a0, r1, zb + 1)], 'steel_galv',
                 np.array([math.cos(0.5 * (a0 + a1)), math.sin(0.5 * (a0 + a1)), 0]))
    mb.cyl((x, y), 1.4, -0.1, 0.25, 'conc_wall', n=16, top='conc_wall')
    f = np.array([-x, -y, 0.0]); f /= np.linalg.norm(f); s = np.array([-f[1], f[0], 0.0])
    tl = math.radians(15); up = UP * math.cos(tl) - f * math.sin(tl); nr = np.cross(s, up)
    if np.dot(nr, f) < 0: nr = -nr
    c0 = np.array([x, y, zb]) + f * 0.6
    Q = lambda u, v, d=0.0: c0 + s * u * w / 2 + up * v + nr * d
    oriented(mb, [Q(-1, 0), Q(1, 0), Q(1, hh), Q(-1, hh)], 'lamps', nr, [(0, 0), (1, 0), (1, 1), (0, 1)])
    oriented(mb, [Q(-1, 0, -0.8), Q(1, 0, -0.8), Q(1, hh, -0.8), Q(-1, hh, -0.8)], 'steel_galv', -nr)
    for (a, b_) in (((-1, 0), (1, 0)), ((1, 0), (1, hh)), ((1, hh), (-1, hh)), ((-1, hh), (-1, 0))):
        q = [Q(*a), Q(*b_), Q(*b_, -0.8), Q(*a, -0.8)]; cen = Q(0, hh / 2, -0.4)
        oriented(mb, q, 'steel_galv', np.mean(q, 0) - cen)
    mb.beam((x, y, zb - 4), (x, y, zb + 0.5), 0.5, 0.5, 'steel_galv')           # service platform stem
    mb.box((x, y), 2.4, 2.4, 0.15, math.degrees(math.atan2(f[1], f[0])), 'steel_galv', z0=zb - 0.6)


def gate(G, mb):
    """Jeff 'Hoppy' Hopgood Memorial Entrance (photos 02, 03, 09): a thin flat canopy on black round columns over a black
    ticket booth; 'CAZALYS STADIUM' band on the booth's street face above white roller shutters; navy name sign at the east end"""
    F = Frame(G); L, W, h = G['L'], G['W'], G['h']; th = 0.45
    P = [F.P(-L / 2, -W / 2), F.P(L / 2, -W / 2), F.P(L / 2, W / 2), F.P(-L / 2, W / 2)]
    pad = [F.P(-L / 2 - 2, -W / 2 - 1), F.P(L / 2 + 2, -W / 2 - 1), F.P(L / 2 + 2, W / 2 + 4), F.P(-L / 2 - 2, W / 2 + 4)]
    oriented(mb, [(*p, 0.01) for p in pad], 'paving', UP)
    oriented(mb, [(*p, h + th) for p in P], 'roof_white', UP); oriented(mb, [(*p, h) for p in P], 'soffit_dark', -UP)
    for i in range(4):
        a_, b_ = P[i], P[(i + 1) % 4]; m = np.array([(a_[0] + b_[0]) / 2 - G['c'][0], (a_[1] + b_[1]) / 2 - G['c'][1], 0])
        oriented(mb, [(*a_, h), (*b_, h), (*b_, h + th), (*a_, h + th)], 'paint_black', m)
    for u in (-L / 2 + 0.8, -(G['booth'][0] / 2 + 0.6), G['booth'][0] / 2 + 0.6, L / 2 - 0.8):   # inner pair clear of the booth ends (photo 01: sign face unobstructed)
        for v in (-W / 2 + 0.8, W / 2 - 0.8):
            mb.cyl(F.P(u, v), 0.3, 0.0, h, 'paint_black', n=16)
    bl, bw, bh = G['booth']; vo = G['booth_off']; fr = vo + bw / 2               # booth front face (street, +v)
    mb.box(F.P(0, vo), bl, bw, bh, math.degrees(F.a), 'paint_black')   # plain charcoal render (photo 01)
    mb.box(F.P(0, fr - 0.3), bl, 0.6, h - 0.6 - bh, math.degrees(F.a), 'paint_black', z0=bh)   # name band rises to the canopy
    n = np.array([-math.sin(F.a), math.cos(F.a), 0.0])
    def Q(u, z): return (*F.P(u, fr + 0.02), z)
    oriented(mb, [Q(-bl / 2, bh + 0.02), Q(bl / 2, bh + 0.02), Q(bl / 2, h - 0.65), Q(-bl / 2, h - 0.65)], 'sign_gate', n, [(1, 0), (0, 0), (0, 1), (1, 1)])
    for u0, u1 in ((-bl / 2 + 2.6, -0.05), (0.35, bl / 2 - 1.2)):   # two roller shutters with a notice between (photo 01)
        oriented(mb, [Q(u0, 1.15), Q(u1, 1.15), Q(u1, 2.65), Q(u0, 2.65)], 'shutter', n)
    for u in (-bl / 2 + 0.3, -1.6, 2.6, bl / 2 - 0.3):   # diagonal struts from the band to the soffit (photo 01)
        d = 1.0 if u > 0 else -1.0; mb.beam((*F.P(u, fr - 0.1), h - 0.62), (*F.P(u + d * 1.2, fr - 0.1), h - 0.02), 0.08, 0.08, 'paint_black')
    # navy name sign: a freestanding wall at the east end, facing the footpath
    c = F.P(L / 2 - 2.0, W / 2 + 0.6); mb.box(c, 5.0, 0.35, 2.5, math.degrees(F.a), 'paint_black')
    q = [(*F.P(L / 2 - 4.5, W / 2 + 0.79), 0.0), (*F.P(L / 2 + 0.5, W / 2 + 0.79), 0.0), (*F.P(L / 2 + 0.5, W / 2 + 0.79), 2.5), (*F.P(L / 2 - 4.5, W / 2 + 0.79), 2.5)]
    oriented(mb, q, 'sign_hopgood', n, [(1, 0), (0, 0), (0, 1), (1, 1)])
    # turnstile fence each side of the booth: black mesh between the columns
    for s_ in (-1, 1):
        u0, u1 = s_ * bl / 2, s_ * (L / 2 - 0.8)
        both(mb, [(*F.P(u0, fr), 0.0), (*F.P(u1, fr), 0.0), (*F.P(u1, fr), 2.4), (*F.P(u0, fr), 2.4)], 'mesh',
             [(0, 0), (abs(u1 - u0), 0), (abs(u1 - u0), 2.4), (0, 2.4)])


# ---------------- fence, boundary seats, ground ----------------
def fence(col):
    mb = MB('fence'); h = D['fence_h']; bs = np.arange(0, 360.001, 0.5)
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]; ra, rb = fence_r(ba), fence_r(bb)
        L = math.radians(ba) * ra; L2 = math.radians(bb) * rb
        both(mb, [P3(ba, ra, 0.05), P3(bb, rb, 0.05), P3(bb, rb, h), P3(ba, ra, h)], 'mesh', [(L, 0.05), (L2, 0.05), (L2, h), (L, h)])
        mb.beam(P3(ba, ra, h), P3(bb, rb, h), 0.05, 0.05, 'steel_galv'); mb.beam(P3(ba, ra, 0.08), P3(bb, rb, 0.08), 0.03, 0.03, 'steel_galv')
    s = 0.0; b = 0.0
    while b < 360:
        r = fence_r(b); mb.beam(P3(b, r, 0), P3(b, r, h + 0.05), 0.06, 0.06, 'steel_galv'); b += math.degrees(2.5 / r)
    mb.build(col)


def in_arc(b, arcs):
    return any(a0 <= b <= a1 for a0, a1 in arcs)


def boundary_seats(mb):
    """loose tip-up seats on a concrete kerb just behind the fence, colours in threes: maroon, gold, teal (photos 01, 04-06)"""
    B = D['boundary_seats']; P = D['palettes']['boundary']; cyc = [p[0] for p in P]; grp = B['group']
    for a0, a1 in B['arcs']:
        r0 = fence_r(a0) + B['behind']; b = a0 + math.degrees(0.5 / r0); k = 0; run = []
        while b < a1:
            if not in_arc(b, B['skip']):
                r = fence_r(b) + B['behind']; a = math.radians(b); o = (math.sin(a), math.cos(a)); t = (math.cos(a), -math.sin(a))
                seat(pol(b, r + 0.55), t, o, 0.15, cyc[(k // grp) % len(cyc)]); run.append(b); k += 1
                b += math.degrees(0.52 / r)
                if k % (grp * 4) == 0: b += math.degrees(B['gap'] / r)
            else:
                b += 0.25
        # kerb under every run of seats
        runs = []; s0 = None; prev = None
        for x in run:
            if s0 is None: s0 = x
            elif x - prev > 1.0: runs.append((s0, prev)); s0 = x
            prev = x
        if s0 is not None: runs.append((s0, prev))
        for s0, s1 in runs:
            bs = np.arange(s0 - 0.3, s1 + 0.3, 0.5)
            for i in range(len(bs) - 1):
                ba, bb = bs[i], bs[i + 1]
                q = [P3(ba, fence_r(ba) + 0.25, 0.15), P3(bb, fence_r(bb) + 0.25, 0.15), P3(bb, fence_r(bb) + 1.35, 0.15), P3(ba, fence_r(ba) + 1.35, 0.15)]
                oriented(mb, q, 'conc_kerb', UP)
                oriented(mb, [P3(ba, fence_r(ba) + 0.25, 0), P3(bb, fence_r(bb) + 0.25, 0), q[1], q[0]], 'conc_kerb', -np.array([*pol(0.5 * (ba + bb), 1), 0]))
                oriented(mb, [P3(ba, fence_r(ba) + 1.35, 0), P3(bb, fence_r(bb) + 1.35, 0), q[2], q[3]], 'conc_kerb', np.array([*pol(0.5 * (ba + bb), 1), 0]))


def ground(col):
    """grass from the fence out to the perimeter, a paved ring 2.5 m wide just behind the fence"""
    mb = MB('ground'); Pm = np.array(D['perimeter'], float); bs = np.arange(0, 360.001, 1.0)
    def outer(b):
        d = np.array(pol(b, 1.0)); best = None
        for a, c in zip(Pm, np.roll(Pm, -1, 0)):
            e = c - a; M = np.array([[d[0], -e[0]], [d[1], -e[1]]])
            if abs(np.linalg.det(M)) < 1e-9: continue
            t, s = np.linalg.solve(M, a)
            if t > 0 and 0 <= s <= 1: best = t if best is None else max(best, t)
        return best or fence_r(b) + 20
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]; fa, fb = fence_r(ba % 360), fence_r(bb % 360)
        for r0a, r0b, r1a, r1b, m, z in ((fa, fb, fa + 2.5, fb + 2.5, 'paving', -0.01), (fa + 2.5, fb + 2.5, outer(ba), outer(bb), 'grass', -0.02)):
            q = [P3(ba, r0a, z), P3(bb, r0b, z), P3(bb, r1b, z), P3(ba, r1a, z)]
            oriented(mb, q, m, UP, uv=[(p[0] / TILE[m][0], p[1] / TILE[m][1]) for p in q])
    mb.build(col)


def build_all():
    clear(); col = bpy.context.scene.collection
    global POSTS
    mb = MB('stands'); mr = MB('roofs'); mx = MB('extras'); POSTS = MB('seat_posts'); SEATS.clear(); SEAT_XF.clear(); AISLES.clear()
    RNG.bit_generator.state = np.random.default_rng(7).bit_generator.state
    for S in D['terraces']: open_terrace(S, mb)
    grandstand(D['grandstand'], mb, mr)
    for B in D['buildings']: building(B, mx)
    club_front(D['club_front'], mx)
    south_front(D['south_front'], mx)
    for S in D['shelters']: shelter(S, mx)
    for T in D['tents']: tent(T, mx)
    bleacher(D['bleacher'], mx); sails(D['sails'], mx); scoreboard(D['scoreboard'], mx)
    for C in D['coach_box']: coach_box(C, mx)
    gate(D['gate'], mx)
    boundary_seats(mx)
    mb.build(col); mr.build(col); mx.build(col); fence(col)
    for c_, m_ in SEATS.items():
        m_.M = [c_ if x == 'seat' else x for x in m_.M]; m_.build(col)
    POSTS.build(col)
    if not os.environ.get('NOGROUND'): ground(col)
    mt = MB('towers')
    for T in D['towers']: tower(mt, *T['xy'], D['tower_top'])
    mt.build(col)
