# MCG exterior, built from measurements of the 2026 Google Earth views and the Esri satellite (model/mcg.json).
# Runs inside Blender: import build; build.build_all(). Local frame: x east, y north, metres, z up from the plaza.
import bpy, math, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from mb import MB, rect, ccw, TILE
D = json.load(open(os.path.join(HERE, 'mcg.json')))


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


def periodic(tab, step=1.0):
    """tab: [[bearing, v...], ...] -> function(bearing) with periodic linear interpolation per column"""
    t = np.array(sorted(tab), float); b = np.concatenate([t[:, 0] - 360, t[:, 0], t[:, 0] + 360])
    cols = [np.concatenate([t[:, k]] * 3) for k in range(1, t.shape[1])]
    return lambda q: [float(np.interp(q % 360, b, c)) for c in cols]


def pol(b, r):
    a = math.radians(b); return (r * math.sin(a), r * math.cos(a))


def tower(mb, T):
    x, y = T['xy']; zt = T['top']; hh = T['head_h']; zb = zt - hh; wt, wb = T['w_top'], T['w_bot']
    n = 16; r0, r1 = T['r_base'], T['r_top']
    for k in range(n):  # tapered round mast
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        p = lambda a, r, z: (x + r * math.cos(a), y + r * math.sin(a), z)
        mb.face([p(a0, r0, 0), p(a1, r0, 0), p(a1, r1, zb + 1.0), p(a0, r1, zb + 1.0)], 'paint_white')
    # head faces the field centre; tilt < 0 leans its top toward the field so the lamps point down (GE n_n: top 5 m in)
    dx, dy = -x, -y; L = math.hypot(dx, dy); f = np.array([dx / L, dy / L, 0.0]); s = np.array([-f[1], f[0], 0.0])
    tl = math.radians(T['tilt']); up = np.array([0, 0, 1.0]) * math.cos(tl) - f * math.sin(tl)
    nrm = f * math.cos(tl) + np.array([0, 0, 1.0]) * math.sin(tl)
    c0 = np.array([x, y, zb]) + f * 0.6
    def P(u, v, d=0.0):
        w = wb + (wt - wb) * v / hh; return c0 + s * (u * w / 2) + up * v + nrm * d
    q = [P(-1, 0), P(1, 0), P(1, hh), P(-1, hh)]
    mb.face(q, 'lamps', uv=[(0, 0), (1, 0), (1, 1), (0, 1)])            # field side: lamp grid
    qb = [P(-1, 0, -0.9), P(1, 0, -0.9), P(1, hh, -0.9), P(-1, hh, -0.9)]
    mb.face(qb[::-1], 'lamps', uv=[(1, 0), (0, 0), (0, 1), (1, 1)][::-1])  # back of the head: open lamp frame
    for i in range(4):
        j = (i + 1) % 4; mb.face([q[j], q[i], qb[i], qb[j]], 'paint_white')


def build_all():
    clear(); col = bpy.context.scene.collection
    mb = MB('towers')
    for T in D['towers']:
        tower(mb, T)
    mb.build(col)
    bowl_all(col)


# ---------------- bowl, roof, facade (polar sections, 0.5 deg) ----------------
def polar_of_poly(P, bs):
    """outermost radius where each bearing's ray crosses polygon P (list of xy); nan if none"""
    P = np.array(P, float); out = np.full(len(bs), np.nan)
    A = P; Bq = np.roll(P, -1, 0)
    for i, b in enumerate(bs):
        d = np.array(pol(b, 1.0)); best = np.nan
        for a, c in zip(A, Bq):
            e = c - a; M = np.array([[d[0], -e[0]], [d[1], -e[1]]])
            if abs(np.linalg.det(M)) < 1e-9: continue
            t, s = np.linalg.solve(M, a)
            if t > 0 and 0 <= s <= 1: best = t if np.isnan(best) else max(best, t)
        out[i] = best
    return out


def facseg(b):
    b %= 360
    for s in D['facade']:
        if s[0] <= b < s[1]: return s
    return D['facade'][-1]


def sec_tab(name, default):
    return periodic(D[name]) if name in D else (lambda q: default)


