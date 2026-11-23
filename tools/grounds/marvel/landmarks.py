"""The landmark buildings round Marvel Stadium, modelled from Google Earth (Marvel rebuild, stage 6).

The plain extrusions of tools/grounds/marvel/surrounds.py stand in for the city further out; the
buildings next to the ground, which every fly-through and many match shots see, are built here one by
one from Google Earth's 3D views (.claude/review/marvel/landmarks/ge_*.png): their real shape, their
folds, fins, balconies and bands as geometry, and only fine detail (mullions, floor lines, panel
joints) in their textures. Footprints are OpenStreetMap's (surrounds.py's frame: x east, y north, the
model's 0, 0); heights are OpenStreetMap's where it has them (surveyed from nearmap), else read off
Google Earth against the stadium. Writes assets/grounds/marvel/landmarks.glb; surrounds.py leaves these
footprints (LANDMARK_WAYS) out of buildings.bin.

    python3 tools/grounds/marvel/landmarks.py        (pip bpy; reads the cached /tmp/marvel_surrounds_*.osm)

Map data (c) OpenStreetMap contributors, ODbL. Looks only.
"""
import glob
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import surrounds as S  # noqa: E402

OUT = os.path.join(HERE, "..", "..", "..", "assets", "grounds", "marvel", "landmarks.glb")
TEX = os.path.join(HERE, "landmark_tex")
RNG = np.random.default_rng(11)


# ---------------------------------------------------------------- textures (fine detail only)
def _save(name, img):
    os.makedirs(TEX, exist_ok=True)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").save(os.path.join(TEX, name + ".png"))


def curtain(name, glass, frame, bay=1.5, floor=3.6, px=24, slab=0.35, noise=8.0, nb=4, nf=2):
    """A glass curtain wall: panes `bay` wide and `floor` tall, thin mullions, a spandrel at each
    floor. One tile is `nb` bays by `nf` floors."""
    W, H = int(nb * bay * px), int(nf * floor * px)
    img = np.zeros((H, W, 3), float)
    img[:] = glass
    for j in range(nf):
        for i in range(nb):
            y0, x0 = int(j * floor * px), int(i * bay * px)
            img[y0:y0 + int(floor * px), x0:x0 + int(bay * px)] += RNG.normal(0, noise)
    x = (np.arange(W) + 0.5) / px
    y = (np.arange(H) + 0.5) / px
    img[:, (x % bay) < 0.08] = frame
    img[((y % floor) < slab), :] = np.array(frame) * 0.8 + np.array(glass) * 0.2
    _save(name, img)


def panels(name, colour, joint, w=1.5, h=1.2, px=24, noise=5.0, holes=None, hole_size=0.6, hole_p=0.5):
    """Flat cladding panels with dark joints. One tile is 4 by 4 panels."""
    W, H = int(4 * w * px), int(4 * h * px)
    img = np.zeros((H, W, 3), float)
    img[:] = colour
    for j in range(4):
        for i in range(4):
            img[int(j * h * px):int((j + 1) * h * px), int(i * w * px):int((i + 1) * w * px)] += RNG.normal(0, noise)
    x = (np.arange(W) + 0.5) / px
    y = (np.arange(H) + 0.5) / px
    img[:, (x % w) < 0.05] = joint
    img[(y % h) < 0.05, :] = joint
    if holes:
        # small dark triangular openings in about half the panels (NAB's silver sections, ge c_e)
        for j in range(4):
            for i in range(4):
                if RNG.random() < hole_p:
                    x0, y0 = int((i + 0.5 * (1 - hole_size)) * w * px), int((j + 0.5 * (1 - hole_size)) * h * px)
                    hh = int(hole_size * h * px)
                    for r in range(hh):
                        # point down in one panel, up in the next, as the real screen's folded triangles
                        k = r if (i + j) % 2 == 0 else hh - 1 - r
                        ww = int((hh - k) / hh * hole_size * w * px)
                        xs = x0 + (int(hole_size * w * px) - ww) // 2
                        img[y0 + r, xs:xs + ww] = holes
    _save(name, img)


def solar_roof(name, px=16):
    """A roof under solar arrays: dark grey-navy membrane, panel rows 1.0 m deep in runs, 0.6 m pale walkways every
    4 rows. 8 m by 8 m a tile."""
    W = H = 8 * px
    rng = np.random.default_rng(31)
    img = np.zeros((H, W, 3), float) + (88, 94, 104) + rng.normal(0, 3.0, (H, W, 3))
    y = (np.arange(H) + 0.5) / px
    x = (np.arange(W) + 0.5) / px
    for k in range(8):
        if k % 4 == 3:
            img[(y >= k) & (y < k + 0.6)] = (150, 152, 150)
            continue
        rows = (y >= k + 0.05) & (y < k + 0.95)
        img[np.ix_(rows, (x % 2.0) < 1.94)] = (40, 48, 64)
        img[np.ix_(rows, (x % 2.0) >= 1.94)] = (120, 124, 128)
    _save(name, img)
    TILE[name] = (8.0, 8.0)


def stripe_roof(name, px=16):
    """A white roof membrane with long runs of blue solar panels, 2.4 m of panels to 2.0 m of white, as Google Earth's
    c_nw foreground roof shows. 8.8 m by 8.8 m a tile."""
    W = H = int(8.8 * px)
    rng = np.random.default_rng(37)
    img = np.zeros((H, W, 3), float) + (214, 216, 214) + rng.normal(0, 3.0, (H, W, 3))
    y = (np.arange(H) + 0.5) / px
    x = (np.arange(W) + 0.5) / px
    rows = (y % 4.4) < 2.4
    img[np.ix_(rows, (x % 1.1) < 1.04)] = (58, 76, 112)
    img[np.ix_(rows, (x % 1.1) >= 1.04)] = (150, 160, 176)
    _save(name, img)
    TILE[name] = (8.8, 8.8)


def flat(name, colour, noise=4.0):
    img = np.zeros((32, 32, 3), float) + colour + RNG.normal(0, noise, (32, 32, 3))
    _save(name, img)


# tile size in metres of each texture (u along the wall, v up)
TILE = {}


