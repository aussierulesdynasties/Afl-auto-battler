# York Park exterior (2024-25, before the Centre West rebuild), built from model/york_park.json.
# Runs inside Blender: import build; build.build_all(). Local frame: x east, y north, z up from the field, metres.
# Each stand is a run of polar sections (every 0.5 deg) between its bearings; the fence is the ellipse fitted to the
# grass edge on the Esri tile (work/fence.json).
import bpy, math, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from mb import MB, TILE
D = json.load(open(os.path.join(HERE, 'york_park.json')))
FE = json.load(open(os.path.join(SP, 'work', 'fence.json')))['ell']   # x0, y0, a1, a2, rot(deg)
OSM = json.load(open(os.path.join(SP, 'work', 'osm_xy.json')))


def unlean(S):
    """The Esri tile is not straight down: raised parts show displaced (relief displacement). Each stand's 'lean'
    table [[b, dx, dy], ..] is the plan shift (m) from the tile to the true position, measured by work/xyzfit.py against
    six Google Earth views. Shift the elevated tables (roof, block, back) and move the stand's ends with them."""
    L = np.array(S.get('lean', []), float)
    if not len(L): return
    ends = []
    for key in ('roof', 'block', 'back'):
        if key not in S: continue
        t = np.array(S[key], float); bs = np.arange(t[0, 0], t[-1, 0] + 1e-6, 0.25); cols = []
        for k in range(1, t.shape[1]):
            r = np.interp(bs, t[:, 0], t[:, k]); a = np.radians(bs)
            x = r * np.sin(a) + np.interp(bs, L[:, 0], L[:, 1]); y = r * np.cos(a) + np.interp(bs, L[:, 0], L[:, 2])
            b2 = bs + (np.degrees(np.arctan2(x, y)) - bs + 180) % 360 - 180
            cols.append((b2, np.hypot(x, y)))
        n0 = float(np.mean([c[0][0] for c in cols])); n1 = float(np.mean([c[0][-1] for c in cols]))
        grid = np.linspace(n0, n1, max(2, int((n1 - n0) / 0.5) + 1))
        S[key] = [[float(g)] + [float(np.interp(g, c[0], c[1])) for c in cols] for g in grid]; ends.append((n0, n1))
    S['b0'], S['b1'] = round(ends[0][0], 2), round(ends[0][1], 2)


for _S in D['stands']: unlean(_S)


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
            oriented(mb, [P3(ba, r0, z0), P3(bb, s0, w0), P3(bb, s1, w1), P3(ba, r1, z1)], m, out, uv)


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
        return [(rs0, 0.0), (rs0, zs0), (rb - 0.4, zs1), (rb - 0.4, zb), (rb, zb), (rb, 0.0)]
    strip(mb, bs, prof, [M['front'], M['seat'], 'conc_wall', 'conc_wall', M['back']], -1)
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        endcap(mb, b, prof(b), 'conc_wall', sg)
    roof_strip(S, bs, geo, mr)


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
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        ri, ro = deck(b); a = math.radians(b); tan = np.array([math.cos(a), -math.sin(a), 0.0]) * sg
        oriented(mr, [P3(b, ri, zr0 - th - 0.6), P3(b, ro, zr1 - th - 0.3), P3(b, ro, zr1), P3(b, ri, zr0)], 'fascia', tan)
    # top trusses: a bottom chord on the deck, a raised top chord peaking 2.4 m above it 40% back from the front, diagonals
    sp = S.get('rib', 0)
    if not sp: return
    b, b_end = bs[0], bs[-1]
    while True:
        ri, ro = deck(b); rm = 0.5 * (ri + ro); step = math.degrees(sp / rm)
        b += step if b != bs[0] else 0.35 * step
        if b > b_end - 0.2 * step: break
        ri, ro = deck(b)
        z = lambda r: zr0 + (zr1 - zr0) * (r - ri) / (ro - ri)
        pk = ri + 0.4 * (ro - ri); H = 2.4
        A = P3(b, ri + 0.2, z(ri + 0.2) + 0.15); K = P3(b, pk, z(pk) + H); Bp = P3(b, ro - 0.2, z(ro - 0.2) + 0.15)
        mr.beam(A, K, 0.35, 0.35, 'steel_white'); mr.beam(K, Bp, 0.35, 0.35, 'steel_white')
        mr.beam(A, Bp, 0.25, 0.25, 'steel_white')
        for f in (0.2, 0.55, 0.8):
            r1 = ri + f * (ro - ri); zt = (z(r1) + H * (r1 - ri) / (pk - ri)) if r1 < pk else (z(r1) + H * (ro - r1) / (ro - pk))
            mr.beam(P3(b, r1, z(r1) + 0.15), P3(b, r1, zt), 0.18, 0.18, 'steel_white')


