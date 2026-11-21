"""Hand-made tiles for the lead's 2nd fault list: concrete (bridges), hut walls, roofs with stronger ribs, apron asphalt, far farmland."""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFilter
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(H, 'tex'); R = np.random.default_rng(4)
def noise(n, scale, oct_=3):
    out = np.zeros((n, n), np.float32); a = 1.0
    for o in range(oct_):
        k = max(2, int(n / scale * 2 ** o)); g = R.random((k, k)).astype(np.float32)
        out += a * np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC), np.float32) / 255; a *= 0.5
    return (out - out.min()) / (np.ptp(out) + 1e-6)
def save(a, nm, alpha=None):
    a = np.clip(a, 0, 255).astype(np.uint8)
    if alpha is not None: a = np.dstack([a, alpha.astype(np.uint8)])
    Image.fromarray(a).save(os.path.join(T, nm)); print(nm, a.shape, a[..., :3].reshape(-1, 3).mean(0).round())
# concrete: 4 m tile, 512 px; 2 m panel joints, speckle, rain streaks
n = 512; c = 172 + 22 * (noise(n, 64) - 0.5) + R.normal(0, 5, (n, n))
streak = noise(n, 24, 2)[:, :1].repeat(n, 1).T * 0 + np.asarray(Image.fromarray((R.random((8, 64)) * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC), np.float32) / 255
c -= 18 * np.clip(streak - 0.55, 0, 1) * 3
for j in (0, 256): c[j:j + 3, :] -= 45; c[:, j:j + 3] -= 45
save(np.dstack([c, c * 0.99, c * 0.96]), 'concrete.png', np.zeros((n, n)))
# hut wall: 6 m x 3.2 m tile (768 x 410 px, 128 px/m): weatherboard, roller door, window (glass alpha), plinth
W_, H_ = 768, 410; ppm = 128; img = np.full((H_, W_), 232.0); al = np.zeros((H_, W_))
for y in range(0, H_, 23): img[y:y + 3, :] -= 38          # board shadow every 0.18 m
img += R.normal(0, 3, (H_, W_))
def rect(u0, u1, v0, v1): return slice(H_ - int(v1 * ppm), H_ - int(v0 * ppm)), slice(int(u0 * ppm), int(u1 * ppm))
r = rect(0.5, 3.4, 0.0, 2.6); img[r] = 150; sub = img[r]
for y in range(0, sub.shape[0], 10): sub[y:y + 2, :] -= 30   # roller door slats
img[rect(0.42, 3.48, 2.6, 2.72)] = 90                       # door head
r = rect(4.3, 5.6, 1.1, 2.1); img[r] = 60; al[r] = 255      # window glass
img[rect(4.24, 5.66, 1.04, 1.1)] = 250; img[rect(4.24, 5.66, 2.1, 2.16)] = 250
img[rect(0, 6, 0, 0.18)] = 120                               # plinth
save(np.dstack([img, img, img]), 'wall_hut.png', al)
# roofs: re-made with deeper ribs and weathering (zincalume), mean ~170
def ribbed(n, tile_m, rib_m, sky=None):
    ppm = n / tile_m; u = np.arange(n) / ppm; ph = (u % rib_m) / rib_m
    prof = np.where(ph < 0.12, 120, np.where(ph < 0.2, 205, 172)).astype(np.float32)
    a = np.tile(prof, (n, 1)) + 14 * (noise(n, n / 3, 2) - 0.5) + R.normal(0, 3, (n, n))
    al = np.zeros((n, n))
    if sky:
        for k in np.arange(0, tile_m, sky):
            j0 = int(k * ppm); a[:, j0:j0 + int(ppm)] = np.where(np.tile(prof, (n, 1))[:, j0:j0 + int(ppm)] > 150, 205, 150) * np.array([1.0])
    return np.dstack([a, a * 1.01, a * 1.03]), al
a, al = ribbed(512, 3.04, 0.76); save(a, 'roof_metal.png', al)
a, al = ribbed(1024, 12.0, 0.76, sky=6.0); save(a, 'roof_shed.png', al)
# apron asphalt: 32 m tile, 1024 px (32 px/m): grain, patch repairs, oil stains, yellow walkway lines, white bay ticks
n = 1024; ppm = 32; a = 118 + 20 * (noise(n, 128) - 0.5) + R.normal(0, 7, (n, n))
im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGB'); d = ImageDraw.Draw(im)
for _ in range(5):
    x, y = R.integers(0, n - 200, 2); w, h = R.integers(60, 200, 2); t = int(R.integers(95, 140)); d.rectangle([x, y, x + w, y + h], fill=(t, t, t))
st = Image.new('L', (n, n), 0); ds = ImageDraw.Draw(st)
for _ in range(26):
    x, y = R.integers(0, n, 2); rx, ry = R.integers(12, 46, 2); ds.ellipse([x - rx, y - ry, x + rx, y + ry], fill=int(R.integers(60, 140)))
st = st.filter(ImageFilter.GaussianBlur(9))
pass  # no walkway lines: the aerial shows a plain concourse  # for y0 in (300, 330): d.rectangle([0, y0, n, y0 + 4], fill=(214, 182, 52))     # two yellow walkway lines 0.12 m
pass  # no bay ticks  # for x0 in range(0, n, int(2.6 * ppm)): d.rectangle([x0, 700, x0 + 4, 700 + int(5.4 * ppm)], fill=(226, 226, 222))   # bay ticks
pass  # d.rectangle([0, 700, n, 704], fill=(226, 226, 222))
a = np.asarray(im, np.float32) * (1 - 0.45 * np.asarray(st, np.float32)[..., None] / 255)
save(a, 'apron.png')
# far farmland: 600 m tile, 1024 px; fields (voronoi), tree clumps, tracks; mean ~ 225 so it modulates the vertex colour
n = 1024; P = R.random((60, 2)) * n; tone = R.uniform(0.82, 1.08, 60); hue = R.uniform(-0.06, 0.06, 60)
yy, xx = np.mgrid[0:n, 0:n]; best = np.full((n, n), 1e9); lab = np.zeros((n, n), int)
for k, (px, py) in enumerate(P):
    for ox in (-n, 0, n):
        for oy in (-n, 0, n):
            dd = (xx - px - ox) ** 2 + (yy - py - oy) ** 2; m = dd < best; best[m] = dd[m]; lab[m] = k
f = tone[lab] * (1 + 0.06 * (noise(n, 64) - 0.5)); hh = hue[lab]
rgb = np.dstack([f * (1 + hh), f, f * (1 - hh)]) * 225
edge = (np.abs(np.diff(lab, axis=0, prepend=lab[:1])) + np.abs(np.diff(lab, axis=1, prepend=lab[:, :1]))) > 0
rgb[edge] *= 0.7                                                                    # hedgerows and fences
cl = noise(n, 90, 3) > 0.68; rgb[cl] *= 0.62                                       # tree clumps
w_ = np.outer(np.sin(np.pi * (np.arange(n) + 0.5) / n), np.sin(np.pi * (np.arange(n) + 0.5) / n))[..., None]   # seamless: cross-fade with the half-rolled copy
rs = np.roll(np.roll(rgb, n // 2, 0), n // 2, 1); rgb = (rgb * w_ + rs * (1 - w_)) / 1.0
pass  # far_land.png now comes from mk_far2.py only  # save(rgb, 'far_land.png', np.zeros(rgb.shape[:2]))
