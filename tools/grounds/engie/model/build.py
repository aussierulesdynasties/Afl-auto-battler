# ENGIE Stadium (Sydney Showground Stadium, Sydney Olympic Park) as it is today, rebuilt to the MCG standard
# (docs/MCG_STANDARD.md). Plan from OpenStreetMap (ODbL: osm.py writes the fence, roof edges, light masts and video
# wall into engie.json); everything else modelled by eye from photos (Google Earth and Street View for looking at
# only, never measured or sampled; see the data-source rule in docs/MCG_STANDARD.md).
# Data: model/engie.json. Runs inside Blender: import build; build.build_all().
# Frame: x east, y north, z up from the field, metres; bearings clockwise from north, from the OSM pitch's centre.
#
# What is modelled (nothing painted on that has depth in the real ground):
#  - one continuous bowl of real stepped rows: a lower tier, a cross aisle and an upper tier under the roofs, one
#    tier in the open north-east end; aisle stairs with handrails, vomitories cut into the lower tier, the players'
#    race through the north-east stand;
#  - seven roofs: five 1998 segments, each a shallow barrel arched between two light towers and hung on cable
#    stays from them; the 2012 north and east roofs, flat with A-frame trusses on top, hung on stays from the two
#    towers beside the open end; corrugated undersides on radial rafters, round columns, a fascia with downlights;
#  - eight red lattice light towers, each a leaning square mast and a flared lattice head with 44 LED floods;
#  - the oval scoreboard on its steel lattice over a charcoal building behind the open end;
#  - the outside walls: precast bays with recessed openings and windows on the old stands, raking white V struts
#    on the east stand, light blue cladding and a concrete stair tower on the north stand.
import bpy, math, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from mb import MB, TILE
D = json.load(open(os.path.join(HERE, 'engie.json')))
STEP = 0.5


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


def periodic(tab):
    """[[bearing, v...], ...] -> f(bearing) -> [v...], linear, periodic over 360"""
    t = np.array(sorted([[r[0] % 360] + list(r[1:]) for r in tab]), float)
    b = np.concatenate([t[:, 0] - 360, t[:, 0], t[:, 0] + 360])
    cols = [np.concatenate([t[:, k]] * 3) for k in range(1, t.shape[1])]
    return lambda q: [float(np.interp(q % 360, b, c)) for c in cols]


_F = periodic(D['fence']); _G = periodic(D['front_gap']); _RF = periodic(D['rf']); _RB = periodic(D['rb'])
def rF(b): return _F(b)[0]
def r0(b): return rF(b) + _G(b)[0]
def roof_front(b): return _RF(b)[0]
def roof_back(b): return _RB(b)[0]


def pol(b, r):
    a = math.radians(b); return (r * math.sin(a), r * math.cos(a))


def P3(b, r, z):
    return (*pol(b, r), z)


def arc(b0, b1, step=STEP):
    n = max(1, int(round(abs(b1 - b0) / step))); return list(np.linspace(b0, b1, n + 1))


def radial(b):
    a = math.radians(b); return np.array([math.sin(a), math.cos(a), 0.0])


def tangent(b):
    a = math.radians(b); return np.array([math.cos(a), -math.sin(a), 0.0])


def quad_strip(mb, bs, A, B, m, tu=None):
    """Faces between two section points A(b)->(r,z) and B(b)->(r,z) over bearings bs, UV u round the ground."""
    kk = math.pi / 180; tu, tv = TILE.get(m, (1.0, 1.0))
    for b0, b1 in zip(bs, bs[1:]):
        a0, a1, c0, c1 = A(b0), A(b1), B(b0), B(b1)
        rm = 0.25 * (a0[0] + a1[0] + c0[0] + c1[0]); L = math.hypot(c0[0] - a0[0], c0[1] - a0[1]) / tv
        u0, u1 = b0 * kk * rm / tu, b1 * kk * rm / tu
        mb.face([P3(b0, *a0), P3(b1, *a1), P3(b1, *c1), P3(b0, *c0)], m,
                uv=[(u0, 0), (u1, 0), (u1, L), (u0, L)])


def sweep(mb, bs, sec):
    """sec(b) -> [(r, z, material of the segment ending here), ...], a fixed length; faces each segment over bs."""
    n = len(sec(bs[0]))
    S = [sec(b) for b in bs]
    for k in range(1, n):
        m = S[0][k][2]
        if m is None:
            continue
        quad_strip(mb, bs, lambda b, k=k: sec(b)[k - 1][:2], lambda b, k=k: sec(b)[k][:2], m)


def endcap(mb, b, S, m, flip=False):
    """Close a section at bearing b with the polygon S [(r, z)] (the section and the ground under it)."""
    from mb import earclip
    poly = [(r, z) for r, z in S]
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    for tri in earclip(poly if area > 0 else poly[::-1]):
        q = [P3(b, r, z) for r, z in tri]
        mb.face(q if flip else q[::-1], m)


# ---------------- the bowl ----------------
# Rows: tread 0.80 m; the lower tier rises 0.38 m a row, the upper 0.45 m (the photo sphere's rake). A cross aisle
# 1.8 m wide splits them under the roofs; the upper tier starts a 1.0 m wall above it. Behind the top row: a
# platform under the roof (a raised row of boxes behind a parapet), then the back wall.
FRONT_Z = 1.4
TREAD = 0.80
LOW_N, LOW_RISE = 13, 0.36
AISLE = 1.8
# Level 3 between the tiers: the corporate suites (Sydney Showground fact sheet: suites 1-12 and function rooms on
# L3). A glazed front 2.5 m tall, set 0.6 m back under the upper tier's 0.6 m fascia (photo sphere: the dark band
# between the tiers right round the bowl).
SUITE_H, FASCIA_H, OVER = 2.5, 0.6, 0.6
UP_N, UP_RISE = 9, 0.42
OPEN_N, OPEN_RISE = 16, 0.40


def stand_at(b):
    bb = b % 360
    for s in D['stands']:
        b0, b1 = s['b0'], s['b1']
        if b0 <= bb <= b1 or b0 <= bb + 360 <= b1:
            return s
    return None


def is_open(b):
    """The open north-east end, without a roof."""
    return 8.0 <= b % 360 <= 72.0


def tier_low(b):
    a = r0(b) + 0.3; return a, FRONT_Z, a + LOW_N * TREAD, FRONT_Z + LOW_N * LOW_RISE


def tier_up(b):
    _, _, r1, z1 = tier_low(b); a = r1 + AISLE; z = z1 + SUITE_H + FASCIA_H
    return a, z, a + UP_N * TREAD, z + UP_N * UP_RISE


def tier_open(b):
    a = r0(b) + 0.3; return a, FRONT_Z, a + OPEN_N * TREAD, FRONT_Z + OPEN_N * OPEN_RISE


def back_r(b):
    """The stand's outside wall: 1.5 m in from the roof's back edge (the roof overhangs it)."""
    return roof_back(b) - 1.5


def top_z(b):
    return tier_up(b)[3]


def stepped(r0_, z0, n, run, rise, mt='tread', mr='riser'):
    out = []
    for k in range(n):
        out += [(r0_ + k * run, z0 + (k + 1) * rise, mr), (r0_ + (k + 1) * run, z0 + (k + 1) * rise, mt)]
    return out


def sec_roofed(b):
    f = r0(b); a0, z0, a1, z1 = tier_low(b); c0, e0, c1, e1 = tier_up(b); rb = back_r(b)
    return ([(f, 0.0, None), (f, FRONT_Z, 'stand_front'), (a0, FRONT_Z, 'conc_light')]
            + stepped(a0, z0, LOW_N, TREAD, LOW_RISE)
            + [(c0 + OVER, z1, 'conc_light'), (c0 + OVER, z1 + SUITE_H, 'suite_glass'), (c0, z1 + SUITE_H, 'soffit'),
               (c0, e0, 'tier_fascia')]
            + stepped(c0, e0, UP_N, TREAD, UP_RISE)
            + [(c1 + 1.6, e1, 'conc_light'), (c1 + 1.6, e1 + 1.1, 'parapet'), (c1 + 1.8, e1 + 1.1, 'parapet'),
               (c1 + 1.8, e1 + 0.9, 'parapet'), (rb, e1 + 0.9, 'deck')])


def sec_open(b):
    f = r0(b); a0, z0, a1, z1 = tier_open(b)
    return ([(f, 0.0, None), (f, FRONT_Z, 'stand_front'), (a0, FRONT_Z, 'conc_light')]
            + stepped(a0, z0, OPEN_N, TREAD, OPEN_RISE)
            + [(a1 + 2.6, z1, 'conc_light'), (a1 + 2.6, z1 + 1.1, 'parapet'), (a1 + 2.8, z1 + 1.1, 'parapet'),
               (a1 + 2.8, 0.0, 'conc_back')])


