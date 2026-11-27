"""The buildings that face Norwood Oval, modelled one by one (the rest of the suburb is surrounds.py's).

East, between the ground and Osmond Terrace (Google Earth e_270 / e_090 / e_045 / e_135, the top-down
tiles): the row of six two-storey red-brick townhouses, gable ends to the ground; the big two-storey
brick house behind them; the pale blue-grey shed by the terraces; the single-storey villa with its
verandah (37-39); the two-storey brick villa with its balcony at the north-east; the townhouses at the
north-east corner (43); the south-east house with its pool court and the tennis court.
Plan metres from the centre circle (x east, y north).
"""
import math
import numpy as np
from nwlib import V, add, box3, obox, unit, perp, wall, prism
from north import gable_building, skillion
from land import T, on_land

P = "town"


def chimney(part, p, z0, z1, mat="brick_terrace"):
    obox(part, p, 0.0, 0.7, 0.5, z0, z1, mat, top=mat)
    obox(part, p, 0.0, 0.86, 0.66, z1 - 0.25, z1 - 0.1, "render_cream", top="render_cream", bottom="render_cream")
    for dx in (-0.16, 0.16):
        obox(part, (p[0] + dx, p[1]), 0.0, 0.2, 0.2, z1, z1 + 0.35, "pipe_brown", top="pipe_brown")


def verandah(part, a, b, depth, z, posts_every=2.6, mat="roof_slate_grey"):
    """A verandah along the wall a->b (outside on the right), its roof falling from z to z - 0.5, on posts."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    u = unit(b - a)
    n = -perp(u)
    L = float(np.linalg.norm(b - a))
    q = [a, b, b + n * depth, a + n * depth]
    add(part, [V(*q[0], z), V(*q[1], z), V(*q[2], z - 0.5), V(*q[3], z - 0.5)][::-1], mat)
    add(part, [V(*q[0], z - 0.08), V(*q[1], z - 0.08), V(*q[2], z - 0.58), V(*q[3], z - 0.58)], "fascia_cream")
    k = max(2, int(L / posts_every) + 1)
    for j in range(k):
        c = a + u * (0.15 + (L - 0.3) * j / (k - 1)) + n * (depth - 0.15)
        obox(part, c, math.atan2(u[1], u[0]), 0.12, 0.12, 0.0, z - 0.55, "timber_white", top="timber_white")
    # the frieze under the gutter and the beam
    c0, c1 = a + n * (depth - 0.15), b + n * (depth - 0.15)
    box3(part, V(*c0, z - 0.72), V(*c1, z - 0.72), 0.14, 0.3, "timber_white")


def blinds(part, x, y0, y1, z_top, z_bot, stripe=0.3):
    """Striped canvas blinds hanging on a west-facing verandah edge at x, from y0 down to y1 (y0 > y1),
    z_top to z_bot: white and grey-blue stripes, a stripe wide each, a slight bulge outwards at the foot."""
    n = int((y0 - y1) / stripe)
    for k in range(n):
        ya, yb = y0 - k * stripe, y0 - (k + 1) * stripe
        mat = "paint_white" if k % 2 == 0 else "awning_blue"
        add(part, [V(x, ya, z_top), V(x, yb, z_top), V(x - 0.12, yb, z_bot), V(x - 0.12, ya, z_bot)], mat)
        add(part, [V(x + 0.01, yb, z_top), V(x + 0.01, ya, z_top), V(x - 0.11, ya, z_bot), V(x - 0.11, yb, z_bot)], mat)


def townhouses():
    """Six two-storey townhouses in a row (Google Earth e_270): orange-red brick, white-trimmed sash windows
    two to a floor on the gable end facing the ground, grey Colorbond gables, a low wing at the back.
    Each roof traced on Google Earth's top-down mosaic (lean taken out for 7 m, 2026-11-22): the party walls
    at y below, each main roof's west and east ends in WE/EE (roof edges, overhang included)."""
    YB = [-11.5, -18.9, -26.1, -33.2, -40.3, -45.6, -53.0]
    WE = [75.25, 76.22, 76.51, 76.9, 77.19, 76.51]
    EE = [83.32, 86.26, 84.3, 87.61, 87.9, 83.71]
    part = P + "_terrace"
    for k in range(6):
      with on_land(part):
        y0, y1 = YB[k], YB[k + 1]
        yc, wd = (y0 + y1) / 2, y0 - y1
        x0, x1 = WE[k] + 0.35, EE[k] - 0.35
        gable_building(part, ((x0 + x1) / 2, yc), 0.0, x1 - x0, wd - 0.6, 6.0, 8.9, "brick_terrace", "roof_pale",
                       over=0.35, windows=[(1.1, 1.0, 2.6, min(4.2, wd - 3.0)), (1.1, 3.9, 5.4, min(4.2, wd - 3.0))],
                       gable_mat="brick_terrace")
        gable_building(part, (x1 + 2.6, yc), 0.0, 5.2, min(5.0, wd - 0.8), 3.0, 4.6, "brick_terrace", "roof_pale",
                       over=0.3, windows=(1.0, 0.9, 2.2, 2.4))
        chimney(part, (x1 - 2.4, y0 - 0.9), 7.0, 10.0)
        # party walls stand proud of the roof between the houses
        if k:
            obox(part, ((x0 + x1) / 2, y0), 0.0, x1 - x0 + 0.6, 0.36, 6.0, 7.3, "brick_terrace", top="render_cream")
        # small timber deck and steps on the ground side
        obox(part, (x0 - 0.8, yc), 0.0, 1.6, 3.2, 0.0, 0.5, "timber_dark", top="timber_dark")
    # the low flat-roofed garage at the row's south end
    with on_land(part):
        prism(part, [(77.5, -53.6), (82.0, -53.6), (82.0, -60.0), (77.5, -60.0)], 0.0, 3.2, "brick_terrace", top="roof_grey")
    # the south end house, set back and lower, hipped to the ground (top-down: x 70.4-78.9, y -58.0 to -66.5)
    with on_land(part):
        gable_building(part, (74.65, -62.25), math.pi / 2, 7.8, 7.8, 5.8, 8.4, "brick_terrace", "roof_pale",
                       over=0.35, windows=[(1.1, 1.0, 2.6, 3.2), (1.1, 3.9, 5.4, 3.2)], hip=True)
    # the jacarandas' bed and the low brick wall in front of the row (between the terrace walk and the houses)
    with on_land(part):
        box3(part, V(71.0, -10.0, 0.0), V(71.0, -57.0, 0.0), 0.3, 0.9, "brick_terrace")