def bowl_all(col):
    STEP = D.get('step', 0.5); bs = np.arange(0, 360, STEP)
    fb = periodic(D['fence']); ri = periodic(D['roof_inner']); ro = periodic(D['roof_outer']); rh = periodic(D['roof_h'])
    tiers = periodic(D['tiers']); mats = D['mats']; tw_ = periodic(D['roof_teal_w'])
    def matat(key, b):
        for b0, b1, m in mats[key]:
            if b0 <= b % 360 < b1: return m
        return mats[key][0][2]
    fp = np.full(len(bs), np.nan)
    for k in ('shane_warne', 'mcc', 'olympic', 'ponsford'):
        r = polar_of_poly(D['osm'][k], bs); fp = np.fmax(fp, r)
    secs = []
    for i, b in enumerate(bs):
        rf = fb(b)[0]; rin = ri(b)[0]; rout = ro(b)[0]; h = rh(b)[0]
        d1, z1, d2, zb2, zt2, e2, z2, d3, zb3, zt3, zback, zfac = tiers(b)
        fseg = facseg(b); zfac = fseg[2]
        rfp = fp[i] if not np.isnan(fp[i]) else rout
        rfp = max(rfp, rf + d3 + 6)
        # (r, z, material-of-segment-from-previous-point)
        S = [(rf, -5.3, None), (rf, -4.2, 'fence'), (rf + 1.5, -4.2, 'conc_grey'), (rf + d1, z1, matat('t1', b)),
             (rf + d2, z1, 'conc_grey'), (rf + d2, zb2, 'conc_light'), (rf + d2 - 0.4, zt2, 'fascia'),
             (rf + e2, z2, matat('t2', b)), (rf + d3, z2, 'conc_grey'), (rf + d3, zb3, 'conc_light'),
             (rf + d3 - 0.4, zt3, 'fascia'), (rout - 8, zback, matat('t3', b)), (rout - 8, h - edge(b)[1], 'conc_grey'),
             (min(rfp, rout), h - edge(b)[1], 'roof_soffit')]
        secs.append(dict(b=b, S=S, ed=edge(b), dk=matat('deck', b) if 'deck' in mats else 'conc_light', rin=rin, rout=rout, h=h, rfp=rfp, zfac=zfac, tw=tw_(b)[0], fm=fseg[3], fs0=fseg[0]))
    mb = MB('bowl')
    n = len(secs)
    for i in range(n):
        A = secs[i]; Bs = secs[(i + 1) % n]
        for k in range(1, len(A['S'])):
            m = A['S'][k][2]
            p0 = (*pol(A['b'], A['S'][k - 1][0]), A['S'][k - 1][1]); p1 = (*pol(A['b'], A['S'][k][0]), A['S'][k][1])
            q0 = (*pol(Bs['b'], Bs['S'][k - 1][0]), Bs['S'][k - 1][1]); q1 = (*pol(Bs['b'], Bs['S'][k][0]), Bs['S'][k][1])
            mb.face([p0, q0, q1, p1], m)
        # facade wall and deck at the footprint
        fz = A['zfac']; gz = Bs['zfac']  # each sector keeps its own block height; steps at block edges
        a0 = (*pol(A['b'], A['rfp']), 0.0); b0 = (*pol(Bs['b'], Bs['rfp']), 0.0)
        a1 = (*pol(A['b'], A['rfp']), fz); b1 = (*pol(Bs['b'], Bs['rfp']), fz)
        tu, tv = TILE.get(A['fm'], (1, 1)); k = math.pi / 180
        ua = (A['b'] - A['fs0']) * k * A['rfp'] / tu; ub = ua + ((Bs['b'] - A['b']) % 360) * k * 0.5 * (A['rfp'] + Bs['rfp']) / tu
        mb.face([a0, a1, b1, b0], A['fm'], uv=[(ua, 0), (ua, fz / tv), (ub, fz / tv), (ub, 0)])
        c0 = (*pol(A['b'], A['rout'] - 8), fz); c1 = (*pol(Bs['b'], Bs['rout'] - 8), fz)
        mb.face([c0, a1, b1, c1][::-1], A['dk'])
        # upper back wall: deck up to the roof's outer fascia, set 1.5 m in from the roof edge
        wa = min(A['rfp'], A['rout']) - 1.5; wb = min(Bs['rfp'], Bs['rout']) - 1.5
        for za, zb, m in back_bands(A['b'], fz, A['h'] - A['ed'][1]):
            mb.face([(*pol(A['b'], wa), za), (*pol(A['b'], wa), zb), (*pol(Bs['b'], wb), zb), (*pol(Bs['b'], wb), za)], m)
        if abs(fz - gz) > 0.01:  # end wall where the next block is lower or higher
            lo, top = min(fz, gz), max(fz, gz); hm = A['fm'] if fz > gz else Bs['fm']
            q = [(*pol(Bs['b'], Bs['rfp']), lo), (*pol(Bs['b'], Bs['rfp']), top), (*pol(Bs['b'], Bs['rout'] - 8), top), (*pol(Bs['b'], Bs['rout'] - 8), lo)]
            mb.face(q, hm); mb.face(q[::-1], hm)
        # radial step between neighbouring footprint radii shows as a wall (handled by the quad above)
    mb.build(col)
    # plaza: concrete from under the facade out to its measured edge, then the park gravel strip
    pz = periodic(D['plaza']); gv = periodic(D['gravel']); mp = MB('plaza')
    for i in range(n):
        A = secs[i]; Bs = secs[(i + 1) % n]
        for r0a, r0b, r1a, r1b, m in ((A['rfp'] - 3, Bs['rfp'] - 3, pz(A['b'])[0], pz(Bs['b'])[0], 'paving'),
                                      (pz(A['b'])[0], pz(Bs['b'])[0], gv(A['b'])[0], gv(Bs['b'])[0], 'gravel')):
            if r1a - r0a < 0.05 and r1b - r0b < 0.05: continue
            mp.face([(*pol(A['b'], r0a), 0.0), (*pol(Bs['b'], r0b), 0.0), (*pol(Bs['b'], max(r0b, r1b)), 0.0), (*pol(A['b'], max(r0a, r1a)), 0.0)], m)
    mp.build(col)
    # roof
    mr = MB('roof')
    for i in range(n):
        A = secs[i]; Bs = secs[(i + 1) % n]
        if in_screen(A['b']) and in_screen(Bs['b']): continue  # the screen box replaces the roof here
        def ring(s, r, z): return (*pol(s['b'], r), z)
        mclear = D.get('roof_clear_w', 0.0)
        tw = lambda s: min(s['tw'], s['rout'] - s['rin'] - 1) if s['tw'] > 0.5 else 0.0
        zr = lambda s, r: s['h'] - s['ed'][0] * (r - s['rin']) / (s['rout'] - s['rin'])
        for (ra, za, rb, zb_, m) in [(lambda s: s['rin'], lambda s: s['h'] - 3.0, lambda s: s['rin'], lambda s: s['h'], 'roof_fascia'),
                                     (lambda s: s['rin'], lambda s: s['h'], lambda s: s['rin'] + tw(s), lambda s: zr(s, s['rin'] + tw(s)), 'roof_teal'),
                                     (lambda s: s['rin'] + tw(s), lambda s: zr(s, s['rin'] + tw(s)), lambda s: s['rout'], lambda s: s['h'] - s['ed'][0], matat('roof', A['b'])),
                                     (lambda s: s['rout'], lambda s: s['h'] - s['ed'][0], lambda s: s['rout'], lambda s: s['h'] - s['ed'][1], 'roof_fascia'),
                                     (lambda s: s['rout'], lambda s: s['h'] - s['ed'][1], lambda s: s['rin'], lambda s: s['h'] - 3.0, 'roof_soffit')]:
            mr.face([ring(A, ra(A), za(A)), ring(A, rb(A), zb_(A)), ring(Bs, rb(Bs), zb_(Bs)), ring(Bs, ra(Bs), za(Bs))][::-1], m)
    # dark gutter walkway along each truss line, inner teal edge to the outer fascia (GE n_n: ~0.9 m wide)
    STEP = D.get('step', 0.5)
    for tb in list(D['trusses']['b']) + mast_bearings():
        if in_screen(tb): continue
        A = secs[int(round(tb / STEP)) % n]
        r0 = A['rin'] + (min(A['tw'], A['rout'] - A['rin'] - 1) if A['tw'] > 0.5 else 0.0); r1 = A['rout']
        zr = lambda r: A['h'] - A['ed'][0] * (r - A['rin']) / (A['rout'] - A['rin']) + 0.08
        da = math.degrees(0.45 / max(r0, 1)); db = math.degrees(0.45 / r1)
        mr.face([(*pol(tb - da, r0), zr(r0)), (*pol(tb + da, r0), zr(r0)), (*pol(tb + db, r1), zr(r1)), (*pol(tb - db, r1), zr(r1))][::-1], 'steel_dark')
    mr.build(col)
    struct_all(col)
    screens_all(col)
    canopy_all(col)


