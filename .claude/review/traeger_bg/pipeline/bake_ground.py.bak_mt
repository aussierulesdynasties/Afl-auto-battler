"""Bake tex/ground_detail.png (one tile = 4 m, x1.21 lift) into the scene's ground.png -> data/<name>/prep/ground_baked.png.
Usage: python -E bake_ground.py mcg [px]. Multiplies in linear light like Blender did, re-encodes sRGB. Prints grey std."""
import os, sys, json
import numpy as np
from PIL import Image, ImageFilter
Image.MAX_IMAGE_PIXELS = None
H = os.path.dirname(os.path.abspath(__file__)); name = sys.argv[1]; S = int(sys.argv[2]) if len(sys.argv) > 2 else 8192
D = os.path.join(H, 'data', name, 'prep'); NE = json.load(open(os.path.join(D, 'meta.json')))['near']
def dec(a): a = a / 255.0; return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
def enc(v): v = np.clip(v, 0, 1); return 255 * np.where(v <= 0.0031308, 12.92 * v, 1.055 * v ** (1 / 2.4) - 0.055)
g = Image.open(os.path.join(D, 'ground.png')).convert('RGB').resize((S, S), Image.BICUBIC)
tiles = 2 * NE / 4.0; ppt = S / tiles   # output px per detail tile
det = Image.open(os.path.join(H, 'tex', 'ground_detail.png')).convert('RGB'); DS = det.size[0]
# pre-filter the tile (wrapped) to the output footprint, as texture filtering would
sig = max(0.0, DS / ppt / 2); big = Image.fromarray(np.tile(np.asarray(det), (3, 3, 1)))
det = np.asarray(big.filter(ImageFilter.GaussianBlur(sig)), np.float32)[DS:2 * DS, DS:2 * DS]
dl = dec(det)
c = (np.arange(S) + 0.5) / S * tiles
fx = (c % 1.0) * DS - 0.5                      # u -> column
fy = ((1.0 - (c % 1.0)) * DS - 0.5)            # rows run down: v = 1 - row
i0 = np.floor(fx).astype(int); ax = (fx - i0)[None, :, None]
out = np.empty((S, S, 3), np.uint8); ga = np.asarray(g)
for r0 in range(0, S, 512):
    rr = np.arange(r0, min(S, r0 + 512)); j0 = np.floor(fy[rr]).astype(int); ay = (fy[rr] - j0)[:, None, None]
    J0, J1 = j0 % DS, (j0 + 1) % DS; I0, I1 = i0 % DS, (i0 + 1) % DS
    d = (dl[J0][:, I0] * (1 - ax) + dl[J0][:, I1] * ax) * (1 - ay) + (dl[J1][:, I0] * (1 - ax) + dl[J1][:, I1] * ax) * ay
    out[rr] = np.round(enc(dec(ga[rr].astype(np.float32)) * d * 1.21)).astype(np.uint8)
p = os.path.join(D, 'ground_baked.png'); Image.fromarray(out).save(p, optimize=False)
gr = out[::4, ::4].astype(np.float32) @ np.array([0.299, 0.587, 0.114])
print(p, S, 'px, %.3f m/px' % (2 * NE / S), 'grey std %.1f' % gr.std(), 'MB %.1f' % (os.path.getsize(p) / 1e6))
