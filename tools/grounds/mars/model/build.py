# Mars Stadium, Ballarat (finished 2026 ground), built from model/mars.json.
# Runs inside Blender: import build; build.build_all(). Local frame: x east, y north, z up from the field, metres.
# Each stand is a run of polar sections (every 0.5 deg) between its bearings; the fence is the ellipse fitted to the
# grass edge on the Esri tile (work/fence.json).
import bpy, math, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from mb import MB, TILE
D = json.load(open(os.path.join(HERE, 'mars.json')))
FR = np.array(json.load(open(os.path.join(SP, 'work', 'fence.json')))['fr'] + [json.load(open(os.path.join(SP, 'work', 'fence.json')))['fr'][0]])
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


for _S in D['stands']:
    if not _S.get('no_unlean'): unlean(_S)


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


def pol(b, r):
    a = math.radians(b); return (r * math.sin(a), r * math.cos(a))


def fence_r(b):
    """radius from the origin to the fence along bearing b (traced grass edge, one value per degree)"""
    return float(np.interp(b % 360, np.arange(361), FR))


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
    col = SEAT_COL[0]
    if not tmpl: SEAT_XF.append((tuple(P), tuple(t), tuple(o), z, col))
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
            oriented(shell, [V(i, j), V(i, j + 1), V(i + 1, j + 1), V(i + 1, j)], 'seat_plastic' if tmpl else col, out,
                     [((j + 1) / 2, i / 6), ((j + 2) / 2, i / 6), ((j + 2) / 2, (i + 1) / 6), ((j + 1) / 2, (i + 1) / 6)])
    if tmpl: return
    oriented(POSTS,[X(-0.04, -0.45, 0.0), X(0.04, -0.45, 0.0), X(0.04, -0.45, 0.38), X(-0.04, -0.45, 0.38)], 'steel_galv', -o3)


SEAT_COL = ['seat_navyblue']


def seat_colour(pal, j, n, b):
    """seat colours from the finished-ground aerial press/gi/ta_aerial.jpg (sampled) and the 2017 Commons photo
    press/wm/20170707_141248: 'blue' = the new lower banks (navy blue); 'fade' = the new upper tiers (dark charcoal navy);
    'mix' = the old stands, navy blue and slate grey scattered about half and half"""
    h = (math.sin(j * 12.9898 + b * 78.233) * 43758.5453) % 1.0
    if pal == 'blue': return 'seat_navyblue'
    if pal == 'mix': return 'seat_slategrey' if h < 0.5 else 'seat_navyblue'
    return 'seat_charcoal'


def seat_rows(bs, prof, k, n, aisle=12.0, gap=1.1, pal='mix'):
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
                SEAT_COL[0] = seat_colour(pal, j, n, b); seat(pol(b, rr), t, o, zz)
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


# ---------------- stand kinds ----------------
def single(S, mb, mr):
    bs = brange(S); M = S['mats']; zs0, zs1 = S['z_seat']; zr0, zr1 = S['z_roof']
    def geo(b):
        rf = fence_r(b % 360); ri, ro = interp(S['roof'], b); rs0 = rf + S['seat_front']; rb = ro - S['back_in']
        return rf, ri, ro, rs0, rb
    def prof(b):
        rf, ri, ro, rs0, rb = geo(b); zb = zr1 - 0.6 - (zr1 - zr0) * (S['back_in'] / (ro - ri))
        # front wall up, seats up the rake, back wall of the bowl up to the roof, cap, facade down
        if S.get('nose'):  # open undercroft (2026 ground-floor photo): rake underside is the ceiling, blockwork wall set deep
            N = S['nose']; rw = rb - N.get('deep', 8.0); zw = zs0 + (zs1 - zs0) * (rw - rs0) / (rb - 0.4 - rs0) - 0.8
            return [(rs0, 0.0), (rs0, zs0), (rb - 0.4, zs1), (rb - 0.4, zb), (rb, zb), (rb, N['under']), (rw, zw), (rw, 0.0)]
        return [(rs0, 0.0), (rs0, zs0), (rb - 0.4, zs1), (rb - 0.4, zb), (rb, zb), (rb, 0.0)]
    tail = ['conc_wall', 'roof_soffit', 'conc_block'] if S.get('nose') else [M['back']]
    n = nrows(prof, bs, 1); tp, tm = terrace(prof, [M['front'], M['seat'], 'conc_wall', 'conc_wall'] + tail, [(1, n)])
    strip(mb, bs, tp, tm, -1); seat_rows(bs, prof, 1, n, pal=S.get('pal', 'mix'))
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        endcap(mb, b, tp(b), 'conc_wall', sg)
    ribs = roof_strip(S, bs, geo, mr)
    if S.get('nose'): nose(S, bs, geo, mr, mb)
    if S.get('brace'): bracing(S, ribs, geo, mr)

