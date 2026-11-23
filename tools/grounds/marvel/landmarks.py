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


def curtain(name, glass, frame, bay=1.5, floor=3.6, px=24, slab=0.35, noise=8.0):
    """A glass curtain wall: panes `bay` wide and `floor` tall, thin mullions, a spandrel at each
    floor. One tile is 4 bays by 2 floors."""
    W, H = int(4 * bay * px), int(2 * floor * px)
    img = np.zeros((H, W, 3), float)
    img[:] = glass
    for j in range(2):
        for i in range(4):
            y0, x0 = int(j * floor * px), int(i * bay * px)
            img[y0:y0 + int(floor * px), x0:x0 + int(bay * px)] += RNG.normal(0, noise)
    x = (np.arange(W) + 0.5) / px
    y = (np.arange(H) + 0.5) / px
    img[:, (x % bay) < 0.08] = frame
    img[((y % floor) < slab), :] = np.array(frame) * 0.8 + np.array(glass) * 0.2
    _save(name, img)


def panels(name, colour, joint, w=1.5, h=1.2, px=24, noise=5.0, holes=None):
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
                if RNG.random() < 0.5:
                    x0, y0 = int((i + 0.3) * w * px), int((j + 0.2) * h * px)
                    for r in range(int(0.6 * h * px)):
                        img[y0 + r, x0:x0 + int((0.6 * h * px - r) * 0.5)] = holes
    _save(name, img)


def flat(name, colour, noise=4.0):
    img = np.zeros((32, 32, 3), float) + colour + RNG.normal(0, noise, (32, 32, 3))
    _save(name, img)


# tile size in metres of each texture (u along the wall, v up)
TILE = {}


def make_textures():
    # NAB, 700 Bourke Street (Google Earth ge_nab_a/b): dark blue reflective glass in 1.5 m panes with
    # thin dark mullions; the light sections silver-white panels with a few slot windows; roof plant grey.
    # PC check 2026-11-23: (46, 50, 57) rendered (13, 22, 46) on the shaded east face against Google
    # Earth's (62, 86, 110); its silver panels there render at (0.44, 0.51, 0.65) of their colour, so
    # the glass is a mid grey-blue that the sky in it and the shade bring down to Google Earth's.
    curtain("nab_glass", (110, 128, 150), (80, 90, 104), bay=1.5, floor=3.9, noise=10.0)
    TILE["nab_glass"] = (6.0, 7.8)
    # PC check round 2: the north tip's panels rendered (88, 105, 136) against GE (60, 87, 113): greyer, darker
    panels("nab_silver", (150, 166, 178), (118, 130, 142), w=1.5, h=1.3, holes=(52, 58, 66))
    TILE["nab_silver"] = (6.0, 5.2)
    flat("fin_white", (232, 234, 236))
    flat("corner_red", (206, 118, 90))  # copper orange-red: GE c_e reads (108, 77, 86) in shade
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
    # the two sawtooth towers north-east of the ground read light grey in Google Earth from the east (PC check
    # round 3: "dark_glass" rendered them deep blue, 39-44 darker); their glass is a pale grey
    # round 4: east-facing walls render about (0.57, 0.62, 0.73) of their colour (NAB's glass and these towers measured
    # on the PC), so Google Earth's (122, 140, 149) needs a light grey: the glass behind the pale bands reads light
    curtain("grey_glass", (176, 184, 186), (150, 156, 160), bay=1.8, floor=2.4, slab=0.0, noise=6.0)
    TILE["grey_glass"] = (7.2, 4.8)
    curtain("office_glass", (78, 98, 116), (180, 186, 190), bay=1.5, floor=2.7, slab=0.0, noise=8.0)
    TILE["office_glass"] = (6.0, 5.4)
    flat("white_band", (226, 228, 228))
    # PC check round 2: Google Earth reads the two curved towers west of the ground as green-grey glass
    curtain("tower_glass", (84, 102, 98), (120, 132, 128), bay=1.5, floor=3.05, slab=0.0, noise=9.0)
    TILE["tower_glass"] = (6.0, 6.1)
    flat("balustrade", (120, 140, 150))
    flat("steel", (196, 198, 200))
    flat("steel_dark", (196, 200, 198))  # galvanised, light in Google Earth
    flat("rock_a", (156, 150, 138), noise=10.0)
    flat("rock_b", (128, 122, 112), noise=10.0)
    flat("slab_grey", (150, 160, 156))  # slab edges: grey-green, not white (PC check round 2)
    flat("timber", (74, 64, 52))
    flat("concrete_deck", (170, 168, 160))
    for n in ("fin_white", "corner_red", "roof_grey", "roof_dark", "sx_glass", "podium_glass", "white_band", "steel", "rock_a", "rock_b",
              "timber", "concrete_deck", "balustrade", "slab_grey", "steel_dark"):
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


