"""The second oval, north-west of Barossa Park (the old Lyndoch recreation oval, Gather Round's fan zone): its turf,
the gravel path round it, goal and behind posts at both ends, four training light poles, the three interchange
shelters on the east wing and the cricket nets past the north end.

Traced on the 2026 satellite mosaic (the oval is not in OpenStreetMap): the grass is an ellipse about 157 x 209 m
round (-196.8, 176.6), its long axis 4 degrees west of north (the grass's own centroid and second moments); the
boundary line runs about 8 m inside the grass edge. The light poles stand where their shadows start; the shelters,
nets and path from the mosaic. The 2025 Gather Round photo (from the north-west) shows the same layout.
"""
import math

import numpy as np

C = (-196.8, 176.6)
BEARING = -4.0          # long axis, degrees east of north
GRASS = (78.5, 104.6)   # grass edge, semi axes across and along
FIELD = (71.0, 96.0)    # boundary line
PATH_IN, PATH_W = 2.0, 3.0   # the gravel path: from 2 m outside the grass edge, 3 m wide (west and south sides)
POLES = [(-161.7, 258.3), (-245.0, 261.7), (-221.7, 116.7), (-128.3, 138.3)]
SHELTERS = [(-121.0, 197.0), (-120.5, 184.0), (-120.0, 172.0)]   # interchange shelters, along the boundary
NETS = ((-258.0, 300.0), (-248.0, 258.0))   # cricket nets: west and east lane edges at the north and south ends


def net_texture(size=128, metres=0.5):
    """knotted nylon netting, 50 mm square mesh, the twine drawn 10 mm so it holds up at a distance: an alpha mask (RGBA), `metres` a tile"""
    a = np.zeros((size, size, 4), np.uint8)
    g = (np.arange(size) + 0.5) / size * metres
    line = (g % 0.05) < 0.01
    a[line, :, :] = (34, 40, 36, 255)
    a[:, line, :] = (34, 40, 36, 255)
    return a, metres, metres


def local(e, n):
    """plan -> (across, along) metres in the oval's own frame"""
    a = math.radians(BEARING)
    de, dn = np.asarray(e, float) - C[0], np.asarray(n, float) - C[1]
    along = de * math.sin(a) + dn * math.cos(a)
    across = de * math.cos(a) - dn * math.sin(a)
    return across, along


def plan(across, along):
    a = math.radians(BEARING)
    return (C[0] + across * math.cos(a) + along * math.sin(a), C[1] - across * math.sin(a) + along * math.cos(a))


def stale_vineyard(pts):
    """True for an OpenStreetMap vineyard drawn before the oval was built: one that covers the oval's grass. Its
    vines are gone (the 2026 mosaic shows the oval, its paths and the precinct there), so it is neither painted
    nor planted."""
    from shapely.geometry import Polygon
    poly = Polygon(pts).buffer(0)
    t = np.linspace(0, 2 * math.pi, 48, endpoint=False)
    ell = Polygon([plan(GRASS[0] * math.cos(a), GRASS[1] * math.sin(a)) for a in t])
    return poly.intersection(ell).area > 0.3 * ell.area


def on_oval(e, n, margin=1.1):
    """inside the grass (and its path) of the second oval"""
    x, y = local(e, n)
    return math.hypot(x / GRASS[0], y / GRASS[1]) < margin


def rho(e, n, semi):
    x, y = local(e, n)
    return np.hypot(x / semi[0], y / semi[1])


def paint(img, E, N, base_grass):
    """paint the oval into a texture (H x W x 3 float, sRGB 0-255) whose pixels sit at plan E, N"""
    x, y = local(E, N)
    rg = np.hypot(x / GRASS[0], y / GRASS[1])
    rf = np.hypot(x / FIELD[0], y / FIELD[1])
    grass = rg < 1.0
    turf = np.array((92, 136, 58), float)
    apron = np.array((104, 138, 64), float)
    # mowing: straight bands along the ground through the middle, rings round the outside
    band = (np.floor(x / 7.5) % 2).astype(float)
    ring = (np.floor((1.0 - rf) * 96.0 / 4.5) % 2).astype(float)
    inner = rf < 0.62
    shade = np.where(inner, band, ring)
    col = turf[None, None, :] * (0.94 + 0.1 * shade)[..., None]
    img[grass] = np.where((rf < 1.0)[..., None], col, apron[None, None, :] * np.ones_like(col))[grass]
    # the boundary line
    line = np.abs(rf - 1.0) * min(FIELD) < 0.08
    img[line & grass] = (214, 218, 206)
    # the path (gravel) round the west and south: grass edge + PATH_IN to + PATH_W
    dist = (rg - 1.0) * min(GRASS)
    path = (dist > PATH_IN) & (dist < PATH_IN + PATH_W) & ((x < 0) | (y < -40))
    img[path] = (188, 178, 156)
    return img


