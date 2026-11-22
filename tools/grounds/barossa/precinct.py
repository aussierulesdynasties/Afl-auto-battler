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
COL = {
    GRASS: (104, 128, 66), VERGE: (96, 124, 60), ASPHALT: (70, 71, 74), CONCRETE: (200, 196, 186), PATH: (186, 180, 168),
    NETBALL: (38, 74, 140), TENNIS: (40, 78, 136), MULCH: (104, 80, 58), BALLAST: (128, 114, 98), DRY: (176, 156, 110),
    PARKING: (78, 79, 82), BOWLS: (150, 140, 104), OVAL2: (100, 132, 62), SAND: (196, 176, 140),
}

# Hand traced on the mosaic (plan E, N).
POLYS = [
    # second oval's surround and the land west of the courts are grass
    (GRASS, [(-180, 25), (-180, 180), (-125, 180), (-125, 80), (-110, 78), (-108, 25)]),
    # tennis courts (six) and their apron
    (CONCRETE, [(-178, 22), (-178, 80), (-104, 80), (-104, 22)]),
    (TENNIS, [(-175, 26), (-175, 75), (-108, 75), (-108, 26)]),
    # netball courts (four, two blocks)
    (CONCRETE, [(-116, 83), (-116, 163), (-60, 163), (-60, 83)]),
    (NETBALL, [(-112, 85.5), (-112, 159), (-63, 160), (-63, 85.5)]),
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
    cls = np.full(E.shape, GRASS, np.uint8)
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
    # court lines: netball (two courts a block, 30.5 x 15.25) and tennis (23.77 x 10.97, six)
    for cx, cy in ((-99.5, 104.0), (-75.5, 104.0), (-99.5, 141.0), (-75.5, 141.0)):
        _rect(d, P, cx, cy, 15.25, 30.5, white)
        d.line([P((cx - 7.6, cy - 5.08)), P((cx + 7.6, cy - 5.08))], fill=white, width=1)
        d.line([P((cx - 7.6, cy + 5.08)), P((cx + 7.6, cy + 5.08))], fill=white, width=1)
        for s in (-1, 1):
            d.arc([P((cx - 4.9, cy + s * 15.25 + 4.9)), P((cx + 4.9, cy + s * 15.25 - 4.9))], 0, 360, fill=white)
    for k in range(6):
        cx = -167.0 + k * 11.6
        _rect(d, P, cx, 50.5, 10.97, 23.77, white)
        _rect(d, P, cx, 50.5, 8.23, 23.77, white)
        d.line([P((cx - 4.1, 50.5 - 6.4)), P((cx + 4.1, 50.5 - 6.4))], fill=white, width=1)
        d.line([P((cx - 4.1, 50.5 + 6.4)), P((cx + 4.1, 50.5 + 6.4))], fill=white, width=1)
        d.line([P((cx, 50.5 - 6.4)), P((cx, 50.5 + 6.4))], fill=white, width=1)
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


def _rect(d, P, cx, cy, w, h, col):
    d.rectangle([P((cx - w / 2, cy + h / 2)), P((cx + w / 2, cy - h / 2))], outline=col)


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
