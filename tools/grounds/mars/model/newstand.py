# The two 2026 stands on the south-east (kind 'shell' in mars.json), from the 2026 photos (Wikimedia Commons
# "Eureka Stadium 2026 1-7", the Sept 2026 aerial, press/al_2026) and Google Earth (Dec 2025, the first roof on and the
# second's frame up):
#  - lower and upper tier on precast treads; the upper tier's underside is open behind, stepped row by row, carried on
#    galvanised steel rakers, columns and X bracing, with a pale precast parapet faceted bay by bay along its back;
#  - a grey concrete blockwork ground floor set in under the upper tier, with door openings cut through it;
#  - a thin shell roof, lens-shaped in plan, low at its back edge and curling up to the front, highest mid-stand;
#    underneath: galvanised radial beams, glulam timber rafters between them and steel purlins; a handrail round the
#    back edge;
#  - pairs of raking galvanised columns (a V from one base) carrying the roof's back edge, each faced with a glulam strip;
#  - a precast lift and stair core at the outer end of each stand.
import math
import numpy as np
import build as B

up = np.array([0, 0, 1.0])


def tube(mb, p, q, r, m, n=10):
    """round member from p to q"""
    p = np.array(p, float); q = np.array(q, float); d = q - p; L = np.linalg.norm(d); d /= L
    a = np.cross(d, up); a = a / np.linalg.norm(a) if np.linalg.norm(a) > 1e-6 else np.array([1.0, 0, 0]); b = np.cross(a, d)
    ring = lambda c: [c + r * (math.cos(2 * math.pi * k / n) * a + math.sin(2 * math.pi * k / n) * b) for k in range(n)]
    P, Q = ring(p), ring(q)
    for k in range(n):
        j = (k + 1) % n; mid = (P[k] + P[j]) / 2 - p
        B.oriented(mb, [P[k], P[j], Q[j], Q[k]], m, mid)


def shell(S, mb, mr):
    bs = B.brange(S); b0, b1 = bs[0], bs[-1]; M = S['mats']
    zs0, zs1 = S['z_seat']; zu0, zu1 = S['z_upper']; LB = S['lower_back']; WL = S['wall_in']
    R = S['shell']   # roof: z_back/z_front mid-stand, drop at the ends, curl exponent

    def geo(b):
        rf = B.fence_r(b % 360); ri, ro = B.interp(S['roof'], b); rs0 = rf + S['seat_front']; rb = B.interp(S['back'], b)[0]
        return rf, ri, ro, rs0, rb

    def prof(b):
        rf, ri, ro, rs0, rb = geo(b); rl = rs0 + LB
        # front wall, lower rake, the cross-aisle step up, upper rake, parapet over the back
        return [(rs0, 0.0), (rs0, zs0), (rl, zs1), (rl, zs1 + 0.2), (rl + 1.8, zs1 + 0.2), (rl + 1.8, zu0), (rb - 0.4, zu1),
                (rb - 0.4, zu1 + 1.1), (rb, zu1 + 1.1), (rb, zu1 - 1.4)]

    n1, n5 = B.nrows(prof, bs, 1), B.nrows(prof, bs, 5)
    mats = [M['front'], M['seat'], 'conc_wall', 'conc_tread', 'conc_wall', M['seat'], 'conc_wall', 'conc_wall', 'parapet']
    tp, tm = B.terrace(prof, mats, [(1, n1), (5, n5)])
    B.strip(mb, bs, tp, tm, -1)
    B.seat_rows(bs, prof, 1, n1, pal='blue'); B.seat_rows(bs, prof, 5, n5, pal=S.get('pal', 'mtn'))
    for b, sg in ((b0, -1), (b1, 1)):
        P = tp(b); rf, ri, ro, rs0, rb = geo(b); rl = rs0 + LB
        B.endcap(mb, b, P + [(rb - 0.9, zu1 - 2.0), (rl + 1.8, zu0 - 0.45), (rl + 1.8, 0.0)], 'conc_wall', sg)
    underside(S, bs, geo, n5, mb, mr)
    ground_floor(S, bs, geo, mb)
    roof(S, bs, geo, mr)
    for c in S.get('cores', []):
        core(mb, c[0], geo, S, c[1], c[2] if len(c) > 2 else 'conc_core')


