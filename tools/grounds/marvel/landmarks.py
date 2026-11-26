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
import land  # noqa: E402

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


def mural(name, px=24):
    """The red and white mural on the block north of the Seven fin (Google Earth c_ne, c_nw, seven_nw): a red ground
    with large white figure shapes and a few dark lines. 6 m wide by 15 m tall, one tile."""
    from PIL import ImageDraw
    W, H = 6 * px, 15 * px
    im = Image.new("RGB", (W, H), (192, 44, 46))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(57)
    for _ in range(9):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.uniform(0.6, 1.8) * px
        d.ellipse((x - r, y - r * 1.6, x + r, y + r * 1.6), fill=(236, 232, 228))
    for _ in range(6):
        x0, y0 = rng.uniform(0, W), rng.uniform(0, H)
        d.line((x0, y0, x0 + rng.uniform(-2, 2) * px, y0 + rng.uniform(1, 4) * px), fill=(40, 36, 40), width=int(0.15 * px))
    _save(name, np.asarray(im, float))
    TILE[name] = (6.0, 15.0)


def tri_wall(name, base, tri, px=24, wid=12.0, hgt=15.6, tw=2.4, th=3.6, step=6.0, stagger=2.2, floor=3.9, seed=1,
             joint=None):
    """A wall of `base` panels with triangles of `tri` pointing down, one every `step` m along each floor's row and
    each row stepped `stagger` m on, so they climb in diagonals (NAB's west face, Google Earth obl_w: pale grey with
    dark triangles). One tile `wid` by `hgt` m."""
    from PIL import ImageDraw
    W, H = int(wid * px), int(hgt * px)
    rng = np.random.default_rng(seed)
    img = np.zeros((H, W, 3), float) + base + rng.normal(0, 3.0, (H, W, 3))
    if joint is not None:
        x = (np.arange(W) + 0.5) / px
        y = (np.arange(H) + 0.5) / px
        img[:, (x % 1.5) < 0.06] = joint
        img[(y % floor) < 0.08, :] = joint
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)
    nr = int(round(hgt / floor))
    for r in range(nr):
        y0 = (r * floor + 0.15) * px
        for k in range(-1, int(wid / step) + 2):
            x0 = ((k * step + r * stagger) % wid) * px
            for xo in (0, -W, W):
                d.polygon([(x0 + xo, y0), (x0 + xo + tw * px, y0), (x0 + xo + tw * px / 2, y0 + th * px)], fill=tri)
    _save(name, np.asarray(im, float))
    TILE[name] = (wid, hgt)


def lattice(name, glass, frame, px=24, bay=3.0, floor=3.2, w=0.55):
    """A heavy white lattice of diagonal members over dark glass, an X in every bay of every floor, with a floor
    beam (Google Earth ext_180: the tower north-east of the ground). One tile 4 bays by 2 floors."""
    from PIL import ImageDraw
    W, H = int(4 * bay * px), int(2 * floor * px)
    rng = np.random.default_rng(3)
    img = np.zeros((H, W, 3), float) + glass + rng.normal(0, 4.0, (H, W, 3))
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)
    for j in range(2):
        for i in range(4):
            x0, y0, x1, y1 = i * bay * px, j * floor * px, (i + 1) * bay * px, (j + 1) * floor * px
            d.line([(x0, y0), (x1, y1)], fill=frame, width=int(w * px))
            d.line([(x1, y0), (x0, y1)], fill=frame, width=int(w * px))
            d.line([(x0, y0), (x1, y0)], fill=frame, width=int(w * 1.2 * px))
            d.line([(x0, y0), (x0, y1)], fill=frame, width=int(w * 0.8 * px))
    _save(name, np.asarray(im, float))
    TILE[name] = (4 * bay, 2 * floor)


def slot_wall(name, wall, slot, px=24, wid=12.0, floor=3.1, nf=8):
    """White wall with one meandering column of paired narrow dark slot windows a face, shifting a little floor to floor
    (Google Earth ext_180: Lacrosse's white faces are mostly blank, the slots in one wandering vertical run). One tile
    `wid` m wide and `nf` floors tall."""
    W, H = int(wid * px), int(nf * floor * px)
    rng = np.random.default_rng(4)
    img = np.zeros((H, W, 3), float) + wall + rng.normal(0, 3.0, (H, W, 3))
    for j in range(nf):
        off = 0.9 * math.sin(j * 0.9)
        for sx in (5.0, 6.1):
            x0 = int((sx + off) * px)
            y0 = int((j * floor + 0.5) * px)
            img[y0:y0 + int(2.1 * px), x0:x0 + int(0.45 * px)] = slot
    _save(name, img)
    TILE[name] = (wid, nf * floor)


def solar_cells(name, px=24):
    """Solar panels in their frames: dark cells about 1 x 1.7 m, thin pale gaps, a wider white gap after every
    second panel (Google Earth c_sw, c_se: black panels in a white grid, in two-panel blocks). 4 m by 3.4 m a tile."""
    W, H = int(4.0 * px), int(3.4 * px)
    rng = np.random.default_rng(9)
    img = np.zeros((H, W, 3), float) + (34, 42, 58) + rng.normal(0, 3.0, (H, W, 3))
    x = (np.arange(W) + 0.5) / px
    y = (np.arange(H) + 0.5) / px
    img[:, (x % 1.0) < 0.06] = (186, 190, 192)
    img[:, (x % 2.0) < 0.2] = (214, 216, 214)
    img[(y % 1.7) < 0.06, :] = (186, 190, 192)
    _save(name, img)
    TILE[name] = (4.0, 3.4)


def ribbed(name, base, px=24):
    """Ribbed metal cladding: vertical ribs every 0.3 m, a light and a dark edge each, with a louvre band 1.2 m
    deep near the top (Google Earth ext_000: the plant room's light grey-blue ribbed walls). 6 m by 6 m a tile."""
    W = H = int(6 * px)
    rng = np.random.default_rng(12)
    img = np.zeros((H, W, 3), float) + base + rng.normal(0, 2.5, (H, W, 3))
    x = (np.arange(W) + 0.5) / px
    y = (np.arange(H) + 0.5) / px
    img[:, (x % 0.3) < 0.05] *= 1.12
    img[:, ((x % 0.3) > 0.05) & ((x % 0.3) < 0.09)] *= 0.8
    band = (y > 0.6) & (y < 1.8)
    img[np.ix_(band, np.ones(W, bool))] = np.array(base) * 0.55
    img[np.ix_(band & ((y % 0.15) < 0.07), np.ones(W, bool))] = np.array(base) * 0.95
    _save(name, img)
    TILE[name] = (6.0, 6.0)


