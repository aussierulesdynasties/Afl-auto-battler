"""The AFL trainer's vest back print, as a mask for the kit shader (row 202).

    python3 make_vest_print.py OUT.png

Measured from 2025 broadcasts (Richmond, round 1): "TRAINER" in plain bold condensed sans-serif
capitals 10.5 x 31 cm, and a one-digit number 14 x 7 cm in the same style. The top half of the
mask is the word, filling its box; the bottom half the digits 0-9, one per tenth, each filling
its box (oval3d_player.gdshader stretches each box over its measured place on the vest). White
on black in every channel. Barlow Condensed Bold (SIL Open Font License, assets/fonts).
"""
import sys

from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
FONT = "assets/fonts/BarlowCondensed-Bold.ttf"
W, H = 1024, 512
PAD = 6   # px of clear edge round each box, so mipmaps never bleed one into the next


def fill(img, box, text, keep=False):
    """text drawn to fill box (x0, y0, x1, y1) edge to edge, ink bounds stretched to it; with keep,
    its full height and its own width (the "4" the box was measured on fills it), centred."""
    f = ImageFont.truetype(FONT, 400)
    l, t, r, b = f.getbbox(text)
    g = Image.new("L", (r - l + 4, b - t + 4), 0)
    ImageDraw.Draw(g).text((2 - l, 2 - t), text, font=f, fill=255)
    g = g.crop(g.getbbox())
    x0, y0, x1, y1 = box
    w, h = x1 - x0 - 2 * PAD, y1 - y0 - 2 * PAD
    if keep:
        w = min(w, round(g.width * h / g.height * keep))
    g = g.resize((w, h), Image.LANCZOS)
    img.paste(g, (x0 + (x1 - x0 - w) // 2, y0 + PAD))


img = Image.new("L", (W, H), 0)
fill(img, (0, 0, W, H // 2), "TRAINER")
cw = W // 10
# The digits as wide as the measured "4" makes them (7 x 14 cm, against the font's own shape).
f4 = ImageFont.truetype(FONT, 400).getbbox("4")
four = (cw - 2 * PAD) / ((H // 2 - 2 * PAD) * (f4[2] - f4[0]) / (f4[3] - f4[1]))
for d in range(10):
    fill(img, (d * cw, H // 2, (d + 1) * cw, H), str(d), keep=four)
img.convert("RGB").save(OUT)
print("WROTE", OUT)
