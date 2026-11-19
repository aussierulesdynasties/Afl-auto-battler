# python work/cmp.py v x0,y0,x1,y1 scale out.jpg : GE crop (top) above outline overlay crop (bottom), from full-frame images
import sys, numpy as np
from PIL import Image, ImageFilter
v = sys.argv[1]; box = tuple(int(t) for t in sys.argv[2].split(',')); sc = float(sys.argv[3]); out = sys.argv[4]
g = Image.open(f'ge/{v}.png').convert('RGB'); r = Image.open(f'render/{v}.png').convert('RGBA')
A = np.asarray(r, float); G = np.asarray(g, float); m = A[:, :, 3] / 255
o = G.copy()
for th, col in ((0.5, (255, 0, 255)),):
    e = np.asarray(Image.fromarray((m > th).astype(np.uint8) * 255).filter(ImageFilter.FIND_EDGES)) > 0; o[e] = col
# inner model edges: luminance edges of the render inside the silhouette, in cyan
L = Image.fromarray((A[:, :, :3] @ [0.3, 0.59, 0.11]).astype(np.uint8)).filter(ImageFilter.FIND_EDGES)
e2 = (np.asarray(L) > 60) & (m > 0.5); o[e2] = o[e2] * 0.4 + np.array((0, 255, 255)) * 0.6
mm = A[:, :, :3] * m[:, :, None] + 255 * (1 - m[:, :, None])
ims = [Image.fromarray(x.clip(0, 255).astype(np.uint8)).crop(box) for x in (G, o, mm)]
w, h = ims[0].size; W, H = int(w * sc), int(h * sc)
c = Image.new('RGB', (W, 3 * H))
for i, im in enumerate(ims): c.paste(im.resize((W, H), Image.LANCZOS), (0, i * H))
c.save(out, quality=88); print(out, c.size)
