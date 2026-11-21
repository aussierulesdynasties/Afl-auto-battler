# Accor Stadium (Sydney Olympic Park), today's ground in its oval (AFL) layout, built from work/plan.json.
# Runs inside Blender: import build; build.build_all(). Local frame: x east, y north, z up from the field, metres
# (origin = OSM centroid of way 4385777). Bowl, saddle roof, the two arches, four ramp towers, facade, signs, fence.
import bpy, math, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from mb import MB, TILE
PL = json.load(open(os.path.join(SP, 'work', 'plan.json')))
FE = PL['fence']                     # x0, y0, a1, a2, rot(deg from +x): the AFL oval
D = {'fence_h': 1.1}
CC = np.array(PL['centre'], float); AX = math.radians(PL['axis'])
OSM = json.load(open(os.path.join(SP, 'work', 'osm_xy.json')))


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
    # ellipse in its own frame: ((u/a1)^2 + (v/a2)^2 = 1), u along rot
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


def P3(b, r, z):
    x, y = pol(b, r); return (x, y, z)


def strip(mb, bs, prof, mats, rdir_out):
    """prof(b) -> list of (r, z); mats[k] = material of segment k->k+1; outward normal of segment = left of travel in (r,z)
    when rdir_out is +1 (solid on the right walking the profile)."""
    for i in range(len(bs) - 1):
        A, B = prof(bs[i]), prof(bs[i + 1]); ba, bb = bs[i], bs[i + 1]
        for k in range(len(A) - 1):
            m = mats[k]
            if m is None: continue
            (r0, z0), (r1, z1) = A[k], A[k + 1]; (s0, w0), (s1, w1) = B[k], B[k + 1]
            dr, dz = r1 - r0, z1 - z0; L = math.hypot(dr, dz)
            if L < 1e-6 and math.hypot(s1 - s0, w1 - w0) < 1e-6: continue
            bm = math.radians(0.5 * (ba + bb)); rad = np.array([math.sin(bm), math.cos(bm), 0.0])
            out = rdir_out * (-dz * rad + np.array([0, 0, dr]))  # left of travel
            tu, tv = TILE.get(m, (1, 1)); rm = 0.5 * (r0 + r1) if L > 1e-6 else r0
            ua = math.radians(ba) * rm / tu; ub = math.radians(bb) * rm / tu
            uv = [(ua, 0), (ub, 0), (ub, L / tv), (ua, L / tv)]
            if dz < -1e-6: uv = [(ua, L / tv), (ub, L / tv), (ub, 0), (ua, 0)]   # walls going down: wall top = image top
            oriented(mb, [P3(ba, r0, z0), P3(bb, s0, w0), P3(bb, s1, w1), P3(ba, r1, z1)], m, out, uv)


SEAT_COL = 'seat_aqua'   # colour seat_rows lays now (one instanced .bin per colour)
SEATS = None      # MB for the 3D seat shells (proof renders only; the GLB instances them), set by build_all
POSTS = None      # MB for the seat pedestals (exported in the GLB)
SEAT_XF = []      # (P, t, o, z) per seat, for the instanced seat files
AISLES = []       # aisle-stair bearings (for the seat-height proof)
ROW = 0.8         # tread depth (m): one row of seats


def stepped(p0, p1, n):
    """the straight rake p0 -> p1 (r, z) as n treads with risers between them"""
    (r0, z0), (r1, z1) = p0, p1; pts = [(r0, z0)]
    for k in range(n):
        zk = z0 + (z1 - z0) * k / (n - 1) if n > 1 else z0; rk = r0 + (r1 - r0) * (k + 1) / n
        if k > 0: pts.append((pts[-1][0], zk))
        pts.append((rk, zk))
    return pts


def terrace(prof, mats, segs):
    """swap each seat segment k of prof for n stepped treads; segs = [(k, n)]"""
    def p2(b):
        P = prof(b)
        for k, n in sorted(segs, reverse=True): P = P[:k] + stepped(P[k], P[k + 1], n) + P[k + 2:]
        return P
    M = list(mats)
    for k, n in sorted(segs, reverse=True): M = M[:k] + ['conc_tread'] * (2 * n - 1) + M[k + 1:]
    return p2, M


