"""Draws every club's current home guernsey (2026) for the 3D match player, from
tools/kits/kits_today.txt, into assets/oval3d/kits_today.png, and writes data/kits_today.csv
(each club's cell and its collar and armhole bindings).

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

Like kits.txt: shapes and colours only, never sponsors, maker or league logos, or the club
emblem (director 2026-11-13: "Leave them off").
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
                if t[0] in ("collar", "armholes"):
                    trims[t[0]] = (kit_atlas.colour(t[1], cols), float(t[2]) if len(t) > 2 else 2.0)
        drawn = lambda ops: [o for o in ops if o.split()[0] not in ("collar", "armholes")]
        kits.append({"code": code, "pic": pic, "front": drawn(f_ops), "back": drawn(b_ops), "cols": cols,
                     "trims": trims})
    return kits


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..")
    out = sys.argv[2] if len(sys.argv) > 2 else None
    kits = parse(os.path.join(root, "tools", "kits", "kits_today.txt"), kit_atlas.club_colours(root))
    kit_atlas.SIDE = SIDE
    rows = math.ceil(len(kits) / PER_ROW)
    atlas = Image.new("RGB", (PER_ROW * SIDE * 2, max(1, rows) * SIDE), "#000000")
    for i, k in enumerate(kits):
        x, y = (i % PER_ROW) * SIDE * 2, (i // PER_ROW) * SIDE
        atlas.paste(kit_atlas.draw_side(k["front"], k["cols"]), (x, y))
        atlas.paste(kit_atlas.draw_side(k["back"], k["cols"]), (x + SIDE, y))
    atlas.save(os.path.join(out or os.path.join(root, "assets", "oval3d"), "kits_today.png"), optimize=True)
    with open(os.path.join(out or os.path.join(root, "data"), "kits_today.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["code", "cell", "collar", "collar_cm", "armholes", "armholes_cm", "picture"])
        for i, k in enumerate(kits):
            c = k["trims"].get("collar", ("", 0.0))
            a = k["trims"].get("armholes", ("", 0.0))
            w.writerow([k["code"], i, c[0], c[1] if c[0] else "", a[0], a[1] if a[0] else "", k["pic"]])
    print("%d guernseys, atlas %dx%d" % (len(kits), atlas.width, atlas.height))


if __name__ == "__main__":
    main()