def underside(S, bs, geo, n5, mb, mr):
    """the upper tier seen from behind: a stepped precast soffit one step per row, the back parapet's own underside,
    a raker beam under every bay, columns down to the ground and X bracing between them"""
    zs0, zs1 = S['z_seat']; zu0, zu1 = S['z_upper']; LB = S['lower_back']; th = 0.45
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]
        def steps(b):
            rf, ri, ro, rs0, rb = geo(b); r0 = rs0 + LB + 1.8; r1 = rb - 0.4; pts = [(r1 - 0.5, zu1 - 2.0)]
            for k in range(n5 - 1, -1, -1):   # each tread's underside, back to front
                zk = zu0 + (zu1 - zu0) * k / max(1, n5 - 1) - th; rk = r0 + (r1 - r0) * k / n5
                pts.append((pts[-1][0], zk)); pts.append((rk, zk))
            return pts
        A, Bq = steps(ba), steps(bb); bm = math.radians(0.5 * (ba + bb)); rad = np.array([math.sin(bm), math.cos(bm), 0.0])
        for k in range(len(A) - 1):
            (r0, z0), (r1, z1) = A[k], A[k + 1]; (s0, w0), (s1, w1) = Bq[k], Bq[k + 1]
            n = -up if abs(z1 - z0) < 1e-6 else -rad
            if abs(r1 - r0) < 1e-6 and abs(z1 - z0) < 1e-6: continue
            B.oriented(mb, [B.P3(ba, r0, z0), B.P3(bb, s0, w0), B.P3(bb, s1, w1), B.P3(ba, r1, z1)], 'conc_soffit', n)
    bay = S['bay']; b = bs[0] + math.degrees(0.5 * bay / geo(bs[0])[4])
    cols = []
    while b < bs[-1] - 0.2:
        rf, ri, ro, rs0, rb = geo(b); r0 = rs0 + LB + 1.8
        zf = lambda r: zu0 + (zu1 - zu0) * (r - r0) / (rb - 0.4 - r0) - 0.75
        mr.beam(B.P3(b, r0 + 0.5, zf(r0 + 0.5)), B.P3(b, rb - 0.2, zf(rb - 0.2)), 0.45, 0.9, 'steel_galv')   # raker
        rc = rb - 3.5; cols.append((b, rc, zf(rc) - 0.45))
        mr.beam(B.P3(b, rc, 0.0), B.P3(b, rc, zf(rc) - 0.4), 0.45, 0.45, 'steel_galv')   # back column
        rm = r0 + 0.45 * (rb - r0); mr.beam(B.P3(b, rm, 0.0), B.P3(b, rm, zf(rm) - 0.4), 0.4, 0.4, 'steel_galv')
        b += math.degrees(bay / rb)
    for (ba, ra, za), (bb, rb_, zb) in zip(cols[:-1], cols[1:]):   # ring beam under the parapet line and X bracing
        mr.beam(B.P3(ba, ra, za), B.P3(bb, rb_, zb), 0.35, 0.6, 'steel_galv')
        zl = 3.8
        mr.beam(B.P3(ba, ra, zl), B.P3(bb, rb_, zb - 0.3), 0.18, 0.18, 'steel_galv')
        mr.beam(B.P3(bb, rb_, zl), B.P3(ba, ra, za - 0.3), 0.18, 0.18, 'steel_galv')
    # the parapet's chamfered bottom edge: a sloped face from the parapet foot back under the rake
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]; ra, rb_ = geo(ba)[4], geo(bb)[4]
        bm = math.radians(0.5 * (ba + bb)); rad = np.array([math.sin(bm), math.cos(bm), 0.0])
        B.oriented(mb, [B.P3(ba, ra, zu1 - 1.4), B.P3(bb, rb_, zu1 - 1.4), B.P3(bb, rb_ - 0.9, zu1 - 2.0), B.P3(ba, ra - 0.9, zu1 - 2.0)],
                   'parapet', rad - up)
        # the galvanised ring girder under the parapet: 1.0 m deep plate girder, flanges proud
        ga, gb = ra - 1.3, rb_ - 1.3; zt, zb = zu1 - 2.0, zu1 - 3.0
        B.oriented(mr, [B.P3(ba, ga, zb), B.P3(bb, gb, zb), B.P3(bb, gb, zt), B.P3(ba, ga, zt)], 'steel_galv', rad)
        for z in (zb, zt - 0.05):
            B.oriented(mr, [B.P3(ba, ga - 0.2, z), B.P3(bb, gb - 0.2, z), B.P3(bb, gb + 0.2, z), B.P3(ba, ga + 0.2, z)], 'steel_galv', -up if z == zb else up)
            B.oriented(mr, [B.P3(ba, ga + 0.2, z), B.P3(bb, gb + 0.2, z), B.P3(bb, gb + 0.2, z + 0.05), B.P3(ba, ga + 0.2, z + 0.05)], 'steel_galv', rad)


