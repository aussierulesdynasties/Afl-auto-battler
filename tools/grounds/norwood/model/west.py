"""The west side: the Western Stand (Centenary Pavilion: brick podium, eight rows of teal seats, glazed rooms
along the back, a long flat roof on slender columns, red corrugated back wall with steel stairs to Woods
Street) and the Wolf Blass Community Centre in the south-west corner (a glass box upstairs under a thin
cantilevered roof, a dark and red ground floor, black panels to the street).

Plan: OpenStreetMap's grandstand outline (way 547107342) on Google Earth's mosaic; heights and details from
AFLW 2025 photo 23 and Google Earth's west views."""
import math
import numpy as np
from nwlib import V, add, box3, cyl, tube, obox, unit, perp, offset_poly, along, length, wall, band, prism

P = "ws"
# roof front, south to north: OSM way 547107342 moved 0.9 m west. The roof's front edge, traced every 5 m on
# Google Earth's top-down mosaic with the lean taken out for its 8.8 m height, stands 0.9 m (0.0-1.3) west of
# OSM's line (2026-11-22). The satellite mosaic sits 2.3 m east of Google Earth's frame: never trace from it.
RF = [np.array([-55.2, -43.5]), np.array([-57.8, 3.0]), np.array([-60.3, 49.5])]
U = unit(RF[-1] - RF[0])


def line(d, z=None):
    pts = offset_poly(RF, d)          # left of south->north is west: d > 0 goes back
    return [np.array([p[0], p[1], z]) for p in pts] if z is not None else pts


def at(s, d, z):
    L = line(d)
    p, _ = along(L, s)
    return np.array([p[0], p[1], z])


LEN = length(RF)
D_POD = 1.5
Z_POD = 1.6
NROW = 8
TREAD, RISE = 0.75, 0.36
D_ROW0 = 2.3
D_BOX = D_ROW0 + NROW * TREAD + 0.2
D_BACK = 10.5
Z_FRONT, Z_BACKR = 8.8, 8.3


def z_roof(d):
    return Z_FRONT + (Z_BACKR - Z_FRONT) * (d + 0.5) / (D_BACK + 0.9)