def make_textures():
    # NAB, 700 Bourke Street (Google Earth ge_nab_a/b): dark blue reflective glass in 1.5 m panes with
    # thin dark mullions; the light sections silver-white panels with a few slot windows; roof plant grey.
    # Colour set like for like (PC check round 7): Google Earth's east faces are in sun (NAB's white fins read
    # (218, 225, 230)), the game's are in shade (the sun is in the south-west), so the shaded render cannot be
    # matched pixel for pixel. Rendered with the sun where Google Earth's was (preinspect PREINSPECT_SUN=60,45,1.45,
    # the fins then at 204), the glass between the fins must read Google Earth's (54, 79, 103): dark blue glass.
    # Round 8: the PC read it about 18 too red (the sun's warm sheen on it), so its red is taken out: a teal-navy.
    # Round 10 audit: Google Earth's east blocks each read their own tone (the glass of each block is set at its
    # own angle, and the panes vary pane to pane), and the pane grid shows: one glass a block, a lighter frame
    # and a larger tile (8 bays by 4 floors) so the per-pane tones do not repeat every 6 m.
    # Round 11 (PC check of round 10): blocks 1-2 read B-R +48 against Google Earth's +21, too blue: grey-navy
    # Round 12 (PC check of round 11): the east glass overshot to grey, (68, 88, 104) B-R 36 against Google Earth's
    # (56, 83, 109) B-R 52: about 10 less red and 6 more blue
    for nm, gl in (("nab_glass_a", (36, 58, 78)), ("nab_glass_b", (44, 66, 86)), ("nab_glass_c", (32, 52, 72)),
                   ("nab_glass_d", (52, 74, 94)), ("nab_glass_w", (40, 61, 81))):
        curtain(nm, gl, (74, 92, 110), bay=1.5, floor=3.9, noise=10.0, nb=8, nf=4)
        TILE[nm] = (12.0, 15.6)
    # the roof (Google Earth obl_e, nabroof1): dark grey membrane under a grid of solar panels and glazing
    # round 12 (Google Earth obl_e close up): dark grey-navy roof covered in rows of dark solar panels with pale
    # walkways between them
    solar_roof("nab_roof")
    flat("nab_rooflight", (68, 94, 100), noise=5.0)  # teal glass pyramids (ge12b nab_top); round 12 self-check: greyer, it read a teal block
    flat("roof_garden", (92, 104, 70), noise=12.0)
    # PC check round 2: the north tip's panels rendered (88, 105, 136) against GE (60, 87, 113): greyer, darker
    # round 12 (PC check: dots, where Google Earth shows dark triangular openings): big triangles in most panels
    panels("nab_silver", (160, 174, 184), (128, 138, 148), w=1.5, h=1.3, holes=(46, 54, 64), hole_size=0.85, hole_p=0.85)
    TILE["nab_silver"] = (6.0, 5.2)
    flat("fin_white", (232, 234, 236))
    flat("corner_red", (176, 104, 88))
    flat("nab_terra", (150, 74, 54), noise=8.0)  # the roof's folded plates: darker brick-red than the slots (PC round 11)  # copper red-brown: GE in sun (184, 113, 94); (206, 118, 90) rendered orange
    flat("roof_grey", (138, 138, 134), noise=6.0)
    flat("roof_dark", (78, 82, 88), noise=6.0)
    # Southern Cross's roof: pale weathered metal, the valleys' glazing grey-blue, the sides' louvres
    panels("sx_roof", (186, 178, 162), (168, 160, 146), w=3.0, h=1.0, noise=3.0)
    TILE["sx_roof"] = (12.0, 4.0)
    flat("sx_glass", (150, 166, 176))
    curtain("sx_louvre", (96, 108, 118), (150, 156, 160), bay=1.2, floor=0.6, slab=0.25, noise=4.0)
    TILE["sx_louvre"] = (4.8, 1.2)
    flat("podium_glass", (70, 92, 112))
    # Docklands' pale offices: grey-white panels, dark ribbon glazing (ge_seven_b, ge_aflhouse_b)
    panels("pale_panel", (204, 206, 206), (168, 170, 172), w=1.8, h=1.4)
    TILE["pale_panel"] = (7.2, 5.6)
    curtain("dark_glass", (58, 70, 84), (46, 52, 60), bay=1.8, floor=2.4, slab=0.0, noise=7.0)
    TILE["dark_glass"] = (7.2, 4.8)
    # the two sawtooth towers north-east of the ground (PC check round 7, like for like with the sun where Google Earth's
    # was): Google Earth reads their glass bands (88, 110, 124) and their pale bands (153, 167, 173), a blue-grey tower
    curtain("grey_glass", (46, 54, 62), (70, 76, 82), bay=1.8, floor=2.4, slab=0.0, noise=4.0)  # round 12: the balconies' dark recesses
    # round 12 (PC check of round 11): they read white-grey; Google Earth shows grey walls with dark balconies
    panels("band_panel", (166, 170, 172), (150, 154, 156), w=1.8, h=1.4)
    TILE["band_panel"] = (7.2, 5.6)
    TILE["grey_glass"] = (7.2, 4.8)
    # round 10: the round office reads dark glass in Google Earth (ext_090, c_w): dark panes, grey frames
    curtain("office_glass", (50, 64, 78), (110, 118, 124), bay=1.5, floor=2.7, slab=0.0, noise=8.0)
    TILE["office_glass"] = (6.0, 5.4)
    flat("white_band", (226, 228, 228))
    # round 12 (own audit of the round 11 PC renders): the round office read light blue-grey bands; Google Earth
    # (ext_045, c_sw) shows dark glass bands with thin pale rails
    flat("round_glass", (40, 52, 64), noise=3.0)
    flat("seven_glass", (66, 94, 124), noise=4.0)
    stripe_roof("stripe_roof")
    flat("roof_white", (214, 216, 212), noise=4.0)  # the former Seven building's blue curtain wall (seven_w, c_nw)
    # round 12 (PC check of round 11): Victoria Point's glass is blue under its white slab edges, not green-grey
    curtain("vp_glass", (60, 84, 110), (88, 104, 120), bay=1.5, floor=3.05, slab=0.0, noise=3.0)
    TILE["vp_glass"] = (6.0, 6.1)
    # round 12 (PC check of round 11): 720 Bourke still read blue mottling; Google Earth shows crisp white wavy
    # balcony bands over dark glass, and a glass atrium roof. One flat dark glass (no pane-to-pane tone to mottle)
    flat("bourke_glass", (40, 50, 60), noise=2.0)
    panels("atrium_glass", (140, 150, 156), (176, 180, 182), w=3.0, h=1.5, noise=4.0)  # self-check: (118,138,150) read a blue lid
    TILE["atrium_glass"] = (6.0, 3.0)
    # round 10: HOME Docklands' two towers north-west of the ground (Google Earth obl_n, obl_nw, ext_135): dark
    # navy glass in a white frame grid, about 1.4 m windows every 1.6 m
    flat("home_frame", (214, 216, 214))
    # round 11 read lilac in sun at (76, 84, 90); round 12 (PC check of round 11): far too light, Google Earth is dark
    # navy glass in the white grid
    flat("home_glass", (40, 52, 70), noise=3.0)
    flat("near_wall", (200, 202, 200))
    panels("plaza_red", (186, 128, 112), (164, 116, 102), w=1.2, h=0.6, noise=8.0)
    TILE["plaza_red"] = (4.8, 2.4)
    flat("tree_leaf", (70, 88, 52), noise=10.0)
    # 720 Bourke's slab edges (round 11, PC check: far too pale, mottled): off-white over a mid-grey balustrade, low
    # contrast, so the sub-pixel bands at range average to Google Earth's grey instead of a moire of white on dark
    # round 12 (PC check of round 11): white wavy bands, crisp (the grey of round 11 lost them)
    flat("bourke_edge", (226, 228, 228), noise=2.0)
    graffiti("graffiti")
    TILE["graffiti"] = (48.0, 4.0)
    ivy("ivy")
    TILE["ivy"] = (6.0, 4.0)  # the low offices south of Bourke Street: white-grey walls (obl_s)
    # PC check round 2: Google Earth reads the two curved towers west of the ground as green-grey glass
    curtain("tower_glass", (84, 102, 98), (120, 132, 128), bay=1.5, floor=3.05, slab=0.0, noise=9.0)
    TILE["tower_glass"] = (6.0, 6.1)
    # round 12 self-check (obl_s): the bands must read about half the face: the balustrades are solid white upstands
    flat("balustrade", (212, 214, 214), noise=2.0)
    flat("steel", (196, 198, 200))
    flat("steel_dark", (196, 200, 198))  # galvanised, light in Google Earth
    flat("rock_a", (156, 150, 138), noise=10.0)
    flat("rock_b", (128, 122, 112), noise=10.0)
    flat("slab_grey", (150, 160, 156))  # slab edges: grey-green, not white (PC check round 2)
    flat("timber", (74, 64, 52))
    flat("concrete_deck", (170, 168, 160))
    for n in ("bourke_edge", "home_frame", "home_glass", "near_wall", "tree_leaf", "fin_white", "corner_red", "roof_grey", "roof_dark", "sx_glass", "podium_glass", "white_band", "steel", "rock_a", "rock_b",
              "timber", "concrete_deck", "balustrade", "slab_grey", "steel_dark", "round_glass", "bourke_glass", "seven_glass", "roof_white"):
        TILE[n] = (4.0, 4.0)


# ---------------------------------------------------------------- mesh building
class Geo:
    """Faces gathered per material: vertices (x east, y north, z up), quads/polys, UVs in metres."""

    def __init__(self):
        self.parts = {}

    def poly(self, mat, pts, uvs=None):
        pts = [tuple(map(float, p)) for p in pts]
        if uvs is None:
            uvs = _auto_uv(pts)
        self.parts.setdefault(mat, []).append((pts, [tuple(map(float, u)) for u in uvs]))

    def wall(self, mat, a, b, z0, z1, u0=0.0):
        """A vertical quad from plan point a to b (outward face on the right of a->b when the
        footprint runs counter-clockwise), z0..z1. Returns the run length."""
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        self.poly(mat, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)],
                  [(u0, z0), (u0 + L, z0), (u0 + L, z1), (u0, z1)])
        return L

    def cap(self, mat, ring, z, up=True):
        r = ring if up else ring[::-1]
        self.poly(mat, [(x, y, z) for x, y in r], [(x, y) for x, y in r])

    def prism(self, ring, z0, z1, wall, top="roof_grey", bottom=False):
        ring = ccw(ring)
        u = 0.0
        for i in range(len(ring)):
            u += self.wall(wall(i) if callable(wall) else wall, ring[i], ring[(i + 1) % len(ring)], z0, z1, u)
        if top:
            self.cap(top, ring, z1)
        if bottom:
            self.cap(bottom if isinstance(bottom, str) else top, ring, z0, up=False)


def _auto_uv(pts):
    p = np.array(pts)
    n = np.cross(p[1] - p[0], p[2] - p[0])
    if abs(n[2]) > 0.7 * np.linalg.norm(n):
        return [(x, y) for x, y, _ in pts]
    t = np.array([n[1], -n[0], 0.0])
    t /= np.linalg.norm(t) + 1e-9
    return [(float(np.dot(q, t)), float(q[2])) for q in p]


def ccw(ring):
    ring = [tuple(map(float, q)) for q in ring]
    if ring[0] == ring[-1]:
        ring = ring[:-1]
    a = sum(ring[i][0] * ring[(i + 1) % len(ring)][1] - ring[(i + 1) % len(ring)][0] * ring[i][1] for i in range(len(ring)))
    return ring if a > 0 else ring[::-1]


def outward(a, b):
    """Unit outward normal of a counter-clockwise footprint edge a->b."""
    d = np.array(b, float) - np.array(a, float)
    d /= np.linalg.norm(d)
    return np.array([d[1], -d[0]])


def inset(ring, d):
    """The counter-clockwise footprint `ring` moved `d` inward with mitred corners (vertex for vertex)."""
    ring = [np.array(q, float) for q in ccw(ring)]
    out = []
    for i in range(len(ring)):
        n0 = outward(ring[i - 1], ring[i])
        n1 = outward(ring[i], ring[(i + 1) % len(ring)])
        m = n0 + n1
        k = 1.0 + float(np.dot(n0, n1))
        out.append(tuple(ring[i] - m / max(k, 0.3) * d))
    return out


_FAC = {}


def facade_tex(wall, glass, floor, sill, head, phase, win=None):
    """A floor-high facade texture for banded(): the wall's band from the floor to `sill`, glass to `head` with a
    mullion every 1.5 m (or, with win=(width, spacing), punched windows `width` wide every `spacing` m), wall again
    to the next floor. Round 9 (PC check): modelled 0.3-1 m sills and reveals are under a pixel at broadcast range and
    shimmered as wavy stripes; as a texture the engine's mipmaps average them. Returns the texture's name."""
    key = (wall, glass, round(floor, 3), round(sill, 3), round(head, 3), round(phase % floor, 3), win)
    if key in _FAC:
        return _FAC[key]
    name = "fac%d" % len(_FAC)
    px = 24
    wc = np.asarray(Image.open(os.path.join(TEX, wall + ".png")).convert("RGB"), float).reshape(-1, 3).mean(0)
    gc = np.asarray(Image.open(os.path.join(TEX, glass + ".png")).convert("RGB"), float).reshape(-1, 3).mean(0)
    span = 6.0 if win is None else win[1] * max(1, round(6.0 / win[1]))
    W, H = int(round(span * px)), int(round(floor * px))
    x = (np.arange(W) + 0.5) / px
    y = ((np.arange(H)[::-1] + 0.5) / px + phase) % floor   # image rows run top-down, v (height) runs up
    img = np.zeros((H, W, 3), float) + wc + RNG.normal(0, 3.0, (H, W, 3))
    band = (y >= sill) & (y < head)
    if win is None:
        cols = (x % 1.5) >= 0.16  # round 11: 0.08 m mullions vanished in the mipmaps (Victoria Point read a plain slab)
    else:
        cols = (x % win[1]) < win[0]
    m = band[:, None] & cols[None, :]
    img[m] = gc + RNG.normal(0, 4.0, (int(m.sum()), 3))
    _save(name, img)
    TILE[name] = (span, floor)
    _FAC[key] = name
    return name


