"""2000-px working copy + pixel grid (lines every 50, labels every 100)."""
import sys
from PIL import Image, ImageDraw, ImageFont
k = sys.argv[1]
im = Image.open("ref/%s.jpg" % k).convert("RGB")
W = 2000; H = round(im.height * W / im.width)
im = im.resize((W, H), Image.LANCZOS); im.save("grid/%s_2000.png" % k)
g = im.copy(); d = ImageDraw.Draw(g, "RGBA")
f = ImageFont.truetype("arial.ttf", 18)
for x in range(0, W, 50):
    d.line([(x, 0), (x, H)], fill=(255, 255, 0, 150 if x % 100 == 0 else 60), width=1)
    if x % 100 == 0:
        for y0 in (2, H // 2, H - 22):
            d.text((x + 2, y0), str(x), fill=(255, 255, 0, 255), font=f, stroke_width=2, stroke_fill=(0, 0, 0))
for y in range(0, H, 50):
    d.line([(0, y), (W, y)], fill=(0, 255, 255, 150 if y % 100 == 0 else 60), width=1)
    if y % 100 == 0:
        for x0 in (2, W // 2 + 4, W - 50):
            d.text((x0, y + 2), str(y), fill=(0, 255, 255, 255), font=f, stroke_width=2, stroke_fill=(0, 0, 0))
g.save("grid/%s_grid.jpg" % k, quality=90)
print(k, W, H)
