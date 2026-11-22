# Blacktown's own pieces the ground kit has no kind for (kit/build.py calls build(kit, col) when blacktown.json names
# this file in "custom"). Plan positions in the model's metres (x east, y north, origin = the kit origin), heights above
# the field. Sources: Google Earth 3D mesh (straight-down shots and status-bar heights, whole metres) and close Google
# Earth obliques of the stand's back and roof (2026-11-22), the NSW 7.5 cm aerial for ground lines.
import math
import numpy as np

Z_GALLERY = 5.4       # top seat row and the gallery floor behind it (seat rows estimated from the 1,600 seats)
COL_STEP = 8.2        # back columns: 8 bays over the 66 m of the north half's back (Google Earth oblique)
MAST_STEP = 8.2       # roof masts along the spine (6 masts 8.1 m apart over the north 40 m, Google Earth top view)
MAST_FRAC = 0.42      # the spine: 42% of the roof's depth back from its front edge
MAST_H = 5.0          # mast tops read 16 m on Google Earth's status bar, the deck 11 m
LIGHT_STEP = 10.4     # twin floodlights under the roof's front edge (Google Earth oblique)
# the lower wing behind the south half of the stand: 8 m out from the roof's back edge, flat roof (Google Earth top view)
WING_B = (230.5, 255.5); WING_OUT = 8.0; WING_H = 8.0
# the indoor centre west of the stand: roof corners from the Google Earth top view (whole building turned about 6.5 deg)
IC_ROOF = [(-147.6, -19.6), (-122.5, -21.4), (-117.0, 31.9), (-140.9, 33.7)]
# heights from Google Earth's status bar on a 3 m grid (whole metres above the turf): the roof reads 6 m over its west two
# thirds and 7 m over the east third (a mono-pitch from 5.6 to 6.8 m fits every reading), the monitors 8 m, and a strip
# at each end reads 3 m (a lower annexe 5 m deep at the north end, 3.5 m at the south). The ground is 1 m below the turf.
# the raised walkway along the wing's outer face: Google Earth reads 2-3 m at its south end and 3-4 m at its north end,
# 2.5-7 m out from the wing; the obliques show solid parapet walls and a stair down to the ground at the south end
WALK_B = (235.0, 255.5); WALK_R = (2.5, 7.0); WALK_Z = (2.5, 3.5)
# concrete stairs straight up the bank from the fence to the path on top (Google Earth top view, 2025-07-24)
BANK_STAIRS = (100.0, 154.0); STAIR_W = 2.4
IC_W = 25.0; IC_ZW, IC_ZE = 5.6, 6.8; IC_OVER = 0.6; IC_PLINTH = 0.8; IC_BASE = -1.0
IC_ENDS = (2.5, 3.5, 3.3)              # south strip depth, north strip depth, their height
IC_EXT_S = 1.0                          # the south strip reaches 1 m past the roof corners seen from above (3 m readings)
IC_MON = (12.4, 8.0, 5, 12.5, 3.5, 8.0)   # roof monitors: first centre from the south roof edge, spacing, count, length, depth, top


