"""The Sir Edwin Smith Stand (1914 heritage grandstand, the southern end): a bent three-segment stand under a
red hipped roof with Dutch-gable ends, three timber front gables and two louvred cupolas, an open front on
cream timber posts, a brick podium with balustrade and stairs, and a two-storey brick back with pilasters,
cream bands and real window openings.

Plan from Google Earth's top-down mosaic (front eave corners, the cupola) corrected for lean; heights and
details from the January 2026 Commons photos (19: the back; AFLW 2025 01: the front)."""
import math
import numpy as np
from nwlib import (V, add, quad, prism, box3, cyl, tube, wall, band, offset_poly, along, length, unit, perp, obox)

P = "ses"

def lean(p, h, c):
    """A point read off Google Earth's top-down tile centred on c, at height h, moved to where it stands."""
    p, c = np.asarray(p, float), np.asarray(c, float)
    return c + (p - c) * (1 - h / 260.0)

TILE_W = (-75.8, -84.8)
TILE_C = (4.2, -84.8)
ZE = 9.0              # eave (front and back)
PITCH = math.radians(27.0)
D = 16.4              # eave to eave, front to back
FE = [lean((-48.5, -72.5), ZE, TILE_W), lean((-36.0, -85.0), ZE, TILE_W), lean((-11.5, -98.2), ZE, TILE_C), lean((13.0, -99.0), ZE, TILE_C)]
ZR = ZE + D / 2 * math.tan(PITCH)
OVER = 0.9            # eave overhang past the back wall
DECK = 1.9            # the seating deck's front edge above the concourse
NROW = 14
TREAD, RISE = 0.84, 0.37
D_ROW0 = 1.7          # first row's riser behind the front eave
D_BACKIN = D_ROW0 + NROW * TREAD + 0.3     # the inside back wall
D_BACK = D - OVER     # the outside back wall
Z_TOP = DECK + NROW * RISE


def line(d, z=None):
    pts = offset_poly(FE, -d)
    return [np.array([p[0], p[1], z]) for p in pts] if z is not None else pts


def at(s, d, z):
    """The point s metres along the stand from its west end, d back from the front eave, at height z."""
    L = line(d)
    p, u = along(L, s * length(L) / length(FE))
    return np.array([p[0], p[1], z])


def seg_lengths():
    return [float(np.linalg.norm(FE[i + 1] - FE[i])) for i in range(3)]


def roof():
    e0, e1, r = line(0, ZE), line(D, ZE), line(D / 2, ZR)
    zg = ZR - 1.9                       # the Dutch gable's foot
    t = (zg - ZE) / (ZR - ZE) * D / 2   # how far in from the end the gablet stands
    u_w = unit(FE[1] - FE[0])
    u_e = unit(FE[3] - FE[2])
    uw, ue = np.append(u_w, 0), np.append(u_e, 0)
    nw = np.append(perp(u_w), 0)
    ne = np.append(perp(u_e), 0)
    qf_w = e0[0] + uw * t - nw * t + V(0, 0, zg - ZE)
    qb_w = e1[0] + uw * t + nw * t + V(0, 0, zg - ZE)
    rw = r[0] + uw * t
    qf_e = e0[3] - ue * t - ne * t + V(0, 0, zg - ZE)
    qb_e = e1[3] - ue * t + ne * t + V(0, 0, zg - ZE)
    re = r[3] - ue * t
    R = [rw, r[1], r[2], re]
    # front slopes (eave -> ridge), back slopes, by segment
    for i in range(3):
        f = [e0[i], e0[i + 1], R[i + 1], R[i]]
        b = [e1[i + 1], e1[i], R[i], R[i + 1]]
        if i == 0:
            f = [e0[0], e0[1], R[1], rw, qf_w]
            b = [e1[1], e1[0], qb_w, rw, R[1]]
        if i == 2:
            f = [e0[2], e0[3], qf_e, re, R[2]]
            b = [e1[3], e1[2], R[2], re, qb_e]
        add(P + "_roof", f, "roof_red")
        add(P + "_roof", b, "roof_red")
    # hip ends and the Dutch gables
    add(P + "_roof", [e1[0], e0[0], qf_w, qb_w], "roof_red")
    add(P + "_roof", [e0[3], e1[3], qb_e, qf_e], "roof_red")
    for qf, qb, rr, out in ((qf_w, qb_w, rw, -uw), (qf_e, qb_e, re, ue)):
        gable_face(qb, qf, rr, out, P + "_gables")
    # ridge capping and hip cappings (rolled ridge, a shade darker)
    for i in range(3):
        box3(P + "_roof", R[i] + V(0, 0, 0.05), R[i + 1] + V(0, 0, 0.05), 0.32, 0.12, "roof_cap")
    for a, b in ((e0[0], qf_w), (e1[0], qb_w), (e0[3], qf_e), (e1[3], qb_e)):
        box3(P + "_roof", a + V(0, 0, 0.05), b + V(0, 0, 0.05), 0.3, 0.1, "roof_cap")
    # valleys/hips at the bends: cappings along the mitre on the convex (back) side, flashings at the front
    for i in (1, 2):
        box3(P + "_roof", e1[i] + V(0, 0, 0.05), R[i] + V(0, 0, 0.05), 0.3, 0.1, "roof_cap")
        box3(P + "_roof", e0[i] + V(0, 0, 0.03), R[i] + V(0, 0, 0.03), 0.4, 0.05, "flashing")
    return R


