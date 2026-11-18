"""Denser palm frond (one frond along v): broad leaflets so the crown reads at game distance."""
import math, random
from PIL import Image, ImageDraw
n = 1024; r = random.Random(111)
im = Image.new("RGBA", (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im); cx = n / 2
for y in range(0, n - 4, 6):
    t = y / n; half = n * 0.48 * math.sin(math.pi * (0.06 + 0.88 * t))
    g = r.randint(100, 140)
    for s in (-1, 1):
        ex = cx + s * half; ey = y + half * 0.45
        d.line([(cx, y), (ex, ey)], fill=(52, g, 50, 255), width=9)
        d.line([(cx, y + 3), (ex, ey + 3)], fill=(38, int(g * 0.78), 40, 255), width=3)
d.line([(cx, 0), (cx, n)], fill=(150, 140, 80, 255), width=10)
im.save("tex/palm_frond.png")