def big_house():
    """Behind the row: a two-storey brick house under a big grey hipped roof with chimneys, and its south wing."""
    part = P + "_house_e"
    gable_building(part, (108.75, -27.85), math.pi / 2, 29.9, 20.1, 7.2, 11.2, "brick_terrace", "roof_slate_grey",
                   over=0.5, windows=[(1.3, 1.1, 3.0, 3.6), (1.3, 4.3, 6.2, 3.6)], hip=True)
    for y in (-17.0, -24.0, -31.0, -38.0):
        chimney(part, (104.5, y), 9.0, 12.6)
    gable_building(part, (110.0, -48.5), 0.0, 22.0, 8.0, 3.4, 5.4, "brick_terrace", "roof_slate_grey", over=0.4,
                   windows=(1.2, 1.0, 2.4, 3.2), hip=True)
    # the two-level verandah across the north two-thirds of its west front (Google Earth gE_s, 2026-11-26):
    # white posts, a balcony with a balustrade, and striped canvas blinds drawn halfway down the upper level
    xw, ya, yb, dp = 98.7, -13.4, -35.0, 2.6
    verandah(part, (xw, ya), (xw, yb), dp, 3.5)
    verandah(part, (xw, ya), (xw, yb), dp, 7.1)
    obox(part, (xw - dp / 2, (ya + yb) / 2), 0.0, dp, ya - yb, 3.55, 3.75, "timber_white", top="timber_dark",
         bottom="timber_white")
    box3(part, V(xw - dp + 0.15, ya, 4.75), V(xw - dp + 0.15, yb, 4.75), 0.08, 0.08, "timber_white")
    for y in np.arange(yb + 0.2, ya, 0.16):
        box3(part, V(xw - dp + 0.15, y, 3.75), V(xw - dp + 0.15, y, 4.75), 0.03, 0.03, "timber_white")
    blinds(part, xw - dp + 0.05, ya - 0.2, yb + 0.2, 6.5, 5.3)


def shed():
    """The pale blue-grey corrugated shed beside the east terraces (e_270, e_090), its dark west wall to
    the ground, a lower annex to the east."""
    part = P + "_shed"
    gable_building(part, (78.0, 25.5), math.pi / 2, 23.0, 18.0, 6.2, 7.6, "corr_bluegrey", "roof_zinc", over=0.3,
                   windows=None, gable_mat="corr_bluegrey")
    prism(part, [(87.0, 14.0), (93.0, 14.0), (93.0, 37.0), (87.0, 37.0)], 0.0, 4.2, "corr_bluegrey", top="roof_zinc")
    # the west face's dark cladding panel (by the terraces) and roller doors
    wall(part, (68.9, 15.0), (68.9, 36.0), 0.0, 5.8, "panel_black",
         openings=[(2.0, 5.2, 0.0, 3.6), (12.0, 15.2, 0.0, 3.6)], depth=0.15, glass="steel_dark")
    # plant and bins in the lean-to strip along its west side
    for y in (16.0, 21.0, 26.0, 31.0):
        obox(part, (67.0, y), 0.0, 1.4, 2.2, 0.0, 1.4, "alu", top="alu")
    # the green container hut and the white hut in the sandy yard to its south
    obox(part, (75.5, 4.0), 0.0, 6.0, 2.5, 0.0, 2.6, "roof_grey_green", top="roof_grey_green")
    obox(part, (82.5, 2.5), 0.0, 5.5, 3.0, 0.0, 2.4, "render_white", top="roof_zinc")