def nose(S, bs, geo, mr, mb):
    """PTA 2017 photos 13/15: the roof rolls over the back in a quarter-round nose of radius R onto a triangle-panel band,
    which stands on columns over an open, recessed ground floor (band bottom at z 'under')"""
    N = S['nose']; R, zu = N['R'], N['under']; zr1 = S['z_roof'][1]; M = S['mats']; up = np.array([0, 0, 1.0]); K = 8
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]; roa, rob = geo(ba)[2], geo(bb)[2]; bm = math.radians(0.5 * (ba + bb)); rad = np.array([math.sin(bm), math.cos(bm), 0.0])
        ua, ub = math.radians(ba) * roa / 6, math.radians(bb) * rob / 6
        for k in range(K):
            t0, t1 = k * math.pi / 2 / K, (k + 1) * math.pi / 2 / K; tm = 0.5 * (t0 + t1)
            pa = lambda r0, t: (r0 + R * math.sin(t), zr1 - R + R * math.cos(t))
            (a0r, a0z), (a1r, a1z), (b0r, b0z), (b1r, b1z) = pa(roa, t0), pa(roa, t1), pa(rob, t0), pa(rob, t1)
            oriented(mr, [P3(ba, a0r, a0z), P3(bb, b0r, b0z), P3(bb, b1r, b1z), P3(ba, a1r, a1z)], 'fascia', rad * math.sin(tm) + up * math.cos(tm),
                     [(ua, t0 * R / 6), (ub, t0 * R / 6), (ub, t1 * R / 6), (ua, t1 * R / 6)])
        ra, rb_ = roa + R, rob + R; zt = zr1 - R
        if 'cell' not in N:
            tu, tv = TILE.get(M['back'], (6, 12)); va, vb = math.radians(ba) * ra / tu, math.radians(bb) * rb_ / tu
            oriented(mb, [P3(ba, ra, zu), P3(bb, rb_, zu), P3(bb, rb_, zt), P3(ba, ra, zt)], M['back'], rad, [(va, zu / tv), (vb, zu / tv), (vb, zt / tv), (va, zt / tv)])
        else:  # dark backing behind the open triangles
            oriented(mb, [P3(ba, ra - 0.4, zu), P3(bb, rb_ - 0.4, zu), P3(bb, rb_ - 0.4, zt), P3(ba, ra - 0.4, zt)], 'tri_void', rad)
        rba, rbb = geo(ba)[4], geo(bb)[4]
        oriented(mb, [P3(ba, rba, zu), P3(bb, rbb, zu), P3(bb, rb_, zu), P3(ba, ra, zu)], 'roof_soffit', -up)
    if 'cell' in N: tri_band(N, bs, geo, R, zu, zr1 - R, mb)
    b = bs[0] + math.degrees(0.5 * N.get('col', 6.0) / geo(bs[0])[2])
    while b <= bs[-1]:
        ro = geo(b)[2]; rc = ro + R - 0.8
        mb.cyl(pol(b, rc), 0.35, 0.0, zu - 1.2, 'steel_white', n=16)
        if 'cell' in N:  # Y head: two raked arms from the column top out to the band bottom (photo: V-branching columns)
            for sg in (-1, 1):
                mb.beam(P3(b, rc, zu - 1.2), P3(b + sg * math.degrees(1.6 / rc), rc + 0.3, zu), 0.25, 0.25, 'steel_white')
            mb.beam(P3(b, rc, zu - 1.2), P3(b, rc, zu), 0.3, 0.3, 'steel_white')
        b += math.degrees(N.get('col', 6.0) / ro)

