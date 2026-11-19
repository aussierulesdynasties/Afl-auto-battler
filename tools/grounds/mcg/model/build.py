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
    qb = [P(-1, 0, -0.9), P(1, 0, -0.9), P(1, hh, -0.9), P(-1, hh, -0.9)]
    # the head tapers, so one UV quad bends the lamp grid along its diagonal: cut it into a fine grid instead
    NU, NV = 8, 16
    for i in range(NU):
        for j in range(NV):
            u0, u1, v0, v1 = i / NU, (i + 1) / NU, j / NV, (j + 1) / NV
            g = lambda u, v, d: P(2 * u - 1, v * hh, d)
            mb.face([g(u0, v0, 0), g(u1, v0, 0), g(u1, v1, 0), g(u0, v1, 0)], 'lamps',
                    uv=[(u0, v0), (u1, v0), (u1, v1), (u0, v1)])                  # field side: lamp grid
            mb.face([g(u0, v1, -0.9), g(u1, v1, -0.9), g(u1, v0, -0.9), g(u0, v0, -0.9)], 'lamps',
                    uv=[(1 - u0, v1), (1 - u1, v1), (1 - u1, v0), (1 - u0, v0)])  # back of the head: lamp frame
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
        fasc = matat('fascia', b) if 'fascia' in mats else 'tier_fascia'  # tier-front band per sector (white at the MCC)
        rfp = fp[i] if not np.isnan(fp[i]) else rout
        rfp = max(rfp, rf + d3 + 6)
        # (r, z, material-of-segment-from-previous-point)
        S = [(rf, -5.3, None), (rf, -4.2, 'fence'), (rf + 1.5, -4.2, 'conc_grey'), (rf + d1, z1, matat('t1', b)),
             (rf + d2, z1, 'conc_grey'), (rf + d2, zb2, 'tier_wall'), (rf + d2 - 0.4, zt2, fasc),
             (rf + e2, z2, matat('t2', b)), (rf + d3, z2, 'conc_grey'), (rf + d3, zb3, 'tier_wall'),
             (rf + d3 - 0.4, zt3, fasc), (rout - 8, zback, matat('t3', b)), (rout - 8, h - edge(b)[1], 'conc_grey'),
             (min(rfp, rout, screen_rb(b) - 0.3), h - edge(b)[1], 'roof_soffit')]
        secs.append(dict(b=b, S=S, ed=edge(b), dk=matat('deck', b) if 'deck' in mats else 'conc_light', rin=rin, rout=rout, h=h, rfp=rfp, zfac=zfac, tw=tw_(b)[0], fm=fseg[3], fs0=fseg[0], fend=fseg[4] if len(fseg) > 4 else fseg[3]))
    mb = MB('bowl')
    n = len(secs)
    for i in range(n):
        A = secs[i]; Bs = secs[(i + 1) % n]
        for k in range(1, len(A['S'])):
            m = A['S'][k][2]
            p0 = (*pol(A['b'], A['S'][k - 1][0]), A['S'][k - 1][1]); p1 = (*pol(A['b'], A['S'][k][0]), A['S'][k][1])
            q0 = (*pol(Bs['b'], Bs['S'][k - 1][0]), Bs['S'][k - 1][1]); q1 = (*pol(Bs['b'], Bs['S'][k][0]), Bs['S'][k][1])
            # rake UVs: u = arc length along the tier (at the segment's mid radius), v = distance up the section,
            # so seat rows run along the bowl and climb the rake (planar xy UVs smeared them into a flat wall)
            tu, tv = TILE.get(m, (1, 1)); rm = 0.5 * (A['S'][k - 1][0] + A['S'][k][0]); kk = math.pi / 180
            L = math.hypot(A['S'][k][0] - A['S'][k - 1][0], A['S'][k][1] - A['S'][k - 1][1])
            ua = A['b'] * kk * rm / tu; ub = ua + ((Bs['b'] - A['b']) % 360) * kk * rm / tu
            mb.face([p0, q0, q1, p1], m, uv=[(ua, 0), (ub, 0), (ub, L / tv), (ua, L / tv)])
        # upper back wall: deck up to the roof's outer fascia, set 1.5 m in from the roof edge
        wa = min(A['rfp'], A['rout']) - 1.5; wb = min(Bs['rfp'], Bs['rout']) - 1.5
        wa = backr(A['b'], wa); wb = backr(Bs['b'], wb)  # set-back stand wall (north gate terrace)
        fz = A['zfac']
        for za, zb, m in back_bands(A['b'], fz, A['h'] - A['ed'][1]):
            mb.face([(*pol(A['b'], wa), za), (*pol(A['b'], wa), zb), (*pol(Bs['b'], wb), zb), (*pol(Bs['b'], wb), za)], m)
        # radial step between neighbouring footprint radii shows as a wall (handled by the quad above)
    facade_all(mb, secs, fb, ri, ro, rh, tiers, matat)
    # aisle stairs: a radial strip per aisle on each tier at the bearings read off the photos (mcg.json aisles),
    # lifted 3 cm off the seats; dark concrete through navy seats, pale through grey and MCC green (photos).
    # Top tier: each aisle has a short cross landing at z ~20.7 (the "+" in every far-side photo).
    AW = D.get('aisle_w', 1.2); TU, TV = TILE.get('aisle_dark', (1.2, 3.2))
    def lift(r, z, ra, za, rb, zb, h=0.03):
        L = math.hypot(rb - ra, zb - za); return r - h * (zb - za) / L, z + h * (rb - ra) / L
    g0, g1 = D.get('gangway_t3', (20.4, 21.2)); GW = D.get('gangway_w', 3.6)
    for tn, k1 in (('t1', 3), ('t2', 7), ('t3', 11)):
        for ab in D.get('aisles', {}).get(tn, []):
            A = secs[int(round(ab / STEP)) % n]; (ra, za), (rb, zb) = A['S'][k1 - 1][:2], A['S'][k1][:2]
            m = 'aisle_dark' if matat(tn, ab) in ('seat_navy', 'seat_slate') else 'aisle_light'
            L = math.hypot(rb - ra, zb - za); (r0, z0), (r1, z1) = lift(ra, za, ra, za, rb, zb), lift(rb, zb, ra, za, rb, zb)
            d0 = math.degrees(AW / 2 / r0); d1 = math.degrees(AW / 2 / r1)
            mb.face([(*pol(ab - d0, r0), z0), (*pol(ab + d0, r0), z0), (*pol(ab + d1, r1), z1), (*pol(ab - d1, r1), z1)],
                    m, uv=[(0, 0), (AW / TU, 0), (AW / TU, L / TV), (0, L / TV)])
            if tn == 't3':
                q = []
                for zg in (g0, g1):
                    r = ra + (rb - ra) * (zg - za) / (zb - za); q.append(lift(r, zg, ra, za, rb, zb, 0.04))
                (r0, z0), (r1, z1) = q; dg = math.degrees(GW / 2 / r0)
                mb.face([(*pol(ab - dg, r0), z0), (*pol(ab + dg, r0), z0), (*pol(ab + dg, r1), z1), (*pol(ab - dg, r1), z1)], m)
    # the ground's own name signs (mcg.json signs: centre bearing, length m, texture), hand-drawn in signs.py, fixed
    # 5 cm proud of the top tier's front fascia and centred on it (MCC: members' upper tier, photo commons
    # MCC 050425.jpg; Shane Warne Stand: south top-tier front)
    for cb, SL, sm in D.get('signs', []):
        st, sh = TILE.get(sm, (SL, 1.2))
        def rz(b, z):  # the fascia's radius at this bearing and height (interpolated between sections), 5 cm proud
            f = (b % 360) / STEP; i0 = int(f) % n; t = f - int(f); out = []
            for A in (secs[i0], secs[(i0 + 1) % n]):
                (ra, za), (rb, zb) = A['S'][9][:2], A['S'][10][:2]; out.append((ra + (rb - ra) * (z - za) / (zb - za), za, zb))
            return out[0][0] * (1 - t) + out[1][0] * t - 0.05, out[0][1] * (1 - t) + out[1][1] * t, out[0][2] * (1 - t) + out[1][2] * t
        _, za, zb = rz(cb, 17); zc = 0.5 * (za + zb); sh = min(sh, zb - za); z0, z1 = zc - sh / 2, zc + sh / 2
        half = math.degrees(SL / 2 / rz(cb, zc)[0]); NS = max(2, int(SL / 0.5))
        for k in range(NS):
            ba = cb - half + 2 * half * k / NS; bb_ = cb - half + 2 * half * (k + 1) / NS  # bearing rises left to right seen from the field
            ua, ub = k / NS, (k + 1) / NS
            mb.face([(*pol(ba, rz(ba, z0)[0]), z0), (*pol(bb_, rz(bb_, z0)[0]), z0), (*pol(bb_, rz(bb_, z1)[0]), z1),
                     (*pol(ba, rz(ba, z1)[0]), z1)], sm, uv=[(ua, 0), (ub, 0), (ub, 1), (ua, 1)])
    mb.build(col)
    # plaza: traced on Esri where the paving ends (mcg.json plaza_poly = hard ground to the lawn/fence/rail,
    # paving_poly = grey paving; tan gravel between them on the north). Sampled at every 0.5 deg plus every polygon
    # corner's bearing, so each edge is one straight line with no lumps.
    HP = D['plaza_poly']; PP = D['paving_poly']
    vb = [math.degrees(math.atan2(x, y)) % 360 for x, y in HP + PP]
    pb = np.array(sorted(set(np.round(np.concatenate([bs, vb]), 4))))
    rin_ = np.array([s['rfp'] - 3 for s in secs]); bb = np.concatenate([bs - 360, bs, bs + 360]); rr3 = np.concatenate([rin_] * 3)
    r0 = np.interp(pb, bb, rr3); rh_ = polar_of_poly(HP, pb); rp_ = np.fmin(polar_of_poly(PP, pb), rh_)
    mp = MB('plaza'); n2 = len(pb)
    for i in range(n2):
        j = (i + 1) % n2; ba, bq = pb[i], pb[j]
        for r0a, r0b, r1a, r1b, m in ((r0[i], r0[j], rp_[i], rp_[j], 'paving'), (rp_[i], rp_[j], rh_[i], rh_[j], 'gravel')):
            if r1a - r0a < 0.05 and r1b - r0b < 0.05: continue
            mp.face([(*pol(ba, r0a), 0.0), (*pol(bq, r0b), 0.0), (*pol(bq, max(r0b, r1b)), 0.0), (*pol(ba, max(r0a, r1a)), 0.0)], m)
    mp.build(col)
    # roof
    mr = MB('roof')
    for i in range(n):
        A = secs[i]; Bs = secs[(i + 1) % n]
        if in_screen(A['b']) and in_screen(Bs['b']): continue  # the screen box replaces the roof here
        def ring(s, r, z): return (*pol(s['b'], r), z)
        mclear = D.get('roof_clear_w', 0.0)
        FI = D.get('roof_fascia_in', 1.0)  # inner roof edge depth: a slim ~1 m beam (ground photo s10), not a 3 m band
        tw = lambda s: min(s['tw'], s['rout'] - s['rin'] - 1) if s['tw'] > 0.5 else 0.0
        zr = lambda s, r: s['h'] - s['ed'][0] * (r - s['rin']) / (s['rout'] - s['rin'])
        for (ra, za, rb, zb_, m) in [(lambda s: s['rin'], lambda s: s['h'] - FI, lambda s: s['rin'], lambda s: s['h'], 'roof_fascia'),
                                     (lambda s: s['rin'], lambda s: s['h'], lambda s: s['rin'] + tw(s), lambda s: zr(s, s['rin'] + tw(s)), 'roof_teal'),
                                     (lambda s: s['rin'] + tw(s), lambda s: zr(s, s['rin'] + tw(s)), lambda s: s['rout'], lambda s: s['h'] - s['ed'][0], matat('roof', A['b'])),
                                     (lambda s: s['rout'], lambda s: s['h'] - s['ed'][0], lambda s: s['rout'], lambda s: s['h'] - s['ed'][1], 'roof_fascia'),
                                     (lambda s: s['rout'], lambda s: s['h'] - s['ed'][1], lambda s: s['rin'], lambda s: s['h'] - FI, 'roof_soffit')]:
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


