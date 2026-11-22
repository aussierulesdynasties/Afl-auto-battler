"""Barossa Park's plan, traced on the 2026 Google satellite mosaic (0.25 m a pixel) and set against the reference
photos (README). Plan coordinates are (E, N) in metres from the boundary fence's centre, lat -34.5984014,
lon 138.8858792; heights are metres above the arena (181 m above sea level by the Terrarium heights).
"""
import math

import numpy as np

LAT0, LON0 = -34.5984014, 138.8858792
FIELD_ASL = 181.0

# Boundary fence: centre (E, N), half axes and rotation (counter-clockwise from east, the long axis 17.3 degrees west
# of north). Fitted (robust least squares, distance to the curve) to the grass edge traced on every half degree of
# the 2026 Google mosaic at 0.2 m a pixel (work/z20.png): 644 of 718 traced points within 1 m (the rest are
# shadows and stands over the edge), rms 0.31 m, 95% within 0.57 m. The same ellipse as GroundModels.FIT["barossa"].
FENCE = (0.163, -0.467, 65.766, 86.139, 17.284)


def _frame():
    fx, fy, a1, a2, rot = FENCE
    t = math.radians(rot)
    return fx, fy, a1, a2, math.cos(t), math.sin(t)


def fence_r(b):
    """distance from the plan origin to the fence along compass bearing b (degrees)"""
    fx, fy, a1, a2, c, s = _frame()
    d = (math.sin(math.radians(b)), math.cos(math.radians(b)))
    o = (-fx, -fy)
    u0 = (c * o[0] + s * o[1], -s * o[0] + c * o[1])
    ud = (c * d[0] + s * d[1], -s * d[0] + c * d[1])
    A = (ud[0] / a1) ** 2 + (ud[1] / a2) ** 2
    B = 2 * (u0[0] * ud[0] / a1 ** 2 + u0[1] * ud[1] / a2 ** 2)
    C = (u0[0] / a1) ** 2 + (u0[1] / a2) ** 2 - 1
    return (-B + math.sqrt(B * B - 4 * A * C)) / (2 * A)


def fence_normal(b):
    """the fence's outward unit normal where the ray at bearing b meets it"""
    fx, fy, a1, a2, c, s = _frame()
    r = fence_r(b)
    e, n = r * math.sin(math.radians(b)) - fx, r * math.cos(math.radians(b)) - fy
    u, v = c * e + s * n, -s * e + c * n
    gu, gv = u / a1 ** 2, v / a2 ** 2
    ge, gn = c * gu - s * gv, s * gu + c * gv
    k = math.hypot(ge, gn)
    return ge / k, gn / k


def polar(b, off):
    """plan point `off` metres outside the fence, square to it (an exact offset of the ellipse), from the fence
    point at bearing b"""
    r = fence_r(b)
    ne, nn = fence_normal(b)
    return (r * math.sin(math.radians(b)) + ne * off, r * math.cos(math.radians(b)) + nn * off)


_FOOT = None


def offsets(E, N):
    """plan points -> (bearing of their foot on the fence, signed distance square to the fence: + outside)"""
    global _FOOT
    from scipy.spatial import cKDTree
    if _FOOT is None:
        bs = np.arange(0.0, 360.0, 0.01)
        F = np.array([[fence_r(x) * math.sin(math.radians(x)), fence_r(x) * math.cos(math.radians(x))] for x in bs])
        Nn = np.array([fence_normal(x) for x in bs])
        _FOOT = (bs, F, Nn, cKDTree(F))
    bs, F, Nn, tree = _FOOT
    q = np.stack([np.ravel(E), np.ravel(N)], 1)
    _, i = tree.query(q)
    off = np.einsum("ij,ij->i", q - F[i], Nn[i])
    return bs[i].reshape(np.shape(E)), off.reshape(np.shape(E))


def bearing(e, n):
    return math.degrees(math.atan2(e, n)) % 360