def tri_band(N, bs, geo, R, z0, z1, mb):
    """3D folded triangle panels (photo measure: cells cw x ch, each cut by its two diagonals into 4 triangles whose shared
    centre is pushed out 'fold' m; a seeded share 'dark' of triangles are open (dark glass behind), the rest white)"""
    cw, ch, fold, dk = N['cell'][0], N['cell'][1], N.get('fold', 0.35), N.get('dark', 0.4)
    rows = max(1, round((z1 - z0) / ch)); ch = (z1 - z0) / rows
    rng = np.random.default_rng(int(bs[0] * 10))
    b = bs[0]
    while True:
        r = geo(b)[2] + R; b2 = b + math.degrees(cw / r)
        if b2 > bs[-1]: break
        r2 = geo(b2)[2] + R; bm = 0.5 * (b + b2); rm = 0.5 * (r + r2); a = math.radians(bm); out = np.array([math.sin(a), math.cos(a), 0.0])
        for k in range(rows):
            za, zb = z0 + k * ch, z0 + (k + 1) * ch; c = P3(bm, rm + fold, 0.5 * (za + zb))
            corners = [P3(b, r, za), P3(b2, r2, za), P3(b2, r2, zb), P3(b, r, zb)]
            for j in range(4):
                p, q = corners[j], corners[(j + 1) % 4]
                ci = int(round((b - bs[0]) * math.pi / 180 * r / cw))
                if (j % 2) == ((ci + k) % 2):  # regular bow-tie diamonds (2026 aerials): side pair open on even cells, top/bottom on odd  # open triangle: white frame edges only
                    for u, v in ((p, c), (q, c)): mb.beam(u, v, 0.08, 0.08, 'paint_white')
                else:
                    oriented(mb, [p, q, c], 'paint_white', out)
            mb.beam(corners[0], corners[1], 0.12, 0.12, 'paint_white'); mb.beam(corners[0], corners[3], 0.12, 0.12, 'paint_white')
        b = b2