def gable_face(a, b, apex, out, part, mat="timber_cream"):
    """A vertical gable triangle a-b-apex (outside along `out`), with boards, barge boards and a finial."""
    add(part, [a, b, apex], "gable_dark")                       # the shadowed vent behind the boards
    w = np.linalg.norm((b - a)[:2])
    ub = unit(b - a)
    n = 32
    for k in range(1, n):
        x = a + ub * w * k / n
        h = (apex[2] - a[2]) * (1 - abs(2 * k / n - 1))
        if h < 0.15:
            continue
        p0 = x + out * 0.04
        box3(part, p0 + V(0, 0, 0.02), p0 + V(0, 0, h - 0.06), 0.07, 0.03, mat)
    # tie beam across the foot and a collar
    box3(part, a + out * 0.08 + V(0, 0, 0.1), b + out * 0.08 + V(0, 0, 0.1), 0.22, 0.12, mat)
    # barge boards: raking boards standing proud
    for p in (a, b):
        box3(part, p + out * 0.18 + V(0, 0, 0.05), apex + out * 0.18 + V(0, 0, 0.12), 0.3, 0.06, mat)
    box3(part, apex + out * 0.2, apex + out * 0.2 + V(0, 0, 1.1), 0.09, 0.09, "steel_dark")   # finial


def front_gables():
    for s, w, hg in ((22.0, 5.0, 2.2), (40.8, 5.0, 2.2), (60.5, 5.0, 2.2)):
        c = at(s, 0.0, ZE)
        c2 = at(s + 0.5, 0.0, ZE)
        u = unit(c2 - c)
        n = np.append(perp(u[:2]), 0)           # out, toward the field
        a, b = c - u * w / 2 + n * 0.15, c + u * w / 2 + n * 0.15
        ap = c + n * 0.15 + V(0, 0, hg)
        dm = hg / math.tan(PITCH)
        meet = c - n * dm + V(0, 0, hg)
        add(P + "_gables", [a, ap, meet, c - u * w / 2 - n * 0.0], "roof_red")
        add(P + "_gables", [ap, b, c + u * w / 2, meet], "roof_red")
        box3(P + "_gables", ap + V(0, 0, 0.05), meet + V(0, 0, 0.05), 0.28, 0.1, "roof_cap")
        gable_face(a, b, ap, n, P + "_gables")
        # the eave fascia breaks under the gable: a timber bracketed beam
        box3(P + "_gables", a + n * 0.1 - V(0, 0, 0.35), b + n * 0.1 - V(0, 0, 0.35), 0.18, 0.4, "timber_cream")


