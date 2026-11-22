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


def townhouses():
    """Six two-storey townhouses in a row (Google Earth e_270): orange-red brick, white-trimmed sash windows
    two to a floor on the gable end facing the ground, grey Colorbond gables, a low wing at the back."""
    ys = [-14.5, -23.9, -33.3, -42.7, -52.1]
    for k, y in enumerate(ys):
        part = P + "_terrace"
        gable_building(part, (80.5, y), 0.0, 13.0, 8.8, 6.0, 8.9, "brick_terrace", "roof_pale", over=0.35,
                       windows=[(1.1, 1.0, 2.6, 4.2), (1.1, 3.9, 5.4, 4.2)], gable_mat="brick_terrace")
        gable_building(part, (89.6, y + 1.2), 0.0, 5.2, 5.0, 3.0, 4.6, "brick_terrace", "roof_pale", over=0.3,
                       windows=(1.0, 0.9, 2.2, 2.4))
        chimney(part, (85.8, y + 4.0), 7.0, 10.0)
        # party walls stand proud of the roof between the houses
        if k:
            yy = y + 4.7
            obox(part, (80.5, yy), 0.0, 13.6, 0.36, 6.0, 7.3, "brick_terrace", top="render_cream")
        # small timber deck and steps on the ground side
        obox(part, (73.2, y), 0.0, 1.6, 3.2, 0.0, 0.5, "timber_dark", top="timber_dark")
    # the south end house, set back and lower (top-down tile: x 70-80, y -57 to -66)
    gable_building(P + "_terrace", (75.5, -61.5), math.pi / 2, 8.5, 9.0, 5.8, 8.4, "brick_terrace", "roof_pale",
                   over=0.35, windows=[(1.1, 1.0, 2.6, 3.6), (1.1, 3.9, 5.4, 3.6)], gable_mat="brick_terrace")
    # the jacarandas' bed and the low brick wall in front of the row (between the terrace walk and the houses)
    for y0, y1 in ((-10.0, -58.0),):
        box3(P + "_terrace", V(71.0, y0, 0.0), V(71.0, y1, 0.0), 0.3, 0.9, "brick_terrace")


def big_house():
    """Behind the row: a two-storey brick house under a big grey hipped roof with chimneys, and its south wing."""
    part = P + "_house_e"
    gable_building(part, (110.5, -30.0), math.pi / 2, 36.0, 20.0, 7.2, 11.2, "brick_terrace", "roof_slate_grey",
                   over=0.5, windows=[(1.3, 1.1, 3.0, 3.6), (1.3, 4.3, 6.2, 3.6)], hip=True)
    for y in (-18.0, -27.0, -36.0, -44.0):
        chimney(part, (106.0, y), 9.0, 12.6)
    gable_building(part, (110.0, -51.5), 0.0, 22.0, 8.0, 3.4, 5.4, "brick_terrace", "roof_slate_grey", over=0.4,
                   windows=(1.2, 1.0, 2.4, 3.2), hip=True)


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
    """The two-storey red-brick villa at the north-east (e_090): grey hipped roof, two-level verandah facing
    the ground with white posts and balustrade, chimneys."""
    part = P + "_villa_ne"
    gable_building(part, (102.0, 79.0), 0.0, 23.0, 15.0, 7.4, 11.0, "brick_terrace", "roof_slate_grey", over=0.5,
                   windows=[(1.3, 1.1, 3.1, 3.8), (1.3, 4.4, 6.4, 3.8)], hip=True, quoins="render_cream")
    a, b = (90.4, 72.0), (90.4, 86.0)
    verandah(part, b, a, 2.6, 3.5)
    verandah(part, b, a, 2.6, 7.1)
    # the balcony floor and balustrade
    obox(part, (89.1, 79.0), 0.0, 2.6, 14.0, 3.55, 3.75, "timber_white", top="timber_dark", bottom="timber_white")
    box3(part, V(87.9, 72.0, 4.75), V(87.9, 86.0, 4.75), 0.08, 0.08, "timber_white")
    for y in np.arange(72.2, 86.0, 0.16):
        box3(part, V(87.9, y, 3.75), V(87.9, y, 4.75), 0.03, 0.03, "timber_white")
    for y in (74.0, 84.0):
        chimney(part, (106.0, y), 10.0, 12.8)
    gable_building(part, (107.0, 66.5), 0.0, 12.0, 8.0, 3.4, 5.2, "brick_terrace", "roof_slate_grey", over=0.4,
                   windows=(1.2, 1.0, 2.6, 3.2), hip=True)