def roof_strip(S, bs, geo, mr):
    """roof deck from ri (z_roof[0]) to ro (z_roof[1]), 0.5 m thick, white trusses on top every S['rib'] metres"""
    zr0, zr1 = S['z_roof']; th = 0.5; M = S['mats']; sol = S.get('solar', [])
    def deck(b):
        rf, ri, ro, rs0, rb = geo(b); return ri, ro
    def roofmat(b):
        for b0, b1, f0, f1 in sol:
            if b0 <= b < b1: return 'solar_zone'
        return M['roof']
    # u = true distance along the deck's mid line (bearing x radius is wrong on straight stands, whose polar radius grows to the ends)
    sm = [0.0]
    for i in range(len(bs) - 1):
        sm.append(sm[-1] + float(np.linalg.norm(np.subtract(P3(bs[i + 1], sum(deck(bs[i + 1])) / 2, 0), P3(bs[i], sum(deck(bs[i])) / 2, 0)))))
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
            ua, ub = sm[i] / tu, sm[i + 1] / tu
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
    sp = S.get('rib', 0); ribs = []
    if not sp: return ribs
    b, b_end = bs[0], bs[-1]
    while True:
        ri, ro = deck(b); rm = 0.5 * (ri + ro); step = math.degrees(sp / rm)
        b += step if b != bs[0] else 0.35 * step
        if b > b_end - 0.2 * step: break
        ri, ro = deck(b); ribs.append(b)
        z = lambda r: zr0 + (zr1 - zr0) * (r - ri) / (ro - ri)
        pk = ri + 0.4 * (ro - ri); H = 2.4; o = 0.15
        if S.get('rib_under'): H, o = -2.4, -th - 0.15   # aerial: the old roofs are flat white on top, trusses hang underneath
        re_ = (ro - S.get('back_in', 0) - 0.4) if S.get('rib_under') else ro - 0.2   # under-trusses stop inside the back wall
        A = P3(b, ri + 0.2, z(ri + 0.2) + o); K = P3(b, pk, z(pk) + o + H); Bp = P3(b, re_, z(re_) + o)
        mr.beam(A, K, 0.35, 0.35, 'steel_white'); mr.beam(K, Bp, 0.35, 0.35, 'steel_white')
        mr.beam(A, Bp, 0.25, 0.25, 'steel_white')
        for f in (0.2, 0.55, 0.8):
            r1 = ri + f * (re_ - ri); zt = o + ((z(r1) + H * (r1 - ri) / (pk - ri)) if r1 < pk else (z(r1) + H * (re_ - r1) / (re_ - pk)))
            mr.beam(P3(b, r1, z(r1) + o), P3(b, r1, zt), 0.18, 0.18, 'steel_white')
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
        P = [(rs0, 0.0), (rs0, zs0), (rl, zs1), (rl, zb1), (rl + 0.6, zb1), (rl + 0.6, zu0), (rb - 0.4, zu1), (rb - 0.4, zb), (rb, zb)]
        if not OB: return P + [(rb, 0.0)]
        rp = rl + 0.6 + OB   # open back (2026 design render, press/wm): rake soffit down over the concourse to a clad podium
        return P + [(rb, zu1 - 1.0), (rp, zb1 + 0.5), (rp, 0.0)]
    OB = S.get('open_back', 0)
    n1, n5 = nrows(prof, bs, 1), nrows(prof, bs, 5)
    mats = [M['front'], M['seat'], M['box'], 'conc_wall', 'conc_wall', M['seat'], 'conc_wall', 'conc_wall']
    mats += ['steel_galv', 'conc_wall', M['back']] if OB else [M['back']]
    tp, tm = terrace(prof, mats, [(1, n1), (5, n5)])
    strip(mb, bs, tp, tm, -1); seat_rows(bs, prof, 1, n1, pal='blue'); seat_rows(bs, prof, 5, n5, pal='fade')
    if OB:   # raked steel columns from the concourse up to the soffit, one per rafter bay
        b = bs[0]
        while b <= bs[-1] + 1e-6:
            rf, ri, ro, rs0, rb = geo(b); rp = rs0 + S['lower_back'] + 0.6 + OB; rc = rb - 2.0
            zc = (zu1 - 1.0) + (S['box'][1] + 0.5 - (zu1 - 1.0)) * (rb - rc) / (rb - rp)
            mr.beam(P3(b, rc - 1.0, 0.0), P3(b, rc, zc), 0.45, 0.45, 'steel_galv')
            b += math.degrees(S.get('raft', 4.5) * 2 / rb)
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        endcap(mb, b, tp(b), 'conc_wall', sg)
    (arch_roof if S.get('arch') is not None else roof_strip)(S, bs, geo, mr)