def villa_37():
    """37-39: a single-storey villa with a hipped grey roof, a verandah to the ground and a long rear wing."""
    part = P + "_villa37"
    gable_building(part, (104.0, 29.0), math.pi / 2, 16.0, 13.0, 3.9, 7.0, "bluestone", "roof_slate_grey", over=0.5,
                   windows=(1.2, 1.0, 2.8, 3.4), hip=True, quoins="render_cream")
    verandah(part, (97.5, 21.5), (97.5, 36.5), 2.4, 3.4)
    gable_building(part, (106.0, 15.5), 0.0, 18.0, 12.0, 3.4, 5.4, "render_cream", "roof_pale", over=0.4,
                   windows=(1.2, 1.0, 2.6, 3.4), hip=True)
    chimney(part, (101.0, 31.5), 5.0, 8.2)
    chimney(part, (107.0, 26.0), 5.0, 8.2)


def villa_ne():
    """The two-storey red-brick villa at the north-east (e_090; placed on Google Earth's top-down mosaic): grey hipped roof, two-level verandah facing
    the ground with white posts and balustrade, chimneys."""
    part = P + "_villa_ne"
    gable_building(part, (99.5, 79.0), 0.0, 23.0, 15.0, 7.4, 11.0, "brick_terrace", "roof_slate_grey", over=0.5,
                   windows=[(1.3, 1.1, 3.1, 3.8), (1.3, 4.4, 6.4, 3.8)], hip=True, quoins="render_cream")
    a, b = (87.9, 72.0), (87.9, 86.0)
    verandah(part, b, a, 2.6, 3.5)
    verandah(part, b, a, 2.6, 7.1)
    # the balcony floor and balustrade
    obox(part, (86.6, 79.0), 0.0, 2.6, 14.0, 3.55, 3.75, "timber_white", top="timber_dark", bottom="timber_white")
    box3(part, V(85.4, 72.0, 4.75), V(85.4, 86.0, 4.75), 0.08, 0.08, "timber_white")
    for y in np.arange(72.2, 86.0, 0.16):
        box3(part, V(85.4, y, 3.75), V(85.4, y, 4.75), 0.03, 0.03, "timber_white")
    for y in (71.5, 84.0):
        chimney(part, (103.5, y), 10.0, 12.8)
    gable_building(part, (104.5, 66.5), 0.0, 12.0, 8.0, 3.4, 5.2, "brick_terrace", "roof_slate_grey", over=0.4,
                   windows=(1.2, 1.0, 2.6, 3.2), hip=True)


def townhouses_ne():
    """The big two-storey building at the north-east corner, beside the school's courts: two parallel hipped
    wings with a gabled wing between them, pale grey roofs. Its footprint is traced from Google Earth's
    top-down mosaic (lean taken out for 9 m, 2026-11-23); its walls and windows are not yet checked against
    oblique photos."""
    part = P + "_ne43"
    for x0, x1 in ((55.3, 64.2), (71.5, 79.0)):
        gable_building(part, ((x0 + x1) / 2 + 0.0, 95.75), math.pi / 2, 24.1 - 1.0, x1 - x0 - 1.0, 7.0, 10.0,
                       "render_cream", "roof_slate_grey", over=0.5,
                       windows=[(1.2, 1.0, 2.8, 3.2), (1.2, 4.0, 5.8, 3.2)], hip=True)
    gable_building(part, (67.85, 95.0), math.pi / 2, 21.0, 7.3 - 0.6, 6.4, 9.2, "render_cream", "roof_slate_grey",
                   over=0.3, windows=[(1.2, 1.0, 2.8, 3.2), (1.2, 4.0, 5.6, 3.2)], gable_mat="render_cream")