def banded(g, ring, z0, z1, floor, sill, head, recess, wall, glass, top="roof_grey", parapet=1.0, reveal=None, win=None):
    """Floors of ribbon windows: from each floor's level a solid band `sill` high on the face, then glass up to
    `head`, then solid to the next floor. Round 9: drawn as one flat face per edge carrying a floor-high texture
    (facade_tex), not modelled sills and reveals, which shimmered at range; `recess` and `reveal` are kept for the
    callers' record. win=(width, spacing) gives punched windows instead of ribbons."""
    out = ccw(ring)
    nf = max(1, int(round((z1 - z0) / floor)))
    fl = (z1 - z0) / nf
    tex = facade_tex(wall, glass, fl, sill * fl / floor, head * fl / floor, z0, win)
    u = 0.0
    for i in range(len(out)):
        u += g.wall(tex, out[i], out[(i + 1) % len(out)], z0, z1, u)
    if parapet:
        g.prism(out, z1, z1 + parapet, wall, top=None)
        g.prism(inset(out, 0.3), z1, z1 + parapet, wall, top=None)
        rim = inset(out, 0.3)
        for i in range(len(out)):
            j = (i + 1) % len(out)
            g.poly(wall, [(*out[i], z1 + parapet), (*out[j], z1 + parapet), (*rim[j], z1 + parapet), (*rim[i], z1 + parapet)])
    if top:
        g.cap(top, out, z1)


def cylinder_ring(c, r, n=24, a0=0.0, a1=2 * math.pi):
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * k / n), c[1] + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n)]


def lattice_mast(g, mat, c, z0, h, w0=3.0, w1=0.8, bay=3.0):
    """A square steel lattice mast: four legs tapering from w0 to w1 wide, braced every `bay`."""
    nb = max(1, int(h / bay))
    def corner(k, z):
        w = w0 + (w1 - w0) * (z - z0) / h
        sx, sy = ((1, 1), (-1, 1), (-1, -1), (1, -1))[k]
        return np.array([c[0] + sx * w / 2, c[1] + sy * w / 2, z])
    for k in range(4):
        strut(g, mat, corner(k, z0), corner(k, z0 + h), 0.22)
        for b in range(nb):
            za, zb = z0 + b * h / nb, z0 + (b + 1) * h / nb
            strut(g, mat, corner(k, za), corner((k + 1) % 4, zb), 0.1)
            strut(g, mat, corner(k, zb), corner((k + 1) % 4, zb), 0.1)
    strut(g, mat, np.r_[c, z0 + h], np.r_[c, z0 + h + 6.0], 0.18)


# ---------------------------------------------------------------- the buildings
def _inside(pt, poly):
    x, y = pt
    c = False
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[i - 1]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


def osm_ways():
    files = sorted(glob.glob("/tmp/marvel_surrounds_*.osm"))
    if not files:
        sys.exit("run tools/grounds/marvel/surrounds.py first (it caches the map tiles in /tmp)")
    _, ways = S.load(files[0], files[1:])
    return {t.get("_id"): (t, p) for t, p in ways if t.get("_id")}


def shade(g, mat, p, t, n, w, size, depth, z):
    """NAB's white sun-shade: a downward-pointing triangle `w` wide and `size` tall on the wall, its top
    edge standing `depth` off the wall at the middle and its point on the wall, so it reads as a white
    triangle with its two halves lit differently (Google Earth c_e, 2026-11-23). p is the top-left corner."""
    p = np.array(p, float)
    A = np.r_[p, z + size]
    B = np.r_[p + t * w, z + size]
    C = np.r_[p + t * w / 2, z]
    M = np.r_[p + t * w / 2 + n * depth, z + size]
    g.poly(mat, [A, C, M])
    g.poly(mat, [M, C, B])
    g.poly(mat, [A, M, B])


def polyline_points(pts, n):
    """n+1 points spaced evenly by length along the polyline pts."""
    pts = np.array(pts, float)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    s = np.linspace(0, d[-1], n + 1)
    return np.stack([np.interp(s, d, pts[:, 0]), np.interp(s, d, pts[:, 1])], 1), d[-1]