def banded(g, ring, z0, z1, floor, sill, head, recess, wall, glass, top="roof_grey", parapet=1.0):
    """Floors of ribbon windows: from each floor's level a solid band `sill` high on the face, then
    glass `recess` back from it up to `head`, then solid to the next floor. The window reveals (sill,
    head) are modelled; a negative recess makes the solid bands stand out as balconies instead."""
    out = ccw(ring)
    inn = inset(out, recess)
    nf = max(1, int(round((z1 - z0) / floor)))
    fl = (z1 - z0) / nf
    for f in range(nf):
        z = z0 + f * fl
        a, b = z + sill * fl / floor, z + head * fl / floor
        u = 0.0
        for i in range(len(out)):
            j = (i + 1) % len(out)
            g.wall(wall, out[i], out[j], z, a, u)
            g.wall(glass, inn[i], inn[j], a, b, u)
            u += g.wall(wall, out[i], out[j], b, z + fl, u)
            # sill (faces up) and head (faces down) between the face and the glass
            g.poly(wall, [(*out[i], a), (*out[j], a), (*inn[j], a), (*inn[i], a)][::-1])
            g.poly(wall, [(*out[i], b), (*out[j], b), (*inn[j], b), (*inn[i], b)])
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
    slots = {"east": ((0.27, 4.5, 3.0), (0.53, 3.0, -2.5), (0.69, 4.0, 3.0))}
    depth = 3.5
    outline = []
    for name, pl in faces:
        L = polyline_length(pl)
        cuts = [(c * L - w / 2, c * L + w / 2, sh) for c, w, sh in slots.get(name, ())]
        edges = [0.0] + [x for c in cuts for x in c[:2]] + [L]
        shift = [0.0] + [c[2] for c in cuts for _ in (0, 1)] + [0.0]
        u = 0.0
        for bi in range(0, len(edges), 2):
            s0, s1 = edges[bi], edges[bi + 1]
            sub = _sub_polyline(pl, s0, s1)
            k = max(1, int(round((s1 - s0) / 14.0)))
            pts, _ = polyline_points(sub, k)
            for j in range(k):
                p0, p1 = pts[j], pts[j + 1]
                w = float(np.linalg.norm(p1 - p0))
                t = (p1 - p0) / w
                n = outward(p0, p1)
                f = ((s0 + (j + 0.5) * (s1 - s0) / k) / L)
                if name == "west":
                    mat = "nab_glass"
                elif name == "east":
                    mat = "nab_silver" if f > 0.88 else "nab_glass"
                else:
                    mat = "nab_glass"
                # alternate edges lean out (a block's two ends stay plumb, so its slots' walls are flat)
                lean0 = n * fold * (j % 2 == 1)
                lean1 = n * fold * ((j + 1) % 2 == 1 and j + 1 < k)
                if j == 0:
                    lean0 = lean0 + t * shift[bi]
                if j == k - 1:
                    lean1 = lean1 + t * shift[bi + 1]
                g.poly(mat, [(*p0, base), (*p1, base), (*(p1 + lean1), top), (*(p0 + lean0), top)],
                       [(u, base), (u + w, base), (u + w, top), (u, top)])
                outline.append(p0 + lean0)
                outline.append(p1 + lean1)
                # the leaning edge leaves a triangular gap to its neighbour: a narrow fold wall closes it
                if j + 1 < k:
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
                if mat == "nab_glass":
                    # white shades, one row a floor (3.9 m), one every 6.5 m along a row, each row stepped
                    # 2.2 m on so they climb in diagonals: about five a row on a 30 m block and eleven rows,
                    # 3.4 m wide and 5.6 m tall, as counted on Google Earth's c_e (2026-11-23)
                    # The west face, to the stadium, carries them far closer (Google Earth from the west, PC check
                    # round 2): 4.2 m wide every 4.8 m, so the face reads pale with the dark glass left in
                    # diagonal bands between them.
                    sw, sp, sh, st = (4.2, 4.8, 7.0, 1.6) if name == "west" else (3.4, 6.5, 5.6, 2.2)
                    for r, z in enumerate(np.arange(base + 1.0, top - sh - 0.9, 3.9)):
                        for s_ in np.arange((r * st - u) % sp, w - sw - 0.2, sp):
                            s_ = float(s_) + 0.2  # clear of the facet edge
                            lean = (lean0 + (lean1 - lean0) * (s_ / w)) * ((z - base) / (top - base))
                            shade(g, "fin_white", p0 + t * s_ + lean + n * 0.6, t, n, sw, sh, 0.35, z)  # 0.6 m clears the folded facet, which is not flat
                u += w
            if bi + 2 < len(edges):
                # the slot to the next block: two side walls and a back wall 3.5 m in, all orange-red,
                # leaning along the face as the blocks' edges do; glass ground storey carried across
                a0 = _at(pl, s1)
                b0 = _at(pl, edges[bi + 2])
                t = (b0 - a0) / np.linalg.norm(b0 - a0)
                n = outward(a0, b0)
                sa, sb = t * shift[bi + 1], t * shift[bi + 2]
                ai, bi_ = a0 - n * depth, b0 - n * depth
                g.poly("corner_red", [(*a0, base), (*ai, base), (*(ai + sa), top), (*(a0 + sa), top)])
                g.poly("corner_red", [(*ai, base), (*bi_, base), (*(bi_ + sb), top), (*(ai + sa), top)])
                g.poly("corner_red", [(*bi_, base), (*b0, base), (*(b0 + sb), top), (*(bi_ + sb), top)])
                g.wall("podium_glass", a0 - n * 2.0, b0 - n * 2.0, 0.0, base)
                g.poly("fin_white", [(*(a0 - n * 2.0), base - 0.6), (*(b0 - n * 2.0), base - 0.6),
                                     (*b0, base), (*a0, base)])
                g.poly("corner_red", [(*(ai + sa), top), (*(bi_ + sb), top), (*(b0 + sb), top), (*(a0 + sa), top)])
                # the slot is not a plain stripe: folded orange-red panels zigzag out of it across the bays' edges,
                # each a triangle from one side of the slot reaching 3.5 m onto the next bay, its point folded 0.9 m
                # out, so the red reads in irregular folded shapes between the bays (Google Earth c_e, PC check
                # round 3); five folds up the height, alternate ones mirrored
                nf = 5
                for kf in range(nf):
                    z0, z1 = base + (top - base) * kf / nf, base + (top - base) * (kf + 1) / nf
                    zm = (z0 + z1) / 2 + (top - base) / nf * (0.18 if kf % 2 else -0.15)
                    f0, f1, fm = (z0 - base) / (top - base), (z1 - base) / (top - base), (zm - base) / (top - base)
                    if kf % 2 == 0:
                        g.poly("corner_red", [(*(a0 + sa * f0 + n * 0.15), z0), (*(b0 + t * 3.5 + sb * fm + n * 0.9), zm),
                                              (*(a0 + sa * f1 + n * 0.15), z1)])
                    else:
                        g.poly("corner_red", [(*(b0 + sb * f0 + n * 0.15), z0), (*(a0 - t * 3.5 + sa * fm + n * 0.9), zm),
                                              (*(b0 + sb * f1 + n * 0.15), z1)])
                u += float(np.linalg.norm(b0 - a0))
    # parapet and roof over the facets' tops, plant set back on the roof
    rim = ccw([tuple(q) for q in outline])
    g.cap("roof_grey", rim, top)
    for i in range(len(rim)):
        g.wall("nab_silver", rim[i], rim[(i + 1) % len(rim)], top, top + 1.4)
    # the roof: folded dark glass planes rising from the parapet to a ridge point over the middle, as
    # Google Earth's obl_e and obl_sw show it (not flat)
    T = [np.array(q) for q in ccw([tuple(q) for q in (P[0], P[1], P[2])])]
    apex = np.r_[np.mean(np.array(T), 0), top + 9.0]
    for i in range(3):
        a, b = T[i], T[(i + 1) % 3]
        g.poly("roof_dark", [np.r_[a, top + 1.4], np.r_[b, top + 1.4], apex])
    # the ground storey's soffit
    g.cap("roof_grey", [tuple(q) for q in ring], base - 0.6, up=False)


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
    banded(g, block, 0.0, 16.8, 4.2, 1.1, 3.5, 0.35, "pale_panel", "dark_glass")
    c = np.mean(np.array(block), 0)
    g.prism([tuple(c + (np.array(q) - c) * 0.4) for q in block], 16.8, 20.2, "pale_panel", top="roof_grey")
    lattice_mast(g, "steel", (c[0] + 14.0, c[1] + 12.0), 20.2, 24.0)
    d = (-147.5, 40.5)
    banded(g, cylinder_ring(d, 10.4, 28), 0.0, 12.6, 4.2, 1.0, 3.6, 0.3, "pale_panel", "dark_glass", parapet=0.6)
    banded(g, cylinder_ring(d, 8.2, 24), 12.6, 16.8, 4.2, 1.0, 3.6, 0.3, "pale_panel", "dark_glass", parapet=0.6)
    g.prism(cylinder_ring(d, 6.0, 20), 16.8, 18.8, "pale_panel", top="roof_grey")


