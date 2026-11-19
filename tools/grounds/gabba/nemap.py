import json, math, sys
from PIL import Image, ImageDraw
d = json.load(open('model_in6.json')); cx, cy = d['Cc']
sat = sys.argv[1] if len(sys.argv) > 1 else 'sat/sat_model11135.png'
im = Image.open(sat).convert('RGB'); x0, x1, y0, y1 = 30, 170, -10, 120; S = 6
def px(p): return ((p[0] + 200) / 0.25, (200 - p[1]) / 0.25)
cr = im.crop((int(px((x0, y1))[0]), int(px((x0, y1))[1]), int(px((x1, y0))[0]), int(px((x1, y0))[1])))
cr = cr.resize((cr.width * S // 4, cr.height * S // 4)); dr = ImageDraw.Draw(cr)
def q(p): a = px(p); return ((a[0] - px((x0, y1))[0]) * S / 4, (a[1] - px((x0, y1))[1]) * S / 4)
def poly(pts, c, w=2):
    dr.line([q(p) for p in pts] + [q(pts[0])], fill=c, width=w)
for key, c in (('RF', (255, 255, 0)), ('RO', (255, 128, 0))):
    A, R = d[key]; pts = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a, r in zip(A, R)]
    dr.line([q(p) for p in pts], fill=c, width=2)
poly(d['parts']['483353591'], (0, 255, 255))
ex = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}
for name, (pts, c) in ex.items(): poly(pts, tuple(c))
for gx in range(40, 171, 10):
    dr.line([q((gx, y0)), q((gx, y1))], fill=(80, 80, 80), width=1); dr.text(q((gx, y0 + 2)), str(gx), fill=(255, 255, 255))
for gy in range(0, 121, 10):
    dr.line([q((x0, gy)), q((x1, gy))], fill=(80, 80, 80), width=1); dr.text(q((x0 + 1, gy)), str(gy), fill=(255, 255, 255))
cr.save(sys.argv[3] if len(sys.argv) > 3 else 'nemap.png'); print(cr.size)
