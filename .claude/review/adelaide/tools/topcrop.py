"""Crop the straight-down overlay (left half of topdown.py output) to a world box with a labelled metre grid.
topcrop.py ovl.png out.png x0 y0 x1 y1 [k] ; TOP as in render.py"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
cx, cy, sz = map(float, os.environ.get('TOP', '0,-10,400').split(','))
im = Image.open(sys.argv[1]).convert('RGB'); n = im.size[1]; im = im.crop((0, 0, n, n))
x0, y0, x1, y1 = map(float, sys.argv[3:7]); k = float(sys.argv[7]) if len(sys.argv) > 7 else 3
s = n / sz
def px(x, y): return ((x - (cx - sz / 2)) * s, ((cy + sz / 2) - y) * s)
a = px(x0, y1); b = px(x1, y0)
c = im.crop((int(a[0]), int(a[1]), int(b[0]), int(b[1]))).resize((int((b[0] - a[0]) * k), int((b[1] - a[1]) * k)), Image.NEAREST)
d = ImageDraw.Draw(c)
for x in range(int(np.ceil(x0)), int(x1) + 1):
    X = (px(x, 0)[0] - int(a[0])) * k; d.line([(X, 0), (X, c.size[1])], fill=(255, 0, 0) if x % 10 == 0 else (120, 60, 60), width=1)
    if x % 10 == 0: d.text((X + 2, 2), str(x), fill=(255, 255, 0))
for y in range(int(np.ceil(y0)), int(y1) + 1):
    Y = (px(0, y)[1] - int(a[1])) * k; d.line([(0, Y), (c.size[0], Y)], fill=(255, 0, 0) if y % 10 == 0 else (120, 60, 60), width=1)
    if y % 10 == 0: d.text((2, Y + 2), str(y), fill=(255, 255, 0))
c.save(sys.argv[2])
