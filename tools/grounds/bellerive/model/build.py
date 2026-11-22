# Bellerive Oval (Ninja Stadium, Hobart) exterior, as it is today, built from the Google Earth straight-down ortho
# (plan: fence, roof edges, building footprints) and the oblique Google Earth views (heights). Data: model/bellerive.json.
# Runs inside Blender: import build; build.build_all(). Frame: x east, y north, z up from the field, metres.
import bpy, math, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from mb import MB, rect, ccw, TILE, Frame
D = json.load(open(os.path.join(HERE, 'bellerive.json')))
STEP = 0.5


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


def periodic(tab):
    """[[bearing, v...], ...] -> f(bearing) -> [v...], linear, periodic over 360"""
    t = np.array(sorted(tab), float); b = np.concatenate([t[:, 0] - 360, t[:, 0], t[:, 0] + 360])
    cols = [np.concatenate([t[:, k]] * 3) for k in range(1, t.shape[1])]
    return lambda q: [float(np.interp(q % 360, b, c)) for c in cols]


def pol(b, r):
    a = math.radians(b); return (r * math.sin(a), r * math.cos(a))


def P3(b, r, z):
    return (*pol(b, r), z)


FENCE = periodic(D['fence'])
def rf(b): return FENCE(b)[0]


def arc(b0, b1):
    n = max(1, int(round(abs(b1 - b0) / STEP))); return list(np.linspace(b0, b1, n + 1))


def strip(mb, bs, A, B, m, tu=None):
    """Quad strip between two section points A(b)->(r,z) and B(b)->(r,z) over bearings bs. UV: u = arc length at the
    strip's mid radius / tile, v = length along the section / tile, so seat rows and ribs run round the ground."""
    tu_, tv = TILE.get(m, (1, 1)); tu = tu or tu_; kk = math.pi / 180
    for b0, b1 in zip(bs, bs[1:]):
        a0, a1, c0, c1 = A(b0), A(b1), B(b0), B(b1)
        rm = 0.25 * (a0[0] + a1[0] + c0[0] + c1[0]); L = math.hypot(c0[0] - a0[0], c0[1] - a0[1])
        u0 = b0 * kk * rm / tu; u1 = b1 * kk * rm / tu
        mb.face([P3(b0, *a0), P3(b1, *a1), P3(b1, *c1), P3(b0, *c0)], m,
                uv=[(u0, 0), (u1, 0), (u1, L / tv), (u0, L / tv)])


def endcap(mb, b, S, m, flip=False):
    """Close a swept section at bearing b: S = [(r, z), ...] polygon in the (r, z) plane."""
    P = [P3(b, r, z) for r, z in S]
    if flip: P = P[::-1]
    poly2 = [(r, z) for r, z in S]
    from mb import earclip
    sgn = 1 if sum(poly2[i][0] * poly2[(i + 1) % len(poly2)][1] - poly2[(i + 1) % len(poly2)][0] * poly2[i][1]
                   for i in range(len(poly2))) > 0 else -1
    idx = {tuple(p): i for i, p in enumerate(poly2)}
    for tri_ in earclip(poly2 if sgn > 0 else poly2[::-1]):
        q = [P3(b, r, z) for r, z in tri_]
        mb.face(q[::-1] if flip else q, m)


def sweep(mb, bs, sec, cap0=True, cap1=True, capm='conc_grey'):
    """sec(b) -> [(r, z, material-of-segment-to-this-point), ...] with a fixed length; faces each segment over bs."""
    S = [sec(b) for b in bs]; n = len(S[0])
    for k in range(1, n):
        m = S[0][k][2]
        if m is None: continue
        strip(mb, bs, lambda b, k=k: sec(b)[k - 1][:2], lambda b, k=k: sec(b)[k][:2], m)
    outline = lambda s: [(p[0], p[1]) for p in s] + [(s[-1][0], 0.0), (s[0][0], 0.0)]
    if cap0: endcap(mb, bs[0], outline(S[0]), capm, flip=False)
    if cap1: endcap(mb, bs[-1], outline(S[-1]), capm, flip=True)


# ---------------- the main stand: Ricky Ponting (west) + David Boon (south), one continuous bowl ----------------
# Each tier is real stepped rows (a riser and a tread a row), not a slope painted with seats: the seats are
# instanced 3D shells on the treads (seat_list(), written beside the glb). The row count is fixed within a
# sweep, so the bowl is swept in two parts that meet at SPLIT, the Boon / Ponting join: the Boon's rows
# (S counts) and the Ponting's (W counts) each run at their own pitch. ROWS: (lower, upper).
SPLIT = 214.0
ROWS = {'S': (10, 9), 'W': (12, 16)}


def stepped(r0, z0, r1, z1, n, mt='tread', mr='riser'):
    """n rows from (r0, z0) up to (r1, z1): a riser up, then a tread out, each row."""
    out = []; run = (r1 - r0) / n; rise = (z1 - z0) / n
    for k in range(n):
        out += [(r0 + k * run, z0 + (k + 1) * rise, mr), (r0 + (k + 1) * run, z0 + (k + 1) * rise, mt)]
    return out


def main_tiers(b):
    """The main stand's two tiers at bearing b: [(r0, z0, r1, z1), (r0, z0, r1, z1)] (lower, upper)."""
    d1, z1, w, rz, d2, z2, zb = periodic(D['main']['tiers'])(b)
    f = rf(b); fz = D['fence_h']
    return [(f + 0.6, fz, f + d1, z1), (f + d1 + w, z1 + rz, f + d2, z2)]


def main_sec_n(nl, nu):
    def sec(b):
        d1, z1, w, rz, d2, z2, zb = periodic(D['main']['tiers'])(b)
        f = rf(b); fz = D['fence_h']
        (a0, b0, a1, b1), (c0, e0, c1, e1) = main_tiers(b)
        return ([(f, 0.0, None), (f, fz, 'fence'), (f + 0.6, fz, 'conc_grey')] + stepped(a0, b0, a1, b1, nl)
                + [(f + d1 + w, z1, 'conc_grey'), (f + d1 + w, z1 + rz, 'ribbon' if rz > 2.0 else 'tier_wall')] + stepped(c0, e0, c1, e1, nu)
                + [(f + d2 + 1.2, z2, 'conc_grey'), (f + d2 + 1.2, zb, 'backwall')])
    return sec


def main_sec(b):
    return main_sec_n(*ROWS['S' if b < SPLIT else 'W'])(b)


def main_parts():
    M = D['main']; return [(arc(M['b0'], SPLIT), 'S'), (arc(SPLIT, M['b1']), 'W')]


PONTING_B0 = 212.0


def arc_frame(b0, b1, r_of):
    """Arc-length frame along a facade: s (m along the wall at its own radius) -> bearing, and a point at
    (s, z, out) with `out` metres outward of the wall line r_of(b)."""
    bs = np.linspace(b0, b1, 721); rr = np.array([r_of(b) for b in bs])
    ss = np.concatenate([[0.0], np.cumsum(np.radians(np.diff(bs)) * 0.5 * (rr[1:] + rr[:-1]))])
    bear = lambda s_: float(np.interp(s_, ss, bs))
    def P(s_, z, out=0.0):
        b = bear(s_); return P3(b, r_of(b) + out, z)
    return ss[-1], bear, P


def ribbon(mb, P, s0, s1, z0, z1, out, m, step=1.5):
    """A wall band between s0 and s1 (z0..z1), `out` m off the wall line, in short flat pieces round the arc."""
    n = max(1, int(math.ceil((s1 - s0) / step)))
    for k in range(n):
        a, b_ = s0 + (s1 - s0) * k / n, s0 + (s1 - s0) * (k + 1) / n
        mb.face([P(a, z0, out), P(b_, z0, out), P(b_, z1, out), P(a, z1, out)], m)


def hband(mb, P, s0, s1, z, out0, out1, m, step=1.5):
    """A horizontal band at height z from `out0` to `out1` off the wall line (a soffit or a ledge)."""
    n = max(1, int(math.ceil((s1 - s0) / step)))
    for k in range(n):
        a, b_ = s0 + (s1 - s0) * k / n, s0 + (s1 - s0) * (k + 1) / n
        mb.face([P(a, z, out0), P(b_, z, out0), P(b_, z, out1), P(a, z, out1)], m)


def post(mb, P, s_, z0, z1, out, w, d, m):
    """A square column or mullion w (along the wall) x d (out from it) at s_."""
    q = [(s_ - w / 2, out), (s_ + w / 2, out), (s_ + w / 2, out + d), (s_ - w / 2, out + d)]
    for (a, o1), (b_, o2) in zip(q, q[1:] + q[:1]):
        mb.face([P(a, z0, o1), P(b_, z0, o2), P(b_, z1, o2), P(a, z1, o1)], m)
    mb.face([P(a, z1, o) for a, o in q], m)