def ground_floor(S, bs, geo, mb):
    """blockwork walls 3.4 m high set wall_in m inside the parapet, a door opening cut through every few bays (reveal,
    dark room behind), a concrete slab over"""
    zw = 3.4; WL = S['wall_in']; doors = S.get('doors', 3); bay = S['bay']
    s_acc = 0.0; nb = 0
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]; ra, rb_ = geo(ba)[4] - WL, geo(bb)[4] - WL
        bm = math.radians(0.5 * (ba + bb)); rad = np.array([math.sin(bm), math.cos(bm), 0.0])
        seg = math.radians(bb - ba) * 0.5 * (ra + rb_)
        door = (int(s_acc / bay) % doors == 1) and (s_acc % bay) > bay * 0.4 and (s_acc % bay) < bay * 0.4 + 2.0
        s_acc += seg
        if door:   # opening 2.4 m high: lintel above, a 0.25 m reveal and a dark back wall 3 m in
            B.oriented(mb, [B.P3(ba, ra, 2.4), B.P3(bb, rb_, 2.4), B.P3(bb, rb_, zw), B.P3(ba, ra, zw)], 'conc_block', rad)
            B.oriented(mb, [B.P3(ba, ra - 0.25, 2.4), B.P3(bb, rb_ - 0.25, 2.4), B.P3(bb, rb_, 2.4), B.P3(ba, ra, 2.4)], 'conc_wall', -up)
            B.oriented(mb, [B.P3(ba, ra - 3.0, 0), B.P3(bb, rb_ - 3.0, 0), B.P3(bb, rb_ - 3.0, 2.4), B.P3(ba, ra - 3.0, 2.4)], 'tri_void', rad)
        else:
            B.oriented(mb, [B.P3(ba, ra, 0), B.P3(bb, rb_, 0), B.P3(bb, rb_, zw), B.P3(ba, ra, zw)], 'conc_block', rad)
        B.oriented(mb, [B.P3(ba, ra, zw), B.P3(bb, rb_, zw), B.P3(bb, rb_ + 0.3, zw), B.P3(ba, ra + 0.3, zw)], 'conc_wall', up)
        rfa, rfb = [geo(x)[3] + S['lower_back'] + 1.8 for x in (ba, bb)]
        B.oriented(mb, [B.P3(ba, rfa, zw), B.P3(bb, rfb, zw), B.P3(bb, rb_, zw), B.P3(ba, ra, zw)], 'conc_soffit', up)
        zt = S['z_upper'][0] - 0.45
        B.oriented(mb, [B.P3(ba, rfa, zw), B.P3(bb, rfb, zw), B.P3(bb, rfb, zt), B.P3(ba, rfa, zt)], 'conc_block', rad)