def mast_bearings():
    """Bearings of the Northern Stand roof masts: one every M['arc'] metres of outer roof edge from M['b0']."""
    M = D['masts']; ro = periodic(D['roof_outer']); bs = []
    span = lambda b: (b % 360) >= M['lo'] or (b % 360) <= M['hi']
    for sgn in (1, -1):
        b = M['b0']
        while span(b):
            if b % 360 not in bs: bs.append(b % 360)
            b += sgn * math.degrees(M['arc'] / ro(b)[0])
    return bs


def edge(b):
    for b0, b1, dt, db in D.get('roof_edge', []):
        if b0 <= b % 360 < b1: return dt, db
    return 2.0, 4.5


def back_bands(b, z0, z1):
    """Upper back wall bands at bearing b from z0 to z1: dark glass unless a measured block says otherwise."""
    cuts = [(max(z0, a), min(z1, c), m) for b0, b1, a, c, m in D.get('backwall', []) if b0 <= b % 360 < b1 and min(z1, c) > max(z0, a)]
    cuts.sort(); out = []; z = z0
    for a, c, m in cuts:
        if a > z: out.append((z, a, 'glass'))
        out.append((max(a, z), c, m)); z = max(z, c)
    if z < z1: out.append((z, z1, 'glass'))
    return out


