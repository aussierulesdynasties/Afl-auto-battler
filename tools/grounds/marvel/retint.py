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
    "navy": (130, 137, 146),  # round 10: greyer (lilac in the audit); PC check round 2: the east podium rendered (85, 101, 126) against GE (114, 130, 142)
    # round 10 (full audit): the cladding read lilac in both lights. The 2019 street photo (overcast, so near its true
    # colour) shows neutral greys: light grey cladding, near-black navy stair blocks, a dark grey upper band.
    "slate": (140, 144, 148),
    # PC checks 2026-11-23: (150, 146, 136) read a little cool against Google Earth's (171, 161, 151);
    # (160, 144, 131) read tan in the west forecourt, where Google Earth is grey. A light warm grey.
    "paving": (158, 152, 144),
    # Undersides face down, where the match light is a dim blue-violet (measured under the shut roof:
    # a (118, 122, 116) map rendered (49, 49, 69)). Painted warm and green so they render the grey with
    # a faint green the director set for roof undersides (2026-11-21), about (85, 90, 82).
    "soffit": (196, 200, 172),
}


# the bowl's outer face (round 12, item 6.4)
# Calibration render (cloud, sun 60,45): a (60, 90, 130) map rendered (6, 44, 96) on both the east and west faces, which
# face away from that sun and take the sky's blue light, so the red falls away fastest. Google Earth's face reads
# (46, 71, 105). A light grey-blue map renders a mid navy there without turning mauve where the sun does fall.
BOWL = {"band": (110, 120, 134), "glass": (110, 120, 134)}


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


