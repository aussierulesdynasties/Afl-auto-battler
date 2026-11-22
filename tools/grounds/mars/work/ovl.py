# Overlay a model render (render/<v>.png, transparent film) on the Google Earth view ge/<v>.png.
# python work/ovl.py v [alpha] [x0,y0,x1,y1] -> render/ov_<v>.jpg (model at alpha over GE, model silhouette outlined in magenta)
import sys, numpy as np
from PIL import Image, ImageFilter
v = sys.argv[1]; al = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
g = Image.open(f'ge/{v}.png').convert('RGB'); r = Image.open(f'render/{v}.png').convert('RGBA')
A = np.asarray(r, float); G = np.asarray(g, float); m = A[:, :, 3:4] / 255
o = G * (1 - al * m) + A[:, :, :3] * al * m
sil = Image.fromarray((m[:, :, 0] > 0.5).astype(np.uint8) * 255); e = np.asarray(sil.filter(ImageFilter.FIND_EDGES)) > 0
o[e] = (255, 0, 255)
im = Image.fromarray(o.clip(0, 255).astype(np.uint8))
if len(sys.argv) > 3: im = im.crop(tuple(int(t) for t in sys.argv[3].split(',')))
rr = Image.fromarray((A[:, :, :3] * m + 255 * (1 - m)).astype(np.uint8))
if len(sys.argv) > 3: rr = rr.crop(tuple(int(t) for t in sys.argv[3].split(',')))
im.save(f'render/ov_{v}.jpg', quality=88); rr.save(f'render/m_{v}.jpg', quality=88); print('ok', v)