def nab(g, ring, h=72.0):
    """National Australia Bank, 700 Bourke Street (2004): a triangle in plan between the rail yard,
    Wurundjeri Way and Bourke Street (Google Earth ge_nab_a, ge_nab_b, c_e).
    - Its faces are folded into tall facets about 14 m wide, each leaning out 2.2 m at alternate
      edges, so the light breaks across them as Google Earth shows.
    - The south and east faces are grey-blue glass with white triangular shades climbing in diagonal
      rows. The east face is four glass blocks and a silver-white north tip, split by three slanting
      slots clad orange-red; the south face has red-orange strips down two folds.
    - The west face, to the stadium, is glass under close-set white shades that leave diagonal dark bands.
    - It stands on a 7 m glazed ground storey set back behind white V struts (c_e's white zigzag)."""
    ring = ccw(ring)
    P = [np.array(q) for q in ring]
    faces = [("south", [P[0], P[1]]), ("east", [P[1], P[2]]), ("west", P[2:] + [P[0]])]
    base, top, fold = 7.0, h, 2.2
    # The east face (Google Earth c_e, PC check of 2026-11-23) is four glass blocks and a silver end, split
    # by three slots clad orange-red that run the full height on a slant: (centre along the face from its
    # south corner, width, how far the slot's top sits along from its foot), read off the 119 m face.
    # Round 8 (PC sun-on check): the red read as 10% of the face against Google Earth's 1.3%, and the face as one
    # flat wall where Google Earth shows four blocks with angled joins. Each slot is a V notch 6 m wide at the face:
    # its two sides angled glass, which catch the light differently from the blocks, and only a 1 m red strip at
    # the back, 4 m in.
    # Round 9 (PC: "the four blocks are coplanar, the same shading, no fold depth"): each east block is one flat
    # plane turned a few degrees from the next, its ends standing out from the face line by these (start, end)
    # metres, so one block's end stands proud of its neighbour and shows its red return wall, as Google Earth's
    # do; the notches between are 3.5 m wide at the face, all red inside.
    slots = {"east": ((0.27, 3.5, 3.0), (0.53, 3.5, -2.5), (0.69, 3.5, 3.0))}
    yaw = {"east": ((0.0, 6.0), (6.0, 0.5), (0.5, 6.0), (5.0, 0.0))}
    depth, back = 3.0, 1.0
    rng = np.random.default_rng(700)
    outline = []
    for name, pl in faces:
        L = polyline_length(pl)
        cuts = [(c * L - w / 2, c * L + w / 2, sh) for c, w, sh in slots.get(name, ())]
        edges = [0.0] + [x for c in cuts for x in c[:2]] + [L]
        shift = [0.0] + [c[2] for c in cuts for _ in (0, 1)] + [0.0]
        u = 0.0
        yw = yaw.get(name)
        nF = outward(pl[0], pl[-1])
        for bi in range(0, len(edges), 2):
            s0, s1 = edges[bi], edges[bi + 1]
            sub = _sub_polyline(pl, s0, s1)
            k = max(1, int(round((s1 - s0) / 14.0)))
            pts, _ = polyline_points(sub, k)
            if yw:
                y0_, y1_ = yw[bi // 2]
                pts = pts + nF[None, :] * np.linspace(y0_, y1_, k + 1)[:, None]
            for j in range(k):
                p0, p1 = pts[j], pts[j + 1]
                w = float(np.linalg.norm(p1 - p0))
                t = (p1 - p0) / w
                n = outward(p0, p1)
                f = ((s0 + (j + 0.5) * (s1 - s0) / k) / L)
                if name == "west":
                    # round 12 (Google Earth nab_nw, PC check obl_nw: ours read dark navy): the west face is tall bands
                    # of light grey panels with dark triangular openings alternating with dark glass under white shades
                    mat = "nab_silver" if j % 2 == 0 else "nab_glass_w"
                elif name == "east":
                    mat = "nab_silver" if f > 0.88 else ("nab_glass_a", "nab_glass_b", "nab_glass_c", "nab_glass_d")[bi // 2]
                else:
                    mat = ("nab_glass_b", "nab_glass_a", "nab_glass_c")[min(2, j * 3 // k)]
                # alternate edges lean out (a block's two ends stay plumb, so its slots' walls are flat)
                lean0 = n * fold * (j % 2 == 1) * (yw is None)
                lean1 = n * fold * ((j + 1) % 2 == 1 and j + 1 < k) * (yw is None)
                if j == 0:
                    lean0 = lean0 + t * shift[bi]
                if j == k - 1:
                    lean1 = lean1 + t * shift[bi + 1]
                g.poly(mat, [(*p0, base), (*p1, base), (*(p1 + lean1), top), (*(p0 + lean0), top)],
                       [(u, base), (u + w, base), (u + w, top), (u, top)])
                outline.append(p0 + lean0)
                outline.append(p1 + lean1)
                # the leaning edge leaves a triangular gap to its neighbour: a narrow fold wall closes it
                if j + 1 < k and yw is None:
                    nn = outward(pts[j + 1], pts[min(j + 2, k)])
                    q = pts[j + 1]
                    g.poly(mat, [(*q, base), (*(q + lean1), top), (*(q + nn * fold * ((j + 1) % 2 == 1)), top)])
                # the ground storey: glass set back 2 m, a white V strut pair per facet in front of it
                g.wall("podium_glass", p0 - n * 2.0, p1 - n * 2.0, 0.0, base)
                g.poly("fin_white", [(*(p0 - n * 2.0), base - 0.6), (*(p1 - n * 2.0), base - 0.6),
                                     (*p1, base), (*p0, base)])
                for a_, b_ in ((p0, p0 + t * w / 2), (p0 + t * w / 2, p1)):
                    strut(g, "fin_white", np.r_[a_, base], np.r_[(a_ + b_) / 2 - n * 0.6, 0.0], 0.45)
                    strut(g, "fin_white", np.r_[b_, base], np.r_[(a_ + b_) / 2 - n * 0.6, 0.0], 0.45)
                # red-orange strips down the south face's folds at its thirds
                if name == "south" and k > 2 and j in (k // 3, 2 * k // 3):
                    g.poly("corner_red", [(*p0, base), (*(p0 + t * 3.2), base), (*(p0 + t * 3.2 + lean0), top),
                                          (*(p0 + lean0), top)])
                if mat.startswith("nab_glass"):
                    # white shades, one row a floor (3.9 m), one every 6.5 m along a row, each row stepped
                    # 2.2 m on so they climb in diagonals: about five a row on a 30 m block and eleven rows,
                    # 3.4 m wide and 5.6 m tall, as counted on Google Earth's c_e (2026-11-23)
                    # The west face, to the stadium, carries them far closer (Google Earth from the west, PC check
                    # round 2): 4.2 m wide every 4.8 m, so the face reads pale with the dark glass left in
                    # diagonal bands between them.
                    # Round 8: the east face's shades read 28% of it on the PC against Google Earth's 10.6%: 2.4 m by 3.9 m.
                    # Round 9: Google Earth's east shades are slim (about 1.7 m by 3.5 m), every 4.5 m, and the rows are
                    # uneven, about a third of the places empty: PC measured ours 19.6% white against its 10.6%.
                    # Round 12 (PC check: the east shades sat on a regular grid; Google Earth's run in staggered
                    # diagonals rising to the right, about 60 degrees, some places empty): one every 9 m along a row,
                    # each floor's row stepped 2.2 m on, about one in six left out, a little jitter
                    # Round 12 (nab_nw): the west face's glass bands carry them as the east's do, a little larger
                    sw, sp, sh, st = (2.4, 6.0, 4.0, 2.2) if name == "west" else (1.7, 9.0, 3.5, 2.2)
                    for r, z in enumerate(np.arange(base + 1.0, top - sh - 0.9, 3.9)):
                        for s_ in np.arange((r * st - u) % sp, w - sw - 0.2, sp):
                            if rng.random() < 0.16:
                                continue
                            s_ = float(np.clip(s_ + rng.uniform(-0.3, 0.3), 0.0, w - sw - 0.2))
                            s_ = float(s_) + 0.2  # clear of the facet edge
                            lean = (lean0 + (lean1 - lean0) * (s_ / w)) * ((z - base) / (top - base))
                            shade(g, "fin_white", p0 + t * s_ + lean + n * 0.6, t, n, sw, sh, 0.35, z)  # 0.6 m clears the folded facet, which is not flat
                u += w
            if bi + 2 < len(edges):
                # the slot to the next block: a V notch, its sides angled glass and a red strip at its back, leaning
                # along the face as the blocks' edges do; glass ground storey carried across
                a0 = _at(pl, s1) + (nF * yw[bi // 2][1] if yw else 0.0)
                b0 = _at(pl, edges[bi + 2]) + (nF * yw[bi // 2 + 1][0] if yw else 0.0)
                t = (b0 - a0) / np.linalg.norm(b0 - a0)
                n = outward(a0, b0)
                sa, sb = t * shift[bi + 1], t * shift[bi + 2]
                mid = (_at(pl, s1) + _at(pl, edges[bi + 2])) / 2 - nF * depth
                ai, bi_ = mid - t * back / 2, mid + t * back / 2
                sm = (sa + sb) / 2
                g.poly("corner_red", [(*a0, base), (*ai, base), (*(ai + sm), top), (*(a0 + sa), top)])
                g.poly("corner_red", [(*ai, base), (*bi_, base), (*(bi_ + sm), top), (*(ai + sm), top)])
                g.poly("corner_red", [(*bi_, base), (*b0, base), (*(b0 + sb), top), (*(bi_ + sm), top)])
                g.wall("podium_glass", a0 - n * 2.0, b0 - n * 2.0, 0.0, base)
                g.poly("fin_white", [(*(a0 - n * 2.0), base - 0.6), (*(b0 - n * 2.0), base - 0.6),
                                     (*b0, base), (*a0, base)])
                g.poly("roof_grey", [(*(ai + sm), top), (*(bi_ + sm), top), (*(b0 + sb), top), (*(a0 + sa), top)])
                u += float(np.linalg.norm(b0 - a0))
    # parapet and roof over the facets' tops, plant set back on the roof
    rim = ccw([tuple(q) for q in outline])
    for i in range(len(rim)):
        g.wall("nab_silver", rim[i], rim[(i + 1) % len(rim)], top, top + 1.4)
    # the roof: folded dark glass planes rising from the parapet to a ridge point over the middle, as
    # Google Earth's obl_e and obl_sw show it (not flat)
    nab_roof(g, rim, P, top)
    # the ground storey's soffit
    g.cap("roof_grey", [tuple(q) for q in ring], base - 0.6, up=False)


def _clip_line(p, d, tri):
    """The segment of the line p + s d inside the convex counter-clockwise triangle tri, or None."""
    lo, hi = -1e9, 1e9
    for i in range(3):
        a, b = np.array(tri[i]), np.array(tri[(i + 1) % 3])
        n = -outward(a, b)  # inward
        den = float(np.dot(d, n)); num = float(np.dot(p - a, n))
        if abs(den) < 1e-9:
            if num < 0:
                return None
            continue
        s_ = -num / den
        if den > 0:
            lo = max(lo, s_)
        else:
            hi = min(hi, s_)
    return (p + d * lo, p + d * hi) if hi - lo > 1.0 else None


def nab_roof(g, rim, P, top):
    """NAB's roof as Google Earth's straight-down shot shows it (ge12b nab_top, 2026-11-23): a flat dark grey roof
    under solar arrays with walkways; a field of small teal pyramid rooflights over the middle; round cooling
    towers and a plant room towards the north; a garden strip with a kerb along the east parapet (0.27-0.62 of the
    east face); and two short runs of brick-red folded plates inside it. No sawtooth rows."""
    z = top + 0.3
    g.cap("nab_roof", rim, z)
    tri = [np.array(q) for q in ccw([tuple(q) for q in (P[0], P[1], P[2])])]
    A, B, C = np.array(P[0], float), np.array(P[1], float), np.array(P[2], float)
    # east face runs B (south) to C (north); in_e points into the roof from it
    te = (C - B) / np.linalg.norm(C - B)
    in_e = -outward(B, C)
    Le = float(np.linalg.norm(C - B))
    inner = [np.array(q) for q in inset([tuple(q) for q in tri], 6.0)]
    tw = (A - C) / np.linalg.norm(A - C)
    in_w = -outward(C, A)
    # Round 12 (Google Earth obl_e close up, ge12): no sawtooth rows (the roof is solar arrays edge to edge, in
    # nab_roof's texture); the garden sits right behind the east parapet over the second block, 0.29 to 0.48 of the
    # face, sunken 1 m; the folded brick-red plates are one patch: a band behind the garden and, over the third
    # block, right up to the parapet. Round 11's strip along the whole parapet and three stepped rows were too much.
    # Round 12 (Google Earth straight down on the roof, ge12b nab_top): the garden runs along the east parapet from
    # 0.27 to 0.62 of the east face, about 12 m deep; inside it a zigzag strip of brick-red folded plates from 0.33 to
    # 0.87, 12 to 26 m in; south-west of those a field of small glass pyramids (rooflights) in staggered rows; the rest
    # of the roof is solar arrays (nab_roof's texture). No sawtooth rows.
    # (the cap is one polygon, so the garden is laid on it inside a 0.6 m planter kerb, not sunk through it)
    g0, g1, d0, d1 = 0.27 * Le, 0.62 * Le, 0.8, 12.0
    q = [B + te * g0 + in_e * d0, B + te * g1 + in_e * d0, B + te * g1 + in_e * d1, B + te * g0 + in_e * d1]
    g.poly("roof_garden", [(*x, z + 0.05) for x in ccw([tuple(x) for x in q])])
    for i in range(4):
        a_, b_ = q[i], q[(i + 1) % 4]
        g.poly("roof_grey", [(*a_, z), (*b_, z), (*b_, z + 0.6), (*a_, z + 0.6)])
        g.poly("roof_grey", [(*b_, z), (*a_, z), (*a_, z + 0.6), (*b_, z + 0.6)])
    rng = np.random.default_rng(71)
    for k in range(16):  # shrubs and small trees along the garden
        c = B + te * (g0 + (g1 - g0) * (k + 0.5) / 16) + in_e * rng.uniform(d0 + 1.5, d1 - 1.5)
        if k % 4 == 1:
            tree(g, c, z, 4.5, 1.8)
        else:
            g.prism(cylinder_ring(c, 1.0, 6), z, z + 1.0, "roof_garden", top="roof_garden")

    def folded(p0, p1, w_dir, width, n, rise=2.4):
        """A zigzag of folded plates: n diamonds along p0-p1, each ridge rising `rise` at its middle."""
        L = float(np.linalg.norm(p1 - p0)); t = (p1 - p0) / L
        for i in range(n):
            a0 = p0 + t * L * i / n
            a1 = p0 + t * L * (i + 1) / n
            m = (a0 + a1) / 2 + w_dir * width / 2
            peak = np.r_[m, z + rise]
            for x0, x1 in ((a0, a1), (a1, a1 + w_dir * width), (a1 + w_dir * width, a0 + w_dir * width), (a0 + w_dir * width, a0)):
                g.poly("nab_terra", [(*x0, z), (*x1, z), tuple(peak)])
    folded(B + te * (0.33 * Le) + in_e * 12.5, B + te * (0.87 * Le) + in_e * 12.5, in_e, 7.0, 9)
    folded(B + te * (0.40 * Le) + in_e * 19.5, B + te * (0.80 * Le) + in_e * 19.5, in_e, 6.5, 6)
    # the rooflight pyramids: teal glass in staggered rows, about 4.5 m square in nab_top (20 px at 0.26 m a pixel)
    for r in range(6):
        for c_ in range(9):
            f_ = 0.10 + 0.042 * c_ + 0.021 * (r % 2)
            d_ = 15.0 + 5.5 * r
            ctr = B + te * (f_ * Le) + in_e * d_
            if not _inside(tuple(ctr), [tuple(x) for x in inner]):
                continue
            sq = [ctr + (te * sx + in_e * sy) * 2.2 for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            for i in range(4):
                g.poly("nab_rooflight", [(*sq[i], z), (*sq[(i + 1) % 4], z), (*ctr, z + 2.0)])

    # plant: six round cooling towers and a plant room, north of the middle (Google Earth's white drums)
    cen = (A + B + C) / 3.0
    pc = cen + (C - cen) * 0.25 + in_e * 0.0
    for i in range(6):
        c = pc + te * (3.6 * (i % 3)) + tw * (3.6 * (i // 3))
        g.prism(cylinder_ring(c, 1.5, 10), z, z + 2.4, "steel", top="roof_grey")
    pr = pc - te * 6.0 - tw * 2.0
    room = [pr, pr + te * 8.0, pr + te * 8.0 + in_w * 5.0, pr + in_w * 5.0]
    g.prism([tuple(x) for x in room], z, z + 3.2, "roof_grey", top="roof_grey")


def _at(pl, s):
    """The plan point s metres along the polyline pl."""
    pl = np.array(pl, float)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pl, axis=0), axis=1))]
    return np.array([np.interp(s, d, pl[:, 0]), np.interp(s, d, pl[:, 1])])


def _sub_polyline(pl, s0, s1):
    """The part of polyline pl from s0 to s1 metres along it, its corners kept."""
    pl = np.array(pl, float)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pl, axis=0), axis=1))]
    return [_at(pl, s0)] + [pl[i] for i in range(len(pl)) if s0 < d[i] < s1] + [_at(pl, s1)]


def polyline_length(pl):
    return float(sum(np.linalg.norm(np.array(pl[i + 1]) - np.array(pl[i])) for i in range(len(pl) - 1)))


def strut(g, mat, a, b, r):
    """A square-section strut from a to b, r wide."""
    a, b = np.array(a, float), np.array(b, float)
    d = b - a
    d /= np.linalg.norm(d)
    u = np.cross(d, [0, 0, 1.0])
    if np.linalg.norm(u) < 1e-6:
        u = np.array([1.0, 0, 0])
    u /= np.linalg.norm(u)
    v = np.cross(d, u)
    c = [u * r / 2 + v * r / 2, -u * r / 2 + v * r / 2, -u * r / 2 - v * r / 2, u * r / 2 - v * r / 2]
    for i in range(4):
        g.poly(mat, [a + c[i], a + c[(i + 1) % 4], b + c[(i + 1) % 4], b + c[i]])


def seven(g, ring):
    """The former Seven Network headquarters, 150-170 Harbour Esplanade (Google Earth ge_seven_b,
    ge_ferry_b, c_w, c_nw): four storeys of pale grey panels with ribbon windows set back in each
    floor, a rooftop plant room and the station's steel lattice mast, and at its south corner on
    the promenade a round drum in tiers that steps in towards the top."""
    ring = ccw(ring)
    # OpenStreetMap draws the drum as the arc of the footprint's first points; the block takes the chord
    arc = [q for q in ring if math.hypot(q[0] + 147.5, q[1] - 40.5) < 11.0]
    block = [q for q in ring if q not in arc[1:-1]]
    # round 12 (PC check of round 11, c_nw; Google Earth seven_w, seven_nw close up): its walls are a blue glass
    # curtain wall with thin pale spandrels, not pale panels with ribbon windows
    banded(g, block, 0.0, 16.8, 4.2, 0.45, 4.0, 0.35, "pale_panel", "seven_glass")
    c = np.mean(np.array(block), 0)
    g.prism([tuple(c + (np.array(q) - c) * 0.4) for q in block], 16.8, 20.2, "pale_panel", top="roof_grey")
    # the mast is a slim lattice column standing against the west face, by Harbour Esplanade, from the ground to about
    # 34 m (triangulated from seven_w: 0.82 of the way along the west wall from its south end); round 11 had it on the
    # roof's east half, about 340 px left of Google Earth's in c_nw
    a_, b_ = np.array((-168.6, 54.3)), np.array((-180.0, 87.7))
    mp = a_ + (b_ - a_) * 0.82 - outward(tuple(a_), tuple(b_)) * 1.2  # the map draws this edge clockwise: minus is west
    assert mp[0] < -178.5
    lattice_mast(g, "steel", tuple(mp), 0.0, 28.0, w0=1.4, w1=0.9, bay=2.5)  # with its 6 m spike, 34 m
    d = (-147.5, 40.5)
    banded(g, cylinder_ring(d, 10.4, 28), 0.0, 12.6, 4.2, 1.0, 3.6, 0.3, "pale_panel", "dark_glass", parapet=0.6)
    banded(g, cylinder_ring(d, 8.2, 24), 12.6, 16.8, 4.2, 1.0, 3.6, 0.3, "pale_panel", "dark_glass", parapet=0.6)
    g.prism(cylinder_ring(d, 6.0, 20), 16.8, 18.8, "pale_panel", top="roof_grey")


def round_office(g, ring, h=29.0):
    """The curved glass office south-west of the stadium on Harbour Esplanade (Google Earth
    ge_aflhouse_b, c_sw): eight floors of glass, each floor's slab edge a white band standing out."""
    banded(g, ring, 0.0, h, h / 6, 0.3, 3.4, 0.3, "white_band", "round_glass", parapet=1.2)  # round 12: thin pale rails


def ferry(g, ring):
    """The ferry terminal shed on the harbour plaza: a low glazed box under a white gable roof with
    a glazed ridge (Google Earth ge_ferry_b)."""
    ring = ccw(ring)
    banded(g, ring, 0.0, 4.2, 4.2, 0.9, 3.7, 0.2, "white_band", "office_glass", top=None, parapet=0)
    P = np.array(ring)
    # roof: ridge along the long axis
    e = [np.linalg.norm(P[(i + 1) % len(P)] - P[i]) for i in range(len(P))]
    i = int(np.argmax(e))
    a, b = P[i], P[(i + 1) % len(P)]
    t = (b - a) / np.linalg.norm(b - a)
    n = np.array([-t[1], t[0]])
    c = P.mean(0)
    L = float(np.linalg.norm(b - a)) / 2 + 0.6
    proj = [float(np.dot(q - c, n)) for q in P]
    w0, w1 = min(proj) - 0.6, max(proj) + 0.6
    ra, rb = c - t * L, c + t * L
    for side, wv in ((w0, w0), (w1, w1)):
        pass
    r0 = np.r_[ra, 6.0]
    r1 = np.r_[rb, 6.0]
    e0 = [np.r_[ra + n * w0, 4.2], np.r_[rb + n * w0, 4.2]]
    e1 = [np.r_[ra + n * w1, 4.2], np.r_[rb + n * w1, 4.2]]
    g.poly("white_band", [e0[0], e0[1], r1, r0])
    g.poly("white_band", [e1[1], e1[0], r0, r1])
    g.poly("white_band", [e0[0], r0, e1[0]])
    g.poly("white_band", [e1[1], r1, e0[1]])
    # glazed ridge light
    g.poly("office_glass", [np.r_[ra + n * 1.2, 6.25], np.r_[rb + n * 1.2, 6.25], np.r_[rb - n * 1.2, 6.25], np.r_[ra - n * 1.2, 6.25]])


def rocks(g, shore, water, width=4.5, seed=5):
    """Rock armour along a sea wall: boulders 0.7 to 1.6 m across in a band `width` wide on the water
    side of the polyline `shore` (Google Earth: Harbour Esplanade's grey-brown rip-rap)."""
    rng = np.random.default_rng(seed)
    P = np.array(shore, float)
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]
        L = float(np.linalg.norm(b - a))
        if L < 0.5:
            continue
        t = (b - a) / L
        n = np.array([t[1], -t[0]])
        if not water(tuple((a + b) / 2 + n * 2.0)):
            n = -n
        for _ in range(int(L * width / 1.1)):
            p = a + t * rng.uniform(0, L) + n * rng.uniform(0.2, width)
            r = rng.uniform(0.35, 0.8)
            hgt = rng.uniform(0.4, 0.95) * (1.0 - 0.5 * float(np.dot(p - a, n)) / width)
            k = rng.integers(5, 7)
            ang = rng.uniform(0, 2 * math.pi)
            base = [(p[0] + r * math.cos(ang + 2 * math.pi * m / k) * rng.uniform(0.75, 1.15),
                     p[1] + r * math.sin(ang + 2 * math.pi * m / k) * rng.uniform(0.75, 1.15)) for m in range(k)]
            tip = (p[0] + rng.normal(0, 0.12), p[1] + rng.normal(0, 0.12), hgt)
            mat = ("rock_a", "rock_b")[int(rng.integers(0, 2))]
            for m in range(k):
                g.poly(mat, [(*base[m], 0.0), (*base[(m + 1) % k], 0.0), tip])


def piles(g, start, along, out, rows, per_row, step=2.8, gap=3.0, h=1.1):
    """Rows of old timber piles standing out of the water off the plaza (Google Earth ge_ferry_b)."""
    start, along, out = np.array(start, float), np.array(along, float), np.array(out, float)
    for r in range(rows):
        for k in range(per_row):
            c = start + along * r * step + out * (1.5 + k * gap)
            g.prism(cylinder_ring(c, 0.28, 6), 0.0, h, "timber", top="timber")


def gangway(g, ring, edge):
    """The hinged gangway from the plaza's edge down to a floating jetty: 2.2 m wide, with rails."""
    J = np.array(ring, float)
    E = np.array(edge, float)
    best = None
    for q in J:
        for i in range(len(E) - 1):
            a, b = E[i], E[i + 1]
            t = np.clip(np.dot(q - a, b - a) / np.dot(b - a, b - a), 0, 1)
            p = a + (b - a) * t
            d = float(np.linalg.norm(q - p))
            if best is None or d < best[0]:
                best = (d, p, q)
    d, p, q = best
    if d < 0.5:
        return
    t = (q - p) / d
    n = np.array([-t[1], t[0]]) * 1.1
    g.poly("concrete_deck", [(*(p - n), 0.35), (*(p + n), 0.35), (*(q + n), 0.5), (*(q - n), 0.5)][::-1])
    for sgn in (-1, 1):
        strut(g, "steel", np.r_[p + n * sgn, 1.35], np.r_[q + n * sgn, 1.5], 0.06)


def jetty(g, ring, z=0.5):
    """A floating jetty or pontoon from its OpenStreetMap outline: a concrete deck with its edge."""
    g.prism(ring, 0.0, z, "concrete_deck", top="concrete_deck")


def balconies(g, ring, z0, z1, floor, depth, wave=0.0, seed=0, glass="tower_glass", roof="roof_grey"):
    """A residential tower of balconies: each floor a white slab edge on the footprint (pushed out by
    up to `wave` metres in a slow ripple that drifts floor to floor, as 720 Bourke's are), glass set
    back `depth` behind it, a glass balustrade at the slab edge."""
    out = ccw(ring)
    c = np.mean(np.array(out), 0)
    core = inset(out, depth)
    nf = max(1, int(round((z1 - z0) / floor)))
    fl = (z1 - z0) / nf
    u = 0.0
    for i in range(len(core)):
        j = (i + 1) % len(core)
        u += g.wall(glass, core[i], core[j], z0, z1, u)
    for f in range(nf + 1):
        z = z0 + f * fl
        if wave:
            ang = np.arctan2(np.array(out)[:, 1] - c[1], np.array(out)[:, 0] - c[0])
            push = wave * (0.5 + 0.5 * np.sin(3 * ang + f * 0.45 + seed))
            edge = [tuple(np.array(q) + (np.array(q) - c) / (np.linalg.norm(np.array(q) - c) + 1e-6) * pp)
                    for q, pp in zip(out, push)]
        else:
            edge = out
        th = 0.7  # round 12: crisp white bands that hold at range (0.45 still read grey in obl_e)
        for i in range(len(edge)):
            j = (i + 1) % len(edge)
            g.wall("bourke_edge", edge[i], edge[j], z - th, z)
            if f < nf:
                g.wall("balustrade", edge[i], edge[j], z, z + 1.05)
            g.poly("slab_grey", [(*edge[i], z), (*edge[j], z), (*core[j], z), (*core[i], z)][::-1])
            g.poly("slab_grey", [(*edge[i], z - th), (*edge[j], z - th), (*core[j], z - th), (*core[i], z - th)])
    g.cap(roof, out, z1)


def gantries(g, W, step=55.0, reach=450.0):
    """Overhead wiring gantries over the Southern Cross rail yards east of the stadium (Google Earth
    c_e, c_ne): every `step` metres along the yard, a portal over each group of electrified tracks,
    two square masts 8 m tall and a braced girder across at 7.4 m; a lone track gets a cantilever."""
    segs = []
    for t, p in W.values():
        if t.get("railway") != "rail" or t.get("layer", "0").startswith("-") or t.get("electrified") == "no":
            continue
        if t.get("bridge") or t.get("tunnel"):
            continue
        a = np.array(p, float)
        for i in range(len(a) - 1):
            if a[i, 0] > 60 and abs(a[i, 1]) < reach and a[i, 0] < reach:
                segs.append((a[i], a[i + 1]))
    if not segs:
        return
    P = np.vstack([s_[0] for s_ in segs])
    c = P.mean(0)
    d = np.linalg.svd(P - c)[2][0]
    n = np.array([-d[1], d[0]])
    for s0 in np.arange(-reach, reach, step):
        o = c + d * s0
        hits = []
        for a, b in segs:
            # where the cross line o + n * k meets segment a-b
            M = np.array([n, a - b]).T
            if abs(np.linalg.det(M)) < 1e-9:
                continue
            k, t_ = np.linalg.solve(M, a - o)
            if 0.0 <= t_ <= 1.0:
                hits.append(k)
        if not hits:
            continue
        hits.sort()
        groups = [[hits[0]]]
        for k in hits[1:]:
            if k - groups[-1][-1] > 14.0:
                groups.append([k])
            else:
                groups[-1].append(k)
        for gr in groups:
            k0, k1 = gr[0] - 2.4, gr[-1] + 2.4
            p0, p1 = o + n * k0, o + n * k1
            if np.linalg.norm(p0) < 150 or np.linalg.norm(p1) < 150:
                continue
            if len(gr) == 1:
                strut(g, "steel_dark", np.r_[p0, 0.0], np.r_[p0, 7.6], 0.3)
                strut(g, "steel_dark", np.r_[p0, 7.0], np.r_[o + n * (gr[0] + 1.0), 7.0], 0.12)
                continue
            for q in (p0, p1):
                strut(g, "steel_dark", np.r_[q, 0.0], np.r_[q, 8.0], 0.35)
            L = float(np.linalg.norm(p1 - p0))
            m = max(2, int(L / 2.5))
            for zc in (7.0, 7.8):
                strut(g, "steel_dark", np.r_[p0, zc], np.r_[p1, zc], 0.14)
            for i in range(m):
                q0 = p0 + (p1 - p0) * i / m
                q1 = p0 + (p1 - p0) * (i + 1) / m
                strut(g, "steel_dark", np.r_[q0, 7.0 if i % 2 else 7.8], np.r_[q1, 7.8 if i % 2 else 7.0], 0.07)


def southern_cross(g, ring):
    """Southern Cross Station's roof (2006): a field of soft domes over the platforms, six long dunes
    running with the tracks with glazed valleys between, each dune rising into domes about 42 m apart
    with a vent cowl on every crown; the edges about 14 m up, the crowns about 24 m. Under it the
    sides are louvred glass from 7 m, open below (Google Earth sx_top, sx_nw, sx_sw)."""
    from shapely.geometry import Point, Polygon
    P = Polygon(ring)
    A, B, C = np.array([562.5, -275.5]), np.array([358.1, -352.2]), np.array([284.3, -155.4])
    u = (A - B) / np.linalg.norm(A - B)          # across the dunes
    v = (C - B) / np.linalg.norm(C - B)          # along the tracks
    LU, LV = float(np.linalg.norm(A - B)), float(np.linalg.norm(C - B))
    ND, NDOME = 6, 5

    def z_at(a, b):
        fu = (a / LU * ND) % 1.0
        fv = (b / LV * NDOME) % 1.0
        edge = min(a, LU - a, b, LV - b)
        rise = min(1.0, max(0.0, edge / 12.0))
        return 14.0 + rise * 10.0 * math.sin(math.pi * fu) ** 0.8 * (0.45 + 0.55 * math.sin(math.pi * fv) ** 2)

    step = 3.0
    na, nb = int(LU / step), int(LV / step)
    inside = Polygon(ring).buffer(2.0)
    for i in range(na):
        for j in range(nb):
            a0, a1, b0, b1 = i * step, (i + 1) * step, j * step, (j + 1) * step
            cpt = B + u * (a0 + a1) / 2 + v * (b0 + b1) / 2
            if not inside.contains(Point(*cpt)):
                continue
            fu = (((a0 + a1) / 2) / LU * ND) % 1.0
            mat = "sx_glass" if (fu < 0.045 or fu > 0.955) else "sx_roof"
            q = [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]
            g.poly(mat, [(*(B + u * a + v * b), z_at(a, b)) for a, b in q])
    # vent cowls on every dome's crown: a curved hood 4 m wide opening down the dune
    for d in range(ND):
        for k in range(NDOME):
            a = (d + 0.5) * LU / ND
            b = (k + 0.5) * LV / NDOME
            c = B + u * a + v * b
            if not P.contains(Point(*c)):
                continue
            z = z_at(a, b)
            for m in range(4):
                t0, t1 = math.pi * m / 4, math.pi * (m + 1) / 4
                p0 = c + u * 2.0 * math.cos(t0)
                p1 = c + u * 2.0 * math.cos(t1)
                g.poly("white_band", [(*p0, z), (*p1, z), (*(p1 - v * 2.5), z + 2.0 * math.sin(t1)),
                                      (*(p0 - v * 2.5), z + 2.0 * math.sin(t0))])
            # the hood's dark mouth
            g.poly("roof_dark", [(*(c - v * 2.5 + u * 2.0 * math.cos(math.pi * m / 8)), z + 2.0 * math.sin(math.pi * m / 8) * 0.95)
                                 for m in range(9)])
    # the sides under the roof's edge: louvred glass from 7 m up, the concourse open below it
    rr = ccw(ring)
    for i in range(len(rr)):
        a_, b_ = np.array(rr[i]), np.array(rr[(i + 1) % len(rr)])
        def loc(pt):
            w = pt - B
            return z_at(min(max(float(np.dot(w, u)), 0.0), LU), min(max(float(np.dot(w, v)), 0.0), LV))
        g.poly("sx_louvre", [(*a_, 7.0), (*b_, 7.0), (*b_, loc(b_) - 0.3), (*a_, loc(a_) - 0.3)])
        g.poly("roof_grey", [(*a_, 6.4), (*b_, 6.4), (*b_, 7.0), (*a_, 7.0)])


def sawtooth(g, ring, z, pitch=6.0, h=1.8):
    """Rows of sawtooth rooflights over a roof's middle: each a white slope rising `h` over `pitch` to a glazed upright
    face, the rows along the roof's longer side; solar panels on every other slope."""
    rr = np.array(ring, float)
    c0 = rr.mean(0)
    ev, evec = np.linalg.eigh(np.cov((rr - c0).T))
    ax = evec[:, 1]
    cr = np.array([-ax[1], ax[0]])
    pa, pc = (rr - c0) @ ax, (rr - c0) @ cr
    poly = [tuple(q) for q in ring]
    for k, s0 in enumerate(np.arange(pc.min() * 0.6, pc.max() * 0.6 - pitch, pitch)):
        a0, a1 = pa.min() * 0.7, pa.max() * 0.7
        p00, p10 = c0 + ax * a0 + cr * s0, c0 + ax * a1 + cr * s0
        p01, p11 = c0 + ax * a0 + cr * (s0 + pitch), c0 + ax * a1 + cr * (s0 + pitch)
        if not all(_inside(tuple(q), poly) for q in (p00, p10, p01, p11)):
            continue
        slope = "nab_roof" if k % 2 else "roof_white"
        g.poly(slope, [(*p00, z), (*p10, z), (*p11, z + h), (*p01, z + h)])
        g.poly("sx_glass", [(*p11, z), (*p01, z), (*p01, z + h), (*p11, z + h)])
        g.poly("roof_white", [(*p00, z), (*p01, z + h), (*p01, z)])
        g.poly("roof_white", [(*p10, z), (*p11, z), (*p11, z + h)])


def near_buildings(g, W):
    """The buildings within about 250 m that were plain boxes (round 10 audit), each with its own look from Google Earth.
    - HOME Docklands, 685 La Trobe Street (2024): two towers north-west of the ground, 101 m and 28 floors (CTBUH;
      OpenStreetMap gives none, the 2023 city massing predates them), dark glass in a white frame grid.
    - The City of Melbourne's 2023 massing for the offices south of Bourke Street (10757: white-grey walls, dark ribbon
      glazing, dark grey roofs with white parapets, obl_s), the podium under Lacrosse north of the ground (16888) and the
      low building north-west (3046), each part from its own base to its own top."""
    for wid in ("1507403839", "1507403840"):
        # round 10 check: 1.4 m windows left the frame too thin and the towers read navy against Google Earth's
        # grey-white grid; the frame is 0.5 m and the glass a lighter blue-grey
        # round 12 self-check (c_nw): still read white with dark windows; Google Earth's is dark glass in a thin white grid
        banded(g, W[wid][1], 0.0, 101.0, 3.6, 0.25, 3.35, 0.0, "home_frame", "home_glass", top="roof_grey",
               parapet=1.2, win=(1.4, 1.6))
    # Round 12 (PC check of round 11): the city's massing for the two foreground roofs of c_nw and c_sw, which Google
    # Earth shows in detail: 6153 (north-west, c_nw) blue glass under a white roof striped with solar panels; 9966 and
    # 9967 (south-west, c_sw) white roofs with rows of sawtooth glazed rooflights and solar panels.
    looks = {10757: ("near_wall", "dark_glass", "roof_grey"), 16888: ("pale_panel", "dark_glass", "roof_grey"),
             3046: ("pale_panel", "dark_glass", "roof_grey"), 6153: ("pale_panel", "seven_glass", "stripe_roof"),
             9966: ("near_wall", "dark_glass", "sawtooth"), 9967: ("near_wall", "dark_glass", "sawtooth")}
    skip = [p for t, p in W.values() if t.get("_id") in S.LANDMARK_WAYS and len(p) > 3]
    for sid, parts in S.com_parts(set(looks), skip).items():
        wall, glass, roof = looks[sid]
        for base, top, ring in parts:
            # Victoria Point's forecourt deck (10757's 0-9.5 m part): Google Earth (obl_s) shows its top as the
            # red-orange paved plaza between the tower and the stadium, (179, 128, 118), with planted beds and trees
            deck = sid == 10757 and base < 0.5
            highest = top >= max(t_ for _, t_, _ in parts) - 0.01
            r_ = "plaza_red" if deck else (roof if highest else "roof_grey")
            if r_ == "sawtooth":
                r_ = "roof_white"
                sawtooth(g, ring, top)
            if top - base >= 3.0:
                banded(g, ring, base, top, 3.6, 0.9, 2.9, 0.0, wall, glass, top=r_, parapet=0.0)
            else:
                g.prism(ring, base, top, wall, top=r_)
            # roof plant on the offices (Google Earth ext_000: white plant boxes and ducts on light grey roofs)
            if not deck and top > 20.0 and len(ring) >= 4 and sid in (10757, 16888, 3046):
                rr = np.array(ring); c0 = rr.mean(0); ext = rr.max(0) - rr.min(0)
                if min(ext) > 10.0:
                    # round 12 (PC check of round 11, ext_000): Google Earth's roofs carry a big plant room and several
                    # white air-handling boxes; round 11's three small steel boxes read blue and too few
                    rr_ = [tuple(q) for q in ring]
                    pr = min(14.0, 0.3 * min(ext))
                    if _inside(tuple(c0), rr_):
                        g.prism([(c0[0] - pr, c0[1] - pr * 0.7), (c0[0] + pr, c0[1] - pr * 0.7), (c0[0] + pr, c0[1] + pr * 0.7),
                                 (c0[0] - pr, c0[1] + pr * 0.7)], top, top + 4.5, "near_wall", top="roof_grey")
                    for dx, dy, w_, d_ in ((-0.32, -0.25, 5.0, 3.5), (0.3, 0.22, 4.0, 4.0), (-0.05, 0.33, 6.0, 2.5),
                                           (0.3, -0.3, 3.5, 3.5), (-0.33, 0.2, 4.5, 3.0)):
                        cc = c0 + np.array([dx * ext[0], dy * ext[1]])
                        if _inside(tuple(cc), rr_):
                            g.prism([(cc[0] - w_ / 2, cc[1] - d_ / 2), (cc[0] + w_ / 2, cc[1] - d_ / 2),
                                     (cc[0] + w_ / 2, cc[1] + d_ / 2), (cc[0] - w_ / 2, cc[1] + d_ / 2)], top, top + 2.4,
                                    "near_wall", top="near_wall")
            if deck:
                for gid in ("1507400706", "1507400707", "1507400708", "1507400709", "1507400710", "1507400711"):
                    bed = W[gid][1]
                    g.prism(bed, top, top + 0.5, "near_wall", top="roof_garden")
                    c = np.array(bed[:-1] if tuple(bed[0]) == tuple(bed[-1]) else bed).mean(0)
                    tree(g, c, top + 0.5, 7.0, 2.6)
                # Round 11 (PC check): the beds read sparse; Google Earth's plaza is lined with trees in round beds
                rng_ = np.random.default_rng(31)
                blk = [r2 for b2, t2, r2 in parts if b2 > 0.5] + skip
                rr = np.array(ring)
                # round 12 (PC check of round 11): still too sparse; Google Earth's plaza reads half green: every 7.5 m
                for x_ in np.arange(rr[:, 0].min() + 5, rr[:, 0].max() - 5, 7.5):
                    for y_ in np.arange(rr[:, 1].min() + 5, rr[:, 1].max() - 5, 7.5):
                        q = (x_ + rng_.uniform(-3, 3), y_ + rng_.uniform(-3, 3))
                        if not _inside(q, [tuple(p_) for p_ in ring]) or any(_inside(q, [tuple(p_) for p_ in b_]) for b_ in blk):
                            continue
                        if any(_inside(q, [tuple(p_) for p_ in inset(b_, -4.0)]) for b_ in blk if len(b_) > 2):
                            continue
                        g.prism(cylinder_ring(q, 2.9, 10), top, top + 0.45, "near_wall", top="roof_garden")
                        tree(g, q, top + 0.45, rng_.uniform(6.0, 9.0), rng_.uniform(2.2, 3.2))


def tree(g, c, z, h, r):
    """A plaza tree: a dark trunk and a lumpy eight-sided canopy (Google Earth's planted beds on the forecourt)."""
    g.prism(cylinder_ring(c, 0.25, 6), z, z + h * 0.45, "timber", top=None)
    mid = z + h * 0.65
    ring = [(c[0] + r * (1.0 + 0.12 * math.sin(3 * k)) * math.cos(k * math.pi / 4),
             c[1] + r * (1.0 + 0.12 * math.sin(3 * k)) * math.sin(k * math.pi / 4)) for k in range(8)]
    for k in range(8):
        a, b = ring[k], ring[(k + 1) % 8]
        g.poly("tree_leaf", [(*a, mid), (*b, mid), (c[0], c[1], z + h)])
        g.poly("tree_leaf", [(*b, mid), (*a, mid), (c[0], c[1], z + h * 0.4)])


def graffiti(name, px=24):
    """The concrete wall along Wurundjeri Way (Google Earth c_e, c_ne; PC zoom_wall of round 11): pale grey precast
    panels with separate painted pieces and bare stretches between them, not an even confetti. A piece is either
    big bubble lettering (blue or white fill, dark outline), a cluster of dark tags, or a smaller coloured throw-up.
    48 m by 4 m a tile, so the pieces do not repeat often."""
    from PIL import ImageDraw, ImageFont, ImageFilter
    W, H = 48 * px, 4 * px
    rng = np.random.default_rng(48)
    base = np.zeros((H, W, 3), float) + (196, 194, 186) + rng.normal(0, 3.5, (H, W, 3))
    x = (np.arange(W) + 0.5) / px
    base[:, (x % 2.4) < 0.03] *= 0.82                     # precast panel joints
    base[: int(0.25 * px)] *= 0.93                        # the coping's shadow line
    base[int(H * 0.9):] *= 0.9                            # dirt at the foot
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(1.7 * px))
    letters = "ABCDEKMORSTWZ"
    pos = 1.0
    while pos < 46.0:
        # round 12 self-check against Google Earth offices_ne / c_e: most of the wall is painted, the bare stretches short
        kind = rng.choice(["piece", "piece", "tags", "throw", "bare"])
        span = float(rng.uniform(2.5, 6.5))
        if kind == "bare":
            pos += span
            continue
        x0, y0 = int(pos * px), int(rng.uniform(0.6, 1.4) * px)
        if kind == "piece":
            fill = [(96, 132, 196), (232, 234, 236), (120, 160, 210), (210, 214, 222)][rng.integers(4)]
            # each piece on its own painted ground, as Google Earth's read as coloured blocks from the road
            bg = [(70, 96, 150), (150, 120, 168), (96, 150, 140), (200, 170, 96), (180, 96, 96)][rng.integers(5)]
            d.rounded_rectangle((x0 - int(0.3 * px), int(0.35 * px), x0 + int((span + 0.3) * px), int(3.2 * px)),
                                radius=int(0.6 * px), fill=bg)
            word = "".join(rng.choice(list(letters), int(span / 1.3)))
            for k, ch in enumerate(word):
                cx = x0 + int(k * 1.25 * px)
                d.text((cx, y0), ch, font=font, fill=(34, 36, 46), stroke_width=int(0.12 * px), stroke_fill=(34, 36, 46))
                d.text((cx, y0), ch, font=font, fill=fill)
        elif kind == "throw":
            fill = [(214, 150, 176), (220, 204, 120), (150, 196, 170), (236, 236, 232)][rng.integers(4)]
            for k in range(int(span / 1.6)):
                cx, cy = x0 + int(k * 1.5 * px), y0 + int(0.4 * px)
                d.ellipse((cx, cy, cx + int(1.3 * px), cy + int(1.4 * px)), fill=fill, outline=(40, 40, 46), width=int(0.08 * px))
        else:   # dark tags: thin scribbled strokes
            for _ in range(int(span * 3)):
                cx, cy = x0 + rng.uniform(0, span * px), y0 + rng.uniform(0, 1.6 * px)
                pts = [(cx + rng.uniform(-0.4, 0.4) * px, cy + rng.uniform(-0.3, 0.3) * px) for _ in range(5)]
                d.line(pts, fill=(38, 38, 44), width=max(2, int(0.06 * px)))
        pos += span + float(rng.uniform(0.3, 1.2))
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    _save(name, np.asarray(im, float))


def ivy(name, px=24):
    """Ivy over the wall's NAB end (Google Earth c_e): dark and mid greens in leaf clumps. 6 m by 4 m a tile."""
    from PIL import ImageFilter
    W, H = 6 * px, 4 * px
    rng = np.random.default_rng(6)
    img = np.zeros((H, W, 3), float) + (62, 84, 48)
    yy, xx = np.mgrid[0:H, 0:W]
    for _ in range(900):
        cx, cy, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.05, 0.18) * px
        m = (xx - cx) ** 2 + (yy - cy) ** 2 < r * r
        img[m] = [(48, 70, 38), (78, 104, 56), (96, 120, 66), (40, 58, 34)][rng.integers(4)]
    _save(name, np.asarray(Image.fromarray(img.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5)), float))


