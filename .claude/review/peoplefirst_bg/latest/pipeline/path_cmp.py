import sys
from PIL import Image
g = sys.argv[1]
x0, y0, x1, y1 = map(float, sys.argv[2:6])  # metres, x east, y north
out = sys.argv[6]
sat = Image.open(f'data/{g}/sat.png').convert('RGB')
top = Image.open(f'out/{g}/ortho/top.png').convert('RGB')
def crop(im, half):
    s = im.size[0] / (2 * half)
    box = (int((x0 + half) * s), int((half - y1) * s), int((x1 + half) * s), int((half - y0) * s))
    return im.crop(box)
half = 700.0
a = crop(sat, half); b = crop(top, half)
W = 700; H = int(W * (y1 - y0) / (x1 - x0))
a = a.resize((W, H)); b = b.resize((W, H))
# brighten satellite cast for comparison
a = a.point(lambda v: min(255, int(v * 1.6)))
c = Image.new('RGB', (2 * W + 10, H), (255, 255, 255))
c.paste(a, (0, 0)); c.paste(b, (W + 10, 0))
c.save(out)
