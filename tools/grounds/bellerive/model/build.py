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
def main_sec(b):
    T = periodic(D['main']['tiers'])(b)
    d1, z1, w, rz, d2, z2, zb = T
    f = rf(b); fz = D['fence_h']
    m1 = seatmat(b, 'lower'); m2 = seatmat(b, 'upper')
    return [(f, 0.0, None), (f, fz, 'fence'), (f + 0.6, fz, 'conc_grey'), (f + d1, z1, m1),
            (f + d1 + w, z1, 'conc_grey'), (f + d1 + w, z1 + rz, 'tier_wall'), (f + d2, z2, m2),
            (f + d2 + 1.2, z2, 'conc_grey'), (f + d2 + 1.2, zb, 'backwall')]


def seatmat(b, tier):
    for b0, b1, t, m in D['main']['seatmats']:
        if b0 <= b % 360 < b1 and t in (tier, 'both'): return m
    return 'seats_blue'


def main_all(col):
    M = D['main']; mb = MB('main_stand'); bs = arc(M['b0'], M['b1'])
    sweep(mb, bs, main_sec)
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
    for b0, b1, m in M['facmats']:
        bb = [b for b in bs if b0 - 1e-6 <= b <= b1 + 1e-6]
        if len(bb) > 1: strip(mb, bb[::-1], lambda b: (fac(b), 0.0), lambda b: (fac(b), zfac(b)), m)  # v up the wall
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
def members_all(col):
    M = D['members']; mb = MB('members'); bs = arc(M['b0'], M['b1'])
    RI = periodic(M['rin']); RO = periodic(M['rout']); ZR = periodic(M['zr']); fz = D['fence_h']
    def sec(b):
        f = rf(b); ri = RI(b)[0]; g = ri + 0.6; zr = ZR(b)[0]
        return [(f, 0.0, None), (f, fz, 'fence'), (f + 0.6, fz, 'conc_grey'), (g - 0.4, 2.4, 'seats_dark'),
                (g, 2.4, 'conc_grey'), (g, zr - 1.2, 'glass_members')]
    sweep(mb, bs, sec, cap0=False)
    zr = lambda b: ZR(b)[0]
    strip(mb, bs, lambda b: (RI(b)[0] + 0.6, zr(b) - 1.2), lambda b: (RI(b)[0], zr(b) - 1.2), 'roof_soffit')
    strip(mb, bs, lambda b: (RI(b)[0], zr(b) - 1.2), lambda b: (RI(b)[0], zr(b)), 'roof_fascia')
    strip(mb, bs, lambda b: (RI(b)[0], zr(b)), lambda b: (RO(b)[0], zr(b)), 'roof_flat')
    strip(mb, bs[::-1], lambda b: (RO(b)[0], 0.0), lambda b: (RO(b)[0], zr(b)), 'fac_members')
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
    # seating deck: rows rising toward the back
    n = 6
    for k in range(n):
        v0 = sv0 + (sv1 - sv0) * k / n; v1 = sv0 + (sv1 - sv0) * (k + 1) / n; z = sz0 + (sz1 - sz0) * k / (n - 1)
        mb.face([P(-h, v0, z), P(h, v0, z), P(h, v1, z), P(-h, v1, z)], 'seats_dark',
                uv=[(0, 0), (N['L'] / 10, 0), (N['L'] / 10, 0.3), (0, 0.3)])
        zn = sz0 + (sz1 - sz0) * (k + 1) / (n - 1) if k < n - 1 else z
        if zn > z: mb.face([P(-h, v1, z), P(h, v1, z), P(h, v1, zn), P(-h, v1, zn)], 'conc_grey')
        mb.face([P(-h, v0, 0), P(-h, v0, z), P(-h, v1, z), P(-h, v1, 0)][::-1], 'nstand_wall')
        mb.face([P(h, v0, 0), P(h, v0, z), P(h, v1, z), P(h, v1, 0)], 'nstand_wall')
    mb.face([P(-h, sv0, 0), P(h, sv0, 0), P(h, sv0, sz0), P(-h, sv0, sz0)], 'conc_grey')
    # back wall and end walls up to the roof, roof slab, fascia, posts
    mb.face([P(h, rv1, 0), P(-h, rv1, 0), P(-h, rv1, zb), P(h, rv1, zb)], 'nstand_wall')
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