def road(name, lanes, px=24, shoulder=0.8, lane=3.3, tile=12.0):
    """A carriageway's surface, across its width and 12 m along: dark asphalt with solid edge lines and dashed lane
    lines (3 m line, 9 m gap), as Google Earth shows Wurundjeri Way (round 11 PC: ours read pale grey)."""
    Wm = lanes * lane + 2 * shoulder
    W, H = int(Wm * px), int(tile * px)
    rng = np.random.default_rng(lanes)
    img = np.zeros((H, W, 3), float) + (70, 73, 75) + rng.normal(0, 4.0, (H, W, 3))
    x = (np.arange(W) + 0.5) / px
    y = (np.arange(H) + 0.5) / px
    line = (206, 206, 200)
    for e in (shoulder, Wm - shoulder):
        img[:, np.abs(x - e) < 0.08] = line
    for k in range(1, lanes):
        e = shoulder + k * lane
        m = np.abs(x - e) < 0.06
        img[np.ix_(y < 3.0, m)] = line
    # wheel tracks a shade darker down each lane
    for k in range(lanes):
        for f in (0.28, 0.72):
            img[:, np.abs(x - (shoulder + (k + f) * lane)) < 0.35] *= 0.94
    _save(name, img)
    TILE[name] = (Wm, tile)