def nrows(prof, bs, k):
    P = prof(0.5 * (bs[0] + bs[-1])); return max(1, int(round((P[k + 1][0] - P[k][0]) / ROW)))


def seat(P, t, o, z, shell=None):
    """one empty moulded plastic shell (2024 empty-seat photo): pan and back one curved piece, dished across its width,
    a rolled top edge; P = xy of the back of its tread, t = along the row, o = away from the pitch, z = tread top.
    Centre pedestal under the pan."""
    tmpl = shell is not None; shell = shell if tmpl else SEATS
    if not tmpl: SEAT_XF.append((tuple(P), tuple(t), tuple(o), z, SEAT_COL))
    P = np.array(P, float); t = np.array(t, float); o = np.array(o, float); hw = 0.22
    def X(a, d, h):
        q = P + t * a + o * d; return np.array((q[0], q[1], z + h))
    up = np.array([0, 0, 1.0]); o3 = np.array([*o, 0.0])
    # side section (depth d from the tread back, height h): rolled front lip -> pan -> curved up into the back
    prof = [(-0.66, 0.40), (-0.58, 0.45), (-0.36, 0.44), (-0.25, 0.52), (-0.19, 0.70), (-0.16, 0.82), (-0.165, 0.87)]
    def V(i, j):   # j = -1, 0, 1 across; the middle is dished (down on the pan, back on the backrest), the back narrows to the top
        d, h = prof[i]; w = min(1.0, max(0.0, (h - 0.45) / 0.2)); c = 1 - abs(j)
        return X(j * hw * (1 - 0.35 * max(0.0, (h - 0.74) / 0.13) ** 2), d + 0.07 * c * w, h - 0.05 * c * (1 - w) + 0.02 * c * (h > 0.86))
    for i in range(len(prof) - 1):
        dd, dh = prof[i + 1][0] - prof[i][0], prof[i + 1][1] - prof[i][1]
        out = -dh * o3 + dd * up
        for j in (-1, 0):
            oriented(shell, [V(i, j), V(i, j + 1), V(i + 1, j + 1), V(i + 1, j)], 'seat_plastic' if tmpl else SEAT_COL, out,
                     [((j + 1) / 2, i / 6), ((j + 2) / 2, i / 6), ((j + 2) / 2, (i + 1) / 6), ((j + 1) / 2, (i + 1) / 6)])
    if tmpl: return
    oriented(POSTS,[X(-0.04, -0.45, 0.0), X(0.04, -0.45, 0.0), X(0.04, -0.45, 0.38), X(-0.04, -0.45, 0.38)], 'steel_galv', -o3)


def seat_rows(bs, prof, k, n, aisle=12.0, gap=1.1):
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
                seat(pol(b, rr), t, o, zz)
            b += math.degrees(0.5 / rr)


def endcap(mb, b, pts, m, sign):
    """fill the closed section polygon pts [(r,z)...] at bearing b; normal along the tangent (sign +1 = increasing bearing)"""
    from mb import earclip
    P = [(r, z) for r, z in pts]
    a = math.radians(b); tan = np.array([math.cos(a), -math.sin(a), 0.0]) * sign
    for tri in earclip(ccw2(P)):
        oriented(mb, [P3(b, r, z) for r, z in tri], m, tan,
                 uv=[(r / TILE.get(m, (1, 1))[0], z / TILE.get(m, (1, 1))[1]) for r, z in tri])


def ccw2(P):
    s = sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1] for i in range(len(P)))
    return P if s > 0 else P[::-1]


def brange(S):
    st = D.get('step', 0.5); n = max(2, int(round((S['b1'] - S['b0']) / st)) + 1)
    return list(np.linspace(S['b0'], S['b1'], n))


