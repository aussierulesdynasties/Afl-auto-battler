"""Far land 600 m tile (1024 px, ~0.59 m/px): rectangular paddocks, tree belts along boundaries, suburb grain patches. Seamless (wraps)."""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFilter
H = os.path.dirname(os.path.abspath(__file__)); R = np.random.default_rng(11); n = 1024
im = Image.new('RGB', (n * 3, n * 3)); d = ImageDraw.Draw(im)
def rect_wrap(x0, y0, x1, y1, c):
    for ox in (0, n, 2 * n):
        for oy in (0, n, 2 * n): d.rectangle([x0 + ox, y0 + oy, x1 + ox, y1 + oy], fill=c)
# paddocks: random recursive splits (no tile-long lines), each leaf its own tone; belts on some edges
def split(x0, y0, x1, y1, dep):
    w, h = x1 - x0, y1 - y0
    if dep > 7 or (w < 140 and h < 140) or (dep > 2 and R.random() < 0.15):
        t = R.choice([0.78, 0.86, 0.94, 1.02, 1.08, 0.9]); hue = R.uniform(-0.07, 0.05)
        c = tuple(int(v) for v in np.clip(np.array([t * (1 + hue), t, t * (1 - hue)]) * 225, 0, 255))
        rect_wrap(x0, y0, x1, y1, c)
        if R.random() < 0.5: rect_wrap(x0, y0, x1, y0 + 4, (118, 128, 104))
        if R.random() < 0.4: rect_wrap(x0, y0, x0 + 4, y1, (118, 128, 104))
        return
    if w > h: m = x0 + int(w * R.uniform(0.3, 0.7)); split(x0, y0, m, y1, dep + 1); split(m, y0, x1, y1, dep + 1)
    else: m = y0 + int(h * R.uniform(0.3, 0.7)); split(x0, y0, x1, m, dep + 1); split(x0, m, x1, y1, dep + 1)
split(0, 0, n, n, 0)
a = np.asarray(im, np.float32)[n:2 * n, n:2 * n].copy()
# suburb grain: a few patches of house-scale roof speckle (red, grey) on pale yards, with street lines
for _ in range(4):
    cx, cy = R.integers(0, n, 2); r = int(R.integers(80, 150))
    yy, xx = np.mgrid[0:n, 0:n]; dx = (xx - cx + n // 2) % n - n // 2; dy = (yy - cy + n // 2) % n - n // 2
    m = (dx ** 2 + dy ** 2) < r * r
    a[m] = [214, 214, 200]
    roofs = m & (R.random((n, n)) < 0.18); a[roofs] = np.array([[196, 120, 96], [150, 154, 156], [176, 178, 172]])[R.integers(0, 3, roofs.sum())]
    a[m & ((yy % 22) < 3)] = [170, 170, 166]
# copse clumps, small and dark
cl = np.asarray(Image.fromarray((R.random((40, 40)) * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC), np.float32) / 255 > 0.8
a[cl] *= 0.66
a *= 1 + 0.05 * (R.random((n, n, 1)) - 0.5)
a = np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), np.float32)
Image.fromarray(np.dstack([np.clip(a, 0, 255), np.zeros((n, n))]).astype(np.uint8), 'RGBA').save(os.path.join(H, 'tex', 'far_land.png'))
print('far_land', a.reshape(-1, 3).mean(0).round())
