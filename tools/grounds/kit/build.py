# Ground exterior built from <ground>/model/<slug>.json (GROUND env var = the ground's folder, e.g. tools/grounds/barossa).
# Generalised from riverway/model/build.py: the same polar stands (single, two_tier, open, block), fence, concourse,
# light towers and extras, plus grass banks, plain buildings and a whole-ground roof.
# Runs inside Blender: import build; build.build_all(). Local frame: x east, y north, z up from the field, metres;
# the origin is the centre of the boundary fence ellipse.
import bpy, math, json, os, sys
import numpy as np
GROUND = os.path.abspath(os.environ['GROUND']); SLUG = os.path.basename(GROUND)
HERE = os.path.join(GROUND, 'model'); KIT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, KIT)
from mb import MB, TILE, Frame, roof as gable_roof
D = json.load(open(os.path.join(HERE, SLUG + '.json')))
FE = D['fence']   # x0, y0, a1, a2, rot(deg): the boundary fence ellipse


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


SHEAR = []   # stands with 'end_skew' {b, deg, ramp}: an end that is not radial (see skew_b)


def skew_b(b, r):
    """a stand end cut on a line that isn't radial: bearings within 'ramp' degrees of the end slide by up to 'deg' at the
    roof's back edge, nothing at its front edge (the roof table's inner radius) or in front of it"""
    for S in SHEAR:
        E = S['end_skew']; w = 1.0 - abs(b - E['b']) / E['ramp']
        if w <= 0: continue
        ri, ro = interp(S['roof'], b)
        if r <= ri or r > ro + 1.0: continue
        b += E['deg'] * w * min(1.0, (r - ri) / (ro - ri))
    return b


def pol(b, r):
    if SHEAR: b = skew_b(b, r)
    a = math.radians(b); return (r * math.sin(a), r * math.cos(a))


FF = D.get('fence_fourier')   # optional: the fence as one smooth polar Fourier curve about FF['c'] (replaces the ellipse)


def ff_R(th):
    """radius of the Fourier fence curve about FF['c'] at math angle th (radians, from +x toward +y)"""
    return FF['a0'] + sum(a * math.cos(k * th) + b * math.sin(k * th) for k, (a, b) in enumerate(FF['ab'], 1))


def fence_r(b):
    """radius from the origin to the boundary fence along bearing b"""
    if FF:   # march out along the ray to the curve, then bisect (the origin is inside the curve)
        d = np.array(pol(b, 1.0)); c = np.array(FF['c'])
        f = lambda r: np.linalg.norm(d * r - c) - ff_R(math.atan2(*(d * r - c)[::-1]))
        lo, hi = 0.0, 1.0
        while f(hi) < 0: lo, hi = hi, hi + 5.0
        for _ in range(40):
            mid = 0.5 * (lo + hi); lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
        return 0.5 * (lo + hi)
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
    ucum = {}   # running arc length per profile segment, so u runs on across face joints (no texture jump where r changes)
    for i in range(len(bs) - 1):
        A, B = prof(bs[i]), prof(bs[i + 1]); ba, bb = bs[i], bs[i + 1]
        for k in range(len(A) - 1):
            m = mats[k]
            if callable(m): m = m(0.5 * (ba + bb))
            if m is None: continue
            (r0, z0), (r1, z1) = A[k], A[k + 1]; (s0, w0), (s1, w1) = B[k], B[k + 1]
            dr, dz = r1 - r0, z1 - z0; L = math.hypot(dr, dz)
            if L < 1e-6 and math.hypot(s1 - s0, w1 - w0) < 1e-6: continue
            bm = math.radians(0.5 * (ba + bb)); rad = np.array([math.sin(bm), math.cos(bm), 0.0])
            out = rdir_out * (-dz * rad + np.array([0, 0, dr]))  # left of travel
            tu, tv = TILE.get(m, (1, 1)); rm = 0.5 * (r0 + r1) if L > 1e-6 else r0
            ua = ucum.get(k, math.radians(ba) * rm / tu); ub = ua + math.radians(bb - ba) * rm / tu; ucum[k] = ub
            LB = math.hypot(s1 - s0, w1 - w0)   # each side keeps its own length: no shear where the wall height changes
            uv = [(ua, 0), (ub, 0), (ub, LB / tv), (ua, L / tv)]
            if dz < -1e-6: uv = [(ua, L / tv), (ub, LB / tv), (ub, 0), (ua, 0)]   # walls going down: wall top = image top
            oriented(mb, [P3(ba, r0, z0), P3(bb, s0, w0), P3(bb, s1, w1), P3(ba, r1, z1)], m, out, uv)


SEATS = None      # MB for the 3D seat shells (proof renders only; the GLB instances them), set by build_all
POSTS = None      # MB for the seat pedestals (exported in the GLB)
SEAT_XF = []      # (P, t, o, z, colour) per seat, for the instanced seat files
SEAT_RNG = np.random.default_rng(7)
AISLES = []       # aisle-stair bearings (for the seat-height proof)
ROW_COLS = ['seat_a']   # set per stand: S['row_cols'] = seat colour of each row, front to back (last repeats)
SEAT_MIX = None   # or S['seat_mix'] = [[colour, share], ...]: colours scattered at random (a mixed-colour stand)
PITCH = 0.55
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