# ---------------- facade corners: each flat face lays out its own whole windows ----------------
_WP = os.path.join(HERE, 'tex', 'wallcols.json')
WALLC = json.load(open(_WP)) if os.path.exists(_WP) else {}
CORNER_C = D.get('corner_c', 0.6)  # plain wall each side of a sharp corner, metres (the texture's own window edges can widen it)


def wallu(m):
    """a plain-wall column of texture m, as a fraction of its tile"""
    W = WALLC.get(m)
    if not W: return 0.0
    n = W['n']; idx = [i for i, w in enumerate(W['wall']) if w]
    return ((W['best'] if W['wall'][W['best']] or not idx else idx[0]) + 0.5) / n


def wallok(m, u):
    W = WALLC.get(m)
    return True if not W else bool(W['wall'][int(math.floor(u * W['n'])) % W['n']])


def snap_in(m, u, step):
    """from tile coordinate u, walk by `step` (+1 / -1 columns) to the first plain-wall column; returns that u"""
    W = WALLC.get(m)
    if not W or not any(W['wall']): return u
    n = W['n']
    for k in range(4 * n):
        uu = u + step * k / n
        if W['wall'][int(math.floor(uu * n)) % n]: return uu
    return u


def face_u(m, s, sa, sb, cl, cr, whole):
    """tile u at distance s along a flat face [sa, sb] (metres along the wall), corner strips cl / cr wide.
    whole: the texture is one layout for the whole run (u = metres / tile); else repeating bays."""
    tw = TILE.get(m, (1, 1))[0]
    if whole:  # layout drawn from the photo for this whole run: only a window that crosses a corner inside it goes
        uL = snap_in(m, sa / tw, 1) if cl > 0 else sa / tw
        uR = snap_in(m, sb / tw, -1) if cr > 0 else sb / tw
        if uR < uL: return wallu(m)
        return min(max(s / tw, uL), uR)
    Lf = sb - sa; N = int(math.floor((Lf - cl - cr) / tw + 1e-6)); uw = wallu(m)
    if N < 1: return uw
    mL = cl + 0.5 * (Lf - cl - cr - N * tw)
    return uw + min(max((s - sa - mL) / tw, 0.0), N)


