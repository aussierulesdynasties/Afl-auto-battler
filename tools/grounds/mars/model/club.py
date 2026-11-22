"""North Ballarat Sports Club and the clubroom wall behind the north stand's concourse.

Footprint: OSM way 128280661 (ODbL, tools/grounds/mars/osm/near.json); entrance canopy OSM way 1271589372.
Look: GE 3D (n180, Dec 2025), Commons "Mars Stadium North Ballarat Social Club and Eureka" (2022) and
"Eureka Stadium September 2026" (CC0). Every window is a recess: a glass plane with the solid wall built in front of it
(piers, sills, spandrels), so nothing is painted on.
"""
import math, json, os, sys
import numpy as np
import build as B

HERE = os.path.dirname(os.path.abspath(__file__))
up = np.array([0, 0, 1.0])


def _osm(wid):
    sys.path.insert(0, os.path.join(HERE, '..', 'work'))
    from geo import ll2xy
    for w in json.load(open(os.path.join(HERE, '..', 'osm', 'near.json')))['ways']:
        if w['id'] == wid:
            P = [tuple(ll2xy(a, b)) for a, b in w['ll']]
            return P[:-1] if P[0] == P[-1] else P


def slab(mb, p, q, z0, z1, d0, d1, m):
    """a solid block along the wall line p->q (outward normal on the right), from d0 to d1 m proud of it"""
    p, q = np.array(p, float), np.array(q, float); t = q - p; L = np.linalg.norm(t); t /= L; n = np.array([t[1], -t[0]])
    a0, a1, b0, b1 = p + n * d0, p + n * d1, q + n * d0, q + n * d1
    P = lambda v, z: (v[0], v[1], z)
    n3 = np.array([n[0], n[1], 0.0]); t3 = np.array([t[0], t[1], 0.0])
    tu, tv = B.TILE.get(m, (4.8, 2.4)); u0 = (p[0] * t[0] + p[1] * t[1]) / tu   # world-scaled UVs, continuous along a wall line
    B.oriented(mb, [P(a1, z0), P(b1, z0), P(b1, z1), P(a1, z1)], m, n3,
               uv=[(u0, z0 / tv), (u0 + L / tu, z0 / tv), (u0 + L / tu, z1 / tv), (u0, z1 / tv)])
    B.oriented(mb, [P(a0, z1), P(b0, z1), P(b1, z1), P(a1, z1)], m, up)
    B.oriented(mb, [P(a0, z0), P(b0, z0), P(b1, z0), P(a1, z0)], m, -up)
    B.oriented(mb, [P(a0, z0), P(a1, z0), P(a1, z1), P(a0, z1)], m, -t3)
    B.oriented(mb, [P(b0, z0), P(b1, z0), P(b1, z1), P(b0, z1)], m, t3)