def seat(P, t, o, z, shell=None, col=None):
    """one empty moulded plastic shell (2024 empty-seat photo): pan and back one curved piece, dished across its width,
    a rolled top edge; P = xy of the back of its tread, t = along the row, o = away from the pitch, z = tread top.
    Centre pedestal under the pan."""
    tmpl = shell is not None; shell = shell if tmpl else SEATS
    col = col or ROW_COLS[0]
    if not tmpl: SEAT_XF.append((tuple(P), tuple(t), tuple(o), z, col))
    P = np.array(P, float); t = np.array(t, float); o = np.array(o, float); hw = 0.19
    def X(a, d, h):
        q = P + t * a + o * d; return np.array((q[0], q[1], z + h))
    up = np.array([0, 0, 1.0]); o3 = np.array([*o, 0.0])
    # side section (depth d from the tread back, height h): rolled front lip -> pan -> curved up into the back
    prof = [(-0.66, 0.40), (-0.58, 0.45), (-0.36, 0.44), (-0.25, 0.52), (-0.19, 0.70), (-0.16, 0.82), (-0.165, 0.87)]
    def V(i, j):   # j = -1, 0, 1 across; the middle is dished (down on the pan, back on the backrest), the back narrows to the top
        d, h = prof[i]; w = min(1.0, max(0.0, (h - 0.45) / 0.2)); c = 1 - abs(j)
        return X(j * hw * (1 - 0.6 * max(0.0, (h - 0.55) / 0.32) ** 1.3), d + 0.07 * c * w, h - 0.05 * c * (1 - w) + 0.02 * c * (h > 0.86))
    for i in range(len(prof) - 1):
        dd, dh = prof[i + 1][0] - prof[i][0], prof[i + 1][1] - prof[i][1]
        out = -dh * o3 + dd * up
        for j in (-1, 0):
            oriented(shell, [V(i, j), V(i, j + 1), V(i + 1, j + 1), V(i + 1, j)], 'seat_plastic' if tmpl else col, out,
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
    # per section between aisles: N seats centred on even rows, N-1 on odd rows (staggered half a seat, tb_8c29 photo);
    # radial columns (bearing steps), so every row ends the same distance from its aisle
    sec = [b0] + ab + [b1]
    clr = lambda i: (0.3 if i == 0 else gap / 2 + 0.25)
    def row(b, j):   # the back of tread j on the radial line at bearing b (where stepped() draws it), z0, z1
        P = prof(b); (r0, z0), (r1, z1) = P[k], P[k + 1]; return np.array(pol(b, r0 + (r1 - r0) * (j + 1) / n)), z0, z1
    for j in range(n):
        for i in range(len(sec) - 1):
            lo = sec[i] + math.degrees(clr(i) / rf); hi = sec[i + 1] - math.degrees(clr(i + 1 if i + 1 < len(sec) - 1 else 0) / rf)
            st = math.degrees(PITCH / rf); hi -= st / 2
            N = int(math.floor((hi - lo) / st + 1e-9)) + 1
            if N < 1: continue
            mid = 0.5 * (lo + hi) + (st / 2 if j % 2 else 0.0)
            offs = [(m - (N - 1) / 2) * st for m in range(N)]
            for m in range(N):
                bb = mid + offs[m]
                # each row on its own radial line: a step of dr along the row's normal walks off the radial
                # treads where the bowl is not round (Sky Stadium's upper rows ended a tread up, sunk into it)
                q, z0, z1 = row(bb, j); tt = row(bb + 0.05, j)[0] - row(bb - 0.05, j)[0]; tt /= np.linalg.norm(tt)
                oo = np.array((-tt[1], tt[0]))
                if oo @ q < 0: oo = -oo
                zz = z0 + (z1 - z0) * j / (n - 1) if n > 1 else z0
                if SEAT_MIX:
                    cs, ps = zip(*SEAT_MIX); col = cs[int(SEAT_RNG.choice(len(cs), p=np.array(ps) / sum(ps)))]
                else:
                    col = ROW_COLS[min(j, len(ROW_COLS) - 1)]
                seat(tuple(q), tuple(tt), tuple(oo), zz, col=col)


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


# ---------------- stand kinds ----------------
def single(S, mb, mr):
    bs = brange(S); M = S['mats']; zs0, zs1 = S['z_seat']; zr0, zr1 = S['z_roof']
    def geo(b):
        rf = fence_r(b % 360); ri, ro = interp(S['roof'], b); rs0 = rf + S['seat_front']; rb = ro - S['back_in']
        return rf, ri, ro, rs0, rb
    def prof(b):
        rf, ri, ro, rs0, rb = geo(b); zb = zr1 - 0.6 - (zr1 - zr0) * (S['back_in'] / (ro - ri))
        # front wall up, seats up the rake, back wall of the bowl up to the roof, cap, facade down
        rl = min(rs0 + S['seat_depth'], rb - 0.4) if 'seat_depth' in S else rb - 0.4   # seats end at the glass level
        # the box top follows 5 cm under the roof soffit (flat in front of the roof's leading edge) so no wall pierces the deck
        sof = lambda r: zr0 - 0.5 + (r - ri) / (ro - ri) * (zr1 - zr0) - 0.05
        rk = max(rl + 0.01, ri); zk = min(zb, sof(rk)); zf = min(zk, sof(max(rl, ri)))
        return [(rs0, 0.0), (rs0, zs0), (rl, zs1), (rl, zf), (rk, zk), (rb, zb), (rb, 0.0)]
    zones = S.get('back_zones', [])   # stretches of the back wall in another cladding: [b0, b1, mat]
    back = lambda b: next((z[2] for z in zones if z[0] <= b < z[1]), M['back'])
    walls = [None] * 4 if S.get('open_back') else [M.get('bowl', 'conc_wall'), 'conc_wall', 'conc_wall', back]   # open_back: the ground's own back (custom)
    n = nrows(prof, bs, 1); tp, tm = terrace(prof, [M['front'], M['seat']] + walls, [(1, n)])
    strip(mb, bs, tp, tm, -1); seat_rows(bs, prof, 1, n)
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        endcap(mb, b, tp(b), 'conc_wall', sg)
    ribs = roof_strip(S, bs, geo, mr)
    if S.get('brace'): bracing(S, ribs, geo, mr)


def roof_strip(S, bs, geo, mr):
    """roof deck from ri (z_roof[0]) to ro (z_roof[1]), 0.5 m thick, white trusses on top every S['rib'] metres"""
    zr0, zr1 = S['z_roof']; th = 0.5; M = S['mats']; sol = S.get('solar', [])
    def deck(b):
        rf, ri, ro, rs0, rb = geo(b); return ri, ro
    def roofmat(b):
        for b0, b1, f0, f1 in sol:
            if b0 <= b < b1: return 'solar_zone'
        return M['roof']
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]; (ria, roa), (rib, rob) = deck(ba), deck(bb); m = roofmat(0.5 * (ba + bb))
        up = np.array([0, 0, 1.0]); dn = -up
        if m == 'solar_zone':
            f0, f1 = [s for s in sol if s[0] <= 0.5 * (ba + bb) < s[1]][0][2:]
            cuts = [(0, f0, M['roof']), (f0, f1, 'solar'), (f1, 1, M['roof'])]
        else:
            cuts = [(0, 1, m)]
        for g0, g1, mm in cuts:
            ra0, ra1 = ria + g0 * (roa - ria), ria + g1 * (roa - ria); rb0, rb1 = rib + g0 * (rob - rib), rib + g1 * (rob - rib)
            za0, za1 = zr0 + g0 * (zr1 - zr0), zr0 + g1 * (zr1 - zr0)
            tu, tv = TILE.get(mm, (1, 1)); rm = 0.5 * (ra0 + ra1)
            ua, ub = math.radians(ba) * rm / tu, math.radians(bb) * rm / tu
            uv = [(ua, ra0 / tv), (ub, rb0 / tv), (ub, rb1 / tv), (ua, ra1 / tv)]
            oriented(mr, [P3(ba, ra0, za0), P3(bb, rb0, za0), P3(bb, rb1, za1), P3(ba, ra1, za1)], mm, up, uv)
            oriented(mr, [P3(ba, ra0, za0 - th), P3(bb, rb0, za0 - th), P3(bb, rb1, za1 - th), P3(ba, ra1, za1 - th)], 'roof_soffit', dn,
                     [(ua, ra0 / 6), (ub, rb0 / 6), (ub, rb1 / 6), (ua, ra1 / 6)])
        bm = math.radians(0.5 * (ba + bb)); rad = np.array([math.sin(bm), math.cos(bm), 0.0])
        oriented(mr, [P3(ba, ria, zr0 - th - 0.6), P3(bb, rib, zr0 - th - 0.6), P3(bb, rib, zr0), P3(ba, ria, zr0)], 'fascia', -rad)
        oriented(mr, [P3(ba, roa, zr1 - th - 0.3), P3(bb, rob, zr1 - th - 0.3), P3(bb, rob, zr1), P3(ba, roa, zr1)], 'fascia', rad)
    for b, sg in ((bs[0], -1), (bs[-1], 1)):   # close the deck's ends so the slab never reads as loose sheets
        ri, ro = deck(b); t = math.radians(b); tan = np.array([math.cos(t), -math.sin(t), 0.0]) * sg
        oriented(mr, [P3(b, ri, zr0 - th), P3(b, ro, zr1 - th), P3(b, ro, zr1), P3(b, ri, zr0)], 'fascia', tan)
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        ri, ro = deck(b); a = math.radians(b); tan = np.array([math.cos(a), -math.sin(a), 0.0]) * sg
        oriented(mr, [P3(b, ri, zr0 - th), P3(b, ro, zr1 - th), P3(b, ro, zr1), P3(b, ri, zr0)], 'fascia', tan)
    # top trusses: a bottom chord on the deck, a raised top chord peaking 2.4 m above it 40% back from the front, diagonals
    sp = S.get('rib', 0); ribs = []
    if not sp: return ribs
    b, b_end = bs[0], bs[-1]
    while True:
        ri, ro = deck(b); rm = 0.5 * (ri + ro); step = math.degrees(sp / rm)
        b += step if b != bs[0] else 0.35 * step
        if b > b_end - 0.2 * step: break
        ri, ro = deck(b); ribs.append(b)
        z = lambda r: zr0 + (zr1 - zr0) * (r - ri) / (ro - ri)
        pk = ri + 0.4 * (ro - ri); H = 2.4
        A = P3(b, ri + 0.2, z(ri + 0.2) + 0.15); K = P3(b, pk, z(pk) + H); Bp = P3(b, ro - 0.2, z(ro - 0.2) + 0.15)
        mr.beam(A, K, 0.35, 0.35, 'steel_white'); mr.beam(K, Bp, 0.35, 0.35, 'steel_white')
        mr.beam(A, Bp, 0.25, 0.25, 'steel_white')
        for f in (0.2, 0.55, 0.8):
            r1 = ri + f * (ro - ri); zt = (z(r1) + H * (r1 - ri) / (pk - ri)) if r1 < pk else (z(r1) + H * (ro - r1) / (ro - pk))
            mr.beam(P3(b, r1, z(r1) + 0.15), P3(b, r1, zt), 0.18, 0.18, 'steel_white')
    return ribs