def road_strips(g, W):
    """Wurundjeri Way's carriageways beside the stadium and the NAB as their own surface over the map (the map is
    1 m a pixel and cannot carry lane lines): each OpenStreetMap way, as wide as its lanes, 4 cm over the ground."""
    for wid in ("580628688", "580628689", "580628690", "580628691", "787871246", "790397545"):
        t, p = W[wid]
        lanes = int(t.get("lanes", "3"))
        mat = "road%d" % lanes
        if mat not in TILE:
            road(mat, lanes)
        Wm = TILE[mat][0]
        pts = np.array(p, float)
        v = 0.0
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            L = float(np.linalg.norm(b - a))
            if L < 0.1:
                continue
            tdir = (b - a) / L
            n = np.array([-tdir[1], tdir[0]]) * Wm / 2
            g.poly(mat, [(*(a - n), 0.04), (*(a + n), 0.04), (*(b + n), 0.04), (*(b - n), 0.04)][::-1],
                   [(0.0, v), (Wm, v), (Wm, v + L), (0.0, v + L)][::-1])
            v += L


def graffiti_wall(g, W, h=3.4):
    """The painted wall along the stadium side of Wurundjeri Way: the west edge of the northbound carriageway
    (OpenStreetMap ways 580628691, four lanes, then 580628688, three lanes), from the NAB's corner to the stadium's
    north-east corner. Google Earth c_e: rail yards, both carriageways, then the wall under the stadium's east
    offices; the stretch beside the NAB is bare grey concrete, the rest painted (round 11 had it on the rail side)."""
    u = 0.0
    for wid, lanes, mat in (("580628691", 4, "concrete_deck"), ("580628688", 3, "graffiti")):
        pts = np.array(W[wid][1], float)
        off = lanes * 3.3 / 2 + 1.0
        line = []
        for i in range(len(pts)):
            d = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
            d /= np.linalg.norm(d)
            line.append(pts[i] + np.array([-d[1], d[0]]) * off)    # left of a northbound way is west
        assert line[0][0] < pts[0][0], "the wall must sit west of the carriageway"
        for a, b in zip(line[:-1], line[1:]):
            g.wall(mat, a, b, -0.5, h, u)
            u += g.wall(mat, b, a, -0.5, h, u)
        if mat == "graffiti":
            # ivy over the painted wall's first 9 m at the NAB end, on its road face (Google Earth c_e)
            a, b = line[0], line[1]
            t = (b - a) / np.linalg.norm(b - a)
            nrm = np.array([t[1], -t[0]])          # east, to the road
            a2, b2 = a + nrm * 0.06, a + t * 9.0 + nrm * 0.06
            g.wall("ivy", b2, a2, -0.5, h - 0.2) if np.dot(nrm, [1, 0]) > 0 else g.wall("ivy", a2, b2, -0.5, h - 0.2)