def interp(table, b):
    """table: [(bearing, value...)...] sorted, wrapping at 360 -> values at b, on a smooth curve through the rows
    (periodic monotone cubic: no kinks at the rows, no overshoot between them)"""
    from scipy.interpolate import PchipInterpolator
    key = id(table)
    if key not in _SPLINES:
        x = [r[0] for r in table]
        y = np.array([r[1:] for r in table], float)
        xs = np.concatenate([[v - 360 for v in x], x, [v + 360 for v in x]])
        ys = np.concatenate([y, y, y])
        _SPLINES[key] = PchipInterpolator(xs, ys, axis=0)
    return list(_SPLINES[key](b % 360))


_SPLINES = {}


# Round the fence, offsets outside it by bearing (from the unwrapped mosaic, every 10-30 degrees):
# grass verge to `verge`, then the ring road from `road0` to `road1` (asphalt), on the west the concourse (concrete)
# instead of verge and road where `conc` > 0.
RING = [
    # bearing, verge, road0, road1, conc; offsets square to the fence (exact offsets of its ellipse). The road's
    # outer edge and the south-west road's inner edge are the asphalt traced on the 0.2 m mosaic unwrapped round the
    # fitted ellipse (Lab colour, median over 6 degrees, tools/grounds/barossa/shape_check.py); the inner edge along
    # the fence (under Gather Round's parked vans and marquees) read where the road shows between them.
    (0, 1.0, 1.0, 9.3, 0),
    (10, 1.0, 1.0, 7.9, 0),
    (20, 1.0, 1.0, 7.4, 0),
    (42, 1.0, 1.0, 7.4, 0),
    (62, 1.0, 1.0, 10.5, 0),
    (80, 1.5, 1.5, 13.0, 0),
    (95, 1.5, 1.5, 13.9, 0),
    (122, 1.5, 1.5, 13.6, 0),
    (130, 3.0, 4.0, 12.6, 0),
    (142, 10.0, 11.0, 21.5, 0),
    (175, 10.5, 11.0, 20.6, 0),
    (186, 12.3, 15.2, 20.0, 0),
    (215, 12.3, 15.4, 19.5, 0),
    (232, 13.3, 15.6, 19.5, 0),
    (237, 0.0, 0.0, 0.0, 9.0),
    (332, 0.0, 0.0, 0.0, 9.0),
    (340, 1.0, 1.0, 4.5, 0),
    (352, 1.0, 1.0, 9.5, 0),
]

# The temporary grandstands of Gather Round 2026, as the satellite caught them (the open stands with blue seats in the
# 2026 match photo): front edge a -> b (plan), rows rising away from the field.
TEMP_STANDS = [
    {"name": "south_west", "a": (-63.5, -72.0), "b": (-44.0, -88.5), "depth": 9.6, "rows": 12},
    {"name": "south", "a": (-38.5, -92.0), "b": (-14.5, -101.0), "depth": 9.6, "rows": 12},
    {"name": "north_east", "a": (54.0, 59.5), "b": (63.5, 42.0), "depth": 10.4, "rows": 13},
]

# Light towers (four, about 40 m, galvanised tapered poles with a frame of LED floods), placed from the satellite's
# leaning poles and their shadows.
TOWERS = [(27.5, 78.5), (-41.0, -80.0), (-56.0, 66.0), (66.0, -42.0)]

# The clubrooms: a frame along the building (u north-north-east, bearing 9 degrees) and across it (v toward the field).
CLUB_O = (-100.5, 28.0)
CLUB_B = 9.0


def club(u, v):
    a = math.radians(CLUB_B)
    ue = (math.sin(a), math.cos(a))
    ve = (math.cos(a), -math.sin(a))
    return (CLUB_O[0] + ue[0] * u + ve[0] * v, CLUB_O[1] + ue[1] * u + ve[1] * v)


def to3(e, n, h=0.0):
    """plan + height -> glTF (x east, y up, z south)"""
    return (e, h, -n)


def dem_height(dem, e, n):
    return float(dem.at_en(np.array([e]), np.array([n]))[0]) - FIELD_ASL