def bracing(S, ribs, geo, mr):
    """steel frame on the stand back (aerial4, GE): a white column under each roof truss standing 1.3 m proud of the
    cladding up to the roof's rear edge (and one halfway between trusses), a top beam and a girt at 0.68 of the height joining them, and an X brace from
    the girt to the ground in every third bay"""
    zr1 = S['z_roof'][1]; H = zr1 - 0.5; zg = 0.68 * H; cols = []
    full = [x for i, rb0 in enumerate(ribs) for x in ([rb0] if i == 0 else [0.5 * (ribs[i - 1] + rb0), rb0])]
    for b in full:   # a column under each truss and one halfway between (aerial4: about twice as many columns as trusses)
        rf, ri, ro, rs0, rb = geo(b); r = rb + 1.3; cols.append((b, r))
        mr.beam(P3(b, r, 0.0), P3(b, r, H), 0.4, 0.4, 'steel_white')
        mr.beam(P3(b, r, H - 0.3), P3(b, rb, H - 0.3), 0.3, 0.3, 'steel_white')
    for i in range(len(cols) - 1):
        (ba, ra), (bb, rb_) = cols[i], cols[i + 1]
        mr.beam(P3(ba, ra, H - 0.2), P3(bb, rb_, H - 0.2), 0.3, 0.4, 'steel_white')
        mr.beam(P3(ba, ra, zg), P3(bb, rb_, zg), 0.25, 0.3, 'steel_white')
        if i % 3 == 1:
            mr.beam(P3(ba, ra, zg), P3(bb, rb_, 0.3), 0.2, 0.2, 'steel_white')
            mr.beam(P3(bb, rb_, zg), P3(ba, ra, 0.3), 0.2, 0.2, 'steel_white')