def build(k, col):
    S = next(s for s in k.D['stands'] if s['name'] == 'grandstand')
    mb = k.MB('detail'); up = np.array([0, 0, 1.0])
    zr0, zr1 = S['z_roof']; bs = k.brange(S)

    def geo(b):
        rf = k.fence_r(b % 360); ri, ro = k.interp(S['roof'], b); rs0 = rf + S['seat_front']; rb = ro - S['back_in']
        return rf, ri, ro, rs0 + S['seat_depth'], rb

    def rad(b): a = math.radians(b); return np.array([math.sin(a), math.cos(a), 0.0])

    # gallery floor behind the top row, its slab edge and parapet on the back line, the recessed ground-floor wall
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]; (_, _, _, la, ra), (_, _, _, lb, rbb) = geo(ba), geo(bb); bm = 0.5 * (ba + bb)
        k.oriented(mb, [k.P3(ba, la, Z_GALLERY), k.P3(bb, lb, Z_GALLERY), k.P3(bb, rbb, Z_GALLERY), k.P3(ba, ra, Z_GALLERY)], 'paving', up)
        k.oriented(mb, [k.P3(ba, ra, Z_GALLERY - 0.6), k.P3(bb, rbb, Z_GALLERY - 0.6), k.P3(bb, rbb - 2.5, Z_GALLERY - 0.6),
                        k.P3(ba, ra - 2.5, Z_GALLERY - 0.6)], 'render_bt', -up)                     # soffit of the overhang
        for r0, r1, z0, z1, sg in ((ra, rbb, Z_GALLERY - 0.6, Z_GALLERY + 1.0, 1),                    # slab edge + parapet, outside
                                   (ra - 0.2, rbb - 0.2, Z_GALLERY, Z_GALLERY + 1.0, -1),             # parapet, inside
                                   (ra - 2.5, rbb - 2.5, 0.0, Z_GALLERY - 0.6, 1)):                   # ground-floor wall
            k.oriented(mb, [k.P3(ba, r0, z0), k.P3(bb, r1, z0), k.P3(bb, r1, z1), k.P3(ba, r0, z1)], 'render_bt', sg * rad(bm))
        k.oriented(mb, [k.P3(ba, ra - 0.2, Z_GALLERY + 1.0), k.P3(bb, rbb - 0.2, Z_GALLERY + 1.0), k.P3(bb, rbb, Z_GALLERY + 1.0),
                        k.P3(ba, ra, Z_GALLERY + 1.0)], 'render_bt', up)
    # columns on the back line from the ground to the roof soffit, one every COL_STEP along the back
    def along(step, rfun, first):
        out = []; b = bs[0]; L = first
        while True:
            r = rfun(b); b2 = b + math.degrees(L / r)
            if b2 > bs[-1] - math.degrees(1.0 / r): break
            out.append(b2); b = b2; L = step
        return out
    for b in along(COL_STEP, lambda b: geo(b)[4], 2.0):
        c = k.pol(b, geo(b)[4] - 0.3); mb.box(c, 0.6, 0.6, zr0 - 0.5, 90 - b, 'render_bt')
    # roof masts: a steel post on the spine with a stay back and a stay forward to the deck
    deck = lambda b, f: (geo(b)[1] + f * (geo(b)[2] - geo(b)[1]), zr0 + f * (zr1 - zr0))
    for b in along(MAST_STEP, lambda b: deck(b, MAST_FRAC)[0], 3.0):
        r, z = deck(b, MAST_FRAC); top = k.P3(b, r, z + MAST_H)
        mb.beam(k.P3(b, r, z), top, 0.25, 0.25, 'steel_white')
        for f in (0.80, 0.15):
            rr, zz = deck(b, f); mb.beam(top, k.P3(b, rr, zz + 0.1), 0.08, 0.08, 'steel_white')
    # twin floodlights on brackets under the roof's front edge
    for b in along(LIGHT_STEP, lambda b: geo(b)[1], 5.0):
        r = geo(b)[1] + 0.6; t = np.array(k.pol(b + 90, 1.0))
        for s in (-0.35, 0.35):
            c = np.array(k.pol(b, r)) + t * s; mb.cyl(tuple(c), 0.22, zr0 - 1.05, zr0 - 0.55, 'lamps', n=12)
        mb.beam(k.P3(b, r - 0.3, zr0 - 0.5), k.P3(b, r + 0.3, zr0 - 0.5), 0.9, 0.12, 'steel_galv')
    wing(k, mb, S, geo, rad, up)
    walkway(k, mb, geo, rad, up)
    for b in BANK_STAIRS: bank_stair(k, mb, b)
    indoor(k, mb, up)
    mb.build(col)