def two_tier(S, mb, mr):
    bs = brange(S); M = S['mats']; zs0, zs1 = S['z_seat']; zb0, zb1 = S['box']; zu0, zu1 = S['z_upper']; zr0, zr1 = S['z_roof']
    def geo(b):
        rf = fence_r(b % 360); ri, ro = interp(S['roof'], b); rs0 = rf + S['seat_front']; rb = ro - S['back_in']
        return rf, ri, ro, rs0, rb
    def prof(b):
        rf, ri, ro, rs0, rb = geo(b); rl = rs0 + S['lower_back']; rbx = rl + zb0
        zb = zr1 - 0.6 - (zr1 - zr0) * (S['back_in'] / (ro - ri))
        return [(rs0, 0.0), (rs0, zs0), (rl, zs1), (rl, zb1), (rl + 0.6, zb1), (rl + 0.6, zu0), (rb - 0.4, zu1), (rb - 0.4, zb), (rb, zb), (rb, 0.0)]
    strip(mb, bs, prof, [M['front'], M['seat'], M['box'], 'conc_wall', 'conc_wall', M['seat'], 'conc_wall', 'conc_wall', M['back']], -1)
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        endcap(mb, b, prof(b), 'conc_wall', sg)
    roof_strip(S, bs, geo, mr)


def open_stand(S, mb):
    bs = brange(S); M = S['mats']; zs0, zs1 = S['z_seat']
    def prof(b):
        rf = fence_r(b % 360); rs0 = rf + S['seat_front']; rb = interp(S['back'], b)[0]
        return [(rs0, 0.0), (rs0, zs0), (rb - 0.4, zs1), (rb - 0.4, zs1 + 1.1), (rb, zs1 + 1.1), (rb, 0.0)]
    strip(mb, bs, prof, [M['front'], M['seat'], 'conc_wall', 'conc_wall', M['back']], -1)
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        endcap(mb, b, prof(b), 'conc_wall', sg)


def block(S, mb, mr):
    bs = brange(S); M = S['mats']; zs0, zs1 = S['z_seat']; H = S['z_block']
    def prof(b):
        rf = fence_r(b % 360); rs0 = rf + S['front_seats'][0]; r1, r2 = interp(S['block'], b)
        return [(rs0, 0.0), (rs0, zs0), (r1, zs1), (r1, H), (r2, H), (r2, 0.0)]
    strip(mb, bs, prof, [M['front'], M['seat'], M['back'], M['roof'], M['back']], -1)
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        endcap(mb, b, prof(b), M['back'], sg)


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


def concourse(col):
    """hard ground from the fence out to the OSM stadium outline (where that is further than the fence)"""
    P = np.array(OSM['stadium'], float); mb = MB('concourse'); bs = np.arange(0, 360.001, 1.0)
    def outer(b):
        d = np.array(pol(b, 1.0)); best = None
        for a, c in zip(P, np.roll(P, -1, 0)):
            e = c - a; M = np.array([[d[0], -e[0]], [d[1], -e[1]]])
            if abs(np.linalg.det(M)) < 1e-9: continue
            t, s = np.linalg.solve(M, a)
            if t > 0 and 0 <= s <= 1: best = t if best is None else max(best, t)
        return best or fence_r(b) + 20
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]
        q = [P3(ba, fence_r(ba % 360), -0.02), P3(bb, fence_r(bb % 360), -0.02), P3(bb, outer(bb), -0.02), P3(ba, outer(ba), -0.02)]
        oriented(mb, q, D['mats_ground']['concourse'], np.array([0, 0, 1.0]),
                 uv=[(p[0] / TILE.get('paving', (1, 1))[0], p[1] / TILE.get('paving', (1, 1))[1]) for p in q])
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


def build_all():
    clear(); col = bpy.context.scene.collection
    mb = MB('stands'); mr = MB('roofs')
    for S in D['stands']:
        {'single': lambda: single(S, mb, mr), 'two_tier': lambda: two_tier(S, mb, mr),
         'open': lambda: open_stand(S, mb), 'block': lambda: block(S, mb, mr)}[S['kind']]()
    mb.build(col); mr.build(col)
    fence(col)
    if not os.environ.get('NOCONC'): concourse(col)
    if D['towers']:
        mt = MB('towers')
        for T in D['towers']:
            tower(mt, T)
        mt.build(col)