def two_tier(S, mb, mr):
    bs = brange(S); M = S['mats']; zs0, zs1 = S['z_seat']; zb0, zb1 = S['box']; zu0, zu1 = S['z_upper']; zr0, zr1 = S['z_roof']
    def geo(b):
        rf = fence_r(b % 360); ri, ro = interp(S['roof'], b); rs0 = rf + S['seat_front']; rb = ro - S['back_in']
        return rf, ri, ro, rs0, rb
    def prof(b):
        rf, ri, ro, rs0, rb = geo(b); rl = rs0 + S['lower_back']; rbx = rl + zb0
        zb = zr1 - 0.6 - (zr1 - zr0) * (S['back_in'] / (ro - ri))
        return [(rs0, 0.0), (rs0, zs0), (rl, zs1), (rl, zb1), (rl + 0.6, zb1), (rl + 0.6, zu0), (rb - 0.4, zu1), (rb - 0.4, zb), (rb, zb), (rb, 0.0)]
    n1, n5 = nrows(prof, bs, 1), nrows(prof, bs, 5)
    tp, tm = terrace(prof, [M['front'], M['seat'], M['box'], 'conc_wall', 'conc_wall', M['seat'], 'conc_wall', 'conc_wall', M['back']], [(1, n1), (5, n5)])
    strip(mb, bs, tp, tm, -1); seat_rows(bs, prof, 1, n1); seat_rows(bs, prof, 5, n5)
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        endcap(mb, b, tp(b), 'conc_wall', sg)
    roof_strip(S, bs, geo, mr)


def open_stand(S, mb):
    bs = brange(S); M = S['mats']; zs0, zs1 = S['z_seat']
    def prof(b):
        rf = fence_r(b % 360); rs0 = interp(S['front_tab'], b)[0] if 'front_tab' in S else rf + S['seat_front']; rb = interp(S['back'], b)[0]
        return [(rs0, 0.0), (rs0, zs0), (rb - 0.4, zs1), (rb - 0.4, zs1 + 1.1), (rb, zs1 + 1.1), (rb, 0.0)]
    n = nrows(prof, bs, 1); tp, tm = terrace(prof, [M['front'], M['seat'], 'conc_wall', 'conc_wall', M['back']], [(1, n)])
    strip(mb, bs, tp, tm, -1)
    if not S.get('no_seats'): seat_rows(bs, prof, 1, n)
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        endcap(mb, b, tp(b), 'conc_wall', sg)


def block(S, mb, mr):
    bs = brange(S); M = S['mats']; zs0, zs1 = S['z_seat']; H = S['z_block']
    def prof(b):
        rf = fence_r(b % 360); rs0 = rf + S['front_seats'][0]; r1, r2 = interp(S['block'], b)
        return [(rs0, 0.0), (rs0, zs0), (r1, zs1), (r1, H), (r2, H), (r2, 0.0)]
    n = nrows(prof, bs, 1); tp, tm = terrace(prof, [M['front'], M['seat'], M['back'], M['roof'], M['back']], [(1, n)])
    strip(mb, bs, tp, tm, -1); seat_rows(bs, prof, 1, n)
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        endcap(mb, b, tp(b), M['back'], sg)
    if 'poly' in S:   # building traced from the satellite roof, moved by the lean at its height
        L = np.mean(np.array(S['lean'], float)[:, 1:], 0) / S['lean_z']
        P = [(x + L[0] * S['poly_z'], y + L[1] * S['poly_z']) for x, y in S['poly']]
        mb.prism(P, 0.0, S['poly_z'], M['back'], top=M['roof'])
        if 'overhang' in S:   # roof slab projecting toward the pitch along the front edge (poly points 0-1)
            p, q = np.array(P[0]), np.array(P[1]); t = (q - p) / np.linalg.norm(q - p); n = np.array([t[1], -t[0]])
            if np.dot(n, -(p + q) / 2) < 0: n = -n
            o = S['overhang']; Z = S['poly_z']
            mb.prism([tuple(p), tuple(q), tuple(q + n * o), tuple(p + n * o)], Z - 0.6, Z, 'paint_white', top=M['roof'], bot='roof_soffit')
        G = S.get('plant')
        if G:
            c = (G['c'][0] + L[0] * G['z'][1], G['c'][1] + L[1] * G['z'][1])
            mb.box(c, G['L'], G['W'], G['z'][1] - G['z'][0], G['a'], 'paint_white', z0=G['z'][0])