def boon_facade(mb, b0, b1, fac, zfac):
    """Boon Stand outside (GE cf_195): a deep pale cladding band from 6.2 m to the roof, and under it the
    concourse glazing set 1.6 m back behind white columns every 7.2 m, mullions every 1.8 m."""
    L, bear, P = arc_frame(b0, b1, fac)
    zt = zfac(0.5 * (b0 + b1)); zb = 6.2; rec = -1.6
    ribbon(mb, P, 0, L, zb, zt, 0.0, 'boon_band')
    hband(mb, P, 0, L, zb, 0.0, rec, 'roof_soffit')
    ribbon(mb, P, 0, L, 0.0, zb, rec, 'boon_glass')
    hband(mb, P, 0, L, 0.6, rec, rec + 0.35, 'conc_grey')                 # the glazing's plinth
    ribbon(mb, P, 0, L, 0.0, 0.6, rec + 0.35, 'conc_grey')
    n = int(L // 7.2)
    for k in range(n + 1):
        post(mb, P, k * L / n, 0.0, zb, -0.45, 0.45, 0.45, 'steel_white')
    m = int(L // 1.8)
    for k in range(m):
        post(mb, P, (k + 0.5) * L / m, 0.6, zb, rec, 0.1, 0.14, 'steel_white')
    for z in (3.2,):                                                        # transom
        hband(mb, P, 0, L, z, rec, rec + 0.12, 'steel_white')


def _cuts(L, lo, hi, rng, off=0.0):
    """Irregular stations along 0..L: gaps between lo and hi metres, the ends exactly 0 and L."""
    out = [0.0]; s_ = off if off > 0 else rng.uniform(lo, hi)
    while s_ < L - lo * 0.6:
        out.append(s_); s_ += rng.uniform(lo, hi)
    return out + [L]


def _zip(A, B):
    """Triangles between two rows of stations A and B (each a sorted list of (s, node)), the way a
    folded skin is cut: always step along whichever row's next station comes first."""
    tris = []; i = j = 0
    while i < len(A) - 1 or j < len(B) - 1:
        if j >= len(B) - 1 or (i < len(A) - 1 and A[i + 1][0] <= B[j + 1][0]):
            tris.append((A[i][1], A[i + 1][1], B[j][1])); i += 1
        else:
            tris.append((A[i][1], B[j + 1][1], B[j][1])); j += 1
    return tris


def ponting_skin(mb, b0, b1, fac, zfac):
    """Ricky Ponting Stand outside (GE cf_240, cf_270): a folded skin of big flat panels, cut irregularly.
    Five rows of nodes, each row's stations spaced at random (seeded) and in and out of the wall line, are
    zipped into triangles, so no two panels match: a pale silver crown folding out from the roof edge, a
    band of big blue glass and pale panels whose bottom edge rises and falls, then pale facets tucking back
    in over the concourse. Under it the glazed concourse sits 2.4 m back."""
    L, bear, P = arc_frame(b0, b1, fac)
    zt = zfac(0.5 * (b0 + b1)); rng = np.random.default_rng(240)
    # nodes are (s, z, out); a row is a list of (s, node)
    row = lambda ss, zf, out: [(s_, (s_, zf(), out)) for s_ in ss]
    r0 = row(_cuts(L, 10.0, 16.0, rng), lambda: zt, 0.0)
    mids = [0.0] + [0.5 * (r0[k][0] + r0[k + 1][0]) + rng.uniform(-1.5, 1.5) for k in range(len(r0) - 1)] + [L]
    r1 = row(mids, lambda: zt - 3.2 + rng.uniform(-0.4, 0.4), 0.9)
    r2 = row(_cuts(L, 7.0, 14.0, rng), lambda: zt - 6.0 + rng.uniform(-0.6, 0.6), 1.2)
    r3 = row(_cuts(L, 6.0, 13.0, rng), lambda: rng.uniform(8.0, 11.5), 0.7)
    r4 = row(_cuts(L, 8.0, 16.0, rng), lambda: 4.6, -1.4)
    # the glass band's colours run in irregular lengths: mostly blue glass, some sky, grey and pale panels
    segs = _cuts(L, 4.0, 13.0, rng)
    cols = rng.choice(['skin_blue', 'skin_blue', 'skin_blue', 'skin_sky', 'skin_grey', 'skin_pale', 'skin_pale'],
                      len(segs))
    for A, B, m1, m2 in [(r0, r1, 'skin_silver', 'skin_silver2'), (r1, r2, 'skin_silver2', 'skin_pale'),
                         (r2, r3, None, None), (r3, r4, 'skin_pale', 'skin_silver2')]:
        for n_, t in enumerate(_zip(A, B)):
            (s1, z1, _), (s2, z2, _), (s3, z3, _) = t
            if (s2 - s1) * (z3 - z1) - (s3 - s1) * (z2 - z1) < 0:    # face out: counter-clockwise seen from outside
                t = (t[0], t[2], t[1])
            if m1 is None:
                m = str(cols[max(0, int(np.searchsorted(segs, (s1 + s2 + s3) / 3.0)) - 1)])
            else:
                m = m1 if n_ % 2 == 0 else m2
            mb.face([P(*q) for q in t], m)
    # concourse under the skin: soffit back from the lowest nodes, then dark glazing behind columns
    hband(mb, P, 0, L, 4.6, -1.4, -2.4, 'roof_soffit')
    ribbon(mb, P, 0, L, 0.0, 4.6, -2.4, 'backwall')
    n = max(2, int(round(L / 12.5)))
    for k in range(n + 1):
        post(mb, P, k * L / n, 0.0, 4.6, -2.2, 0.5, 0.5, 'steel_white')
    # the skin's ends, closed against the stand
    for s_ in (0.0, L):
        mb.face([P(s_, 0.0, -2.4), P(s_, 0.0, 0.0), P(s_, zt, 0.0), P(s_, 4.6, -2.4)], 'skin_silver2')


def main_all(col):
    M = D['main']; mb = MB('main_stand'); bs = arc(M['b0'], M['b1'])
    for part, k in main_parts():
        sweep(mb, part, main_sec_n(*ROWS[k]))
    R = periodic(M['roof'])
    # roof: front fascia, sloping white deck, outer fascia, soffit back to the stand's back wall
    rin = lambda b: (R(b)[0], R(b)[2]); rout = lambda b: (R(b)[1], R(b)[3])
    th = M['roof_th']
    strip(mb, bs, lambda b: (R(b)[0], R(b)[2] - th), lambda b: (R(b)[0], R(b)[2]), 'roof_fascia')
    for b0, b1, m in M['roofmats']:
        bb = [b for b in bs if b0 - 1e-6 <= b <= b1 + 1e-6]
        if len(bb) > 1: strip(mb, bb, rin, rout, m)
    strip(mb, bs, lambda b: (R(b)[1], R(b)[3]), lambda b: (R(b)[1], R(b)[3] - th), 'roof_fascia')
    strip(mb, bs, lambda b: (R(b)[1], R(b)[3] - th), lambda b: (R(b)[0], R(b)[2] - th), 'roof_soffit')
    # back of the stand: the concourse block from the back wall out to the facade, its top under the roof
    def fac(b): return R(b)[1] - M['fac_in']
    def zfac(b): return R(b)[3] - th
    sb = lambda b: main_sec(b)[-1]
    strip(mb, bs, lambda b: (sb(b)[0], sb(b)[1]), lambda b: (fac(b), sb(b)[1]), 'roof_soffit')
    # the facades are modelled (2026-11-22): the Boon's recessed glazed concourse under a deep band, the
    # Ponting's folded skin of triangular panels (GE close views cf_195, cf_240, cf_270)
    boon_facade(mb, M['b0'], PONTING_B0, fac, zfac)
    ponting_skin(mb, PONTING_B0, M['b1'], fac, zfac)
    for b, flip in ((bs[0], False), (bs[-1], True)):
        endcap(mb, b, [(sb(b)[0], 0.0), (fac(b), 0.0), (fac(b), zfac(b)), (sb(b)[0], zfac(b))], M['endmat'], flip)
        endcap(mb, b, [(R(b)[0], R(b)[2] - th), (R(b)[1], R(b)[3] - th), (R(b)[1], R(b)[3]), (R(b)[0], R(b)[2])], 'roof_fascia', flip)
    mb.build(col)


def skylights(col):
    """Ponting roof: the six raised skylight wedges (GE go22 ortho), apex at the roof's outer edge, tapering to the
    deck toward the field."""
    S = D['skylights']; R = periodic(D['main']['roof']); mb = MB('ponting_skylights')
    for b in S['b']:
        rin, rout, zin, zout = R(b); a = math.radians(b)
        zr = lambda r: zin + (zout - zin) * (r - rin) / (rout - rin) + 0.02
        ro = rout - 0.6; ri = ro - S['len']; ur = (math.sin(a), math.cos(a)); ut = (math.cos(a), -math.sin(a))
        P = lambda r, t, z: (r * ur[0] + t * ut[0], r * ur[1] + t * ut[1], z)
        w = S['half_w']; tip = P(ri, 0, zr(ri)); L = P(ro, -w, zr(ro)); Rr = P(ro, w, zr(ro)); A = P(ro, 0, zr(ro) + S['h'])
        mb.face([tip, A, L], 'skylight'); mb.face([tip, Rr, A], 'skylight_dk'); mb.face([L, A, Rr], 'roof_fascia')
    mb.build(col)


# ---------------- Members (NW) + the north building: glazed two-level face behind a few rows, flat white roof -------
MEM_ROWS = 3


def _window(mb, P, a, b_, z0, z1, d, mw='render_white', pane='win_dark'):
    """A window cut d metres into the wall line between s = a..b_, z0..z1: reveals, sill, head, dark pane."""
    mb.face([P(a, z0, 0), P(a, z0, -d), P(a, z1, -d), P(a, z1, 0)], mw)
    mb.face([P(b_, z0, -d), P(b_, z0, 0), P(b_, z1, 0), P(b_, z1, -d)], mw)
    mb.face([P(a, z0, -d), P(a, z0, 0), P(b_, z0, 0), P(b_, z0, -d)], 'conc_grey')
    mb.face([P(a, z1, 0), P(a, z1, -d), P(b_, z1, -d), P(b_, z1, 0)], mw)
    mb.face([P(a, z0, -d), P(b_, z0, -d), P(b_, z1, -d), P(a, z1, -d)], pane, uv=[(0, 0), (1, 0), (1, 1), (0, 1)])


def _wall_with_holes(mb, P, L, z0, z1, holes, m):
    """The wall line from z0 to z1 over 0..L, with rectangular holes [(a, b_, h0, h1)] left open."""
    xs = sorted({0.0, L, *[h[0] for h in holes], *[h[1] for h in holes]})
    for s0, s1 in zip(xs, xs[1:]):
        mid = 0.5 * (s0 + s1); zs = [z0]
        for a, b_, h0, h1 in holes:
            if a <= mid <= b_: zs += [h0, h1]
        zs = sorted(zs) + [z1]
        for k in range(0, len(zs) - 1, 2):
            if zs[k + 1] > zs[k] + 1e-3:
                ribbon(mb, P, s0, s1, zs[k], zs[k + 1], 0.0, m, step=4.0)


def members_wall(mb, b0, b1, r_of, zr):
    """The Members' outer wall (GE cf_320, cf_345): plain white render, a few small square windows high up
    and spaced unevenly, and at the foot of its north end a glazed entry set 1.2 m in under the wall. Every
    window is cut into the wall with reveals and a sill, not painted on."""
    L, bear, P = arc_frame(b0, b1, r_of)
    top = min(zr(b) for b in np.linspace(b0, b1, 40))
    rng = np.random.default_rng(320)
    holes = []
    s_ = rng.uniform(6.0, 12.0)
    while s_ < L - 4.0:                    # the high windows: about 1.2 m square, 6-20 m apart
        w = rng.uniform(1.0, 1.5); z0 = rng.choice([9.4, 9.4, 9.8]); holes.append((s_, s_ + w, z0, z0 + w * 0.8))
        s_ += w + rng.uniform(6.0, 20.0)
    c = 0.55 * L                           # a pair low down near the middle (GE cf_320, right of the trees)
    holes += [(c, c + 1.2, 5.6, 6.6), (c + 6.0, c + 7.2, 5.6, 6.6)]
    ent = (L - 26.0, L - 3.0, 0.0, 3.0)    # the north end's glazed entry
    _wall_with_holes(mb, P, L, 0.0, top, holes + [ent], 'render_white')
    n = int(math.ceil(L / 2.0))            # where the roof steps up (the north building), the wall above
    for k in range(n):
        s0, s1 = k * L / n, (k + 1) * L / n; z1 = zr(bear(0.5 * (s0 + s1)))
        if z1 > top + 0.01: ribbon(mb, P, s0, s1, top, z1, 0.0, 'render_white', step=4.0)
    for a, b_, z0, z1 in holes:
        _window(mb, P, a, b_, z0, z1, 0.3)
    a, b_, z0, z1 = ent; d = 1.2
    _window(mb, P, a, b_, z0, z1, d, pane='boon_glass')
    n = int((b_ - a) // 3.2)
    for k in range(1, n):
        post(mb, P, a + k * (b_ - a) / n, 0.0, z1, -d, 0.12, 0.14, 'steel_white')
    for k in range(1, n + 1):
        post(mb, P, a + (k - 0.5) * (b_ - a) / n, 0.0, z1, -0.4, 0.35, 0.35, 'render_white')


def members_all(col):
    M = D['members']; mb = MB('members'); bs = arc(M['b0'], M['b1'])
    RI = periodic(M['rin']); RO = periodic(M['rout']); ZR = periodic(M['zr']); fz = D['fence_h']
    def sec(b):
        f = rf(b); ri = RI(b)[0]; g = ri + 0.6; zr = ZR(b)[0]
        return ([(f, 0.0, None), (f, fz, 'fence'), (f + 0.6, fz, 'conc_grey')] + stepped(f + 0.6, fz, g - 0.4, 2.4, MEM_ROWS)
                + [(g, 2.4, 'conc_grey'), (g, zr - 1.2, 'glass_members')])
    sweep(mb, bs, sec, cap0=False)
    zr = lambda b: ZR(b)[0]
    strip(mb, bs, lambda b: (RI(b)[0] + 0.6, zr(b) - 1.2), lambda b: (RI(b)[0], zr(b) - 1.2), 'roof_soffit')
    strip(mb, bs, lambda b: (RI(b)[0], zr(b) - 1.2), lambda b: (RI(b)[0], zr(b)), 'roof_fascia')
    strip(mb, bs, lambda b: (RI(b)[0], zr(b)), lambda b: (RO(b)[0], zr(b)), 'roof_flat')
    members_wall(mb, M['b0'], M['b1'], lambda b: RO(b)[0], zr)
    # the step between the Members (13.5 m) and the taller north building (17 m)
    b = 332.0; endcap(mb, b, [(RI(b)[0], 13.5), (RO(b)[0], 13.5), (RO(b)[0], 14.0), (RI(b)[0], 14.0)], 'fac_members', flip=True)
    b = bs[-1]; endcap(mb, b, [(rf(b), 0.0), (RO(b)[0], 0.0), (RO(b)[0], zr(b)), (RI(b)[0], zr(b)), (RI(b)[0] + 0.6, 2.4),
                               (rf(b) + 0.6, fz), (rf(b), fz)], 'fac_members', flip=True)
    b = bs[0]; endcap(mb, b, [(RI(b)[0] + 0.6, 0.0), (RO(b)[0], 0.0), (RO(b)[0], zr(b)), (RI(b)[0] + 0.6, zr(b))], 'fac_members')
    for b, r, L, W, H in M['plant']:   # rooftop plant boxes (GE x330, ortho)
        c = pol(b, r); mb.box(c, L, W, H, -b, 'plant', z0=zr(b))
    S = M['sign']; mb.box(S['c'], S['L'], S['W'], S['H'], S['a'], 'fac_members', mtop='roof_flat')
    # the NINJA STADIUM sign panels on the tower's north and west faces (hand-made from the GE x330 view)
    F = Frame(dict(c=S['c'], a=S['a'], L=S['L'], W=S['W'])); z0, z1 = 3.5, 18.5; e = 0.03; L2, W2 = S['L'] / 2, S['W'] / 2
    mb.face([F.P(L2 - 0.3, W2 + e, z0), F.P(-L2 + 0.3, W2 + e, z0), F.P(-L2 + 0.3, W2 + e, z1), F.P(L2 - 0.3, W2 + e, z1)],
            'sign_ninja_w', uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    mb.face([F.P(-L2 - e, W2 - 0.3, z0), F.P(-L2 - e, -W2 + 0.3, z0), F.P(-L2 - e, -W2 + 0.3, z1), F.P(-L2 - e, W2 - 0.3, z1)],
            'sign_ninja_d', uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    mb.build(col)


# ---------------- the old Northern Stand: open-fronted, tan skillion roof on white posts ----------------
def nstand(col):
    N = D['nstand']; F = Frame(dict(c=N['c'], a=N['a'], L=N['L'], W=5.0)); mb = MB('northern_stand'); h = N['L'] / 2
    rv0, rv1 = N['roof_v']; zf, zb = N['zr']; sv0, sv1 = N['seat_v']; sz0, sz1 = N['seat_z']
    P = lambda u, v, z: F.P(u, v, z)
    # seating deck: rows rising toward the back, raised on an arcaded front wall (GE from the field, 2026-11-22)
    n = N.get('rows', 6)
    for k in range(n):
        v0 = sv0 + (sv1 - sv0) * k / n; v1 = sv0 + (sv1 - sv0) * (k + 1) / n; z = sz0 + (sz1 - sz0) * k / (n - 1)
        mb.face([P(-h, v0, z), P(h, v0, z), P(h, v1, z), P(-h, v1, z)], 'seats_dark',
                uv=[(0, 0), (N['L'] / 10, 0), (N['L'] / 10, 0.3), (0, 0.3)])
        zn = sz0 + (sz1 - sz0) * (k + 1) / (n - 1) if k < n - 1 else z
        if zn > z: mb.face([P(-h, v1, z), P(h, v1, z), P(h, v1, zn), P(-h, v1, zn)], 'conc_grey')
        mb.face([P(-h, v0, 0), P(-h, v0, z), P(-h, v1, z), P(-h, v1, 0)][::-1], 'nstand_wall')
        mb.face([P(h, v0, 0), P(h, v0, z), P(h, v1, z), P(h, v1, 0)], 'nstand_wall')
    arcade(mb, N, P, h, sv0, sz0)
    # back wall and end walls up to the roof, roof slab, fascia, posts
    back_bays(mb, P, h, rv1, zb)
    for s in (-1, 1):
        q = [P(s * h, sv1, sz1), P(s * h, rv1, 0), P(s * h, rv1, zb), P(s * h, sv1, zb + (zf - zb) * (sv1 - rv1) / (rv0 - rv1))]
        q = [P(s * h, sv1, 0)] + q[1:] + [P(s * h, sv1, sz1)]
        mb.face(q if s > 0 else q[::-1], 'nstand_wall')
    t = 0.35; ov = 0.4
    top = [P(-h - ov, rv0, zf), P(h + ov, rv0, zf), P(h + ov, rv1 + 0.2, zb), P(-h - ov, rv1 + 0.2, zb)]
    mb.face(top, 'roof_tan', uv=[(0, 0), (N['L'] / 4, 0), (N['L'] / 4, 1.25), (0, 1.25)])
    bot = [(x, y, z - t) for x, y, z in top]; mb.face(bot[::-1], 'roof_soffit')
    for i in range(4): j = (i + 1) % 4; mb.face([top[j], top[i], bot[i], bot[j]], 'roof_fascia')
    k = int(N['L'] // N['post'])
    for i in range(k + 1):
        u = -h + i * N['L'] / k; mb.beam(P(u, rv0 + 0.3, 0), P(u, rv0 + 0.3, zf - t), 0.25, 0.25, 'steel_white')
    mb.build(col)



def back_bays(mb, P, h, v, top, nb=8, d=0.6):
    """The Northern Stand's back wall (GE cf_030): pilasters a bay apart and, between them, openings 3.2 m
    high set d back to a dark inside, a lintel band over them up to the roof."""
    W = 2 * h / nb; zo = min(3.2, top - 0.6); pw = 0.6
    for k in range(nb + 1):
        u = -h + k * W; a, b_ = max(-h, u - pw / 2), min(h, u + pw / 2)
        mb.face([P(b_, v, 0), P(a, v, 0), P(a, v, zo), P(b_, v, zo)], 'nstand_wall')
        for uu in (a, b_):
            if -h < uu < h:
                mb.face([P(uu, v, 0), P(uu, v - d, 0), P(uu, v - d, zo), P(uu, v, zo)], 'nstand_wall')
    for k in range(nb):
        a, b_ = -h + k * W + pw / 2, -h + (k + 1) * W - pw / 2
        mb.face([P(b_, v - d, 0), P(a, v - d, 0), P(a, v - d, zo), P(b_, v - d, zo)], 'vom_dark')
        mb.face([P(a, v, zo), P(a, v - d, zo), P(b_, v - d, zo), P(b_, v, zo)], 'nstand_wall')
    mb.face([P(h, v, zo), P(-h, v, zo), P(-h, v, top), P(h, v, top)], 'nstand_wall')


def arcade(mb, N, P, h, v, top, depth=0.8):
    """The Northern Stand's front wall under its seats: N['arches'] segmental arches, each opening a modelled
    recess `depth` deep with a dark back, the piers and spandrels in the stand's cream render."""
    na, aw, sp, ri = N['arches'], N['arch_w'], N['arch_spring'], N['arch_rise']
    hw = aw / 2; R_ = (hw * hw + ri * ri) / (2 * ri); zc = sp + ri - R_
    cs = [-h + (k + 0.5) * 2 * h / na for k in range(na)]
    def arc_pts(c, m=10):
        a0 = math.asin(hw / R_)
        return [(c + R_ * math.sin(t), zc + R_ * math.cos(t)) for t in np.linspace(-a0, a0, m + 1)]
    edges = [-h] + [x for c in cs for x in (c - hw, c + hw)] + [h]
    for k in range(0, len(edges), 2):                       # piers, full height
        mb.face([P(edges[k], v, 0), P(edges[k + 1], v, 0), P(edges[k + 1], v, top), P(edges[k], v, top)], 'nstand_wall')
    for c in cs:
        A = arc_pts(c)
        for (u0, z0), (u1, z1) in zip(A, A[1:]):             # spandrel over the arch, and the arch's soffit
            mb.face([P(u0, v, z0), P(u1, v, z1), P(u1, v, top), P(u0, v, top)], 'nstand_wall')
            mb.face([P(u0, v, z0), P(u0, v + depth, z0), P(u1, v + depth, z1), P(u1, v, z1)], 'nstand_wall')
        for u in (c - hw, c + hw):                           # jambs
            mb.face([P(u, v, 0), P(u, v + depth, 0), P(u, v + depth, sp), P(u, v, sp)], 'nstand_wall')
        back = [P(c - hw, v + depth, 0), P(c + hw, v + depth, 0)] + [P(u, v + depth, z) for u, z in A[::-1]]
        mb.face(back, 'vom_dark')


# ---------------- east: concrete terrace steps at the fence, a grassed hill behind ----------------
def terrace(col):
    T = D['terrace']; mb = MB('east_terrace'); bs = arc(T['b0'], T['b1']); fz = D['fence_h']; HR = periodic(T['hill_r'])
    def sec(b):
        f = rf(b); s = [(f, 0.0, None), (f, 0.5, 'conc_grey'), (f + 0.4, 0.5, 'conc_grey')]
        r, z = f + 0.4, 0.5
        for k in range(T['rows']):
            s += [(r, z + T['rise'], 'conc_grey'), (r + T['run'], z + T['rise'], 'terrace')]; r += T['run']; z += T['rise']
        s += [(r + 1.0, z, 'grass_hill'), (f + HR(b)[0], 0.0, 'grass_hill')]   # GE f135: grass falls away from the top step
        return s
    sweep(mb, bs, sec, capm='grass_hill')
    mb.build(col)


def fence_only(col, b0, b1):
    mb = MB('fence_%d' % b0); bs = arc(b0, b1); fz = D['fence_h']
    sweep(mb, bs, lambda b: [(rf(b), 0.0, None), (rf(b), fz, 'fence'), (rf(b) + 0.25, fz, 'conc_grey'), (rf(b) + 0.25, 0.0, 'fence')],
          capm='fence')
    mb.build(col)


def apron(col):
    """concrete concourse from the fence out to the outer line (stops at the stadium's own boundary)"""
    mb = MB('apron'); AO = periodic(D['apron_out']); bs = arc(0, 360)
    strip(mb, bs, lambda b: (AO(b)[0], -0.02), lambda b: (rf(b), -0.02), 'apron')
    mb.build(col)


def scoreboard(col):
    """The east scoreboard (GE fac_100, cs_090): the dark screen toward the field, a 3.4 m deep steel box
    behind it clad in pale panels with its frame standing proud (posts, rails and X bracing in four bays),
    on a dark plant room with louvred doors. The screen's face stays where the data puts it."""
    S = D['scoreboard']; mb = MB('scoreboard'); F = Frame(dict(c=S['c'], a=S['a'], L=S['L'], W=S['W']))
    h = S['L'] / 2; vf = -S['W'] / 2; dep = 3.4; vb = vf + dep; z0, z1 = S['z0'], S['z0'] + S['H']
    q = lambda u, v, z=None: F.P(u, v, z)
    # the box: back, ends, top and underside, clad
    mb.face([q(-h, vb, z0), q(h, vb, z0), q(h, vb, z1), q(-h, vb, z1)], 'scoreboard_back')
    mb.face([q(h, vf, z0), q(h, vf, z1), q(h, vb, z1), q(h, vb, z0)][::-1], 'scoreboard_back')
    mb.face([q(-h, vb, z0), q(-h, vb, z1), q(-h, vf, z1), q(-h, vf, z0)][::-1], 'scoreboard_back')
    mb.face([q(-h, vf, z1), q(-h, vb, z1), q(h, vb, z1), q(h, vf, z1)][::-1], 'steel_galv')
    mb.face([q(-h, vf, z0), q(h, vf, z0), q(h, vb, z0), q(-h, vb, z0)][::-1], 'steel_galv')
    # the screen's frame and the screen itself, set 0.15 m into it
    mb.face([q(h, vf, z0), q(-h, vf, z0), q(-h, vf, z1), q(h, vf, z1)], 'steel_galv')
    mb.face([q(h - 0.4, vf - 0.03, z0 + 0.4), q(-h + 0.4, vf - 0.03, z0 + 0.4), q(-h + 0.4, vf - 0.03, z1 - 0.4),
             q(h - 0.4, vf - 0.03, z1 - 0.4)], 'screen', uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    # the frame standing 0.25 m proud of the back: posts, three rails, an X in each bay
    vo = vb + 0.14; us = np.linspace(-h, h, 5)
    for u in us: mb.beam(q(u, vo, z0), q(u, vo, z1 + 0.25), 0.28, 0.28, 'steel_white')
    for z in (z0 + 0.1, 0.5 * (z0 + z1), z1):
        mb.beam(q(-h - 0.14, vo, z), q(h + 0.14, vo, z), 0.28, 0.24, 'steel_white')
    for u0, u1 in zip(us, us[1:]):
        for za, zb in ((z0 + 0.1, 0.5 * (z0 + z1)), (0.5 * (z0 + z1), z1)):
            mb.beam(q(u0, vo, za), q(u1, vo, zb), 0.16, 0.16, 'steel_white')
            mb.beam(q(u1, vo, za), q(u0, vo, zb), 0.16, 0.16, 'steel_white')
    # the plant room under it: dark block, louvred doors set into its back
    c = q(0.0, vf + dep / 2); mb.box(c, S['L'] - 1.0, dep, z0, S['a'], 'conc_grey', mtop='steel_galv')
    for u in (-4.0, 0.5, 4.5):
        a_, b_ = u - 0.9, u + 0.9; v = vb - 0.5 + 0.02
        mb.face([q(a_, v, 0.0), q(b_, v, 0.0), q(b_, v, 2.3), q(a_, v, 2.3)], 'vom_dark')
        mb.face([q(a_, v - 0.25, 0.0), q(a_, v, 0.0), q(a_, v, 2.3), q(a_, v - 0.25, 2.3)][::-1], 'conc_grey')
    mb.build(col)


def towers(col):
    """The four light towers (GE out_*): white tapering 12-sided poles, a service platform with a railing
    under the head, and the head itself: a galvanised frame carrying 4 rows of 9 lamps, each lamp a
    modelled box with a glass face, the whole head tilted 22 degrees down at the centre square."""
    T = D['towers']; mb = MB('light_towers'); H = T['H']
    for x, y in T['pos']:
        n = 12; r0, r1 = 1.3, 0.55
        P0 = [(x + r0 * math.cos(2 * math.pi * k / n), y + r0 * math.sin(2 * math.pi * k / n)) for k in range(n)]
        P1 = [(x + r1 * math.cos(2 * math.pi * k / n), y + r1 * math.sin(2 * math.pi * k / n)) for k in range(n)]
        for k in range(n):
            j = (k + 1) % n; mb.face([(*P0[k], 0), (*P0[j], 0), (*P1[j], H), (*P1[k], H)], 'tower')
        mb.cyl((x, y), 1.9, 0.0, 0.6, 'conc_grey', n=12, top='conc_grey')             # footing
        a = math.atan2(-x, -y)                                                       # bearing to the centre
        f = np.array([math.sin(a), math.cos(a), 0.0]); s_ = np.array([math.cos(a), -math.sin(a), 0.0])
        up = np.array([0, 0, 1.0]); tilt = math.radians(22)
        fz = f * math.cos(tilt) - up * math.sin(tilt); uz = up * math.cos(tilt) + f * math.sin(tilt)
        base = np.array([x, y, H]) + f * 0.9
        W, Hh = 8.4, 4.2
        # platform and railing just under the head
        pz = H - 0.9; pc = np.array([x, y, pz]) + f * 0.6
        corners = [pc + s_ * u + f * v for u, v in ((-W / 2 - 0.3, -1.0), (W / 2 + 0.3, -1.0), (W / 2 + 0.3, 1.6), (-W / 2 - 0.3, 1.6))]
        mb.face([tuple(c) for c in corners], 'steel_galv')
        mb.face([tuple(c - up * 0.15) for c in corners[::-1]], 'steel_galv')
        for i in range(4):
            p, q_ = corners[i] + up * 1.1, corners[(i + 1) % 4] + up * 1.1
            mb.beam(tuple(p), tuple(q_), 0.06, 0.06, 'steel_galv')
            mb.beam(tuple(corners[i]), tuple(corners[i] + up * 1.1), 0.06, 0.06, 'steel_galv')
        # the head's frame: two posts off the pole, rails top and bottom and between the lamp rows
        hc = base + up * 1.0
        def hp(u, v, w=0.0): return tuple(hc + s_ * u + uz * v + fz * w)
        for v in np.linspace(0.0, Hh, 5):
            mb.beam(hp(-W / 2, v), hp(W / 2, v), 0.14, 0.14, 'steel_galv')
        for u in (-W / 2, -W / 6, W / 6, W / 2):
            mb.beam(hp(u, -0.1), hp(u, Hh + 0.1), 0.14, 0.14, 'steel_galv')
        mb.beam(tuple(np.array([x, y, H - 0.6])), hp(-W / 6, 0.4), 0.3, 0.3, 'steel_galv')
        mb.beam(tuple(np.array([x, y, H - 0.6])), hp(W / 6, 0.4), 0.3, 0.3, 'steel_galv')
        # lamps: 4 rows of 9 boxes, glass faces toward the ground
        for j in range(4):
            for i in range(9):
                u = -W / 2 + (i + 0.5) * W / 9; v = (j + 0.5) * Hh / 4; e = 0.36
                c = [hp(u + du * e, v + dv * e, 0.1) for du, dv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                cf = [hp(u + du * e, v + dv * e, 0.65) for du, dv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                for k in range(4):
                    mb.face([c[k], c[(k + 1) % 4], cf[(k + 1) % 4], cf[k]], 'steel_galv')
                mb.face(cf, 'lamp_face'); mb.face(c[::-1], 'steel_galv')
    mb.build(col)


# ---------------- vomitories: the tunnels up through the back of the lower tier (GE from the field) ----------------
# Every other seating block has one at its middle: a pale concrete portal box over the top VOM_ROWS rows, its mouth
# a dark tunnel set back into it (modelled, not painted), its roof level with the concourse behind.
VOM_W = 2.6
VOM_ROWS = 6


def vom_bearings():
    out = []
    for part, key in main_parts():
        b0, b1 = part[0], part[-1]; bm = 0.5 * (b0 + b1)
        r = main_tiers(bm)[0][2] - 0.3
        L = math.radians(b1 - b0) * r; n = max(1, int(round(L / AISLE_EVERY)))
        for j in range(0, n, 2):
            out.append((b0 + (b1 - b0) * (j + 0.5) / n, key))
    return out


def vomitories(col):
    mb = MB('vomitories')
    for b, key in vom_bearings():
        nl = ROWS[key][0]
        r0, z0, r1, z1 = main_tiers(b)[0]; run = (r1 - r0) / nl
        ra = r0 + (nl - VOM_ROWS) * run; za = z0 + (nl - VOM_ROWS) * (z1 - z0) / nl
        a = math.radians(b); ur = (math.sin(a), math.cos(a)); ut = (math.cos(a), -math.sin(a))
        P = lambda r, t, z: (r * ur[0] + t * ut[0], r * ur[1] + t * ut[1], z)
        w = VOM_W / 2; top = max(z1 + 0.15, za + 2.9); t = 0.3; zo = za + 2.4   # mouth 2.4 m high, its box 2.9 m
        # outer box: two side walls (each t thick) and the lid
        for s_ in (-1, 1):
            o, i = s_ * w, s_ * (w - t)
            mb.face([P(ra, o, za - 0.2), P(r1, o, za - 0.2), P(r1, o, top), P(ra, o, top)][::(1 if s_ > 0 else -1)], 'vom_conc')
            mb.face([P(ra, i, za - 0.2), P(ra, i, top), P(r1, i, top), P(r1, i, za - 0.2)][::(1 if s_ > 0 else -1)], 'vom_dark')
            mb.face([P(ra, o, za - 0.2), P(ra, o, top), P(ra, i, top), P(ra, i, za - 0.2)][::(-1 if s_ > 0 else 1)], 'vom_conc')
        mb.face([P(ra, -w, top), P(r1, -w, top), P(r1, w, top), P(ra, w, top)][::-1], 'vom_conc')
        # lintel over the mouth, then the tunnel's ceiling and its dark back
        mb.face([P(ra, -w + t, zo), P(ra, w - t, zo), P(ra, w - t, top), P(ra, -w + t, top)][::-1], 'vom_conc')
        mb.face([P(ra, -w + t, zo), P(r1, -w + t, zo), P(r1, w - t, zo), P(ra, w - t, zo)], 'vom_dark')
        mb.face([P(r1 - 0.05, -w + t, za - 0.2), P(r1 - 0.05, w - t, za - 0.2), P(r1 - 0.05, w - t, zo), P(r1 - 0.05, -w + t, zo)][::-1], 'vom_dark')
        mb.face([P(ra, -w + t, za + 0.02), P(r1, -w + t, za + 0.02), P(r1, w - t, za + 0.02), P(ra, w - t, za + 0.02)][::-1], 'tread')
    mb.build(col)


# ---------------- the indoor centre west of the Ponting Stand (OSM building=sports_centre) -----------------
# GE out_W, out_NW, cf_240: a flat-roofed two-storey white box, 40 x 18 m, its long axis 23 deg south of east
# and its east end against the Ponting Stand. Its upper floor is wrapped in two bands of glass on the north,
# south and west faces: tall pale glass under the roof edge, a white floor line, a lower band of dark glass;
# the ground floor is white render with doors and dark windows, glazed across the west end. A single-storey
# service wing with a roller door stands on the north face's east end, a plant screen on its roof.
IC = dict(c=(-113.38, -39.23), a=-23.16, L=40.0, W=18.0)
IC_FLOOR, IC_EAVE, IC_TOP = 4.4, 9.0, 9.6     # first floor, underside of the roof edge, top of the parapet
IC_BANDS = [(4.9, 6.45, 'dk'), (6.7, 8.9, 'up')]


def edge_frame(p, q):
    """A straight wall from plan point p to q, outward on the right: (s, z, out) -> 3D, and its length."""
    p = np.array(p, float); q = np.array(q, float); L = float(np.linalg.norm(q - p)); t = (q - p) / L
    n = np.array([t[1], -t[0]])
    def P(s_, z, out=0.0):
        x, y = p + t * s_ + n * out; return (float(x), float(y), z)
    return L, P


def curtain(mb, P, a, b_, z0, z1, d=0.2, bay=1.5, transoms=(), glass='cw_glass'):
    """Glass set d into the wall between s = a..b_, z0..z1, with reveals, aluminium mullions every `bay` m
    and transoms at the given heights, all modelled."""
    _window(mb, P, a, b_, z0, z1, d, pane=glass)
    n = max(1, int(round((b_ - a) / bay)))
    for k in range(1, n):
        post(mb, P, a + k * (b_ - a) / n, z0, z1, -d, 0.07, 0.12, 'steel_white')
    for z in transoms:
        for k in range(n):
            s0, s1 = a + k * (b_ - a) / n + 0.035, a + (k + 1) * (b_ - a) / n - 0.035
            mb.face([P(s0, z - 0.04, -d + 0.1), P(s1, z - 0.04, -d + 0.1), P(s1, z + 0.04, -d + 0.1), P(s0, z + 0.04, -d + 0.1)], 'steel_white')
            mb.face([P(s0, z + 0.04, -d + 0.1), P(s1, z + 0.04, -d + 0.1), P(s1, z + 0.04, -d), P(s0, z + 0.04, -d)], 'steel_white')


def ic_wall(mb, P, L, top, openings, glass_runs):
    """One face: rendered wall to `top` with the openings left open, then the glass in them."""
    _wall_with_holes(mb, P, L, 0.0, top, [o[:4] for o in openings], 'render_white')
    for a, b_, z0, z1, kind in openings:
        if kind == 'door':
            _window(mb, P, a, b_, z0, z1, 0.25, pane='vom_dark')
        elif kind == 'roller':
            _window(mb, P, a, b_, z0, z1, 0.35, pane='steel_galv')
            for z in np.arange(z0 + 0.2, z1, 0.2):   # the roller door's slats
                mb.face([P(a, z - 0.02, -0.33), P(b_, z - 0.02, -0.33), P(b_, z, -0.30), P(a, z, -0.30)], 'conc_grey')
        else:
            curtain(mb, P, a, b_, z0, z1, **glass_runs.get(kind, {}))


def fascia(mb, P, L, z0, z1, out=0.3, par=0.25):
    """The deep white fascia standing `out` proud of the wall, its soffit, and the parapet's top and inside."""
    # each face carries the corner square at its own end, so no two faces lie on top of each other
    ribbon(mb, P, -out, L + out, z0, z1, out, 'render_white', step=L)
    hband(mb, P, 0.0, L + out, z0, 0.0, out, 'render_white', step=L)
    hband(mb, P, 0.0, L + out, z1, 0.0, out, 'steel_white', step=L)
    hband(mb, P, 0.0, L - par, z1, -par, 0.0, 'steel_white', step=L)
    ribbon(mb, P, L, 0.0, z1 - 0.6, z1, -par, 'render_white', step=L)   # the parapet's inner face, reversed


def indoor_centre(col):
    mb = MB('indoor_centre'); F = Frame(IC); h, w = IC['L'] / 2, IC['W'] / 2
    C = [F.P(-h, -w), F.P(h, -w), F.P(h, w), F.P(-h, w)]          # SW, SE, NE, NW: counter-clockwise
    wing_u = 4.0                                                    # the service wing runs from here to the east end
    rng = np.random.default_rng(77)
    runs = dict(up=dict(glass='cw_glass'), dk=dict(glass='cw_glass_dk'), low=dict(glass='win_dark'),
                gl=dict(glass='cw_glass_dk', transoms=(2.5,)))
    def bands(L, a=0.5, b_=None):
        return [(a, (L - 0.5) if b_ is None else b_, z0, z1, k) for z0, z1, k in IC_BANDS]
    # south face (C0 -> C1): both glass bands end to end, dark windows and two doors on the ground floor
    L, P = edge_frame(C[0], C[1])
    op = bands(L); s_ = 1.2
    while s_ < L - 3.0:
        if abs(s_ - 14.0) < 2.0 or abs(s_ - 29.0) < 2.0:
            op.append((s_, s_ + 1.8, 0.0, 2.4, 'door')); s_ += 4.2; continue
        wd = 3.0 if rng.random() < 0.7 else 4.5
        op.append((s_, min(s_ + wd, L - 1.2), 1.0, 3.3, 'low')); s_ += wd + 1.2
    ic_wall(mb, P, L, IC_EAVE, op, runs); fascia(mb, P, L, IC_EAVE, IC_TOP)
    # east face (C1 -> C2): against the stand's back, plain render
    L, P = edge_frame(C[1], C[2])
    ic_wall(mb, P, L, IC_EAVE, [], {}); fascia(mb, P, L, IC_EAVE, IC_TOP)
    # north face (C2 -> C3): the bands over the wing too; ground floor windows and a door west of the wing
    L, P = edge_frame(C[2], C[3]); sw = h - wing_u
    op = bands(L, 0.5) + [(L - 3.4, L - 1.6, 0.0, 2.4, 'door')]
    op += [(sw + 1.5 + k * 4.6, sw + 4.5 + k * 4.6, 1.0, 3.3, 'low') for k in range(int((L - sw - 5.5) // 4.6))]
    ic_wall(mb, P, L, IC_EAVE, op, runs); fascia(mb, P, L, IC_EAVE, IC_TOP)
    # west end (C3 -> C0): the bands, and below them the ground floor glazed behind white piers, doors in it
    L, P = edge_frame(C[3], C[0])
    op = bands(L) + [(0.8, L - 0.8, 0.3, 3.9, 'gl')]
    ic_wall(mb, P, L, IC_EAVE, op, runs); fascia(mb, P, L, IC_EAVE, IC_TOP)
    for a in (L / 2 - 2.1, L / 2 + 0.1):
        mb.face([P(a, 0.3, -0.1), P(a + 2.0, 0.3, -0.1), P(a + 2.0, 2.5, -0.1), P(a, 2.5, -0.1)], 'vom_dark')
    for k in range(1, 4):
        post(mb, P, 0.8 + k * (L - 1.6) / 4, 0.0, 4.4, 0.0, 0.35, 0.3, 'render_white')
    # the roof inside the parapet: a roof hatch and one small plant unit (GE out_W: the roof is near bare)
    q = lambda u, v, z: F.P(u, v, z)
    i = 0.25; zr = IC_TOP - 0.6
    mb.face([q(-h + i, -w + i, zr), q(h - i, -w + i, zr), q(h - i, w - i, zr), q(-h + i, w - i, zr)], 'roof_white')
    for u, v, L_, W_, H_ in ((-6.0, 5.5, 1.0, 1.0, 0.45), (12.0, 4.0, 1.6, 1.2, 0.9)):
        mb.box(F.P(u, v), L_, W_, H_, IC['a'], 'steel_galv', z0=zr, mtop='steel_white')
    # the service wing on the north face's east half (GE out_W, out_NW): one storey, 11 m deep, its east side
    # following the Ponting's back round; a roller door and a door in its west end, high windows on its
    # north side, a 0.6 m parapet, and a 1.6 m plant screen round the west half of its roof
    wu0, wv0, wv1, wz, rs = -2.0, w, w + 11.0, 5.0, 100.6
    def r_at(u, v):
        x, y = F.P(u, v); return math.hypot(x, y)
    def u_on(v):                                   # where the line v meets the stand's back, r = rs
        lo, hi = wu0, h + 5.0
        for _ in range(50):
            m_ = 0.5 * (lo + hi); lo, hi = (m_, hi) if r_at(m_, v) > rs else (lo, m_)
        return lo
    arc_uv = [(u_on(v), v) for v in np.linspace(wv0, wv1, 6)]
    G = [F.P(wu0, wv0)] + [F.P(u, v) for u, v in arc_uv] + [F.P(wu0, wv1)]
    n = len(G)
    for k in range(1, n):                          # edge 0 (its south side) is the main block's wall
        a, b_ = G[k], G[(k + 1) % n]
        L, P = edge_frame(a, b_)
        op = []
        if k == n - 1: op = [(1.5, 5.0, 0.0, 3.8, 'roller'), (6.4, 7.4, 0.0, 2.2, 'door')]
        if k == n - 2: op = [(1.5 + 3.2 * j, 2.7 + 3.2 * j, 2.2, 3.1, 'low') for j in range(int((L - 2.5) // 3.2))]
        ic_wall(mb, P, L, wz + 0.6, op, runs)
        hband(mb, P, 0.0, max(0.1, L - 0.25), wz + 0.6, -0.25, 0.0, 'steel_white', step=L)
        ribbon(mb, P, L, 0.0, wz, wz + 0.6, -0.25, 'render_white', step=L)
    mb.cap(G, wz, 'roof_white')
    sc_u = wu0 + 0.5 * (arc_uv[-1][0] - wu0)
    S = [F.P(sc_u, wv1 - 0.25), F.P(wu0 + 0.25, wv1 - 0.25), F.P(wu0 + 0.25, wv0 + 1.0)]
    for a, b_ in zip(S, S[1:]):
        L, P = edge_frame(a, b_)
        for o in (0.0, -0.2):
            ribbon(mb, P, 0.0, L, wz, wz + 1.8, o, 'render_white', step=L)
        hband(mb, P, 0.0, L, wz + 1.8, -0.2, 0.0, 'render_white', step=L)
    mb.build(col)


# ---------------- the north-east video board on the hill (GE in_W, out_W) ----------------
# Placed by eye: on the hill top a third of the way from the scoreboard toward the north stand, then checked
# side by side with Google Earth's in_W and out_W. About 14.4 x 6.2 m, its foot 3.2 m up on three braced
# legs, turned to the ground like the scoreboard.
VB = dict(b=70.0, r=97.0, L=14.4, H=6.2, z0=3.2, dep=0.9)


def video_board(col):
    mb = MB('video_board'); b = math.radians(VB['b'])
    F = Frame(dict(c=(VB['r'] * math.sin(b), VB['r'] * math.cos(b)), a=-VB['b'] - 4.0, L=VB['L'], W=VB['dep']))
    h = VB['L'] / 2; vf = -VB['dep'] / 2; vb = -vf; z0, z1 = VB['z0'], VB['z0'] + VB['H']
    q = lambda u, v, z: F.P(u, v, z)
    mb.face([q(-h, vb, z0), q(h, vb, z0), q(h, vb, z1), q(-h, vb, z1)], 'steel_galv')
    mb.face([q(h, vf, z0), q(h, vf, z1), q(h, vb, z1), q(h, vb, z0)][::-1], 'steel_galv')
    mb.face([q(-h, vb, z0), q(-h, vb, z1), q(-h, vf, z1), q(-h, vf, z0)][::-1], 'steel_galv')
    mb.face([q(-h, vf, z1), q(-h, vb, z1), q(h, vb, z1), q(h, vf, z1)][::-1], 'steel_white')
    mb.face([q(-h, vf, z0), q(h, vf, z0), q(h, vb, z0), q(-h, vb, z0)][::-1], 'steel_galv')
    mb.face([q(h, vf, z0), q(-h, vf, z0), q(-h, vf, z1), q(h, vf, z1)], 'steel_white')     # the frame
    mb.face([q(h - 0.25, vf - 0.03, z0 + 0.25), q(-h + 0.25, vf - 0.03, z0 + 0.25), q(-h + 0.25, vf - 0.03, z1 - 0.25),
             q(h - 0.25, vf - 0.03, z1 - 0.25)], 'screen_blue', uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    for u in (-h + 1.2, 0.0, h - 1.2):                    # the legs, each on a concrete pad, braced behind
        mb.box(F.P(u, 0.0), 0.9, 0.9, 0.25, F.a * 180 / math.pi, 'conc_grey')
        mb.beam(q(u, 0.0, 0.25), q(u, 0.0, z0 + 0.4), 0.35, 0.35, 'steel_white')
        mb.beam(q(u, 0.0, 0.25), q(u, vb + 1.6, 0.25), 0.1, 0.1, 'steel_white')
        mb.beam(q(u, vb + 1.6, 0.25), q(u, 0.2, z0 + 0.2), 0.18, 0.18, 'steel_white')
    mb.beam(q(-h + 1.2, 0.0, z0 - 0.2), q(h - 1.2, 0.0, z0 - 0.2), 0.22, 0.22, 'steel_white')
    mb.build(col)


# ---------------- the practice nets and forecourt west of the Ponting (GE out_NW, cf_270, out_W) ------------
# Three outdoor practice lanes on the lawn by Derwent Street's footpath, parallel to the street: a
# synthetic wicket in each, netted sides, back and roof on galvanised posts. The indoor centre's west end
# opens onto a paved forecourt; the yard west of its service wing is asphalt with marked bays.
NETS = dict(c=(-120.2, 4.0), a=65.0, L=30.0, lane=3.2, n=3, H=3.6)


def practice_nets(col):
    mb = MB('practice_nets'); N = NETS; W = N['lane'] * N['n']
    F = Frame(dict(c=N['c'], a=N['a'], L=N['L'], W=W)); h = N['L'] / 2; q = F.P; H = N['H']
    vs = [-W / 2 + k * N['lane'] for k in range(N['n'] + 1)]
    gr = MB('nets_ground')                                    # the wickets: open ground (GroundModels.OPEN_GROUND)
    for k in range(N['n']):
        v0, v1 = vs[k] + 0.1, vs[k + 1] - 0.1
        gr.face([q(-h, v1, 0.03), q(h, v1, 0.03), q(h, v0, 0.03), q(-h, v0, 0.03)], 'syn_pitch',
                uv=[(1, 0), (1, N['L'] / 4.0), (0, N['L'] / 4.0), (0, 0)])
    gr.build(col)
    us = np.linspace(-h, h, 9)
    for v in vs:                                              # posts, top rails and the netted sides
        for u in us: mb.beam(q(u, v, 0.0), q(u, v, H), 0.08, 0.08, 'steel_galv')
        mb.beam(q(-h, v, H), q(h, v, H), 0.06, 0.06, 'steel_galv')
        mb.face([q(-h, v, 0.0), q(h, v, 0.0), q(h, v, H), q(-h, v, H)], 'mesh')
    for u in (-h, h):
        mb.beam(q(u, vs[0], H), q(u, vs[-1], H), 0.06, 0.06, 'steel_galv')
    mb.face([q(h, vs[0], 0.0), q(h, vs[-1], 0.0), q(h, vs[-1], H), q(h, vs[0], H)], 'mesh')   # the batting end
    mb.face([q(-h, vs[0], H), q(h, vs[0], H), q(h, vs[-1], H), q(-h, vs[-1], H)], 'mesh')   # the roof net
    mb.build(col)


def forecourt(col):
    mb = MB('forecourt'); F = Frame(IC); q = F.P
    def slab(u0, u1, v0, v1, m, z=0.03):
        mb.face([q(u0, v1, z), q(u1, v1, z), q(u1, v0, z), q(u0, v0, z)], m)
    slab(-29.0, -20.0, -9.0, 20.0, 'pavers')                   # in front of the glass west end
    slab(-20.0, -2.0, 9.0, 20.0, 'yard')                       # the service yard west of the wing
    for v in (-9.0, 20.0):                                     # kerbs round the paving
        mb.beam(q(-29.0, v, 0.06), q(-20.0 if v < 0 else -2.0, v, 0.06), 0.15, 0.12, 'conc_grey')
    mb.beam(q(-29.0, -9.0, 0.06), q(-29.0, 20.0, 0.06), 0.15, 0.12, 'conc_grey')
    mb.build(col)


def build_all():
    clear(); col = bpy.context.scene.collection
    main_all(col); vomitories(col); skylights(col); members_all(col); nstand(col); terrace(col); scoreboard(col); towers(col); apron(col); indoor_centre(col); video_board(col); practice_nets(col); forecourt(col)
    fence_only(col, D['members']['b1'], 360 + D['terrace']['b0'])


# ---------------- seats: instanced 3D shells on the treads (the MCG standard's seat files) ----------------
SEAT_W = 0.5           # seat pitch along the row
AISLE_EVERY = 16.0     # m of row between aisle stairs (Google Earth: about 16 m blocks in the Boon)
AISLE_W = 1.2
HEADROOM = 2.6         # the seat rule: open sky, or at least this much under a roof


def roof_z(b, r):
    """The main roof's underside above radius r at bearing b, or None where there is no roof over it."""
    rin, rout, zin, zout = periodic(D['main']['roof'])(b)
    if not (rin <= r <= rout) or not (D['main']['b0'] <= b <= D['main']['b1']):
        return None
    return zin + (zout - zin) * (r - rin) / (rout - rin) - D['main']['roof_th']


def _row_seats(out, b0, b1, rows, colour_of, gap=()):
    """Seats along rows [(r_front, r_back, z)] between bearings b0 and b1, aisles every AISLE_EVERY m of row
    (and at the bearings in gap). Each seat: (bearing, radius of its origin, tread z, colour)."""
    for k, (rf_, rb_, z, bb) in enumerate(rows):
        r = rb_ - 0.30
        L = math.radians(b1 - b0) * r
        n_blocks = max(1, int(round(L / AISLE_EVERY)))
        for blk in range(n_blocks):
            s0 = blk * L / n_blocks + AISLE_W / 2; s1 = (blk + 1) * L / n_blocks - AISLE_W / 2
            m = int((s1 - s0) // SEAT_W)
            for i in range(m):
                s = s0 + (s1 - s0 - m * SEAT_W) / 2 + (i + 0.5) * SEAT_W
                b = b0 + math.degrees(s / r)
                if any(abs(b - g) < math.degrees(AISLE_W / 2 / r) for g in gap):
                    continue
                rz = roof_z(b, r)
                if rz is not None and rz - z < HEADROOM:
                    continue
                out.append((b, r, z, colour_of(b, k, bb)))


def seat_list():
    """Every seat as (bearing, radius, tread z, colour)."""
    out = []
    for part, key in main_parts():
        nl, nu = ROWS[key]; b0, b1 = part[0], part[-1]
        # rows at the part's middle bearing; each seat then takes its own bearing's tread
        for tier, n in ((0, nl), (1, nu)):
            for k in range(n):
                rows = []
                def at(b, k=k, tier=tier, n=n):
                    r0, z0, r1, z1 = main_tiers(b)[tier]; run = (r1 - r0) / n
                    return r0 + k * run, r0 + (k + 1) * run, z0 + (k + 1) * (z1 - z0) / n
                bm = 0.5 * (b0 + b1); rf_, rb_, z = at(bm)
                tmp = []
                _row_seats(tmp, b0, b1, [(rf_, rb_, z, bm)], lambda b, kk, bb, tier=tier, k=k: (tier, k))
                for b, r, z_, c in tmp:
                    f_, rb2, z2 = at(b)          # the seat's own row at its bearing
                    if tier == 0 and k >= nl - VOM_ROWS and any(
                            abs(math.radians(b - vb) * rb2) < VOM_W / 2 + 0.25 for vb, _ in vom_bearings()):
                        continue
                    out.append((b, rb2 - 0.30, z2, seat_colour(key, tier, k, b)))
    # the Members' front rows (dark grey), where a row is deep enough to hold a seat
    M = D['members']; RI = periodic(M['rin'])
    for k in range(MEM_ROWS):
        def at(b, k=k):
            f = rf(b); r0, r1 = f + 0.6, RI(b)[0] + 0.2; run = (r1 - r0) / MEM_ROWS
            return r0 + (k + 1) * run, D['fence_h'] + (k + 1) * (2.4 - D['fence_h']) / MEM_ROWS, run
        tmp = []
        bm = 0.5 * (M['b0'] + M['b1'])
        _row_seats(tmp, M['b0'] + 1.0, M['b1'] - 1.0, [(0, at(bm)[0], at(bm)[1], bm)], lambda *a: 0)
        for b, r, z, c in tmp:
            rb_, z_, run = at(b)
            if run >= 0.75:
                out.append((b, rb_ - 0.30, z_, 'seat_bel_dark'))
    out = [(r * math.sin(math.radians(b)), r * math.cos(math.radians(b)), z, b, c) for b, r, z, c in out]
    # the Northern Stand's rows (white), facing the field across its own frame
    N = D['nstand']; F = Frame(dict(c=N['c'], a=N['a'], L=N['L'], W=5.0)); n = N['rows']
    sv0, sv1 = N['seat_v']; sz0, sz1 = N['seat_z']; h = N['L'] / 2
    for k in range(n):
        v1 = sv0 + (sv1 - sv0) * (k + 1) / n; z = sz0 + (sz1 - sz0) * k / (n - 1)
        m = int((N['L'] - 1.0) // SEAT_W)
        for i in range(m):
            u = -h + 0.5 + (i + 0.5) * SEAT_W
            x, y = F.P(u, v1 - 0.30)
            out.append((x, y, z, -N['a'], 'seat_bel_white'))
    # the east terrace: bench blocks on its three lowest steps (GE from the field)
    T = D['terrace']
    for k in range(3):
        for blk in np.arange(T['b0'] + 3, T['b1'] - 3, 9.0):
            for i in range(14):
                f = 0; b = blk + i * 0.4
                r = rf(b) + 0.4 + (k + 1) * T['run'] - 0.30; z = 0.5 + (k + 1) * T['rise']
                out.append((r * math.sin(math.radians(b)), r * math.cos(math.radians(b)), z, b, 'seat_bel_white'))
    return out


def seat_colour(stand, tier, row, b):
    # Boon: the five front rows pale blue-grey, as Google Earth shows them from the field
    if stand == 'S' and tier == 0 and row < 5:
        return 'seat_bel_pale'
    return 'seat_bel_blue'



SEAT_TMPL = None


def seat_template():
    """One moulded seat, glTF frame (x along the row, y up, +z toward the field), origin on the tread under
    the seat's back edge: a pan 0.44 x 0.40 at 0.43 m on a pedestal, a back 0.42 high leaning 12 degrees."""
    tris = []
    def box(cx, cy, cz, sx, sy, sz, lean=0.0):
        ca, sa = math.cos(lean), math.sin(lean)
        P = []
        for dx, dy, dz in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
            y, z = dy * sy / 2, dz * sz / 2
            y, z = y * ca + z * sa, -y * sa + z * ca
            P.append((cx + dx * sx / 2, cy + y, cz + z))
        ctr = np.mean(P, axis=0)
        for a, b_, c, d in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            for t in ((P[a], P[b_], P[c]), (P[a], P[c], P[d])):
                A, B, C = (np.array(q) for q in t)
                # Godot's front face: Plane(a, b, c).normal = (a - c) x (a - b) looks out of the box
                if np.dot(np.cross(A - C, A - B), (A + B + C) / 3 - ctr) < 0:
                    t = (t[0], t[2], t[1])
                tris.extend(t)
    box(0.0, 0.415, 0.24, 0.44, 0.05, 0.40)              # pan
    box(0.0, 0.66, 0.05, 0.42, 0.42, 0.05, lean=0.21)   # back
    box(0.0, 0.2, 0.22, 0.08, 0.40, 0.25)               # pedestal
    return tris


def seat_transforms(seats):
    """Row-major 3x4 per seat in the glTF frame (x east, y up, z south) for GroundModels' seat files. A seat is
    (x east, y north, z up, bearing it faces away from, colour): it looks back along that bearing."""
    out = {}
    for x, y, z, b, c in seats:
        a = math.radians(b); sb, cb = math.sin(a), math.cos(a)
        X = (cb, 0.0, sb); Y = (0.0, 1.0, 0.0); Zv = (-sb, 0.0, cb)   # +z toward the field
        o = (x, z, -y)
        out.setdefault(c, []).append([X[0], Y[0], Zv[0], o[0], X[1], Y[1], Zv[1], o[1], X[2], Y[2], Zv[2], o[2]])
    return out