# ---------------- fence, concourse, towers ----------------
def fence(col):
    mb = MB('fence'); h = D['fence_h']; bs = np.arange(0, 360.001, 0.5)
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]; ra, rb = fence_r(ba), fence_r(bb)
        for d, sg in ((0.0, -1), (0.12, 1)):
            bm = math.radians(0.5 * (ba + bb)); rad = np.array([math.sin(bm), math.cos(bm), 0.0])
            L = math.radians(ba) * ra / TILE.get('fence', (1, 1))[0]; L2 = math.radians(bb) * rb / TILE.get('fence', (1, 1))[0]
            oriented(mb, [P3(ba, ra + d, 0), P3(bb, rb + d, 0), P3(bb, rb + d, h), P3(ba, ra + d, h)], 'fence', sg * rad,
                     [(L, 0), (L2, 0), (L2, 1), (L, 1)])
        oriented(mb, [P3(ba, ra, h), P3(bb, rb, h), P3(bb, rb + 0.12, h), P3(ba, ra + 0.12, h)], 'conc_wall', np.array([0, 0, 1.0]))
    mb.build(col)


# ---------------- plan lookups ----------------
def L2W(u, v):
    return (CC[0] + u * math.sin(AX) + v * math.cos(AX), CC[1] + u * math.cos(AX) - v * math.sin(AX))


def W2L(x, y):
    dx, dy = x - CC[0], y - CC[1]; return (dx * math.sin(AX) + dy * math.cos(AX), dx * math.cos(AX) - dy * math.sin(AX))


def ray_poly(P, b):
    """furthest crossing of the ray from the origin along bearing b with the closed polygon P"""
    d = np.array(pol(b, 1.0)); best = None; P = np.array(P, float)
    for a, c in zip(P, np.roll(P, -1, 0)):
        e = c - a; M = np.array([[d[0], -e[0]], [d[1], -e[1]]])
        if abs(np.linalg.det(M)) < 1e-12: continue
        t, s = np.linalg.solve(M, a)
        if t > 0 and -1e-9 <= s <= 1 + 1e-9: best = t if best is None else max(best, t)
    return best


_RO = np.array(PL['roof_outer'], float); _RO = np.r_[_RO[-1:] - [360, 0], _RO, _RO[:1] + [360, 0]]
OPEN = [L2W(u, v) for u, v in PL['roof_inner_local']]
HT = PL['heights']


def roof_o(b): return float(np.interp(b % 360, _RO[:, 0], _RO[:, 1]))
def roof_i(b): return ray_poly(OPEN, b % 360)
def facade_r(b): return ray_poly(OSM['stadium'], b % 360) - PL.get('facade_inset', 0.0)   # OSM outline = awning edge; wall sits ~10 m in (GE l090)
def sval(b): return abs(math.sin(math.radians(b) - AX))      # 1 on the wings (east, west), 0 at the ends
def zo(b): return HT['roof_outer_end'] + (HT['roof_outer_side'] - HT['roof_outer_end']) * sval(b) ** 2
def zi(b): return HT['roof_inner_end'] + (HT['roof_inner_side'] - HT['roof_inner_end']) * sval(b) ** 2


def deckz(b, r):
    ri, ro = roof_i(b), roof_o(b); return zi(b) + (zo(b) - zi(b)) * (r - ri) / (ro - ri)


# ---------------- the bowl ----------------
LOW = (3.5, 27.5, 1.5, 11.0)        # lower tier: front and back (m out from the fence), front and back tread heights
SEC = 5.0                           # bowl sector (deg): one row count per sector for the upper tier
RISE = 0.5                          # upper tier riser per 0.8 m row
FACADE_BAND = 38.0                  # top of the lower facade = top of the entry louvres (GE l090)