def cupolas(R):
    """Two louvred ventilators on the ridge: cream square base, louvres, bellcast roof, spire."""
    Lr = length(R)
    for frac in (0.44, 0.78):
        p, u = along(R, Lr * frac)
        c = np.array([p[0], p[1]])
        ang = math.atan2(u[1], u[0])
        z0 = ZR - 1.0
        w = 1.55
        obox(P + "_cupola", c, ang, w + 0.25, w + 0.25, z0, ZR + 0.35, "timber_cream", top="timber_cream")
        z1, z2 = ZR + 0.35, ZR + 1.75
        # corner posts and louvre slats on each face (dark gaps between)
        uu = np.array([math.cos(ang), math.sin(ang)])
        vv = perp(uu)
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            q = c + uu * sx * w / 2 + vv * sy * w / 2
            box3(P + "_cupola", (q[0], q[1], z1), (q[0], q[1], z2), 0.16, 0.16, "timber_cream")
        obox(P + "_cupola", c, ang, w - 0.12, w - 0.12, z1, z2, "gable_dark")
        for k in range(9):
            z = z1 + 0.12 + k * 0.145
            for side in range(4):
                a = ang + side * math.pi / 2
                ua = np.array([math.cos(a), math.sin(a)])
                o = c + perp(ua) * (-w / 2 + 0.02)
                p0, p1 = o - ua * (w / 2 - 0.08), o + ua * (w / 2 - 0.08)
                box3(P + "_cupola", (p0[0], p0[1], z), (p1[0], p1[1], z + 0.05), 0.11, 0.035, "timber_cream", up=(0, 0, 1))
        obox(P + "_cupola", c, ang, w + 0.3, w + 0.3, z2, z2 + 0.18, "timber_cream", top="timber_cream")
        # bellcast pyramid: a flared skirt then a steep spire
        def ring(r, z):
            return [np.array([c[0], c[1], z]) + np.append(uu * sx * r + vv * sy * r, 0) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        rings = [ring(1.12, z2 + 0.15), ring(0.9, z2 + 0.45), ring(0.62, z2 + 1.05), ring(0.06, z2 + 2.5)]
        for k in range(3):
            for j in range(4):
                add(P + "_cupola", [rings[k][j], rings[k][(j + 1) % 4], rings[k + 1][(j + 1) % 4], rings[k + 1][j]], "lead_grey")
        tube(P + "_cupola", (c[0], c[1], z2 + 2.4), (c[0], c[1], z2 + 3.3), 0.03, "steel_dark", n=6)
        box3(P + "_cupola", (c[0] - 0.25 * uu[0], c[1] - 0.25 * uu[1], z2 + 3.05), (c[0] + 0.25 * uu[0], c[1] + 0.25 * uu[1], z2 + 3.05), 0.03, 0.03, "steel_dark")


def eaves():
    """Soffits from the eave to the walls (back) and the fascia and gutter all round."""
    fe, be = line(0, ZE), line(D, ZE)
    bw = line(D_BACK, ZE)
    for i in range(3):
        add(P + "_eave", [be[i], be[i + 1], bw[i + 1], bw[i]], "timber_cream")      # rear soffit (seen from below)
    for L, flip in ((fe, False), (be, True)):
        for i in range(3):
            a, b = (L[i], L[i + 1]) if not flip else (L[i + 1], L[i])
            n = np.append(perp(unit((b - a)[:2])), 0) * -1 if False else None
            # fascia: 0.35 m board hanging from the eave, with a gutter in front
            add(P + "_eave", [a - V(0, 0, 0.35), b - V(0, 0, 0.35), b + V(0, 0, 0.02), a + V(0, 0, 0.02)], "fascia_cream")
    # front underside: the roof's underside over the stand (purlins and rafters show as boards)
    fr = line(0.0, ZE)
    rr = line(D_BACKIN, ZE + (D_BACKIN if D_BACKIN < D / 2 else D - D_BACKIN) * math.tan(PITCH))


def body(segs):
    """Podium, balustrade, stairs, rake, inside back wall, rear facade, ends."""
    S = seg_lengths()
    total = sum(S)
    L0 = line(0.6, 0)          # podium front wall line
    # brick podium face from the concourse to the deck, cap, then balustrade piers and panels
    for i in range(3):
        a, b = L0[i][:2], L0[i + 1][:2]
        wall(P + "_body", b, a, 0.0, DECK, "brick_red")     # facing the field (right of b->a is north)
    L1 = line(0.6, DECK)
    L2 = line(1.55, DECK)
    for i in range(3):
        add(P + "_body", [L1[i + 1], L1[i], L2[i], L2[i + 1]], "concrete")              # the front walkway on the deck
    # balustrade: brick piers every 2.4 m with panels between and a cream capping
    Lb = line(0.6)
    lb = length(Lb)
    k = 0
    s = 0.3
    stairs = [8.5, 29.0, 49.5, 63.0]
    while s < lb - 0.3:
        p, u = along(Lb, s)
        if not any(abs(s - st) < 1.6 for st in stairs):
            n = perp(u)
            obox(P + "_body", p - n * 0.15, math.atan2(u[1], u[0]), 0.45, 0.45, DECK, DECK + 1.15, "brick_red", top="render_cream")
            p2, _ = along(Lb, min(s + 2.4, lb - 0.3))
            if not any(abs(s + 1.2 - st) < 1.8 for st in stairs):
                q0, q1 = p - n * 0.15, p2 - n * 0.15
                # panel: a brick wall 0.25 thick, 0.9 tall, with a moulded capping
                wall(P + "_body", q1 + n * 0.12, q0 + n * 0.12, DECK, DECK + 0.9, "brick_red")
                band(P + "_body", q1 + n * 0.12, q0 + n * 0.12, DECK + 0.9, DECK + 1.0, 0.04, "render_cream")
        s += 2.4
    # stairs down to the concourse: a flight of steps in front of the podium with brick cheek walls
    for st in stairs:
        p, u = along(Lb, st)
        n = perp(u)
        ang = math.atan2(u[1], u[0])
        nst = 6
        for k in range(nst):
            z1 = DECK - k * DECK / nst
            dd = 0.3 + k * 0.32
            obox(P + "_stairs", p + n * (dd + 0.16), ang, 2.2, 0.32, 0, z1, "concrete", top="concrete")
        for sx in (-1, 1):
            q = p + u * sx * 1.25
            a0 = q + n * 0.0
            a1 = q + n * (0.3 + nst * 0.32)
            add(P + "_stairs", [(a0[0], a0[1], 0), (a1[0], a1[1], 0), (a1[0], a1[1], 0.5), (a0[0], a0[1], DECK + 1.0)], "brick_red")
            add(P + "_stairs", [(a1[0], a1[1], 0), (a0[0], a0[1], 0), (a0[0], a0[1], DECK + 1.0), (a1[0], a1[1], 0.5)], "brick_red")
    # the rake: risers and treads (seats are placed by seats(); aisles carry nosings)
    for r in range(NROW):
        d0, d1 = D_ROW0 + r * TREAD, D_ROW0 + (r + 1) * TREAD
        z0, z1 = DECK + r * RISE, DECK + (r + 1) * RISE
        A, B, C = line(d0, z0), line(d0, z1), line(d1, z1)
        for i in range(3):
            add(P + "_rake", [A[i + 1], A[i], B[i], B[i + 1]], "concrete_riser")
            add(P + "_rake", [B[i + 1], B[i], C[i], C[i + 1]], "concrete")
    # the inside back wall up to the roof underside (timber boarded, dark)
    zb = DECK + NROW * RISE
    zi = ZE + (D - D_BACKIN) * math.tan(PITCH) if D_BACKIN > D / 2 else ZE + D_BACKIN * math.tan(PITCH)
    A, B = line(D_ROW0 + NROW * TREAD, zb), line(D_ROW0 + NROW * TREAD, zi)
    for i in range(3):
        add(P + "_body", [A[i + 1], A[i], B[i], B[i + 1]], "timber_dark")
    # the roof's underside: front half and back half planes, boarded
    U0, U1, U2 = line(0, ZE - 0.05), line(D / 2, ZR - 0.05), line(D_ROW0 + NROW * TREAD, zi - 0.05)
    for i in range(3):
        add(P + "_under", [U0[i], U0[i + 1], U1[i + 1], U1[i]], "underside")
        add(P + "_under", [U1[i], U1[i + 1], U2[i + 1], U2[i]], "underside")
    # front beam on the posts and the posts (cream timber, square)
    Lp = line(1.05)
    lp = length(Lp)
    posts = [0.25] + [lp * k / 9 for k in range(1, 9)] + [lp - 0.25]
    zbeam = ZE - 0.75
    for s in posts:
        p, u = along(Lp, s)
        box3(P + "_posts", (p[0], p[1], DECK), (p[0], p[1], zbeam), 0.3, 0.3, "timber_cream")
        # knee braces to the beam
        for sx in (-1, 1):
            q = p + u * sx * 0.9
            box3(P + "_posts", (p[0], p[1], zbeam - 1.1), (q[0], q[1], zbeam), 0.12, 0.12, "timber_cream")
    Lpz = [np.array([q[0], q[1], zbeam + 0.3]) for q in Lp]
    for i in range(3):
        box3(P + "_posts", Lpz[i], Lpz[i + 1], 0.32, 0.6, "timber_cream")
    # the rear facade: brick, pilasters every bay, cream bands, two rows of windows and slot vents
    BW = line(D_BACK)
    for i in range(3):
        a, b = BW[i + 1], BW[i]          # walk east->west along the back so the face looks south (out)
        Ls = float(np.linalg.norm(b - a))
        nb = max(2, round(Ls / 4.9))
        bay = Ls / nb
        ops = []
        for k in range(nb):
            s0 = k * bay
            m = s0 + bay / 2
            for w in (-0.75, 0.75):
                ops.append((m + w - 0.33, m + w + 0.33, 2.9, 4.45))     # ground floor tall windows
                ops.append((m + w - 0.3, m + w + 0.3, 7.15, 7.6))       # top row small windows
            ops.append((m - 1.1, m + 1.1, 5.55, 5.7))                   # the long slot vent
        wall(P + "_rear", a, b, 0.0, ZE, "brick_red", openings=ops, depth=0.22, reveal="brick_red", glass="window_dark",
             sill="render_cream")
        u = unit(b - a)
        n = -perp(u)
        for k in range(nb + 1):
            q = a + u * (k * bay)
            if 0 < k < nb or True:
                obox(P + "_rear", q + n * 0.13, math.atan2(u[1], u[0]), 0.62, 0.26, 0.0, ZE - 0.05, "brick_red")
        for z0, z1 in ((4.5, 4.8), (6.35, 6.6), (0.0, 0.35)):
            for k in range(nb):
                q0 = a + u * (k * bay + 0.31)
                q1 = a + u * ((k + 1) * bay - 0.31)
                band(P + "_rear", q0, q1, z0, z1, 0.035, "render_cream" if z0 > 0 else "plinth")
        # downpipes on every third pilaster
        for k in range(0, nb + 1, 3):
            q = a + u * (k * bay) + n * 0.36
            tube(P + "_rear", (q[0], q[1], 0.0), (q[0], q[1], ZE - 0.2), 0.055, "pipe_brown", n=6)
    # end walls: brick below the rake line at the front, full height behind the seats
    for i, s in ((0, 0.0), (3, None)):
        F0 = line(0.6, 0)[i]
        Fd = line(0.6, DECK + 1.0)[i]
        Rb = line(D_ROW0 + NROW * TREAD, Z_TOP + 1.0)[i]
        Bw = line(D_BACK, 0)[i]
        Bt = line(D_BACK, ZE)[i]
        Ri = line(D_ROW0 + NROW * TREAD, ZE)[i]
        Ri0 = line(D_ROW0 + NROW * TREAD, 0)[i]
        poly = [F0, Fd, Rb, Ri0] if i == 0 else [Ri0, Rb, Fd, F0]
        add(P + "_ends", poly, "brick_red")
        add(P + "_ends", poly[::-1], "brick_red")
        add(P + "_ends", [Ri0, Bw, Bt, Ri] if i == 3 else [Bw, Ri0, Ri, Bt], "brick_red")
        add(P + "_ends", [Bw, Ri0, Ri, Bt] if i == 3 else [Ri0, Bw, Bt, Ri], "brick_red")
        # the raking capping on the end wall
        box3(P + "_ends", Fd + V(0, 0, 0.06), Rb + V(0, 0, 0.06), 0.36, 0.12, "render_cream")
        # flues on the back slope near each end
    for frac in (0.3, 0.62):
        p = at(length(FE) * frac, D - 3.2, 0)
        zr = ZE + 3.2 * math.tan(PITCH)
        cyl(P + "_roof", (p[0], p[1]), zr - 0.3, zr + 1.5, 0.2, 0.2, "pipe_brown", n=10, cap="pipe_brown")
        cyl(P + "_roof", (p[0], p[1]), zr + 1.5, zr + 1.75, 0.3, 0.3, "pipe_brown", n=10, cap="pipe_brown")


def seats():
    """Seat positions by colour: (x, y, z, heading) per seat, the heading facing the field."""
    out = {}
    lt = length(FE)
    # colour sections along the stand from the west end (AFLW 2025 photo 01): green, timber, blue, green
    sec = [(0.8, 13.0, "green"), (13.0, 44.0, "timber"), (44.0, 56.0, "blue"), (56.0, lt - 0.8, "green")]
    aisles = [7.0, 19.0, 31.0, 44.0, 56.0, 64.0]
    pitch = 0.5
    for r in range(NROW):
        d = D_ROW0 + r * TREAD + 0.42
        z = DECK + (r + 1) * RISE
        s = 0.8
        while s < lt - 0.8:
            if any(abs(s - a) < 0.6 for a in aisles):
                s += pitch
                continue
            col = next((c for a, b, c in sec if a <= s < b), None)
            if col:
                p = at(s, d, z)
                q = at(s + 0.3, d, z)
                u = unit((q - p)[:2])
                n = perp(u)
                out.setdefault(col, []).append((p[0], p[1], z, math.atan2(n[1], n[0])))
            s += pitch
    return out


def build():
    R = roof()
    front_gables()
    cupolas(R)
    eaves()
    body(seg_lengths())
    return seats()