def goal_posts(m, h, mat_post, mat_pad):
    """goal and behind posts at both ends on the boundary line: goal posts 6.4 m apart, 12 m tall, behind posts 6.4 m
    outside them, 7 m tall, the lower 2.5 m of each padded"""
    for end in (-1, 1):
        for off, tall in ((-9.6, 7.0), (-3.2, 12.0), (3.2, 12.0), (9.6, 7.0)):
            e, n = plan(off, end * FIELD[1])
            y0 = h(e, n)
            m.tube(mat_post, (e, y0, -n), (e, y0 + tall, -n), 0.06, 0.05, seg=8)
            m.tube(mat_pad, (e, y0, -n), (e, y0 + 2.5, -n), 0.16, 0.16, seg=10)


def light_poles(m, h, mat_steel, mat_lamp):
    """training lights: 22 m galvanised poles, each with a crossarm of four floods aimed at the middle"""
    for e, n in POLES:
        y0 = h(e, n) - 0.3
        top = y0 + 22.0
        m.tube(mat_steel, (e, y0, -n), (e, top, -n), 0.22, 0.11, seg=10)
        # crossarm square to the line to the oval's middle
        d = np.array((C[0] - e, C[1] - n))
        d /= np.linalg.norm(d)
        s = np.array((-d[1], d[0]))
        a = np.array((e, n)) - s * 1.6
        b = np.array((e, n)) + s * 1.6
        m.beam(mat_steel, (a[0], top - 0.6, -a[1]), (b[0], top - 0.6, -b[1]), 0.12, 0.12)
        for k in range(4):
            p = a + (b - a) * (k + 0.5) / 4 + d * 0.35
            m.box(mat_lamp, (p[0], top - 0.25, -p[1]), (0.5, 0.36, 0.14), yaw=math.atan2(s[1], s[0]))


def shelters(m, h, mat_frame, mat_roof, mat_seat):
    """interchange shelters: a bench under a curved-look roof on a steel frame, 4 x 1.6 m, open to the field"""
    for e, n in SHELTERS:
        y0 = h(e, n)
        # facing the field (west)
        d = np.array((C[0] - e, C[1] - n))
        d /= np.linalg.norm(d)
        s = np.array((-d[1], d[0]))
        yaw = math.atan2(s[1], s[0])   # the box's x along the shelter, its z toward the field
        for sx in (-1.9, 1.9):
            for dx in (-0.7, 0.7):
                p = np.array((e, n)) + s * sx + d * dx
                m.tube(mat_frame, (p[0], y0, -p[1]), (p[0], y0 + (2.2 if dx < 0 else 2.0), -p[1]), 0.04, seg=6)
        c = np.array((e, n))
        m.box(mat_roof, (c[0], y0 + 2.15, -c[1]), (4.2, 0.06, 1.9), yaw=yaw)
        back = c - d * 0.7
        m.box(mat_roof, (back[0], y0 + 1.2, -back[1]), (4.0, 1.8, 0.05), yaw=yaw)
        seat = c - d * 0.35
        m.box(mat_seat, (seat[0], y0 + 0.45, -seat[1]), (3.6, 0.06, 0.4), yaw=yaw)


def nets(m, h, mat_frame, mat_net, mat_pitch):
    """cricket nets: three lanes 3.2 m wide and 30 m long, posts every 3 m, netting walls and roof (an alpha mask),
    and a synthetic pitch down each lane"""
    (w0, n0), (w1, n1) = NETS
    lanes = 3
    lw = (w1 - w0) / lanes
    L = n0 - n1
    for k in range(lanes + 1):
        e = w0 + k * lw
        for i in range(int(L // 3) + 1):
            n = n1 + i * 3.0
            y0 = h(e, n)
            m.tube(mat_frame, (e, y0, -n), (e, y0 + 3.2, -n), 0.035, seg=5)
        ya, yb = h(e, n1), h(e, n0)
        m.quad(mat_net, (e, ya, -n1), (e, yb, -n0), (e, yb + 3.2, -n0), (e, ya + 3.2, -n1), both=True)
        m.beam(mat_frame, (e, ya + 3.2, -n1), (e, yb + 3.2, -n0), 0.05, 0.05)
    for k in range(lanes):
        ea, eb = w0 + k * lw, w0 + (k + 1) * lw
        ya, yb = h(ea, n1), h(ea, n0)
        m.quad(mat_net, (ea, ya + 3.2, -n1), (eb, ya + 3.2, -n1), (eb, yb + 3.2, -n0), (ea, yb + 3.2, -n0), both=True)
        mid = (ea + eb) / 2
        m.quad(mat_pitch, (mid - 1.2, ya + 0.04, -n1), (mid + 1.2, ya + 0.04, -n1), (mid + 1.2, yb + 0.04, -(n0 - 4)),
               (mid - 1.2, yb + 0.04, -(n0 - 4)))
    # the back (north) end netted
    ya = h(w0, n0)
    m.quad(mat_net, (w0, ya, -n0), (w1, ya, -n0), (w1, ya + 3.2, -n0), (w0, ya + 3.2, -n0), both=True)
