"""Draws every club's home guernsey, season by season (Legacy mode, TODO row 142), from
tools/kits/kits.txt into one atlas the figures and crests wear, and writes data/legacy/kits.csv
(which seasons wear which cell).

    python -P tools/kits/kit_atlas.py [repo root] [kits file] [scratch folder for the outputs]

kits.txt, one guernsey per line (blank lines and # comments skipped):

    CODE FROM-TO SPEC | front ops ; op ; ... | back ops ; ...

SPEC is the game's guernsey spec (design:base/pattern/pattern2/shorts, as data/clubs.csv), used
for the socks, shorts, the oval's discs and the colour bars; its design is the nearest of the
game's own. TO may be blank ("1990-"): to 2025. The back "=" copies the front.

Each side is drawn as seen, in a square: x 0..1 left to right as you look at it, y 0..1 from
the shoulders down. On the front the wearer's right is your left; the shader flips the back.
Colours are #hex, or p s a (the club's primary, secondary and accent that season: data/clubs.csv
under data/legacy/clubs_by_year.csv's era colours), W white, K black.

Ops:
    fill C
    stripes C N [x0 x1 y0 y1]      N equal bands across x0..x1, odd ones (2nd, 4th...) in C
    hoops C N [y0 y1 x0 x1]        the same down y0..y1
    cyc y0 h n C1 C2 ...           n hoops h tall from y0, cycling the colours (the last runs to the hem)
    vcyc x0 w n C1 C2 ...          n stripes w wide from x0, cycling the colours
    rect C x0 y0 x1 y1
    poly C x y x y x y ...
    band C y0 y1                   a full-width hoop
    sash C w [rising]              a sash w wide, wearer's left shoulder to right hip
                                   (on the front: your right shoulder down to your left)
    vneck C depth half [w]         a V collar trim, depth down from the top, half width
    round C depth half [w]         a round collar trim
    vfill C depth half             the V's opening filled (a contrasting V insert)
    arms C [w]                     armhole trim both sides
    hem C [w]                      a band at the hem
"""
import csv
import math
import os
import sys

from PIL import Image, ImageDraw

SS = 4          # supersampling
SIDE = 80       # each side's pixels in the atlas
PER_ROW = 12    # cells (front + back) per atlas row
LAST = 2025     # an open era runs to here; 2026 on is clubs.csv's own guernsey

NAMED = {"W": "#FFFFFF", "K": "#000000"}


def colour(tok, spec_cols):
    if tok in spec_cols:
        return spec_cols[tok]
    if tok in NAMED:
        return NAMED[tok]
    if tok.startswith("#") and len(tok) in (4, 7):
        if len(tok) == 4:
            tok = "#" + "".join(ch * 2 for ch in tok[1:])
        return tok.upper()
    raise ValueError("colour %r" % tok)


# Where the guernsey's edges sit in this square (measured from the figure sheets'
# coordinates): the neck dips at the top centre, the armholes cut the top corners.
ARM_X = 0.10    # armhole depth in from each side
ARM_Y = 0.34    # armhole bottom, down from the top


def draw_side(ops, spec_cols):
    n = SIDE * SS
    im = Image.new("RGB", (n, n), spec_cols["p"])
    d = ImageDraw.Draw(im)
    P = lambda x, y: (x * n, y * n)
    for op in ops:
        t = op.split()
        if not t:
            continue
        k, a = t[0], t[1:]
        if k in ("cyc", "vcyc"):
            # cyc y0 h n C1 C2 ...: n hoops h tall from y0, cycling the colours (vcyc: stripes from x0)
            s0, h, cnt = float(a[0]), float(a[1]), int(a[2])
            cs = [colour(x, spec_cols) for x in a[3:]]
            for i in range(cnt):
                lo, hi = s0 + i * h, (s0 + (i + 1) * h) if i < cnt - 1 or k == "vcyc" else 1.0
                box = [P(0, lo), P(1, hi)] if k == "cyc" else [P(lo, 0), P(hi, 1)]
                d.rectangle(box, fill=cs[i % len(cs)])
            continue
        c = colour(a[0], spec_cols) if a else None
        f = [float(v) for v in a[1:]]
        if k == "fill":
            d.rectangle([0, 0, n, n], fill=c)
        elif k in ("stripes", "hoops"):
            cnt = int(f[0])
            r = f[1:] + [0, 1, 0, 1][len(f) - 1:]
            if k == "stripes":
                x0, x1, y0, y1 = r[:4]
                w = (x1 - x0) / cnt
                for i in range(1, cnt, 2):
                    d.rectangle([P(x0 + i * w, y0), P(x0 + (i + 1) * w, y1)], fill=c)
            else:
                y0, y1, x0, x1 = r[:4]
                h = (y1 - y0) / cnt
                for i in range(1, cnt, 2):
                    d.rectangle([P(x0, y0 + i * h), P(x1, y0 + (i + 1) * h)], fill=c)
        elif k == "rect":
            d.rectangle([P(f[0], f[1]), P(f[2], f[3])], fill=c)
        elif k == "poly":
            pts = [P(f[i], f[i + 1]) for i in range(0, len(f), 2)]
            d.polygon(pts, fill=c)
        elif k == "band":
            d.rectangle([P(0, f[0]), P(1, f[1])], fill=c)
        elif k == "sash":
            # Wearer's left shoulder to right hip: from the front, your right shoulder down
            # to your left; "rising" the other way.
            dx = f[0] / 2 * math.sqrt(2)
            sx, ex = (0.15, 0.85) if len(f) > 1 and f[1] > 0 else (0.85, 0.15)
            d.polygon([P(sx - dx, -0.05), P(sx + dx, -0.05), P(ex + dx, 1.05), P(ex - dx, 1.05)], fill=c)
        elif k in ("vneck", "round", "vfill"):
            depth, half = f[0], f[1]
            w = f[2] if len(f) > 2 else 0.035
            if k == "vfill":
                d.polygon([P(0.5 - half, -0.01), P(0.5 + half, -0.01), P(0.5, depth)], fill=c)
            elif k == "vneck":
                d.line([P(0.5 - half, 0), P(0.5, depth), P(0.5 + half, 0)], fill=c, width=int(w * n), joint="curve")
            else:
                d.arc([P(0.5 - half, -depth), P(0.5 + half, depth)], 0, 180, fill=c, width=int(w * n))
        elif k == "arms":
            w = f[0] if f else 0.035
            for side in (0, 1):
                x = ARM_X if side == 0 else 1 - ARM_X
                e = 0.0 if side == 0 else 1.0
                d.line([P(x, -0.01), P(x, ARM_Y * 0.7), P((x + e) / 2, ARM_Y), P(e, ARM_Y + 0.02)],
                       fill=c, width=int(w * n), joint="curve")
        elif k == "hem":
            w = f[0] if f else 0.04
            d.rectangle([P(0, 1 - w), P(1, 1)], fill=c)
        else:
            raise ValueError("op %r" % op)
    return im.resize((SIDE, SIDE), Image.LANCZOS)