def track(name, px=32):
    """One track bed across 3.6 m and 4.8 m along: grey-brown ballast, timber-dark sleepers every 0.65 m, two
    steel rails 1.6 m apart (Google Earth c_e, c_ne: the Southern Cross yard's tracks with their sleepers)."""
    W, H = int(3.6 * px), int(4.8 * px)
    rng = np.random.default_rng(21)
    # round 13 cloud pair (c_ne): the first try read one flat grey-brown; Google Earth's tracks are rust-brown beds with
    # pale concrete sleepers between grey ballast
    img = np.zeros((H, W, 3), float) + (112, 92, 80) + rng.normal(0, 9.0, (H, W, 3))
    x = (np.arange(W) + 0.5) / px
    y = (np.arange(H) + 0.5) / px
    sl = (y % 0.65) < 0.24
    img[np.ix_(sl, (x > 0.55) & (x < 3.05))] = (176, 172, 164)
    for rx in (1.0, 2.6):
        img[:, np.abs(x - rx) < 0.06] = (64, 58, 54)
        img[:, np.abs(x - rx - 0.06) < 0.02] = (70, 68, 66)
    edge = (x < 0.25) | (x > 3.35)
    img[:, edge] = img[:, edge] * 0.9
    _save(name, img)
    TILE[name] = (3.6, 4.8)


def train_side(name, body, stripe, px=24):
    """A suburban/regional train's side, 24 m a car and 3.6 m tall: body colour, dark windows, a stripe and a dark
    skirt (Google Earth obl_e: silver and purple trains stabled in the yard). One car a tile."""
    W, H = int(24 * px), int(3.6 * px)
    img = np.zeros((H, W, 3), float) + body
    x = (np.arange(W) + 0.5) / px
    y = (np.arange(H) + 0.5) / px  # from the top
    img[(y > 0.9) & (y < 1.8), :] = (40, 46, 56)
    img[np.ix_((y > 0.9) & (y < 1.8), (x % 2.4) < 0.25)] = body
    img[(y > 2.2) & (y < 2.6), :] = stripe
    img[y > 3.2, :] = (50, 50, 52)
    img[:, (x < 0.3) | (x > 23.7)] = (40, 40, 44)
    _save(name, img)
    TILE[name] = (24.0, 3.6)


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
    flat("nab_rooflight", (86, 92, 98), noise=5.0)  # teal glass pyramids (ge12b nab_top); round 12 self-check: greyer, it read a teal block
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
    mural("mural")
    flat("navy_wall", (46, 56, 74), noise=4.0)  # 16888's dark navy cladding (Google Earth c_ne)
    curtain("louvre_grey", (120, 124, 128), (176, 178, 180), bay=0.9, floor=0.5, slab=0.12, noise=3.0)
    TILE["louvre_grey"] = (3.6, 1.0)
    flat("pool_blue", (96, 170, 206), noise=3.0)
    flat("solar", (38, 48, 66), noise=3.0)   # dark solar arrays on 9966/9967's white roofs (Google Earth c_sw)
    flat("roof_white", (214, 216, 212), noise=4.0)  # the former Seven building's blue curtain wall (seven_w, c_nw)
    # round 12 (PC check of round 11): Victoria Point's glass is blue under its white slab edges, not green-grey
    curtain("vp_glass", (60, 84, 110), (88, 104, 120), bay=1.5, floor=3.05, slab=0.0, noise=3.0)
    TILE["vp_glass"] = (6.0, 6.1)
    # round 12 (PC check of round 11): 720 Bourke still read blue mottling; Google Earth shows crisp white wavy
    # balcony bands over dark glass, and a glass atrium roof. One flat dark glass (no pane-to-pane tone to mottle)
    flat("bourke_glass", (52, 74, 100), noise=2.0)  # round 13: Google Earth obl_s/c_se mid blue glass
    panels("atrium_glass", (140, 150, 156), (176, 180, 182), w=3.0, h=1.5, noise=4.0)  # self-check: (118,138,150) read a blue lid
    TILE["atrium_glass"] = (6.0, 3.0)
    # round 10: HOME Docklands' two towers north-west of the ground (Google Earth obl_n, obl_nw, ext_135): dark
    # navy glass in a white frame grid, about 1.4 m windows every 1.6 m
    flat("home_frame", (214, 216, 214))
    # round 11 read lilac in sun at (76, 84, 90); round 12 (PC check of round 11): far too light, Google Earth is dark
    # navy glass in the white grid
    flat("home_glass", (96, 112, 130), noise=3.0)  # round 13 cloud pair obl_w: (70, 92, 118) still read navy
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
    flat("balustrade", (70, 90, 114), noise=2.0)  # round 13: glass balustrades (obl_s pair: white ones read a white tower)
    flat("steel", (196, 198, 200))
    flat("steel_dark", (196, 200, 198))  # galvanised, light in Google Earth
    flat("rock_a", (150, 150, 146), noise=10.0)
    flat("rock_b", (122, 122, 120), noise=10.0)  # round 13: grey rock (Google Earth c_w), not brown
    flat("slab_grey", (150, 160, 156))  # slab edges: grey-green, not white (PC check round 2)
    flat("timber", (74, 64, 52))
    flat("concrete_deck", (170, 168, 160))
    # round 13 (PC check of round 12)
    tri_wall("nab_west", (184, 190, 196), (44, 56, 70), joint=(160, 166, 172))   # obl_w: pale grey with dark triangles
    lattice("lattice_white", (104, 120, 136), (226, 228, 228))  # round 13 cloud pair: (60, 74, 90) read navy                        # ext_180's lattice tower
    slot_wall("slot_white", (220, 222, 222), (30, 34, 40))                         # ext_180's white tower
    solar_cells("solar_cells")
    ribbed("ribbed", (150, 164, 178))                                              # ext_000's plant room
    track("track")
    train_side("train_silver", (176, 180, 184), (120, 60, 140))                    # V/Line and Metro: silver, purple
    train_side("train_white", (210, 212, 214), (60, 90, 170))
    flat("pavilion_glass", (128, 176, 204), noise=3.0)                             # 16888's glazed roof pavilion (c_ne)
    flat("gable_glass", (120, 148, 168), noise=3.0)  # round 13 cloud pair c_sw: (62, 82, 100) read near black                                  # 9966's glazed gable faces (c_sw)
    flat("rail_steel", (150, 152, 154))
    for n in ("bourke_edge", "home_frame", "home_glass", "near_wall", "tree_leaf", "fin_white", "corner_red", "roof_grey", "roof_dark", "sx_glass", "podium_glass", "white_band", "steel", "rock_a", "rock_b",
              "timber", "concrete_deck", "balustrade", "slab_grey", "steel_dark", "round_glass", "bourke_glass", "seven_glass", "roof_white", "navy_wall", "pool_blue", "solar", "pavilion_glass", "gable_glass", "rail_steel"):
        TILE[n] = (4.0, 4.0)


