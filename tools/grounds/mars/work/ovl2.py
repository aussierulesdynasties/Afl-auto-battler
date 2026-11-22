# Like ovl.py but draws every internal model edge (roof lips, tier breaks) in magenta over the GE view, no tint.
# python work/ovl2.py v x0,y0,x1,y1 scale -> render/e_<v>.jpg
import sys, numpy as np
from PIL import Image, ImageFilter
v = sys.argv[1]; box = tuple(int(t) for t in sys.argv[2].split(',')); sc = float(sys.argv[3]) if len(sys.argv) > 3 else 2
g = np.asarray(Image.open(f'ge/{v}.png').convert('RGB'), float).copy(); r = Image.open(f'render/{v}.png').convert('RGBA')
L = r.convert('L').filter(ImageFilter.GaussianBlur(0.6)); e = np.asarray(L.filter(ImageFilter.FIND_EDGES), float) > 28
a = np.asarray(r)[:, :, 3] > 128; e &= a
g[e] = (255, 0, 255)
im = Image.fromarray(g.astype(np.uint8)).crop(box); im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
im.save(f'render/e_{v}.jpg', quality=90); print('ok')