def in_screen(b):
    return any(S['b0'] <= b % 360 <= S['b1'] for S in D.get('screens', []))


def screens_all(col):
    """The two video screens: a box at roof level, LED face to the field, clad back and five posts on top."""
    mb = MB('screens'); P3 = lambda b, r, z: (*pol(b, r), z)
    for S in D['screens']:
        bs = np.linspace(S['b0'], S['b1'], 9)
        for b0, b1 in zip(bs, bs[1:]):
            mb.face([P3(b0, S['rf'], S['zf']), P3(b0, S['rf'], S['zt']), P3(b1, S['rf'], S['zt']), P3(b1, S['rf'], S['zf'])], 'screen')
            mb.face([P3(b1, S['rb'], S['zbk']), P3(b1, S['rb'], S['zt']), P3(b0, S['rb'], S['zt']), P3(b0, S['rb'], S['zbk'])], 'fac_blue')
            mb.face([P3(b0, S['rf'], S['zt']), P3(b0, S['rb'], S['zt']), P3(b1, S['rb'], S['zt']), P3(b1, S['rf'], S['zt'])], 'steel_dark')
            mb.face([P3(b0, S['rb'], S['zbk']), P3(b0, S['rf'], S['zf']), P3(b1, S['rf'], S['zf']), P3(b1, S['rb'], S['zbk'])], 'steel_dark')
        for b, sg in ((S['b0'], 1), (S['b1'], -1)):
            q = [P3(b, S['rf'], S['zf']), P3(b, S['rb'], S['zbk']), P3(b, S['rb'], S['zt']), P3(b, S['rf'], S['zt'])]
            mb.face(q if sg > 0 else q[::-1], 'glass')
        if S.get('flagpoles'):  # the SW box carries the five flagpoles at their surveyed spots
            pts = [(x, y) for x, y in D['flagpoles']]
        else:
            pts = [pol(S['b0'] + (S['b1'] - S['b0']) * (0.15 + 0.7 * k / (S['posts'] - 1)), S['rb'] - 1.0) for k in range(S['posts'])]
        for x, y in pts:
            mb.beam((x, y, S['zt']), (x, y, S['post_top']), 0.4, 0.4, 'steel_galv')
    mb.build(col)


def canopy_all(col):
    """Northern entrance: white folded-plate canopy on the deck, glazed box beside it, on slim posts."""
    mb = MB('canopy'); P3 = lambda b, r, z: (*pol(b, r), z); C = D['canopy']
    bs = np.arange(C['b0'], C['b1'] + 1e-6, C['fold'])
    for k, (b0, b1) in enumerate(zip(bs, bs[1:])):
        z0, z1 = (C['zlo'], C['zhi']) if k % 2 == 0 else (C['zhi'], C['zlo'])
        q = [P3(b0, C['rf'], z0), P3(b1, C['rf'], z1), P3(b1, C['rb'], 0.5 * (z1 + C['zhi'])), P3(b0, C['rb'], 0.5 * (z0 + C['zhi']))]
        mb.face(q, 'paint_white'); mb.face(q[::-1], 'roof_soffit')
        if k % 2 == 0: mb.beam(P3(b0, C['rf'] - 2, C['zdeck']), P3(b0, C['rf'] - 2, z0), 0.3, 0.3, 'steel_white')
    for b0, b1, r, z0, z1 in D['glassbox']:
        for a0, a1 in zip(np.linspace(b0, b1, 5), np.linspace(b0, b1, 5)[1:]):
            q = [P3(a0, r, z0), P3(a1, r, z0), P3(a1, r, z1), P3(a0, r, z1)]; mb.face(q, 'glass'); mb.face(q[::-1], 'glass')
            mb.face([P3(a0, r, z1), P3(a1, r, z1), P3(a1, r - 8, z1), P3(a0, r - 8, z1)], 'roof_grey')
    mb.build(col)


