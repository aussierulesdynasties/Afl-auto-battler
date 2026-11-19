"""Draws every club's current home guernsey (2026) for the 3D match player, from
tools/kits/kits_today.txt, into assets/oval3d/kits_today.png, and writes data/kits_today.csv
(each club's cell, its collar and armhole bindings and its shorts).

    python -P tools/kits/kits_today.py [repo root] [scratch folder for the outputs]

kits_today.txt, one guernsey per line (blank lines and # comments skipped):

    CODE PICTURE | front ops ; op ; ... | back ops ; ...

PICTURE names the photo it was drawn from (the source pages are listed in the file's comments).
The ops and the square are kit_atlas.py's (x 0..1 left to right as you look at that side, y 0..1
from the shoulders down; the back "=" copies the front), drawn larger, since the 3D camera comes
close. Two more ops are not drawn in the picture: the 3D shader draws them on the guernsey's own
edges, where the mesh puts its neck and armholes:

    collar C [w]        the binding round the neck, w cm wide (default 2)
    armholes C [w]      the bindings round both armholes, w cm wide (default 2)

And the shorts worn with it, a plain colour (side stripes are not drawn):

    shorts C            the shorts' colour, written to the csv for the 3D player

One more op is drawn after the others:

    mark C NAME x0 y0 x1 y1   tools/kits/marks/NAME.png (white = the mark), in colour C,
                              stretched into that box

Shapes and colours only, never sponsors, maker or league logos (director 2026-11-13: "Leave them
off"). The club marks that are part of the guernsey's own design (the Lions' lion, Carlton's
monogram, the Eagles' head, the Suns' sun) are drawn: director 2026-11-17, "Draw all five marks".
Each mask is cut from the club's shop photo (the Suns' sun is redrawn from its measured shapes).

y 1 is the photo's hem. On the 3D player the guernsey's hem falls 87% of the way down the square
(measured with a ruler picture, 2026-11-17), so each side is drawn whole and then squeezed into the
top 87%: the photo's hem lands on the player's hem and nothing above it is cut off (director
2026-11-17: "have the guernseys look exactly like the real ones").
"""
import csv
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_atlas  # noqa: E402

SIDE = 256      # each side's pixels: about 2.5 mm a pixel on a 0.6 m guernsey
PER_ROW = 4     # clubs (front + back) per atlas row
YEAR = 2026


def parse(path, clubs):
    kits = []
    for raw in open(path, encoding="utf-8"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        head, _, rest = line.partition("|")
        code, pic = head.split()[:2]
        front, _, back = rest.partition("|")
        cols = clubs(code, YEAR)
        f_ops = [s.strip() for s in front.split(";") if s.strip()]
        b_ops = f_ops if back.strip() == "=" else [s.strip() for s in back.split(";") if s.strip()]
        trims = {}
        for ops in (f_ops, b_ops):
            for op in ops:
                t = op.split()
                if t[0] == "number":
                    trims["number"] = (kit_atlas.colour(t[1], cols), kit_atlas.colour(t[2], cols) if len(t) > 2 else "")
                elif t[0] in ("collar", "armholes", "shorts"):
                    trims[t[0]] = (kit_atlas.colour(t[1], cols), float(t[2]) if len(t) > 2 else 2.0)
        drawn = lambda ops: [o for o in ops if o.split()[0] not in ("collar", "armholes", "shorts", "number")]
        kits.append({"code": code, "pic": pic, "front": drawn(f_ops), "back": drawn(b_ops), "cols": cols,
                     "trims": trims})
    return kits


HEM = 0.87  # where the 3D guernsey's hem falls down the square


def draw(ops, cols, marks_dir):
    """The side's picture: kit_atlas's ops, then each mark stamped on top."""
    im = kit_atlas.draw_side([o for o in ops if o.split()[0] != "mark"], cols)
    for op in ops:
        t = op.split()
        if t[0] != "mark":
            continue
        c, name = kit_atlas.colour(t[1], cols), t[2]
        x0, y0, x1, y1 = [round(float(v) * SIDE) for v in t[3:7]]
        mask = Image.open(os.path.join(marks_dir, name + ".png")).convert("L")
        mask = mask.resize((x1 - x0, y1 - y0), Image.LANCZOS)
        im.paste(Image.new("RGB", mask.size, c), (x0, y0), mask)
    # The photo's hem onto the player's hem; under it, the bottom row carried down (never seen).
    full = im.crop((0, im.height - 1, im.width, im.height)).resize(im.size)
    full.paste(im.resize((im.width, round(im.height * HEM)), Image.LANCZOS), (0, 0))
    return full


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..")
    out = sys.argv[2] if len(sys.argv) > 2 else None
    kits = parse(os.path.join(root, "tools", "kits", "kits_today.txt"), kit_atlas.club_colours(root))
    kit_atlas.SIDE = SIDE
    marks = os.path.join(root, "tools", "kits", "marks")
    rows = math.ceil(len(kits) / PER_ROW)
    atlas = Image.new("RGB", (PER_ROW * SIDE * 2, max(1, rows) * SIDE), "#000000")
    for i, k in enumerate(kits):
        x, y = (i % PER_ROW) * SIDE * 2, (i // PER_ROW) * SIDE
        atlas.paste(draw(k["front"], k["cols"], marks), (x, y))
        atlas.paste(draw(k["back"], k["cols"], marks), (x + SIDE, y))
    atlas.save(os.path.join(out or os.path.join(root, "assets", "oval3d"), "kits_today.png"), optimize=True)
    with open(os.path.join(out or os.path.join(root, "data"), "kits_today.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["code", "cell", "collar", "collar_cm", "armholes", "armholes_cm", "shorts", "picture",
                    "number", "number_edge"])
        for i, k in enumerate(kits):
            c = k["trims"].get("collar", ("", 0.0))
            a = k["trims"].get("armholes", ("", 0.0))
            w.writerow([k["code"], i, c[0], c[1] if c[0] else "", a[0], a[1] if a[0] else "",
                        k["trims"].get("shorts", ("", 0.0))[0], k["pic"], *k["trims"].get("number", ("", ""))])
    print("%d guernseys, atlas %dx%d" % (len(kits), atlas.width, atlas.height))


if __name__ == "__main__":
    main()
