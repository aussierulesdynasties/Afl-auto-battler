# Unwrap one view's photo (and render) of the bowl's rake onto bearing (x, PX px/deg) by height up the section
# (y, top = back of the top tier): radial aisles become vertical lines and walkway bands horizontal ones.
# The section runs from the fence to the back of the top tier along the model's profile, sampled by height z.
# python work/tierstrip.py view b0 b1 out.png [px/deg]
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE); import earthcam
exec(open(os.path.join(HERE, 'seatgrid.py')).read().split("v, b0, b1, out")[0].split("import earthcam")[1])
v, b0, b1, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
PX = float(sys.argv[5]) if len(sys.argv) > 5 else 20
if b1 < b0: b1 += 360
x0, y0, a, d, h, t = C[v]; c = earthcam.cam(h, t, d, tz=a - 13, tx=x0, ty=y0)
ZS = np.arange(31.0, -4.2, -0.1)  # rows: z from the top down, 0.1 m (10 px per metre of height)
def rz(b, z):  # radius on the model's seating surface at height z (the tier faces, not the walls)
    p = prof(b); seg = [(p[0], p[1]), (p[3], p[4]), (p[6], p[7])]
    for (ra, za), (rb, zb) in seg:
        if za <= z <= zb: return ra + (rb - ra) * (z - za) / (zb - za)
    for (ra, za), (rb, zb) in ((p[1], p[2]), (p[4], p[5])):  # walkway walls: vertical
        if za <= z <= zb: return ra
    return np.nan
bs = b0 + np.arange(int((b1 - b0) * PX)) / PX
U = np.full((len(ZS), len(bs)), np.nan); V = np.full_like(U, np.nan)
for j, b in enumerate(bs):
    for i, z in enumerate(ZS):
        r = rz(b, z)
        if np.isnan(r): continue
        U[i, j], V[i, j] = earthcam.proj(c, (*pol(b, r), z))
ims = []
for src in ('ge', 'rr'):
    I = np.asarray(Image.open(os.path.join(SP, src, v + '.png')).convert('RGB'))
    ok = ~np.isnan(U) & (U >= 0) & (U < 1919) & (V >= 0) & (V < 1079)
    o = np.zeros((*U.shape, 3), np.uint8); o[ok] = I[V[ok].astype(int), U[ok].astype(int)]
    im = Image.fromarray(o); dr = ImageDraw.Draw(im)
    for bb in range(math.ceil(b0), int(b1) + 1):
        x = (bb - b0) * PX; dr.line([(x, 0), (x, 6)], fill=(255, 0, 255)); dr.text((x + 1, 6), str(bb % 360), fill=(255, 0, 255)) if bb % 5 == 0 else None
    for z in range(0, 31, 5):
        y = (31 - z) * 10; dr.line([(0, y), (5, y)], fill=(0, 255, 255)); dr.text((6, y - 5), str(z), fill=(0, 255, 255))
    ims.append(im)
w, hh = ims[0].size; o = Image.new('RGB', (w, hh * 2 + 4)); o.paste(ims[0], (0, 0)); o.paste(ims[1], (0, hh + 4)); o.save(out); print(out, o.size)