def wing(k, mb, S, geo, rad, up):
    """two-storey wing on the back of the south half: walls from the stand's back line out to 8 m past the roof edge"""
    b0, b1 = WING_B; bs = [b0 + (b1 - b0) * i / 12 for i in range(13)]
    ri = lambda b: geo(b)[4] - 2.5; ro = lambda b: geo(b)[2] + WING_OUT
    for i in range(12):
        ba, bb = bs[i], bs[i + 1]; bm = 0.5 * (ba + bb)
        k.oriented(mb, [k.P3(ba, ro(ba), 0), k.P3(bb, ro(bb), 0), k.P3(bb, ro(bb), WING_H), k.P3(ba, ro(ba), WING_H)], 'render_bt', rad(bm))
        k.oriented(mb, [k.P3(ba, ri(ba), WING_H), k.P3(bb, ri(bb), WING_H), k.P3(bb, ro(bb), WING_H), k.P3(ba, ro(ba), WING_H)], 'roof_bt', up)
        # parapet 0.6 m round the roof's outer edge
        k.oriented(mb, [k.P3(ba, ro(ba) - 0.2, WING_H), k.P3(bb, ro(bb) - 0.2, WING_H), k.P3(bb, ro(bb) - 0.2, WING_H + 0.6),
                        k.P3(ba, ro(ba) - 0.2, WING_H + 0.6)], 'render_bt', -rad(bm))
        k.oriented(mb, [k.P3(ba, ro(ba), WING_H), k.P3(bb, ro(bb), WING_H), k.P3(bb, ro(bb), WING_H + 0.6), k.P3(ba, ro(ba), WING_H + 0.6)], 'render_bt', rad(bm))
        k.oriented(mb, [k.P3(ba, ro(ba) - 0.2, WING_H + 0.6), k.P3(bb, ro(bb) - 0.2, WING_H + 0.6), k.P3(bb, ro(bb), WING_H + 0.6),
                        k.P3(ba, ro(ba), WING_H + 0.6)], 'render_bt', up)
    for b, sg in ((b0, -1), (b1, 1)):   # the two ends
        t = np.array(k.pol(b + 90, 1.0)); n = np.array([*(t * sg), 0.0])
        k.oriented(mb, [k.P3(b, ri(b), 0), k.P3(b, ro(b), 0), k.P3(b, ro(b), WING_H + 0.6), k.P3(b, ri(b), WING_H + 0.6)], 'render_bt', n)
    # the sign on the outer face near the south end, 0.15 m proud in a frame
    bsg = b0 + math.degrees(8.0 / ro(b0)); r = ro(bsg) + 0.15; t = np.array(k.pol(bsg + 90, 1.0)); c = np.array(k.pol(bsg, r))
    for z0, z1, w, m, dr in ((1.9, 4.9, 9.4, 'board_back', 0.0), (2.05, 4.75, 9.1, 'screen_off', 0.05)):
        a, b_ = c - t * w / 2 + np.array(k.pol(bsg, dr)), c + t * w / 2 + np.array(k.pol(bsg, dr))
        k.oriented(mb, [(*a, z0), (*b_, z0), (*b_, z1), (*a, z1)], m, rad(bsg))


def walkway(k, mb, geo, rad, up):
    b0, b1 = WALK_B; n = 16; bs = [b0 + (b1 - b0) * i / n for i in range(n + 1)]
    base = lambda b: geo(b)[2] + WING_OUT; z = lambda b: WALK_Z[0] + (WALK_Z[1] - WALK_Z[0]) * (b - b0) / (b1 - b0)
    ri = lambda b: base(b) + WALK_R[0]; ro = lambda b: base(b) + WALK_R[1]
    for i in range(n):
        ba, bb = bs[i], bs[i + 1]; bm = 0.5 * (ba + bb); za, zb = z(ba), z(bb)
        k.oriented(mb, [k.P3(ba, ri(ba), za), k.P3(bb, ri(bb), zb), k.P3(bb, ro(bb), zb), k.P3(ba, ro(ba), za)], 'paving', up)
        for rr, sg, h in ((ro, 1, 1.1), (ri, -1, 1.1)):   # solid wall from the ground up to the parapet's top, each side
            k.oriented(mb, [k.P3(ba, rr(ba), 0.0), k.P3(bb, rr(bb), 0.0), k.P3(bb, rr(bb), zb + h), k.P3(ba, rr(ba), za + h)], 'conc_wall', sg * rad(bm))
            d = -0.2 * sg
            k.oriented(mb, [k.P3(ba, rr(ba) + d, za), k.P3(bb, rr(bb) + d, zb), k.P3(bb, rr(bb) + d, zb + h), k.P3(ba, rr(ba) + d, za + h)], 'conc_wall', -sg * rad(bm))
            k.oriented(mb, [k.P3(ba, rr(ba) + d, za + h), k.P3(bb, rr(bb) + d, zb + h), k.P3(bb, rr(bb), zb + h), k.P3(ba, rr(ba), za + h)], 'conc_wall', up)
    # north end wall; at the south end a straight stair down to the ground, 0.3 m treads, 0.17 m risers
    t1 = np.array(k.pol(b1 + 90, 1.0))
    k.oriented(mb, [k.P3(b1, ri(b1), 0), k.P3(b1, ro(b1), 0), k.P3(b1, ro(b1), z(b1) + 1.1), k.P3(b1, ri(b1), z(b1) + 1.1)], 'conc_wall', np.array([*t1, 0.0]))
    t = -np.array(k.pol(b0 + 90, 1.0)); A = np.array(k.pol(b0, ri(b0) + 0.2)); B = np.array(k.pol(b0, ro(b0) - 0.2)); z0 = z(b0)
    ns = int(round(z0 / 0.17)); w = np.linalg.norm(B - A); c = (A + B) / 2; ang = math.degrees(math.atan2(t[1], t[0]))
    for j in range(ns):
        zz = z0 - (j + 1) * z0 / ns; mb.box(tuple(c + t * (0.3 * j + 0.15)), 0.3, w, zz + z0 / ns, ang, 'conc_tread', mtop='conc_tread')
    nn = np.array([t[1], -t[0], 0.0])
    for e in (A, B):   # stair side walls, seen from both sides
        q0, q1 = e, e + t * 0.3 * ns
        for sg in (1, -1): k.oriented(mb, [(*q0, 0), (*q1, 0), (*q1, 1.0), (*q0, z0 + 1.1)], 'conc_wall', sg * nn)


