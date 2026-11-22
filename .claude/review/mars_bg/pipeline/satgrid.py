"""satellite crop with 50 m grid in scene metres. satgrid.py g x0 y0 x1 y1 out.png"""
import sys, json
from PIL import Image, ImageDraw
g = sys.argv[1]; x0, y0, x1, y1 = map(float, sys.argv[2:6])
m = json.load(open(f'data/{g}/sat.json')); R, S = m['half_m'], m['m_per_px']
im = Image.open(f'data/{g}/sat.png').convert('RGB')
P = lambda x, y: ((x + R) / S, (R - y) / S)
a = P(x0, y1); b = P(x1, y0); c = im.crop((int(a[0]), int(a[1]), int(b[0]), int(b[1])))
sc = 1400 / max(c.size); c = c.resize((int(c.width * sc), int(c.height * sc))); d = ImageDraw.Draw(c)
step = 50 if x1 - x0 <= 800 else 100
for x in range(int(x0 // step * step), int(x1) + 1, step):
    u = (x - x0) / S * sc; d.line([(u, 0), (u, c.height)], fill=(255, 255, 0) if x % 500 else (255, 0, 0), width=1); d.text((u + 2, 2), str(x), fill=(255, 255, 0))
for y in range(int(y0 // step * step), int(y1) + 1, step):
    v = (y1 - y) / S * sc; d.line([(0, v), (c.width, v)], fill=(255, 255, 0) if y % 500 else (255, 0, 0), width=1); d.text((2, v + 2), str(y), fill=(255, 255, 0))
c.save(sys.argv[6])
