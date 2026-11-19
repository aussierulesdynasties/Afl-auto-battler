# top-down overlay: model render (alpha) over the satellite crop of the same box, plus an edge-only version.
import sys; sys.path.insert(0, 'work'); import satm
from PIL import Image, ImageFilter, ImageChops, ImageDraw
render, x0, y0, x1, y1, ppm, out = sys.argv[1], *map(float, sys.argv[2:7]), sys.argv[7]
sat = satm.crop(x0, y0, x1, y1, 19, ppm)
r = Image.open(render).convert('RGBA').resize(sat.size)
a = r.split()[3]
edge = a.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 40 else 0)
# model roof edges from colour changes too
g = r.convert('L').filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 60 else 0)
g = ImageChops.multiply(g, a.point(lambda v: 255 if v > 128 else 0))
e = ImageChops.lighter(edge, g)
o = sat.copy(); mag = Image.new('RGB', sat.size, (255, 0, 255)); o.paste(mag, (0, 0), e)
# 5 m grid ticks with labels
d = ImageDraw.Draw(o)
import math
for gx in range(int(math.ceil(x0 / 5) * 5), int(x1) + 1, 5):
    X = (gx - x0) * ppm; d.line([(X, 0), (X, 8)], fill=(255, 255, 0)); d.text((X + 2, 9), str(gx), fill=(255, 255, 0))
for gy in range(int(math.ceil(y0 / 5) * 5), int(y1) + 1, 5):
    Y = (y1 - gy) * ppm; d.line([(0, Y), (8, Y)], fill=(255, 255, 0)); d.text((10, Y - 5), str(gy), fill=(255, 255, 0))
blend = Image.alpha_composite(sat.convert('RGBA'), Image.merge('RGBA', (*r.split()[:3], a.point(lambda v: v // 2)))).convert('RGB')
W = Image.new('RGB', (sat.width, sat.height * 2)); W.paste(o, (0, 0)); W.paste(blend, (0, sat.height)); W.save(out)