def bowl(col):
    mb = MB('bowl')
    race0, race1 = D['race']
    # under the roofs: every bearing from the end of the open stand round to its start
    rs = arc(72.0, 368.0)
    sweep(mb, rs, sec_roofed)
    # the open north-east end, either side of the players' race
    for b0_, b1_ in ((8.0, race0), (race1, 72.0)):
        sweep(mb, arc(b0_, b1_), sec_open)
    # joins: the open stand's ends meet the roofed bowl's rows (its upper tier is higher): end walls
    for b, flip in ((8.0, True), (72.0, False)):
        S = sec_roofed(b); O = sec_open(b)
        # the roofed section's outline above the open one: close it with its own end wall
        poly = [(p[0], p[1]) for p in S] + [(S[-1][0], 0.0), (S[0][0], 0.0)]
        endcap(mb, b, poly, 'conc_back', flip=not flip)
    race(mb)
    mb.build(col)


def race(mb):
    """The players' race through the open stand: a ramped trench between concrete walls from the field to a
    tunnel mouth under the back rows, a steel bridge across it at the top row."""
    b0, b1 = D['race']
    for b, side in ((b0, 1), (b1, -1)):
        O = sec_open(b)
        poly = [(p[0], p[1]) for p in O[1:-1]] + [(O[-2][0], 0.0)]
        endcap(mb, b, poly, 'conc_light', flip=side < 0)
    # floor and tunnel (4 m in from the open stand's top row, at every bearing across the race)
    bm = 0.5 * (b0 + b1)
    rt = lambda b: tier_open(b)[2] - 4.0
    bs = arc(b0, b1, 0.5)
    quad_strip(mb, bs, lambda b: (r0(b), 0.02), lambda b: (rt(b), 0.02), 'race_floor')
    # tunnel: its mouth's lintel and the dark inside
    quad_strip(mb, bs, lambda b: (rt(b), 2.8), lambda b: (rt(b), tier_open(b)[3] + 0.1), 'conc_back')
    quad_strip(mb, bs, lambda b: (rt(b) + 3.0, 0.0), lambda b: (rt(b) + 3.0, 2.8), 'vom_dark')
    quad_strip(mb, bs, lambda b: (rt(b) + 3.0, 2.8), lambda b: (rt(b), 2.8), 'vom_dark')
    for b, s_ in ((b0, 1), (b1, -1)):
        q = [P3(b, rt(b), 0), P3(b, rt(b) + 3.0, 0), P3(b, rt(b) + 3.0, 2.8), P3(b, rt(b), 2.8)]
        mb.face(q if s_ > 0 else q[::-1], 'vom_dark')
    # the top rows run over the tunnel (the bridge): treads and risers above it, the same last K profile points
    K = sum(1 for p in sec_open(bm) if p[0] >= rt(bm) - 0.01)
    S = lambda b: sec_open(b)[-K:]
    for k in range(1, K):
        m = S(b0)[k][2]
        if m:
            quad_strip(mb, bs, lambda b, k=k: S(b)[k - 1][:2], lambda b, k=k: S(b)[k][:2], m)
    # handrails along the race walls
    for b in (b0, b1):
        f = r0(b); p = P3(b, f, 2.4); q = P3(b, rt(b), tier_open(b)[1] + (rt(b) - f) * 0.5 + 1.0)
        mb.beam(p, q, 0.06, 0.06, 'steel_galv')


# ---------------- aisles and handrails ----------------
AISLE_EVERY = 15.0
AISLE_W = 1.2


def aisle_bearings(b0, b1, r):
    L = math.radians(b1 - b0) * r; n = max(1, int(round(L / AISLE_EVERY)))
    return [b0 + (b1 - b0) * k / n for k in range(n + 1)]


def tiers_at(b):
    """[(r_front, z_front, n, run, rise), ...] of the seated tiers at bearing b."""
    if is_open(b):
        a0, z0, a1, z1 = tier_open(b); return [(a0, z0, OPEN_N, TREAD, OPEN_RISE)]
    a0, z0, a1, z1 = tier_low(b); c0, e0, c1, e1 = tier_up(b)
    return [(a0, z0, LOW_N, TREAD, LOW_RISE), (c0, e0, UP_N, TREAD, UP_RISE)]


def blocks():
    """Seating blocks as (b0, b1) between aisles round the bowl."""
    out = []
    parts = [(72.0, 368.0)] if False else []
    for s in D['stands']:
        out.append((s['b0'], s['b1']))
    # the tower gaps between roofs carry seats too
    st = sorted(D['stands'], key=lambda s: s['b0'])
    for i, s in enumerate(st):
        n = st[(i + 1) % len(st)]
        g0, g1 = s['b1'], n['b0'] + (360 if n['b0'] < s['b1'] - 180 else 0)
        if g1 - g0 > 0.5:
            out.append((g0, g1))
    # split the open end at the race
    res = []
    for b0, b1 in out:
        r0_, r1_ = D['race']
        if b0 < r0_ < b1:
            res += [(b0, r0_), (r1_, b1)]
        else:
            res.append((b0, b1))
    return sorted(res)


def aisle_list():
    """Every aisle as a bearing, by seating block, at least one between blocks."""
    out = set()
    for b0, b1 in blocks():
        r = r0((b0 + b1) / 2) + 8
        for a in aisle_bearings(b0, b1, r):
            out.add(round(a % 360, 3))
    rc0, rc1 = D['race']
    return sorted(a for a in out if not (rc0 - 0.01 <= a <= rc1 + 0.01))


def aisles(col):
    """Each aisle: a half step on every row (two steps a row) and a galvanised handrail up its middle."""
    mb = MB('aisles')
    for b in aisle_list():
        t = tangent(b); u = radial(b)
        for r_a, z_a, n, run, rise in tiers_at(b):
            for k in range(n):
                rr = r_a + k * run; zz = z_a + k * rise
                c = np.array(P3(b, rr + run * 0.5 + 0.02, 0)); w = AISLE_W
                # the half step: a box from the tread up half a riser, over the row's front half
                lo = zz; hi = zz + rise * 0.5
                cs = [c + t * w / 2 - u * run * 0.25, c - t * w / 2 - u * run * 0.25, c - t * w / 2 + u * run * 0.25, c + t * w / 2 + u * run * 0.25]
                P = [tuple(p + np.array([0, 0, lo])) for p in cs]; Q = [tuple(p + np.array([0, 0, hi])) for p in cs]
                mb.face(Q[::-1] if False else Q, 'step_edge')
                for i in range(4):
                    j = (i + 1) % 4; mb.face([P[i], P[j], Q[j], Q[i]], 'step_edge')
            # handrail up the middle: posts every 3 rows, a rail 0.9 m above the nosings
            p0 = P3(b, r_a + 0.3, z_a + 0.9); p1 = P3(b, r_a + n * run - 0.3, z_a + n * rise + 0.9)
            mb.beam(p0, p1, 0.05, 0.05, 'steel_galv')
            for k in range(0, n, 3):
                rr = r_a + k * run + run * 0.5; zz = z_a + (k + 1) * rise
                mb.beam(P3(b, rr, zz), P3(b, rr, zz + 0.9 + rise * 0.5), 0.05, 0.05, 'steel_galv')
    mb.build(col)


# ---------------- vomitories: tunnels up through the back of the lower tier ----------------
VOM_W = 2.6
VOM_ROWS = 6


def vom_list():
    """At the middle of every other block under the roofs: the bearing of each vomitory."""
    out = []
    al = aisle_list()
    for b0, b1 in blocks():
        if is_open((b0 + b1) / 2):
            continue
        inside = [a for a in al if b0 - 0.01 <= a <= b1 + 0.01] or [b0, b1]
        inside = sorted(set([b0] + inside + [b1]))
        for j in range(0, len(inside) - 1, 2):
            if inside[j + 1] - inside[j] > 3.0:
                out.append(0.5 * (inside[j] + inside[j + 1]))
    return out