def stand():
    # podium front (brick), deck walkway, glass balustrade on posts
    a, b = line(D_POD)[0], line(D_POD)[-1]
    for i in range(2):
        p0, p1 = line(D_POD)[i], line(D_POD)[i + 1]
        wall(P + "_body", p0, p1, 0.0, Z_POD, "brick_red")          # right of south->north faces east (the field)
        band(P + "_body", p0, p1, Z_POD - 0.12, Z_POD + 0.02, 0.05, "concrete")
    A, B = line(D_POD, Z_POD), line(D_ROW0, Z_POD)
    for i in range(2):
        add(P + "_body", [A[i], A[i + 1], B[i + 1], B[i]], "concrete")
    Lb = line(D_POD + 0.12)
    s = 0.0
    while s <= LEN + 0.01:
        p, u = along(Lb, s)
        box3(P + "_rail", (p[0], p[1], Z_POD), (p[0], p[1], Z_POD + 1.05), 0.05, 0.05, "steel_charcoal")
        s += 1.6
    for i in range(2):
        p0, p1 = Lb[i], Lb[i + 1]
        box3(P + "_rail", (p0[0], p0[1], Z_POD + 1.05), (p1[0], p1[1], Z_POD + 1.05), 0.06, 0.06, "steel_charcoal")
        add(P + "_rail", [(p1[0], p1[1], Z_POD + 0.1), (p0[0], p0[1], Z_POD + 0.1), (p0[0], p0[1], Z_POD + 1.0), (p1[0], p1[1], Z_POD + 1.0)], "glass_rail")
    # rake
    for r in range(NROW):
        d0, d1 = D_ROW0 + r * TREAD, D_ROW0 + (r + 1) * TREAD
        z0, z1 = Z_POD + r * RISE, Z_POD + (r + 1) * RISE
        A, B, C = line(d0, z0), line(d0, z1), line(d1, z1)
        for i in range(2):
            add(P + "_rake", [A[i], A[i + 1], B[i + 1], B[i]], "concrete_riser")
            add(P + "_rake", [B[i], B[i + 1], C[i + 1], C[i]], "concrete")
    ztop = Z_POD + NROW * RISE
    # the glazed rooms along the back: mullions every 1.5 m, a slab under the roof
    G0, G1 = line(D_BOX, ztop), line(D_BOX, z_roof(D_BOX) - 0.45)
    for i in range(2):
        add(P + "_boxes", [G0[i], G0[i + 1], G1[i + 1], G1[i]], "curtain_glass")
    Lm = line(D_BOX - 0.06)
    s = 0.0
    while s <= LEN + 0.01:
        p, _ = along(Lm, s)
        box3(P + "_boxes", (p[0], p[1], ztop), (p[0], p[1], z_roof(D_BOX) - 0.45), 0.08, 0.12, "steel_charcoal")
        s += 1.5
    for i in range(2):
        for z in (ztop + 0.05, ztop + 1.1, z_roof(D_BOX) - 0.5):
            p0, p1 = Lm[i], Lm[i + 1]
            box3(P + "_boxes", (p0[0], p0[1], z), (p1[0], p1[1], z), 0.1, 0.1, "steel_charcoal")
    # the roof: sheeting on top, dark underside, a deep fascia, and columns at the front of the rake
    for i in range(2):
        f0, f1 = line(-0.5)[i], line(-0.5)[i + 1]
        b0, b1 = line(D_BACK + 0.4)[i], line(D_BACK + 0.4)[i + 1]
        zf, zb = z_roof(-0.5), z_roof(D_BACK + 0.4)
        add(P + "_roof", [(f1[0], f1[1], zf), (f0[0], f0[1], zf), (b0[0], b0[1], zb), (b1[0], b1[1], zb)], "roof_zinc")
        add(P + "_roof", [(f0[0], f0[1], zf - 0.35), (f1[0], f1[1], zf - 0.35), (b1[0], b1[1], zb - 0.35), (b0[0], b0[1], zb - 0.35)], "underside_dark")
        add(P + "_roof", [(f0[0], f0[1], zf - 0.6), (f1[0], f1[1], zf - 0.6), (f1[0], f1[1], zf + 0.05), (f0[0], f0[1], zf + 0.05)], "fascia_cream")
        add(P + "_roof", [(b1[0], b1[1], zb - 0.35), (b0[0], b0[1], zb - 0.35), (b0[0], b0[1], zb + 0.05), (b1[0], b1[1], zb + 0.05)], "steel_charcoal")
    # roof ends
    for k, sgn in ((0, 1), (-1, -1)):
        f, b = line(-0.5)[k], line(D_BACK + 0.4)[k]
        zf, zb = z_roof(-0.5), z_roof(D_BACK + 0.4)
        q = [(f[0], f[1], zf - 0.35), (b[0], b[1], zb - 0.35), (b[0], b[1], zb + 0.05), (f[0], f[1], zf + 0.05)]
        add(P + "_roof", q if sgn > 0 else q[::-1], "steel_charcoal")
    # purlins under the roof (exposed steel), every 1.6 m across the depth
    for d in np.arange(0.4, D_BACK, 1.6):
        L = line(d)
        for i in range(2):
            box3(P + "_roof", (L[i][0], L[i][1], z_roof(d) - 0.45), (L[i + 1][0], L[i + 1][1], z_roof(d) - 0.45), 0.08, 0.2, "steel_charcoal")
    nc = 13
    for k in range(nc):
        s = LEN * k / (nc - 1)
        p = at(s, 1.9, 0)
        box3(P + "_cols", (p[0], p[1], Z_POD), (p[0], p[1], z_roof(1.9) - 0.35), 0.22, 0.22, "steel_charcoal")
        q = at(s, D_BACK - 0.3, 0)
        box3(P + "_cols", (p[0], p[1], z_roof(1.9) - 0.55), (q[0], q[1], z_roof(D_BACK - 0.3) - 0.55), 0.18, 0.4, "steel_charcoal")
    # the back: red corrugated wall with a concrete plinth, landings and steel stairs down to Woods Street
    for i in range(2):
        p0, p1 = line(D_BACK)[i + 1], line(D_BACK)[i]
        wall(P + "_back", p0, p1, 0.0, z_roof(D_BACK) - 0.3, "corr_red")
        band(P + "_back", p0, p1, 0.0, 0.5, 0.03, "concrete")
    for s in (64.0,):          # the one stair tower seen behind the stand from Woods Street (GE ws_045/ws_090)
        p, u = along(line(D_BACK), s)
        n = perp(u)        # west, out the back
        ang = math.atan2(u[1], u[0])
        for k in range(12):
            z1 = ztop - k * ztop / 12
            obox(P + "_stairs", p + n * 0.6 + u * (1.2 + k * 0.28), ang, 0.28, 1.1, z1 - 0.05, z1, "steel_dark")
        for sx in (0.1, 1.1):
            a0 = p + n * sx + u * 1.2
            a1 = p + n * sx + u * (1.2 + 12 * 0.28)
            box3(P + "_stairs", (a0[0], a0[1], ztop + 1.0), (a1[0], a1[1], 1.0), 0.05, 0.05, "steel_dark")
            box3(P + "_stairs", (a0[0], a0[1], ztop), (a1[0], a1[1], 0.0), 0.06, 0.25, "steel_dark")
        obox(P + "_stairs", p + n * 0.6 + u * 0.4, ang, 1.6, 1.1, ztop - 0.1, ztop, "steel_dark")
    # ends: maroon corrugated sheeting on a steel frame (photos 02, 03)
    for k in (0, -1):
        q = [line(D_POD, 0)[k], line(D_POD, Z_POD + 1.05)[k], line(D_BOX, ztop + 1.0)[k], line(D_BOX, z_roof(D_BOX) - 0.35)[k],
             line(D_BACK, z_roof(D_BACK) - 0.35)[k], line(D_BACK, 0)[k]]
        add(P + "_ends", q if k == 0 else q[::-1], "corr_red")
        add(P + "_ends", q[::-1] if k == 0 else q, "corr_red")
    # the north end's open steel stair: from the path behind the fence up along the end wall to the third row
    pa, ua = along(line(D_POD), LEN)
    pb, _ = along(line(D_BACK), LEN)
    out = unit(np.asarray(pa) - np.asarray(along(line(D_POD), LEN - 1.0)[0]))      # north, off the end
    run = unit(np.asarray(pa) - np.asarray(pb))                                      # east, toward the field
    z_land = Z_POD + 3 * RISE
    nst = 14
    base = np.asarray(pb) + out * 0.85 + run * 1.2
    ang = math.atan2(run[1], run[0])
    for k in range(nst):
        z1 = z_land * (k + 1) / nst
        obox(P + "_stairs", base + run * (k * 0.28 + 0.14), ang, 0.28, 1.2, z1 - 0.05, z1, "steel_dark")
    top = base + run * (nst * 0.28)
    obox(P + "_stairs", top + run * 0.8, ang, 1.6, 1.2, z_land - 0.12, z_land, "steel_dark")
    for side in (-0.6, 0.6):
        a0 = base + out * side
        a1 = top + out * side
        box3(P + "_stairs", (a0[0], a0[1], 0.0), (a1[0], a1[1], z_land), 0.06, 0.25, "steel_dark")
        box3(P + "_stairs", (a0[0], a0[1], 1.0), (a1[0], a1[1], z_land + 1.0), 0.045, 0.045, "alu")
        for t in (0.0, 0.5, 1.0):
            c = a0 + (a1 - a0) * t
            zc = z_land * t
            box3(P + "_stairs", (c[0], c[1], max(zc - 2.0, 0.0) if t > 0 else 0.0), (c[0], c[1], zc + 1.0), 0.05, 0.05, "steel_dark")
    for k in range(4):          # landing legs
        c = top + run * (0.1 + 1.4 * (k // 2)) + out * (-0.55 + 1.1 * (k % 2))
        box3(P + "_stairs", (c[0], c[1], 0.0), (c[0], c[1], z_land - 0.12), 0.1, 0.1, "steel_dark")


def seats():
    out = {}
    red = [(40.0, 52.0), (62.0, 68.0)]
    aisles = [6.0, 18.5, 31.0, 43.5, 56.0, 68.5, 81.0]
    for r in range(NROW):
        d = D_ROW0 + r * TREAD + 0.38
        z = Z_POD + (r + 1) * RISE
        s = 0.6
        while s < LEN - 0.6:
            if not any(abs(s - a) < 0.6 for a in aisles):
                p = at(s, d, z)
                col = "ws_red" if any(a <= s < b for a, b in red) else "ws_teal"
                n = -perp(U)        # facing east
                out.setdefault(col, []).append((p[0], p[1], z, math.atan2(n[1], n[0])))
            s += 0.48
    return out


W = "wbcc"
FN, FS = np.array([-52.0, -47.6]), np.array([-45.3, -70.5])     # the glass front, north to south (Esri roof outline)
FOOT = [FN, FS, np.array([-48.0, -73.4]), np.array([-57.6, -84.0]), np.array([-59.8, -81.5]), np.array([-59.8, -50.0]),
        np.array([-57.5, -47.6])]
Z1, Z2 = 4.3, 9.3


def wbcc():
    # the ground floor: dark glazing behind a red-framed opening, the street sides black panels
    n = len(FOOT)
    for i in range(n):
        a, b = FOOT[(i + 1) % n], FOOT[i]       # the footprint runs anticlockwise; walk clockwise to face out
        if i == 0:
            # the field front: ground floor glazed shopfront in a red frame; upstairs the curtain wall
            L = float(np.linalg.norm(b - a))
            ops = [(0.6, L - 0.6, 0.0, 3.4)]
            wall(W, a, b, 0.0, Z1, "panel_black", openings=ops, depth=0.3, reveal="panel_red", glass="curtain_glass")
            band(W, a, b, Z1 - 0.55, Z1, 0.08, "panel_red")
            continue
        wall(W, a, b, 0.0, Z1, "panel_black")
    # upstairs: the glass box on the front and north, set on the red band; the rest black panels
    for i in range(n):
        a, b = FOOT[(i + 1) % n], FOOT[i]
        if i in (0, 6):
            add(W, [(a[0], a[1], Z1), (b[0], b[1], Z1), (b[0], b[1], Z2), (a[0], a[1], Z2)], "curtain_glass")
            L = float(np.linalg.norm(b - a))
            u = unit(b - a)
            nn = -perp(u)
            k = 0
            while k * 1.5 <= L + 0.01:
                p = a + u * min(k * 1.5, L) + nn * 0.06
                box3(W, (p[0], p[1], Z1), (p[0], p[1], Z2), 0.07, 0.14, "steel_charcoal")
                k += 1
            for z in (Z1 + 0.05, Z1 + 2.5, Z2 - 0.05):
                p0, p1 = a + nn * 0.06, b + nn * 0.06
                box3(W, (p0[0], p0[1], z), (p1[0], p1[1], z), 0.1, 0.1, "steel_charcoal")
        else:
            add(W, [(a[0], a[1], Z1), (b[0], b[1], Z1), (b[0], b[1], Z2), (a[0], a[1], Z2)], "panel_black")
    # the cantilevered roof: 2.2 m over the front, 0.6 elsewhere, white edge, dark soffit
    big = offset_poly([FOOT[6], FN, FS, FOOT[2]], 2.2)
    roofp = [big[1], big[2]] + [FOOT[2], FOOT[3], FOOT[4], FOOT[5], FOOT[6]]
    roofp = [FOOT[6] + (FOOT[6] - FOOT[5]) * 0.0] + [big[1], big[2], FOOT[2], FOOT[3], FOOT[4], FOOT[5]]
    prism(W + "_roof", [tuple(p) for p in roofp], Z2, Z2 + 0.55, "render_white", top="roof_zinc", bottom="underside_dark")
    # a plant screen on the roof, set back
    c = (FOOT[3] + FOOT[5]) / 2
    obox(W + "_roof", c, math.atan2(*(FOOT[4] - FOOT[3])[::-1]), 6.0, 4.0, Z2 + 0.55, Z2 + 2.0, "steel_charcoal", top="steel_charcoal")


def build():
    stand()
    wbcc()
    return seats()