def arch_roof(S, bs, geo, mr):
    """Mars 2026 stands (press/aus_new.jpg): a curved steel roof whose leading edge rises S['arch'] m from the ends to
    the middle of the stand, cambered S['camber'] m front to back, timber rafters under it every S['raft'] m on steel
    props, and a steel rim fascia on the front edge"""
    zr0, zr1 = S['z_roof']; th = 0.4; M = S['mats']; b0, b1 = bs[0], bs[-1]; ar = S['arch']; cb = S.get('camber', 1.0); K = 6
    def Z(b, u):
        t = (b - b0) / (b1 - b0); lift = -ar * (2 * t - 1) ** 2
        return zr0 + (zr1 - zr0) * u + cb * 4 * u * (1 - u) + lift
    def R(b, u):
        rf, ri, ro, rs0, rb = geo(b); return ri + (ro - ri) * u
    up = np.array([0, 0, 1.0]); dn = -up
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]; rm = 0.5 * (R(ba, 0.5) + R(bb, 0.5))
        for k in range(K):
            u0, u1 = k / K, (k + 1) / K
            q = [P3(ba, R(ba, u0), Z(ba, u0)), P3(bb, R(bb, u0), Z(bb, u0)), P3(bb, R(bb, u1), Z(bb, u1)), P3(ba, R(ba, u1), Z(ba, u1))]
            ua, ub = math.radians(ba) * rm / 6, math.radians(bb) * rm / 6
            uv = [(ua, R(ba, u0) / 6), (ub, R(bb, u0) / 6), (ub, R(bb, u1) / 6), (ua, R(ba, u1) / 6)]
            oriented(mr, q, M['roof'], up, uv)
            oriented(mr, [p - np.array([0, 0, th]) for p in q], 'roof_soffit', dn, uv)
        bm = math.radians(0.5 * (ba + bb)); rad = np.array([math.sin(bm), math.cos(bm), 0.0])
        oriented(mr, [P3(ba, R(ba, 0), Z(ba, 0) - th - 0.5), P3(bb, R(bb, 0), Z(bb, 0) - th - 0.5), P3(bb, R(bb, 0), Z(bb, 0) + 0.3), P3(ba, R(ba, 0), Z(ba, 0) + 0.3)], 'steel_galv', -rad)
        oriented(mr, [P3(ba, R(ba, 1), Z(ba, 1) - th - 0.3), P3(bb, R(bb, 1), Z(bb, 1) - th - 0.3), P3(bb, R(bb, 1), Z(bb, 1)), P3(ba, R(ba, 1), Z(ba, 1))], 'fascia', rad)
    for b, sg in ((b0, -1), (b1, 1)):
        a = math.radians(b); tan = np.array([math.cos(a), -math.sin(a), 0.0]) * sg
        for k in range(K):
            u0, u1 = k / K, (k + 1) / K
            oriented(mr, [P3(b, R(b, u0), Z(b, u0) - th - 0.3), P3(b, R(b, u1), Z(b, u1) - th - 0.3), P3(b, R(b, u1), Z(b, u1) + 0.3), P3(b, R(b, u0), Z(b, u0) + 0.3)], 'steel_white', tan)
    sp = S.get('raft', 4.5); b = b0
    while b <= b1 + 1e-6:
        pts = [P3(b, R(b, u), Z(b, u) - th - 0.35) for u in np.linspace(0.02, 0.98, 7)]
        for p, q in zip(pts[:-1], pts[1:]): mr.beam(p, q, 0.25, 0.7, 'timber')
        rf, ri, ro, rs0, rb = geo(b); um = 0.62
        foot = P3(b, rb - 0.6, S['z_upper'][1] + 0.4); mr.beam(foot, P3(b, R(b, um), Z(b, um) - th - 0.7), 0.35, 0.35, 'steel_galv')
        mr.beam(foot, P3(b, R(b, 0.25), Z(b, 0.25) - th - 0.7), 0.25, 0.25, 'steel_galv')
        b += math.degrees(sp / R(b, 0.5))