def officeglass():
    """The east office boxes' curtain wall (Google Earth from the east, sun on it): dark blue-grey glass
    with a thin transom every 3 m. Its pale mullions are modelled (parts2.py office_box). 6 m by 6 m a tile."""
    W = H = 1024
    rng = np.random.default_rng(8)
    x = (np.arange(W) + 0.5) / W * 6.0
    y = (np.arange(H) + 0.5) / H * 6.0
    img = np.zeros((H, W, 3), float)
    # round 12 (PC check of round 11): the right box rendered (62, 75, 97) against Google Earth's (73, 97, 119), about
    # 20 too dark and too little blue; a lighter blue-grey glass
    img[:] = (58, 74, 92)
    # each pane its own faint tone, as glass reflects a little differently pane to pane
    pane = rng.normal(0.0, 5.0, (4, 4))
    img += pane[(y[:, None] // 1.5).astype(int).clip(0, 3), (x[None, :] // 1.5).astype(int).clip(0, 3)][..., None]
    img[(y % 3.0) < 0.08, :] = (170, 176, 180)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").save(os.path.join(TEX, "officeglass.png"))


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
    # seven_red: the Seven block's red 7 (PC check of round 11: right as it was, the old signred), kept when the roof
    # sign's panels were muted in round 12
    for n, c in (("lamp", (255, 250, 236)), ("screen", (16, 20, 28)), ("seven_red", (178, 20, 25))):
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


def sign_panels():
    """The roof sign's panels (round 12, PC check of round 11: the sign read a loud red block, 36% red pixels against
    Google Earth's 0.7%; Google Earth shows white letters on a muted dark maroon-grey ground, the STADIUM half dark
    grey). Each panel's background is moved to that colour, keeping its texture; the white letters stay."""
    # Round 12 self-check (ext_270, sun on, ground between the letters): (104, 54, 58) rendered (139, 101, 103) against
    # Google Earth's (117, 107, 106), still a red block; (62, 60, 64) rendered (102, 101, 108) against (103, 115, 123).
    # Scaled by those ratios:
    for name, target in (("sign_marvel", (88, 57, 60)), ("signred", (88, 57, 60)),
                         ("sign_stadium", (62, 68, 73)), ("signblack", (62, 68, 73))):
        orig = os.path.join(TEX, "%s_orig.png" % name)
        path = os.path.join(TEX, "%s.png" % name)
        if not os.path.exists(orig):
            Image.open(path).save(orig)
        a = np.asarray(Image.open(orig).convert("RGB"), float)
        letter = a.min(axis=2) > 150
        bg = ~letter
        m = a[bg].mean(0)
        b = a.copy()
        b[bg] = np.clip((a[bg] - m) * 0.5 + np.array(target, float), 0, 255)
        b[letter] = np.clip(a[letter] * 0.92, 0, 255)
        Image.fromarray(b.astype(np.uint8), "RGB").save(path)
        print(name, m.round(), "->", target, "letters %.1f%%" % (100 * letter.mean()))


def main():
    sign_panels()
    for n, t in TARGET.items():
        retint(n, t)
    retint("endroof", (168, 169, 165), out="endrib")
    # The bowl's top band, over the braces up to the roof's edge, the dark blue the MARVEL STADIUM
    # letters stand on (it had the undersides' texture, which is painted warm for the dim light under
    # a roof and so read khaki out here).
    # 2026-11-22: (56, 68, 96) rendered near-black navy on the shaded east face, (1, 27, 70) against
    # Google Earth's (105, 119, 136); a greyer, lighter blue keeps the letters' dark ground in the sun too.
    # round 12 (item 6.4): (62, 68, 82) rendered (6, 25, 56) on the shaded faces against Google Earth's (47, 72, 107)
    retint("upperwall", (96, 106, 122), src="soffit", out="upperwall")
    # the east offices' lobby walls, dark in the void under the boxes: the band's old dark grey-navy
    retint("lobbydark", (62, 68, 82), src="soffit", out="lobbydark")
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
    retint("bluepanel", (52, 58, 74), src="slate", out="bluepanel")  # round 10: the photo's stair blocks (42, 47, 61) by white 207
    # the west podium's piers and spandrels: grey-blue panels, not white (Google Earth c_w, ferry_b).
    # PC check 2026-11-23: (126, 136, 148) rendered (118, 128, 142) against Google Earth's darker blue
    # (74, 103, 129); the west face renders about 0.94 of its colour.
    CONTRAST["podiumpanel"] = 0.5
    # round 2: (80, 109, 134) still rendered a light lavender (103, 116, 139) in the sun against (73, 102, 129)
    # round 10: (52, 92, 124) read saturated blue from every side; the photo shows the podium's piers light grey and its
    # glazing dark, Google Earth's darker blue was its glass and shade together
    retint("podiumpanel", (150, 156, 162), src="slate", out="podiumpanel")
    # the forecourt plinth's street front: blue-grey glass (PC check: Google Earth (76, 102, 118))
    retint("fcglass", (81, 108, 124), src="curtain", out="fcglass")
    # the east office boxes' ribbon glass: light grey (PC check round 3: Google Earth's east boxes are pale grey/white)
    # round 4: (138, 146, 152) still rendered (85, 100, 126) against (117, 132, 142); east-facing walls render
    # about 0.57-0.73 of their colour, so a light grey
    # round 8 (PC sun-on check, like for like): the light grey read (156, 159, 162) against Google Earth's
    # (117, 132, 142). Google Earth shows the boxes' faces as dark blue-grey glass behind slim pale vertical
    # mullions: officeglass() paints the glass, parts2.py models the mullions.
    officeglass()
    # Round 12 (item 6.4, measured on the corrected ext_045 frame, sun on): the bowl's outer face read as near-black
    # glass bands (13, 25, 57) between lilac silver bands (77, 87, 126); Google Earth's face is one even mid navy-blue,
    # (46, 71, 105) all the way down. The face's bands get their own matt materials so the stand roofs' silver and
    # the offices' glass keep theirs.
    CONTRAST["bowlband"] = CONTRAST["bowlglass"] = 0.5
    retint("bowlband", BOWL["band"], src="silver", out="bowlband")
    retint("bowlglass", BOWL["glass"], src="glass", out="bowlglass")
    tiles = os.path.join(TEX, "tiles.json")
    j = json.load(open(tiles))
    j["endrib"] = j["endroof"]
    j["upperwall"] = j["soffit"]
    j["lobbydark"] = j["soffit"]
    j["tread"] = j["concrete"]
    j["ribbon"] = [12, 1.7]
    j["grille"] = [3, 3]
    j["lamp"] = [1, 1]
    j["seven_red"] = [1, 1]
    j["screen"] = [1, 1]
    j["sign_mvst"] = [1, 1]
    # the roof sign's panels are 7.6 m tall (parts2.py, measured 2026-11-23): one tile of lettering each
    j["sign_marvel"] = [13.5, 7.6]
    j["sign_stadium"] = [19.9, 7.6]
    j["bluepanel"] = j["slate"]
    j["podiumpanel"] = j["slate"]
    j["fcglass"] = j["curtain"]
    j["bowlband"] = j["silver"]
    j["bowlglass"] = j["glass"]
    j["officeglass"] = [6, 6]
    for gone in ("office", "undercroft", "louvre"):
        j.pop(gone, None)
    json.dump(j, open(tiles, "w"))


if __name__ == "__main__":
    main()