# ---------------------------------------------------------------- mesh building
class Geo:
    """Faces gathered per material: vertices (x east, y north, z up), quads/polys, UVs in metres."""

    def __init__(self):
        self.parts = {}
        # Round 12 (real land): every z handed in is raised by `lift`, set per building to the land under its foot
        # (land.py). Heights read off Google Earth's 3D are already above sea level and keep lift 0.
        self.lift = 0.0

    def poly(self, mat, pts, uvs=None):
        pts = [(float(p[0]), float(p[1]), float(p[2]) + self.lift) for p in pts]
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
    # Round 12 (Google Earth point picks in c_e and c_ne, 2026-11-23): OpenStreetMap's north tip (147.1, -11.0) stops
    # 15-18 m short. Google Earth puts the tip's foot at (157, -0.5) and its top at (153.3, 7.5): the tip leans out
    # over the rail yard. Walls here stand plumb, so the tip goes midway, (155.2, 3.5), and the OSM kink just south
    # of it on the west face (145.4, -16.7) is dropped.
    tip = min(range(len(ring)), key=lambda i: (ring[i][0] - 147.11) ** 2 + (ring[i][1] + 10.96) ** 2)
    assert abs(ring[tip][1] + 10.96) < 0.1, "the OSM north tip moved; re-pick it"
    ring = [(155.2, 3.5) if i == tip else q for i, q in enumerate(ring)
            if not (abs(q[0] - 145.40) < 0.1 and abs(q[1] + 16.71) < 0.1)]
    P = [np.array(q) for q in ring]
    faces = [("south", [P[0], P[1]]), ("east", [P[1], P[2]]), ("west", P[2:] + [P[0]])]
    # Round 12 (real land): the land falls from 4.4 m along the east face (Google Earth: 7 m above sea level at its foot)
    # to 1 m on the west, by the stadium. The 7 m glazed ground storey is read on the east face (c_e, c_ne), so it
    # stands on that face's land; the west's podium glass runs on down to its lower ground. The top, picked in Google
    # Earth at 60.4 m, stays where it was measured.
    east_land = float(np.mean([land.z(*(np.array(P[1]) + (np.array(P[2]) - np.array(P[1])) * f)) for f in (0.1, 0.5, 0.9)]))
    base, top, fold = east_land + 7.0, h, 2.2
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
                    # round 13 (PC check of round 12, obl_w: still dark navy): one pale grey wall with dark triangles
                    mat = "nab_west"
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


def rocks(g, shore, water, width=6.5, seed=5):
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
            r = rng.uniform(0.5, 1.0)
            # round 13 (PC check of round 12, c_w: no rock showed; cloud check view chk_rocks): the land data runs on
            # flat over the harbour (about 0.8-1.2 m under the promenade, the water painted on it), so armour drawn up
            # from sea level stayed under it. Each boulder now stands on the land under it, 0.7-1.3 m proud at the wall
            # and lower outward
            hgt = rng.uniform(0.7, 1.3) * (1.0 - 0.6 * float(np.dot(p - a, n)) / width)
            k = rng.integers(5, 7)
            ang = rng.uniform(0, 2 * math.pi)
            base = [(p[0] + r * math.cos(ang + 2 * math.pi * m / k) * rng.uniform(0.75, 1.15),
                     p[1] + r * math.sin(ang + 2 * math.pi * m / k) * rng.uniform(0.75, 1.15)) for m in range(k)]
            # round 12 (real land): the water is at sea level (model -2.6) and the promenade 1.6-1.8 m above it, so the
            # armour stands from the water up the sea wall, its tips reaching to about 0.5 m under the promenade
            zl = float(land.z(*p)) - 0.25 - g.lift
            tip = (p[0] + rng.normal(0, 0.12), p[1] + rng.normal(0, 0.12), zl + hgt)
            mat = ("rock_a", "rock_b")[int(rng.integers(0, 2))]
            for m in range(k):
                g.poly(mat, [(*base[m], zl), (*base[(m + 1) % k], zl), tip])


def piles(g, start, along, out, rows, per_row, step=2.8, gap=3.0, h=1.1):
    """Rows of old timber piles standing out of the water off the plaza (Google Earth ge_ferry_b)."""
    start, along, out = np.array(start, float), np.array(along, float), np.array(out, float)
    for r in range(rows):
        for k in range(per_row):
            c = start + along * r * step + out * (1.5 + k * gap)
            g.prism(cylinder_ring(c, 0.28, 6), WATER_Z - 0.5 - g.lift, WATER_Z + h - g.lift, "timber", top="timber")


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
    # round 12 (real land): from the promenade's edge down to the pontoon riding on the water (sea level, model -2.6)
    zp, zq = float(land.z(*p)) - 0.05 - g.lift, WATER_Z + 0.5 - g.lift
    g.poly("concrete_deck", [(*(p - n), zp), (*(p + n), zp), (*(q + n), zq), (*(q - n), zq)][::-1])
    for sgn in (-1, 1):
        strut(g, "steel", np.r_[p + n * sgn, zp + 1.0], np.r_[q + n * sgn, zq + 1.0], 0.06)


# the harbour's water: sea level in the model (land.py; the LiDAR reads 0 m above sea level over Victoria Harbour)
WATER_Z = -2.6


def jetty(g, ring, z=0.5):
    """A floating jetty or pontoon from its OpenStreetMap outline: a concrete deck with its edge."""
    g.prism(ring, WATER_Z - 0.3 - g.lift, WATER_Z + z - g.lift, "concrete_deck", top="concrete_deck")


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
    # round 13 (PC check of round 12, ext_315/c_se: ours read straight bands): the footprint cut every 2 m so the
    # ripple bends each slab edge, a wave about 18 m long along the face that drifts floor to floor
    dense, sarc = [], []
    acc = 0.0
    for i in range(len(out)):
        p0, p1 = np.array(out[i], float), np.array(out[(i + 1) % len(out)], float)
        L = float(np.linalg.norm(p1 - p0))
        k = max(1, int(math.ceil(L / 2.0)))
        for t in range(k):
            dense.append(tuple(p0 + (p1 - p0) * t / k))
            sarc.append(acc + L * t / k)
        acc += L
    sarc = np.array(sarc)
    coreD = inset(dense, depth)
    rng_p = np.random.default_rng(seed + 77)
    for f in range(nf + 1):
        z = z0 + f * fl
        if wave:
            push = wave * (0.5 + 0.5 * np.sin(2 * math.pi * sarc / 18.0 + f * 0.6 + seed))
            edge = [tuple(np.array(q) + (np.array(q) - c) / (np.linalg.norm(np.array(q) - c) + 1e-6) * pp)
                    for q, pp in zip(dense, push)]
            core = coreD
        else:
            edge = out
        th = 0.55  # round 12: crisp white bands that hold at range; round 13 (obl_s pair): 0.7 with white balustrades read
        # the whole tower near white (122, 133, 146) where Google Earth's is blue glass between white bands (45, 68, 91)
        # round 13 (c_se pair): Google Earth's bands also rise and fall along the face, up to about half a metre
        dz = 0.3 * np.sin(2 * math.pi * sarc / 24.0 + f * 0.6 + seed + 1.3) if wave else np.zeros(len(edge))  # second pass: 0.5 m every 18 m read too regular against ext_315
        for i in range(len(edge)):
            j = (i + 1) % len(edge)
            zi, zj = z + dz[i], z + dz[j]
            g.poly("bourke_edge", [(*edge[i], zi - th), (*edge[j], zj - th), (*edge[j], zj), (*edge[i], zi)])
            if f < nf:
                g.poly("balustrade", [(*edge[i], zi), (*edge[j], zj), (*edge[j], zj + 1.05), (*edge[i], zi + 1.05)])
            g.poly("slab_grey", [(*edge[i], zi), (*edge[j], zj), (*core[j], z), (*core[i], z)][::-1])
            g.poly("slab_grey", [(*edge[i], zi - th), (*edge[j], zj - th), (*core[j], z - th), (*core[i], z - th)])
            # planter boxes behind the balustrade on some balconies (Google Earth ext_315: greenery on the bands)
            if wave and 0 < f < nf and rng_p.random() < 0.18:
                e0, e1 = np.array(edge[i]), np.array(edge[j])
                inn = (np.array(core[i]) - e0) * 0.25
                g.prism([tuple(e0 + inn * 0.2), tuple(e1 + inn * 0.2), tuple(e1 + inn), tuple(e0 + inn)], z, z + 1.3,
                        "tree_leaf", top="tree_leaf")
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
            g.lift = float(min(land.z(*p0), land.z(*p1)))   # masts on the yard's own land
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


