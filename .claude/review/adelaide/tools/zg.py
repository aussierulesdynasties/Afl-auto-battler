import sys
from PIL import Image, ImageDraw
def zg(src, x0, y0, x1, y1, s, out, step=10):
    m = Image.open(src).convert('RGB'); c = m.crop((x0, y0, x1, y1)).resize(((x1 - x0) * s, (y1 - y0) * s), Image.LANCZOS); d = ImageDraw.Draw(c)
    for k in range(x0 - x0 % step, x1, step):
        if k < x0: continue
        d.line([((k - x0) * s, 0), ((k - x0) * s, c.height)], fill=(255, 0, 0) if k % (step * 5) == 0 else (120, 0, 0)); d.text(((k - x0) * s + 1, 1), str(k), fill=(255, 255, 0))
    for k in range(y0 - y0 % step, y1, step):
        if k < y0: continue
        d.line([(0, (k - y0) * s), (c.width, (k - y0) * s)], fill=(255, 0, 0) if k % (step * 5) == 0 else (120, 0, 0)); d.text((1, (k - y0) * s + 1), str(k), fill=(255, 255, 0))
    c.save(out)
if __name__ == '__main__':
    a = sys.argv; zg(a[1], *map(int, a[2:7]), a[7], int(a[8]) if len(a) > 8 else 10)