def vomitories(col):
    mb = MB('vomitories')
    for b in vom_list():
        r_a, z_a, r_b, z_b = tier_low(b)
        ra = r_a + (LOW_N - VOM_ROWS) * TREAD; za = z_a + (LOW_N - VOM_ROWS) * LOW_RISE
        u = radial(b); t = tangent(b)
        P = lambda r, s, z: tuple(u * r + t * s + np.array([0, 0, z]))
        w = VOM_W / 2; top = z_b + 0.15; th = 0.3; zo = za + 2.4
        for s_ in (-1, 1):
            o, i = s_ * w, s_ * (w - th)
            mb.face([P(ra, o, za - 0.2), P(r_b, o, za - 0.2), P(r_b, o, top), P(ra, o, top)][::(1 if s_ < 0 else -1)], 'vom_conc')
            mb.face([P(ra, i, za - 0.2), P(ra, i, top), P(r_b, i, top), P(r_b, i, za - 0.2)][::(1 if s_ < 0 else -1)], 'vom_dark')
            mb.face([P(ra, o, za - 0.2), P(ra, o, top), P(ra, i, top), P(ra, i, za - 0.2)][::(-1 if s_ < 0 else 1)], 'vom_conc')
        mb.face([P(ra, -w, top), P(r_b, -w, top), P(r_b, w, top), P(ra, w, top)], 'vom_conc')
        mb.face([P(ra, -w + th, zo), P(ra, w - th, zo), P(ra, w - th, top), P(ra, -w + th, top)], 'vom_conc')
        mb.face([P(ra, -w + th, zo), P(r_b, -w + th, zo), P(r_b, w - th, zo), P(ra, w - th, zo)][::-1], 'vom_dark')
        mb.face([P(r_b, -w + th, za - 0.2), P(r_b, w - th, za - 0.2), P(r_b, w - th, zo), P(r_b, -w + th, zo)], 'vom_dark')
        mb.face([P(ra, -w + th, za + 0.02), P(r_b, -w + th, za + 0.02), P(r_b, w - th, za + 0.02), P(ra, w - th, za + 0.02)], 'conc_light')
        # handrails either side of the mouth, on the rows beside it
        for s_ in (-1, 1):
            mb.beam(P(ra - 0.2, s_ * (w + 0.1), za + 0.95), P(r_b - 0.4, s_ * (w + 0.1), top + 0.95), 0.05, 0.05, 'steel_galv')
    mb.build(col)


# ---------------- roofs ----------------
# Heights, by eye: the roofs' front edges about 17 m over the field and their backs a little lower; the old
# segments arch up about 2.4 m mid-span between their towers. The underside is
# a corrugated deck 0.9 m under the sheet, on radial rafters.
ROOF_ZF, ROOF_ZB, ROOF_TH = 17.0, 16.5, 0.9
ARCH = 2.4


def roof_top(s, b, r):
    """The roof sheet's height at bearing b, radius r, on stand s."""
    rf_, rb_ = roof_front(b), roof_back(b); t = min(1.0, max(0.0, (r - rf_) / max(1.0, rb_ - rf_)))
    z = ROOF_ZF + (ROOF_ZB - ROOF_ZF) * t
    if s['kind'] == 'old':
        z += ARCH * math.sin(math.pi * min(1.0, max(0.0, (b - s['b0']) / (s['b1'] - s['b0']))))
    return z


def roofed():
    return [s for s in D['stands'] if s['kind'] != 'open']


def roof(col):
    mb = MB('roofs')
    for s in roofed():
        b0, b1 = s['b0'] - (0.0 if s['kind'] == 'old' else 1.0), s['b1'] + (0.0 if s['kind'] == 'old' else 1.0)
        bs = arc(b0, b1, 0.5)
        RS = lambda b, f: roof_front(b) + (roof_back(b) - roof_front(b)) * f
        fr = np.linspace(0, 1, 9)
        for b_0, b_1 in zip(bs, bs[1:]):
            for f0, f1 in zip(fr, fr[1:]):
                q = [(b_0, RS(b_0, f0)), (b_1, RS(b_1, f0)), (b_1, RS(b_1, f1)), (b_0, RS(b_0, f1))]
                top = [P3(b, r, roof_top(s, b, r)) for b, r in q]
                bot = [P3(b, r, roof_top(s, b, r) - ROOF_TH) for b, r in q]
                kk = math.pi / 180; rm = RS(b_0, 0.5); tu, tv = TILE.get('roof_top', (1, 1))
                uv = [(b * kk * rm / tu, r / tv) for b, r in q]
                mb.face(top, 'roof_top', uv=uv); mb.face(bot[::-1], 'roof_under', uv=uv[::-1])
            # front and back fascias
            for f, m, out in ((0.0, 'fascia', -1), (1.0, 'fascia_back', 1)):
                a = (b_0, RS(b_0, f)); c = (b_1, RS(b_1, f))
                q = [P3(a[0], a[1], roof_top(s, *a) - ROOF_TH - 0.2), P3(c[0], c[1], roof_top(s, *c) - ROOF_TH - 0.2),
                     P3(c[0], c[1], roof_top(s, *c) + 0.15), P3(a[0], a[1], roof_top(s, *a) + 0.15)]
                mb.face(q if out < 0 else q[::-1], m)
        for b, sg in ((b0, 1), (b1, -1)):
            pts = [(roof_front(b) + (roof_back(b) - roof_front(b)) * f) for f in fr]
            top = [P3(b, r, roof_top(s, b, r) + 0.15) for r in pts]; bot = [P3(b, r, roof_top(s, b, r) - ROOF_TH - 0.2) for r in pts]
            for i in range(len(pts) - 1):
                q = [bot[i], bot[i + 1], top[i + 1], top[i]]
                mb.face(q if sg > 0 else q[::-1], 'fascia')
        roof_under_frame(mb, s, b0, b1)
        if s['kind'] != 'old':
            roof_trusses(mb, s, b0, b1)
        roof_lights(mb, s, b0, b1)
    stays(mb)
    roof_edge_floods(mb)
    mb.build(col)


def roof_under_frame(mb, s, b0, b1):
    """Radial rafters (0.35 m deep steel ribs, every ~5 m at the front) and two purlin lines under the deck; round
    columns from the back platform up to the rafters, every ~12 m."""
    r = roof_front((b0 + b1) / 2); n = max(2, int(round(math.radians(b1 - b0) * r / 5.0)))
    for k in range(n + 1):
        b = b0 + (b1 - b0) * k / n
        ra, rb_ = roof_front(b) + 0.3, roof_back(b) - 0.3
        pts = np.linspace(ra, rb_, 6)
        for p, q in zip(pts, pts[1:]):
            mb.beam(P3(b, p, roof_top(s, b, p) - ROOF_TH - 0.17), P3(b, q, roof_top(s, b, q) - ROOF_TH - 0.17), 0.22, 0.35, 'steel_under')
    for f in (0.3, 0.65):
        bs = arc(b0, b1, 2.0)
        for p, q in zip(bs, bs[1:]):
            rp = roof_front(p) + (roof_back(p) - roof_front(p)) * f; rq = roof_front(q) + (roof_back(q) - roof_front(q)) * f
            mb.beam(P3(p, rp, roof_top(s, p, rp) - ROOF_TH - 0.15), P3(q, rq, roof_top(s, q, rq) - ROOF_TH - 0.15), 0.18, 0.3, 'steel_under')
    # columns: on the line of the box parapet, every ~12 m
    rc = lambda b: tier_up(b)[2] + 1.7
    n = max(2, int(round(math.radians(b1 - b0) * rc((b0 + b1) / 2) / 12.0)))
    for k in range(1, n):
        b = b0 + (b1 - b0) * k / n; r = rc(b); z0 = tier_up(b)[3]
        mb.cyl(pol(b, r), 0.28, z0, roof_top(s, b, r) - ROOF_TH - 0.25, 'steel_white', n=12)
        mb.cyl(pol(b, r), 0.42, roof_top(s, b, r) - ROOF_TH - 0.6, roof_top(s, b, r) - ROOF_TH - 0.25, 'steel_white', n=12)


def roof_trusses(mb, s, b0, b1):
    """The 2012 roofs (north and east): radial A-frame trusses standing 3 m on the sheet, every ~8 m."""
    rm = lambda b: 0.5 * (roof_front(b) + roof_back(b))
    n = max(2, int(round(math.radians(b1 - b0) * rm((b0 + b1) / 2) / 8.0)))
    for k in range(n + 1):
        b = b0 + 0.5 + (b1 - b0 - 1.0) * k / n
        ra, rb_ = roof_front(b) + 1.0, roof_back(b) - 1.0; rmid = 0.5 * (ra + rb_)
        apex = P3(b, rmid, roof_top(s, b, rmid) + 3.0)
        A = P3(b, ra, roof_top(s, b, ra) + 0.1); B = P3(b, rb_, roof_top(s, b, rb_) + 0.1)
        mb.beam(A, apex, 0.25, 0.25, 'steel_white'); mb.beam(apex, B, 0.25, 0.25, 'steel_white')
        mb.beam(A, B, 0.2, 0.2, 'steel_white')
        for f in (0.25, 0.5, 0.75):
            r = ra + (rb_ - ra) * f; zt = roof_top(s, b, r)
            h = 3.0 * (1 - abs(r - rmid) / (rmid - ra))
            mb.beam(P3(b, r, zt + 0.1), P3(b, r, zt + h), 0.12, 0.12, 'steel_white')
        for f0, f1 in ((0.0, 0.25), (0.25, 0.5), (0.75, 0.5), (1.0, 0.75)):
            r0_ = ra + (rb_ - ra) * f0; r1_ = ra + (rb_ - ra) * f1
            h1 = 3.0 * (1 - abs(r1_ - rmid) / (rmid - ra))
            mb.beam(P3(b, r0_, roof_top(s, b, r0_) + 0.1), P3(b, r1_, roof_top(s, b, r1_) + h1), 0.08, 0.08, 'steel_white')