def bank(S, mb):
    """southern viewing area (2026 'standing-room viewing embankment'; earthworks on GE 2025-12-28 at these bearings, no
    photo of the finished bank): concrete kerb wall at the seat line, grass slope rising to z_top at the back, concrete
    path along the crest"""
    bs = brange(S); zt = S['z_top']
    def prof(b):
        rf = fence_r(b % 360); r0 = rf + S['seat_front']; rb = interp(S['back'], b)[0]
        return [(r0, 0.0), (r0, 0.6), (rb - 2.0, zt), (rb, zt), (rb, 0.0)]
    tp, tm = terrace(prof, ['conc_wall', 'grass_bank', 'paving', 'conc_wall'], [])
    strip(mb, bs, tp, tm, -1)
    for b, sg in ((bs[0], -1), (bs[-1], 1)): endcap(mb, b, tp(b), 'conc_wall', sg)


def open_stand(S, mb):
    bs = brange(S); M = S['mats']; zs0, zs1 = S['z_seat']
    def prof(b):
        rf = fence_r(b % 360); rs0 = rf + S['seat_front']; rb = interp(S['back'], b)[0]
        return [(rs0, 0.0), (rs0, zs0), (rb - 0.4, zs1), (rb - 0.4, zs1 + 1.1), (rb, zs1 + 1.1), (rb, 0.0)]
    n = nrows(prof, bs, 1); tp, tm = terrace(prof, [M['front'], M['seat'], 'conc_wall', 'conc_wall', M['back']], [(1, n)])
    strip(mb, bs, tp, tm, -1); seat_rows(bs, prof, 1, n, pal=S.get('pal', 'mix'))
    for b, sg in ((bs[0], -1), (bs[-1], 1)):
        endcap(mb, b, tp(b), 'conc_wall', sg)


def block(S, mb, mr):
    bs = brange(S); M = S['mats']; zs0, zs1 = S['z_seat']; H = S['z_block']
    def prof(b):
        rf = fence_r(b % 360); rs0 = rf + S['front_seats'][0]; r1, r2 = interp(S['block'], b)
        return [(rs0, 0.0), (rs0, zs0), (r1, zs1), (r1, H), (r2, H), (r2, 0.0)]
    n = nrows(prof, bs, 1); tp, tm = terrace(prof, [M['front'], M['seat'], M['back'], M['roof'], M['back']], [(1, n)])
    strip(mb, bs, tp, tm, -1); seat_rows(bs, prof, 1, n, pal=S.get('pal', 'mix'))
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
    """NE gap between the North and Eastern stands: the scoreboard on the NE tower, its round base, two pavilions"""
    E = D.get('extras'); mb = MB('extras')
    if not E: return
    B = E['board']; L, R = np.array(B['left'], float), np.array(B['right'], float); z0, z1 = B['z']
    c, u, n_in, wd = scoreboard(mb, L, R, B['in'], z0, z1, B['depth'], B['frame'], B['back'], [(0.0, 1.0, 'screen_off')], B['rim'], B.get('back_rim'))
    for k in (-1, 1):   # two legs down to the base
        p = c + u * k * (wd / 2 - 1.5); mb.box(p, 0.6, 0.6, z0, math.degrees(math.atan2(u[1], u[0])), 'steel_galv')
    W = E.get('board_sw')
    if W:   # the older SW scoreboard on the SW corner building: LED screen plus a dark side panel toward the Gunns
        b0, b1 = W['b']; L, R = np.array(pol(b0, W['r'])), np.array(pol(b1, W['r'])); z0, z1 = W['z']
        c, u, n_in, wd = scoreboard(mb, L, R, 0.0, z0, z1, W['depth'], W['frame'], W['back'],
                                    [(0.0, W['split'], 'screen_off'), (W['split'], 1.0, 'board_side')], W['rim'])
        ang = math.degrees(math.atan2(u[1], u[0])); back = c - n_in * (W['depth'] / 2 + 0.03)
        for k in (-1, 1):   # maroon side posts and a white top beam on the back (GE l000, l180)
            p = back + u * k * (wd / 2 - 0.25); mb.box(p, 0.5, 0.3, z1 - z0 + 0.2, ang, W['post'], z0=z0 - 0.1)
        mb.box(back, wd, 0.32, 0.5, ang, 'paint_white', z0=z1 - 0.4)
        mb.box(c, wd - 1.0, W['depth'] * 0.8, z0 - W['base'], ang, W['back'], z0=W['base'])
    G = E['ring']; mb.cyl(G['c'], G['r'], 0, G['h'], 'conc_wall', n=36, top='paving')
    for P in E['pavilions']:
        a = math.radians(P['a']); uu = np.array([math.cos(a), math.sin(a)]); vv = np.array([-uu[1], uu[0]]); cc = np.array(P['c'], float)
        if np.dot(vv, -cc) < 0: vv = -vv            # vv points to the pitch
        h, hb, Lp, Wp = P['h'], P['bank'], P['L'], P['W']
        mb.box(cc, Lp, Wp, h, P['a'], P['mat'], mtop='roof_flat')
        # seat bank on the roof: rises from the pitch edge to a rear wall at the middle line
        f0, f1 = cc + vv * Wp / 2, cc
        q = lambda base_, s_, z: (*(base_ + uu * s_ * Lp / 2), z)
        pav_bank(mb, cc, uu, vv, Lp, Wp / 2, h, hb)
        oriented(mb, [q(f1, -1, h), q(f1, 1, h), q(f1, 1, h + hb + 0.4), q(f1, -1, h + hb + 0.4)], 'panel_blue', np.array([*(-vv), 0.0]))
        oriented(mb, [q(f1, -1, h + hb + 0.4), q(f1, 1, h + hb + 0.4), q(f1 + vv * 0.2, 1, h + hb + 0.4), q(f1 + vv * 0.2, -1, h + hb + 0.4)],
                 'paint_white', np.array([0, 0, 1.0]))
    for G in D.get('signs', []):   # flat panel 5 cm proud of the facade, facing the pitch
        c = np.array(G['c'], float); u = np.array(G['u'], float); n = np.array([u[1], -u[0]])
        if np.dot(n, -c) < 0: n = -n
        c = c + n * 0.05; a, b = c - u * G['w'] / 2, c + u * G['w'] / 2; z0, z1 = G['z0'], G['z0'] + G['h']
        oriented(mb, [(*a, z0), (*b, z0), (*b, z1), (*a, z1)], G['mat'], np.array([*n, 0.0]), [(0, 0), (1, 0), (1, 1), (0, 1)])
    mb.build(col)

