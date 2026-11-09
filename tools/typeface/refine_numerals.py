"""Row 6.29 (STYLE-02): finish ARD Signwriter's figures so look-alikes read apart
and score forms fit their line. Edits the built fonts in place, glyph by glyph,
with boolean cuts and joins on the art agent's own outlines (the hand-painted
edges stay), then re-hints with ttfautohint like the originals.

    python tools/typeface/refine_numerals.py assets/fonts/ARDSignwriter-{Regular,Bold,Display}.ttf

What it changes, in font units (1000 per em), each cut measured from its own glyphs:
  I       slab serifs top and bottom, ends cut on the brush's slant, so I is not l, 1 or a bar
  0 / O   the letter O a quarter wider (Q's tail already marks it): the zero's oval against a round
  6 / 9   the hook cut back, so the opening is clear of the bowl (not an 8)
  8       the waist pinched, so the two bowls show (not a 0, 6 or 9)
  ( ) [ ] { } |   scaled to sit inside the line (ascent 760, descent 200):
          they rose to 789 and were cut off in a tight row
Run once: the font's version becomes 0.2, and a font already at 0.2 is skipped.
The art agent's SVG sources are not kept in any repository, so the built fonts are
the source; this script is the record of what was done to them.
Needs fontTools, skia-pathops and ttfautohint-py.
"""

import sys
import tempfile
from pathlib import Path

import pathops
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

DONE = "Version 0.2"
ASC, DESC = 760, -200


def outline(font, name) -> pathops.Path:
    p = pathops.Path()
    font.getGlyphSet()[name].draw(p.getPen())
    return p


def rect(x0, y0, x1, y1) -> pathops.Path:
    return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def poly(pts) -> pathops.Path:
    p = pathops.Path()
    pen = p.getPen()
    pen.moveTo(pts[0])
    for q in pts[1:]:
        pen.lineTo(q)
    pen.closePath()
    return p


def op(a, b, kind) -> pathops.Path:
    return pathops.op(a, b, kind, fix_winding=True, keep_starting_points=False)


def moved(p: pathops.Path, dx=0.0, dy=0.0, sx=1.0, sy=1.0, cx=0.0, cy=0.0) -> pathops.Path:
    """p scaled about (cx, cy), then moved."""
    out = pathops.Path()
    pen = out.getPen()
    t = lambda pt: (cx + (pt[0] - cx) * sx + dx, cy + (pt[1] - cy) * sy + dy)
    for verb, pts in p:
        pts = [t(q) for q in pts]
        if verb == pathops.PathVerb.MOVE:
            pen.moveTo(*pts)
        elif verb == pathops.PathVerb.LINE:
            pen.lineTo(*pts)
        elif verb == pathops.PathVerb.QUAD:
            pen.qCurveTo(*pts)
        elif verb == pathops.PathVerb.CUBIC:
            pen.curveTo(*pts)
        elif verb == pathops.PathVerb.CLOSE:
            pen.closePath()
    return out


def resized(p: pathops.Path, cx: float, d: float) -> pathops.Path:
    """p made d units wider (d < 0: narrower) by moving the halves either side
    of x = cx apart (or together); widening bridges the gap with the cut's own
    cross-section, so bars and bowls stay their painted weight."""
    b = p.bounds
    big = 5000
    left = op(p, rect(-big, -big, cx, big), pathops.PathOp.INTERSECTION)
    right = op(p, rect(cx, -big, big, big), pathops.PathOp.INTERSECTION)
    out = op(moved(left, dx=-d / 2), moved(right, dx=d / 2), pathops.PathOp.UNION)
    if d > 0:
        strip = op(p, rect(cx - 1, b[1] - 10, cx + 1, b[3] + 10), pathops.PathOp.INTERSECTION)
        out = op(out, moved(strip, sx=(d + 4) / 2.0, cx=cx), pathops.PathOp.UNION)
    return out


def runs(p: pathops.Path, y: float) -> list:
    """The ink runs across row y, left to right, as (x0, x1)."""
    b = p.bounds
    cut = op(p, rect(b[0] - 10, y - 0.5, b[2] + 10, y + 0.5), pathops.PathOp.INTERSECTION)
    out, xs = [], []
    for verb, pts in cut:
        if verb == pathops.PathVerb.MOVE and xs:
            out.append((min(xs), max(xs)))
            xs = []
        xs += [q[0] for q in pts]
    if xs:
        out.append((min(xs), max(xs)))
    return sorted(out)


def stem(p: pathops.Path, y: float) -> float:
    """The painted stroke width: the narrowest ink run across row y."""
    return min(r[1] - r[0] for r in runs(p, y))


