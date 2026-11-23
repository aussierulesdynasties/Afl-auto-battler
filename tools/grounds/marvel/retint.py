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
    "navy": (128, 140, 154),  # PC check round 2: the east podium rendered (85, 101, 126) against GE (114, 130, 142)
    "slate": (130, 138, 150),
    # PC checks 2026-11-23: (150, 146, 136) read a little cool against Google Earth's (171, 161, 151);
    # (160, 144, 131) read tan in the west forecourt, where Google Earth is grey. A light warm grey.
    "paving": (158, 152, 144),
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


def grille():
    """The louvres behind the blue blocks' vent openings (Google Earth c_ne): pale grey-blue slats every
    15 cm, dark gaps between, a mullion every 1.5 m. The opening itself is modelled (vent_block); the
    slats are too fine to read in depth. 3 m by 3 m a tile."""
    W = H = 512
    f = (np.arange(H) + 0.5) / H
    img = np.zeros((H, W, 3), float)
    slat = ((f * 20.0) % 1.0) < 0.55
    img[:] = (38, 44, 58)
    img[slat] = (150, 160, 176)
    img[slat & (((f * 20.0) % 1.0) > 0.4)] = (112, 122, 140)
    x = (np.arange(W) + 0.5) / W
    img[:, ((x * 2.0) % 1.0) < 0.035] = (170, 176, 186)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").save(os.path.join(TEX, "grille.png"))


def ribbon():
    """The ribbon screens on the fronts of the middle and top tiers: a dark screen in a thin silver
    frame, lit a deep club-neutral blue with a brighter line of text-like blocks (no words, no
    sponsors). 12 m by 1.7 m a tile; the fronts run from 0.6 m under the tier's front row."""
    W, H = 1024, 145
    img = np.zeros((H, W, 3), float)
    # 2026-11-22: the photos of the bowl (Wikimedia Commons, curtain raiser and 2025 panorama) show the ribbons
    # as bright light-blue bands right round each tier; the dark screen read as a black stripe. The build
    # makes this texture emissive too, so the ribbons glow at night.
    img[:] = (20, 30, 56)
    f = 1.0 - (np.arange(H) + 0.5) / H
    band = (f > 0.24) & (f < 0.86)
    img[band] = (44, 118, 204)
    rng = np.random.default_rng(3)
    x = 40
    while x < W - 60:
        w = int(rng.integers(18, 70))
        rows = (f > 0.46) & (f < 0.64)
        img[rows, x:x + w] = (196, 222, 255)
        x += w + int(rng.integers(10, 40))
    img[(f < 0.06) | (f > 0.94)] = (150, 152, 156)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").save(os.path.join(TEX, "ribbon.png"))


def flat():
    """Flat-coloured textures: the floodlights' lenses (emissive in the build) and the screens' dark faces
    (the match draws the score over them, Oval3DScreens)."""
    for n, c in (("lamp", (255, 250, 236)), ("screen", (16, 20, 28))):
        Image.fromarray(np.full((16, 16, 3), c, np.uint8), "RGB").save(os.path.join(TEX, "%s.png" % n))


def label():
    """MARVEL STADIUM in white on black, the label over each small corner scoreboard (photos: Hawthorn v
    Brisbane 2024, the curtain raiser, Ed Sheeran's stage 2026). Lettering on a flat sign, as the real one."""
    from PIL import ImageDraw, ImageFont
    w, h = 1024, 120
    im = Image.new("RGB", (w, h), (14, 14, 16))
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 84)
    d = ImageDraw.Draw(im)
    tb = d.textbbox((0, 0), "MARVEL STADIUM", font=f)
    d.text(((w - (tb[2] - tb[0])) / 2 - tb[0], (h - (tb[3] - tb[1])) / 2 - tb[1]), "MARVEL STADIUM", font=f, fill=(238, 238, 236))
    im.save(os.path.join(TEX, "sign_mvst.png"))


def main():
    for n, t in TARGET.items():
        retint(n, t)
    retint("endroof", (168, 169, 165), out="endrib")
    # The bowl's top band, over the braces up to the roof's edge, the dark blue the MARVEL STADIUM
    # letters stand on (it had the undersides' texture, which is painted warm for the dim light under
    # a roof and so read khaki out here).
    # 2026-11-22: (56, 68, 96) rendered near-black navy on the shaded east face, (1, 27, 70) against
    # Google Earth's (105, 119, 136); a greyer, lighter blue keeps the letters' dark ground in the sun too.
    retint("upperwall", (80, 92, 114), src="soffit", out="upperwall")
    # Glazing: the dark glass rendered black in shade (Google Earth's office glass reads (96, 114, 132),
    # its shopfronts (84, 104, 121), sky in them included). Lighter, so it reads as glass, not holes.
    retint("glass", (74, 90, 108))
    retint("shopglass", (52, 74, 98))
    retint("tread", (146, 146, 142), src="concrete", out="tread")
    ribbon()
    grille()
    flat()
    label()
    # the blue blocks' plain cladding: the panel joints of the slate texture, a mid blue (Google Earth c_ne)
    CONTRAST["bluepanel"] = 0.5
    retint("bluepanel", (96, 112, 140), src="slate", out="bluepanel")
    # the west podium's piers and spandrels: grey-blue panels, not white (Google Earth c_w, ferry_b).
    # PC check 2026-11-23: (126, 136, 148) rendered (118, 128, 142) against Google Earth's darker blue
    # (74, 103, 129); the west face renders about 0.94 of its colour.
    CONTRAST["podiumpanel"] = 0.5
    # round 2: (80, 109, 134) still rendered a light lavender (103, 116, 139) in the sun against (73, 102, 129)
    retint("podiumpanel", (52, 92, 124), src="slate", out="podiumpanel")
    # the forecourt plinth's street front: blue-grey glass (PC check: Google Earth (76, 102, 118))
    retint("fcglass", (81, 108, 124), src="curtain", out="fcglass")
    # the east office boxes' ribbon glass: light grey (PC check round 3: Google Earth's east boxes are pale grey/white)
    retint("officeglass", (138, 146, 152), src="glass", out="officeglass")
    tiles = os.path.join(TEX, "tiles.json")
    j = json.load(open(tiles))
    j["endrib"] = j["endroof"]
    j["upperwall"] = j["soffit"]
    j["tread"] = j["concrete"]
    j["ribbon"] = [12, 1.7]
    j["grille"] = [3, 3]
    j["lamp"] = [1, 1]
    j["screen"] = [1, 1]
    j["sign_mvst"] = [1, 1]
    # the roof sign's panels are 7.6 m tall (parts2.py, measured 2026-11-23): one tile of lettering each
    j["sign_marvel"] = [13.5, 7.6]
    j["sign_stadium"] = [19.9, 7.6]
    j["bluepanel"] = j["slate"]
    j["podiumpanel"] = j["slate"]
    j["fcglass"] = j["curtain"]
    j["officeglass"] = j["glass"]
    for gone in ("office", "undercroft", "louvre"):
        j.pop(gone, None)
    json.dump(j, open(tiles, "w"))


if __name__ == "__main__":
    main()