def bowl_sector(mb, b0, b1):
    """one 5 deg sector of the bowl: lower tier all round; on the wings a band of boxes, a middle tier and a second
    band; at the ends one band; then the upper tier up toward the roof, a concourse roof back to the facade, louvres
    up to the roof underside, the facade down to the ground"""
    global SEAT_COL
    bs = list(np.linspace(b0, b1, int(round((b1 - b0) / 0.5)) + 1)); bm = 0.5 * (b0 + b1)
    wing = sval(bm) > 0.62
    def upper0(b):
        rf = fence_r(b % 360)
        return (rf + 44.0, 27.0) if wing else (rf + 30.0, 15.0)
    def lim(b):   # last tread must stay 4 m under the roof deck and 3 m inside the facade
        r0, z0 = upper0(b); rw = facade_r(b); n = 0
        while True:
            r1, z1 = r0 + (n + 1) * 0.8, z0 + n * RISE
            if r1 > rw - 3.0 or z1 + 1.2 > deckz(b, r1) - 4.0: return n
            n += 1
    nu = max(2, min(lim(b) for b in bs))
    def prof(b):
        rf = fence_r(b % 360); rw = facade_r(b); lf, lb, zf, zb = LOW
        P = [(rf + lf, 0.0), (rf + lf, zf), (rf + lb, zb)]
        if wing: P += [(rf + lb, 14.5), (rf + lb + 2.0, 14.5), (rf + lb + 14.0, 21.0), (rf + lb + 14.0, 27.0)]
        else: P += [(rf + lb, 15.0)]
        r0, z0 = upper0(b); r1, z1 = r0 + nu * 0.8, z0 + (nu - 1) * RISE
        zd = deckz(b, rw) - 1.0
        P += [(r0, z0), (r1, z1), (r1, z1 + 1.2), (rw - 0.4, z1 + 1.2), (rw - 0.4, zd), (rw, zd), (rw, min(FACADE_BAND, zd)), (rw, 0.0)]   # the wall never rises through the low end roof
        return P
    if wing:
        mats = ['conc_wall', 'conc_tread', 'box_glass', 'conc_tread', 'conc_tread', 'box_glass', 'conc_tread', 'conc_tread', 'conc_wall',
                'roof_flat', 'louvre', 'conc_wall', 'facade_upper', 'facade_main']
        segs = [(1, 30), (4, 15), (7, nu)]
    else:
        mats = ['conc_wall', 'conc_tread', 'box_glass', 'conc_tread', 'conc_tread', 'conc_wall', 'roof_flat', 'louvre', 'conc_wall',
                'facade_upper', 'facade_end']
        segs = [(1, 30), (4, nu)]
    tp, tm = terrace(prof, mats, segs)
    strip(mb, bs, tp, tm, 1)
    SEAT_COL = 'seat_aqua'; seat_rows(bs, prof, 1, 30)
    SEAT_COL = 'seat_teal'
    if wing: seat_rows(bs, prof, 4, 15); seat_rows(bs, prof, 7, nu)
    else: seat_rows(bs, prof, 4, nu)
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        endcap(mb, b, tp(b), 'conc_wall', sg)


def apron(col):
    """concrete apron between the fence and the front of the lower tier"""
    mb = MB('apron'); bs = np.arange(0, 360.001, 0.5)
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]
        q = [P3(ba, fence_r(ba % 360) + 0.12, 0.0), P3(bb, fence_r(bb % 360) + 0.12, 0.0), P3(bb, fence_r(bb % 360) + LOW[0], 0.0),
             P3(ba, fence_r(ba % 360) + LOW[0], 0.0)]
        oriented(mb, q, 'paving', np.array([0, 0, 1.0]), uv=[(p[0] / TILE['paving'][0], p[1] / TILE['paving'][1]) for p in q])
    mb.build(col)


