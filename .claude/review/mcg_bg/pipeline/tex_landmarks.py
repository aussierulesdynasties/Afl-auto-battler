"""Hand-made landmark textures (drawn from measurements of the reference photos; no photo pixels).
Each texture covers a stated tile size in metres (used as UV scale in landmarks.py). Prints grey stddev per texture."""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(HERE, 'tex')
rng = np.random.default_rng(108)
PX = 64   # px per metre for facades

def noise(h, w, amp, blur=1.5):
    n = rng.normal(0, 1, (h, w)).astype(np.float32)
    im = Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    return (np.asarray(im, np.float32) - 128) / 40 * amp
def save(nm, a, tile):
    a = np.clip(a, 0, 255).astype(np.uint8)
    Image.fromarray(a).save(os.path.join(T, nm))
    g = a[..., :3].astype(np.float32) @ np.array([0.299, 0.587, 0.114])
    SIZES[nm] = tile; print(nm, a.shape[1], 'x', a.shape[0], 'tile m', tile, 'grey std %.1f' % g.std())
SIZES = {}

def glass(nm, tw, th, base, floor_h, band_h, band_col, mull_w, mull_col, mull_every, panel_var, vstripe=None):
    """glass facade: per-panel tint variation (each pane reflects a little differently), floor bands, mullions."""
    W, H = int(tw * PX), int(th * PX)
    a = np.zeros((H, W, 3), np.float32) + np.array(base, np.float32)
    nfl = int(round(th / floor_h)); npan = int(round(tw / mull_every))
    for f in range(nfl):
        for p in range(npan):
            y0, y1 = int(f * floor_h * PX), int((f + 1) * floor_h * PX); x0, x1 = int(p * mull_every * PX), int((p + 1) * mull_every * PX)
            a[y0:y1, x0:x1] *= 1 + panel_var * rng.normal()
            # sky reflection: each pane a little lighter at the top
            a[y0:y1, x0:x1] *= np.linspace(1.08, 0.95, y1 - y0)[:, None, None]
    a += noise(H, W, 3)[..., None]
    for p in range(npan):
        x = int(p * mull_every * PX); a[:, x:x + max(1, int(mull_w * PX))] = mull_col
    for f in range(nfl):
        y = int(f * floor_h * PX); a[y:y + max(1, int(band_h * PX))] = band_col
    if vstripe:
        w, col, every = vstripe
        for k in range(int(round(tw / every))):
            x = int(k * every * PX); a[:, x:x + int(w * PX)] = col
    save(nm, a, [tw, th])

# Australia 108: blue-grey glass, white vertical fins (photos: bright vertical lines ~4 m apart), faint floors (3.15 m)
glass('lm_a108_glass.png', 8.0, 12.6, (92, 112, 132), 3.15, 0.08, (120, 136, 150), 0.06, (70, 84, 96), 1.6, 0.06, vstripe=(0.22, (214, 220, 224), 4.0))
# Eureka: dark blue glass with a white band every floor (photo View 003: white floor lines, 3.26 m)
glass('lm_eureka_glass.png', 6.4, 6.52, (38, 66, 112), 3.26, 0.42, (196, 204, 212), 0.05, (26, 44, 76), 1.6, 0.07)
# Eureka crown: gold glass, dark mullion grid
glass('lm_eureka_gold.png', 6.4, 6.52, (182, 160, 104), 3.26, 0.10, (110, 92, 56), 0.08, (110, 92, 56), 1.6, 0.06)
# Rialto: vivid reflective blue (both photos), darker spandrel each floor (3.6 m), mullions 1.5 m
glass('lm_rialto_glass.png', 6.0, 7.2, (56, 112, 196), 3.6, 0.5, (34, 70, 132), 0.05, (40, 80, 150), 1.5, 0.07)

# gold cladding (A108 starburst): 2 x 1 m panels, seams, slight per-panel tone
W, H = int(4 * PX), int(2 * PX); a = np.zeros((H, W, 3), np.float32) + (206, 164, 62)
for i in range(2):
    for j in range(2):
        a[i * PX:(i + 1) * PX, j * 2 * PX:(j + 1) * 2 * PX] *= 1 + 0.07 * rng.normal()
a += noise(H, W, 4)[..., None]
a[::PX] = (120, 92, 34); a[:, ::2 * PX] = (120, 92, 34)
save('lm_gold.png', a, [4, 2])

# Shrine granite: 1.2 x 0.6 m blocks, running bond, joints, grain
W, H = int(4.8 * PX), int(2.4 * PX); a = np.zeros((H, W, 3), np.float32) + (170, 166, 156)
for r in range(4):
    off = (r % 2) * 0.6
    for c in range(-1, 5):
        x0 = int((c * 1.2 + off) * PX); x1 = x0 + int(1.2 * PX); y0, y1 = int(r * 0.6 * PX), int((r + 1) * 0.6 * PX)
        a[y0:y1, max(0, x0):max(0, min(W, x1))] *= 1 + 0.06 * rng.normal()
        if 0 <= x0 < W: a[y0:y1, x0:x0 + 2] = (140, 132, 116)
    a[int(r * 0.6 * PX):int(r * 0.6 * PX) + 2] = (140, 132, 116)
