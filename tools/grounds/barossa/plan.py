"""Barossa Park's plan, traced on the 2026 Google satellite mosaic (0.25 m a pixel) and set against the reference
photos (README). Plan coordinates are (E, N) in metres from the boundary fence's centre, lat -34.5984014,
lon 138.8858792; heights are metres above the arena (181 m above sea level by the Terrarium heights).
"""
import math

import numpy as np

LAT0, LON0 = -34.5984014, 138.8858792
FIELD_ASL = 181.0

# Boundary fence: centre, half axes and rotation (counter-clockwise from east, the long axis 17.3 degrees west of
# north). The same ellipse as GroundModels.FIT["barossa"], which plays the match.
FENCE = (0.0, 0.0, 65.98, 85.63, 17.29)


def fence_r(b):
    """distance from the centre to the fence along compass bearing b (degrees)"""
    fx, fy, a1, a2, rot = FENCE
    t = math.radians(rot)
    a = math.radians(b)
    d = (math.sin(a), math.cos(a))
    c, s = math.cos(t), math.sin(t)
    q = (c * d[0] + s * d[1], -s * d[0] + c * d[1])
    return 1.0 / math.sqrt((q[0] / a1) ** 2 + (q[1] / a2) ** 2)


def polar(b, off):
    """plan point at bearing b, `off` metres outside the fence"""
    r = fence_r(b) + off
    return (r * math.sin(math.radians(b)), r * math.cos(math.radians(b)))


def bearing(e, n):
    return math.degrees(math.atan2(e, n)) % 360


def interp(table, b):
    """table: [(bearing, value...)...] sorted, wrapping at 360 -> interpolated values"""
    b = b % 360
    bs = [r[0] for r in table]
    for k in range(len(table)):
        b0, b1 = table[k][0], table[(k + 1) % len(table)][0]
        span = (b1 - b0) % 360 or 360
        if (b - b0) % 360 <= span:
            f = ((b - b0) % 360) / span
            return [table[k][i] * (1 - f) + table[(k + 1) % len(table)][i] * f for i in range(1, len(table[k]))]
    return list(table[0][1:])


# Round the fence, offsets outside it by bearing (from the unwrapped mosaic, every 10-30 degrees):
# grass verge to `verge`, then the ring road from `road0` to `road1` (asphalt), on the west the concourse (concrete)
# instead of verge and road where `conc` > 0.
RING = [
    # bearing, verge, road0, road1, conc
    (0, 1.4, 1.4, 8.5, 0),
    (30, 1.2, 1.2, 8.0, 0),
    (60, 1.2, 1.2, 9.0, 0),
    (90, 1.5, 1.5, 9.5, 0),
    (120, 1.5, 1.5, 9.5, 0),
    (150, 2.5, 2.5, 13.5, 0),
    (175, 7.0, 8.0, 15.5, 0),
    (200, 9.0, 11.0, 17.0, 0),
    (225, 9.0, 11.0, 18.0, 0),
    (238, 0.0, 0.0, 0.0, 9.0),
    (330, 0.0, 0.0, 0.0, 9.0),
    (338, 1.4, 1.4, 9.0, 0),
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
