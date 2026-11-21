"""Hand-made tiles copied from the People First aerial (reference only, no aerial pixels):
tex/roof_shed.png   12 m tile, 1024 px: ribbed sheet roof, rib every 0.76 m, weathering, multiplier for the roof colour.
tex/roof_solar.png  48 m tile, 2048 px: the same sheet plus solar arrays (dark blue panel strips in rows, as on the NW halls).
tex/park_bays.png   u 31.2 m (12 bays of 2.6 m) x v 34.8 m (two rows of 5.4 m bays back to back, 6.6 m aisle), 2048 px:
                    the park asphalt with 0.12 m white bay lines."""
import numpy as np
from PIL import Image
rng = np.random.default_rng(3)
def noise(n, cells, seed):   # smooth tileable value noise
    r = np.random.default_rng(seed).random((cells, cells)); g = np.arange(n) / n * cells
    i = np.floor(g).astype(int); f = g - i; f = f * f * (3 - 2 * f)
    a = r[np.ix_(i % cells, i % cells)]; b = r[np.ix_(i % cells, (i + 1) % cells)]; c = r[np.ix_((i + 1) % cells, i % cells)]; d = r[np.ix_((i + 1) % cells, (i + 1) % cells)]
    fx = f[None, :]; fy = f[:, None]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy
def sheet(n, metres, seed):
    x = (np.arange(n) + 0.5) / n * metres; ph = (x % 0.76) / 0.76
    rib = np.where(ph < 0.12, 1.06, np.where(ph < 0.22, 0.86, 0.97))[None, :].repeat(n, 0)   # lit crest, shaded flank, flat pan
    w = 0.92 + 0.08 * (0.6 * noise(n, max(2, int(metres / 6)), seed) + 0.4 * noise(n, max(4, int(metres / 1.5)), seed + 1))
    return rib * w
S = sheet(1024, 12.0, 1)
Image.fromarray(np.dstack([np.clip(S * 235, 0, 255)] * 3 + [np.zeros_like(S)]).astype(np.uint8)).save('tex/roof_shed.png')
n, M = 2048, 48.0; S = sheet(n, M, 5); px = n / M
rgb = np.dstack([S, S, S]) * 235
pan = np.array([46, 58, 82], float)
for (x0, y0, strips, L) in [(3, 4, 7, 15), (27, 4, 7, 15), (3, 28, 7, 15), (27, 28, 7, 10)]:   # arrays: strips 1.9 m wide, 0.5 m walk gap
    for k in range(strips):
        a = int((x0 + k * 2.4) * px); b = int((x0 + k * 2.4 + 1.9) * px); c = int(y0 * px); d = int((y0 + L) * px)
        rgb[c:d, a:b] = pan * (0.9 + 0.2 * rng.random())
        for yy in np.arange(y0 + 1.0, y0 + L, 1.0): rgb[int(yy * px):int(yy * px) + 2, a:b] = pan * 1.5   # panel joints
Image.fromarray(np.dstack([np.clip(rgb, 0, 255), np.zeros((n, n))]).astype(np.uint8)).save('tex/roof_solar.png')
pk = np.asarray(Image.open('tex/road_asphalt_park.png').convert('RGB'), float)   # 104 m tile, 4096 px
U, V = 31.2, 34.8
xs = ((np.arange(n) + 0.5) / n * U / 104 * 4096).astype(int); ys = ((np.arange(n) + 0.5) / n * V / 104 * 4096).astype(int)
img = pk[np.ix_(ys, xs)]
u = (np.arange(n) + 0.5) / n * U; v = (np.arange(n) + 0.5) / n * V
inb = lambda vv: ((vv % 17.4) < 10.8)              # bay band (two bays back to back), then the aisle
div = (np.abs(((u + 1.3) % 2.6) - 1.3) < 0.06)     # bay dividers every 2.6 m
back = np.abs((v % 17.4) - 5.4) < 0.06             # line between the paired bays
L = (div[None, :] & inb(v)[:, None]) | back[:, None].repeat(n, 1)
img[L] = img[L] * 0.25 + np.array([226, 226, 220]) * 0.75
Image.fromarray(np.clip(img[::-1], 0, 255).astype(np.uint8)).save('tex/park_bays.png')   # row 0 = v 1 in Blender
print('ok')
pale = img.copy(); pale[~L] = pale[~L] * 1.4; pale[L] = pale[L] * 0.25 + np.array([240, 240, 236]) * 0.75
Image.fromarray(np.clip(pale[::-1], 0, 255).astype(np.uint8)).save('tex/park_bays_pale.png')   # bare concrete end of the SW car park
# shed roof skylights: 1.0 m translucent strips every 6 m across the ribs (12 m tile, so two per tile)
S = sheet(1024, 12.0, 1); rgb = np.dstack([S, S, S]) * 235; y = (np.arange(1024) + 0.5) / 1024 * 12.0
sk = (y % 6.0) < 1.0; rgb[sk] = np.array([178, 190, 200]) * (0.95 + 0.05 * S[sk][..., None])
Image.fromarray(np.dstack([np.clip(rgb, 0, 255), np.zeros((1024, 1024))]).astype(np.uint8)).save('tex/roof_shed.png')
# commercial wall, one tile = 7.2 m wide x 6 m tall (v up): plinth, cladding with column joints, high window band (glass, alpha 1), fascia
W, H = 512, 448; img = np.ones((H, W, 3)); al = np.zeros((H, W)); v = 1 - (np.arange(H) + 0.5) / H; u = (np.arange(W) + 0.5) / W * 7.2
img[v < 0.14] = 0.55
cl = (v >= 0.14) & (v < 0.74); img[cl] = 0.94; img[cl & ((v * 6.0) % 0.6 < 0.04)] = 0.86   # cladding with faint sheet lines
img[:, np.abs(u - 3.6) < 0.18] *= np.where(v < 0.84, 0.72, 1)[:, None, None]   # column joint
wb = (v >= 0.74) & (v < 0.84); img[wb] = np.array([0.36, 0.42, 0.50]); al[wb] = 1.0
img[v >= 0.84] = 1.0
Image.fromarray(np.dstack([np.clip(img * 255, 0, 255), al * 255]).astype(np.uint8)).save('tex/wall_shed.png')
print('shed ok')
