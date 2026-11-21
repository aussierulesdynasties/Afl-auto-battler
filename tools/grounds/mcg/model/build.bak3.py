# MCG exterior, built from measurements of the 2026 Google Earth views and the Esri satellite (model/mcg.json).
# Runs inside Blender: import build; build.build_all(). Local frame: x east, y north, metres, z up from the plaza.
import bpy, math, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from mb import MB, rect, ccw
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
    # head faces the field centre, tilted back by T['tilt'] degrees
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
             (rf + d3 - 0.4, zt3, 'fascia'), (rout - 8, zback, matat('t3', b)), (rout - 8, h - 4.5, 'conc_grey'),
             (min(rfp, rout), h - 4.5, 'roof_soffit')]
        secs.append(dict(b=b, S=S, rin=rin, rout=rout, h=h, rfp=rfp, zfac=zfac, tw=tw_(b)[0], fm=fseg[3]))
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
        mb.face([a0, a1, b1, b0], A['fm'])
        c0 = (*pol(A['b'], A['rout'] - 8), fz); c1 = (*pol(Bs['b'], Bs['rout'] - 8), fz)
        mb.face([c0, a1, b1, c1][::-1], 'conc_light')
        if abs(fz - gz) > 0.01:  # end wall where the next block is lower or higher
            lo, top = min(fz, gz), max(fz, gz); hm = A['fm'] if fz > gz else Bs['fm']
            q = [(*pol(Bs['b'], Bs['rfp']), lo), (*pol(Bs['b'], Bs['rfp']), top), (*pol(Bs['b'], Bs['rout'] - 8), top), (*pol(Bs['b'], Bs['rout'] - 8), lo)]
            mb.face(q, hm); mb.face(q[::-1], hm)
        # radial step between neighbouring footprint radii shows as a wall (handled by the quad above)
    mb.build(col)
    # roof
    mr = MB('roof')
    for i in range(n):
        A = secs[i]; Bs = secs[(i + 1) % n]
        if in_screen(A['b']) and in_screen(Bs['b']): continue  # the screen box replaces the roof here
        def ring(s, r, z): return (*pol(s['b'], r), z)
        mclear = D.get('roof_clear_w', 0.0)
        tw = lambda s: min(s['tw'], s['rout'] - s['rin'] - 1) if s['tw'] > 0.5 else 0.0
        zr = lambda s, r: s['h'] - 2.0 * (r - s['rin']) / (s['rout'] - s['rin'])
        for (ra, za, rb, zb_, m) in [(lambda s: s['rin'], lambda s: s['h'] - 3.0, lambda s: s['rin'], lambda s: s['h'], 'roof_fascia'),
                                     (lambda s: s['rin'], lambda s: s['h'], lambda s: s['rin'] + tw(s), lambda s: zr(s, s['rin'] + tw(s)), 'roof_teal'),
                                     (lambda s: s['rin'] + tw(s), lambda s: zr(s, s['rin'] + tw(s)), lambda s: s['rout'], lambda s: s['h'] - 2.0, matat('roof', A['b'])),
                                     (lambda s: s['rout'], lambda s: s['h'] - 2.0, lambda s: s['rout'], lambda s: s['h'] - 4.5, 'roof_fascia'),
                                     (lambda s: s['rout'], lambda s: s['h'] - 4.5, lambda s: s['rin'], lambda s: s['h'] - 3.0, 'roof_soffit')]:
            mr.face([ring(A, ra(A), za(A)), ring(A, rb(A), zb_(A)), ring(Bs, rb(Bs), zb_(Bs)), ring(Bs, ra(Bs), za(Bs))][::-1], m)
    mr.build(col)
    struct_all(col)
    screens_all(col)
    canopy_all(col)


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
        a, o, h = ri(b)[0], ro(b)[0], rh(b)[0]; return h - 2.0 * (r - a) / (o - a)
    P3 = lambda b, r, z: (*pol(b, r), z)
    T = D['trusses']; rs = periodic(T['r_start']); mb = MB('trusses')
    for b in T['b']:
        o = ro(b)[0]; h = rh(b)[0]; r0 = rs(b)[0]; top = P3(b, o - 1.0, h - 2.0 + T['up'])
        mb.beam(P3(b, r0, zroof(b, r0) + 0.3), top, 0.9, 0.9, 'steel_blue')
        for sg in (-1, 1):  # A-frame legs splayed 2.5 m each side along the roof edge
            db = sg * math.degrees(2.5 / o); mb.beam(P3(b + db, o - 1.0, h - 2.0 - T['down']), top, 0.7, 0.7, 'steel_blue')
        mb.beam(P3(b, r0 + 0.5 * (o - r0), zroof(b, r0 + 0.5 * (o - r0)) + 0.2), P3(b, o - 1.0, h - 2.0 - T['down'] * 0.5), 0.5, 0.5, 'steel_blue')
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