def round_office(g, ring, h=29.0):
    """The curved glass office south-west of the stadium on Harbour Esplanade (Google Earth
    ge_aflhouse_b, c_sw): eight floors of glass, each floor's slab edge a white band standing out."""
    banded(g, ring, 0.0, h, h / 6, 0.55, 3.25, 0.3, "white_band", "office_glass", parapet=1.2)


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


def balconies(g, ring, z0, z1, floor, depth, wave=0.0, seed=0):
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
        u += g.wall("tower_glass", core[i], core[j], z0, z1, u)
    for f in range(nf + 1):
        z = z0 + f * fl
        if wave:
            ang = np.arctan2(np.array(out)[:, 1] - c[1], np.array(out)[:, 0] - c[0])
            push = wave * (0.5 + 0.5 * np.sin(3 * ang + f * 0.45 + seed))
            edge = [tuple(np.array(q) + (np.array(q) - c) / (np.linalg.norm(np.array(q) - c) + 1e-6) * pp)
                    for q, pp in zip(out, push)]
        else:
            edge = out
        th = 0.3
        for i in range(len(edge)):
            j = (i + 1) % len(edge)
            g.wall("white_band", edge[i], edge[j], z - th, z)
            if f < nf:
                g.wall("balustrade", edge[i], edge[j], z, z + 1.05)
            g.poly("white_band", [(*edge[i], z), (*edge[j], z), (*core[j], z), (*core[i], z)][::-1])
            g.poly("white_band", [(*edge[i], z - th), (*edge[j], z - th), (*core[j], z - th), (*core[i], z - th)])
    g.cap("roof_grey", out, z1)


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


