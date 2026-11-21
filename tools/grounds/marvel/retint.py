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


def main():
    for n, t in TARGET.items():
        retint(n, t)
    retint("endroof", (168, 169, 165), out="endrib")
    tiles = os.path.join(TEX, "tiles.json")
    j = json.load(open(tiles))
    j["endrib"] = j["endroof"]
    json.dump(j, open(tiles, "w"))


if __name__ == "__main__":
    main()