a += noise(H, W, 9, 0.8)[..., None]
save('lm_stone.png', a, [4.8, 2.4])

# Shrine roof: stepped stone, each 0.8 m step lit on the tread, dark on the riser
W, H = int(4 * PX), int(3.2 * PX); a = np.zeros((H, W, 3), np.float32)
for s in range(4):
    y0 = int(s * 0.8 * PX); a[y0:y0 + int(0.3 * PX)] = (96, 92, 86); a[y0 + int(0.3 * PX):y0 + int(0.8 * PX)] = (58, 56, 52)
a += noise(H, W, 6, 0.8)[..., None]
save('lm_shrine_roof.png', a, [4, 3.2])

# spire white steel: painted tube, shade across, joints
W, H = 64, 256; a = np.zeros((H, W, 3), np.float32) + (232, 232, 228)
a *= np.linspace(1.0, 0.82, W)[None, :, None]
a += noise(H, W, 5)[..., None]
a[::64] = (170, 170, 168)
save('lm_white.png', a, [0.5, 2.0])

# Arts Centre veil: gold-tan mesh (photo: lattice skirt), RGBA, holes
W = H = 256; a = np.zeros((H, W, 4), np.float32); a[..., :3] = (196, 158, 92); a[..., 3] = 0
for k in range(0, W, 32):
    a[:, k:k + 6, 3] = 255; a[k:k + 6, :, 3] = 255
for k in range(-W, W, 45):
    for y in range(H):
        x = k + y
        if 0 <= x < W - 4: a[y, x:x + 4, 3] = 255
a[..., :3] *= (1 + 0.16 * rng.normal(size=(H, 1, 1))) * (1 + 0.16 * rng.normal(size=(1, W, 1))); a[..., :3] += noise(H, W, 10)[..., None]
save('lm_veil.png', a, [4, 4])

# VINEGAR board: green panel, cream border, letters drawn as strokes (no font)
BW, BH = 1024, 256   # board 10 x 2.5 m
im = Image.new('RGB', (BW, BH), (44, 132, 66)); d = ImageDraw.Draw(im)
d.rectangle([6, 6, BW - 7, BH - 7], outline=(232, 236, 220), width=10)
# letter strokes on a 100 x 160 cell (x right, y down)
L = {'V': [[(0, 0), (50, 160), (100, 0)]],
     'I': [[(50, 0), (50, 160)]],
     'N': [[(0, 160), (0, 0), (100, 160), (100, 0)]],
     'E': [[(100, 0), (0, 0), (0, 160), (100, 160)], [(0, 80), (80, 80)]],
     'G': [[(100, 25), (80, 2), (20, 2), (0, 30), (0, 130), (20, 158), (80, 158), (100, 130), (100, 90), (55, 90)]],
     'A': [[(0, 160), (50, 0), (100, 160)], [(22, 100), (78, 100)]],
     'R': [[(0, 160), (0, 0), (75, 0), (100, 22), (100, 58), (75, 80), (0, 80)], [(55, 80), (100, 160)]]}
x = 92; sw = 26
for ch in 'VINEGAR':
    for st in L[ch]:
        pts = [(x + px * 1.0, 48 + py * 1.0) for px, py in st]
        d.line(pts, fill=(240, 240, 232), width=sw, joint='curve')
        for p in pts: d.ellipse([p[0] - sw / 2 + 1, p[1] - sw / 2 + 1, p[0] + sw / 2 - 1, p[1] + sw / 2 - 1], fill=(240, 240, 232))
    x += 126
a = np.asarray(im, np.float32) + noise(BH, BW, 4)[..., None]
save('lm_vinegar.png', a, [10, 2.5])

# Skipping girl cut-out (RGBA), drawn from shapes measured off the photos: 3 m wide x 5 m tall
GW, GH = 300, 500
im = Image.new('RGBA', (GW, GH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
skin, red, white, hair, shoe = (236, 196, 160, 255), (206, 30, 34, 255), (246, 244, 236, 255), (60, 34, 22, 255), (24, 24, 30, 255)
d.line([(70, 210), (20, 250)], fill=skin, width=16); d.line([(230, 200), (285, 175)], fill=skin, width=16)   # arms
d.ellipse([105, 40, 185, 125], fill=skin); d.pieslice([98, 30, 192, 120], 180, 360, fill=hair)            # head + hair
d.ellipse([170, 30, 205, 65], fill=red)                                                                  # bow
d.polygon([(110, 140), (190, 140), (215, 210), (250, 330), (60, 330), (90, 210)], fill=red)              # dress
d.polygon([(118, 138), (182, 138), (165, 175), (135, 175)], fill=white)                                  # collar
d.rectangle([118, 330, 138, 430], fill=skin); d.rectangle([162, 330, 182, 420], fill=skin)               # legs
d.rectangle([116, 395, 140, 440], fill=white); d.rectangle([160, 385, 184, 430], fill=white)             # socks
d.ellipse([108, 432, 148, 456], fill=shoe); d.ellipse([156, 422, 196, 446], fill=shoe)                   # shoes
a = np.asarray(im, np.float32); a[..., :3] += noise(GH, GW, 4)[..., None]
save('lm_girl.png', a, [3, 5])
json.dump(SIZES, open(os.path.join(T, 'lm_sizes.json'), 'w'), indent=1)