def sawtooth(g, ring, z, pitch=6.0, h=1.8, cover=(0.6, 0.7)):
    """Rows of sawtooth rooflights over a roof's middle: each a white slope rising `h` over `pitch` to a glazed upright
    face, the rows along the roof's longer side; solar panels on every other slope."""
    rr = np.array(ring, float)
    c0 = rr.mean(0)
    ev, evec = np.linalg.eigh(np.cov((rr - c0).T))
    ax = evec[:, 1]
    cr = np.array([-ax[1], ax[0]])
    pa, pc = (rr - c0) @ ax, (rr - c0) @ cr
    poly = [tuple(q) for q in ring]
    for k, s0 in enumerate(np.arange(pc.min() * cover[0], pc.max() * cover[0] - pitch, pitch)):
        a0, a1 = pa.min() * cover[1], pa.max() * cover[1]
        p00, p10 = c0 + ax * a0 + cr * s0, c0 + ax * a1 + cr * s0
        p01, p11 = c0 + ax * a0 + cr * (s0 + pitch), c0 + ax * a1 + cr * (s0 + pitch)
        if not all(_inside(tuple(q), poly) for q in (p00, p10, p01, p11)):
            continue
        slope = "nab_roof" if k % 2 else "roof_white"
        g.poly(slope, [(*p00, z), (*p10, z), (*p11, z + h), (*p01, z + h)])
        g.poly("sx_glass", [(*p11, z), (*p01, z), (*p01, z + h), (*p11, z + h)])
        g.poly("roof_white", [(*p00, z), (*p01, z + h), (*p01, z)])
        g.poly("roof_white", [(*p10, z), (*p11, z), (*p11, z + h)])


def sawtooth_rows(g, ring, z, pitch, h, flip=False):
    """Big sawtooth roof over a whole (possibly L- or U-shaped) footprint: rows `pitch` apart stepping along its longer
    side, each ridge across the building (Google Earth c_sw: five or six gables down the long side), a white slope rising
    `h` to a glazed upright face, cut to the footprint 1 m in from its edge (shapely)."""
    from shapely.geometry import LineString, Polygon
    rr = np.array(ring, float)
    c0 = rr.mean(0)
    ev, evec = np.linalg.eigh(np.cov((rr - c0).T))
    cr = -evec[:, 1] if flip else evec[:, 1]
    ax = np.array([-cr[1], cr[0]])
    pa, pc = (rr - c0) @ ax, (rr - c0) @ cr
    P = Polygon([tuple(q) for q in ring]).buffer(-1.0)
    n = 0
    for s0 in np.arange(pc.min(), pc.max() - pitch + 0.01, pitch):
        segs = []
        for s_ in (s0 + 0.5, s0 + pitch - 0.5):
            L = LineString([tuple(c0 + ax * (pa.min() - 5) + cr * s_), tuple(c0 + ax * (pa.max() + 5) + cr * s_)])
            cut = L.intersection(P)
            parts_ = [cut] if cut.geom_type == "LineString" else list(getattr(cut, "geoms", []))
            segs.append([q for q in parts_ if q.geom_type == "LineString" and not q.is_empty and len(q.coords) >= 2])
        # keep the stretch both edges of the row share
        for la in segs[0]:
            a0, a1 = sorted(float((np.array(q) - c0) @ ax) for q in la.coords)
            for lb in segs[1]:
                b0, b1 = sorted(float((np.array(q) - c0) @ ax) for q in lb.coords)
                u0, u1 = max(a0, b0), min(a1, b1)
                if u1 - u0 < 4.0:
                    continue
                p00, p10 = c0 + ax * u0 + cr * s0, c0 + ax * u1 + cr * s0
                p01, p11 = c0 + ax * u0 + cr * (s0 + pitch), c0 + ax * u1 + cr * (s0 + pitch)
                g.poly("roof_white", [(*p00, z), (*p10, z), (*p11, z + h), (*p01, z + h)])
                g.poly("gable_glass", [(*p11, z), (*p01, z), (*p01, z + h), (*p11, z + h)])  # round 13: glazed (c_sw)
                # round 13 (c_sw pair): the gables' end walls, white (they were open, reading as grey triangles)
                g.poly("roof_white", [(*p00, z), (*p01, z), (*p01, z + h)])
                g.poly("roof_white", [(*p10, z), (*p11, z + h), (*p11, z)])
                g.poly("roof_white", [(*p00, z), (*p01, z + h), (*p01, z)])
                g.poly("roof_white", [(*p10, z), (*p11, z), (*p11, z + h)])
                n += 1
    return n


# 11459 (c_se's foreground, the office tower south-east of the ground): its roof furniture traced from Google Earth's
# straight-down view (ge_detail/b11459_top.png, 250 m range, heading 0; the massing's outline projects onto it within a
# metre). Coordinates are metres in the frame of its 65.9-72.4 m top part: origin (x, y), u along (ux, uy) (its long
# north-west side, running south-east), v at right angles toward the north-east.
B11459_FRAME = (240.934, -234.231, 0.575, -0.818, -31.509, -32.944)
# the dark solar arrays, (u0, u1, v0, v1) in 1 m cells; the plant enclosure, the dish's base and the white boxes
B11459_SOLAR = [(5, 6, 18, 23), (6, 7, 18, 25), (9, 10, 10, 27), (10, 12, 7, 30), (12, 13, 23, 30), (12, 13, 7, 20),
                (13, 14, 24, 30), (13, 14, 7, 19), (14, 15, 13, 19), (14, 15, 26, 30), (15, 17, 14, 19), (15, 18, 27, 30),
                (17, 18, 15, 19), (18, 19, 27, 28), (18, 19, 15, 20), (19, 20, 16, 20), (19, 20, 26, 29), (19, 20, 30, 31),
                (20, 21, 26, 31), (20, 21, 17, 21), (21, 22, 26, 32), (21, 22, 19, 21), (14, 25, 7, 12), (24, 25, 25, 33),
                (25, 26, 27, 33), (24, 27, 34, 40), (25, 27, 7, 10), (26, 27, 25, 33), (28, 30, 7, 24), (30, 31, 10, 16),
                (30, 31, 18, 24), (27, 32, 30, 32), (32, 33, 26, 32), (31, 32, 9, 18), (32, 34, 9, 25), (33, 34, 26, 31),
                (34, 35, 27, 31), (35, 36, 29, 31), (35, 36, 27, 28), (36, 37, 27, 31), (34, 40, 8, 25), (37, 40, 29, 32),
                (40, 41, 29, 31), (40, 41, 9, 25), (41, 44, 29, 32), (43, 44, 22, 26), (43, 44, 17, 21), (44, 45, 12, 26)]