def straight(S, mb, mr):
    """a straight stand (most regional grounds): front edge from S['a'] to S['b'] (plan, m), seats rising 'depth' m away
    from the pitch from z_seat[0] to z_seat[1], a back wall, and an optional skillion roof S['roof'] =
    {z_front, z_back, over_front, over_back, posts (spacing m, 0 = none), mat}. Front wall S['mats']['front']."""
    A = np.array(S['a'], float); B = np.array(S['b'], float); L = np.linalg.norm(B - A); u = (B - A) / L
    n = np.array([u[1], -u[0]])
    if np.dot(n, (A + B) / 2) < 0: n = -n   # away from the pitch
    M = S['mats']; dep = S['depth']; z0, z1 = S['z_seat']; rows = max(2, int(round(dep / ROW))); back = S.get('back_h', 1.1)
    up = np.array([0, 0, 1.0]); n3 = np.array([*n, 0.0]); u3 = np.array([*u, 0.0])
    W = lambda d, s_, z: (*(A + u * s_ + n * d), z)
    prof = stepped((0.0, z0), (dep, z1), rows); prof = [(0.0, 0.0)] + prof + [(dep, z1 + back), (dep + 0.3, z1 + back), (dep + 0.3, 0.0)]
    mats = [M['front']] + ['conc_tread'] * (len(prof) - 5) + ['conc_wall', 'conc_wall', M.get('back', 'conc_wall')]
    for k in range(len(prof) - 1):
        (d0, za), (d1, zb) = prof[k], prof[k + 1]; m = mats[k]; dd, dz = d1 - d0, zb - za
        out = -dz * n3 + dd * up   # left of travel (toward the pitch / up)
        Ls = math.hypot(dd, dz); tu, tv = TILE.get(m, (1, 1))
        oriented(mb, [W(d0, 0, za), W(d0, L, za), W(d1, L, zb), W(d1, 0, zb)], m, out,
                 [(0, 0), (L / tu, 0), (L / tu, Ls / tv), (0, Ls / tv)])
    from mb import earclip
    for s_, sg in ((0.0, -1), (L, 1)):
        for tri in earclip(ccw2(prof)):
            oriented(mb, [W(d, s_, z) for d, z in tri], M.get('end', 'conc_wall'), u3 * sg,
                     [(d / TILE.get(M.get('end', 'conc_wall'), (1, 1))[0], z / TILE.get(M.get('end', 'conc_wall'), (1, 1))[1]) for d, z in tri])
    # seats: N per row between aisles at both ends and every 'aisle' m
    if not S.get('no_seats'):
        ais = S.get('aisle', 12.0); edges = list(np.arange(0.0, L, ais)) + [L]
        if L - edges[-2] < 3: edges.pop(-2)
        dr = dep / rows
        for j in range(rows):
            zz = z0 + (z1 - z0) * j / (rows - 1)
            for e0, e1 in zip(edges[:-1], edges[1:]):
                lo, hi = e0 + 0.7, e1 - 0.7; N = int((hi - lo) / PITCH)
                for m_ in range(N):
                    s_ = lo + (m_ + 0.5) * (hi - lo) / N + (PITCH / 4 if j % 2 else 0)
                    if SEAT_MIX:
                        cs, ps = zip(*SEAT_MIX); col = cs[int(SEAT_RNG.choice(len(cs), p=np.array(ps) / sum(ps)))]
                    else:
                        col = ROW_COLS[min(j, len(ROW_COLS) - 1)]
                    seat(tuple(A + u * s_ + n * (j + 1) * dr), tuple(u), tuple(n), zz, col=col)
    R = S.get('roof')
    if R:
        f0, f1 = -R.get('over_front', 2.0), dep + 0.3 + R.get('over_back', 0.5); za, zb = R['z_front'], R['z_back']; th = 0.35
        e = R.get('over_end', 0.5); rm = R.get('mat', 'roof_grey')
        Q = [W(f0, -e, za), W(f0, L + e, za), W(f1, L + e, zb), W(f1, -e, zb)]
        oriented(mr, Q, rm, up, [(p[0] / TILE.get(rm, (6, 6))[0], p[1] / TILE.get(rm, (6, 6))[1]) for p in Q])
        oriented(mr, [(x, y, z - th) for x, y, z in Q], 'roof_soffit', -up)
        for (pa, pb) in ((0, 1), (1, 2), (2, 3), (3, 0)):
            a3, b3 = np.array(Q[pa]), np.array(Q[pb]); c3 = (a3 + b3) / 2; o_ = c3 - np.mean(Q, 0); o_[2] = 0
            oriented(mr, [tuple(a3), tuple(b3), tuple(b3 - (0, 0, th + 0.25)), tuple(a3 - (0, 0, th + 0.25))], 'fascia', o_)
        sp = R.get('posts', 6.0)
        if sp:
            for s_ in np.linspace(0, L, max(2, int(round(L / sp)) + 1)):
                for d, z in ((f0 + 0.5, za), (dep + 0.15, zb)):
                    zt = za + (zb - za) * (d - f0) / (f1 - f0) - th
                    if d < 0 and not R.get('front_posts', True): continue
                    mr.box(tuple(A + u * s_ + n * d), 0.25, 0.25, zt, math.degrees(math.atan2(u[1], u[0])), R.get('post_mat', 'steel_white'))


def bank(S, mb, mr):
    """grass bank (a hill): from the fence (plus 'front') up to the crest, then down the back to the ground.
    S['bank'] = [[b, r_crest, r_back], ...]; S['z_bank'] = crest height"""
    bs = brange(S); H = S['z_bank']; fr = S.get('front', 2.0)
    def prof(b):
        rf = fence_r(b % 360); rc, rb = interp(S['bank'], b)
        return [(rf + fr, 0.0), (rc, H), (rc + 1.5, H), (rb, 0.0)]
    m = S['mats'].get('bank', 'grass_bank')
    strip(mb, bs, prof, [m, m, m], -1)
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        endcap(mb, b, prof(b), m, sg)


def dome(R, mr):
    """whole-ground roof (R = D['dome']): an elliptical shell over the bowl from the rim ellipse (a, b, rot, z_rim) rising
    'rise' to a crown, translucent panels on a grid of steel ribs (radial every 'rib_deg', rings every 'ring')"""
    a, b_, rot, zr, rise = R['a'], R['b'], R['rot'], R['z_rim'], R['rise']; t = math.radians(rot)
    c, s_ = math.cos(t), math.sin(t)
    def P(u, f):   # u: angle round the ellipse, f: 0 crown .. 1 rim
        x, y = a * f * math.cos(u), b_ * f * math.sin(u); z = zr + rise * (1 - f * f)
        return np.array((c * x - s_ * y, s_ * x + c * y, z))
    nu, nf = 144, 12
    for i in range(nu):
        u0, u1 = 2 * math.pi * i / nu, 2 * math.pi * (i + 1) / nu
        for j in range(nf):
            f0, f1 = j / nf, (j + 1) / nf
            q = [P(u0, f0), P(u1, f0), P(u1, f1), P(u0, f1)]
            if j == 0: q = [P(u0, 0), P(u1, f1), P(u0, f1)]
            oriented(mr, q, R.get('mat', 'etfe'), np.array([0, 0, 1.0]), [(0, 0), (1, 0), (1, 1), (0, 1)][:len(q)])
    for k in range(int(360 / R.get('rib_deg', 7.5))):   # radial ribs
        u = math.radians(k * R.get('rib_deg', 7.5)); pts = [P(u, j / nf) for j in range(1, nf + 1)]
        for p0, p1 in zip(pts[:-1], pts[1:]): mr.beam(p0 - (0, 0, 0.6), p1 - (0, 0, 0.6), 0.5, 1.0, R.get('rib_mat', 'timber'))
    for j in range(2, nf + 1, R.get('ring', 2)):   # rings
        f = j / nf; pts = [P(2 * math.pi * i / nu, f) for i in range(nu + 1)]
        for p0, p1 in zip(pts[:-1], pts[1:]): mr.beam(p0 - (0, 0, 0.5), p1 - (0, 0, 0.5), 0.4, 0.8, R.get('rib_mat', 'timber'))