def townhouses_ne():
    """43: the newer two-storey townhouses at the north-east corner, red brick and grey roofs, gables to the
    ground, solar panels on their north slopes."""
    part = P + "_ne43"
    for k, x in enumerate((60.0, 67.5, 75.0)):
        gable_building(part, (x, 98.0), math.pi / 2, 18.0, 7.2, 6.0, 8.6, "brick_terrace", "roof_slate_grey",
                       over=0.35, windows=[(1.2, 1.0, 2.6, 3.0), (1.2, 3.8, 5.4, 3.0)], gable_mat="render_white")
        # the solar array: a framed panel standing off the roof
        z = 7.0
        obox(part, (x - 1.6, 98.0), math.pi / 2, 9.0, 2.4, z, z + 0.08, "window_dark", top="window_dark")
    gable_building(part, (68.0, 108.0), 0.0, 22.0, 6.0, 5.6, 7.6, "brick_terrace", "roof_slate_grey", over=0.35,
                   windows=[(1.2, 1.0, 2.6, 3.2), (1.2, 3.8, 5.2, 3.2)], hip=True)


def south_east():
    """The south-east block: the big two-storey house with its gables to Osmond Terrace, its pool court,
    the modern house with solar panels and the tennis court beside the ground (top-down tiles)."""
    part = P + "_se"
    gable_building(part, (110.0, -78.0), math.pi / 2, 36.0, 14.0, 6.8, 10.4, "render_cream", "roof_slate_grey",
                   over=0.5, windows=[(1.2, 1.0, 2.8, 3.4), (1.2, 4.0, 5.9, 3.4)], hip=True)
    for y in (-68.0, -80.0, -91.0):
        gable_building(part, (119.5, y), 0.0, 7.0, 6.5, 6.8, 9.8, "render_cream", "roof_slate_grey", over=0.4,
                       windows=[(1.2, 1.0, 2.8, 3.0), (1.2, 4.0, 5.9, 3.0)], gable_mat="render_cream")
    gable_building(part, (96.0, -93.5), 0.0, 22.0, 9.0, 6.4, 9.4, "render_cream", "roof_slate_grey", over=0.4,
                   windows=[(1.2, 1.0, 2.8, 3.2), (1.2, 4.0, 5.6, 3.2)], hip=True)
    # the pool and its paving (the water a hand under the coping)
    obox(part, (94.0, -79.0), 0.0, 16.0, 9.0, 0.0, 0.12, "concrete", top="concrete")
    obox(part, (93.0, -79.5), 0.0, 9.0, 4.4, 0.12, 0.14, "glass_rail", top="glass_rail")
    # the modern house: flat roof, dark frames
    prism(part, [(72.0, -63.0), (91.0, -63.0), (91.0, -76.0), (72.0, -76.0)], 0.0, 6.6, "render_white",
          top="roof_grey")
    for x in (76.0, 83.0):
        obox(part, (x, -69.5), 0.0, 5.0, 8.0, 6.6, 6.72, "window_dark", top="window_dark")
    # the tennis court with its lines (white strips a few millimetres proud) and its fence
    obox(part, (74.5, -85.5), math.pi / 2, 32.0, 14.0, 0.0, 0.04, "court_surround", top="court_surround")
    obox(part, (74.5, -85.5), math.pi / 2, 23.8, 11.0, 0.04, 0.05, "court_green", top="court_green")
    for x in (69.0, 70.4, 78.6, 80.0):
        box3(part, V(x, -97.4, 0.05), V(x, -73.6, 0.05), 0.05, 0.006, "paint_white")
    for y in (-97.4, -91.9, -79.1, -73.6):
        box3(part, V(69.0, y, 0.05), V(80.0, y, 0.05), 0.05, 0.006, "paint_white")
    box3(part, V(74.5, -91.9, 0.05), V(74.5, -79.1, 0.05), 0.05, 0.006, "paint_white")
    box3(part, V(67.5, -85.5, 1.07), V(81.5, -85.5, 1.07), 0.04, 0.04, "steel_dark")   # the net
    for (x0, y0), (x1, y1) in (((67.5, -101.5), (81.5, -101.5)), ((81.5, -101.5), (81.5, -69.5)),
                               ((81.5, -69.5), (67.5, -69.5)), ((67.5, -69.5), (67.5, -101.5))):
        L = math.hypot(x1 - x0, y1 - y0)
        for t in np.arange(0.0, L + 0.01, 3.0):
            x, y = x0 + (x1 - x0) * t / L, y0 + (y1 - y0) * t / L
            box3(part, V(x, y, 0.0), V(x, y, 3.0), 0.06, 0.06, "steel_dark")
        box3(part, V(x0, y0, 3.0), V(x1, y1, 3.0), 0.05, 0.05, "steel_dark")


def build():
    townhouses()
    big_house()
    shed()
    villa_37()
    villa_ne()
    townhouses_ne()
    south_east()
    return {}