B11459_PLANT = [(-0.8, 36.4), (1.6, 50.6), (19.9, 49.9), (19.0, 34.8)]
B11459_DISH = (16.4, 22.1)
B11459_DISHBASE = [(17.0, 16.6), (19.0, 23.4), (25.8, 21.3), (23.8, 14.6)]
B11459_BOXES = [(1.6, 16.1), (1.3, 21.9), (2.0, 29.0), (5.2, 6.8), (29.5, 27.9), (39.2, 26.8), (50.0, 13.2), (48.5, 3.9),
                (49.1, 16.7), (22.5, 5.1), (13.5, 33.6), (23.5, 37.4)]
# in the notch at the tower's east corner (the 65.9 m roof): a glazed slope against the tower, high on its north-west
# edge, and a red-brown terrace beside it
B11459_GLASS = [(28.0, 34.2), (29.1, 46.9), (41.5, 44.3), (41.1, 32.5)]
B11459_TERRACE = [(29.1, 48.0), (32.4, 55.8), (43.1, 52.5), (40.7, 44.9)]


def b11459(g, base, top, ring, parts, wall, glass):
    """11459, c_se's foreground (Round 12 self-check: our roof was a plain grey slab; Google Earth's c_se and its
    close-ups show a white roof with blocks of solar arrays, a satellite dish on a pole, a screened plant enclosure,
    white boxes, and a glazed slope with a terrace in the notch at the east corner). Walls: dark glass behind white
    fins, the top storey a white band (b11459.png)."""
    x0, y0, ux, uy, U0, V0 = B11459_FRAME
    ax, cr = np.array([ux, uy]), np.array([-uy, ux])
    o = np.array([x0, y0]) + ax * U0 + cr * V0

    def P(u, v):
        return tuple(o + ax * u + cr * v)

    hi = max(t_ for _, t_, _ in parts)
    if top < hi - 0.01:
        if top - base >= 3.0:
            banded(g, ring, base, top, 3.6, 0.9, 2.9, 0.0, wall, glass, top="roof_white", parapet=0.0)
        else:
            g.prism(ring, base, top, wall, top="roof_white")
        if abs(top - 65.9) < 0.2 and base > 10:
            gl = [P(*q) for q in B11459_GLASS]
            zl, zh = top + 0.6, hi - 1.0
            g.poly("sx_glass", [(*gl[0], zh), (*gl[1], zh), (*gl[2], zl), (*gl[3], zl)])
            g.poly("sx_glass", [(*gl[0], top), (*gl[0], zh), (*gl[3], zl), (*gl[3], top)])
            g.poly("sx_glass", [(*gl[1], top), (*gl[2], top), (*gl[2], zl), (*gl[1], zh)])
            g.poly("sx_glass", [(*gl[2], top), (*gl[3], top), (*gl[3], zl), (*gl[2], zl)])
            g.poly("nab_terra", [(*P(*q), top + 0.06) for q in B11459_TERRACE])
        return
    # the top storey: a white plant band (b11459.png), its roof white with the furniture on it
    g.prism(ring, base, top, "white_band", top="roof_white")
    z = top + 0.12
    # each block laid as separate panels about 1 x 1.7 m with white roof showing between them, as Google Earth's c_se
    # shows them close up
    for u0, u1, v0, v1 in B11459_SOLAR:
        # round 13 (PC check of round 12, c_se: "scattered dashes"): one dense block of cells a rect, the panel grid in
        # its texture (1 x 1.7 m cells, a white gap every two panels), as Google Earth's two-panel blocks
        q = [P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)]
        g.poly("solar_cells", [(*q[0], z + 0.3), (*q[1], z + 0.3), (*q[2], z + 0.3), (*q[3], z + 0.3)],
               [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    # the plant enclosure: a low pale screen round dark plant and fans (b11459.png)
    g.prism([P(*q) for q in B11459_PLANT], top, top + 2.4, "steel", top="roof_grey")
    for du, dv in ((4.5, 4.0), (4.5, 9.0), (10.5, 4.0), (10.5, 9.0), (15.5, 6.5)):
        c = np.array(P(B11459_PLANT[0][0] + du + 1.0, B11459_PLANT[0][1] + dv + 1.0))
        g.prism(cylinder_ring(c, 1.4, 12), top + 2.4, top + 3.0, "steel", top="roof_dark")
    g.prism([P(*q) for q in B11459_DISHBASE], top, top + 1.4, "roof_white", top="roof_white")
    for u, v in B11459_BOXES:
        g.prism([P(u - 1.2, v - 0.9), P(u + 1.2, v - 0.9), P(u + 1.2, v + 0.9), P(u - 1.2, v + 0.9)], top, top + 1.3,
                "roof_white", top="roof_white")
    # the dish: about 9 m across (its outline in the straight-down view), on a pole about 5 m tall; Google Earth's c_se
    # sees it obliquely: it faces north-north-east, raised about 32 degrees (b11459.png)
    dc = np.array(P(*B11459_DISH))
    g.prism(cylinder_ring(dc, 0.4, 8), top, top + 5.6, "steel", top="steel")
    el, az = math.radians(32), math.radians(20)
    n = np.array([math.cos(el) * math.sin(az), math.cos(el) * math.cos(az), math.sin(el)])
    e1 = np.array([math.cos(az), -math.sin(az), 0.0]); e2 = np.cross(n, e1)
    ctr = np.array([dc[0], dc[1], top + 6.4])
    rim = [ctr + 4.5 * (math.cos(a) * e1 + math.sin(a) * e2) for a in np.linspace(0, 2 * math.pi, 25)[:-1]]
    back = ctr - n * 1.0
    for i in range(len(rim)):
        a_, b_ = rim[i], rim[(i + 1) % len(rim)]
        g.poly("roof_white", [tuple(ctr + n * 0.05), tuple(a_), tuple(b_)][::-1])
        g.poly("roof_white", [tuple(ctr + n * 0.05), tuple(a_), tuple(b_)])
        g.poly("steel", [tuple(back), tuple(b_), tuple(a_)])


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
        g.lift = land.base(W[wid][1])   # 101 m above its own ground (CTBUH)
        # round 13 (PC check of round 12, ext_135/c_nw): a white grid over blue glass: a heavier frame, lighter glass
        banded(g, W[wid][1], 0.0, 101.0, 3.6, 0.5, 3.1, 0.0, "home_frame", "home_glass", top="roof_grey",
               parapet=1.2, win=(1.0, 1.6))
    g.lift = 0.0
    # Round 12 (PC check of round 11): the city's massing for the two foreground roofs of c_nw and c_sw, which Google
    # Earth shows in detail: 6153 (north-west, c_nw) blue glass under a white roof striped with solar panels; 9966 and
    # 9967 (south-west, c_sw) white roofs with rows of sawtooth glazed rooflights and solar panels.
    looks = {10757: ("near_wall", "dark_glass", "roof_grey"), 16888: ("navy_wall", "louvre_grey", "roof_grey"),
             3046: ("pale_panel", "dark_glass", "roof_grey"), 6153: ("pale_panel", "seven_glass", "stripe_roof"),
             9966: ("near_wall", "dark_glass", "sawtooth"), 9967: ("near_wall", "dark_glass", "sawtooth"),
             15419: ("near_wall", "dark_glass", "roof_grey"), 11459: ("near_wall", "dark_glass", "roof_white")}
    skip = [p for t, p in W.values() if t.get("_id") in S.LANDMARK_WAYS and len(p) > 3]
    for sid, parts in S.com_parts(set(looks), skip).items():
        wall, glass, roof = looks[sid]
        for base, top, ring in parts:
            # Victoria Point's forecourt deck (10757's 0-9.5 m part): Google Earth (obl_s) shows its top as the
            # red-orange paved plaza between the tower and the stadium, (179, 128, 118), with planted beds and trees
            deck = sid == 10757 and base < 0.5
            highest = top >= max(t_ for _, t_, _ in parts) - 0.01
            r_ = "plaza_red" if deck else (roof if highest else "roof_grey")
            if sid in (9966, 9967):
                # (OpenStreetMap's 46 m outline of these had hidden them all: surrounds.com_massing)
                # Round 12 self-check, points picked in Google Earth's c_sw (2026-11-23): the flat roof at the frame's foot,
                # white with blocks of dark solar arrays, reads 39.4 m at (-206, -243) and (-195, -252): the top of the
                # massing's 32.4-39.4 m part. The glazed gables stand on it over the 39.4-43.4 m part (a glazed face picked
                # at 41.4 m at (-195, -244)), five or so across, their glass toward the west. 9967 under the camera is the
                # same white roof with solar arrays.
                hi = top >= max(t_ for _, t_, _ in parts) - 0.01
                if base < 0.5:
                    banded(g, ring, base, top, 3.6, 0.9, 2.9, 0.0, wall, glass, top="roof_white", parapet=0.0)
                elif sid == 9966 and hi:
                    rows = sawtooth_rows(g, ring, base, 9.0, top - base, flip=True)  # round 13 (c_sw pair): glass toward the west, as Google Earth
                    assert rows >= 3, (sid, rows)
                else:
                    g.prism(ring, base, top, "near_wall", top="roof_white")
                    if not hi:
                        rr = np.array(ring); c0 = rr.mean(0)
                        for q in rr:
                            for f_ in (0.45, 0.75):
                                cc = c0 + (q - c0) * f_
                                if _inside(tuple(cc), [tuple(x) for x in ring]):
                                    g.poly("solar_cells", [(cc[0] - 4.0, cc[1] - 2.5, top + 0.08), (cc[0] + 4.0, cc[1] - 2.5, top + 0.08),
                                                     (cc[0] + 4.0, cc[1] + 2.5, top + 0.08), (cc[0] - 4.0, cc[1] + 2.5, top + 0.08)])
                continue
            if sid == 11459:
                b11459(g, base, top, ring, parts, wall, glass)
                continue
            if sid == 15419:
                # Round 12 self-check (ext_000: this office is the foreground right under the camera, not 10757): its
                # massing's upper parts are a big plant room and a lift overrun, plain pale cladding; white
                # air-handling boxes stand round them on the roof (Google Earth ext_000)
                if base > 0.5:
                    # round 13 (PC check of round 12, ext_000): ribbed light grey-blue metal with a louvre band, and
                    # rooftop units on its roof
                    g.prism(ring, base, top, "ribbed", top="roof_grey")
                    rr2 = np.array(ring); c2 = rr2.mean(0); e2 = rr2.max(0) - rr2.min(0)
                    for dx, dy in ((-0.25, -0.2), (0.22, 0.18), (0.0, -0.25), (-0.2, 0.22)):
                        cc = c2 + np.array([dx * e2[0], dy * e2[1]])
                        if _inside(tuple(cc), [tuple(x) for x in ring]) and min(e2) > 6.0:
                            g.prism([(cc[0] - 1.5, cc[1] - 1.1), (cc[0] + 1.5, cc[1] - 1.1), (cc[0] + 1.5, cc[1] + 1.1),
                                     (cc[0] - 1.5, cc[1] + 1.1)], top, top + 1.6, "steel", top="roof_grey")
                    continue
                banded(g, ring, base, top, 3.6, 0.9, 2.9, 0.0, wall, glass, top="roof_grey", parapet=0.0)
                plant = [r2 for b2, _, r2 in parts if b2 > 0.5]
                rr = np.array(ring); c0 = rr.mean(0)
                for f_ in (0.62, 0.78):
                    for q in rr[::max(1, len(rr) // 10)]:
                        cc = c0 + (q - c0) * f_
                        if _inside(tuple(cc), [tuple(x) for x in ring]) and not any(_inside(tuple(cc), [tuple(x) for x in r2]) for r2 in plant):
                            g.prism([(cc[0] - 2.2, cc[1] - 1.6), (cc[0] + 2.2, cc[1] - 1.6), (cc[0] + 2.2, cc[1] + 1.6),
                                     (cc[0] - 2.2, cc[1] + 1.6)], top, top + 2.4, "roof_white", top="roof_white")
                continue
            if r_ == "sawtooth":
                r_ = "roof_white"
                sawtooth(g, ring, top)
            if sid == 16888 and top - base >= 3.0:
                # round 12 (Google Earth c_ne, points picked at 50-63 E, 153 N): a dark navy clad box with a grey louvre
                # band under its parapet, not a pale office with ribbon windows; a light blue strip on its roof
                h_ = top - base
                banded(g, ring, base, top, h_, h_ - 2.6, h_ - 0.4, 0.0, wall, glass, top=r_, parapet=0.0)
                # round 13 (PC check of round 12: the strip and the glazed pavilion were missing): picked in Google
                # Earth's c_ne (2026-11-24): a pool along the box's north-east roof edge, its ends at (58.8, 152.1)
                # and (54.6, 156.1), 20.4 m (model); behind it to the south-west a dark glazed pavilion about 20 by
                # 7 m, 4 m tall, with a grey roof
                pc_ = np.array([56.5, 154.3])
                if _inside(tuple(pc_), [tuple(q) for q in ring]) and abs(top - 20.4) < 4.0:
                    ua = np.array([-0.72, 0.69]); ua /= np.linalg.norm(ua); ub = np.array([ua[1], -ua[0]])
                    if ub @ np.array([-1.0, -1.0]) < 0:
                        ub = -ub   # toward the south-west
                    def box(c, a, b):
                        return [tuple(c - ua * a - ub * b), tuple(c + ua * a - ub * b), tuple(c + ua * a + ub * b),
                                tuple(c - ua * a + ub * b)]
                    g.prism(box(pc_ + ub * 0.5, 8.5, 1.3), top, top + 0.5, "pool_blue", top="pool_blue")
                    g.prism(box(pc_ + ub * 6.5, 10.0, 3.5), top, top + 4.0, "podium_glass", top="roof_grey")
            elif top - base >= 3.0:
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
                                 (c0[0] - pr, c0[1] + pr * 0.7)], top, top + 2.6, "roof_grey", top="roof_grey")  # round 13: low grey (L4)
                    for dx, dy, w_, d_ in ((-0.32, -0.25, 5.0, 3.5), (0.3, 0.22, 4.0, 4.0), (-0.05, 0.33, 6.0, 2.5),
                                           (0.3, -0.3, 3.5, 3.5), (-0.33, 0.2, 4.5, 3.0)):
                        cc = c0 + np.array([dx * ext[0], dy * ext[1]])
                        if _inside(tuple(cc), rr_):
                            g.prism([(cc[0] - w_ / 2, cc[1] - d_ / 2), (cc[0] + w_ / 2, cc[1] - d_ / 2),
                                     (cc[0] + w_ / 2, cc[1] + d_ / 2), (cc[0] - w_ / 2, cc[1] + d_ / 2)], top, top + 1.5,
                                    "roof_grey", top="roof_grey")
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
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(2.2 * px))
    letters = "ABCDEKMORSTWZ"
    pos = 1.0
    while pos < 46.0:
        # round 12 self-check against Google Earth offices_ne / c_e: most of the wall is painted, the bare stretches short
        # round 13 (PC check of round 12: "poster boards"): continuous painting, no boards and no bare gaps
        kind = rng.choice(["piece", "piece", "tags", "throw"])
        span = float(rng.uniform(2.5, 6.5))
        if kind == "bare":
            pos += span
            continue
        x0, y0 = int(pos * px), int(rng.uniform(0.6, 1.4) * px)
        if kind == "piece":
            fill = [(96, 132, 196), (240, 240, 242), (120, 170, 220), (236, 170, 200)][rng.integers(4)]
            # each piece on its own painted ground, as Google Earth's read as coloured blocks from the road
            bg = [(70, 110, 180), (130, 170, 214), (60, 70, 96), (210, 150, 190), (230, 230, 232)][rng.integers(5)]
            # its painted ground as overlapping splashes, not a board
            for _ in range(int(span * 4) + 4):
                ex, ey = x0 + rng.uniform(-0.3, span) * px, rng.uniform(0.4, 3.4) * px
                rx, ry = rng.uniform(0.8, 1.6) * px, rng.uniform(0.6, 1.2) * px
                d.ellipse((ex - rx, ey - ry, ex + rx, ey + ry), fill=bg)
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
        pos += span + float(rng.uniform(0.0, 0.4))
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
        # round 12 (real land): cut into pieces of 5 m at most, each corner 4 cm over the land (land.py)
        fine = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            k = max(1, int(math.ceil(np.linalg.norm(b - a) / 5.0)))
            fine += [a + (b - a) * (i / k) for i in range(1, k + 1)]
        pts = np.array(fine)
        v = 0.0
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            L = float(np.linalg.norm(b - a))
            if L < 0.1:
                continue
            tdir = (b - a) / L
            n = np.array([-tdir[1], tdir[0]]) * Wm / 2
            za, zb = float(land.z(*a)) + 0.04, float(land.z(*b)) + 0.04
            g.poly(mat, [(*(a - n), za), (*(a + n), za), (*(b + n), zb), (*(b - n), zb)][::-1],
                   [(0.0, v), (Wm, v), (Wm, v + L), (0.0, v + L)][::-1])
            v += L


def _yard_tracks(W, reach=450.0):
    """The Southern Cross yard's surface tracks east of the ground (OpenStreetMap railway=rail, not bridges or tunnels)."""
    out = []
    for t, p in W.values():
        if t.get("railway") != "rail" or t.get("layer", "0").startswith("-") or t.get("bridge") or t.get("tunnel"):
            continue
        a = np.array(p, float)
        if len(a) > 1 and (a[:, 0] > 60).any() and (np.abs(a[:, 1]) < reach).any() and (a[:, 0] < reach).any():
            out.append(a)
    return out


def track_strips(g, W):
    """Round 13 (PC check of round 12, obl_w/obl_s/c_ne/top: the yard read as blurry brown stripes): each track of the
    yard as its own 3.6 m strip of ballast, sleepers and rails over the map, cut every 5 m and 5 cm over the land."""
    for pts in _yard_tracks(W):
        fine = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            k = max(1, int(math.ceil(np.linalg.norm(b - a) / 5.0)))
            fine += [a + (b - a) * (i / k) for i in range(1, k + 1)]
        v = 0.0
        for a, b in zip(fine[:-1], fine[1:]):
            L = float(np.linalg.norm(b - a))
            if L < 0.1:
                continue
            n = np.array([-(b - a)[1], (b - a)[0]]) / L * 1.8
            za, zb = float(land.z(*a)) + 0.05, float(land.z(*b)) + 0.05
            g.poly("track", [(*(a - n), za), (*(a + n), za), (*(b + n), zb), (*(b - n), zb)][::-1],
                   [(0.0, v), (3.6, v), (3.6, v + L), (0.0, v + L)][::-1])
            v += L


# Trains stabled in the yard, picked in Google Earth's straight-down view (900 m up over the ground's centre, heading
# north; /tmp/claude-0/r13/top_yard.png): each the two ends of a train in that frame's pixels, mapped to the model at
# 1.765 px a metre about (640, 360), then laid along the nearest track. Most read dark-roofed silver suburban sets.
YARD_TRAINS = [((957, 52), (995, 97), "train_silver"), ((1010, 75), (1040, 125), "train_silver"),
               ((1065, 132), (1117, 197), "train_silver"), ((1030, 325), (1060, 400), "train_silver"),
               ((1042, 425), (1057, 450), "train_white"), ((1125, 320), (1160, 390), "train_silver"),
               ((1055, 465), (1080, 500), "train_silver")]


def trains(g, W):
    S_ = 1588.0 / 900.0
    segs = [(a[i], a[i + 1]) for a in _yard_tracks(W) for i in range(len(a) - 1)]
    def near(q):
        best = None
        for a, b in segs:
            d = b - a; L2 = float(d @ d)
            if L2 < 1e-6:
                continue
            t = max(0.0, min(1.0, float((q - a) @ d) / L2))
            r = a + d * t
            dist = float(np.linalg.norm(q - r))
            if best is None or dist < best[0]:
                best = (dist, r, d / math.sqrt(L2))
        return best
    for (x0, y0), (x1, y1), mat in YARD_TRAINS:
        q0 = np.array([(x0 - 640) / S_, (360 - y0) / S_]); q1 = np.array([(x1 - 640) / S_, (360 - y1) / S_])
        d0, r0, tdir = near((q0 + q1) / 2)
        if d0 > 8.0:
            print("train off any track by %.1f m, skipped" % d0, q0, q1)
            continue
        L = float(np.linalg.norm(q1 - q0))
        ncar = max(1, int(round(L / 24.0)))
        for k in range(ncar):
            ca = r0 + tdir * (k - ncar / 2) * 24.0 + tdir * 0.4
            cb = ca + tdir * 23.2
            nn = np.array([-tdir[1], tdir[0]]) * 1.5
            z0 = float(min(land.z(*ca), land.z(*cb))) + 0.6
            ring = [tuple(ca - nn), tuple(cb - nn), tuple(cb + nn), tuple(ca + nn)]
            g.lift = 0.0
            g.prism(ring, z0, z0 + 3.6, mat, top="rail_steel")  # round 13: Google Earth top_yard: pale roofs


def graffiti_wall(g, W, h=3.4):
    """The painted wall along the stadium side of Wurundjeri Way: the west edge of the northbound carriageway
    (OpenStreetMap ways 580628691, four lanes, then 580628688, three lanes), from the NAB's corner to the stadium's
    north-east corner. Google Earth c_e: rail yards, both carriageways, then the wall under the stadium's east
    offices; the stretch beside the NAB is bare grey concrete, the rest painted (round 11 had it on the rail side)."""
    u = 0.0
    # round 13 (c_ne pair): Google Earth's painted wall runs on north past the stadium's offices to the podium at
    # 150 m north; ours stopped where OpenStreetMap's way ends (128.6, 73.1). It continues along the next northbound way
    for wid, lanes, mat in (("580628691", 4, "concrete_deck"), ("580628688", 3, "graffiti"), ("790397545", 3, "graffiti")):
        pts = np.array(W[wid][1], float)
        if wid == "790397545":
            from shapely.geometry import LineString as _LS
            cut = _LS([tuple(q) for q in pts]).intersection(_LS([(-500, 150.0), (500, 150.0)]))
            keep = [q for q in pts if q[1] <= 150.0]
            if not cut.is_empty and cut.geom_type == "Point":
                keep.append(np.array(cut.coords[0]))
            pts = np.array(keep, float)
        off = lanes * 3.3 / 2 + 1.0
        line = []
        for i in range(len(pts)):
            d = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
            d /= np.linalg.norm(d)
            line.append(pts[i] + np.array([-d[1], d[0]]) * off)    # left of a northbound way is west
        assert line[0][0] < pts[0][0], "the wall must sit west of the carriageway"
        for a, b in zip(line[:-1], line[1:]):
            g.lift = float(min(land.z(*a), land.z(*b)))   # round 12: on the road's land
            g.wall(mat, a, b, -0.5, h, u)
            u += g.wall(mat, b, a, -0.5, h, u)
        if wid == "580628688":
            # ivy over the painted wall's first 9 m at the NAB end, on its road face (Google Earth c_e)
            a, b = line[0], line[1]
            g.lift = float(land.z(*a))
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
    # Round 12 (real land, land.py): heights read off Google Earth's 3D (NAB's top, the mural, the city massing's tops)
    # are above sea level and keep lift 0, their feet running down into the land; heights given above the ground
    # (OpenStreetMap, CTBUH, floor counts) stand on the lowest land under their footprint.
    nab(g, W["221441430"][1], h=60.0)
    near_buildings(g, W)
    graffiti_wall(g, W)
    g.lift = 0.0
    road_strips(g, W)
    track_strips(g, W)
    trains(g, W)
    g.lift = land.base(W["33261092"][1])
    seven(g, W["33261092"][1])
    g.lift = 0.0
    # round 12 (PC check of round 11: "the red/white mural building next to the Seven block is missing"): a navy block
    # against the north end of the Seven fin with a pale box on top; its north wall carries a red and white mural.
    # The mural's position and heights were picked in Google Earth from two views (c_ne and c_nw agree): a north-facing
    # wall at 92.8 m north, from 94.5 to 90 m west of the centre, 10-25 m up.
    mb = [(-101.5, 90.3), (-88.5, 90.3), (-88.5, 92.8), (-101.5, 92.8)]
    g.prism(mb, 0.0, 22.0, "navy_wall", top="roof_grey")
    g.prism([(-100.5, 90.6), (-91.0, 90.6), (-91.0, 92.5), (-100.5, 92.5)], 22.0, 26.0, "pale_panel", top="roof_grey")
    g.poly("mural", [(-89.0, 92.85, 9.5), (-95.0, 92.85, 9.5), (-95.0, 92.85, 24.5), (-89.0, 92.85, 24.5)],
           [(0.0, 0.0), (6.0, 0.0), (6.0, 15.0), (0.0, 15.0)])
    g.lift = land.base(W["44158938"][1])
    round_office(g, W["44158938"][1], h=21.6)  # six floors in Google Earth's ge_vicpoint_b
    g.lift = land.base(W["1246185747"][1])
    ferry(g, W["1246185747"][1])
    # Victoria Point (128 m, 2006): a curved glass tower, recessed balconies behind white slab edges
    # Round 11 (PC check): it read a plain grey slab; Google Earth shows white slab edges and balustrades a floor
    # (about a third of each floor) over blue-grey glass, and a crown stepped back over planted terraces
    vp = W["296368687"][1]
    g.lift = land.base(vp)
    # Round 12 (PC check of round 11): crisper white edges over blue glass, and the crown stepped twice over planted
    # terraces
    banded(g, vp, 0.0, 110.0, 3.05, 0.4, 2.8, 0.45, "white_band", "vp_glass", parapet=1.2, top="roof_garden")
    banded(g, inset(vp, 3.5), 110.0, 119.0, 3.05, 0.4, 2.8, 0.45, "white_band", "vp_glass", parapet=1.2, top="roof_garden")
    banded(g, inset(vp, 7.0), 119.0, 128.0, 3.05, 0.4, 2.8, 0.45, "white_band", "vp_glass", parapet=1.5)
    for zt, ring_ in ((111.2, inset(vp, 1.7)), (120.2, inset(vp, 5.2))):
        for k, q in enumerate(ring_[::2]):
            tree(g, q, zt, 3.0, 1.2)
    # 720 Bourke (109 m, 2014): rippling white balcony slabs, planted (ge_nab_b)
    g.lift = land.base(W["332358301"][1])
    balconies(g, W["332358301"][1], 6.0, 109.0, 3.2, 1.6, wave=1.4, glass="bourke_glass", roof="atrium_glass")
    g.prism(W["332358301"][1], 0.0, 6.0, "podium_glass", top=None)
    # the two sawtooth towers north of the stadium (ge_north65_b): white frames, grey glass
    # Round 10: Google Earth close up (ext_135) shows white panel walls with dark punched windows, not ribbons
    g.lift = land.base(W["221441428"][1])
    # round 13 (PC check of round 12, ext_180): a heavy white lattice over dark glass; Lacrosse white with slot windows
    g.prism(W["221441428"][1], 0.0, 65.0, "lattice_white", top="roof_grey")
    g.lift = land.base(W["992236548"][1])
    g.prism(W["992236548"][1], 0.0, 70.0, "slot_white", top="roof_grey")
    g.lift = 0.0
    for wid in ("711957749", "711957750"):
        jetty(g, W[wid][1])
        gangway(g, W[wid][1], [(-198.1, -34.0), (-223.8, -42.3), (-220.1, -53.6), (-206.7, -92.3), (-202.4, -104.2)])
    gantries(g, W)
    g.lift = land.base(W["33261083"][1])
    southern_cross(g, W["33261083"][1])
    g.lift = WATER_Z
    water_ring = [tuple(q) for q in W["23368547"][1]]
    def in_water(pt):
        return _inside(pt, water_ring)
    rocks(g, [(-254.2, 128.7), (-198.1, -34.0)], in_water)
    rocks(g, [(-176.7, -95.2), (-157.4, -152.8)], in_water, seed=6)
    # pile rows either side of the plaza, square to the shore
    t = np.array([-198.1 + 254.2, -34.0 - 128.7]); t /= np.linalg.norm(t)
    g.lift = 0.0
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
