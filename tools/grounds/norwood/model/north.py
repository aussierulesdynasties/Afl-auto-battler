"""The north end: the clubrooms in the north-west corner (the sandstone L under grey gabled roofs, the brick
hall north of it, the angled wing facing the ground), the red-roofed kiosk at the Western Stand's north end,
the long shed on the northern boundary and the little red-roofed hut behind the northern goals.

Footprints traced on Esri World Imagery (aligned with OpenStreetMap; used only to measure), heights from
Google Earth's north and north-west views; walls from photos 05-07 (sandstone with brick quoins)."""
import math
import numpy as np
from nwlib import V, add, box3, cyl, obox, unit, perp, wall, band, prism

P = "north"


def gable_building(part, c, ang, L, W, z_eave, z_ridge, wallmat, roofmat, over=0.5, windows=None, hip=False,
                   quoins=None, gable_mat=None):
    """A rectangular building centred on c, its ridge along bearing ang (rad), L long and W wide: walls with
    real window openings, a gable (or hipped) roof overhanging `over`, fascias, barge boards."""
    u = np.array([math.cos(ang), math.sin(ang)])
    v = perp(u)
    c = np.asarray(c, float)
    corners = [c - u * L / 2 - v * W / 2, c + u * L / 2 - v * W / 2, c + u * L / 2 + v * W / 2, c - u * L / 2 + v * W / 2]
    # walls: the long sides with windows, the gable ends up to the ridge
    for k in range(4):
        a, b = corners[(k + 1) % 4], corners[k]
        side_len = float(np.linalg.norm(b - a))
        ops = []
        if windows:
            w, h0, h1, step = windows
            n = int(side_len // step)
            for j in range(n):
                m = (j + 0.5) * side_len / n
                ops.append((m - w / 2, m + w / 2, h0, h1))
        wall(part, a, b, 0.0, z_eave, wallmat, openings=ops, depth=0.25, reveal=wallmat, glass="window_dark", sill="render_cream")
        if quoins:
            for q in (a, b):
                for z in np.arange(0.0, z_eave - 0.3, 0.6):
                    obox(part, q, math.atan2(*(b - a)[::-1]), 0.5 if int(z / 0.6) % 2 else 0.32, 0.5 if int(z / 0.6) % 2 == 0 else 0.32,
                         z, z + 0.3, quoins, top=quoins)
    ue, ve = np.append(u, 0), np.append(v, 0)
    cz = np.array([c[0], c[1], 0.0])
    def P3(su, sv, z):
        return cz + ue * su + ve * sv + V(0, 0, z)
    hl, hw = L / 2 + over, W / 2 + over
    drop = over * (z_ridge - z_eave) / (W / 2)
    ze = z_eave - drop
    if hip:
        r0, r1 = P3(-L / 2 + W / 2, 0, z_ridge), P3(L / 2 - W / 2, 0, z_ridge)
        add(part, [P3(-hl, -hw, ze), P3(hl, -hw, ze), r1, r0], roofmat)
        add(part, [P3(hl, hw, ze), P3(-hl, hw, ze), r0, r1], roofmat)
        add(part, [P3(hl, -hw, ze), P3(hl, hw, ze), r1], roofmat)
        add(part, [P3(-hl, hw, ze), P3(-hl, -hw, ze), r0], roofmat)
    else:
        r0, r1 = P3(-hl, 0, z_ridge), P3(hl, 0, z_ridge)
        add(part, [P3(-hl, -hw, ze), P3(hl, -hw, ze), r1, r0], roofmat)
        add(part, [P3(hl, hw, ze), P3(-hl, hw, ze), r0, r1], roofmat)
        for s in (-1, 1):
            g = [P3(s * L / 2, -W / 2, z_eave), P3(s * L / 2, W / 2, z_eave), P3(s * L / 2, 0, z_ridge)]
            add(part, g if s > 0 else g[::-1], gable_mat or wallmat)
            # barge boards
            for sv in (-1, 1):
                box3(part, P3(s * hl, sv * hw, ze) + V(0, 0, 0.05), P3(s * hl, 0, z_ridge) + V(0, 0, 0.05), 0.25, 0.08, "fascia_cream")
    # underside of the overhang (soffit) and the fascias
    for sv in (-1, 1):
        a, b = P3(-hl, sv * hw, ze), P3(hl, sv * hw, ze)
        add(part, [b - V(0, 0, 0.22), a - V(0, 0, 0.22), a, b] if sv < 0 else [a - V(0, 0, 0.22), b - V(0, 0, 0.22), b, a], "fascia_cream")
        add(part, [P3(-hl, sv * hw, ze - 0.02), P3(hl, sv * hw, ze - 0.02), P3(hl, sv * W / 2, z_eave - 0.02), P3(-hl, sv * W / 2, z_eave - 0.02)][::(-1 if sv > 0 else 1)], "fascia_cream")
    box3(part, r0 + V(0, 0, 0.04), r1 + V(0, 0, 0.04), 0.3, 0.1, roofmat)


def skillion(part, poly, z_hi, z_lo, hi_edge, wallmat, roofmat, over=0.4):
    """A building with a mono-pitch roof falling from edge hi_edge (index into poly) to the opposite side."""
    pts = [np.asarray(p, float) for p in poly]
    a, b = pts[hi_edge], pts[(hi_edge + 1) % len(pts)]
    u = unit(b - a)
    n = -perp(u)      # outward of that edge (poly anticlockwise)
    depth = max(float(np.dot(p - a, -n)) for p in pts)
    def z_at(p):
        t = float(np.dot(p - a, -n)) / depth
        return z_hi + (z_lo - z_hi) * t
    for k in range(len(pts)):
        p, q = pts[(k + 1) % len(pts)], pts[k]
        add(part, [(p[0], p[1], 0), (q[0], q[1], 0), (q[0], q[1], z_at(q)), (p[0], p[1], z_at(p))][::-1], wallmat)
    # the roof sheet with its overhang
    c = sum(pts) / len(pts)
    big = [c + (p - c) * (1 + over / max(1.0, float(np.linalg.norm(p - c)))) for p in pts]
    add(part, [(p[0], p[1], z_at(p) + 0.05) for p in big], roofmat)
    add(part, [(p[0], p[1], z_at(p) - 0.12) for p in big][::-1], "fascia_cream")
    for k in range(len(big)):
        p, q = big[k], big[(k + 1) % len(big)]
        add(part, [(p[0], p[1], z_at(p) - 0.12), (q[0], q[1], z_at(q) - 0.12), (q[0], q[1], z_at(q) + 0.05), (p[0], p[1], z_at(p) + 0.05)], "fascia_cream")


def build():
    # the sandstone clubrooms (Simon Black Academy): main wing, ridge east-west
    gable_building(P + "_club", (-58.9, 82.0), 0.0, 19.0, 13.5, 5.2, 8.6, "sandstone", "roof_grey", windows=(1.1, 1.2, 3.0, 3.6),
                   quoins="brick_red")
    # the brick hall north of it, ridge north-south, pale roof
    gable_building(P + "_hall", (-63.2, 96.3), math.pi / 2, 14.0, 14.0, 5.6, 7.9, "brick_red", "roof_pale", windows=(1.2, 2.2, 4.2, 3.5))
    # the angled wing on the corner of the ground, ridge running north-west to south-east
    gable_building(P + "_wing", (-46.0, 90.0), math.radians(-45), 19.0, 8.5, 4.6, 7.2, "sandstone", "roof_grey_green",
                   windows=(1.0, 1.2, 2.9, 3.2), quoins="brick_red")
    # the lower link between the two
    obox(P + "_link", (-50.5, 81.0), math.radians(-45), 7.0, 6.0, 0.0, 3.6, "render_cream", top="roof_pale")
    # the long shed on the northern boundary: skillion falling to the street
    skillion(P + "_shed", [(-44.5, 100.4), (-25.6, 100.4), (-25.6, 107.0), (-44.5, 107.0)], 3.8, 3.2, 0, "corr_cream", "roof_grey")
    # the red-roofed hut behind the northern goals: brick, red gable roof, ridge north-south
    gable_building(P + "_hut", (-5.2, 102.0), math.pi / 2, 8.0, 8.2, 2.8, 4.4, "brick_red", "roof_red", windows=(0.9, 1.0, 2.0, 3.0))
    # the red skillion kiosk at the Western Stand's north end, falling to the field, cream walls, white annex
    skillion(P + "_kiosk", [(-64.0, 60.0), (-56.8, 60.0), (-56.8, 71.6), (-64.0, 71.6)], 3.9, 3.0, 3, "render_cream", "roof_red")
    obox(P + "_kiosk", (-65.6, 65.0), math.pi / 2, 8.0, 3.2, 0.0, 3.0, "render_white", top="roof_pale")
    return {}