# ---------------- roof ----------------
def roof(col):
    mr = MB('roof'); ms = MB('roof_steel'); bs = np.arange(0, 360.001, 0.5); th = 0.6
    up = np.array([0, 0, 1.0])
    def uvl(p, m):
        u, v = W2L(p[0], p[1]); tu, tv = TILE[m]; return (v / tu, u / tv)
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]
        A = [(ba, roof_i(ba)), (bb, roof_i(bb)), (bb, roof_o(bb)), (ba, roof_o(ba))]
        top = [P3(b, r, deckz(b, r)) for b, r in A]; bot = [P3(b, r, deckz(b, r) - th) for b, r in A]
        for k in range(8):   # 8 radial pieces so the dark band outside each arch (GE top65: |v| 64-104 m, |u| < 95 m) gets its own sheets
            f0, f1 = k / 8, (k + 1) / 8
            pc = [(ba, A[0][1] + f0 * (A[3][1] - A[0][1])), (bb, A[1][1] + f0 * (A[2][1] - A[1][1])),
                  (bb, A[1][1] + f1 * (A[2][1] - A[1][1])), (ba, A[0][1] + f1 * (A[3][1] - A[0][1]))]
            tq = [P3(b, r, deckz(b, r)) for b, r in pc]; cu, cv = W2L(*np.mean(np.array(tq), 0)[:2])
            m = 'roof_top'
            oriented(mr, tq, m, up, [uvl(p, 'roof_top') for p in tq])
        oriented(mr, bot, 'roof_soffit', -up, [uvl(p, 'roof_soffit') for p in bot])
        for k0, k1, sgn in ((0, 1, -1), (2, 3, 1)):   # inner fascia (toward the pitch) and outer edge
            (b_a, r_a), (b_b, r_b) = A[k0], A[k1]; drop = 1.6 if sgn < 0 else 1.0
            bmid = math.radians(0.5 * (ba + bb)); rad = np.array([math.sin(bmid), math.cos(bmid), 0.0]) * sgn
            q = [P3(b_a, r_a, deckz(b_a, r_a) - th - drop), P3(b_b, r_b, deckz(b_b, r_b) - th - drop), P3(b_b, r_b, deckz(b_b, r_b)), P3(b_a, r_a, deckz(b_a, r_a))]
            oriented(mr, q, 'fascia', rad)
    # outer edge truss: a top chord 1.4 m over the deck edge, two bottom chords 3 m under it, a web every 4 m
    step = 4.0; b = 0.0; nodes = []
    while b < 360:
        ro = roof_o(b); z = zo(b); nodes.append((b, ro, z)); b += math.degrees(step / ro)
    nodes.append(nodes[0])
    for (ba, ra, za), (bb, rb, zb) in zip(nodes[:-1], nodes[1:]):
        T1 = P3(bb, rb + 0.6, zb + 1.4); T0 = P3(ba, ra + 0.6, za + 1.4)
        Bi0, Bi1 = P3(ba, ra - 0.6, za - 3.0), P3(bb, rb - 0.6, zb - 3.0)
        Bo0, Bo1 = P3(ba, ra + 1.8, za - 3.0), P3(bb, rb + 1.8, zb - 3.0)
        ms.beam(T0, T1, 0.45, 0.45, 'steel_white'); ms.beam(Bi0, Bi1, 0.35, 0.35, 'steel_white'); ms.beam(Bo0, Bo1, 0.35, 0.35, 'steel_white')
        ms.beam(Bo0, T1, 0.2, 0.2, 'steel_white'); ms.beam(Bi0, T1, 0.2, 0.2, 'steel_white'); ms.beam(Bo0, Bi0, 0.18, 0.18, 'steel_white')
    # radial trusses under the deck every 3 deg: bottom chord 2.6 m under the soffit, verticals and diagonals every 5 m
    for b in np.arange(0.0, 360.0, 3.0):
        ri, ro = roof_i(b), roof_o(b); n = max(2, int((ro - ri) / 5.0)); rs = np.linspace(ri + 0.5, ro - 0.5, n + 1)
        tz = lambda r: deckz(b, r) - th - 0.15; bz = lambda r: deckz(b, r) - th - 2.6
        ms.beam(P3(b, rs[0], bz(rs[0])), P3(b, rs[-1], bz(rs[-1])), 0.3, 0.3, 'steel_white')
        for k in range(n):
            ms.beam(P3(b, rs[k], tz(rs[k])), P3(b, rs[k], bz(rs[k])), 0.16, 0.16, 'steel_white')
            ms.beam(P3(b, rs[k], bz(rs[k])), P3(b, rs[k + 1], tz(rs[k + 1])), 0.14, 0.14, 'steel_white')
    mr.build(col); ms.build(col)