def build():
    import bpy
    import bmesh  # noqa: F401
    make_textures()
    W = osm_ways()
    g = Geo()
    nab(g, W["221441430"][1], h=60.0)
    near_buildings(g, W)
    graffiti_wall(g, W)
    road_strips(g, W)
    seven(g, W["33261092"][1])
    round_office(g, W["44158938"][1], h=21.6)  # six floors in Google Earth's ge_vicpoint_b
    ferry(g, W["1246185747"][1])
    # Victoria Point (128 m, 2006): a curved glass tower, recessed balconies behind white slab edges
    # Round 11 (PC check): it read a plain grey slab; Google Earth shows white slab edges and balustrades a floor
    # (about a third of each floor) over blue-grey glass, and a crown stepped back over planted terraces
    vp = W["296368687"][1]
    # Round 12 (PC check of round 11): crisper white edges over blue glass, and the crown stepped twice over planted
    # terraces
    banded(g, vp, 0.0, 110.0, 3.05, 0.75, 2.6, 0.45, "white_band", "vp_glass", parapet=1.2, top="roof_garden")
    banded(g, inset(vp, 3.5), 110.0, 119.0, 3.05, 0.75, 2.6, 0.45, "white_band", "vp_glass", parapet=1.2, top="roof_garden")
    banded(g, inset(vp, 7.0), 119.0, 128.0, 3.05, 0.75, 2.6, 0.45, "white_band", "vp_glass", parapet=1.5)
    for zt, ring_ in ((111.2, inset(vp, 1.7)), (120.2, inset(vp, 5.2))):
        for k, q in enumerate(ring_[::2]):
            tree(g, q, zt, 3.0, 1.2)
    # 720 Bourke (109 m, 2014): rippling white balcony slabs, planted (ge_nab_b)
    balconies(g, W["332358301"][1], 6.0, 109.0, 3.2, 1.6, wave=1.4, glass="bourke_glass", roof="atrium_glass")
    g.prism(W["332358301"][1], 0.0, 6.0, "podium_glass", top=None)
    # the two sawtooth towers north of the stadium (ge_north65_b): white frames, grey glass
    # Round 10: Google Earth close up (ext_135) shows white panel walls with dark punched windows, not ribbons
    banded(g, W["221441428"][1], 0.0, 65.0, 3.1, 0.9, 2.8, 0.45, "band_panel", "grey_glass", parapet=1.5, win=(1.8, 3.0))
    banded(g, W["992236548"][1], 0.0, 70.0, 3.1, 0.9, 2.8, 0.45, "band_panel", "grey_glass", parapet=1.5, win=(1.8, 3.0))
    for wid in ("711957749", "711957750"):
        jetty(g, W[wid][1])
        gangway(g, W[wid][1], [(-198.1, -34.0), (-223.8, -42.3), (-220.1, -53.6), (-206.7, -92.3), (-202.4, -104.2)])
    gantries(g, W)
    southern_cross(g, W["33261083"][1])
    water_ring = [tuple(q) for q in W["23368547"][1]]
    def in_water(pt):
        return _inside(pt, water_ring)
    rocks(g, [(-254.2, 128.7), (-198.1, -34.0)], in_water)
    rocks(g, [(-176.7, -95.2), (-157.4, -152.8)], in_water, seed=6)
    # pile rows either side of the plaza, square to the shore
    t = np.array([-198.1 + 254.2, -34.0 - 128.7]); t /= np.linalg.norm(t)
    piles(g, (-206.0, -12.0), -t, np.array([-t[1], t[0]]) * -1, 22, 9, step=2.6, gap=2.4)
    t2 = np.array([-157.4 + 176.7, -152.8 + 95.2]); t2 /= np.linalg.norm(t2)
    piles(g, (-178.0, -108.0), t2, np.array([-t2[1], t2[0]]) * -1, 12, 9, step=2.6, gap=2.4)  # 12 storeys: from Google Earth's c_e it tops 50 m, from obl_ne well under OSM's 72 m
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for mat, faces in g.parts.items():
        V, F, UV = [], [], []
        for pts, uvs in faces:
            o = len(V)
            V += pts
            F.append(list(range(o, o + len(pts))))
            UV.append(uvs)
        me = bpy.data.meshes.new(mat)
        me.from_pydata(V, [], F)
        me.update()
        tu, tv = TILE.get(mat, (4.0, 4.0))
        ul = me.uv_layers.new(name="UVMap")
        for poly, uv in zip(me.polygons, UV):
            for k, li in enumerate(poly.loop_indices):
                ul.data[li].uv = (uv[k][0] / tu, uv[k][1] / tv)
        m = bpy.data.materials.new(mat)
        m.use_nodes = True
        m.use_backface_culling = False
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        tx = nt.nodes.new("ShaderNodeTexImage")
        tx.image = bpy.data.images.load(os.path.join(TEX, mat + ".png"))
        nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
        # grey_glass: matt enough that the sky does not turn the towers blue (PC check round 3)
        b.inputs["Roughness"].default_value = 0.7 if mat == "grey_glass" else (0.35 if "glass" in mat else 0.85)
        me.materials.append(m)
        ob = bpy.data.objects.new(mat, me)
        sc.collection.objects.link(ob)
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(OUT), export_format="GLB", export_apply=True)
    print("wrote", os.path.abspath(OUT), {k: len(v) for k, v in g.parts.items()})


if __name__ == "__main__":
    build()