def bank_stair(k, mb, b):
    """a flight of 0.5 m treads up the bank's measured slope, kerbs each side, a steel handrail down the middle"""
    fr = k.fence_r(b); r0, r1 = fr + 1.0, fr + 16.0; n = int((r1 - r0) / 0.5); u = np.array(k.pol(b, 1.0)); t = np.array(k.pol(b + 90, 1.0))
    ang = math.degrees(math.atan2(u[1], u[0])); zs = [k.terrain_z(b, r0 + (r1 - r0) * j / n) for j in range(n + 1)]
    for j in range(n):
        r = r0 + (r1 - r0) * (j + 0.5) / n; c = np.array(k.pol(b, r)); zt = max(zs[j], zs[j + 1]) + 0.05
        mb.box(tuple(c), (r1 - r0) / n, STAIR_W, zt - min(zs[j], zs[j + 1]) + 0.25, ang, 'conc_tread', z0=min(zs[j], zs[j + 1]) - 0.25, mtop='conc_tread')
        for sg in (-1, 1):
            mb.box(tuple(c + t * sg * (STAIR_W / 2 + 0.1)), (r1 - r0) / n, 0.2, zt + 0.2 - min(zs[j], zs[j + 1]) + 0.25, ang, 'conc_wall', z0=min(zs[j], zs[j + 1]) - 0.25)
    for j in range(0, n, 6):   # handrail posts, then the rail along their tops
        mb.box(tuple(k.pol(b, r0 + (r1 - r0) * j / n)), 0.06, 0.06, 0.95, ang, 'steel_galv', z0=zs[j])
    mb.beam(k.P3(b, r0, zs[0] + 0.95), k.P3(b, r1, zs[-1] + 0.95), 0.05, 0.05, 'steel_galv')


