# The bowl's plan as it was in 1990, read off the GA survey vertical (AUS/C236 frame 280, 10 May 1990, CC BY 4.0),
# registered at 0.25 m/px, north up ("src90"). Plan only; heights still come from ref46 (gen2's rim trace).
# Each ring is given as metres outward from the photo fence (g) at keypoint bearings, read on fence-relative unrolled
# strips of the photo sampled at ground level; a ring at height z is then moved for the survey camera's lean.
import math
import numpy as np

CX, CY = 20.972, 39.995
# model -> src90 pixel transform (rotation about cq, then shift), and the survey camera's lean: a point at height h
# shows at C + (P - C) * HC / (HC - h)
FIT = [-56.488560482758935, 132.598953472487, 1.505898093999361, 1075.8266735858847, 849.6165023352361]
HALF = 250.0; CL = np.array([-440.0, 240.0]); HC = 2000.0
_th = math.radians(FIT[2]); _R = np.array([[math.cos(_th), -math.sin(_th)], [math.sin(_th), math.cos(_th)]]); _cq = np.array(FIT[3:5])


def m2px(x, h=0.0):
    x = np.atleast_2d(np.asarray(x, float)); h = np.broadcast_to(np.asarray(h, float), (len(x),))[:, None]
    xs = CL + (x - CL) * HC / (HC - h); q = np.c_[(xs[:, 0] + HALF) / 0.25 - 0.5, (HALF - xs[:, 1]) / 0.25 - 0.5]
    return (_R @ (q - _cq).T).T + _cq + FIT[:2]


def px2m(p, h=0.0):
    p = np.atleast_2d(np.asarray(p, float)); q = (_R.T @ (p - _cq - FIT[:2]).T).T + _cq
    xs = np.c_[-HALF + (q[:, 0] + 0.5) * 0.25, HALF - (q[:, 1] + 0.5) * 0.25]; h = np.broadcast_to(np.asarray(h, float), (len(p),))[:, None]
    return CL + (xs - CL) * (HC - h) / HC


# photo fence: the field-grass edge, fitted as radius against polar angle (8 harmonics, residual median 0.24 m)
FOURIER = [80.42995091743913, -0.492261890378746, -1.0252314590091502, -7.336845107250339, 16.385499716868733, 1.2298147648800877,
           -0.4854195265868438, -0.006382352300576077, -0.35100155559291424, -0.2712147081453594, -0.3120423855006314, -0.8487734502953725,
           0.18580648511060852, 0.22586544456168636, 0.15640841450228518, 0.013836420458944693, 0.24885244609255733]


def r_grass(t):
    t = np.atleast_1d(np.asarray(t, float)); B = [np.ones_like(t)]
    for k in range(1, 9): B += [np.cos(k * t), np.sin(k * t)]
    return np.stack(B, 1) @ np.array(FOURIER)


# on the north and east the morning sun puts the fence's shadow on the grass, so the grass edge stops short of the
# fence; there the fence is the pale wall-top line, this far beyond the grass edge (m, read per 5 degrees)
PALE = [(0, 0.0), (5, 0.6), (10, 1.31), (15, 2.06), (20, 2.44), (25, 2.75), (30, 2.94), (35, 3.06), (40, 2.88), (45, 2.88),
        (50, 2.95), (55, 3.03), (60, 3.12), (65, 3.12), (70, 3.31), (75, 3.12), (80, 2.94), (85, 2.56), (90, 2.0), (95, 1.5),
        (100, 1.19), (105, 0.8), (110, 0.4), (115, 0.0)]


def pale(bdeg):
    return np.interp(bdeg, [a for a, _ in PALE], [b for _, b in PALE], left=0.0, right=0.0)


