"""The ground of Barossa Park's precinct, 360 m a side round the fence: what each square metre is (grass, ring road,
concourse, car parks, courts, garden beds, the old railway's ballast) and how high it lies.

Surfaces are painted into one map (0.176 m a pixel, painted in code: colours, bay lines and court lines, no photo
pixels). Heights are the designed levels near the field (the arena, the ring road, the concourse, the upper level the
terraces climb to, the courts' pads) blended out into the Terrarium heights of the land round it.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import oval2
import paint
from plan import RING, interp, club, FIELD_ASL, offsets, polar

HALF = 180.0
PX = 2048
MPP = 2 * HALF / PX

# surface classes
GRASS, VERGE, ASPHALT, CONCRETE, PATH, NETBALL, TENNIS, MULCH, BALLAST, DRY, PARKING, BOWLS, OVAL2, SAND = range(14)
OPEN = 14   # ground no trace covers: painted as the land round it (land.paint_ground)
COL = {
    GRASS: (104, 128, 66), VERGE: (96, 124, 60), ASPHALT: (70, 71, 74), CONCRETE: (200, 196, 186), PATH: (186, 180, 168),
    NETBALL: (38, 74, 140), TENNIS: (40, 78, 136), MULCH: (104, 80, 58), BALLAST: (128, 114, 98), DRY: (176, 156, 110),
    PARKING: (78, 79, 82), BOWLS: (150, 140, 104), OVAL2: (100, 132, 62), SAND: (196, 176, 140),
}

# The courts, fitted on the satellite's court lines (z18, a line template slid and turned over the top-hat image:
# tools/grounds/barossa/README.md): centre (E, N) and the bearing of the long axis (degrees, east of north). Four
# tennis courts west of the clubrooms; four netball courts in two blocks to the north, the north block's also lined
# for two tennis courts.
TENNIS_COURTS = [(-162.75, 48.75, -3.25), (-145.38, 50.25, -3.5), (-131.12, 51.5, -3.25), (-116.98, 52.88, -3.25)]
NETBALL_COURTS = [(-93.38, 101.12, -3.5), (-74.38, 102.62, -3.5), (-99.88, 134.5, -3.75), (-73.12, 136.62, -4.25)]
MULTI_TENNIS = [(-96.5, 136.0, -3.75), (-77.0, 137.6, -3.75)]   # the tennis lines over the north netball block


def turned(cx, cy, pts, bearing):
    """points (across, along) of a court-frame shape -> plan (E, N), the along axis at the bearing"""
    c, s = math.cos(math.radians(bearing)), math.sin(math.radians(bearing))
    return [(cx + x * c + y * s, cy - x * s + y * c) for x, y in pts]


def box(cx, cy, hw, hh, bearing):
    return turned(cx, cy, [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)], bearing)


# the court surfaces (dark edges on the satellite) and the fences round them, in the courts' own frame
TENNIS_SURFACE = (-139.6, 48.0, 33.4, 19.0, -3.3)
NETBALL_NORTH = (-87.2, 138.2, 22.6, 16.8, -3.8)
NETBALL_SOUTH = (-84.6, 101.8, 22.1, 16.6, -3.5)

def court_lines():
    """every court line as a plan polyline (points, closed): netball 30.5 x 15.25 with thirds, the centre circle
    and the 4.9 m goal circles; tennis 23.77 x 10.97 doubles, singles, service and centre service lines"""
    out = []
    for cx, cy, br in NETBALL_COURTS:
        out.append((box(cx, cy, 7.625, 15.25, br), True))
        for sgn in (-1, 1):
            out.append((turned(cx, cy, [(-7.625, sgn * 5.083), (7.625, sgn * 5.083)], br), False))
            t = np.linspace(0, math.pi, 33)
            out.append((turned(cx, cy, [(4.9 * math.cos(x), sgn * (15.25 - 4.9 * math.sin(x))) for x in t], br), False))
        t = np.linspace(0, 2 * math.pi, 25)[:-1]
        out.append((turned(cx, cy, [(0.45 * math.cos(x), 0.45 * math.sin(x)) for x in t], br), True))
    for cx, cy, br in TENNIS_COURTS + MULTI_TENNIS:
        out.append((box(cx, cy, 5.485, 11.885, br), True))
        for sgn in (-1, 1):
            out.append((turned(cx, cy, [(sgn * 4.115, -11.885), (sgn * 4.115, 11.885)], br), False))
            out.append((turned(cx, cy, [(-4.115, sgn * 6.4), (4.115, sgn * 6.4)], br), False))
            out.append((turned(cx, cy, [(0, sgn * 11.885), (0, sgn * 11.785)], br), False))   # centre mark
        out.append((turned(cx, cy, [(0, -6.4), (0, 6.4)], br), False))
    return out


SURFACES = {"court_tennis": (TENNIS_SURFACE, TENNIS), "court_netball_s": (NETBALL_SOUTH, NETBALL),
            "court_netball_n": (NETBALL_NORTH, NETBALL)}
COURT_MPP = 0.04          # the court textures: 4 cm a pixel, lines drawn 4x finer and averaged down


def paint_court(key):
    """one court surface's own texture, in its own frame (u across from its west side, v along from its north end):
    the acrylic colour with a faint mottle and every court line on it, 50 mm wide"""
    (cx, cy, hw, hh, br), cls = SURFACES[key]
    W, H = int(round(2 * hw / COURT_MPP)), int(round(2 * hh / COURT_MPP))
    ss = 4
    c, s_ = math.cos(math.radians(br)), math.sin(math.radians(br))
    def frame(p):      # plan -> court frame (across, along)
        de, dn = p[0] - cx, p[1] - cy
        return de * c - dn * s_, de * s_ + dn * c
    im = Image.new("L", (W * ss, H * ss), 0)
    d = ImageDraw.Draw(im)
    px = lambda q: ((q[0] + hw) / COURT_MPP * ss, (hh - q[1]) / COURT_MPP * ss)
    lw = max(1, int(round(0.05 / COURT_MPP * ss)))
    for pts, closed in court_lines():
        f = [px(frame(p)) for p in pts]
        if closed:
            f = f + f[:1]
        d.line(f, fill=255, width=lw, joint="curve")
    line = np.asarray(im.resize((W, H), Image.BOX), np.float32)[..., None] / 255.0
    base = np.array(COL[cls], np.float32)
    n1 = paint.fbm(H, W, 707, (6, 18, 54), (0.5, 0.3, 0.2))
    col = base * (0.95 + 0.08 * n1)[..., None]
    out = col * (1 - line) + np.array((228, 230, 226), np.float32) * line
    return np.clip(out, 0, 255).astype(np.uint8)


# Hand traced on the mosaic (plan E, N).
POLYS = [
    # second oval's surround and the land west of the courts are grass
    (GRASS, [(-180, 25), (-180, 180), (-125, 180), (-125, 80), (-110, 78), (-108, 25)]),
    # tennis courts (four) and their apron
    (CONCRETE, [(-178, 22), (-178, 80), (-104, 80), (-104, 22)]),
    (TENNIS, box(*TENNIS_SURFACE)),
    # netball courts (four, two blocks)
    (CONCRETE, [(-116, 83), (-116, 163), (-60, 163), (-60, 83)]),
    (NETBALL, box(*NETBALL_SOUTH)),
    (NETBALL, box(*NETBALL_NORTH)),
    # court pavilion apron and the playground
    (CONCRETE, [(-131, 124), (-131, 162), (-113, 162), (-113, 124)]),
    (MULCH, [(-152, 84), (-148, 118), (-120, 122), (-114, 100), (-118, 84)]),
    # north car park and its road out to Barossa Valley Way
    (PARKING, [(-63, 84), (-63, 130), (-50, 143), (-30, 150), (-8, 146), (-14, 132), (-28, 118), (-36, 104), (-34, 92), (-46, 86)]),
    (ASPHALT, [(-14, 132), (-8, 146), (4, 150), (12, 142), (0, 126)]),
    # west car park (round the shed and the water tanks), and the upper road behind the terraces
    (PARKING, [(-172, 24), (-104, 24), (-96, 6), (-92, -14), (-116, -20), (-150, -2), (-174, 12)]),
    # south-east car park and the bowls club's
    (PARKING, [(48, -78), (72, -66), (122, -58), (128, -84), (88, -96), (58, -96)]),
    (BOWLS, [(52, -96), (88, -84), (100, -120), (64, -132)]),
    (BOWLS, [(92, -122), (130, -110), (142, -146), (104, -160)]),
    # Barossa Valley Way's verge and the paddock across it is dry grass (drawn by land.py past the precinct)
]

# Paths (plan polyline, width): the crossing and the park's loop to the east, the path along the south.
PATHS = [
    ([(68, -22), (90, -20), (110, -17), (126, -14)], 2.6),
    ([(76, 8), (92, 14), (108, 14), (120, 8), (126, -6)], 2.4),
    ([(76, -64), (90, -55), (108, -44), (124, -24)], 2.4),
]

# Bay lines: (start, end, count, bay depth) painted along a kerb line
BAYS = [
    ((-62, 90), (-62, 126), 14, 5.2),
    ((-45, 104), (-24, 140), 14, 5.2),
    ((-52, 110), (-36, 136), 11, -5.2),
]


def classify():
    """surface class per pixel (row 0 is the north edge)"""
    e = (np.arange(PX) + 0.5) * MPP - HALF
    n = HALF - (np.arange(PX) + 0.5) * MPP
    E, N = np.meshgrid(e, n)
    # every ring is an exact offset of the fence: distance square to it, and the bearing of its foot
    b, off = offsets(E, N)
    ring = np.array([interp(RING, x) for x in np.arange(0, 360.5, 0.5)])
    k = np.clip((b * 2).astype(int), 0, 720)
    verge, road0, road1, conc = ring[k, 0], ring[k, 1], ring[k, 2], ring[k, 3]
    cls = np.full(E.shape, OPEN, np.uint8)
    cls[off < 0] = GRASS
    cls[(off >= 0) & (off < verge)] = VERGE
    cls[(off >= road0) & (off < road1)] = ASPHALT
    w = conc > 0.5
    cls[w & (off >= 0) & (off < conc)] = CONCRETE
    # the concourse widens to the buildings on the west: concrete to the clubrooms' and pavilion's fronts
    west = (b > 236) & (b < 318) & (off >= 0) & (off < 26)
    cls[west] = CONCRETE
    # the path along the top of the south-west grass verge (inside the retaining wall)
    sw = (b > 175) & (b < 238) & (off >= road0 - 2.0) & (off < road0)
    cls[sw] = PATH
    im = Image.fromarray(cls)
    d = ImageDraw.Draw(im)
    P = lambda p: ((p[0] + HALF) / MPP, (HALF - p[1]) / MPP)
    for c, poly in POLYS:
        d.polygon([P(p) for p in poly], fill=int(c))
    for pts, wd in PATHS:
        d.line([P(p) for p in pts], fill=int(PATH), width=max(1, int(wd / MPP)), joint="curve")
    cls = np.array(im)
    # keep the arena grass inside the fence whatever the polygons say
    cls[off < 0] = GRASS
    return cls, E, N, b, off


def paint_map(cls):
    out = np.zeros(cls.shape + (3,), np.float32)
    for c, col in COL.items():
        out[cls == c] = col
    # open ground takes the land's own colours (OpenStreetMap land use, the satellite's wooded and watered shares),
    # so the precinct's square edge does not show against the land texture past it
    import land
    op = cls == OPEN
    if op.any():
        out[op] = land.ground_window(HALF, PX)[op]
    # the second oval's turf, mowing and path (oval2.py), over the grass the polygons gave it
    e = (np.arange(PX) + 0.5) * MPP - HALF
    E, N = np.meshgrid(e, -e)
    oval2.paint(out, E, N, COL[GRASS])
    # broad mottle and fine grain so no surface reads as flat colour
    n1 = paint.fbm(PX, PX, 101, (8, 24, 64, 160), (0.35, 0.3, 0.2, 0.15))
    n2 = paint.fbm(PX, PX, 202, (256, 512, 1024, 2048), (0.25, 0.25, 0.25, 0.25))
    out *= (0.88 + 0.16 * n1 + 0.08 * (n2 - 0.5))[..., None]
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    P = lambda p: ((p[0] + HALF) / MPP, (HALF - p[1]) / MPP)
    white = (226, 226, 220)
    # parking bays
    for a, b, cnt, depth in BAYS:
        a, b = np.array(a, float), np.array(b, float)
        u = (b - a) / cnt
        nrm = np.array((-u[1], u[0])) / np.linalg.norm(u) * depth
        for i in range(cnt + 1):
            p = a + u * i
            d.line([P(p), P(p + nrm)], fill=white, width=1)
    # court lines live on the courts' own textures (paint_court, laid by build.py)
    # ring road centre line (broken)
    for bb in np.arange(0, 236, 1.0):
        if int(bb) % 3:
            continue
        v, r0, r1, c = interp(RING, bb)
        rm = (r0 + r1) / 2
        p0 = _pol(bb, rm)
        p1 = _pol(bb + 0.9, rm)
        d.line([P(p0), P(p1)], fill=(214, 210, 190), width=1)
    im = im.filter(ImageFilter.GaussianBlur(0.35))
    return np.array(im)


def _pol(b, off):
    return polar(b, off)


# ------------------------------------------------------------------ heights

def upper_level(b):
    """the level of the ring road / upper concourse outside the south-west retaining wall"""
    return interp([(170, 0.15), (195, 1.4), (215, 2.6), (240, 3.0), (275, 3.0), (282, 0.25), (330, 0.25), (340, 0.15)], b)[0]


def design(E, N, b, off, dem):
    """designed level near the field and the weight of the land's own height outside it"""
    ring = np.array([interp(RING, x) for x in np.arange(0, 360.5, 0.5)])
    k = np.clip((b * 2).astype(int), 0, 720)
    road1 = np.maximum(ring[k, 2], ring[k, 3])
    up = np.array([upper_level(x) for x in np.arange(0, 360.5, 0.5)])[k]
    h = np.where(off < 0, 0.0, 0.15)
    sw = (b > 172) & (b < 238)
    # inside the south-west wall the verge rises gently; the road beyond sits at the upper level
    h = np.where(sw & (off >= 0) & (off < road1 - 7.0), 0.15 + 0.06 * np.clip(off, 0, 12), h)
    h = np.where(sw & (off >= road1 - 7.0), up, h)
    west = (b >= 238) & (b < 282)
    h = np.where(west & (off >= 26.0), up, h)
    # pads: courts and the west car park
    flat = 14.0 + np.where((b > 238) & (b < 340), 12.0, 0.0)
    w = np.clip((off - road1 - flat) / 30.0, 0, 1)
    w = w * w * (3 - 2 * w)
    land = dem - FIELD_ASL
    return h * (1 - w) + land * w, w
