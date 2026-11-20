# Gridded satellite crop: python work/satgrid.py x0 x1 y0 y1 pxpm out  (5 m grid, labels every 10 m)
import sys, os
from PIL import Image, ImageDraw
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
x0, x1, y0, y1, k = map(float, sys.argv[1:6]); out = sys.argv[6]
S = Image.open(os.path.join(SP, 'sat', 'esri_025.png')).convert('RGB')
c = S.crop((int((x0 + 260) * 4), int((260 - y1) * 4), int((x1 + 260) * 4), int((260 - y0) * 4)))
c = c.resize((int((x1 - x0) * k), int((y1 - y0) * k)), Image.LANCZOS); d = ImageDraw.Draw(c)
for x in range(int(x0) // 5 * 5, int(x1) + 1, 5):
    X = (x - x0) * k; d.line([(X, 0), (X, c.height)], fill=(255, 0, 255) if x % 10 == 0 else (120, 0, 120))
    if x % 10 == 0: d.text((X + 2, 2), str(x), fill=(255, 255, 0))
for y in range(int(y0) // 5 * 5, int(y1) + 1, 5):
    Y = (y1 - y) * k; d.line([(0, Y), (c.width, Y)], fill=(0, 255, 255) if y % 10 == 0 else (0, 110, 110))
    if y % 10 == 0: d.text((2, Y + 2), str(y), fill=(255, 255, 0))
c.save(out); print(out, c.size)