# ---------------- fence, concourse, towers ----------------
def fence(col):
    fm = D.get('fence_mat', 'mesh'); mb = MB('fence'); h = D['fence_h']; bs = np.arange(0, 360.001, 0.5)
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]; ra, rb = fence_r(ba), fence_r(bb)
        if any(g0 <= 0.5 * (ba + bb) <= g1 for g0, g1 in D.get('fence_gaps', [])): continue   # open to the field (player race)
        for d, sg in ((0.0, -1), (0.12, 1)):
            bm = math.radians(0.5 * (ba + bb)); rad = np.array([math.sin(bm), math.cos(bm), 0.0])
            L = math.radians(ba) * ra / TILE.get(fm, (1, 1))[0]; L2 = math.radians(bb) * rb / TILE.get(fm, (1, 1))[0]
            oriented(mb, [P3(ba, ra + d, 0), P3(bb, rb + d, 0), P3(bb, rb + d, h), P3(ba, ra + d, h)], fm, sg * rad,
                     [(L, 0), (L2, 0), (L2, 1), (L, 1)])
        oriented(mb, [P3(ba, ra, h), P3(bb, rb, h), P3(bb, rb + 0.12, h), P3(ba, ra + 0.12, h)], D.get('fence_cap', 'conc_wall'), np.array([0, 0, 1.0]))
    mb.build(col)


_TZ = {}


def terrain_z(b, r):
    """ground height at bearing b, radius r from the ground's 'terrain' table (heights measured beyond the fence, see
    concourse); 0 when the ground has none"""
    T = D.get('terrain')
    if not T: return 0.0
    if 'tb' not in _TZ:
        tb = np.array(T['b'], float); o = np.argsort(tb); _TZ.update(tb=tb[o], Z=np.array(T['z'], float)[o], dr=np.array(T['dr'], float))
    key = round(b % 360, 6)
    if key not in _TZ:
        _TZ[key] = (fence_r(key), [float(np.interp(key, _TZ['tb'], _TZ['Z'][:, j], period=360)) for j in range(len(_TZ['dr']))])
    fr, col = _TZ[key]; return float(np.interp(r - fr, _TZ['dr'], col))


def concourse(col):
    """grass bank from the fence out to the outer path ring (outer_r), a path ring beyond it (path_w a number or a [b, w] table; ground_r, where the ground disc ends, likewise); with a 'terrain' table
    {b: [bearings], dr: [distances beyond the fence], z: [[height per dr] per bearing]} the bank and path follow the
    measured ground (held at the last measured height beyond the table), otherwise they are flat"""
    mb = MB('concourse'); bs = np.arange(0, 360.001, 1.0); RO = D['outer_r']
    Ro = (lambda b: float(np.interp(b % 360, *zip(*RO), period=360))) if isinstance(RO, list) else (lambda b: RO)
    PWt = D.get('path_w', 3.0); T = D.get('terrain')
    pw = (lambda b: float(np.interp(b % 360, *zip(*PWt), period=360))) if isinstance(PWt, list) else (lambda b: PWt)
    RG = D.get('ground_r', 240)   # where the ground disc ends: a number or a [b, r] table
    Rg = (lambda b: float(np.interp(b % 360, *zip(*RG), period=360))) if isinstance(RG, list) else (lambda b: RG)
    def band2(ra, rb, ra2, rb2, step):   # radii across a band on both edges of a 1-degree slice, split every 'step' m
        n = max(1, int(math.ceil(max(rb - ra, rb2 - ra2) / step))) if T else 1
        return [ra + (rb - ra) * j / n for j in range(n + 1)], [ra2 + (rb2 - ra2) * j / n for j in range(n + 1)]
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]
        for r0a, r0b, r1a, r1b, m in ((fence_r(ba % 360) + 0.12, fence_r(bb % 360) + 0.12, Ro(ba), Ro(bb), D['mats_ground']['concourse']),
                                      (Ro(ba), Ro(bb), Ro(ba) + pw(ba), Ro(bb) + pw(bb), D['mats_ground'].get('path', 'paving'))):
            A, B = band2(r0a, r1a, r0b, r1b, 1.5)
            for j in range(len(A) - 1):
                q = [P3(ba, A[j], terrain_z(ba, A[j]) - 0.02), P3(bb, B[j], terrain_z(bb, B[j]) - 0.02),
                     P3(bb, B[j + 1], terrain_z(bb, B[j + 1]) - 0.02), P3(ba, A[j + 1], terrain_z(ba, A[j + 1]) - 0.02)]
                oriented(mb, q, m, np.array([0, 0, 1.0]), uv=[(p[0] / TILE.get(m, (1, 1))[0], p[1] / TILE.get(m, (1, 1))[1]) for p in q])
    for G in D.get('rings', []):   # a flat band between two [b, r] tables (a running track round the field)
        ti, to = G['in'], G['out']
        for i in range(len(bs) - 1):
            ba, bb = bs[i], bs[i + 1]; m = G['mat']
            q = [P3(ba, interp(ti, ba)[0], 0.015), P3(bb, interp(ti, bb)[0], 0.015), P3(bb, interp(to, bb)[0], 0.015), P3(ba, interp(to, ba)[0], 0.015)]
            oriented(mb, q, m, np.array([0, 0, 1.0]), uv=[(p[0] / TILE.get(m, (1, 1))[0], p[1] / TILE.get(m, (1, 1))[1]) for p in q])
    # field-level floor inside the fence (the game lays its field on top) and a ground disc under everything beyond the path,
    # so nothing stands over sky (Bruce gate fix, 2026-11-19)
    gm = D['mats_ground'].get('field', 'ground_grass'); om = D['mats_ground'].get('outside', 'ground_grass')
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]
        Q = [([P3(ba, 0, -0.05), P3(bb, fence_r(bb % 360) + 0.2, -0.05), P3(ba, fence_r(ba % 360) + 0.2, -0.05)], gm)]
        A, B = band2(Ro(ba) + pw(ba) - 0.2, Rg(ba), Ro(bb) + pw(bb) - 0.2, Rg(bb), 4.0)
        for j in range(len(A) - 1):
            Q.append(([P3(ba, A[j], terrain_z(ba, A[j]) - 0.04), P3(bb, B[j], terrain_z(bb, B[j]) - 0.04),
                       P3(bb, B[j + 1], terrain_z(bb, B[j + 1]) - 0.04), P3(ba, A[j + 1], terrain_z(ba, A[j + 1]) - 0.04)], om))
        for q, m in Q:
            oriented(mb, q, m, np.array([0, 0, 1.0]), uv=[(p[0] / TILE.get(m, (1, 1))[0], p[1] / TILE.get(m, (1, 1))[1]) for p in q])
    mb.build(col)