def struct_all(col):
    """Blue cantilever trusses (east and south roofs) and the Northern Stand's white masts with stays and bracing."""
    ri = periodic(D['roof_inner']); ro = periodic(D['roof_outer']); rh = periodic(D['roof_h'])
    def zroof(b, r):
        a, o, h = ri(b)[0], ro(b)[0], rh(b)[0]; return h - edge(b)[0] * (r - a) / (o - a)
    P3 = lambda b, r, z: (*pol(b, r), z)
    T = D['trusses']; rs = periodic(T['r_start']); mb = MB('trusses')
    feet = []
    for b in T['b']:
        o = ro(b)[0]; h = rh(b)[0]; r0 = rs(b)[0]; top = P3(b, o - 1.0, h + T['top'])
        mb.beam(P3(b, r0, zroof(b, r0) + 0.3), top, 0.9, 0.9, 'steel_blue')
        sp = T['splay']; zf = h - T['foot']
        for sg in (-1, 1):  # A-frame legs splayed along the roof edge
            db = sg * math.degrees(sp / o); mb.beam(P3(b + db, o - 1.0, zf), top, 0.7, 0.7, 'steel_blue')
        mb.beam(P3(b, r0 + 0.5 * (o - r0), zroof(b, r0 + 0.5 * (o - r0)) + 0.2), P3(b, o - 1.0, 0.5 * (zf + h + T['top'])), 0.5, 0.5, 'steel_blue')
        feet.append((b, o, zf, h))
    for (b1, o1, z1, h1), (b2, o2, z2, h2) in zip(feet, feet[1:]):  # V ties between neighbouring feet
        bm = 0.5 * (b1 + b2); om = 0.5 * (o1 + o2); zm = 0.5 * (h1 + h2) - T['tie']
        mb.beam(P3(b1 + math.degrees(T['splay'] / o1), o1 - 1.0, z1), P3(bm, om - 1.0, zm), 0.35, 0.35, 'steel_blue')
        mb.beam(P3(b2 - math.degrees(T['splay'] / o2), o2 - 1.0, z2), P3(bm, om - 1.0, zm), 0.35, 0.35, 'steel_blue')
    mb.build(col)
    M = D['masts']; mt = periodic(M['top']); mm = MB('masts')
    def span(b):  # inside the Northern Stand arc lo..360..hi
        b %= 360; return b >= M['lo'] or b <= M['hi']
    bs = []
    for sgn in (1, -1):
        b = M['b0']
        while span(b):
            if b % 360 not in [x % 360 for x in bs]: bs.append(b % 360)
            b += sgn * math.degrees(M['arc'] / ro(b)[0])
    bs = sorted(bs, key=lambda q: (q - M['lo']) % 360)
    tops = []
    for b in bs:
        o = ro(b)[0]; zt = mt(b)[0]; tp = P3(b, o, zt); tops.append((b, o, zt))
        mm.beam(P3(b, o, M['z0']), tp, 1.0, 0.8, 'steel_white')
        ri_ = o - M['stay_in']; mm.beam(tp, P3(b, ri_, zroof(b, ri_) + 0.2), 0.25, 0.25, 'steel_white')
    for (b1, o1, z1), (b2, o2, z2) in zip(tops, tops[1:]):
        zl = M['z0'] + 1.0; zu = min(rh(b1)[0], rh(b2)[0]) - 4.5
        mm.beam(P3(b1, o1, zl), P3(b2, o2, zu), 0.3, 0.3, 'steel_white')
        mm.beam(P3(b1, o1, zu), P3(b2, o2, zl), 0.3, 0.3, 'steel_white')
        bm = b1 + ((b2 - b1 + 180) % 360 - 180) / 2; om = ro(bm)[0]; ap = P3(bm, om, zroof(bm, om) - 1.0)
        mm.beam(P3(b1, o1, z1), ap, 0.3, 0.3, 'steel_white'); mm.beam(P3(b2, o2, z2), ap, 0.3, 0.3, 'steel_white')  # V stays
        mm.beam(P3(b1, o1, z1), P3(b2, o2, z2), 0.25, 0.25, 'steel_white')  # tie along the mast tops
    mm.build(col)
