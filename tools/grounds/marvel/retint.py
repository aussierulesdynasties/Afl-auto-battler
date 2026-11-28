"""Marvel Stadium's surface colours brought to Google Earth's (Marvel rebuild, stage 5).

The hand-made textures (.claude/review/marvel/mv2/tex, gen_tex.py then paint_tex.py) keep their
joints, seams and panels; this moves each one's mean colour to what Google Earth shows from the same
camera (tools: docs/MCG_STANDARD.md), keeping every pixel's difference from the mean. It also writes
endrib.png, the end roofs' radial ribs (they used the tiers' dark riser texture). Run once after
paint_tex.py; the originals are kept beside them as <name>_orig.png so a rerun starts from them.
Looks only.

    python3 tools/grounds/marvel/retint.py
"""
import json, os
import numpy as np
from PIL import Image

TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".claude", "review", "marvel", "mv2", "tex")

# Google Earth, 2026-11-21 (obl_* and ext_* sheets): the arch trusses and the space trusses are pale
# grey-green, not teal; the end roofs read nearly as light as the side roofs; the side roofs a warm
# light grey; the facade's cladding light blue-grey, with far less panel-to-panel tone than the hand
# painting had (CONTRAST); the forecourt paving grey.
TARGET = {
    "teal": (196, 208, 202),
    "endroof": (196, 196, 190),
    "deck": (206, 206, 199),
    "navy": (108, 120, 138),
    "slate": (130, 138, 150),
    "paving": (150, 146, 136),
    # The blue office blocks on the corners (ge c_ne): a mid blue, lighter and bluer than the navy.
    "louvre": (98, 110, 134),
    # Undersides face down, where the match light is a dim blue-violet (measured under the shut roof:
    # a (118, 122, 116) map rendered (49, 49, 69)). Painted warm and green so they render the grey with
    # a faint green the director set for roof undersides (2026-11-21), about (85, 90, 82).
    "soffit": (196, 200, 172),
}


# How much of each texture's own variation is kept (1 = all).
CONTRAST = {"navy": 0.5, "slate": 0.45}


def retint(name, target, src=None, out=None):
    orig = os.path.join(TEX, "%s_orig.png" % (src or name))
    path = os.path.join(TEX, "%s.png" % (src or name))
    if not os.path.exists(orig):
        Image.open(path).save(orig)
    a = np.asarray(Image.open(orig).convert("RGB"), float)
    m = a.reshape(-1, 3).mean(0)
    b = np.clip((a - m) * CONTRAST.get(name, 1.0) + np.array(target, float), 0, 255).astype(np.uint8)
    Image.fromarray(b, "RGB").save(os.path.join(TEX, "%s.png" % (out or name)))
    print(out or name, m.round(), "->", target)


def office():
    """The pale office boxes over the east concourse (Wurundjeri Way side; Google Earth c_e, c_ne): a
    light grey spandrel band at every storey and a ribbon of dark glass between, behind slim pale fins
    every 0.75 m. One storey of 3.75 m by 6 m a tile; the walls start 9 m up, so each storey's
    spandrel starts 1.5 m into the tile (texture v is height, from the bottom)."""
    W, H = 1024, 640
    img = np.zeros((H, W, 3), float)
    f = 1.0 - (np.arange(H) + 0.5) / H  # height in the storey, 0 at the bottom
    spandrel = ((f - 0.4) % 1.0) < 0.35
    x = (np.arange(W) + 0.5) / W
    fin = ((x * 8.0) % 1.0) < 0.12
    glass = np.array((104, 114, 126), float)
    img[:] = glass
    img[:, fin] = (186, 190, 194)
    # a little sky in the glass's top, as Google Earth's glazing shows
    sky = np.clip((((f - 0.4) % 1.0) - 0.35) / 0.65, 0, 1)
    img += (np.array((0, 0, 0)) + (1 - sky)[:, None, None] * np.array((14, 16, 20)))
    img[spandrel] = (202, 205, 209)
    edge = (np.abs(((f - 0.4) % 1.0) - 0.35) < 0.012) | (((f - 0.4) % 1.0) < 0.012)
    img[edge] = (150, 154, 158)
    rng = np.random.default_rng(7)
    img += rng.normal(0, 2.0, img.shape)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").save(os.path.join(TEX, "office.png"))


def undercroft():
    """The open ground floor under the east boxes: slim pale columns every 6 m in front of a shaded
    recess, darker towards the soffit above it. 6 m by 9 m a tile (0 to 9 m up)."""
    W, H = 512, 768
    f = 1.0 - (np.arange(H) + 0.5) / H
    img = np.zeros((H, W, 3), float)
    img[:] = np.array((62, 68, 78), float)
    img *= (1.0 - 0.35 * f)[:, None, None]
    x = (np.arange(W) + 0.5) / W
    img[:, x < 0.09] = (168, 170, 172)
    img[f > 0.93] = (150, 152, 154)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").save(os.path.join(TEX, "undercroft.png"))


def ribbon():
    """The ribbon screens on the fronts of the middle and top tiers: a dark screen in a thin silver
    frame, lit a deep club-neutral blue with a brighter line of text-like blocks (no words, no
    sponsors). 12 m by 1.7 m a tile; the fronts run from 0.6 m under the tier's front row."""
    W, H = 1024, 145
    img = np.zeros((H, W, 3), float)
    img[:] = (22, 26, 40)
    f = 1.0 - (np.arange(H) + 0.5) / H
    band = (f > 0.32) & (f < 0.78)
    img[band] = (30, 52, 104)
    rng = np.random.default_rng(3)
    x = 40
    while x < W - 60:
        w = int(rng.integers(18, 70))
        rows = (f > 0.46) & (f < 0.64)
        img[rows, x:x + w] = (150, 170, 210)
        x += w + int(rng.integers(10, 40))
    img[(f < 0.06) | (f > 0.94)] = (150, 152, 156)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").save(os.path.join(TEX, "ribbon.png"))


def main():
    for n, t in TARGET.items():
        retint(n, t)
    retint("endroof", (168, 169, 165), out="endrib")
    # The bowl's top band, over the braces up to the roof's edge, the dark blue the MARVEL STADIUM
    # letters stand on (it had the undersides' texture, which is painted warm for the dim light under
    # a roof and so read khaki out here).
    retint("upperwall", (56, 68, 96), src="soffit", out="upperwall")
    retint("tread", (146, 146, 142), src="concrete", out="tread")
    office()
    undercroft()
    ribbon()
    tiles = os.path.join(TEX, "tiles.json")
    j = json.load(open(tiles))
    j["endrib"] = j["endroof"]
    j["upperwall"] = j["soffit"]
    j["tread"] = j["concrete"]
    j["ribbon"] = [12, 1.7]
    j["office"] = [6, 3.75]
    j["undercroft"] = [6, 9]
    json.dump(j, open(tiles, "w"))


if __name__ == "__main__":
    main()