def indoor(k, mb, up):
    """the indoor centre: a rectangle fitted to the roof corners seen from above, a mono-pitch roof rising to the east,
    rendered plinth and panels with a recessed glazed band under the eave on the west, a glazed east wall, modelled fins,
    five raised monitors (a dark louvred band under an overhanging cap), and the low strips at both ends"""
    R = np.array(IC_ROOF, float); c = R.mean(0); ax = (R[2] + R[3]) / 2 - (R[0] + R[1]) / 2; L = np.linalg.norm(ax); ax /= L
    cr = np.array([ax[1], -ax[0]])                       # across the building, pointing east
    O = c - ax * (L / 2 + IC_EXT_S) - cr * IC_W / 2; L += IC_EXT_S
    def P(u, v, z): q = O + ax * u + cr * v; return (float(q[0]), float(q[1]), z)
    def zr(v): return IC_ZW + (IC_ZE - IC_ZW) * v / IC_W   # roof top surface
    n3 = lambda d: np.array([*d, 0.0])
    def quad(a, b, m, nrm, z0a, z1a, z0b, z1b):            # wall from plan point a to b, bottom/top heights at each end
        k.oriented(mb, [(*a, z0a), (*b, z0b), (*b, z1b), (*a, z1a)], m, nrm)
    ds, dn, ze = IC_ENDS; u0, u1 = ds, L - dn; o = IC_OVER
    # the main hall's walls, inset o under the eaves
    pa = lambda u, v: (O + ax * u + cr * v)
    SW, SE, NE, NW = pa(u0, o), pa(u0, IC_W - o), pa(u1, IC_W - o), pa(u1, o)
    zg = IC_PLINTH + 0.55 * (zr(o) - IC_PLINTH)
    # west: plinth, panels, a glazed band 0.3 m back with fins
    quad(SW, NW, 'conc_wall', n3(-cr), IC_BASE, IC_PLINTH, IC_BASE, IC_PLINTH)
    quad(SW, NW, 'render_bt', n3(-cr), IC_PLINTH, zg, IC_PLINTH, zg)
    quad(SW + cr * 0.3, NW + cr * 0.3, 'glass_bt', n3(-cr), zg, zr(o), zg, zr(o))
    k.oriented(mb, [(*SW, zg), (*NW, zg), (*(NW + cr * 0.3), zg), (*(SW + cr * 0.3), zg)], 'render_bt', up)
    # east: glazed from the plinth to the eave, behind fins
    quad(NE, SE, 'conc_wall', n3(cr), IC_BASE, IC_PLINTH, IC_BASE, IC_PLINTH)
    quad(NE, SE, 'glass_bt', n3(cr), IC_PLINTH, zr(IC_W - o), IC_PLINTH, zr(IC_W - o))
    # the two ends (their top follows the roof's pitch)
    quad(SE, SW, 'render_bt', n3(-ax), IC_BASE, zr(IC_W - o), IC_BASE, zr(o))
    quad(NW, NE, 'render_bt', n3(ax), IC_BASE, zr(o), IC_BASE, zr(IC_W - o))
    ang = math.degrees(math.atan2(ax[1], ax[0]))
    for a, z0, z1, side in ((SW + cr * 0.3, zg, zr(o), -1), (SE, IC_PLINTH, zr(IC_W - o), 1)):   # fins 2.4 m apart
        n = int((u1 - u0) / 2.4)
        for j in range(1, n):
            f = a + ax * (u1 - u0) * j / n + cr * side * 0.2 * (1 if side > 0 else 0)
            mb.box(tuple(f + cr * side * 0.15), 0.12, 0.55, z1 - z0, ang, 'render_bt', z0=z0)
    # the roof: 0.5 m deep fascia all round, the top on the pitch
    C4 = [(0, 0), (L, 0), (L, IC_W), (0, IC_W)]
    k.oriented(mb, [P(u0, 0, zr(0)), P(u1, 0, zr(0)), P(u1, IC_W, zr(IC_W)), P(u0, IC_W, zr(IC_W))], 'roof_bt', up)
    k.oriented(mb, [P(u0, 0, zr(0) - 0.5), P(u0, IC_W, zr(IC_W) - 0.5), P(u1, IC_W, zr(IC_W) - 0.5), P(u1, 0, zr(0) - 0.5)], 'roof_soffit', -up)
    quad(pa(u0, 0), pa(u1, 0), 'fascia', n3(-cr), zr(0) - 0.5, zr(0), zr(0) - 0.5, zr(0))
    quad(pa(u1, IC_W), pa(u0, IC_W), 'fascia', n3(cr), zr(IC_W) - 0.5, zr(IC_W), zr(IC_W) - 0.5, zr(IC_W))
    quad(pa(u0, IC_W), pa(u0, 0), 'fascia', n3(-ax), zr(IC_W) - 0.5, zr(IC_W), zr(0) - 0.5, zr(0))
    quad(pa(u1, 0), pa(u1, IC_W), 'fascia', n3(ax), zr(0) - 0.5, zr(0), zr(IC_W) - 0.5, zr(IC_W))
    # the low strips at each end: rendered walls, a flat roof
    for ua, ub in ((0.0, u0), (u1, L)):
        poly = [tuple(pa(ua, 0.3)), tuple(pa(ub, 0.3)), tuple(pa(ub, IC_W - 0.3)), tuple(pa(ua, IC_W - 0.3))]
        mb.prism(poly, IC_BASE, ze - 0.4, 'render_bt')
        mb.prism([tuple(pa(ua, 0)), tuple(pa(ub, 0)), tuple(pa(ub, IC_W)), tuple(pa(ua, IC_W))], ze - 0.4, ze, 'fascia', top='roof_bt', bot='roof_soffit')
    # monitors across the roof
    m0, dm, nm, ml, md, mt = IC_MON; angc = math.degrees(math.atan2(cr[1], cr[0]))
    for j in range(nm):
        m = pa(m0 + j * dm, IC_W / 2 + 0.3); zb = zr(IC_W / 2) - 0.6; zc = mt - 0.4
        mb.box(tuple(m), ml - 0.4, md - 0.4, zc - zb, angc, 'glass_bt', z0=zb)
        for s_ in np.linspace(-1, 1, 9)[1:-1]:   # mullions in the louvred band
            mb.box(tuple(m + cr * s_ * (ml - 0.4) / 2), 0.08, md - 0.3, zc - zb, angc, 'render_bt', z0=zb)
        mb.box(tuple(m), ml, md, 0.4, angc, 'render_bt', z0=zc, mtop='roof_bt')