def arches(col):
    """the two main arches: a triangular truss (two top chords 4 m apart, one bottom chord under them), a parabola
    from foot to foot over the roof, panels every 6 m"""
    A = PL['arch']; ma = MB('arches'); u0, u1 = A['u_feet']; ua = A['u_apex']; Z = A['z_apex']; w = A['width'] / 2; dp = A['depth'] - 1.0
    L = lambda u: Z * (1 - ((u - ua) / ((u1 - ua) if u > ua else (ua - u0))) ** 2)
    for v in A['v']:
        n = int((u1 - u0) / 6.0); us = np.linspace(u0, u1, n + 1)
        def pt(u, dv, dz):
            x, y = L2W(u, v + dv); return (x, y, max(0.0, L(u)) + dz)
        for k in range(n):
            a, b = us[k], us[k + 1]
            for dv, dz, s in ((-w, 0, 1.0), (w, 0, 1.0), (0, -dp, 0.9)):
                ma.beam(pt(a, dv, dz), pt(b, dv, dz), s, s, 'steel_white')
            ma.beam(pt(a, -w, 0), pt(a, w, 0), 0.35, 0.35, 'steel_white')
            ma.beam(pt(a, -w, 0), pt(b, 0, -dp), 0.35, 0.35, 'steel_white'); ma.beam(pt(a, w, 0), pt(b, 0, -dp), 0.35, 0.35, 'steel_white')
            ma.beam(pt(a, 0, -dp), pt(b, -w, 0), 0.35, 0.35, 'steel_white'); ma.beam(pt(a, 0, -dp), pt(b, w, 0), 0.35, 0.35, 'steel_white')
        for uf in (u0, u1):   # white tapered concrete pylon (GE l000, l180): 10 x 9 m at the ground, up the arch line to 22 m
            ut = ua + (uf - ua) * math.sqrt(1 - 22.0 / Z); sg = 1 if uf > ua else -1
            B = [(*L2W(uf + sg * du, v + dv), 0.0) for du, dv in ((5, -4.5), (5, 4.5), (-5, 4.5), (-5, -4.5))]
            T = [(*L2W(ut + sg * du, v + dv), 22.0) for du, dv in ((1.5, -w - 0.6), (1.5, w + 0.6), (-1.5, w + 0.6), (-1.5, -w - 0.6))]
            cen = np.mean(np.array(B + T), 0)
            for i in range(4):
                q = [B[i], B[(i + 1) % 4], T[(i + 1) % 4], T[i]]; m = np.mean(np.array(q), 0)
                nn = m - cen; nn[2] = 0; nn /= np.linalg.norm(nn) + 1e-9
                oriented(ma, q, 'conc_wall', nn, [(0, 0), (1.6, 0), (1.6, 3.7), (0, 3.7)])   # concrete thrust block (BVN: 'four prominent concrete thrust blocks')
    ma.build(col)


def towers(col):
    """the four spiral ramp towers: a ribbed drum of ramps, a flat top, the lift core rising through it"""
    mt = MB('towers'); zt = PL.get('tower_h', 36.0); n = 72
    for x, y, r in PL['towers']:
        for k in range(n):
            a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n; am = 0.5 * (a0 + a1)
            p = lambda a, rr, z: (x + rr * math.cos(a), y + rr * math.sin(a), z)
            u0, u1 = a0 / (0.5 * math.pi), a1 / (0.5 * math.pi)   # exactly 4 tiles per drum so the helix closes
            oriented(mt, [p(a0, r, 0), p(a1, r, 0), p(a1, r, zt), p(a0, r, zt)], 'ramp', np.array([math.cos(am), math.sin(am), 0]),
                     [(u0, 0), (u1, 0), (u1, zt / TILE['ramp'][1]), (u0, zt / TILE['ramp'][1])])
        mt.cyl((x, y), r, zt, zt + 0.6, 'conc_wall', n=72, top='roof_flat')
        # the wide flat disc cap over the top ramp (roof_above_008, towers_034, backs_066): ~1.35 x the drum (signage_085), on 12 posts
        for k in range(12):
            a = 2 * math.pi * k / 12; mt.cyl((x + 0.9 * r * math.cos(a), y + 0.9 * r * math.sin(a)), 0.25, zt + 0.6, zt + 3.4, 'steel_white', n=8)
        mt.cyl((x, y), 1.35 * r, zt + 3.4, zt + 4.0, 'fascia', n=72, top='roof_flat')
        d = np.array(PL['centre']) - np.array((x, y)); d = d / np.linalg.norm(d) * r * 0.35
        mt.cyl((x + d[0], y + d[1]), 6.0, zt + 0.6, zt + 7.0, 'steel_white', n=36, top='roof_flat')
    mt.build(col)


