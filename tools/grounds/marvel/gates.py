"""Marvel Stadium's level-1 concourse deck and its public gates, as they stand since the 2024 Grimshaw works.

The deck (the external concourse, OpenStreetMap 751006317, "Marvel Stadium External Concourse (Level 1)") runs
round the north and east of the ground at the south plaza's level (landmarks.PLAZA_Z, 8.6), over the car park:
light concrete in sawn panels with dark radial bands, a low concrete parapet at its edge and a sheer wall down to
the street. Its outline is read off Esri World Imagery (polar unwraps, 0.1 m a pixel); the gates are built from
the 2024 Grimshaw / AIA photographs and the 2019 Street View captures named at each gate below.

The geometry is made in two stages because Blender's own Python has neither PIL nor shapely:

    python tools/grounds/marvel/gates.py                 textures and faces, then runs Blender for stage 2
    blender -b --python gates.py -- --export <pickle>    3D lettering and the glTF export (run by stage 1)

Frame: landmarks.py's (x east, y north, z up; model z = metres above sea level - 2.6). Bearings are compass
bearings from the centre of the ground, r the distance from it. Writes assets/grounds/marvel/gates.glb.
Map data (c) OpenStreetMap contributors, ODbL. Imagery is reference only; every texture is drawn here.
"""
import json
import math
import os
import pickle
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "assets", "grounds", "marvel", "gates.glb")
TEX = os.path.join(HERE, "gate_tex")
FONTS = os.path.join(ROOT, "assets", "fonts")
BLENDER = os.environ.get("BLENDER", r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")

TILE = {}
NRM = {}           # smooth-shaded parts for stage 2: material -> per face, a normal per vertex
TEXT = []          # 3D lettering for stage 2: (text, font, size, centre xyz, outward normal xy, depth, material)


# ================================================================ stage 1 (system Python: numpy, PIL, shapely)
def _stage1():
    import numpy as np
    from PIL import Image
    sys.path.insert(0, HERE)
    import land
    import landmarks as L

    rng = np.random.default_rng(23)

    def save(name, img, tile):
        os.makedirs(TEX, exist_ok=True)
        img = np.asarray(img, float)
        mode = "RGBA" if img.shape[2] == 4 else "RGB"
        Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), mode).save(os.path.join(TEX, name + ".png"))
        TILE[name] = tile

    def flat(name, colour, noise=3.0):
        save(name, np.zeros((32, 32, 3)) + colour + rng.normal(0, noise, (32, 32, 3)), (4.0, 4.0))

    # ------------------------------------------------------------ textures
    def concrete_panels(name, px=24, tile=12.0, panel=3.0, base=(178, 175, 169)):
        """The deck (Street View 2019, n_plaza, nw_corner, g6, g7): light grey broom-finished concrete in sawn
        panels about 3 m square, faint joints, patches of weathering."""
        n = int(tile * px)
        y, x = np.mgrid[0:n, 0:n] / px
        img = np.zeros((n, n, 3)) + np.array(base, float)
        cell = np.floor(x / panel) + 17 * np.floor(y / panel)
        img += ((np.sin(cell * 12.9898) * 43758.5453 % 1.0)[..., None] - 0.5) * 8.0
        img[((x % panel) < 0.025) | ((y % panel) < 0.025)] -= 26
        img += rng.normal(0, 3.5, (n, n, 1))
        blot = np.zeros((n, n))
        for _ in range(8):
            cx, cy, r = rng.uniform(0, tile, 3)
            blot += np.exp(-(((x - cx) % tile) ** 2 + ((y - cy) % tile) ** 2) / (2 * (0.8 + r * 0.3) ** 2))
        img -= (np.clip(blot, 0, 1) * 9)[..., None]
        save(name, img, (tile, tile))

    concrete_panels("deck_concrete")
    flat("deck_band", (62, 62, 64), 4.0)              # the dark radial bands set in the deck (charcoal granite)
    concrete_panels("parapet_concrete", tile=6.0, panel=6.0, base=(170, 167, 160))
    flat("retaining", (150, 147, 140), 5.0)           # the sheer wall from the deck down to the street
    flat("step_nosing", (96, 96, 98), 3.0)

    g = L.Geo()
    UP = (0.0, 0.0, 1.0)

    def face(mat, pts, out, uvs=None):
        """g.poly with the winding set so the face's normal points along `out` (glTF faces are one-sided)."""
        P = np.array(pts, float)
        n = np.zeros(3)
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            n += ((a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1]))
        if float(np.dot(n, out)) < 0:
            pts = list(pts)[::-1]
            uvs = list(uvs)[::-1] if uvs is not None else None
        g.poly(mat, pts, uvs)

    def h(v, z=0.0):
        return (float(v[0]), float(v[1]), z)
    DECK_Z = L.PLAZA_Z
    EDGE = json.load(open(os.path.join(HERE, "fit", "deck_edge.json")))   # bearing -> plinth radius (marvel.glb)

    def u(b):
        a = math.radians(b)
        return np.array([math.sin(a), math.cos(a)])

    def pt(b, r):
        return tuple(u(b) * r)

    # ------------------------------------------------------------ deck outline
    # Outer edge read off the polar unwraps (aerial/pe.jpg, pn.jpg, the deck's parapet line): bearing -> r.
    OUTER = [(280, 148), (290, 148), (300, 150), (310, 150), (320, 152), (330, 155), (340, 158), (350, 160),
             (360, 158.5), (370, 156), (380, 150), (420, 150), (450, 151), (455, 152), (475, 146), (490, 146)]

    ABUT = {float(k): v for k, v in json.load(open(os.path.join(HERE, "fit", "deck_abut.json")))["r"].items()}

    def abut(b):
        """The wall of a building the deck runs up to at bearing b, or None."""
        k = round((b % 360) * 2) / 2
        lo, hi = ABUT.get(math.floor(b % 360 * 2) / 2), ABUT.get(math.ceil(b % 360 * 2) / 2)
        if lo is None or hi is None:
            return ABUT.get(k)
        t = (b % 360 * 2) % 1.0
        return lo + (hi - lo) * t

    # The wall along Wurundjeri Way (marvel.glb, the Marvel thread's round 17): 7.95 m west of the centreline of the
    # northbound ways 580628688 and 790397545 (3 lanes x 3.3 m / 2 + 0.3 m kerb + 2.7 m verge), each way offset on
    # its own as landmarks.graffiti_wall does. The deck stops at it; past it lay the verge and the road.
    WALL_OFF = 3 * 3.3 / 2 + 0.3 + 2.7
    WAYS = json.load(open(os.path.join(HERE, "fit", "wurundjeri_ways.json")))["ways"]
    WALL_SEGS = []
    for wpts in WAYS.values():
        wp = np.array(wpts, float)
        line = []
        for i in range(len(wp)):
            dv = wp[min(i + 1, len(wp) - 1)] - wp[max(i - 1, 0)]
            dv /= np.linalg.norm(dv)
            line.append(wp[i] + np.array([-dv[1], dv[0]]) * WALL_OFF)    # left of a northbound way is west
        WALL_SEGS += list(zip(line[:-1], line[1:]))

    def wall_r(b):
        """Distance out along the radial at bearing b to the Wurundjeri Way wall, or None if it misses."""
        d = u(b)
        best = None
        for a, c in WALL_SEGS:
            e = c - a
            den = d[0] * (-e[1]) - d[1] * (-e[0])
            if abs(den) < 1e-9:
                continue
            t = (a[0] * (-e[1]) - a[1] * (-e[0])) / den          # along the radial
            s_ = (d[0] * a[1] - d[1] * a[0]) / den                 # along the segment
            if t > 0 and -1e-6 <= s_ <= 1 + 1e-6:
                best = t if best is None else min(best, t)
        return best

    def r_out(b):
        bb = b if b >= 280 else b + 360
        xs, ys = zip(*OUTER)
        r = float(np.interp(bb, xs, ys))
        w = abut(b)
        r = min(r, w - 0.02) if w is not None else r
        wr = wall_r(b)
        return min(r, wr) if wr is not None else r

    def at_wall(b):
        """The deck's edge is the Wurundjeri Way wall here (marvel.glb draws that wall and its coping)."""
        wr = wall_r(b)
        return wr is not None and r_out(b) >= wr - 1e-6

    def r_in(b):
        k = "%.1f" % ((round(b * 2) / 2) % 360)
        return float(EDGE[k])

    SPANS = [(280.0, 490.0)]          # 280 -> 130 through north (bearings past 360 wrap)
    STEP = 0.5
    BAND_W = 0.45
    band_at = [1.8 + k * 3.75 for k in range(-25, 40)]
    band_at = [b % 360 for b in band_at]

    def banded(b):
        b %= 360
        return b >= 280 or b <= 34 or 95 <= b <= 130

    # Deck top: split at each band so the bands are their own faces (no coplanar overlap, no z-fighting).
    def edge_line_point(b, side, r):
        """The point at radius r on the line BAND_W/2 to one side of the radial at bearing b."""
        n = np.array([u(b)[1], -u(b)[0]])     # clockwise normal (towards smaller bearings... east of a north radial)
        h = BAND_W / 2 * side
        t = math.sqrt(max(r * r - h * h, 0.0))
        return tuple(u(b) * t + n * h)

    cuts = []          # (bearing, kind): band edges inside banded zones, regular steps elsewhere
    for b0, b1 in SPANS:
        b = b0
        while b < b1 - 1e-6:
            cuts.append(b)
            b += STEP
        cuts.append(b1)

    def ring_pts(bs, radius):
        return [pt(b, radius(b % 360)) for b in bs]

    # deck faces: quads between consecutive sample bearings, with bands replacing their slivers
    samples = sorted(set([round(c, 3) for c in cuts]))
    bands = sorted(set(round(b if b >= 280 else b + 360, 3) for b in band_at if banded(b)))
    bands = [b for b in bands if 280 < b < 490]
    # build a list of (bearing, point_in, point_out) edges, bands contributing two edges each
    edges = []
    for b in samples:
        if any(abs(b - c) < (BAND_W / 2) / (r_in(b % 360) * math.pi / 180) + 1e-3 for c in bands):
            continue
        edges.append((b, pt(b, r_in(b % 360)), pt(b, r_out(b))))
    for c in bands:
        bi, bo = r_in(c % 360), r_out(c)
        for side in (+1, -1):
            pi = edge_line_point(c, side, bi)
            po = edge_line_point(c, side, bo)
            bb = c - side * math.degrees(BAND_W / 2 / bi)
            edges.append((bb + 0.0, pi, po))
    edges.sort(key=lambda e: e[0])
    for (ba, ia, oa), (bb, ib, ob) in zip(edges, edges[1:]):
        mid = (ba + bb) / 2
        mat = "deck_band" if any(abs(mid - c) < 0.05 for c in bands) and (bb - ba) < 0.5 else "deck_concrete"
        face(mat, [(*ia, DECK_Z), (*oa, DECK_Z), (*ob, DECK_Z), (*ib, DECK_Z)], UP,
             [(ia[0], ia[1]), (oa[0], oa[1]), (ob[0], ob[1]), (ib[0], ib[1])])

    # ------------------------------------------------------------ north steps (OpenStreetMap 1507403842 + 1509700089)
    # Straight down from the deck edge at bearing 356.5 to the street at r 167.5.
    STEPS_B = 356.4
    STEPS_W = 4.0
    s0 = r_out(STEPS_B)
    s1 = 167.5
    zt, zb = DECK_Z, land.z(*pt(STEPS_B, s1))
    nst = max(1, int(round((zt - zb) / 0.165)))
    run = (s1 - s0) / nst
    side_n = np.array([u(STEPS_B)[1], -u(STEPS_B)[0]])
    ax = u(STEPS_B)
    for k in range(nst):
        ztop = zt - (k + 1) * (zt - zb) / nst
        a0 = ax * (s0 + k * run)
        a1 = ax * (s0 + (k + 1) * run)
        l0, r0 = a0 + side_n * STEPS_W / 2, a0 - side_n * STEPS_W / 2
        l1, r1 = a1 + side_n * STEPS_W / 2, a1 - side_n * STEPS_W / 2
        zprev = zt - k * (zt - zb) / nst
        face("deck_concrete", [(*r0, zprev), (*r0, ztop), (*l0, ztop), (*l0, zprev)], h(ax))     # riser
        face("deck_concrete", [(*r0, ztop), (*r1, ztop), (*l1, ztop), (*l0, ztop)], UP)          # tread
    for sgn in (+1, -1):                     # cheek walls each side of the flight, with the parapet's height
        e0 = ax * s0 + side_n * (STEPS_W / 2 + 0.25) * sgn
        e1 = ax * s1 + side_n * (STEPS_W / 2 + 0.25) * sgn
        ring = [tuple(e0), tuple(e1), tuple(e1 - side_n * 0.25 * sgn), tuple(e0 - side_n * 0.25 * sgn)]
        cen = np.mean(np.array(ring), axis=0)
        for i in range(4):
            a, b = ring[i], ring[(i + 1) % 4]
            face("parapet_concrete", [(*a, zb - 1.0), (*b, zb - 1.0), (*b, zt + 1.0), (*a, zt + 1.0)],
                 h((np.array(a) + np.array(b)) / 2 - cen))
        face("parapet_concrete", [(*q, zt + 1.0) for q in ring], UP)
    steps_gap = math.degrees((STEPS_W / 2 + 0.5) / s0)

    # ------------------------------------------------------------ edge wall and parapet
    PAR_H, PAR_T = 1.0, 0.25
    outer = [b for b in samples]
    for ba, bb in zip(outer, outer[1:]):
        if abs(((ba + bb) / 2) % 360 - STEPS_B) < steps_gap:
            continue
        if abut(ba) is not None and abut(bb) is not None:     # a building's wall is the edge here
            continue
        if at_wall(ba) and at_wall(bb):                       # so is the Wurundjeri Way wall
            continue
        a, b = pt(ba, r_out(ba)), pt(bb, r_out(bb))
        ai, bi = pt(ba, r_out(ba) - PAR_T), pt(bb, r_out(bb) - PAR_T)
        za, zb_ = land.z(*a) - 1.0, land.z(*b) - 1.0
        o = h(u((ba + bb) / 2))
        face("retaining", [(*a, za), (*b, zb_), (*b, DECK_Z), (*a, DECK_Z)], o)   # outward face below the deck
        face("parapet_concrete", [(*a, DECK_Z), (*b, DECK_Z), (*b, DECK_Z + PAR_H), (*a, DECK_Z + PAR_H)], o)
        face("parapet_concrete", [(*bi, DECK_Z), (*ai, DECK_Z), (*ai, DECK_Z + PAR_H), (*bi, DECK_Z + PAR_H)], (-o[0], -o[1], 0))
        face("parapet_concrete", [(*a, DECK_Z + PAR_H), (*b, DECK_Z + PAR_H), (*bi, DECK_Z + PAR_H), (*ai, DECK_Z + PAR_H)], UP)

    # ================================================================ Gate 7 (north, bearings 334 to 0.7)
    # Built from Street View, June 2019 (gates/refs g7_doors2019, g7_west2019, g7_east2019, g7_ticketbay2019,
    # cameras fitted to marvel.glb's columns to half a degree) and the undated photosphere g7_photosphere, which
    # shows the same booths. West to east: a triangle-clad wall with a black board (336.2-334.9); a bank of
    # grilled turnstile lanes with waist-high ticket gates under the "Gate 7" sign (345.86-336.2); one more turnstile and three double grilled
    # doors (348.67-345.86), all opening into a vestibule where marvel.glb's glass is cut away
    # (MARVEL_GATE_CUTS, 335.34-349.09); then three Ticket Sales booths built out between columns C5 to C8
    # (348.8-0.7), windows 1-12 numbered eastward. Columns C4, C3 and C2 carry the red-topped "Gate 7" wrap.
    # The triangle cladding is drawn in the same pattern language (long white lines meeting at nodes); it is
    # not traced line for line. The vestibule is 2 m deep and dark: nothing behind it is modelled.
    from PIL import ImageDraw, ImageFont

    def font(name, px):
        return ImageFont.truetype(os.path.join(FONTS, name), int(px))

    def save_pil(name, im, tile):
        save(name, np.asarray(im, float), tile)

    GLASS_R = [115.06, 114.85, 114.65, 114.48, 114.32, 114.19, 114.09, 114.03, 114.0, 114.03, 114.09, 114.19,
               114.32, 114.48, 114.65, 114.85, 115.06, 115.28, 115.51, 115.75, 115.99, 116.23, 116.47, 116.71,
               116.94, 117.16, 117.36, 117.55, 117.73, 117.88, 118.02]   # marvel.glb bowlglass, 330.34 + 1.25 i
    GB0, GDB = 330.34, 1.25

    def Wb(b):
        return b + 360.0 if b < 180 else b

    def Z(hh):
        return DECK_Z + hh

    def tang(b):
        """Unit vector along the facade towards increasing bearing (east, at the north end)."""
        a = math.radians(b)
        return np.array([math.cos(a), -math.sin(a)])

    def glass(b, d=0.0):
        """Plan point on marvel.glb's glass line on the radial at bearing b, pushed d metres out along it."""
        b = Wb(b)
        i = min(max(int((b - GB0) // GDB), 0), len(GLASS_R) - 2)
        A = np.array(pt(GB0 + i * GDB, GLASS_R[i]))
        B = np.array(pt(GB0 + (i + 1) * GDB, GLASS_R[i + 1]))
        uu = u(b)
        t = -(uu[0] * A[1] - uu[1] * A[0]) / (uu[0] * (B - A)[1] - uu[1] * (B - A)[0])
        return A + t * (B - A) + uu * d

    def deg(b, metres, d=0.0):
        """Bearing `metres` along the facade from b (positive = west, the reading direction from outside)."""
        return b - math.degrees(metres / np.linalg.norm(glass(b, d)))

    def marks(b_hi, b_lo):
        b_hi, b_lo = Wb(b_hi), Wb(b_lo)
        vs = [GB0 + k * GDB for k in range(len(GLASS_R)) if b_lo + 1e-6 < GB0 + k * GDB < b_hi - 1e-6]
        return [b_hi] + sorted(vs, reverse=True) + [b_lo]

    def span(b_hi, b_lo, d):
        ms = marks(b_hi, b_lo)
        return sum(float(np.linalg.norm(glass(a, d) - glass(c, d))) for a, c in zip(ms, ms[1:]))

    def strip(mat, b_hi, b_lo, h0, h1, d, fit=None, v0=0.0, u0=0.0, inward=False):
        """Vertical facing on the glass line pushed d out, from b_hi (east) to b_lo (west), so its texture reads
        left to right from outside. fit = the texture width stretched once over the whole span."""
        ms = marks(b_hi, b_lo)
        L = span(b_hi, b_lo, d)
        k = fit / L if fit else 1.0
        s = u0
        for a, c in zip(ms, ms[1:]):
            pa, pc = glass(a, d), glass(c, d)
            ds = float(np.linalg.norm(pc - pa))
            o = u((a + c) / 2) * (-1 if inward else 1)
            face(mat, [(*pa, Z(h0)), (*pc, Z(h0)), (*pc, Z(h1)), (*pa, Z(h1))], (o[0], o[1], 0.0),
                 [(s * k, h0 - v0), ((s + ds) * k, h0 - v0), ((s + ds) * k, h1 - v0), (s * k, h1 - v0)])
            s += ds
        return L

    def radial(mat, b, d0, d1, h0, h1, facing, fit=None):
        """A wall along the radial at bearing b from d0 to d1 out, facing east (+1) or west (-1)."""
        A, B = glass(b, d0), glass(b, d1)
        t = tang(b) * facing
        L = abs(d1 - d0)
        k = fit / L if fit else 1.0
        face(mat, [(*A, Z(h0)), (*B, Z(h0)), (*B, Z(h1)), (*A, Z(h1))], (t[0], t[1], 0.0),
             [(d0 * k, h0), (d1 * k, h0), (d1 * k, h1), (d0 * k, h1)])

    def hbox(mat, c, a, length, width, h0, h1, top=True, bottom=False):
        """A box standing on plan centre c, `length` along unit vector a, `width` across it."""
        a = np.array(a, float) / np.linalg.norm(a)
        n = np.array([-a[1], a[0]])
        c = np.array(c, float)
        ring = [c + a * length / 2 + n * width / 2, c - a * length / 2 + n * width / 2,
                c - a * length / 2 - n * width / 2, c + a * length / 2 - n * width / 2]
        for i in range(4):
            p, q = ring[i], ring[(i + 1) % 4]
            o = (p + q) / 2 - c
            L = float(np.linalg.norm(q - p))
            face(mat, [(*p, Z(h0)), (*q, Z(h0)), (*q, Z(h1)), (*p, Z(h1))], (o[0], o[1], 0.0),
                 [(0, h0), (L, h0), (L, h1), (0, h1)])
        if top:
            face(mat, [(*p, Z(h1)) for p in ring], UP)
        if bottom:
            face(mat, [(*p, Z(h0)) for p in ring], (0.0, 0.0, -1.0))

    def fbox(mat, b, d, w, dp, h0, h1, top=True, bottom=False):
        """A box on the facade: centred on bearing b, d out, w along the facade, dp deep."""
        hbox(mat, glass(b, d), tang(b), w, dp, h0, h1, top, bottom)

    def panel(mat, b, d, w, h0, h1):
        """A flat rectangle facing out, centred on bearing b, d out, w wide; its texture fits it exactly."""
        # Lie along the polyline segment under b, not the circle's tangent: the glass radii vary, so a panel
        # on the circle tangent dips behind the facing it sits on over one half of its width.
        c = glass(b, d)
        t = glass(b + 0.01, d) - glass(b - 0.01, d)
        t = t / np.linalg.norm(t)
        o = np.array([t[1], -t[0]]) if np.dot([t[1], -t[0]], u(b)) > 0 else np.array([-t[1], t[0]])
        p, q = c + t * w / 2, c - t * w / 2          # east edge first: reads left to right from outside
        face(mat, [(*p, Z(h0)), (*q, Z(h0)), (*q, Z(h1)), (*p, Z(h1))], (o[0], o[1], 0.0),
             [(0, 0), (w, 0), (w, h1 - h0), (0, h1 - h0)])

    # ------------------------------------------------------------ Gate 7 textures
    RED = (204, 52, 58)          # the red top stripes (sign band, booth headers, column wraps)
    SIGN_GREY = (80, 82, 88)
    LABEL_SLATE = (78, 84, 104)  # the column labels are bluer than the band (vid2026_t422 sampled)
    WHITE = (246, 246, 244)
    CLAD = (150, 152, 158)

    def tri_clad(name, W_, H_, px=80):
        """The cladding round the doors and booths: light grey panels with faint joints. The white line
        graphic of 2019 (g7_doors2019, g7_ticketbay2019) is gone in Nov 2026 (vid2026_t422, t429, t441):
        the walls and booth fronts are plain."""
        im = Image.new("RGB", (int(W_ * px), int(H_ * px)), CLAD)
        dr = ImageDraw.Draw(im)
        for x in np.arange(0, W_, 0.75):
            dr.line([(x * px, 0), (x * px, H_ * px)], fill=(140, 142, 148), width=1)
        for y in np.arange(0, H_, 1.15):
            dr.line([(0, y * px), (W_ * px, y * px)], fill=(140, 142, 148), width=1)
        save_pil(name, im, (W_, H_))

    tri_clad("tri_clad", 6.0, 4.6)
    flat("dark_frame", (38, 39, 42), 2.0)            # the charcoal frames of the booths, the door and lane posts
    flat("lintel_grey", (196, 196, 193), 2.5)        # the light grey lintel under the soffit
    flat("interior_dark", (34, 35, 37), 3.0)
    flat("interior_floor", (70, 70, 72), 3.0)
    flat("tray_white", (224, 225, 226), 2.0)          # the ticket trays under the windows
    flat("board_black", (24, 24, 26), 1.5)
    flat("steel", (172, 174, 178), 2.0)
    flat("lane_plate", (112, 126, 142), 2.0)
    flat("col_red", RED, 2.0)

    def louvre(name, w, hgt, px=120):
        """Black louvre panels over the doors and lanes (g7_doors2019): a frame with horizontal slats."""
        im = Image.new("RGB", (int(w * px), int(hgt * px)), (30, 31, 33))
        dr = ImageDraw.Draw(im)
        for y in np.arange(0.06, hgt - 0.04, 0.05):
            dr.line([(0.04 * px, y * px), ((w - 0.04) * px, y * px)], fill=(52, 54, 57), width=2)
        dr.rectangle([0, 0, w * px - 1, hgt * px - 1], outline=(16, 16, 17), width=int(0.04 * px))
        save_pil(name, im, (w, hgt))

    louvre("louvre_lo", 1.4, 0.70)
    louvre("louvre_hi", 1.4, 0.76)

    def grille_door(name, w=0.70, hgt=2.30, px=200):
        """One leaf of the grilled doors and lane gates (g7_doors2019, vid2026_t448): a black frame round a square
        welded mesh of 50 mm cells you can see through (alpha clip), with rails 0.80 and 1.55 m up."""
        W_, H_ = int(w * px), int(hgt * px)
        im = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        col = (22, 22, 24, 255)
        step = int(0.05 * px)
        for x in range(0, W_, step):
            dr.line([(x, 0), (x, H_)], fill=col, width=2)
        for y in range(0, H_, step):
            dr.line([(0, y), (W_, y)], fill=col, width=2)
        f = int(0.05 * px)
        dr.rectangle([0, 0, W_ - 1, H_ - 1], outline=col, width=f)
        for zr in (0.80, 1.55):
            ym = H_ - int(zr * px)
            dr.rectangle([0, ym - f // 2, W_, ym + f // 2], fill=col)
        save_pil(name, im, (w, hgt))

    grille_door("grille_door")
    grille_door("grille_lane", w=1.10)          # one leaf across each turnstile lane

    def bars(name, w=1.0, hgt=2.3, px=120):
        """The vertical bar screens between the turnstile lanes (alpha clip)."""
        W_, H_ = int(w * px), int(hgt * px)
        im = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        col = (150, 152, 156, 255)
        for x in range(0, W_, int(0.11 * px)):
            dr.rectangle([x, 0, x + 2, H_], fill=col)
        dr.rectangle([0, 0, W_, int(0.04 * px)], fill=col)
        dr.rectangle([0, H_ - int(0.04 * px), W_, H_], fill=col)
        dr.rectangle([0, H_ - int(1.05 * px) - 3, W_, H_ - int(1.05 * px) + 3], fill=col)
        save_pil(name, im, (w, hgt))

    bars("bars_v")

    def wheelchair(dr, x0, y0, s, fill):
        """The access pictogram, drawn in a white-outlined box of side s px at (x0, y0)."""
        dr.rectangle([x0, y0, x0 + s, y0 + s], outline=fill, width=max(2, s // 18))
        cx, cy = x0 + s * 0.45, y0 + s * 0.62
        rw = s * 0.22
        dr.arc([cx - rw, cy - rw, cx + rw, cy + rw], 200, 520, fill=fill, width=max(2, s // 14))
        dr.ellipse([x0 + s * 0.36, y0 + s * 0.12, x0 + s * 0.48, y0 + s * 0.24], fill=fill)
        w_ = max(2, s // 12)
        dr.line([(x0 + s * 0.42, y0 + s * 0.28), (x0 + s * 0.44, y0 + s * 0.55)], fill=fill, width=w_)
        dr.line([(x0 + s * 0.44, y0 + s * 0.55), (x0 + s * 0.66, y0 + s * 0.55)], fill=fill, width=w_)
        dr.line([(x0 + s * 0.66, y0 + s * 0.55), (x0 + s * 0.76, y0 + s * 0.78)], fill=fill, width=w_)
        dr.line([(x0 + s * 0.43, y0 + s * 0.38), (x0 + s * 0.60, y0 + s * 0.38)], fill=fill, width=w_)

    def arrow_down(dr, cx, y0, y1, fill, w_):
        dr.line([(cx, y0), (cx, y1 - w_)], fill=fill, width=w_)
        hw = (y1 - y0) * 0.32
        dr.line([(cx - hw, y1 - hw), (cx, y1)], fill=fill, width=w_)
        dr.line([(cx + hw, y1 - hw), (cx, y1)], fill=fill, width=w_)

    B_SIGN_E, B_SIGN_W = 345.86, 339.64          # the Gate 7 sign band, +2.30 to +3.00
    sign_len = span(B_SIGN_E, B_SIGN_W, 0.08)

    def gate7_sign(px=200):
        """The sign band (g7_doors2019, camera at heading 172, 40 deg): dark grey with a red top stripe; from
        the east end, the access box 0.8 m in, then "Gate 7" between two down arrows centred 6.3 m in, the
        arrows 5.0 and 7.8 m in, and the club's MARVEL box at the west end (g7_west2019, partly behind C3)."""
        W_, H_ = int(sign_len * px), int(0.70 * px)
        im = Image.new("RGB", (W_, H_), SIGN_GREY)
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, W_, int(0.08 * px)], fill=RED)
        wheelchair(dr, int(0.82 * px), int(0.20 * px), int(0.40 * px), WHITE)
        # Nov 2026 front view (vid2026_t422, scaled from columns C4, C3, C2): "Gate 7" centred 7.25 m in, caps
        # 0.32 m tall, the first arrow 5.85 m in; the second sits behind C3 from there, placed symmetrically
        dr.text((7.25 * px, 0.40 * px), "Gate 7", font=font("Barlow-SemiBold.ttf", 0.42 * px), fill=WHITE,
                anchor="mm")
        for ax in (6.05, 8.45):  # left arrow 0.5 text-widths before the text (vid2026_t422 sign crop)
            arrow_down(dr, ax * px, 0.22 * px, 0.60 * px, WHITE, max(3, int(0.035 * px)))
        # the west end reads "[MARVEL] STADIUM" (vid2026_t422, t452): the red box 0.80 m, then STADIUM 1.0 m wide
        sw_ = int(1.00 * px)
        sx_ = W_ - sw_ - int(0.08 * px)
        mw, mh = int(0.80 * px), int(0.30 * px)
        mx, my = sx_ - mw - int(0.06 * px), int(0.28 * px)
        dr.rectangle([mx, my, mx + mw, my + mh], fill=(196, 30, 38))
        dr.text((mx + mw / 2, my + mh / 2), "MARVEL", font=font("BarlowCondensed-Bold.ttf", 0.27 * px), fill=WHITE,
                anchor="mm")
        dr.text((sx_ + sw_ / 2, my + mh / 2), "STADIUM", font=font("BarlowCondensed-Bold.ttf", 0.27 * px),
                fill=WHITE, anchor="mm")
        save_pil("gate7_sign", im, (sign_len, 0.70))

    gate7_sign()

    WRAP_C = 2 * math.pi * 0.415

    def col_wrap(px=300):
        """The wrap on columns C4, C3, C2 (+2.87 to +3.58, measured against the sign in g7_doors2019): a red ring 0.17 m deep over a dark grey band with
        a large "7" with "Gate" down the column to its right, on slate blue (vid2026_t422, t448); three repeats round the column."""
        w = WRAP_C / 3
        W_, H_ = int(w * px), int(0.71 * px)
        im = Image.new("RGB", (W_, H_), LABEL_SLATE)
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, W_, int(0.17 * px)], fill=RED)
        g = Image.new("RGBA", (int(0.50 * px), int(0.22 * px)), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((g.width / 2, g.height / 2), "Gate", font=font("Barlow-SemiBold.ttf", 0.17 * px),
                               fill=WHITE + (255,), anchor="mm")
        g = g.rotate(-90, expand=True)                  # reads top to bottom, right of the 7 (vid2026_t422, t448)
        dr.text((int(0.30 * px), int(0.44 * px)), "7", font=font("Barlow-SemiBold.ttf", 0.50 * px), fill=WHITE,
                anchor="mm")
        im.paste(g, (int(0.45 * px), int(0.19 * px)), g)
        save_pil("col_wrap7", im, (w, 0.71))

    col_wrap()

    def booth_header(name, w, px=200):
        """Booth header (g7_ticketbay2019): dark grey, red top stripe, a white ticket badge and "Ticket Sales",
        the pair centred on the bay."""
        W_, H_ = int(w * px), int(0.73 * px)
        im = Image.new("RGB", (W_, H_), SIGN_GREY)
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, W_, int(0.07 * px)], fill=RED)
        f = font("Barlow-SemiBold.ttf", 0.40 * px)
        tw = dr.textlength("Ticket Sales", font=f)
        s = int(0.33 * px)
        gap = int(0.10 * px)
        x0 = (W_ - (s + gap + tw)) / 2
        y0 = int(0.43 * px - s / 2)
        dr.rounded_rectangle([x0, y0, x0 + s, y0 + s], radius=int(0.03 * px), fill=WHITE)
        tk = Image.new("RGBA", (int(s * 0.80), int(s * 0.46)), (0, 0, 0, 0))
        td = ImageDraw.Draw(tk)
        td.rectangle([0, 0, tk.width, tk.height], fill=SIGN_GREY + (255,))
        rr = tk.height // 5
        for cxn in (0, tk.width):
            td.ellipse([cxn - rr, tk.height / 2 - rr, cxn + rr, tk.height / 2 + rr], fill=(0, 0, 0, 0))
        tk = tk.rotate(40, expand=True, resample=Image.BICUBIC)
        im.paste(tk, (int(x0 + (s - tk.width) / 2), int(y0 + (s - tk.height) / 2)), tk)
        dr.text((x0 + s + gap, 0.43 * px), "Ticket Sales", font=f, fill=WHITE, anchor="lm")
        save_pil(name, im, (w, 0.73))

    def booth_glazing(name, w, px=100):
        """The dark glazing over each booth header (g7_east2019): 4 panes across, 2 up, charcoal mullions."""
        W_, H_ = int(w * px), int(1.20 * px)
        a = np.zeros((H_, W_, 3)) + np.array((44, 50, 56), float) + np.linspace(14, -6, H_)[:, None, None]
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        dr = ImageDraw.Draw(im)
        m = max(3, int(0.06 * px))
        for k in range(5):
            x = int(k * (W_ - 1) / 4)
            dr.rectangle([x - m // 2, 0, x + m // 2, H_], fill=(32, 33, 36))
        dr.rectangle([0, H_ // 2 - m // 2, W_, H_ // 2 + m // 2], fill=(32, 33, 36))
        save_pil(name, im, (w, 1.20))

    def window_unit(n, px=200):
        """One ticket window, +1.04 to +2.31, measured on g7_ticketbay2019 against the 2.21 m clad wall: a light
        head strip, the dark teal number plate (2.06-2.27), a dark upper pane, a light rail (1.73-1.80), the
        teal lower pane (1.13-1.73) and a light sill (1.04-1.13); thin dark jambs either side."""
        W_, H_ = int(0.70 * px), int(1.27 * px)
        im = Image.new("RGB", (W_, H_), (20, 26, 30))
        dr = ImageDraw.Draw(im)

        def band(h0, h1, col):
            dr.rectangle([0, int((2.31 - h1) * px), W_, int((2.31 - h0) * px)], fill=col)
        band(2.27, 2.31, (214, 216, 218))
        band(2.06, 2.27, (30, 56, 62))
        band(1.73, 1.80, (214, 216, 218))
        band(1.13, 1.73, (26, 64, 68))
        band(1.04, 1.13, (214, 216, 218))
        dr.text((W_ / 2, int(0.145 * px)), str(n), font=font("Barlow-SemiBold.ttf", 0.13 * px),
                fill=(150, 172, 174), anchor="mm")
        dr.rectangle([int(0.25 * px), int(0.53 * px), int(0.45 * px), int(0.57 * px)], fill=(70, 110, 112))
        j_ = int(0.025 * px)
        dr.rectangle([0, 0, j_, H_], fill=(34, 35, 38))
        dr.rectangle([W_ - j_, 0, W_, H_], fill=(34, 35, 38))
        save_pil("window_%d" % n, im, (0.70, 1.27))

    for n in range(1, 13):
        window_unit(n)

    def notice(px=200):
        """The notices between the windows (g7_ticketbay2019): white sheets 0.48 x 0.46; their print is too
        small to read in any reference, so it is drawn as faint grey lines of type, not words."""
        W_, H_ = int(0.48 * px), int(0.46 * px)
        im = Image.new("RGB", (W_, H_), (240, 240, 238))
        dr = ImageDraw.Draw(im)
        for k, y in enumerate(np.arange(0.06, 0.40, 0.03)):
            dr.line([(0.05 * px, y * px), ((0.43 - 0.10 * (k % 3 == 2)) * px, y * px)], fill=(205, 205, 206),
                    width=2)
        save_pil("notice", im, (0.48, 0.46))

    notice()

    # ------------------------------------------------------------ Gate 7 geometry
    COLS = {"C2": (338.56, (-42.79, 108.95)), "C3": (341.29, (-37.54, 110.83)), "C4": (345.16, (-30.04, 113.39)),
            "C5": (349.02, (-22.45, 115.68)), "C6": (352.88, (-14.69, 117.61)), "C7": (356.69, (-6.89, 119.05)),
            "C8": (360.47, (0.99, 119.96))}

    # Column wraps (C4, C3, C2): a 24-sided ring 15 mm proud of the 0.40 m column, one repeat centred outward.
    for key in ("C4", "C3", "C2"):
        bc, (cx, cy) = COLS[key]
        n_, R = 24, 0.415
        ang = [bc + 60 - k * 360.0 / n_ for k in range(n_ + 1)]
        for k in range(n_):
            a0, a1 = ang[k], ang[k + 1]
            p0 = (cx + R * math.sin(math.radians(a0)), cy + R * math.cos(math.radians(a0)))
            p1 = (cx + R * math.sin(math.radians(a1)), cy + R * math.cos(math.radians(a1)))
            o = u((a0 + a1) / 2)
            s0, s1 = k * WRAP_C / n_, (k + 1) * WRAP_C / n_
            face("col_wrap7", [(*p0, Z(2.87)), (*p1, Z(2.87)), (*p1, Z(3.58)), (*p0, Z(3.58))], (o[0], o[1], 0.0),
                 [(s0, 0), (s1, 0), (s1, 0.71), (s0, 0.71)])
            q0 = (cx + 0.39 * math.sin(math.radians(a0)), cy + 0.39 * math.cos(math.radians(a0)))
            q1 = (cx + 0.39 * math.sin(math.radians(a1)), cy + 0.39 * math.cos(math.radians(a1)))
            face("dark_frame", [(*p0, Z(2.87)), (*p1, Z(2.87)), (*q1, Z(2.87)), (*q0, Z(2.87))], (0.0, 0.0, -1.0))
            face("col_red", [(*p0, Z(3.58)), (*p1, Z(3.58)), (*q1, Z(3.58)), (*q0, Z(3.58))], UP)

    # CCTV on C4, C3, C2 (vid2026_t422): two white box cameras under the soffit (+4.60), one looking straight
    # out, one turned 60 degrees east, each on a short drop from the soffit
    flat("cctv_white", (228, 228, 226), 2.0)
    for key in ("C4", "C3", "C2"):
        bc, (cx, cy) = COLS[key]
        o = np.array(u(bc), float)
        e = np.array([math.cos(math.radians(bc)), -math.sin(math.radians(bc))])
        for d_ in (o, o * math.cos(math.radians(60)) + e * math.sin(math.radians(60))):
            d_ = d_ / np.linalg.norm(d_)
            c_ = np.array([cx, cy]) + d_ * (0.415 + 0.16)
            hbox("cctv_white", c_, d_, 0.32, 0.15, 4.26, 4.42, bottom=True)
            hbox("dark_frame", c_ + d_ * 0.165, d_, 0.01, 0.11, 4.28, 4.40)
            hbox("cctv_white", np.array([cx, cy]) + d_ * 0.50, d_, 0.05, 0.05, 4.42, 4.60, top=False)

    # --- the Level 1 concourse behind the doors and lanes (glass cut 335.34-349.09 in marvel.glb).
    # Measured on the Jun 2019 indoor pano (S8e-zEW8Ht0ZIZPprEsBoA, camera P(342.5, r108.8)) and checked against
    # the Nov 2026 concourse photo (white ceiling, round downlights): a flat white ceiling band at +3.00 runs
    # 3.8 m in from the glass, ending in a white bulkhead up to +4.60; past it the underside of the Level 2 tier
    # (marvel.glb). The concrete floor runs level to the bar railing at the back of the lower tier, r 100.
    # Floor and ceiling run 1.5 degrees past each end of the cut so the view along the concourse never ends.
    VB_E, VB_W = 348.67, 336.2
    CC_E, CC_W = 350.6, 333.8
    WB = -3.8                                                       # white ceiling band depth
    flat("conc_floor", (120, 120, 118), 3.0)
    flat("ceiling_white", (236, 236, 233), 1.5)
    flat("lamp_lit", (255, 246, 228), 0.0)
    flat("rail_dark", (46, 48, 50), 2.0)

    def d_back(b):
        return 100.0 - float(np.linalg.norm(glass(b, 0.0)))

    ms = marks(CC_E, CC_W)
    for a, c in zip(ms, ms[1:]):
        fa, fc = glass(a, -0.12), glass(c, -0.12)
        ba, bc_ = glass(a, d_back(a)), glass(c, d_back(c))
        face("conc_floor", [(*fa, Z(0.0)), (*fc, Z(0.0)), (*bc_, Z(0.0)), (*ba, Z(0.0))], UP)
        wa, wc = glass(a, WB), glass(c, WB)
        face("ceiling_white", [(*fa, Z(3.00)), (*fc, Z(3.00)), (*wc, Z(3.00)), (*wa, Z(3.00))], (0.0, 0.0, -1.0))
    strip("ceiling_white", CC_E, CC_W, 3.00, 4.60, WB, inward=True)                 # bulkhead, facing in
    strip("interior_dark", CC_E, CC_W, 2.30, 3.00, -0.12, inward=True)              # back of the sign band

    # round downlights, 0.2 m, two rows 2.4 m apart along the band
    n_lamp = max(1, int(span(CC_E, CC_W, -1.3) / 2.4))
    for k in range(n_lamp):
        for dd in (-1.3, -3.0):
            bl = deg(CC_E, 1.2 + 2.4 * k, dd)
            cpt = glass(bl, dd)
            ring = [(cpt[0] + 0.1 * math.cos(t), cpt[1] + 0.1 * math.sin(t), Z(2.995))
                    for t in np.linspace(0, 2 * math.pi, 13)[:-1]]
            face("lamp_lit", ring, (0.0, 0.0, -1.0))

    # the bar railing at the back of the lower tier: posts every 2 m, top rail at 1.0 m, mid rail at 0.5 m
    rb = marks(CC_E, CC_W)
    for a, c in zip(rb, rb[1:]):
        pa, pc = glass(a, d_back(a)), glass(c, d_back(c))
        dv = pc - pa
        L = float(np.linalg.norm(dv))
        for zz in (0.50, 0.97):
            hbox("rail_dark", (pa + pc) / 2, dv, L, 0.05, zz, zz + 0.05, bottom=True)
    n_post = int(span(CC_E, CC_W, d_back(342.0)) / 2.0)
    for k in range(n_post + 1):
        bp = deg(CC_E, 2.0 * k, d_back(342.0))
        hbox("rail_dark", glass(bp, d_back(bp)), tang(bp), 0.05, 0.05, 0.0, 1.02)

    def rotor(b, d):
        """A full-height turnstile rotor: a steel post and three wings of horizontal bars, 0.5 m long."""
        c = glass(b, d)
        hbox("steel", c, tang(b), 0.09, 0.09, 0.0, 2.20)
        for wing in range(3):
            a = math.radians(30 + 120 * wing)
            ax = tang(b) * math.cos(a) + u(b) * math.sin(a)
            for zz in np.arange(0.18, 2.10, 0.13):
                hbox("steel", c + ax * 0.30, ax, 0.50, 0.03, zz, zz + 0.03, bottom=True)
        hbox("dark_frame", c, tang(b), 1.0, 1.0, 2.20, 2.30, bottom=True)              # the head over it

    # --- the door bay, 348.67 to 345.86: a full-height turnstile, then three double grilled doors
    DB_E, DB_W = 348.67, 345.86
    mod_len = span(DB_E, DB_W, 0.03) / 4
    edges_b = [DB_E] + [deg(DB_E, mod_len * k, 0.03) for k in (1, 2, 3)] + [DB_W]
    for k in range(4):
        be, bw = edges_b[k], edges_b[k + 1]
        bm = (be + bw) / 2
        if k == 0:
            rotor(bm, -0.55)
            for bb in (be, bw):
                radial("bars_v", bb, -1.1, 0.0, 0.0, 2.30, +1, fit=1.0)
                radial("bars_v", bb, -1.1, 0.0, 0.0, 2.30, -1, fit=1.0)
        else:
            leaf = (mod_len - 0.10) / 2
            for side in (-1, 1):
                panel("grille_door", deg(bm, side * leaf / 2, 0.03), 0.03, leaf, 0.0, 2.30)
        fbox("dark_frame", be, 0.0, 0.09, 0.12, 0.0, 2.30)                             # posts
    fbox("dark_frame", DB_W, 0.0, 0.09, 0.12, 0.0, 2.30)
    strip("dark_frame", DB_E, DB_W, 2.24, 2.30, 0.07)                                  # head rail

    # --- the turnstile bank, 345.86 to 336.2: one lane every ~1.2 m between black posts. Each lane is closed by
    # a grilled leaf (g7_doors2019, vid2026_t448: mesh with a mid rail, a scanning plate at its head); behind it,
    # inside, stand the waist-high ticket gates (g7in y350_t95, y350_t125 and through the grilles in both
    # outside views): a steel pedestal on every post line with a dark reader on its outer end and two guide
    # rails running on into the concourse.
    TB_E, TB_W = DB_W, VB_W
    nl = max(1, int(round(span(TB_E, TB_W, 0.0) / 1.2)))
    lane = span(TB_E, TB_W, 0.0) / nl
    lb = [deg(TB_E, lane * k, 0.0) for k in range(nl)] + [TB_W]
    for k in range(nl):
        be, bw = lb[k], lb[k + 1]
        panel("grille_lane", (be + bw) / 2, 0.03, lane - 0.10, 0.0, 2.12)
        panel("lane_plate", (be + bw) / 2, 0.05, 0.46, 2.12, 2.24)
    for bb in lb:
        fbox("dark_frame", bb, 0.0, 0.10, 0.12, 0.0, 2.30)
        r_ = u(bb)
        hbox("steel", glass(bb, -0.80), r_, 0.90, 0.22, 0.0, 0.95)                    # the pedestal
        hbox("board_black", glass(bb, -0.49), r_, 0.28, 0.24, 0.95, 1.07)             # the reader
        for zz in (0.48, 0.86):                                                      # guide rails
            hbox("steel", glass(bb, -1.65), r_, 0.80, 0.04, zz, zz + 0.04, bottom=True)
        hbox("steel", glass(bb, -2.03), r_, 0.04, 0.04, 0.0, 0.90)                    # the rails' end post
    strip("dark_frame", TB_E, TB_W, 2.24, 2.30, 0.07)

    # --- over the doors and lanes: louvres (two tiers), the Gate 7 sign, the lintel
    def louvred(b_hi, b_lo, h0, h1, mat):
        n_ = max(1, int(round(span(b_hi, b_lo, 0.03) / 1.4)))
        strip(mat, b_hi, b_lo, h0, h1, 0.03, fit=n_ * 1.4, v0=h0)

    louvred(DB_E, B_SIGN_E, 2.30, 3.00, "louvre_lo")
    louvred(B_SIGN_W, VB_W, 2.30, 3.00, "louvre_lo")
    louvred(DB_E, VB_W, 3.00, 3.76, "louvre_hi")
    strip("gate7_sign", B_SIGN_E, B_SIGN_W, 2.30, 3.00, 0.08, fit=sign_len, v0=2.30)
    for bb, fc in ((B_SIGN_E, +1), (B_SIGN_W, -1)):
        radial("dark_frame", bb, 0.03, 0.08, 2.30, 3.00, fc)
    TRI_LINTEL_W = deg(DB_E, 1.5, 0.03)
    strip("tri_clad", DB_E, TRI_LINTEL_W, 3.76, 4.60, 0.03)
    strip("lintel_grey", TRI_LINTEL_W, VB_W, 3.76, 4.60, 0.03)
    strip("tri_clad", 348.8, DB_E, 0.0, 3.76, 0.03)                                  # the sliver east of the doors

    # --- the triangle-clad wall west of the lanes, with its black board
    TW_E, TW_W = VB_W, 334.9          # west end measured on g7_west2019 (sv.py ray, glass line)
    strip("tri_clad", TW_E, TW_W, 0.0, 4.60, 0.05, u0=11.0)
    radial("tri_clad", TW_W, 0.0, 0.05, 0.0, 4.60, -1)
    fbox("board_black", deg(TW_E, 0.66, 0.05), 0.08, 1.20, 0.06, 1.20, 2.30)   # centre 335.87, g7_west2019

    # --- the Ticket Sales booths, 348.8 to 0.69, built out 2.55 m between columns C5 to C8
    BD = 2.55
    BO_W, BO_E = 348.8, 360.69
    radial("tri_clad", BO_W, 0.0, BD, 0.0, 4.60, -1)                                  # west return wall
    # the tall black directory board on the west return wall, left of the doors in g7_doors2019 (about 1.7 to
    # 3.3 m up, 0.7 m out along the return; placed against the photo)
    hbox("board_black", glass(BO_W, 0.7) - tang(BO_W) * 0.03, u(BO_W), 0.70, 0.06, 1.70, 3.30)
    radial("tri_clad", BO_E, 0.0, BD, 0.0, 4.60, +1)                                  # east return wall
    FR = 0.65                     # the charcoal frame runs this far each side of a column's centre
    cuts_b = [BO_E, deg(COLS["C8"][0], FR, BD)]
    for key in ("C7", "C6"):
        cb = COLS[key][0]
        cuts_b += [deg(cb, -FR, BD), deg(cb, FR, BD)]
    cuts_b += [deg(COLS["C5"][0], -FR, BD), BO_W]
    for i in range(0, len(cuts_b), 2):                 # the frames round C8, C7, C6, C5
        strip("dark_frame", cuts_b[i], cuts_b[i + 1], 0.0, 4.60, BD)
    bays = [(cuts_b[i], cuts_b[i + 1]) for i in range(1, len(cuts_b) - 1, 2)]          # east to west
    first_no = {0: 9, 1: 5, 2: 1}                 # C7-C8 holds 9-12, C6-C7 5-8, C5-C6 1-4 (numbered eastward)
    for bi, (be, bw) in enumerate(bays):
        w = span(be, bw, BD)
        strip("dark_frame", be, bw, 0.0, 0.12, BD)
        strip("tri_clad", be, bw, 0.12, 2.33, BD, u0=3.0 * bi)
        booth_header("booth_header_%d" % bi, w)
        strip("booth_header_%d" % bi, be, bw, 2.33, 3.06, BD, fit=w, v0=2.33)
        booth_glazing("booth_glazing_%d" % bi, w)
        strip("booth_glazing_%d" % bi, be, bw, 3.06, 4.26, BD, fit=w, v0=3.06)
        strip("dark_frame", be, bw, 4.26, 4.60, BD)
        mid = (be + bw) / 2
        for j, off in enumerate((-2.55, -0.85, 0.85, 2.55)):          # left to right from outside
            bwin = deg(mid, off, BD)
            no = first_no[bi] + 3 - j
            panel("window_%d" % no, bwin, BD + 0.012, 0.70, 1.04, 2.31)
            fbox("tray_white", bwin, BD + 0.07, 0.74, 0.12, 0.38, 1.00, bottom=True)
        for off in (-1.70, 0.0, 1.70):
            panel("notice", deg(mid, off, BD), BD + 0.012, 0.48, 1.61, 2.07)

    # ------------------------------------------------------------ Threaded Field (Simon Perry, 1999-2000)
    # The green coil on the north-west forecourt, in front of Gate 7: one painted steel tube about 0.32 m thick wound
    # into a conical spiral. Its open end stands in the air at the big end; the first loop rests on the deck and the
    # three smaller ones dive into it, each cut off at the deck (the pointed ends in the photos are the tube meeting
    # the floor at a slant). Shape and size: fitted to the photo c008 (row scans of the tube, every loop's top and
    # cut ends, rms about 10 px). Plan position: the Esri aerial, whose footprint agrees with the fit's length to
    # 5 %; the photo's camera sat about 4.7 m from where the facade fit put it, so the fit is moved 3.24 m west and
    # 3.36 m north onto the aerial. Tube diameter from c008's widths at the fit's depths.
    def coil_paint(name, tile_u=2.0, tile_v=2 * math.pi * 0.16, px=200):
        """Green semi-gloss paint, chipped in places down to a paler yellow-green coat (c008 close crops)."""
        nu, nv = int(tile_u * px), int(round(tile_v * px))
        ky = np.fft.fftfreq(nv)[:, None] * nv / tile_v
        kx = np.fft.fftfreq(nu)[None, :] * nu / tile_u
        k = np.hypot(kx, ky)

        def fbm(scale, octaves=4):          # FFT-filtered noise: wraps both ways, so the tube shows no seam
            out = np.zeros((nv, nu))
            for o in range(octaves):
                f = np.fft.fft2(rng.normal(0, 1, (nv, nu)))
                out += np.real(np.fft.ifft2(f * np.exp(-(k * scale / 2 ** o) ** 2))) * 0.5 ** o
            return (out - out.mean()) / out.std()
        img = np.zeros((nv, nu, 3)) + np.array([62.0, 128.0, 44.0])
        img += fbm(0.6, 2)[..., None] * np.array([4.0, 7.0, 3.0])              # brushing and fade
        chip = fbm(0.35)
        m = chip > 1.55                                                         # the chipped patches
        rim = (chip > 1.35) & ~m
        img[rim] = img[rim] * 0.8
        img[m] = np.array([150.0, 180.0, 108.0]) + rng.normal(0, 6, (int(m.sum()), 3))
        img[rng.random((nv, nu)) > 0.9985] = (172.0, 190.0, 140.0)             # small chips
        img += rng.normal(0, 2.0, (nv, nu, 1))
        save(name, img, (tile_u, tile_v))

    coil_paint("coil_paint")
    NRM["coil_paint"] = []
    CX = [-35.004 - 3.24, 127.724 + 3.36, 240.139]                             # first loop's centre, axis heading
    CR = [2.523, 2.373, 2.221, 1.778, 1.402, 1.044, 0.913]                     # loop radius at the knots
    CH = [2.571, 2.495, 2.284, 1.687, 0.925, 0.271, -0.032]                    # loop centre height at the knots
    CS = [0.443, 1.249, 2.215, 2.104, 2.110, 1.000]                            # advance along the axis between knots
    CK = [0, 0.25, 0.75, 1.75, 2.75, 3.75, 4.3]                                # knots, in turns from the open end
    LAM, ELL, TUBE_R = -0.042, 1.113, 0.16
    COIL_Z = DECK_Z + 0.04            # c008's fit rested the first loop for a 0.13 m tube; this one is 0.16
    ax = u(CX[2])
    nn = -np.array([ax[1], -ax[0]])                     # winds clockwise seen from the open end (c008)
    sk = np.r_[0, np.cumsum(CS)]
    tt = np.linspace(0, 4.3, 1300)
    Rt, Ht, St = np.interp(tt, CK, CR), np.interp(tt, CK, CH), np.interp(tt, CK, sk)
    ph = -2 * np.pi * tt
    xy = (np.array(CX[:2])[None] + ax[None] * (St + LAM * Rt * np.sin(ph))[:, None]
          + nn[None] * (ELL * Rt * np.cos(ph))[:, None])
    C = np.c_[xy, Ht + Rt * np.sin(ph)]
    T = np.gradient(C, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]
    NS = 20
    rings, norms = [], []
    ref = np.cross(T[0], (0.0, 0.0, 1.0))
    ref /= np.linalg.norm(ref)
    ang = np.linspace(0, 2 * np.pi, NS + 1)
    for i in range(len(C)):                                # parallel transport: the tube does not twist
        ref = ref - T[i] * float(np.dot(ref, T[i]))
        ref /= np.linalg.norm(ref)
        b2 = np.cross(T[i], ref)
        nr = np.cos(ang)[:, None] * ref[None] + np.sin(ang)[:, None] * b2[None]
        norms.append(nr)
        rings.append(C[i][None] + nr * TUBE_R)
    CIRC = 2 * math.pi * TUBE_R

    def clip_up(P, N, UV):
        """Sutherland-Hodgman against the deck: keeps the part of a face above the floor."""
        oP, oN, oU = [], [], []
        for k_ in range(len(P)):
            a, b = k_, (k_ + 1) % len(P)
            za, zb = P[a][2], P[b][2]
            if za >= 0:
                oP.append(P[a])
                oN.append(N[a])
                oU.append(UV[a])
            if (za >= 0) != (zb >= 0):
                f = za / (za - zb)
                oP.append(P[a] + (P[b] - P[a]) * f)
                nv_ = N[a] + (N[b] - N[a]) * f
                oN.append(nv_ / np.linalg.norm(nv_))
                oU.append(UV[a] + (UV[b] - UV[a]) * f)
        return oP, oN, oU

    def coil_face(P, N, UV):
        g.poly("coil_paint", [(p_[0], p_[1], p_[2] + COIL_Z) for p_ in P], [tuple(map(float, x_)) for x_ in UV])
        NRM["coil_paint"].append([tuple(map(float, n_)) for n_ in N])

    for i in range(len(C) - 1):
        for j in range(NS):
            P = [rings[i][j], rings[i][j + 1], rings[i + 1][j + 1], rings[i + 1][j]]
            N = [norms[i][j], norms[i][j + 1], norms[i + 1][j + 1], norms[i + 1][j]]
            UV = [np.array((seg[i], CIRC * j / NS)), np.array((seg[i], CIRC * (j + 1) / NS)),
                  np.array((seg[i + 1], CIRC * (j + 1) / NS)), np.array((seg[i + 1], CIRC * j / NS))]
            if min(p_[2] for p_ in P) >= 0:
                coil_face(P, N, UV)
            elif max(p_[2] for p_ in P) > 0:
                P, N, UV = clip_up(P, N, UV)
                if len(P) >= 3:
                    coil_face(P, N, UV)
    # the open end, cut square (c008): a disc facing back along the tube
    disc = [np.array((0.15 + 0.15 * math.cos(a_), 0.15 + 0.15 * math.sin(a_))) for a_ in ang[:NS]]
    coil_face([rings[0][j] for j in range(NS)][::-1], [-T[0]] * NS, disc[::-1])

    # ------------------------------------------------------------ hand over to Blender
    data = {"parts": g.parts, "tile": TILE, "text": TEXT, "tex": TEX, "out": OUT, "nrm": NRM}
    pkl = os.path.join(TEX, "_gates.pkl")
    with open(pkl, "wb") as f:
        pickle.dump(data, f)
    subprocess.run([BLENDER, "-b", "--python", os.path.abspath(__file__), "--", "--export", pkl], check=True)
    os.remove(pkl)


# ================================================================ stage 2 (Blender's Python)
def _stage2(pkl):
    import bpy
    data = pickle.load(open(pkl, "rb"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    mats = {}

    def material(name):
        if name in mats:
            return mats[name]
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        path = os.path.join(data["tex"], name + ".png")
        if os.path.exists(path):
            tx = nt.nodes.new("ShaderNodeTexImage")
            tx.image = bpy.data.images.load(path)
            nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
            # Wire mesh and bar screens (saved RGBA): alpha clip, exported as glTF alphaMode MASK. Blender holds
            # every image with 4 channels, so the PNG's own colour type decides (byte 25: 6 = RGBA). Marked MASK,
            # an opaque face is left off the stands' light in a match and a ceiling took the grass's green.
            with open(path, "rb") as fh:
                rgba = fh.read(26)[25] in (4, 6)
            if rgba:
                rd = nt.nodes.new("ShaderNodeMath")
                rd.operation = "ROUND"
                nt.links.new(tx.outputs["Alpha"], rd.inputs[0])
                nt.links.new(rd.outputs[0], b.inputs["Alpha"])
        b.inputs["Roughness"].default_value = 0.3 if "glass" in name else (0.4 if ("steel" in name or "paint" in name) else 0.85)
        b.inputs["Metallic"].default_value = 1.0 if "steel" in name else 0.0
        if name.endswith("_lit"):          # downlights: emissive, exported as glTF emissive + strength
            b.inputs["Emission Color"].default_value = (1.0, 0.95, 0.86, 1.0)
            b.inputs["Emission Strength"].default_value = 4.0
        mats[name] = m
        return m

    for mat, faces in data["parts"].items():
        V, F, UV = [], [], []
        for pts, uvs in faces:
            o = len(V)
            V += pts
            F.append(list(range(o, o + len(pts))))
            UV.append(uvs)
        me = bpy.data.meshes.new(mat)
        me.from_pydata(V, [], F)
        me.update()
        tu, tv = data["tile"].get(mat, (4.0, 4.0))
        ul = me.uv_layers.new(name="UVMap")
        for poly, uv in zip(me.polygons, UV):
            for k, li in enumerate(poly.loop_indices):
                ul.data[li].uv = (uv[k][0] / tu, uv[k][1] / tv)
        if mat in data.get("nrm", {}):
            me.normals_split_custom_set([n for fn in data["nrm"][mat] for n in fn])
        me.materials.append(material(mat))
        ob = bpy.data.objects.new("gates_" + mat, me)
        sc.collection.objects.link(ob)

    for text, font, size, c, n, depth, mat in data["text"]:
        cu = bpy.data.curves.new("t", "FONT")
        cu.body = text
        cu.font = bpy.data.fonts.load(os.path.join(FONTS, font))
        cu.size = size
        cu.extrude = depth / 2
        cu.align_x = "CENTER"
        cu.align_y = "CENTER"
        ob = bpy.data.objects.new("gates_txt", cu)
        sc.collection.objects.link(ob)
        ob.rotation_euler = (math.pi / 2, 0, math.atan2(n[0], -n[1]))
        ob.location = c
        cu.materials.append(material(mat))
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.convert(target="MESH")
        ob.select_set(False)

    os.makedirs(os.path.dirname(data["out"]), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(data["out"]), export_format="GLB", export_apply=True)
    print("wrote", data["out"], {k: len(v) for k, v in data["parts"].items()}, len(data["text"]), "lettering")


if __name__ == "__main__":
    if "--export" in sys.argv:
        _stage2(sys.argv[sys.argv.index("--export") + 1])
    else:
        _stage1()