def refine(font: TTFont) -> list:
    cm = font.getBestCmap()
    hmtx = font["hmtx"]
    new = {}
    widths = {}
    said = []

    def g(ch):
        return cm[ord(ch)]

    # I: slab serifs, as wide as the l's tail reaches, as deep as the 1's foot.
    i = outline(font, g("I"))
    ib = i.bounds
    sw = ib[2] - ib[0]
    serif = round(sw * 0.62)
    depth = round(sw * 0.62)
    # Each slab's outer ends are cut on the brush's slant, like the 1's foot.
    sl = round(depth * 0.45)
    x0, x1, top = ib[0] - serif, ib[2] + serif, ib[3]
    slabs = op(poly([(x0 + sl, 0), (x1, 0), (x1 - sl, depth), (x0, depth)]),
               poly([(x0, top - depth), (x1 - sl, top - depth), (x1, top), (x0 + sl, top)]), pathops.PathOp.UNION)
    new[g("I")] = moved(op(i, slabs, pathops.PathOp.UNION), dx=serif)
    widths[g("I")] = hmtx[g("I")][0] + 2 * serif
    said.append("I: serifs %d wide, %d deep" % (serif, depth))

    # O wider by a quarter of the zero's ink: a round against the zero's oval.
    # (Narrowing the zero instead closed its counter to a slit.)
    zb = outline(font, g("0")).bounds
    do = round((zb[2] - zb[0]) * 0.25)
    o = pathops.simplify(outline(font, g("O")), fix_winding=True, keep_starting_points=False)
    ob = o.bounds
    wide = moved(resized(o, (ob[0] + ob[2]) / 2, do), dx=do / 2)
    new[g("O")] = wide
    widths[g("O")] = hmtx[g("O")][0] + do
    # The Q keeps its drawing: its tail already sets it apart, and its bowl
    # overlaps the tail, so cutting it apart filled the counter.
    said.append("O %+d" % do)

    # 6: the hook's end cut back on a slant. Its end sits a stroke above the
    # bowl; after the cut it sits two and a half strokes above.
    six = outline(font, g("6"))
    sb = six.bounds
    h = sb[3]
    st = sw  # the I is one painted stroke
    cx = (sb[0] + sb[2]) / 2
    lo = h * 0.625 + 6
    new[g("6")] = op(six, poly([(cx, lo), (sb[2] + 20, lo), (sb[2] + 20, h * 0.83), (cx, h * 0.79)]),
                     pathops.PathOp.DIFFERENCE)
    # 9: the same cut, turned half round.
    nine = outline(font, g("9"))
    nb = nine.bounds
    hi = nb[3] - (h * 0.625 + 6)
    new[g("9")] = op(nine, poly([(cx, hi), (nb[0] - 20, hi), (nb[0] - 20, nb[3] - h * 0.83), (cx, nb[3] - h * 0.79)]),
                     pathops.PathOp.DIFFERENCE)
    said.append("6/9: hooks cut back to %.0f%% of the height (stroke %.0f)" % (83, st))

    # 8: the waist pinched from both sides, a third of a stroke deep.
    e = outline(font, g("8"))
    eb = e.bounds
    # The waist is where the outer edge comes in furthest, between 40% and 65% up.
    best = None
    for k in range(40, 66):
        y = eb[3] * k / 100.0
        r = runs(e, y)
        if not r:
            continue
        w = r[-1][1] - r[0][0]
        if best is None or w < best[1]:
            best = (y, w)
    wy = best[0]
    nd = round(st * 0.45)
    span = round(st * 0.9)
    notch = op(poly([(eb[0] - 30, wy - span), (eb[0] + nd, wy), (eb[0] - 30, wy + span)]),
               poly([(eb[2] + 30, wy - span), (eb[2] - nd, wy), (eb[2] + 30, wy + span)]), pathops.PathOp.UNION)
    new[g("8")] = op(e, notch, pathops.PathOp.DIFFERENCE)
    said.append("8: waist at %.0f pinched %d each side" % (wy, nd))

    # Brackets and the bar: inside the line box, centred where they were.
    for ch in "()[]{}|":
        n = g(ch)
        p = outline(font, n)
        b = p.bounds
        mid = (b[1] + b[3]) / 2
        f = min(1.0, (ASC - 10 - mid) / (b[3] - mid), (mid - (DESC + 10)) / (mid - b[1]))
        if f < 1.0:
            new[n] = moved(p, sy=f, cy=mid)
    said.append("brackets scaled to %d..%d" % (DESC + 10, ASC - 10))

    glyf = font["glyf"]
    for n, p in new.items():
        p = pathops.simplify(p, fix_winding=True, keep_starting_points=False)
        tt = TTGlyphPen(None)
        p.draw(Cu2QuPen(tt, max_err=1.0, reverse_direction=True))
        gl = tt.glyph()
        gl.recalcBounds(glyf)
        glyf[n] = gl
        hmtx[n] = (widths.get(n, hmtx[n][0]), gl.xMin if gl.numberOfContours else 0)
    return said


def main(paths) -> int:
    import ttfautohint
    for path in map(Path, paths):
        version = TTFont(str(path))["name"].getDebugName(5) or ""
        if version.startswith(DONE):
            print("%s: already refined (%s), skipped" % (path.name, version))
            continue
        tmp = Path(tempfile.mkdtemp())
        bare = tmp / "bare.ttf"
        ttfautohint.ttfautohint(in_file=str(path), out_file=str(bare), dehint=True)
        font = TTFont(str(bare))
        said = refine(font)
        for rec in font["name"].names:
            if rec.nameID == 5:
                rec.string = DONE
            elif rec.nameID == 3:
                rec.string = str(rec.toUnicode()).replace("0.1", "0.2")
        font["head"].fontRevision = 0.2
        raw = tmp / "raw.ttf"
        font.save(str(raw))
        font.close()
        ttfautohint.ttfautohint(in_file=str(raw), out_file=str(path))
        print("%s: %s" % (path.name, "; ".join(said)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