# ---------------- east: concrete terrace steps at the fence, a grassed hill behind ----------------
def terrace(col):
    T = D['terrace']; mb = MB('east_terrace'); bs = arc(T['b0'], T['b1']); fz = D['fence_h']; HR = periodic(T['hill_r'])
    def sec(b):
        f = rf(b); s = [(f, 0.0, None), (f, 0.5, 'conc_grey'), (f + 0.4, 0.5, 'conc_grey')]
        r, z = f + 0.4, 0.5
        for k in range(T['rows']):
            s += [(r, z + T['rise'], 'conc_grey'), (r + T['run'], z + T['rise'], 'terrace')]; r += T['run']; z += T['rise']
        s += [(f + HR(b)[0], T['hill_z'], 'grass_hill'), (f + HR(b)[0] + 3.0, 0.0, 'grass_hill')]
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
    S = D['scoreboard']; mb = MB('scoreboard'); F = Frame(dict(c=S['c'], a=S['a'], L=S['L'], W=S['W']))
    mb.box(S['c'], S['L'], S['W'], S['H'], S['a'], 'scoreboard_back', z0=S['z0'])
    h = S['L'] / 2; v = -S['W'] / 2 - 0.03   # screen face toward the field (west): blank dark screen
    z0, z1 = S['z0'] + 0.4, S['z0'] + S['H'] - 0.4
    mb.face([F.P(h - 0.4, v, z0), F.P(-h + 0.4, v, z0), F.P(-h + 0.4, v, z1), F.P(h - 0.4, v, z1)], 'screen', uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    for u in (-h + 2.5, h - 2.5): mb.box(F.P(u, 0)[:2], 1.0, 1.0, S['z0'], S['a'], 'steel_galv')
    mb.build(col)


def towers(col):
    T = D['towers']; mb = MB('light_towers'); H = T['H']
    for x, y in T['pos']:
        n = 8; r0, r1 = 1.3, 0.6
        P0 = [(x + r0 * math.cos(2 * math.pi * k / n), y + r0 * math.sin(2 * math.pi * k / n)) for k in range(n)]
        P1 = [(x + r1 * math.cos(2 * math.pi * k / n), y + r1 * math.sin(2 * math.pi * k / n)) for k in range(n)]
        for k in range(n):
            j = (k + 1) % n; mb.face([(*P0[k], 0), (*P0[j], 0), (*P1[j], H), (*P1[k], H)], 'tower')
        # lamp head facing the centre, tilted down 25 degrees
        a = math.atan2(-x, -y); ux, uy = math.cos(a), -math.sin(a); fx, fy = math.sin(a), math.cos(a)
        Fr = Frame(dict(c=(x + fx * 0.8, y + fy * 0.8), a=math.degrees(math.atan2(uy, ux)), L=7.0, W=1.2))
        c = Fr.P(0, 0)[:2]; mb.box(c, 7.0, 1.0, 4.2, math.degrees(math.atan2(uy, ux)), 'steel_galv', z0=H - 1.0)
        z0, z1 = H - 0.8, H + 3.0
        mb.face([Fr.P(3.4, 0.55, z0), Fr.P(-3.4, 0.55, z0), Fr.P(-3.4, 0.55, z1), Fr.P(3.4, 0.55, z1)][::-1], 'lamps',
                uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    mb.build(col)


def build_all():
    clear(); col = bpy.context.scene.collection
    main_all(col); skylights(col); members_all(col); nstand(col); terrace(col); scoreboard(col); towers(col); apron(col)
    fence_only(col, D['members']['b1'], 360 + D['terrace']['b0'])