def facade_extras(col):
    """louvre fins over the east and west entries, the two name signs above them"""
    me = MB('facade')
    # entry fins (GE l090, l270): flat white panels 1.2 m wide at a 1.75 m pitch, standing 1.2 m proud of a dark recess
    z0, z1 = PL['louvre_z']
    for b0, b1 in PL['louvres']:
        b = b0
        while b < b1:
            r = facade_r(b); n = np.array(pol(b, 1.0)); t = np.array([n[1], -n[0]])
            me.box(tuple(np.array(pol(b, r)) + n * 1.2), 1.2, 0.4, z1 - z0, math.degrees(math.atan2(t[1], t[0])), 'steel_white', z0=z0)
            b += math.degrees(1.75 / r)
        bs = np.linspace(b0, b1, int((b1 - b0) / 0.5) + 1)
        for i in range(len(bs) - 1):
            q = [P3(bs[i], facade_r(bs[i]) + 0.15, 0.0), P3(bs[i + 1], facade_r(bs[i + 1]) + 0.15, 0.0),
                 P3(bs[i + 1], facade_r(bs[i + 1]) + 0.15, z1), P3(bs[i], facade_r(bs[i]) + 0.15, z1)]
            oriented(me, q, 'box_glass', np.array([*pol(0.5 * (bs[i] + bs[i + 1]), 1.0), 0.0]), [(0, 0), (1, 0), (1, z1 / 3.5), (0, z1 / 3.5)])
    # entry canopies: a thin grey deck 5.6 m up, 2-15 m out from the wall, a post every 10 m on the outer edge
    C = PL['canopy']; o0, o1 = C['out']; zc = C['z']
    for b0, b1 in PL['canopies']:
        bs = np.linspace(b0, b1, int((b1 - b0) / 0.5) + 1)
        for i in range(len(bs) - 1):
            ra, rb = facade_r(bs[i]), facade_r(bs[i + 1])
            for z, nz in ((zc + 0.4, 1.0), (zc, -1.0)):
                q = [P3(bs[i], ra + o0, z), P3(bs[i + 1], rb + o0, z), P3(bs[i + 1], rb + o1, z), P3(bs[i], ra + o1, z)]
                oriented(me, q, 'roof_flat' if nz > 0 else 'steel_galv', np.array([0, 0, nz]), [(p[0] / 6.0, p[1] / 6.0) for p in q])
            q = [P3(bs[i], ra + o1, zc), P3(bs[i + 1], rb + o1, zc), P3(bs[i + 1], rb + o1, zc + 0.4), P3(bs[i], ra + o1, zc + 0.4)]
            oriented(me, q, 'fascia', np.array([*pol(0.5 * (bs[i] + bs[i + 1]), 1.0), 0.0]), [(0, 0), (1, 0), (1, 0.2), (0, 0.2)])
        b = b0
        while b <= b1:
            me.cyl(tuple(pol(b, facade_r(b) + o1 - 0.5)), 0.25, 0.0, zc, 'steel_white', n=12); b += math.degrees(10.0 / facade_r(b))
    for G in PL['signs']:
        b = G['b']; r = facade_r(b) + 1.0; n = np.array(pol(b, 1.0)); t = np.array([n[1], -n[0]])
        c = np.array(pol(b, r)); a, d = c + t * G['w'] / 2 + n * 0.06, c - t * G['w'] / 2 + n * 0.06; z0, z1 = G['z0'], G['z0'] + G['h']
        me.box(tuple(c - n * 0.25), G['w'], 0.5, G['h'], math.degrees(math.atan2(t[1], t[0])), 'sign_back', z0=z0)
        oriented(me, [(*a, z0), (*d, z0), (*d, z1), (*a, z1)], 'sign_accor', np.array([*n, 0.0]), [(0, 0), (1, 0), (1, 1), (0, 1)])
    me.build(col)


def build_all():
    clear(); col = bpy.context.scene.collection
    global SEATS, POSTS
    mb = MB('bowl'); SEATS = MB('seats'); SEATS.smooth = True; POSTS = MB('seat_posts'); SEAT_XF.clear(); AISLES.clear()
    for b0 in np.arange(0.0, 360.0, SEC):
        bowl_sector(mb, b0, b0 + SEC)
    mb.build(col)
    roof(col); arches(col); towers(col); facade_extras(col); fence(col); apron(col)
    if not os.environ.get('NOSEATS'): SEATS.build(col)
    POSTS.build(col)