def roof(S, bs, geo, mr):
    """the shell: plan between the roof table's front (ri) and back (ro) edges; height z(s, u) with u = 0 at the front:
    the back edge at z_back, curling up to z_front at the front (exponent 'curl'), both dropping 'drop' m to the ends"""
    R = S['shell']; b0, b1 = bs[0], bs[-1]; th = 0.35; K = 10
    def Z(b, u):
        t = (b - b0) / (b1 - b0); e = 1 - (2 * t - 1) ** 2
        zb = R['z_back'] - R['drop'] * (1 - e); zf = R['z_front'] - R['drop_front'] * (1 - e)
        return zb + (zf - zb) * (1 - u) ** R['curl']
    def Rr(b, u):   # lens plan (GE Dec 2025, the first roof): full depth mid-stand, 'lens' of it at the ends
        rf, ri, ro, rs0, rb = geo(b); t = (b - b0) / (b1 - b0); L = R.get('lens', 1.0)
        return ri + (ro - ri) * u * (L + (1 - L) * math.sqrt(max(0.0, 1 - (2 * t - 1) ** 2)))
    P = lambda b, u, dz=0.0: B.P3(b, Rr(b, u), Z(b, u) + dz)
    us = np.linspace(0, 1, K + 1)
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]; rm = 0.5 * (Rr(ba, 0.5) + Rr(bb, 0.5)); bm = math.radians(0.5 * (ba + bb))
        rad = np.array([math.sin(bm), math.cos(bm), 0.0]); ua_, ub_ = math.radians(ba) * rm / 6, math.radians(bb) * rm / 6
        for k in range(K):
            u0, u1 = us[k], us[k + 1]
            q = [P(ba, u0), P(bb, u0), P(bb, u1), P(ba, u1)]; uv = [(ua_, u0 * 4), (ub_, u0 * 4), (ub_, u1 * 4), (ua_, u1 * 4)]
            B.oriented(mr, q, S['mats']['roof'], up, uv)
            B.oriented(mr, [P(ba, u0, -th), P(bb, u0, -th), P(bb, u1, -th), P(ba, u1, -th)], 'roof_under', -up, uv)
        # front edge: a dark grey fascia 0.9 m deep, set on the curl; back edge: a 0.6 m rim
        B.oriented(mr, [P(ba, 0, -0.9), P(bb, 0, -0.9), P(bb, 0, 0.05), P(ba, 0, 0.05)], 'fascia_dark', -rad)
        B.oriented(mr, [P(ba, 1, -0.6), P(bb, 1, -0.6), P(bb, 1, 0.05), P(ba, 1, 0.05)], 'steel_galv', rad)
        B.oriented(mr, [P(ba, 1, -0.6), P(bb, 1, -0.6), P(bb, 1, -th), P(ba, 1, -th)], 'steel_galv', -up)
        B.oriented(mr, [P(ba, 0, -0.9), P(bb, 0, -0.9), P(bb, 0.02, -th), P(ba, 0.02, -th)], 'fascia_dark', -up)
    for b, sg in ((b0, -1), (b1, 1)):   # end edges
        a = math.radians(b); tan = np.array([math.cos(a), -math.sin(a), 0.0]) * sg
        for k in range(K):
            B.oriented(mr, [P(b, us[k], -th), P(b, us[k + 1], -th), P(b, us[k + 1], 0.05), P(b, us[k], 0.05)], 'fascia_dark', tan)
    # underside framing: a galvanised radial beam every bay, a glulam rafter mid-bay, purlins every 2.2 m
    bay = S['bay']; b = b0 + math.degrees(0.5 * bay / Rr(b0, 0.5)); beams = []
    while b < b1 - 0.2:
        beams.append(b); b += math.degrees(bay / Rr(b, 0.5))
    def under(b, u, d): return np.array(P(b, u, -th - d))
    for j, b in enumerate(beams):
        pts = [under(b, u, 0.45) for u in np.linspace(0.03, 0.97, 9)]
        for p, q in zip(pts[:-1], pts[1:]): mr.beam(p, q, 0.35, 0.9, 'steel_galv')
        if j + 1 < len(beams):   # glulam rafter on the diagonal of the bay, as in the photos
            bn = beams[j + 1]; pts = [under(b + (bn - b) * u, 0.15 + 0.7 * u, 0.4) for u in np.linspace(0, 1, 6)]
            for p, q in zip(pts[:-1], pts[1:]): mr.beam(p, q, 0.3, 0.75, 'timber')
    nu = int(np.mean([Rr(b0, 1) - Rr(b0, 0), Rr(b1, 1) - Rr(b1, 0), Rr((b0 + b1) / 2, 1) - Rr((b0 + b1) / 2, 0)]) / 2.2)
    for u in np.linspace(0.05, 0.95, max(4, nu)):
        bb_ = np.linspace(b0 + 0.3, b1 - 0.3, 40); pts = [under(b, u, 0.15) for b in bb_]
        for p, q in zip(pts[:-1], pts[1:]): mr.beam(p, q, 0.12, 0.2, 'steel_galv')
    # handrail round the back edge: posts every 2 m, a top and a mid rail
    bb_ = []; b = b0 + 0.2
    while b < b1 - 0.1:
        bb_.append(b); b += math.degrees(2.0 / Rr(b, 0.97))
    top = [np.array(P(b, 0.97, 1.1)) for b in bb_]; mid = [np.array(P(b, 0.97, 0.55)) for b in bb_]
    for b, t in zip(bb_, top): tube(mr, P(b, 0.97, 0.0), t, 0.03, 'steel_galv', n=6)
    for L in (top, mid):
        for p, q in zip(L[:-1], L[1:]): tube(mr, p, q, 0.025, 'steel_galv', n=6)
    # the V columns: one base pad every second bay, 4 m inside the roof's back edge; two raking arms to the back edge half
    # a bay either side, each faced with a glulam strip on its outer side
    for j in range(1, len(beams), 3):
        b = beams[j]; rf, ri, ro, rs0, rb = geo(b); base = np.array(B.P3(b, rb - S['wall_in'] + 1.2, 0.0))
        mr.box((base[0], base[1]), 1.2, 1.2, 0.5, math.degrees(math.atan2(base[1], base[0])), 'conc_wall')
        for sg in (-1, 1):
            bt = b + sg * math.degrees(0.8 * bay / Rr(b, 1))
            if not (b0 <= bt <= b1): continue
            tp = np.array(P(bt, 0.97, -th - 0.3)); p0 = base + up * 0.5
            tube(mr, p0, tp, 0.32, 'steel_galv', n=12)
            d = tp - p0; d /= np.linalg.norm(d); o = np.array([base[0], base[1], 0.0]); o /= np.linalg.norm(o)
            o = o - d * np.dot(o, d); o /= np.linalg.norm(o)
            mr.beam(p0 + o * 0.36 + d * 1.5, tp + o * 0.36 - d * 1.0, 0.3, 0.1, 'timber')


def core(mb, b, geo, S, sg, m):
    """lift and stair core beside the stand's end: a 7 x 6 m box to 2.5 m over the upper tier (precast, or brick for the
    one between the two stands)"""
    rf, ri, ro, rs0, rb = geo(b); r = rb - 4.0; a = math.radians(b); rad = np.array([math.sin(a), math.cos(a)])
    tan = np.array([math.cos(a), -math.sin(a)]) * sg; c = rad * r + tan * 4.0
    H = S['z_upper'][1] + 2.5 if m != 'brick_core' else 8.2   # al_2026: the brick building between is two storeys
    ang = math.degrees(math.atan2(rad[1], rad[0]))
    mb.box(tuple(c), 7.0, 6.0, H, ang, m, mtop='conc_wall')
    mb.box(tuple(c), 7.3, 6.3, 0.5, ang, 'conc_wall', z0=H)   # capping slab, proud all round