def tower(mb, T):
    x, y = T['xy']; zt = T['top']; hh = T.get('head_h', 6.0); w = T.get('head_w', 7.0); zb = zt - hh
    n = 12; r0, r1 = T.get('r_base', 0.9), T.get('r_top', 0.45)
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        p = lambda a, r, z: (x + r * math.cos(a), y + r * math.sin(a), z)
        oriented(mb, [p(a0, r0, 0), p(a1, r0, 0), p(a1, r1, zb + 1), p(a0, r1, zb + 1)], 'steel_galv',
                 np.array([math.cos(0.5 * (a0 + a1)), math.sin(0.5 * (a0 + a1)), 0]))
    f = np.array([-x, -y, 0.0]); f /= np.linalg.norm(f); s = np.array([-f[1], f[0], 0.0])
    tl = math.radians(T.get('tilt', 15)); up = np.array([0, 0, 1.0]) * math.cos(tl) - f * math.sin(tl); nr = np.cross(s, up)
    if np.dot(nr, f) < 0: nr = -nr
    c0 = np.array([x, y, zb]) + f * 0.6
    Q = lambda u, v, d=0.0: c0 + s * u * w / 2 + up * v + nr * d
    oriented(mb, [Q(-1, 0), Q(1, 0), Q(1, hh), Q(-1, hh)], 'lamps', nr, [(0, 0), (1, 0), (1, 1), (0, 1)])
    oriented(mb, [Q(-1, 0, -0.8), Q(1, 0, -0.8), Q(1, hh, -0.8), Q(-1, hh, -0.8)], 'steel_galv', -nr)
    for (a, b_) in (((-1, 0), (1, 0)), ((1, 0), (1, hh)), ((1, hh), (-1, hh)), ((-1, hh), (-1, 0))):
        q = [Q(*a), Q(*b_), Q(*b_, -0.8), Q(*a, -0.8)]; cen = Q(0, hh / 2, -0.4)
        oriented(mb, q, 'steel_galv', np.mean(q, 0) - cen)


def scoreboard(mb, L, R, inset, z0, z1, depth, frame, back, faces, rim, back_rim=None):
    """board box between plan points L and R (pulled 'inset' toward the pitch): frame material all round, the screen
    faces [(f0, f1, mat)] across the front inside a rim, a plain back panel inside the same rim"""
    u = (R - L) / np.linalg.norm(R - L); n_in = np.array([-u[1], u[0]])
    if np.dot(n_in, -(L + R) / 2) < 0: n_in = -n_in
    c = (L + R) / 2 + n_in * inset; ang = math.degrees(math.atan2(u[1], u[0])); wd = np.linalg.norm(R - L)
    mb.box(c, wd, depth, z1 - z0, ang, frame, z0=z0)
    a0 = c - u * (wd / 2 - rim); a1 = c + u * (wd / 2 - rim); hz = z1 - z0 - 2 * rim
    for sg, items in ((1, faces), (-1, [(0.0, 1.0, back)])):
        for f0, f1, m in items:
            p = c + n_in * sg * (depth / 2 + 0.02); A = a0 + (a1 - a0) * f0 + (p - c); Bq = a0 + (a1 - a0) * f1 + (p - c)
            w_ = np.linalg.norm(Bq - A); tu, tv = TILE.get(m, (1, 1))
            oriented(mb, [(*A, z0 + rim), (*Bq, z0 + rim), (*Bq, z1 - rim), (*A, z1 - rim)], m, np.array([*(n_in * sg), 0.0]),
                     [(0, 0), (w_ / tu, 0), (w_ / tu, hz / tv), (0, hz / tv)])
    if back_rim:   # a different colour round the back panel: a full-size face just behind the panel
        p = c - n_in * (depth / 2 + 0.01); A = c - u * wd / 2 + (p - c); Bq = c + u * wd / 2 + (p - c)
        oriented(mb, [(*A, z0), (*Bq, z0), (*Bq, z1), (*A, z1)], back_rim, np.array([*(-n_in), 0.0]))
    return c, u, n_in, wd


def pav_bank(mb, cc, uu, vv, Lp, run, h, hb):
    """seat bank on a pavilion roof: stepped rows from the pitch edge (z h) back to a rear wall (z h + hb), 3D seats,
    stepped side walls in the blue panels"""
    n = max(2, int(round(run / ROW))); f0 = cc + vv * run
    d = lambda j: run * j / n; zj = lambda j: h + hb * j / (n - 1)
    Pt = lambda dd, ss, z: (*(f0 - vv * dd + uu * ss), z)
    up = np.array([0, 0, 1.0]); vv3 = np.array([*vv, 0.0])
    sec = [(0.0, h)]
    for j in range(n):
        if j > 0:
            oriented(mb, [Pt(d(j), -Lp / 2, zj(j - 1)), Pt(d(j), Lp / 2, zj(j - 1)), Pt(d(j), Lp / 2, zj(j)), Pt(d(j), -Lp / 2, zj(j))], 'conc_tread', vv3)
            sec.append((d(j), zj(j)))
        oriented(mb, [Pt(d(j), -Lp / 2, zj(j)), Pt(d(j), Lp / 2, zj(j)), Pt(d(j + 1), Lp / 2, zj(j)), Pt(d(j + 1), -Lp / 2, zj(j))], 'conc_tread', up)
        sec.append((d(j + 1), zj(j)))
        sx = -Lp / 2 + 0.5
        while sx < Lp / 2 - 0.45:
            if abs(sx) > 0.55 + 0.25:   # aisle stair down the middle
                seat(f0 - vv * d(j + 1) + uu * sx, uu, -vv, zj(j))
            sx += 0.5
    from mb import earclip
    sec.append((run, h))
    for s_ in (-1, 1):
        for tri in earclip(ccw2(sec)):
            oriented(mb, [Pt(dd, s_ * Lp / 2, z) for dd, z in tri], 'panel_blue', np.array([*(uu * s_), 0.0]))