def club_colours(root):
    """A function (code, year) -> p, s and a that club wore that season: data/clubs.csv and
    data/legacy/past_clubs.csv, with data/legacy/clubs_by_year.csv's era colours over them."""
    base = {}
    for f in ("data/clubs.csv", "data/legacy/past_clubs.csv"):
        for r in csv.DictReader(open(os.path.join(root, f), encoding="utf-8")):
            base[r["code"]] = {"p": r["primary"].upper(), "s": r["secondary"].upper(), "a": r["accent"].upper()}
    eras = list(csv.DictReader(open(os.path.join(root, "data/legacy/clubs_by_year.csv"), encoding="utf-8")))

    def at(code, year):
        cols = dict(base[code])
        for r in eras:
            if r["code"] == code and int(r["from"]) <= year <= int(r["to"] or 9999):
                for k, col in (("p", "primary"), ("s", "secondary"), ("a", "accent")):
                    if r[col]:
                        cols[k] = r[col].upper()
        return cols
    return at


def parse(path, clubs):
    """Every picture's line: its drawing (or the picture it copies) and its seasons."""
    kits = []
    by_pic = {}
    for no, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        head, _, rest = line.partition("|")
        t = head.split()
        code, years, pic = t[0], t[1], t[2]
        if years.startswith("alt"):
            lo = hi = 0     # drawn and charted, but no season wears it (a one-off or mid-season change)
            worn = int(years[3:])
        else:
            a, _, b = years.partition("-")
            lo, hi = int(a), int(b) if b else LAST
            worn = lo
        k = {"code": code, "from": lo, "to": hi, "pic": pic, "line": no, "year": years}
        if len(t) > 3 and t[3] == "=":
            src = by_pic[t[4]]
            k.update({"spec": src["spec"], "front": src["front"], "back": src["back"], "cols": src["cols"]})
        else:
            spec = t[3]
            front, _, back = rest.partition("|")
            cols = clubs(code, worn)
            f_ops = [s.strip() for s in front.split(";") if s.strip()]
            b_ops = f_ops if back.strip() == "=" else [s.strip() for s in back.split(";") if s.strip()]
            k.update({"spec": spec, "front": f_ops, "back": b_ops, "cols": cols})
        by_pic[pic] = k
        kits.append(k)
    return kits


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..")
    src = sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, "tools", "kits", "kits.txt")
    out = sys.argv[3] if len(sys.argv) > 3 else None    # a scratch folder instead of the game's files
    kits = parse(src, club_colours(root))
    # One cell per distinct drawing: pictures that differ only in what isn't drawn share it.
    cells = {}
    for k in kits:
        key = repr((k["front"], k["back"], sorted(k["cols"].items())))
        k["cell"] = cells.setdefault(key, len(cells))
    rows = math.ceil(len(cells) / PER_ROW)
    atlas = Image.new("RGB", (PER_ROW * SIDE * 2, max(1, rows) * SIDE), "#000000")
    done = set()
    for k in kits:
        i = k["cell"]
        if i in done:
            continue
        done.add(i)
        x, y = (i % PER_ROW) * SIDE * 2, (i // PER_ROW) * SIDE
        atlas.paste(draw_side(k["front"], k["cols"]), (x, y))
        atlas.paste(draw_side(k["back"], k["cols"]), (x + SIDE, y))
    atlas.save(os.path.join(out or os.path.join(root, "assets", "vignette"), "kits_atlas.png"), optimize=True)
    with open(os.path.join(out or os.path.join(root, "data", "legacy"), "kits.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["code", "from", "to", "cell", "guernsey", "picture"])
        for k in kits:
            w.writerow([k["code"], k["from"], k["to"], k["cell"], k["spec"], k["pic"]])
    print("%d pictures, %d drawings, atlas %dx%d" % (len(kits), len(cells), atlas.width, atlas.height))


if __name__ == "__main__":
    main()