def punched(mb, p, q, H, mat, wins, ww=1.6, pitch=3.6):
    """sandstone wall 0.3 m proud of a recessed glass plane, cut by window rows wins = [(sill, head)...]"""
    p, q = np.array(p, float), np.array(q, float); L = np.linalg.norm(q - p)
    if L < 2.0:
        slab(mb, p, q, 0.0, H, 0.0, 0.3, mat); return
    nw = max(1, int((L - 1.2) // pitch)); s0 = (L - nw * pitch) / 2 + (pitch - ww) / 2
    lerp = lambda s: p + (q - p) * (s / L)
    zs = [0.0]
    for a, b in wins: zs += [a, b]
    zs.append(H)
    for k in range(0, len(zs) - 1, 2):   # solid bands between window rows
        slab(mb, p, q, zs[k], zs[k + 1], 0.0, 0.3, mat)
    for a, b in wins:                    # piers between the windows of each row, and the sill ledge
        cuts = [0.0] + [x for i in range(nw) for x in (s0 + i * pitch, s0 + i * pitch + ww)] + [L]
        for i in range(0, len(cuts) - 1, 2):
            if cuts[i + 1] - cuts[i] > 0.01: slab(mb, lerp(cuts[i]), lerp(cuts[i + 1]), a, b, 0.0, 0.3, mat)
        for i in range(nw):
            s = s0 + i * pitch; slab(mb, lerp(s - 0.05), lerp(s + ww + 0.05), a - 0.08, a, 0.0, 0.38, 'paint_white')
    mb.wall(tuple(p), tuple(q), 0.0, H, 'glass_dark')


def curtain(mb, mr, p, q, H, z_floor=4.2):
    """the glazed wing: glass plane, aluminium mullions every 1.5 m, a white floor-edge band and roof fascia proud"""
    p, q = np.array(p, float), np.array(q, float); L = np.linalg.norm(q - p); n = int(L // 1.5)
    mb.wall(tuple(p), tuple(q), 0.0, H, 'glass_dark')
    for i in range(n + 1):
        a = p + (q - p) * (i / max(1, n)); b = p + (q - p) * min(1.0, (i / max(1, n)) + 0.06 / L)
        slab(mr, a, b, 0.0, H, 0.0, 0.15, 'steel_galv')
    slab(mb, p, q, z_floor, z_floor + 0.8, 0.0, 0.5, 'paint_white')
    slab(mb, p, q, H - 0.9, H + 0.4, 0.0, 0.4, 'paint_white')
    slab(mr, p, q, 2.9, 3.0, 0.0, 0.12, 'steel_galv')          # ground-floor transom
    slab(mr, p, q, z_floor + 2.6, z_floor + 2.7, 0.0, 0.12, 'steel_galv')


def nbsc(col, D):
    """the club: OSM footprint, 2 storeys (z 8.6, parapet to 9.0); sandstone curve to the car park, glazed west wing"""
    mb = B.MB('club'); mr = B.MB('club_frame')
    P = _ccw(_behind_stand(_osm(128280661)))
    H = D.get('z', 8.6)
    for i in range(len(P)):
        p, q = P[i], P[(i + 1) % len(P)]; m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        if m[1] > 96 and m[0] > -3 or m[0] > 30:     # the curved sandstone front and the east end
            punched(mb, p, q, H, 'sandstone', [(1.0, 2.9), (5.0, 6.9)])
        elif m[1] > 100:                               # the glazed west wing on the car park
            curtain(mb, mr, p, q, H)
        else:                                          # sides and the face under the stand roof: rendered blockwork
            slab(mb, p, q, 0.0, H, 0.0, 0.05, 'conc_block')
    mb.cap(P, H, D.get('roof', 'roof_flat'))
    # parapet upstand round the roof edge
    for i in range(len(P)):
        p, q = np.array(P[i], float), np.array(P[(i + 1) % len(P)], float)
        _parapet(mb, p, q, H)
    for c, L_, W, h, a in D.get('plant', []):
        mb.box(tuple(c), L_, W, h, a, 'paint_white', z0=H)
    # entrance canopy (OSM 1271589372): a 0.4 m slab at 4.6 m on two round columns
    C = _ccw(_osm(1271589372)); mb.prism(C, 4.6, 5.0, 'paint_white', top='roof_white', bot='roof_soffit')
    cx = np.mean([c[0] for c in C]); cy = np.mean([c[1] for c in C])
    far = max(C, key=lambda c: c[1])
    for f in (0.35, 0.75):
        x, y = cx + (far[0] - cx) * f, cy + (far[1] - cy) * f
        mr.cyl((x, y), 0.2, 0.0, 4.6, 'steel_white', n=16)
    mb.build(col); mr.build(col)


def _behind_stand(P):
    """OSM draws the club's front edge under the north stand's roof; the clubroom wall there is the stand's back wall
    (club_front), so the building starts just behind it"""
    S = [s for s in B.D['stands'] if s.get('club')][0]; out = []
    for x, y in P:
        b = math.degrees(math.atan2(x, y)) % 360; r = math.hypot(x, y); bb = b if b >= S['b0'] else b + 360
        if S['b0'] <= bb <= S['b1']:
            r = max(r, B.fence_r(b) + S['back_rel'] + 0.3)
        out.append(B.pol(b, r))
    return out


def _parapet(mb, p, q, H):
    """0.6 m upstand on the roof edge, 0.25 m thick, inside the wall line"""
    t = q - p; L = np.linalg.norm(t)
    if L < 1e-6: return
    slab(mb, p, q, H, H + 0.6, -0.25, 0.3, 'paint_white')


def _ccw(P):
    s = sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1] for i in range(len(P)))
    return list(P) if s > 0 else list(P)[::-1]


def club_front(S, bs, geo, mb, mr, zs1, zb_of):
    """the clubroom wall at the back of the north concourse (2022 photo): face-brick piers every 6 m, full-height glazing
    between them (doors and windows, 3.0 m) behind aluminium mullions, a brick spandrel over to the roof soffit"""
    W = S.get('pier', 6.0); b = bs[0]
    while b < bs[-1] - 0.1:
        rb = geo(b)[4] - 0.4; b2 = min(bs[-1], b + math.degrees(W / rb)); rb2 = geo(b2)[4] - 0.4
        p, q = B.pol(b, rb), B.pol(b2, rb2)            # clockwise along the wall: the right-hand normal faces the pitch
        zt = min(zb_of(b), zb_of(b2))
        L = W; f = 0.9 / max(L, 1.0)
        pa = np.array(p); qa = np.array(q)
        slab(mb, pa, pa + (qa - pa) * f, zs1, zt, 0.0, 0.35, 'brick_core')                       # pier
        slab(mb, pa + (qa - pa) * f, qa, zs1 + 3.0, zt, 0.0, 0.2, 'brick_core')                  # spandrel
        n = 4
        for k in range(n + 1):                                                                     # mullions
            s = f + (1 - f) * k / n; a = pa + (qa - pa) * s; c = pa + (qa - pa) * min(1.0, s + 0.08 / L)
            slab(mr, a, c, zs1, zs1 + 3.0, 0.0, 0.12, 'steel_galv')
        slab(mr, pa + (qa - pa) * f, qa, zs1 + 2.2, zs1 + 2.28, 0.0, 0.12, 'steel_galv')         # door-head transom
        b = b2