def extras(col):
    """plain pieces listed in riverway.json: boxes (plant room, blocks), shade sails on posts, interchange shelters, the
    video screen on its legs, and the name signs"""
    E = D.get('extras', {}); mb = MB('extras')
    for B in E.get('boxes', []):
        mb.box(B['c'], B['L'], B['W'], B['h'], B['a'], B['mat'], z0=B.get('z0', 0.0), mtop=B.get('top'))
    for P in E.get('polys', []):
        mb.prism([tuple(p) for p in P['p']], P.get('z0', 0.0), P['h'], P['mat'], top=P.get('top'), bot=P.get('bot'))
    for B in E.get('buildings', []):   # plain building: walls, windows band, a roof (flat, skillion, gable or hip)
        F = Frame(B); L, W, h = B['L'], B['W'], B['h']; z0 = B.get('z0', 0.0)
        mb.prism([F.P(u, v) for u, v in ((-L / 2, -W / 2), (L / 2, -W / 2), (L / 2, W / 2), (-L / 2, W / 2))], z0, z0 + h, B['mat'], bot=B['mat'])
        gable_roof(mb, F, -L / 2, L / 2, -W / 2, W / 2, B.get('roof', 'flat'), z0 + h, z0 + h + B.get('rise', 0.4), B.get('roofmat', 'roof_grey'),
                   over=B.get('over', 0.4), gm=B['mat'], soffit='roof_soffit', fascia=B.get('fascia', 'fascia'), ridge_axis=B.get('ridge', 'u'))
    for G in E.get('sails', []):   # flat fabric roof on corner posts, sloping one way
        c = np.array(G['c'], float); a = math.radians(G['a']); u = np.array([math.cos(a), math.sin(a)]); v = np.array([-u[1], u[0]])
        L, W = G['L'] / 2, G['W'] / 2; z0, z1 = G['z']
        Q = [(c - u * L - v * W, z0), (c + u * L - v * W, z0), (c + u * L + v * W, z1), (c - u * L + v * W, z1)]
        q3 = [(*p, z) for p, z in Q]
        oriented(mb, q3, G['mat'], np.array([0, 0, 1.0]), [(0, 0), (1, 0), (1, 1), (0, 1)])
        oriented(mb, [(x, y, z - 0.03) for x, y, z in q3], G['mat'], np.array([0, 0, -1.0]), [(0, 0), (1, 0), (1, 1), (0, 1)])
        for p, z in Q: mb.cyl(tuple(p), 0.12, 0, z, 'steel_white', n=8)
    for H in E.get('shelters', []):   # interchange bench shelter: back wall, two ends, a sloping roof
        c = np.array(H['c'], float); a = math.radians(H['a']); u = np.array([math.cos(a), math.sin(a)]); v = np.array([-u[1], u[0]])
        if np.dot(v, -c) < 0: v = -v
        L, W, h = H['L'], H['W'], H['h']
        mb.box(tuple(c - v * W / 2), L, 0.15, h, H['a'], 'shelter_wall')
        for k in (-1, 1): mb.box(tuple(c + u * k * L / 2), 0.15, W, h, H['a'], 'shelter_wall')
        mb.box(tuple(c), L + 0.4, W + 0.4, 0.12, H['a'], 'shelter_roof', z0=h, mtop='shelter_roof')
        mb.box(tuple(c - v * W / 4), L - 0.4, 0.45, 0.45, H['a'], 'steel_galv')
    S = E.get('screen')
    if S:
        L, R = np.array(S['left'], float), np.array(S['right'], float); z0, z1 = S['z']
        c, u, n_in, wd = scoreboard(mb, L, R, 0.0, z0, z1, S['depth'], 'board_back', 'board_back', [(0.0, 1.0, 'screen_off')], 0.3)
        for k in (-1, 1):
            p = c + u * k * (wd / 2 - 1.0); mb.box(p, 0.5, 0.5, z0, math.degrees(math.atan2(u[1], u[0])), 'steel_galv')
    for G in D.get('signs', []):   # flat panel 5 cm proud of the facade, facing the pitch
        c = np.array(G['c'], float); u = np.array(G['u'], float); n = np.array([u[1], -u[0]])
        if np.dot(n, -c) < 0: n = -n
        if G.get('out'): n = -n   # panel on the stand's back wall, facing away from the pitch
        c = c + n * 0.05; a, b = c - u * G['w'] / 2, c + u * G['w'] / 2; z0, z1 = G['z0'], G['z0'] + G['h']
        oriented(mb, [(*a, z0), (*b, z0), (*b, z1), (*a, z1)], G['mat'], np.array([*n, 0.0]), [(0, 0), (1, 0), (1, 1), (0, 1)])
    if mb.F: mb.build(col)


def build_all():
    clear(); col = bpy.context.scene.collection
    global SEATS, POSTS
    mb = MB('stands'); mr = MB('roofs'); SEATS = MB('seats'); SEATS.smooth = True; POSTS = MB('seat_posts'); SEAT_XF.clear()
    global ROW_COLS, SEAT_MIX
    SHEAR[:] = [S for S in D['stands'] if S.get('end_skew')]
    for S in D['stands']:
        ROW_COLS = S.get('row_cols', D.get('row_cols', ['seat_a'])); SEAT_MIX = S.get('seat_mix', D.get('seat_mix'))
        {'bank': lambda: bank(S, mb, mr), 'straight': lambda: straight(S, mb, mr), 'single': lambda: single(S, mb, mr), 'two_tier': lambda: two_tier(S, mb, mr),
         'open': lambda: open_stand(S, mb), 'block': lambda: block(S, mb, mr)}[S['kind']]()
    if D.get('dome'): dome(D['dome'], mr)
    mb.build(col); mr.build(col); keep = SHEAR[:]; SHEAR.clear()
    fence(col); extras(col); SEATS.build(col); POSTS.build(col)
    if not os.environ.get('NOCONC'): concourse(col)
    if D.get('custom'):   # a ground's own pieces the kit has no kind for: <ground>/model/<custom>.py, build(kit) gets this module
        import importlib.util
        spec = importlib.util.spec_from_file_location('custom_' + SLUG, os.path.join(HERE, D['custom']))
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        SHEAR[:] = keep; mod.build(sys.modules[__name__], col); SHEAR.clear()
    if D['towers']:
        mt = MB('towers')
        for T in D['towers']:
            tower(mt, T)
        mt.build(col)