def buildings(col):
    """club buildings traced from the GE top view: prism walls, flat roof, rooftop plant, round drums"""
    mb = MB('buildings')
    for B in D.get('buildings', []):
        mb.prism([tuple(q) for q in B['poly']], 0.0, B['z'], B['wall'], top=B['roof'])
        for c, L, W, h, a in B.get('plant', []):
            mb.box(tuple(c), L, W, h, a, 'paint_white', z0=B['z'])
        for c, r, z in B.get('drums', []):
            mb.cyl(tuple(c), r, 0.0, z, B.get('drum', 'conc_wall'), n=36, top=B['roof'])
    mb.build(col)

def build_all():
    clear(); col = bpy.context.scene.collection
    global SEATS, POSTS
    mb = MB('stands'); mr = MB('roofs'); SEATS = MB('seats'); SEATS.smooth = True; POSTS = MB('seat_posts'); SEAT_XF.clear()
    for S in D['stands']:
        {'bank': lambda: bank(S, mb), 'single': lambda: single(S, mb, mr), 'two_tier': lambda: two_tier(S, mb, mr),
         'open': lambda: open_stand(S, mb), 'block': lambda: block(S, mb, mr)}[S['kind']]()
    mb.build(col); mr.build(col)
    fence(col); extras(col); buildings(col); SEATS.build(col); POSTS.build(col)
    if not os.environ.get('NOCONC'): concourse(col)
    if D['towers']:
        mt = MB('towers')
        for T in D['towers']:
            tower(mt, T)
        mt.build(col)