# keypoints: bearing (model polar degrees, 0 = east, 90 = north) -> g (m beyond the grass edge) of
# apron end, seat/bank toe, walkway a, walkway b, rim inner edge, rim outer edge, outer foot, gravel end, path end
COLS = ('toe_a', 'toe', 'walk_a', 'walk_b', 'top_in', 'top_out', 'foot', 'path_out', 'conc_out')
KP = [
    # north (re-read on unrolled strips, 2026-11-19): lower tier front -> 13.5 m all along; from the stand to 91 deg a
    # pale cross walkway 13.5 -> 15 m and an upper tier to 19 m; from 90 deg the upper tier is a sliver to 82 deg, then
    # only the pale rim behind the lower tier
    (112, 0.8, 1.2, 13.5, 15.0, 19.0, 21.0, 24.0, 28.0, 33.0),
    (104, 1.4, 1.8, 13.5, 15.0, 19.0, 21.5, 25.5, 29.5, 34.0),
    (91.5, 3.2, 3.6, 13.5, 15.0, 19.0, 21.5, 25.5, 29.5, 34.0),
    (90.5, 3.3, 3.7, 13.5, 15.0, 16.3, 18.5, 22.5, 26.5, 31.0),
    (82, 3.4, 3.8, 13.5, 15.0, 15.4, 18.0, 22.0, 26.0, 31.0),
    (70, 3.6, 4.0, 13.5, 14.0, 14.4, 17.0, 21.0, 25.0, 30.0),
    # north-east to east: grass bank from the fence, pale rim walkway, terracotta gravel, pale path
    (66, 3.6, 4.0, 8.5, 9.5, 13.5, 16.5, 20.0, 24.0, 28.0),
    (58, 3.5, 3.9, 9.0, 10.0, 15.0, 20.0, 23.0, 30.0, 34.0),
    (32, 3.3, 3.7, 9.5, 10.5, 15.5, 20.0, 23.0, 30.0, 34.0),
    (26, 3.1, 3.5, 11.0, 12.0, 19.0, 24.0, 27.0, 33.0, 37.0),
    (14, 2.4, 2.8, 12.0, 13.0, 21.0, 25.0, 28.0, 34.0, 38.0),
    (6, 1.4, 1.8, 12.5, 13.5, 22.0, 26.0, 29.0, 35.0, 39.0),
    # south-east seats: grass apron, pale front walkway, terracotta seats, pale rim, grey concourse, gravel, path
    (3, 10.0, 14.5, 21.0, 21.5, 26.5, 29.5, 33.5, 38.0, 43.0),
    (-2, 10.5, 14.5, 21.5, 22.0, 29.0, 32.0, 36.0, 40.0, 44.0),
    (-30, 11.0, 15.0, 22.0, 22.5, 30.0, 34.0, 38.0, 42.0, 46.0),
    (-46, 12.0, 16.0, 23.5, 24.0, 32.0, 35.5, 39.0, 43.5, 48.0),
    (-56, 13.0, 17.0, 24.5, 25.0, 32.5, 36.0, 40.0, 44.5, 49.0),
    (-66, 15.0, 19.0, 25.5, 26.0, 33.0, 36.0, 40.0, 44.5, 49.0),
    # south: grass bank behind a 5 m pale apron; its top edge runs diagonally out towards the south-east seats;
    # gravel then the pale path end 33-35 m and 37-39 m out (re-read 2026-11-19), a lawn instead of gravel past -113
    (-71, 5.0, 6.0, 17.5, 18.5, 30.5, 34.5, 36.5, 40.0, 45.0),
    (-80, 5.0, 6.0, 16.5, 17.5, 28.0, 32.0, 33.5, 35.5, 39.0),
    (-88, 5.0, 6.0, 15.0, 16.0, 25.0, 29.0, 30.5, 33.0, 37.0),
    (-94, 5.0, 6.0, 14.0, 15.0, 22.5, 27.0, 28.5, 33.5, 37.0),
    (-110, 5.0, 6.0, 12.5, 13.5, 20.0, 23.0, 24.5, 34.5, 37.5),
    (-120, 5.0, 6.0, 12.0, 13.0, 19.0, 22.0, 23.5, 34.0, 37.0),
    (-130, 5.0, 6.0, 11.5, 12.5, 18.0, 20.0, 22.0, 30.0, 33.0),
    # south-west (re-read 2026-11-19): to -147.5 a pale apron to 3.6 m, one tier 4.2 -> 14.5 m, pale rim to 17.5 m;
    # a concrete vomitory block -147.5 .. -154; then seats 1.5 -> 14 m, a pale walkway to 16.5 m, an upper tier to 20.5 m
    (-132, 3.6, 4.2, 8.0, 9.0, 14.5, 17.5, 19.5, 24.0, 27.0),
    (-147.5, 3.6, 4.2, 8.0, 9.0, 14.5, 17.5, 19.5, 24.0, 27.0),
    (-154, 0.9, 1.5, 14.0, 16.5, 20.5, 22.0, 24.0, 27.0, 30.0),
    (-180, 0.9, 1.5, 14.0, 16.5, 20.5, 22.0, 24.0, 27.0, 30.0),
]


def sector(bdeg):
    """what each part of the bowl is, by bearing"""
    b = np.asarray(bdeg, float)
    return np.where(b > 68, 'N', np.where(b > 4, 'E', np.where(b > -70.5, 'SE', np.where(b > -131, 'S', 'SW'))))


def walkway(bdeg):
    """a pale cross walkway between two seat tiers: all the north stand, south-west beyond -151"""
    b = np.asarray(bdeg, float); return (b > 68) | (b < -151)


def block(bdeg):
    """the concrete vomitory block in the south-west seats"""
    b = np.asarray(bdeg, float); return (b > -154.5) & (b < -147.0)


def gsmooth(a, sig):
    a = np.asarray(a, float); h = int(3 * sig); k = np.exp(-0.5 * (np.arange(-h, h + 1) / sig) ** 2); k /= k.sum()
    return np.convolve(np.pad(a, h, mode='edge'), k, mode='valid')


def rings(TH, z):
    """TH: ray angles (radians); z: dict ring -> heights per ray. Returns dict ring -> radius per ray (m from centre)."""
    bd = np.degrees(np.asarray(TH, float)); bd = (bd + 180) % 360 - 180
    kb = np.array([k[0] for k in KP], float); o = np.argsort(kb)
    rg = r_grass(np.asarray(TH, float)); u = np.c_[np.cos(TH), np.sin(TH)]
    out = {'fence': rg + pale(bd)}
    for j, name in enumerate(COLS):
        g = np.interp(bd, kb[o], np.array([k[j + 1] for k in KP], float)[o])
        g = gsmooth(g, 1.2)
        r0 = rg + g
        # lean: where the photo shows a ring point at height h, the point itself sits nearer the survey camera
        zz = np.broadcast_to(np.asarray(z.get(name, 0.0), float), r0.shape)
        P0 = np.c_[CX + r0 * u[:, 0], CY + r0 * u[:, 1]]
        P1 = px2m(m2px(P0, 0.0), zz)
        out[name] = r0 + np.sum((P1 - P0) * u, 1)
    # keep every ring at least 0.4 m beyond the one before it (fence first)
    prev = out['fence']
    for name in COLS:
        out[name] = np.maximum(out[name], prev + 0.4); prev = out[name]
    return out