def env_corners():
    """bearings of the sharp corners (turn >= 15 deg) on the outer footprint (osm envelope)"""
    out = []
    for k in ('shane_warne', 'mcc', 'olympic', 'ponsford'):
        P = np.array(D['osm'][k], float); n = len(P)
        for i in range(n):
            a, b, c = P[i - 1], P[i], P[(i + 1) % n]
            br = math.degrees(math.atan2(b[0], b[1])) % 360; r = math.hypot(*b)
            env = np.nanmax([polar_of_poly(D['osm'][kk], [br])[0] for kk in ('shane_warne', 'mcc', 'olympic', 'ponsford')] + [0.0])
            if abs(env - r) > 0.3: continue
            d1 = b - a; d2 = c - b
            if abs(math.degrees(math.atan2(d1[0] * d2[1] - d1[1] * d2[0], d1 @ d2))) >= 15: out.append(round(br, 4))
    return sorted(set(out))


def facade_all(mb, secs, fb, ri, ro, rh, tiers, matat):
    """Facade walls, undercrofts, block decks and end walls at the footprint, on bearings refined so every footprint
    corner, facade segment edge and undercroft edge is an exact vertex. Each flat face between corners lays out its own
    whole windows with a plain strip at each sharp corner; no texture runs round an edge."""
    STEP = D.get('step', 0.5); C = CORNER_C
    corners = env_corners(); cs = set(corners)
    brk = set(np.round(np.arange(0, 360, STEP), 4)) | cs | {round(s_[0] % 360, 4) for s_ in D['facade']}
    for u in D.get('undercroft', []): brk |= {round(u[0], 4), round(u[1], 4)}
    fbs = np.array(sorted(brk))
    fp = np.full(len(fbs), np.nan)
    for k in ('shane_warne', 'mcc', 'olympic', 'ponsford'):
        fp = np.fmax(fp, polar_of_poly(D['osm'][k], fbs))
    F = []
    for i, b in enumerate(fbs):
        rf = fb(b)[0]; rout = ro(b)[0]; d3 = tiers(b)[7]
        rfp = fp[i] if not np.isnan(fp[i]) else rout; rfp = max(rfp, rf + d3 + 6)
        fs = facseg(b)
        F.append(dict(b=float(b), rfp=rfp, rout=rout, zfac=fs[2], fm=fs[3], fs0=fs[0], fend=fs[4] if len(fs) > 4 else fs[3],
                      dk=matat('deck', b) if 'deck' in D['mats'] else 'conc_light'))
    n = len(F); P3 = lambda b, r, z: (*pol(b, r), z)
    for i in range(n):  # distance along the wall from each facade segment's start
        A = F[i]
        if i == 0 or F[i - 1]['fs0'] != A['fs0']: A['s'] = 0.0
        else:
            Pv = F[i - 1]; A['s'] = Pv['s'] + math.dist(pol(Pv['b'], Pv['rfp']), pol(A['b'], A['rfp']))
    # sharp corners also read off the built wall line itself (a turn >= 15 deg between built points), so a corner whose
    # footprint vertex sits behind another block's outline (the 351 deg step) still gets its corner treatment
    XY = [np.array(pol(A['b'], A['rfp'])) for A in F]
    for k in range(n):
        d1 = XY[k] - XY[k - 1]; d2 = XY[(k + 1) % n] - XY[k]
        if np.linalg.norm(d1) < 0.05 or np.linalg.norm(d2) < 0.05: continue
        if abs(math.degrees(math.atan2(d1[0] * d2[1] - d1[1] * d2[0], d1 @ d2))) >= 15: cs.add(round(F[k]['b'], 4))
    runs = []; i = 0
    while i < n:
        j = i
        while j + 1 < n and F[j + 1]['s'] > 0: j += 1
        runs.append((i, j + 1)); i = j + 1
    for i0, i1 in runs:  # sections i0 .. i1-1; F[i1 % n] (next run's start) closes the last quad
        A0 = F[i0]; m = A0['fm']; fz = A0['zfac']; tw, tv = TILE.get(m, (1, 1))
        E = F[i1 % n]; L_ = F[i1 - 1]; send = L_['s'] + math.dist(pol(L_['b'], L_['rfp']), pol(E['b'], E['rfp']))
        whole = True  # photo-aligned layout (u = metres / tile) for every run; windows move only at corners
        prv = F[(i0 - 1) % n]
        step0 = abs(prv['zfac'] - fz) > 0.01; step1 = abs(E['zfac'] - fz) > 0.01
        cuts = [i0] + [k for k in range(i0 + 1, i1) if round(F[k]['b'], 4) in cs] + [i1]
        faces = [dict(fa=fa, fb=fz_, sa=F[fa]['s'], sb=send if fz_ == i1 else F[fz_]['s'], d=0.0, uL=-1e9, uR=1e9) for fa, fz_ in zip(cuts, cuts[1:])]
        if whole:  # photo layout for the whole run: at each corner inside it, a window that crosses the corner moves whole
            cw = C / tw  # onto the face holding most of it, leaving a plain strip C wide at the corner
            for Lf, Rf in zip(faces, faces[1:]):
                uc = Lf['sb'] / tw - Lf['d']; Rf['d'] = Lf['d']
                if wallok(m, uc): Lf['uR'] = uc; Rf['uL'] = uc; continue
                ws = snap_in(m, uc, -1); we = snap_in(m, uc, 1)
                if we - uc >= uc - ws:  # mostly on the right face: left face ends on plain wall, right face shifts
                    Lf['uR'] = ws; Rf['d'] = Lf['sb'] / tw - (ws - cw); Rf['uL'] = ws
                else:  # mostly on the left face: it shifts so the window ends a strip short of the corner
                    Lf['d'] = Lf['sb'] / tw - (we + cw); Lf['uR'] = we; Rf['uL'] = we
        cw = C / tw
        if round(A0['b'], 4) in cs or step0:  # run starts on a sharp corner or a height step: no part-window at the edge
            u0 = faces[0]['sa'] / tw
            if not wallok(m, u0 + cw): faces[0]['d'] = 0.0; faces[0]['uL'] = snap_in(m, u0 + cw, 1)
            else: faces[0]['uL'] = u0 + cw
            faces[0]['uL'] = max(faces[0]['uL'], u0)
        if round(E['b'], 4) in cs or step1:
            fl = faces[-1]; u1 = send / tw - fl['d']
            fl['uR'] = min(fl['uR'], snap_in(m, u1 - cw, -1) if not wallok(m, u1 - cw) else u1 - cw)
        for fc in faces:
            fa, fz_, sa, sb = fc['fa'], fc['fb'], fc['sa'], fc['sb']
            cl = C if (fa > i0 or round(F[fa]['b'], 4) in cs or step0) else 0.0
            cr = C if (fz_ < i1 or round(E['b'], 4) in cs or step1) else 0.0
            if whole: fu = lambda s_, fc=fc: min(max(s_ / tw - fc['d'], fc['uL']), fc['uR'])
            else: fu = lambda s_, sa=sa, sb=sb, cl=cl, cr=cr: face_u(m, s_, sa, sb, cl, cr, False)
            for k in range(fa, fz_):
                A = F[k]; Bs = F[(k + 1) % n]; s0 = A['s']; s1 = sb if k + 1 == fz_ else Bs['s']
                ua = fu(s0); ub = fu(s1)
                a0 = P3(A['b'], A['rfp'], 0.0); b0 = P3(Bs['b'], Bs['rfp'], 0.0); a1 = P3(A['b'], A['rfp'], fz); b1 = P3(Bs['b'], Bs['rfp'], fz)
                uc = next((u for u in D.get('undercroft', []) if u[0] <= A['b'] < u[1]), None)
                if uc is None:
                    mb.face([a0, a1, b1, b0], m, uv=[(ua, 0), (ua, fz / tv), (ub, fz / tv), (ub, 0)])
                    continue
                # open ground floor (f045 NE blocks): wall from the slab up, dark back wall set in, soffit, shaded floor
                zu, sbk = uc[2], uc[3]; ra, rb_ = A['rfp'] - sbk, Bs['rfp'] - sbk; kq = math.pi / 180
                a2 = P3(A['b'], A['rfp'], zu); b2 = P3(Bs['b'], Bs['rfp'], zu)
                mb.face([a2, a1, b1, b2], m, uv=[(ua, zu / tv), (ua, fz / tv), (ub, fz / tv), (ub, zu / tv)])
                ka, kb = P3(A['b'], ra, 0.0), P3(Bs['b'], rb_, 0.0); ka2, kb2 = P3(A['b'], ra, zu), P3(Bs['b'], rb_, zu)
                ub2 = ((Bs['b'] - uc[0]) % 360) * kq * ra / 6.0; ua2 = (A['b'] - uc[0]) * kq * ra / 6.0
                mb.face([ka, ka2, kb2, kb], 'uc_back', uv=[(ua2, 0), (ua2, zu / 24.0), (ub2, zu / 24.0), (ub2, 0)])
                mb.face([ka2, a2, b2, kb2], 'uc_soffit')
                mb.face([P3(A['b'], ra, 0.02), P3(Bs['b'], rb_, 0.02), P3(Bs['b'], Bs['rfp'], 0.02), P3(A['b'], A['rfp'], 0.02)], 'uc_floor')
                for be in (uc[0], uc[1]):  # end walls where the open floor meets the closed one
                    if abs(A['b'] - be) < 1e-6 or abs(Bs['b'] - be) < 1e-6:
                        S_ = A if abs(A['b'] - be) < 1e-6 else Bs
                        q = [P3(be, S_['rfp'] - sbk, 0.0), P3(be, S_['rfp'] - sbk, zu), P3(be, S_['rfp'], zu), P3(be, S_['rfp'], 0.0)]
                        mb.face(q, 'uc_back'); mb.face(q[::-1], 'uc_back')
    # solid corner strips (director: "a solid strip at every corner"): at each sharp footprint corner, C/2 of plain
    # wall each side of the edge, 3 cm proud of the facade, full face height (from the slab up over an open floor)
    for k in range(n):
        if round(F[k]['b'], 4) not in cs: continue
        Pc = F[k]; Pv = F[(k - 1) % n]; Pn = F[(k + 1) % n]; kc = pol(Pc['b'], Pc['rfp'])
        out = np.array(pol(Pc['b'], 1.0)) - np.array(pol(Pc['b'], 0.0)); out = out / np.linalg.norm(out) * 0.03
        for Q, Sd in ((Pv, Pv), (Pn, Pc)):  # Sd: the section whose face this half sits on
            kq = np.array(pol(Q['b'], Q['rfp'])) - np.array(kc); Lq = np.linalg.norm(kq)
            if Lq < 1e-3: continue
            e = np.array(kc) + kq / Lq * min(C / 2, Lq) + out; c0 = np.array(kc) + out
            zt = Sd['zfac']; ucq = next((u for u in D.get('undercroft', []) if u[0] <= Sd['b'] < u[1]), None)
            zb = ucq[2] if ucq else 0.0; mm = 'cs_' + Sd['fm']; tvq = TILE.get(mm, (0.6, 1))[1]
            q = [(*c0, zb), (*c0, zt), (*e, zt), (*e, zb)]; uv = [(0, zb / tvq), (0, zt / tvq), (0.5, zt / tvq), (0.5, zb / tvq)]
            mb.face(q, mm, uv=uv); mb.face(q[::-1], mm, uv=uv[::-1])
    for k in range(n):  # block roofs (decks) and the end walls where the next block is lower or higher
        A = F[k]; Bs = F[(k + 1) % n]; fz = A['zfac']; gz = Bs['zfac']
        a1 = P3(A['b'], A['rfp'], fz); b1 = P3(Bs['b'], Bs['rfp'], fz)
        c0 = P3(A['b'], A['rout'] - 8, fz); c1 = P3(Bs['b'], Bs['rout'] - 8, fz)
        if A['dk'] in ('solar', 'terrace'):  # panels / paving only on the front 9 m of the block roof, plain roof behind
            ra, rb_ = max(A['rout'] - 8, A['rfp'] - 9), max(Bs['rout'] - 8, Bs['rfp'] - 9)
            m0 = P3(A['b'], ra, fz); m1 = P3(Bs['b'], rb_, fz)
            mb.face([m0, a1, b1, m1][::-1], A['dk']); mb.face([c0, m0, m1, c1][::-1], 'roof_grey')
        else:
            mb.face([c0, a1, b1, c1][::-1], A['dk'])
        if abs(fz - gz) > 0.01:  # end wall: its own whole windows, plain strip at both vertical edges
            lo, top = min(fz, gz), max(fz, gz); hm = A['fend'] if fz > gz else Bs['fend']
            L = Bs['rfp'] - (Bs['rout'] - 8); tv = TILE.get(hm, (1, 1))[1]
            u0 = face_u(hm, 0.0, 0.0, L, C, C, False); u1 = face_u(hm, L, 0.0, L, C, C, False)
            q = [P3(Bs['b'], Bs['rfp'], lo), P3(Bs['b'], Bs['rfp'], top), P3(Bs['b'], Bs['rout'] - 8, top), P3(Bs['b'], Bs['rout'] - 8, lo)]
            uv = [(u0, lo / tv), (u0, top / tv), (u1, top / tv), (u1, lo / tv)]
            mb.face(q, hm, uv=uv); mb.face(q[::-1], hm, uv=uv[::-1])


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