def south_east():
    """The south-east block: the big two-storey house with its gables to Osmond Terrace, its pool court,
    the modern house with solar panels and the tennis court beside the ground (top-down tiles)."""
    part = P + "_se"
    with on_land(part):
        gable_building(part, (110.0, -78.0), math.pi / 2, 36.0, 14.0, 6.8, 10.4, "render_cream", "roof_slate_grey",
                       over=0.5, windows=[(1.2, 1.0, 2.8, 3.4), (1.2, 4.0, 5.9, 3.4)], hip=True)
    with on_land(part):
        for y in (-68.0, -80.0, -91.0):
            gable_building(part, (119.5, y), 0.0, 7.0, 6.5, 6.8, 9.8, "render_cream", "roof_slate_grey", over=0.4,
                           windows=[(1.2, 1.0, 2.8, 3.0), (1.2, 4.0, 5.9, 3.0)], gable_mat="render_cream")
    with on_land(part):
        gable_building(part, (96.0, -93.5), 0.0, 22.0, 9.0, 6.4, 9.4, "render_cream", "roof_slate_grey", over=0.4,
                       windows=[(1.2, 1.0, 2.8, 3.2), (1.2, 4.0, 5.6, 3.2)], hip=True)
    # the pool and its paving (the water a hand under the coping): top-down, pool x 92.3-97.7, y -77.3 to -81.7
    with on_land(part):
        obox(part, (94.5, -78.8), 0.0, 17.0, 9.0, 0.0, 0.12, "concrete", top="concrete")
        obox(part, (95.0, -79.5), 0.0, 5.4, 4.4, 0.12, 0.14, "glass_rail", top="glass_rail")
    # the two modern houses north of the pool: flat roofs covered in solar panels (traced, lean out for 6.6 m)
    for (x0, x1, y0, y1) in ((80.8, 90.1, -73.0, -63.5), (93.1, 102.6, -73.6, -60.6)):
      with on_land(part):
        prism(part, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 0.0, 6.6, "render_white", top="roof_grey")
        for xx in np.arange(x0 + 1.4, x1 - 1.0, 2.2):
            obox(part, (xx, (y0 + y1) / 2), 0.0, 1.8, (y1 - y0) - 2.4, 6.7, 6.78, "window_dark", top="window_dark")
    # the low building south of the court, its flat roof under two rows of solar panels
    with on_land(part):
        prism(part, [(68.5, -104.7), (84.3, -104.7), (84.3, -97.8), (68.5, -97.8)], 0.0, 3.5, "render_white", top="roof_grey")
        for yy in (-99.9, -102.6):
            obox(part, (76.4, yy), 0.0, 14.4, 1.9, 3.6, 3.68, "window_dark", top="window_dark")
    # the tennis court (Google Earth top-down: its green x 66.05-82.35, y -66.8 to -97.8) with its lines
    # (white strips a few millimetres proud) and its fence
    with on_land(part, level=float(T.height(74.2, -82.3))):   # the court is level, cut into the slope
        CX, CY = 74.2, -82.3
        obox(part, (CX, CY), math.pi / 2, 31.0, 16.3, 0.0, 0.04, "court_surround", top="court_surround")
        obox(part, (CX, CY), math.pi / 2, 23.77, 10.97, 0.04, 0.05, "court_green", top="court_green")
        for dx in (-5.485, -4.115, 4.115, 5.485):
            box3(part, V(CX + dx, CY - 11.885, 0.05), V(CX + dx, CY + 11.885, 0.05), 0.05, 0.006, "paint_white")
        for dy in (-11.885, -6.4, 6.4, 11.885):
            box3(part, V(CX - 5.485, CY + dy, 0.05), V(CX + 5.485, CY + dy, 0.05), 0.05, 0.006, "paint_white")
        box3(part, V(CX, CY - 6.4, 0.05), V(CX, CY + 6.4, 0.05), 0.05, 0.006, "paint_white")
        box3(part, V(CX - 7.0, CY, 1.07), V(CX + 7.0, CY, 1.07), 0.04, 0.04, "steel_dark")   # the net
        X0, X1, Y0, Y1 = CX - 8.15, CX + 8.15, CY - 15.5, CY + 15.5
        for (x0, y0), (x1, y1) in (((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, Y1)), ((X1, Y1), (X0, Y1)), ((X0, Y1), (X0, Y0))):
            L = math.hypot(x1 - x0, y1 - y0)
            for t in np.arange(0.0, L + 0.01, 3.0):
                x, y = x0 + (x1 - x0) * t / L, y0 + (y1 - y0) * t / L
                box3(part, V(x, y, 0.0), V(x, y, 3.0), 0.06, 0.06, "steel_dark")
            box3(part, V(x0, y0, 3.0), V(x1, y1, 3.0), 0.05, 0.05, "steel_dark")


def build():
    # each on the real land (land.py): the row's houses one by one, the rest as the groups they stand in
    townhouses()
    for fn, part in ((big_house, P + "_house_e"), (shed, P + "_shed"), (villa_37, P + "_villa37"),
                     (villa_ne, P + "_villa_ne"), (townhouses_ne, P + "_ne43")):
        with on_land(part):
            fn()
    south_east()
    return {}
