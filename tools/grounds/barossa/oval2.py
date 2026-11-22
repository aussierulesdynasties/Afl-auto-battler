"""The second oval, north-west of Barossa Park (the old Lyndoch recreation oval, Gather Round's fan zone): its turf
with the running track's lane lines mown in, the gravel path down its west side, goal and behind posts at both ends,
four training light poles, the three interchange shelters on the east wing and the cricket nets past the north end.

Measured on the 2026 satellite mosaic (the oval is not in OpenStreetMap). The six lane lines (ground level, so true
on the leaning aerial) are one smooth curve and its exact offsets: a superellipse |along/A|^n + |across/B|^n = 1
round (-196.8, 182.91), long axis 14.38 degrees west of north, A 72.46 m, B 47.18 m, n 3.02, fitted by making the
mosaic's lines along its normals as sharp as they go; the lines lie 0.3 + 1.22 k m outside it (k = 0..5), 1.22 m
lanes. Against the mosaic: 8,216 strong line samples, rms 0.33 m, 90% within 0.55 m (shape_check.py). The grass
round it runs on into the park, so it has no edge of its own; the turf is painted to 4 m past the outer lane. The
goal posts' shadows cross the track's ends, so the posts stand just outside it on the long axis (to about 2 m). The
light poles stand where their shadows start; the shelters, nets and path from the mosaic. The 2025 Gather Round
photo (from the south-east) shows the mown rings, the posts at both ends and the light poles.
"""
import math

import numpy as np

C = (-196.8, 182.91)
BEARING = -14.38                 # long axis, degrees east of north
TRACK = (47.18, 72.46, 3.02)     # superellipse: semi axes across and along, exponent
LANES = [0.3 + 1.22 * k for k in range(6)]   # lane lines, metres outside the curve
TURF = LANES[-1] + 4.0           # mown turf to 4 m past the outer lane
KEEP = LANES[-1] + 12.0          # no vines or planted trees within this
POSTS_AT = 72.46 + LANES[-1] + 1.5   # goal line, along the axis from the middle
PATH = [(-268.0, 297.3), (-266.7, 273.3), (-268.0, 246.7), (-270.7, 220.0), (-274.7, 188.0), (-281.3, 158.7),
        (-285.3, 140.0), (-280.0, 118.7), (-260.0, 97.3), (-233.3, 78.7), (-212.0, 70.7), (-188.0, 62.7)]
PATH_W = 3.0
POLES = [(-161.7, 258.3), (-245.0, 261.7), (-221.7, 116.7), (-128.3, 138.3)]
SHELTERS = [(-121.0, 197.0), (-120.5, 184.0), (-120.0, 172.0)]   # interchange shelters, along the boundary
NETS = ((-258.0, 300.0), (-248.0, 258.0))   # cricket nets: west and east lane edges at the north and south ends
_CURVE = None
_TREE = None


def curve(n=20000):
    """the track's base curve, dense, in the oval's own frame (across, along) and its outward normals"""
    global _CURVE
    if _CURVE is None:
        B, A, ex = TRACK
        t = np.linspace(0, 2 * math.pi, n, endpoint=False)
        c, s = np.cos(t), np.sin(t)
        x = B * np.sign(c) * np.abs(c) ** (2 / ex)
        y = A * np.sign(s) * np.abs(s) ** (2 / ex)
        nx = np.sign(x) * np.abs(x / B) ** (ex - 1) / B
        ny = np.sign(y) * np.abs(y / A) ** (ex - 1) / A
        ln = np.hypot(nx, ny) + 1e-12
        _CURVE = (np.stack([x, y], 1), np.stack([nx / ln, ny / ln], 1))
    return _CURVE


def offset(e, n):
    """signed distance (metres, + outside) from the track's base curve, square to it"""
    global _TREE
    from scipy.spatial import cKDTree
    P, Nn = curve()
    if _TREE is None:
        _TREE = cKDTree(P)
    x, y = local(e, n)
    shp = np.shape(x)
    q = np.stack([np.ravel(x), np.ravel(y)], 1)
    _, i = _TREE.query(q)
    d = q - P[i]
    out = np.hypot(d[:, 0], d[:, 1]) * np.sign(np.sum(d * Nn[i], 1))
    return out.reshape(shp) if shp else float(out[0])


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
    """True for an OpenStreetMap vineyard drawn before the oval was built: one that covers the oval's turf. Its vines
    are gone (the 2026 mosaic shows the oval, its paths and the precinct there), so it is neither painted nor
    planted."""
    from shapely.geometry import Polygon
    poly = Polygon(pts).buffer(0)
    P, Nn = curve(400)
    ring = [plan(*(p + q * TURF)) for p, q in zip(P, Nn)]
    turf = Polygon(ring)
    return poly.intersection(turf).area > 0.3 * turf.area


def on_oval(e, n):
    """within the oval's turf and the grass kept clear round it"""
    return offset(e, n) < KEEP


def paint(img, E, N, base_grass):
    """paint the oval into a texture (H x W x 3 float, sRGB 0-255) whose pixels sit at plan E, N"""
    x, y = local(E, N)
    near = np.abs(x) < TRACK[0] + TURF + 2
    near &= np.abs(y) < TRACK[1] + TURF + 2
    d = np.full(E.shape, np.inf)
    d[near] = offset(E[near], N[near])
    turf = np.array((92, 136, 58), float)
    # mowing: straight bands along the ground inside the track (as the mosaic shows), rings following it outside
    band = (np.floor(x / 7.5) % 2).astype(float)
    ring = (np.floor(np.where(np.isfinite(d), d, 0) / 3.0) % 2).astype(float)
    shade = np.where(d < 0, band, ring)
    col = turf[None, None, :] * (0.94 + 0.1 * shade)[..., None]
    m = d < TURF
    img[m] = col[m]
    # the lane lines, mown in darker (the mosaic and the 2025 photo show them as dark rings, not paint)
    for L in LANES:
        line = np.abs(d - L) < 0.06
        img[line] = turf * 0.72
    # the gravel path down the west side
    _path(img, E, N)
    return img


def _path(img, E, N):
    from scipy.interpolate import splprep, splev
    from scipy.spatial import cKDTree
    pts = np.array(PATH)
    tck, _ = splprep([pts[:, 0], pts[:, 1]], s=len(pts) * 2.0)
    q = np.array(splev(np.linspace(0, 1, 2000), tck)).T
    box = (E > q[:, 0].min() - 5) & (E < q[:, 0].max() + 5) & (N > q[:, 1].min() - 5) & (N < q[:, 1].max() + 5)
    dd, _ = cKDTree(q).query(np.stack([E[box], N[box]], 1))
    m = np.zeros(E.shape, bool)
    m[box] = dd < PATH_W / 2
    img[m] = (188, 178, 156)


def goal_posts(m, h, mat_post, mat_pad):
    """goal and behind posts at both ends just outside the track on the long axis: goal posts 6.4 m apart, 12 m tall,
    behind posts 6.4 m outside them, 7 m tall, the lower 2.5 m of each padded"""
    for end in (-1, 1):
        for off, tall in ((-9.6, 7.0), (-3.2, 12.0), (3.2, 12.0), (9.6, 7.0)):
            e, n = plan(off, end * POSTS_AT)
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
