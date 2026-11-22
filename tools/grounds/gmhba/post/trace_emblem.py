"""The Geelong Cats emblem on the Premiership Stand's west wall, traced from Google Earth's close view of that
wall (2026-11-22). Writes tex_src_cats_emblem.png beside this file, which mktex.py puts on the wall.

The Google Earth screenshot is not kept in the repo and no pixel of it is shipped: only the traced flat colours
are. To redo it, shoot

    https://earth.google.com/web/@-38.1581649,144.3532950,31.0a,220.0d,6y,90.0h,72.0t,0r

at 1280x720 with tools/grounds/gmhba/qa/ge_shoot.js, then

    python3 tools/grounds/gmhba/post/trace_emblem.py <that screenshot>.png

How: each pixel of the emblem's crop goes to the nearest of four colours (white, navy, pale blue, the wall), the
classes are mirrored about the shield's axis (the emblem is symmetric; the camera is a few degrees off square),
scaled up 4x with the camera's 0.951 vertical squash taken out, smoothed and re-classified. The shield's outline
is the smoothed edge where the wall starts. Specks (blur at class edges) are dropped. The lettering is too small
in Google Earth to trace, so GEELONG and CATS are set in type at the traced size and arch: GEELONG in white
across the navy band at the shield's top, CATS in heavy navy capitals under the point. Only flat colours are
written: navy, white and the pale blue of the hoops' outer ends.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

CROP = (470, 170, 870, 600)          # the emblem in the 1280x720 screenshot (left, top, right, bottom)
CLASSES = np.array([[203, 220, 229], [18, 30, 47], [120, 146, 158], [89, 113, 129]], float)  # white navy pale wall
AXIS = 203                           # the shield's mirror axis in the crop (px)
S = 4                                # upscale
SQUASH = 0.951                       # the camera's vertical foreshortening
NAVY, WHITE, PALE = (28, 44, 86), (240, 242, 245), (150, 175, 205)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
HERE = os.path.dirname(os.path.abspath(__file__))


def _filt(mask, f):
    return np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(f)) > 127


def _open_close(mask, k):
    """Drop specks and fill pinholes narrower than k px."""
    m = _filt(_filt(mask, ImageFilter.MinFilter(k)), ImageFilter.MaxFilter(k))
    return _filt(_filt(m, ImageFilter.MaxFilter(k)), ImageFilter.MinFilter(k))


def _round(mask, r):
    """Round erosion (r < 0) or dilation (r > 0) by about |r| px."""
    b = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(abs(r) / 1.6)), float)
    return b > (250 if r < 0 else 5) if abs(r) > 0 else mask


def _drop_small(mask, area):
    """Keep only the connected parts of mask of at least `area` px (labelled on a quarter-size grid)."""
    q = 4
    small = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).resize(
        (mask.shape[1] // q, mask.shape[0] // q), Image.BOX)) > 127
    h, w = small.shape
    seen = np.zeros_like(small)
    keep_s = np.zeros_like(small)
    for y0, x0 in zip(*np.nonzero(small)):
        if seen[y0, x0]:
            continue
        part, stack = [], [(y0, x0)]
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            part.append((y, x))
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < h and 0 <= xx < w and small[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True
                    stack.append((yy, xx))
        if len(part) * q * q >= area:
            ys, xs = zip(*part)
            keep_s[list(ys), list(xs)] = True
    big = np.asarray(Image.fromarray((keep_s * 255).astype(np.uint8)).resize((mask.shape[1], mask.shape[0]),
                                                                             Image.NEAREST)) > 127
    return mask & _round(big, 6)


def classes(shot):
    a = np.asarray(Image.open(shot).convert("RGB"), float)[CROP[1]:CROP[3], CROP[0]:CROP[2]]
    return ((a[:, :, None] - CLASSES[None, None]) ** 2).sum(3).argmin(2)


def trace(lab):
    H0, W0 = lab.shape
    # Mirror the white / navy / pale-or-wall memberships about the axis and average.
    oh = np.stack([(lab == 0), (lab == 1), (lab >= 2)], -1).astype(float)
    xs = np.arange(W0)
    mx = 2 * AXIS - xs
    ok = (mx >= 0) & (mx < W0)
    m = np.zeros_like(oh)
    m[:, ok] = oh[:, mx[ok]]
    sym = (oh + m) / 2
    W, H = W0 * S, int(H0 * S / SQUASH)
    P = np.stack([np.asarray(Image.fromarray((sym[..., k] * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
                             .filter(ImageFilter.GaussianBlur(6)), float) for k in range(3)], -1)
    L = P.argmax(-1)
    ax = AXIS * S
    # The shield's outline: per row, its half width is how far in from the right the wall/pale class reaches;
    # smoothed, closed with a rounded point, mirrored.
    hw = np.zeros(H)
    for y in range(H):
        x = min(W - 1, ax + 720)
        while x > ax and L[y, x] == 2:
            x -= 1
        hw[y] = x - ax
    ys = np.arange(H)
    good = (ys >= 80) & (ys <= 1120) & (hw > 0)
    k = np.ones(21) / 21
    h2 = np.convolve(np.where(good, hw, 0), k, "same") / np.maximum(np.convolve(good.astype(float), k, "same"), 1e-6)
    pts = [(ax + h2[y], y) for y in range(80, 1121, 4)]
    for t in np.linspace(0, 1, 12)[1:]:
        pts.append((ax + h2[1120] * (1 - t) ** 1.3, 1120 + 130 * t))
    poly = pts + [(2 * ax - x, y) for x, y in reversed(pts)]
    mimg = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mimg).polygon(poly, fill=255)
    mk = np.asarray(mimg).copy()
    for x in range(int(ax - h2[80]), int(ax + h2[80])):      # the arched top: first non-wall row per column
        nz = np.nonzero(L[:200, x] != 2)[0]
        if len(nz):
            mk[nz[0]:80, x] = 255
    mask = np.asarray(Image.fromarray(mk).filter(ImageFilter.MedianFilter(9))) > 127
    # White and navy, specks dropped. Then pale: in Google Earth every broad white shape (the hoops' ends, the
    # whisker sweeps, the blaze) is pale blue inside a white edge about 16 px (4x) wide, while the lines and the
    # eyes stay white. The sun washes some of that pale to white in the screenshot, so the pale is drawn from
    # the white shapes' width rather than from the traced pale.
    white = _open_close(P[..., 1] < np.maximum(P[..., 0], P[..., 2]), 9)
    core = _round(white, -28)
    pale = _drop_small(_round(white, -14) & _round(core, 30), 9000)
    L = np.where(white, 0, 1)
    L[pale] = 2
    # The rim: everything within 70 px of the outline keeps its traced white/navy; inside that, the band at the top
    # (the shield's top down to GEELONG's foot) is plain navy for the lettering.
    inner = _filt(mask, ImageFilter.MinFilter(141))
    top = np.zeros_like(mask)
    for x in range(W):
        col = np.nonzero(inner[:, x])[0]
        if len(col):
            top[col[0]:335, x] = True
    L[top & inner] = 1
    # Pale specks left in the navy (smaller than a hoop's end) go navy.
    lone = (L == 2) & ~_filt(_filt(L == 2, ImageFilter.MinFilter(41)), ImageFilter.MaxFilter(41))
    L[lone] = 1
    pal = np.array([WHITE, NAVY, PALE], np.uint8)
    img = Image.fromarray(np.dstack([pal[L], (mask * 255).astype(np.uint8)]), "RGBA")
    # GEELONG, arched with the band.
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, 172)
    word = "GEELONG"
    ws = [d.textlength(c, font=font) for c in word]
    gap = 8
    total = sum(ws) + gap * (len(word) - 1)
    x = ax - total / 2
    for c, w in zip(word, ws):
        cx = x + w / 2
        t = (cx - ax) / (total / 2)
        y = 245 + 44 * t * t
        ang = -math.degrees(math.atan(2 * 44 * t / (total / 2)))
        g = Image.new("RGBA", (int(w * 1.8), 200), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((g.width / 2, 100), c, font=font, fill=WHITE + (255,), anchor="mm")
        g = g.rotate(ang, resample=Image.BICUBIC)
        img.alpha_composite(g, (int(cx - g.width / 2), int(y - 100)))
        x += w + gap
    # CATS under the point: Google Earth has it 0.64 of the shield's width, 0.3 of its height, condensed.
    big = ImageFont.truetype(FONT, 400)
    t = Image.new("RGBA", (1800, 600), (0, 0, 0, 0))
    ImageDraw.Draw(t).text((900, 300), "CATS", font=big, fill=NAVY + (255,), anchor="mm", stroke_width=14,
                           stroke_fill=NAVY + (255,))
    t = t.crop(t.getbbox())
    sw, sh = int(2 * 660 * 0.64), 380
    t = t.resize((sw, sh), Image.LANCZOS)
    out = Image.new("RGBA", (W, 1250 + 40 + sh + 10), (0, 0, 0, 0))
    out.alpha_composite(img.crop((0, 0, W, min(H, 1250))), (0, 0))
    out.alpha_composite(t, (ax - sw // 2, 1250 + 40))
    return out.crop(out.getbbox())


if __name__ == "__main__":
    em = trace(classes(sys.argv[1]))
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "tex_src_cats_emblem.png")
    em.save(dst)
    print(dst, em.size)