def backr(b, r):
    """Upper back wall radius: a measured set-back (mcg.json backr [b0, b1, r]) or the default r."""
    for b0, b1, rr in D.get('backr', []):
        if b0 <= b % 360 < b1: return rr
    return r


def screen_rb(b):
    """Back face radius of the screen box at bearing b (inf outside the screens): the bowl soffit stops behind it."""
    return min([S['rb'] for S in D.get('screens', []) if S['b0'] <= b % 360 <= S['b1']] or [1e9])


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
            mb.beam((x, y, S['zt']), (x, y, S['post_top']), 0.25, 0.25, 'steel_galv')  # poles: GE f045 (NE), f225 (SW)
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
            q = [P3(a0, r, z0), P3(a1, r, z0), P3(a1, r, z1), P3(a0, r, z1)]; mb.face(q, 'backglass'); mb.face(q[::-1], 'backglass')
            mb.face([P3(a0, r, z1), P3(a1, r, z1), P3(a1, r - 8, z1), P3(a0, r - 8, z1)], 'roof_grey')
    for b0, b1, r0, r1, zt, fm, sm in D.get('blocks', []):  # stair towers and podiums standing out from the facade
        n = max(2, int(abs(b1 - b0) / 0.5) + 1); bb = np.linspace(b0, b1, n); kk = math.pi / 180
        tv = TILE.get(fm, (1, 1))[1]; sv = TILE.get(sm, (1, 1))[1]; Lf = (b1 - b0) * kk * r1
        whole = TILE.get(fm, (1, 1))[0] >= 0.8 * Lf; Cc = CORNER_C
        for a0, a1 in zip(bb, bb[1:]):  # front: its own whole windows, plain strip at both corners
            u0 = face_u(fm, (a0 - b0) * kk * r1, 0.0, Lf, Cc, Cc, whole); u1 = face_u(fm, (a1 - b0) * kk * r1, 0.0, Lf, Cc, Cc, whole)
            mb.face([P3(a0, r1, 0), P3(a1, r1, 0), P3(a1, r1, zt), P3(a0, r1, zt)][::-1], fm,
                    uv=[(u0, 0), (u1, 0), (u1, zt / tv), (u0, zt / tv)][::-1])
            mb.face([P3(a0, r0, zt), P3(a1, r0, zt), P3(a1, r1, zt), P3(a0, r1, zt)], 'roof_grey')
        for b, sg in ((b0, -1), (b1, 1)):  # sides: the same, so no window sits on either vertical edge
            q = [P3(b, r0, 0), P3(b, r1, 0), P3(b, r1, zt), P3(b, r0, zt)]; L = r1 - r0
            v0, v1 = face_u(sm, 0.0, 0.0, L, Cc, Cc, False), face_u(sm, L, 0.0, L, Cc, Cc, False)
            mb.face(q if sg > 0 else q[::-1], sm, uv=[(v0, 0), (v1, 0), (v1, zt / sv), (v0, zt / sv)] if sg > 0 else [(v0, zt / sv), (v1, zt / sv), (v1, 0), (v0, 0)])
            # solid strip on both faces at this front corner (director: "a solid strip at every corner")
            cp = np.array(pol(b, r1)); tg = np.array(pol(b + sg * 0.01, r1)) - cp; tg /= np.linalg.norm(tg)
            ro = np.array(pol(b, 1.0)) - np.array(pol(b, 0.0)); ro /= np.linalg.norm(ro); h = CORNER_C / 2
            for m_, dirv, nv in ((fm, -tg, ro), (sm, -ro, tg)):  # front face runs back along -tg, side face inward
                mm = 'cs_' + m_; tq = TILE.get(mm, (0.6, 1))[1]; o = nv * 0.03
                q = [(*(cp + o), 0), (*(cp + o), zt), (*(cp + dirv * h + o), zt), (*(cp + dirv * h + o), 0)]
                uv = [(0, 0), (0, zt / tq), (0.5, zt / tq), (0.5, 0)]; mb.face(q, mm, uv=uv); mb.face(q[::-1], mm, uv=uv[::-1])
    for b0, b1, rf, rb, zf, zb in D.get('lanterns', []):  # sloped glazed skylight on a block roof (NW glass block, f315)
        bb = np.linspace(b0, b1, max(2, int(abs(b1 - b0) / 0.5) + 1)); kk = math.pi / 180; L = math.hypot(rf - rb, zb - zf)
        for a0, a1 in zip(bb, bb[1:]):
            u0 = (a0 - b0) * kk * rf / 6.0; u1 = (a1 - b0) * kk * rf / 6.0
            mb.face([P3(a0, rf, zf), P3(a1, rf, zf), P3(a1, rb, zb), P3(a0, rb, zb)], 'skylight', uv=[(u0, 0), (u1, 0), (u1, L / 24.0), (u0, L / 24.0)])
            mb.face([P3(a0, rb, zf), P3(a0, rb, zb), P3(a1, rb, zb), P3(a1, rb, zf)], 'steel_dark')
        for b, sg in ((b0, 1), (b1, -1)):
            q = [P3(b, rf, zf), P3(b, rb, zb), P3(b, rb, zf)]; mb.face(q if sg > 0 else q[::-1], 'steel_dark')
    for b, r, z in D.get('legs', []):  # legs under the north-east metal box
        mb.beam(P3(b, r, 0.0), P3(b, r, z), 0.45, 0.45, 'paint_white')
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
        mm.beam(P3(b, o, M['z0']), tp, 1.0, 0.8, 'steel_galv')
        ri_ = o - M['stay_in']; mm.beam(tp, P3(b, ri_, zroof(b, ri_) + 0.2), 0.25, 0.25, 'steel_galv')
    for (b1, o1, z1), (b2, o2, z2) in zip(tops, tops[1:]):
        zl = M['z0'] + 1.0; zu = min(rh(b1)[0], rh(b2)[0]) - 4.5
        mm.beam(P3(b1, o1, zl), P3(b2, o2, zu), 0.3, 0.3, 'steel_galv')
        mm.beam(P3(b1, o1, zu), P3(b2, o2, zl), 0.3, 0.3, 'steel_galv')
        bm = b1 + ((b2 - b1 + 180) % 360 - 180) / 2; om = ro(bm)[0]; ap = P3(bm, om, zroof(bm, om) - 1.0)
        mm.beam(P3(b1, o1, z1), ap, 0.3, 0.3, 'steel_galv'); mm.beam(P3(b2, o2, z2), ap, 0.3, 0.3, 'steel_galv')  # V stays
        mm.beam(P3(b1, o1, z1), P3(b2, o2, z2), 0.25, 0.25, 'steel_galv')  # tie along the mast tops
    mm.build(col)
