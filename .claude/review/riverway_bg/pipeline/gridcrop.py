"""Satellite crop with a metre grid (scene frame). gridcrop.py sat.png half_m m_per_px x0 y0 x1 y1 out.png [scale]"""
import sys
from PIL import Image, ImageDraw
S = Image.open(sys.argv[1]).convert('RGB'); R, mpp = float(sys.argv[2]), float(sys.argv[3])
x0, y0, x1, y1 = map(float, sys.argv[4:8]); k = float(sys.argv[9]) if len(sys.argv) > 9 else 2
def px(x, y): return ((x + R) / mpp, (R - y) / mpp)
a = px(x0, y1); b = px(x1, y0)
C = S.crop((int(a[0]), int(a[1]), int(b[0]), int(b[1]))); C = C.resize((int(C.width * k), int(C.height * k)))
d = ImageDraw.Draw(C)
for x in range(int(x0 // 10 * 10), int(x1) + 1, 10):
    u = (px(x, 0)[0] - int(a[0])) * k; d.line([(u, 0), (u, C.height)], fill=(255, 255, 0) if x % 50 == 0 else (255, 80, 80), width=1)
    if x % 50 == 0: d.text((u + 2, 2), str(x), fill=(255, 255, 0))
for y in range(int(y0 // 10 * 10), int(y1) + 1, 10):
    v = (px(0, y)[1] - int(a[1])) * k; d.line([(0, v), (C.width, v)], fill=(255, 255, 0) if y % 50 == 0 else (255, 80, 80), width=1)
    if y % 50 == 0: d.text((2, v + 2), str(y), fill=(255, 255, 0))
C.save(sys.argv[8])