def roof_lights(mb, s, b0, b1):
    """Downlights under the front fascia every ~6 m (the photo sphere's black fittings)."""
    r = roof_front((b0 + b1) / 2); n = max(2, int(round(math.radians(b1 - b0) * r / 6.0)))
    for k in range(n):
        b = b0 + (b1 - b0) * (k + 0.5) / n; rr = roof_front(b) + 0.8; z = roof_top(s, b, rr) - ROOF_TH - 0.2
        t = tangent(b); u = radial(b); c = np.array(P3(b, rr, z))
        mb.beam(tuple(c), tuple(c - np.array([0, 0, 0.5])), 0.08, 0.08, 'steel_dark')
        lc = c - np.array([0, 0, 0.75]) - u * 0.1
        mb.beam(tuple(lc - t * 0.35), tuple(lc + t * 0.35), 0.45, 0.4, 'steel_dark')


def stays(mb):
    """Every roof hangs in part from the light towers (photo sphere: fans of white cables from each tower's
    crossbar, where the head starts to flare, down to the roof either side). The two towers beside the open end
    carry only the north and east roofs, on one side each."""
    for T in D['towers']:
        tb = T['b']
        for end, s in tower_neighbours(T):
            a = tower_point(T, tower_zx(T), end * 0.5 * tower_w(T, tower_zx(T)), 0.0)
            near = s['b1'] if end * tower_side_sign(T, s) < 0 else s['b0']
            sg = 1 if near == s['b0'] else -1
            far_n = 5 if 'stays' in T else 3
            rr = roof_front(near) + 0.4 * (roof_back(near) - roof_front(near))
            for k in range(far_n):
                d_m = 6.0 + k * 8.0
                b = near + sg * math.degrees(d_m / rr)
                for f in ((0.2, 0.6) if 'stays' in T else (0.4,)):
                    r = roof_front(b) + (roof_back(b) - roof_front(b)) * f
                    q = P3(b, r, roof_top(s, b, r) + 0.15)
                    mb.beam(tuple(a), q, 0.06, 0.06, 'cable')
                    mb.box(pol(b, r), 0.5, 0.3, 0.25, 90 - b, 'steel_white', z0=roof_top(s, b, r) + 0.02)


# ---------------- level 3: the suites' glazed front between the tiers ----------------
def suites(col):
    """Aluminium mullions every 1.5 m on the suites' glass (between the walkway and the upper tier's soffit), a
    concrete pier every fourth one where the suites divide, and a glass balustrade along the walkway's edge."""
    mb = MB('suites')
    b0, b1 = 72.0, 368.0
    L, P = arc_frame(b0, b1, lambda b: tier_up(b)[0] + OVER)
    zf = lambda s_: tier_low(float(np.interp(s_, [0, L], [b0, b1])))[3]
    for k, s_ in enumerate(np.arange(0.75, L, 1.5)):
        z1 = zf(s_)
        if k % 4 == 0:
            panel(mb, P, s_ - 0.15, s_ + 0.15, z1, z1 + SUITE_H, -0.12, 'conc_light')
            for sg in (-1, 1):
                mb.face([P(s_ + sg * 0.15, z1, 0.0), P(s_ + sg * 0.15, z1, -0.12), P(s_ + sg * 0.15, z1 + SUITE_H, -0.12), P(s_ + sg * 0.15, z1 + SUITE_H, 0.0)][::sg], 'conc_light')
        else:
            mb.beam(P(s_, z1, -0.05), P(s_, z1 + SUITE_H, -0.05), 0.07, 0.1, 'steel_dark')
    # a transom at door head height
    ss = np.arange(0.0, L, 3.0)
    for a, b in zip(ss, ss[1:]):
        mb.beam(P(a, zf(a) + 2.1, -0.05), P(b, zf(b) + 2.1, -0.05), 0.06, 0.08, 'steel_dark')
    # the walkway's glass balustrade at the back of the lower tier: posts every 1.5 m, a top rail
    L2, P2 = arc_frame(b0, b1, lambda b: tier_low(b)[2] + 0.1)
    for a in np.arange(0.0, L2, 1.5):
        z = zf(a); mb.beam(P2(a, z), P2(a, z + 1.0), 0.05, 0.05, 'steel_galv')
    ss = np.arange(0.0, L2, 3.0)
    for a, b in zip(ss, ss[1:]):
        za, zb_ = zf(a), zf(b)
        mb.beam(P2(a, za + 1.0), P2(b, zb_ + 1.0), 0.06, 0.06, 'steel_galv')
        mb.face([P2(a, za + 0.1), P2(b, zb_ + 0.1), P2(b, zb_ + 0.95), P2(a, za + 0.95)], 'balustrade_glass')
        mb.face([P2(a, za + 0.95), P2(b, zb_ + 0.95), P2(b, zb_ + 0.1), P2(a, za + 0.1)], 'balustrade_glass')
    mb.build(col)