def build():
    import bpy
    import bmesh  # noqa: F401
    make_textures()
    W = osm_ways()
    g = Geo()
    nab(g, W["221441430"][1], h=60.0)
    seven(g, W["33261092"][1])
    round_office(g, W["44158938"][1], h=21.6)  # six floors in Google Earth's ge_vicpoint_b
    ferry(g, W["1246185747"][1])
    # Victoria Point (128 m, 2006): a curved glass tower, recessed balconies behind white slab edges
    banded(g, W["296368687"][1], 0.0, 128.0, 3.05, 0.3, 2.9, 0.45, "slab_grey", "tower_glass", parapet=1.5)
    # 720 Bourke (109 m, 2014): rippling white balcony slabs, planted (ge_nab_b)
    balconies(g, W["332358301"][1], 6.0, 109.0, 3.2, 1.6, wave=1.4)
    g.prism(W["332358301"][1], 0.0, 6.0, "podium_glass", top=None)
    # the two sawtooth towers north of the stadium (ge_north65_b): white frames, grey glass
    banded(g, W["221441428"][1], 0.0, 65.0, 3.1, 0.9, 2.8, 0.45, "pale_panel", "grey_glass", parapet=1.5)
    banded(g, W["992236548"][1], 0.0, 70.0, 3.1, 0.9, 2.8, 0.45, "pale_panel", "grey_glass", parapet=1.5)
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