def roof_edge_floods(mb):
    """"A further eight clusters of six units are used on the leading edge of the roof" (ANCR 2012): a bracket of
    six floods (two rows of three) under the front fascia, two on the long east roof, one mid-roof elsewhere."""
    spots = []
    for s in roofed():
        n = 2 if s['name'] == 'E' else 1
        spots += [(s, s['b0'] + (s['b1'] - s['b0']) * (k + 1) / (n + 1)) for k in range(n)]
    for s, b in spots:
        u = radial(b); t = tangent(b); rr = roof_front(b) + 0.2; z = roof_top(s, b, rr) - ROOF_TH - 0.25
        c = np.array(P3(b, rr, z))
        mb.beam(tuple(c), tuple(c - np.array([0, 0, 0.9])), 0.12, 0.12, 'steel_dark')
        bar = c - np.array([0, 0, 0.9]) - u * 0.25
        mb.beam(tuple(bar - t * 1.5), tuple(bar + t * 1.5), 0.1, 0.1, 'steel_dark')
        tilt = math.radians(35); fz = -u * math.cos(tilt) - np.array([0, 0, 1.0]) * math.sin(tilt)
        uz = np.array([0, 0, 1.0]) * math.cos(tilt) - u * math.sin(tilt)
        for j in range(2):
            for i in range(3):
                c0 = bar + t * (i - 1) * 1.0 + uz * (j - 0.5) * 0.75 - u * 0.2
                cs = [c0 + t * (du * 0.34) + uz * (dv * 0.3) for du, dv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                cf = [p + fz * 0.28 for p in cs]
                for k in range(4):
                    mb.face([tuple(cs[k]), tuple(cs[(k + 1) % 4]), tuple(cf[(k + 1) % 4]), tuple(cf[k])][::-1], 'lamp_body')
                mb.face([tuple(p) for p in cf][::-1], 'lamp_face'); mb.face([tuple(p) for p in cs], 'lamp_body')


# ---------------- light towers ----------------
# Eight red lattice towers (modelled by eye from photos; "six distinctive triangular red painted architectural
# towers" of 1998 and two of 2012 at the north-east end, ANCR 2012). Triangular in section: two legs on the face
# toward the field, one behind. By eye from photos: the legs spread from about 2.4 m apart at
# roof level to 5.5 m at a heavy crossbar 10 m under the top, with a Y of members inside under it; above
# the crossbar the head flares on the same V to 10 m wide at the top; its top 5 m is the lamp frame (four rows of
# 11 LED floods, 348 in the ground since 2024), the band under it a pale mesh screen. Bases from OSM's mapped
# masts, tops (46 m, leaning in 6-8 m) triangulated from Google Earth; the six in the roof gaps stand on the gap decks.
TW_XDROP, TW_LAMP, TW_TOPW, TW_XW, TW_DP = 10.0, 5.0, 10.0, 5.5, 1.5


def _seat_towers():
    """A tower in a roof gap stands on the gap block's deck, behind the top row: where OSM maps the mast over
    the rows (within its few metres), its base moves out to the deck (1.4 m behind the block's front wall)."""
    for T in D['towers']:
        if T['base'][2] < 1.0:
            continue
        e, n = T['base'][:2]; r = math.hypot(e, n); need = tier_up(T['b'])[2] + 1.8 + TW_DP / 2 + 0.65
        if r < need:
            T['base'][0], T['base'][1] = e * need / r, n * need / r


_seat_towers()


def tower_zx(T):
    return T['top'][2] - TW_XDROP


def tower_w(T, z):
    """The width between the two field-side legs at height z."""
    zx = tower_zx(T)
    if z <= zx:
        return max(1.4, TW_XW + (TW_XW - 2.4) / (zx - 17.0) * (z - zx))
    return TW_XW + (TW_TOPW - TW_XW) * (z - zx) / TW_XDROP


def tower_axes(T):
    top = np.array(T['top'], float)
    toc = -np.array([top[0], top[1], 0.0]); toc /= np.linalg.norm(toc)
    side = np.cross(toc, [0, 0, 1.0]); side /= np.linalg.norm(side)
    return toc, side


def tower_point(T, z, u, v):
    """A point at height z, u metres along the face (tangential), v metres toward the field from the axis."""
    base = np.array(T['base'], float); top = np.array(T['top'], float)
    c = base + (top - base) * ((z - base[2]) / (top[2] - base[2]))
    toc, side = tower_axes(T)
    return c + side * u + toc * v


def tower_side_sign(T, s):
    """+1 if stand s lies on the tower's +side, else -1."""
    toc, side = tower_axes(T)
    bm = 0.5 * (s['b0'] + s['b1'])
    p = np.array(P3(bm, 100.0, 0.0)) - np.array(T['top'], float)
    return 1 if np.dot(p, side) > 0 else -1


def tower_neighbours(T):
    """[(end, stand)] for the roofs either side the tower carries (end -1/+1 = which crossbar end)."""
    out = []
    names = [T['stays']] if 'stays' in T else None
    for s in roofed():
        if names is not None and s['name'] not in names:
            continue
        gap = min(abs(((T['b'] - s['b1']) + 180) % 360 - 180), abs(((s['b0'] - T['b']) + 180) % 360 - 180))
        if gap < 8.0:
            out.append((tower_side_sign(T, s), s))
    return out


def towers(col):
    mb = MB('light_towers')
    for T in D['towers']:
        zb, zt = T['base'][2], T['top'][2]; zx = tower_zx(T); zl = zt - TW_LAMP; zy = zx - 6.0
        toc, side = tower_axes(T)
        W = lambda z: tower_w(T, z)
        F = lambda z, sg: tuple(tower_point(T, z, sg * 0.5 * W(z), 0.5 * TW_DP))   # field-side legs
        Bk = lambda z: tuple(tower_point(T, z, 0.0, -0.5 * TW_DP))                  # the back leg
        zs = list(np.arange(zb, zx, 1.6)) + [zx]
        zh = list(np.linspace(zx, zt, 7))
        # legs, following the V (piecewise, so the bend at the crossbar is kept)
        for a, b in zip(zs + zh[1:], (zs + zh[1:])[1:]):
            for sg in (-1, 1):
                mb.beam(F(a, sg), F(b, sg), 0.34, 0.34, 'tower_red')
            mb.beam(Bk(a), Bk(b), 0.3, 0.3, 'tower_red')
        # mast bracing: rungs across the face, an X in each face bay, a zigzag on the two side faces
        for i, (a, b) in enumerate(zip(zs, zs[1:])):
            mb.beam(F(a, -1), F(a, 1), 0.14, 0.14, 'tower_red')
            if a < zy:
                mb.beam(F(a, -1), F(b, 1), 0.1, 0.1, 'tower_red'); mb.beam(F(a, 1), F(b, -1), 0.1, 0.1, 'tower_red')
            for sg in (-1, 1):
                p, q = (F(a, sg), Bk(b)) if i % 2 == 0 else (Bk(a), F(b, sg))
                mb.beam(p, q, 0.1, 0.1, 'tower_red'); mb.beam(F(a, sg), Bk(a), 0.11, 0.11, 'tower_red')
        # the heavy crossbar, a lighter one where the Y meets, the Y itself and the centre post up the head
        mb.beam(F(zx, -1), F(zx, 1), 0.45, 0.45, 'tower_red')
        for sg in (-1, 1):
            mb.beam(F(zx, sg), Bk(zx), 0.22, 0.22, 'tower_red')
        mb.beam(F(zy, -1), F(zy, 1), 0.2, 0.2, 'tower_red')
        cy = tuple(tower_point(T, zy, 0.0, 0.5 * TW_DP))
        for sg in (-1, 1):
            mb.beam(F(zx, sg), cy, 0.16, 0.16, 'tower_red')
        mb.beam(cy, tuple(tower_point(T, zt, 0.0, 0.5 * TW_DP)), 0.16, 0.16, 'tower_red')
        # the head: rails across at each level, raking members back to the rear leg
        for z in zh:
            mb.beam(F(z, -1), F(z, 1), 0.2, 0.2, 'tower_red')
            for sg in (-1, 1):
                mb.beam(F(z, sg), Bk(z), 0.1, 0.1, 'tower_red')
        mb.beam(Bk(zt), tuple(tower_point(T, zt, -0.5 * W(zt), -0.5 * TW_DP)), 0.12, 0.12, 'tower_red')
        mb.beam(Bk(zt), tuple(tower_point(T, zt, 0.5 * W(zt), -0.5 * TW_DP)), 0.12, 0.12, 'tower_red')
        # the mesh screen between the crossbar and the lamp frame: vertical slats 0.3 m apart
        zs0, zs1 = zx + 0.25, zl - 0.15
        for u in np.arange(-0.5 * W(zs1) + 0.2, 0.5 * W(zs1) - 0.1, 0.3):
            z0 = zs0 if abs(u) < 0.5 * W(zs0) - 0.15 else zx + (2 * abs(u) + 0.3 - TW_XW) / (TW_TOPW - TW_XW) * TW_XDROP
            if z0 >= zs1 - 0.2:
                continue
            mb.beam(tuple(tower_point(T, z0, u, 0.5 * TW_DP - 0.12)), tuple(tower_point(T, zs1, u, 0.5 * TW_DP - 0.12)), 0.05, 0.14, 'tower_mesh')
        # the lamp frame: four rows of 11 LED floods, aimed down at the field
        tilt = math.radians(25)
        fz = toc * math.cos(tilt) - np.array([0, 0, 1.0]) * math.sin(tilt)
        uz = np.array([0, 0, 1.0]) * math.cos(tilt) + toc * math.sin(tilt)
        for j in range(4):
            z = zl + (j + 0.5) * TW_LAMP / 4; w = W(z) - 0.9
            for i in range(11):
                u = -w / 2 + (i + 0.5) * w / 11
                c0 = tower_point(T, z, u, 0.5 * TW_DP + 0.15)
                ex, ey = 0.36, 0.32
                c = [c0 + side * (du * ex) + uz * (dv * ey) for du, dv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                cf = [p + fz * 0.3 for p in c]
                for k in range(4):
                    mb.face([tuple(c[k]), tuple(c[(k + 1) % 4]), tuple(cf[(k + 1) % 4]), tuple(cf[k])], 'lamp_body')
                mb.face([tuple(p) for p in cf], 'lamp_face'); mb.face([tuple(p) for p in c[::-1]], 'lamp_body')
                mb.beam(tuple(c0 - toc * 0.1), tuple(c0 + fz * 0.05), 0.06, 0.06, 'lamp_body')
        # a grated catwalk behind the lamp frame with its guard rail
        cw = [tuple(tower_point(T, zl - 0.1, sg * 0.5 * W(zl), v)) for sg, v in ((-1, 0.5 * TW_DP), (1, 0.5 * TW_DP), (1, -0.5 * TW_DP), (-1, -0.5 * TW_DP))]
        mb.face(cw, 'steel_galv'); mb.face(cw[::-1], 'steel_galv')
        for (a, b) in ((cw[2], cw[3]), (cw[1], cw[2]), (cw[3], cw[0])):
            mb.beam(tuple(np.array(a) + [0, 0, 1.1]), tuple(np.array(b) + [0, 0, 1.1]), 0.05, 0.05, 'steel_galv')
        # the access ladder up the back leg, rungs every 0.6 m, to the catwalk
        out = -toc
        for sg in (-1, 1):
            mb.beam(tuple(tower_point(T, zb + 2.5, sg * 0.22, -0.5 * TW_DP) + out * 0.45), tuple(tower_point(T, zl - 0.1, sg * 0.22, -0.5 * TW_DP) + out * 0.45), 0.05, 0.05, 'tower_red')
        for z in np.arange(zb + 2.6, zl - 0.2, 0.6):
            mb.beam(tuple(tower_point(T, z, -0.22, -0.5 * TW_DP) + out * 0.45), tuple(tower_point(T, z, 0.22, -0.5 * TW_DP) + out * 0.45), 0.03, 0.03, 'tower_red')
        for z in np.arange(zb + 3.0, zl - 0.2, 3.0):   # stand-off brackets tying the ladder to the leg
            mb.beam(tuple(tower_point(T, z, 0.0, -0.5 * TW_DP)), tuple(tower_point(T, z, 0.0, -0.5 * TW_DP) + out * 0.45), 0.05, 0.05, 'tower_red')
        # footing: a concrete plinth on the ground, a steel base plate on a gap deck
        wb = max(W(zb), 1.4) + 1.2
        mb.box(tuple(np.array(T['base'][:2])), wb, TW_DP + 1.2, 0.6, math.degrees(math.atan2(side[1], side[0])), 'conc_light' if zb < 1 else 'steel_galv', z0=zb - 0.05)
    mb.build(col)


# ---------------- outside walls ----------------
def arc_frame(b0, b1, r_of):
    """Arc-length frame along a wall at r_of(b): returns (length, P(s, z, out)) with `out` metres outward."""
    bs = np.linspace(b0, b1, 721); rr = np.array([r_of(b) for b in bs])
    ss = np.concatenate([[0.0], np.cumsum(np.radians(np.diff(bs)) * 0.5 * (rr[1:] + rr[:-1]))])
    def P(s, z, out=0.0):
        b = float(np.interp(s, ss, bs)); return P3(b, r_of(b) + out, z)
    return float(ss[-1]), P


def panel(mb, P, s0, s1, z0, z1, out, m):
    """A wall face from s0 to s1 (subdivided along the arc), z0..z1, `out` m outward; normal outward."""
    n = max(1, int(math.ceil((s1 - s0) / 1.5))); ss = np.linspace(s0, s1, n + 1)
    for a, b in zip(ss, ss[1:]):
        mb.face([P(a, z0, out), P(b, z0, out), P(b, z1, out), P(a, z1, out)], m)


def reveal(mb, P, s0, s1, z0, z1, out0, out1, m, sides=True, top=True, bottom=True):
    """The returns of an opening cut into a wall at out0, going back to out1 (out1 < out0): its jambs, head and
    sill faces, facing into the opening."""
    if sides:
        mb.face([P(s0, z0, out1), P(s0, z0, out0), P(s0, z1, out0), P(s0, z1, out1)], m)
        mb.face([P(s1, z0, out0), P(s1, z0, out1), P(s1, z1, out1), P(s1, z1, out0)], m)
    n = max(1, int(math.ceil((s1 - s0) / 1.5))); ss = np.linspace(s0, s1, n + 1)
    for a, b in zip(ss, ss[1:]):
        if top:
            mb.face([P(a, z1, out0), P(b, z1, out0), P(b, z1, out1), P(a, z1, out1)], m)
        if bottom:
            mb.face([P(a, z0, out1), P(b, z0, out1), P(b, z0, out0), P(a, z0, out0)], m)


def slab_edge(mb, P, s0, s1, z, d, h, m):
    """A floor slab's edge standing d m proud of the wall, h m deep, with its top and underside."""
    panel(mb, P, s0, s1, z - h, z, d, m)
    n = max(1, int(math.ceil((s1 - s0) / 1.5))); ss = np.linspace(s0, s1, n + 1)
    for a, b in zip(ss, ss[1:]):
        mb.face([P(a, z, 0.0), P(a, z, d), P(b, z, d), P(b, z, 0.0)][::-1], m)
        mb.face([P(a, z - h, 0.0), P(b, z - h, 0.0), P(b, z - h, d), P(a, z - h, d)][::-1], m)


def wall_top(s, b):
    """Where the outside wall meets the roof's underside (or the deck, between the roofs)."""
    return roof_top(s, b, back_r(b)) - ROOF_TH - 0.2


def facade_old(mb, s):
    """The 1998 stands' outside wall (Google Earth fac_S, fac_SW, fac_W): concourse openings at the ground,
    recessed 3 m between precast piers; a precast storey with recessed windows; ribbed cladding up to the
    roof; slab edges proud of the wall at each floor."""
    b0, b1 = s['b0'], s['b1']; L, P = arc_frame(b0, b1, back_r)
    BAY = 7.2; n = max(1, int(round(L / BAY))); bay = L / n
    zt = lambda sv: wall_top(s, b0 + (b1 - b0) * sv / L)
    for k in range(n):
        a, e = k * bay, (k + 1) * bay
        # ground: a pier 1.2 m, then an opening into the concourse
        p0, p1 = a + 0.6, e - 0.6
        panel(mb, P, a, p0, 0.0, 4.2, 0.0, 'precast'); panel(mb, P, p1, e, 0.0, 4.2, 0.0, 'precast')
        reveal(mb, P, p0, p1, 0.0, 3.6, 0.0, -3.0, 'precast', bottom=False)
        panel(mb, P, p0, p1, 3.6, 4.2, 0.0, 'precast')
        panel(mb, P, p0, p1, 0.0, 3.6, -3.0, 'concourse')
        mb.face([P(p0, 0.02, -3.0), P(p1, 0.02, -3.0), P(p1, 0.02, 0.0), P(p0, 0.02, 0.0)][::-1], 'paving')
        # first floor: two windows a bay, recessed 0.25 m, with a sill
        ws = [(a + 1.2, a + 3.2), (a + 4.0, a + 6.0)]
        cur = a
        for w0, w1 in ws:
            panel(mb, P, cur, w0, 4.2, 8.4, 0.0, 'precast')
            panel(mb, P, w0, w1, 4.2, 5.4, 0.0, 'precast'); panel(mb, P, w0, w1, 7.0, 8.4, 0.0, 'precast')
            reveal(mb, P, w0, w1, 5.4, 7.0, 0.0, -0.25, 'precast')
            panel(mb, P, w0, w1, 5.4, 7.0, -0.25, 'glass_dark')
            mb.beam(P(w0 - 0.05, 5.36, 0.06), P(w1 + 0.05, 5.36, 0.06), 0.12, 0.08, 'precast')
            mb.beam(P((w0 + w1) / 2, 5.4, -0.22), P((w0 + w1) / 2, 7.0, -0.22), 0.06, 0.06, 'win_frame')
            cur = w1
        panel(mb, P, cur, e, 4.2, 8.4, 0.0, 'precast')
        # above: ribbed cladding to the roof
        ss = np.linspace(a, e, 6)
        for p, q in zip(ss, ss[1:]):
            mb.face([P(p, 8.4, 0.0), P(q, 8.4, 0.0), P(q, zt(q), 0.0), P(p, zt(p), 0.0)], 'clad_grey')
    for z in (4.2, 8.4):
        slab_edge(mb, P, 0, L, z + 0.15, 0.35, 0.45, 'precast')


def facade_east(mb, s):
    """The 2012 east (Cumberland) stand: charcoal cladding over glazing at the ground, slab edges at each
    floor and white steel V struts raking out from the wall to the roof's back edge (Google Earth out_E)."""
    b0, b1 = s['b0'], s['b1']; L, P = arc_frame(b0, b1, back_r)
    zt = lambda sv: wall_top(s, b0 + (b1 - b0) * sv / L)
    ss = np.linspace(0, L, int(L / 1.5) + 1)
    for p, q in zip(ss, ss[1:]):
        mb.face([P(p, 4.5, 0.0), P(q, 4.5, 0.0), P(q, zt(q), 0.0), P(p, zt(p), 0.0)], 'clad_charcoal')
    BAY = 9.0; n = max(1, int(round(L / BAY))); bay = L / n
    for k in range(n):
        a, e = k * bay, (k + 1) * bay
        panel(mb, P, a, a + 0.5, 0.0, 4.5, 0.0, 'clad_charcoal'); panel(mb, P, e - 0.5, e, 0.0, 4.5, 0.0, 'clad_charcoal')
        reveal(mb, P, a + 0.5, e - 0.5, 0.0, 3.9, 0.0, -1.2, 'clad_charcoal', bottom=False)
        panel(mb, P, a + 0.5, e - 0.5, 3.9, 4.5, 0.0, 'clad_charcoal')
        panel(mb, P, a + 0.5, e - 0.5, 0.0, 3.9, -1.2, 'glass_shop')
        for m_ in np.arange(a + 0.5 + 1.8, e - 0.6, 1.8):
            mb.beam(P(m_, 0.0, -1.15), P(m_, 3.9, -1.15), 0.07, 0.07, 'win_frame')
        # the V: two struts from one shoe on the ground 3 m out, up to the roof's back edge
        sm = (a + e) / 2; foot = P(sm, 0.0, 3.0)
        for sv in (a + 0.8, e - 0.8):
            b = b0 + (b1 - b0) * sv / L
            topp = P3(b, roof_back(b) - 0.6, roof_top(s, b, roof_back(b) - 0.6) - ROOF_TH - 0.1)
            mb.beam(foot, topp, 0.36, 0.36, 'steel_white')
        mb.box(pol(b0 + (b1 - b0) * sm / L, back_r(b0 + (b1 - b0) * sm / L) + 3.0), 1.0, 1.0, 0.4, 0, 'conc_light')
    for z in (4.5, 9.3):
        slab_edge(mb, P, 0, L, z + 0.1, 0.5, 0.5, 'precast')


def facade_north(mb, s):
    """The 2012 north (Sydney Royal) stand: light blue panels over a glazed ground floor, slab edges, and the
    concrete stair and lift tower (Google Earth fac_N, out_N)."""
    b0, b1 = s['b0'], s['b1']; L, P = arc_frame(b0, b1, back_r)
    zt = lambda sv: wall_top(s, b0 + (b1 - b0) * sv / L)
    ss = np.linspace(0, L, int(L / 1.5) + 1)
    for p, q in zip(ss, ss[1:]):
        mb.face([P(p, 4.6, 0.0), P(q, 4.6, 0.0), P(q, zt(q), 0.0), P(p, zt(p), 0.0)], 'clad_blue')
    BAY = 8.0; n = max(1, int(round(L / BAY))); bay = L / n
    for k in range(n):
        a, e = k * bay, (k + 1) * bay
        panel(mb, P, a, a + 0.45, 0.0, 4.6, 0.0, 'precast'); panel(mb, P, e - 0.45, e, 0.0, 4.6, 0.0, 'precast')
        reveal(mb, P, a + 0.45, e - 0.45, 0.0, 4.0, 0.0, -1.0, 'precast', bottom=False)
        panel(mb, P, a + 0.45, e - 0.45, 4.0, 4.6, 0.0, 'precast')
        panel(mb, P, a + 0.45, e - 0.45, 0.0, 4.0, -1.0, 'glass_shop')
        # vertical fins between the blue panels
        for m_ in np.arange(a + 2.0, e - 1.0, 2.0):
            mb.beam(P(m_, 4.7, 0.12), P(m_, zt(m_) - 0.1, 0.12), 0.12, 0.24, 'precast')
    for z in (4.6, 9.4):
        slab_edge(mb, P, 0, L, z + 0.1, 0.45, 0.45, 'precast')
    # the stair tower, 8 x 7 m, 19 m tall, a third of the way along from the west
    sc = L * 0.32; c = np.array(P(sc, 0.0, 3.5)); b = b0 + (b1 - b0) * sc / L
    mb.box(tuple(c[:2]), 8.0, 7.0, 19.0, 90 - b, 'precast', mtop='conc_light')
    t = tangent(b); u = radial(b)
    for z in np.arange(2.0, 17.0, 3.2):     # slot windows up the stair
        q = c + u * 3.52
        mb.face([tuple(q - t * 0.6 + np.array([0, 0, z])), tuple(q + t * 0.6 + np.array([0, 0, z])),
                 tuple(q + t * 0.6 + np.array([0, 0, z + 2.2])), tuple(q - t * 0.6 + np.array([0, 0, z + 2.2]))][::-1], 'glass_dark')


def facades(col):
    mb = MB('facades')
    for s in roofed():
        if s['kind'] == 'old':
            facade_old(mb, s)
        elif s['name'] == 'N':
            facade_north(mb, s)
        else:
            facade_east(mb, s)
    gap_blocks(mb)
    mb.build(col)


def gap_blocks(mb):
    """Between two roofs, where a light tower stands: a concrete service block behind the top row, its flat deck
    at 13 m carrying the tower (Google Earth in_NW, in_SE: the pale deck in each gap)."""
    st = sorted(roofed(), key=lambda s: s['b0'])
    for i in range(len(st) - 1):
        g0, g1 = st[i]['b1'], st[i + 1]['b0']
        if g1 - g0 < 1.0:
            continue
        bs = arc(g0, g1, 0.5); ZD = 13.0
        rin = lambda b: tier_up(b)[2] + 1.8
        quad_strip(mb, bs, lambda b: (rin(b), tier_up(b)[3] + 1.1), lambda b: (rin(b), ZD), 'precast')
        quad_strip(mb, bs, lambda b: (rin(b), ZD), lambda b: (back_r(b), ZD), 'deck_pale')
        quad_strip(mb, bs, lambda b: (back_r(b), ZD), lambda b: (back_r(b), 0.0), 'precast')
        for b, fl in ((g0, False), (g1, True)):
            endcap(mb, b, [(rin(b), tier_up(b)[3] + 1.1), (rin(b), ZD), (back_r(b), ZD), (back_r(b), 0.0), (rin(b), 0.0)], 'precast', flip=fl)
        # a parapet round the deck
        L, P = arc_frame(g0, g1, back_r)
        panel(mb, P, 0, L, ZD, ZD + 1.1, -0.15, 'precast')
        # stair-tower windows down the outside
        for z in np.arange(1.5, 12.0, 3.2):
            panel(mb, P, L / 2 - 0.7, L / 2 + 0.7, z, z + 2.0, 0.02, 'glass_dark')


# ---------------- the scoreboard behind the open end ----------------
# An oval 30 x 17.5 m (the 2013 photo: a screen in a white oval with the stadium name above), its rim light
# blue today, on a steel lattice cage standing on a charcoal single-storey building. Placed on OSM's video wall.
_VW = D['osm_video_wall']
SB_B, SB_R = 0.5 * (_VW[0][0] + _VW[1][0]), 0.5 * (_VW[0][1] + _VW[1][1])


def scoreboard(col):
    mb = MB('scoreboard')
    u = radial(SB_B); t = tangent(SB_B); up = np.array([0, 0, 1.0])
    C = np.array(P3(SB_B, SB_R, 0.0))
    # the building: 46 m along the arc, 10 m deep, 5.2 m tall, charcoal cladding, doors and a lighter parapet
    L, P = arc_frame(SB_B - 11.0, SB_B + 11.0, lambda b: 116.0)
    L2, P2 = arc_frame(SB_B - 11.0, SB_B + 11.0, lambda b: 126.0)
    panel(mb, P, 0, L, 0, 4.6, 0.0, 'clad_charcoal'); panel(mb, P, 0, L, 4.6, 5.2, 0.0, 'precast')
    for k, s0 in enumerate(np.linspace(3, L - 6, 7)):
        reveal(mb, P, s0, s0 + 2.4, 0.0, 2.6, 0.0, -0.3, 'clad_charcoal', bottom=False)
        panel(mb, P, s0, s0 + 2.4, 0.0, 2.6, -0.3, 'door_dark' if k % 2 else 'glass_shop')
    ss = np.linspace(0, L, 16)
    for a, b in zip(ss, ss[1:]):
        mb.face([P(a, 5.2), P(b, 5.2), P2(b * L2 / L, 5.2), P2(a * L2 / L, 5.2)][::-1], 'deck_pale')
        mb.face([P2(a * L2 / L, 0), P2(b * L2 / L, 0), P2(b * L2 / L, 5.2), P2(a * L2 / L, 5.2)][::-1], 'clad_charcoal')
    for s0, P_, fl in ((0.0, None, False), (L, None, True)):
        b = SB_B - 11.0 if s0 == 0 else SB_B + 11.0
        endcap(mb, b, [(116.0, 0.0), (116.0, 5.2), (126.0, 5.2), (126.0, 0.0)], 'clad_charcoal', flip=fl)
    # the oval: rim (light blue band, white edge), the screen set back in it, a back skin and the lattice cage
    W, H, zc, dep = 30.0, 17.5, 14.9, 1.4
    O = C - u * 0.0
    def ell(k, n, sc=1.0):
        a = 2 * math.pi * k / n; return O + t * (W / 2 * sc * math.cos(a)) + up * (zc + H / 2 * sc * math.sin(a))
    n = 48
    for k in range(n):
        a0, a1 = ell(k, n), ell(k + 1, n); i0, i1 = ell(k, n, 0.86), ell(k + 1, n, 0.86)
        f = -u * dep / 2; bk = u * dep / 2
        mb.face([tuple(a0 + f), tuple(a1 + f), tuple(i1 + f), tuple(i0 + f)][::-1], 'sb_rim')
        mb.face([tuple(a0 + bk), tuple(a1 + bk), tuple(i1 + bk), tuple(i0 + bk)], 'sb_back')
        mb.face([tuple(a0 + f), tuple(a0 + bk), tuple(a1 + bk), tuple(a1 + f)][::-1], 'sb_edge')
        # the inner field of the oval (behind the screen), set back 0.3 m
        mb.face([tuple(O + up * zc + f * 0.6), tuple(i0 + f * 0.6), tuple(i1 + f * 0.6)][::-1], 'sb_field')
        mb.face([tuple(i0 + f), tuple(i1 + f), tuple(i1 + f * 0.6), tuple(i0 + f * 0.6)], 'sb_edge')
        mb.face([tuple(O + up * zc + bk), tuple(a0 + bk), tuple(a1 + bk)], 'sb_back')
    # the screen: 22 x 10 m, its frame standing proud
    sw, sh, sz = 22.0, 10.0, zc - 0.6
    q = lambda x, y, d: tuple(O + t * x + up * (sz + y) - u * d)
    mb.face([q(-sw / 2, -sh / 2, 1.0), q(sw / 2, -sh / 2, 1.0), q(sw / 2, sh / 2, 1.0), q(-sw / 2, sh / 2, 1.0)][::-1], 'screen')
    for (x0, y0, x1, y1) in ((-sw / 2 - 0.3, -sh / 2 - 0.3, sw / 2 + 0.3, -sh / 2), (-sw / 2 - 0.3, sh / 2, sw / 2 + 0.3, sh / 2 + 0.3),
                             (-sw / 2 - 0.3, -sh / 2, -sw / 2, sh / 2), (sw / 2, -sh / 2, sw / 2 + 0.3, sh / 2)):
        mb.face([q(x0, y0, 1.1), q(x1, y0, 1.1), q(x1, y1, 1.1), q(x0, y1, 1.1)][::-1], 'steel_dark')
        for (xa, ya, xb, yb) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
            mb.face([q(xa, ya, 1.1), q(xb, yb, 1.1), q(xb, yb, 0.6), q(xa, ya, 0.6)], 'steel_dark')
    # the cage behind: vertical trusses every 5 m and horizontal ones every 3.5 m, 2.5 m behind the back skin
    for x in np.arange(-12.5, 12.6, 5.0):
        hh = H / 2 * math.sqrt(max(0.0, 1 - (x / (W / 2)) ** 2)) * 0.97
        for d in (dep / 2 + 0.2, dep / 2 + 2.6):
            mb.beam(tuple(O + t * x + up * (zc - hh) + u * d), tuple(O + t * x + up * (zc + hh) + u * d), 0.2, 0.2, 'steel_grey')
        for zz in np.arange(zc - hh, zc + hh, 1.75):
            mb.beam(tuple(O + t * x + up * zz + u * (dep / 2 + 0.2)), tuple(O + t * x + up * (zz + 1.75) + u * (dep / 2 + 2.6)), 0.08, 0.08, 'steel_grey')
    for zz in np.arange(zc - 7.0, zc + 7.1, 3.5):
        ww = W / 2 * math.sqrt(max(0.0, 1 - ((zz - zc) / (H / 2)) ** 2)) * 0.97
        for d in (dep / 2 + 0.2, dep / 2 + 2.6):
            mb.beam(tuple(O + t * -ww + up * zz + u * d), tuple(O + t * ww + up * zz + u * d), 0.2, 0.2, 'steel_grey')
    # legs: four columns from the building's roof up into the cage, braced
    for x in (-9.0, -3.0, 3.0, 9.0):
        for d in (dep / 2 + 0.2, dep / 2 + 2.6):
            mb.beam(tuple(O + t * x + up * 5.2 + u * d), tuple(O + t * x + up * (zc - H / 2 * 0.8) + u * d), 0.4, 0.4, 'steel_grey')
        mb.beam(tuple(O + t * x + up * 5.2 + u * (dep / 2 + 0.2)), tuple(O + t * x + up * 9.0 + u * (dep / 2 + 2.6)), 0.15, 0.15, 'steel_grey')
    mb.build(col)


# ---------------- the ground round the stadium ----------------
def apron(col):
    """Paving from the outside walls out to 150 m; the surroundings take over beyond (GroundModels.SURROUNDS)."""
    mb = MB('apron')
    def wall(b):
        bb = b % 360
        if 8.0 <= bb <= 72.0:
            return tier_open(b)[2] + 2.8
        return back_r(b)
    bs = arc(0.0, 360.0, 1.0)
    quad_strip(mb, bs, lambda b: (wall(b), 0.01), lambda b: (150.0, 0.01), 'paving')
    mb.build(col)


def build_all():
    clear(); col = bpy.context.scene.collection
    bowl(col); aisles(col); vomitories(col); roof(col); suites(col); towers(col); facades(col); scoreboard(col); apron(col)


# ---------------- seats: instanced 3D seats on the treads ----------------
# Red tip-up seats folded up: a red pad on a black back, the folded black pan in front (photo sphere, Jan 2019),
# with the odd orange seat; orange at the open end (the 2013 photo), some red among them.
SEAT_W = 0.5


def roof_under(b, r):
    s = stand_at(b)
    if s is None or s['kind'] == 'open' or not (roof_front(b) <= r <= roof_back(b)):
        return None
    return roof_top(s, b, r) - ROOF_TH - 0.4


def seat_list():
    """Every seat as (x, y, z, bearing, colour)."""
    rng = np.random.default_rng(11)
    out = []
    al = aisle_list(); vl = vom_list(); rc0, rc1 = D['race']
    for b0, b1 in blocks():
        bm = 0.5 * (b0 + b1); open_ = is_open(bm)
        tiers = tiers_at(bm)
        for ti, (r_a, z_a, n, run, rise) in enumerate(tiers):
            for k in range(n):
                r = r_a + (k + 1) * run - 0.30
                L = math.radians(b1 - b0) * r; m = int(L // SEAT_W)
                for i in range(m):
                    b = b0 + math.degrees((i + 0.5) * L / m / r)
                    rr_a, zz_a, _, rn, rs = tiers_at(b)[ti]
                    rr = rr_a + (k + 1) * rn - 0.30; zz = zz_a + (k + 1) * rs
                    if any(abs(math.radians(b - a) * rr) < AISLE_W / 2 + 0.2 for a in al):
                        continue
                    if rc0 - 0.3 <= b <= rc1 + 0.3:
                        continue
                    # the vomitory's mouth and the row in front of it (a walkway there, under its wall)
                    if not open_ and ti == 0 and k >= LOW_N - VOM_ROWS - 1 and any(abs(math.radians(b - v) * rr) < VOM_W / 2 + 0.25 for v in vl):
                        continue
                    # where the open stand meets the roofed rows (their treads differ) and where a tower stands
                    if any(abs(math.radians(b - j) * rr) < 0.6 for j in (8.0, 72.0, 368.0)):
                        continue
                    if any(math.hypot(rr * math.sin(math.radians(b)) - T['base'][0], rr * math.cos(math.radians(b)) - T['base'][1])
                           < 0.5 * tower_w(T, max(zz, T['base'][2])) + TW_DP + 1.0 for T in D['towers']):
                        continue
                    ru = roof_under(b, rr)
                    if ru is not None and ru - zz < 2.2:
                        continue
                    x = rng.random()
                    if open_:
                        c = 'seat_engie_red' if x < 0.15 else 'seat_engie_orange'
                    else:
                        c = 'seat_engie_orange' if x < 0.06 else 'seat_engie_red'
                    out.append((rr * math.sin(math.radians(b)), rr * math.cos(math.radians(b)), zz, b, c))
    return out


def _box(tris, cx, cy, cz, sx, sy, sz, lean=0.0):
    ca, sa = math.cos(lean), math.sin(lean); P = []
    for dx, dy, dz in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
        y, z = dy * sy / 2, dz * sz / 2
        y, z = y * ca + z * sa, -y * sa + z * ca
        P.append((cx + dx * sx / 2, cy + y, cz + z))
    ctr = np.mean(P, axis=0)
    for a, b_, c, d in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        for t in ((P[a], P[b_], P[c]), (P[a], P[c], P[d])):
            A, B, C = (np.array(q) for q in t)
            if np.dot(np.cross(A - C, A - B), (A + B + C) / 3 - ctr) < 0:
                t = (t[0], t[2], t[1])
            tris.extend(t)


def seat_pad():
    """The coloured part of a folded seat (glTF frame: x along the row, y up, +z toward the field; origin on
    the tread under the seat's back): the backrest's cushion, 0.42 x 0.24 m, above the folded pan."""
    t = []
    _box(t, 0.0, 0.73, 0.035, 0.42, 0.24, 0.035, lean=0.17)
    return t


def seat_shell():
    """The black parts: the backrest shell, the folded pan standing in front of it, the side frames."""
    t = []
    _box(t, 0.0, 0.66, -0.01, 0.46, 0.44, 0.05, lean=0.17)        # back shell
    _box(t, 0.0, 0.47, 0.13, 0.44, 0.42, 0.06, lean=0.10)         # the folded pan
    for x in (-0.24, 0.24):
        _box(t, x, 0.30, 0.08, 0.04, 0.60, 0.30)                  # side frame on the tread
    return t


def seat_transforms(seats):
    out = {}
    for x, y, z, b, c in seats:
        a = math.radians(b); sb, cb = math.sin(a), math.cos(a)
        X = (cb, 0.0, sb); Y = (0.0, 1.0, 0.0); Zv = (-sb, 0.0, cb)
        o = (x, z, -y)
        out.setdefault(c, []).append([X[0], Y[0], Zv[0], o[0], X[1], Y[1], Zv[1], o[1], X[2], Y[2], Zv[2], o[2]])
    return out
