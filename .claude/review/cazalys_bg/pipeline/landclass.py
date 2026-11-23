"""Land classes for the mid terrain ring from the z14 aerial (reference only: class labels, never pixels on a model).
0 forest, 1 urban, 2 cane/paddock, 3 mangrove, 4 water. -> data/<g>/prep/mid_cls.npy (same grid as mid_h.npy)"""
import sys, os, json, numpy as np
from PIL import Image, ImageFilter
g = sys.argv[1]; D = os.path.join('data', g); P = os.path.join(D, 'prep')
meta = json.load(open(os.path.join(P, 'meta.json'))); H = np.load(os.path.join(P, 'mid_h.npy')) + meta['base']
sj = json.load(open(os.path.join(D, 'sat_z14.json'))); S = np.asarray(Image.open(os.path.join(D, 'sat_z14.png')).filter(ImageFilter.BoxBlur(1))).astype(float)
m = H.shape[0]; st = meta['mid_step']; half = meta['mid']
c = np.arange(m) * st - half
col = np.clip(((c + sj['half_m']) / sj['m_per_px']).astype(int), 0, S.shape[1] - 1)
row = np.clip(((sj['half_m'] - c) / sj['m_per_px']).astype(int), 0, S.shape[0] - 1)
px = S[row[:, None], col[None, :]]; r, gg, b = px[..., 0], px[..., 1], px[..., 2]
mx = px.max(-1); mn = px.min(-1); sat = (mx - mn) / np.maximum(mx, 1); v = mx
cls = np.zeros((m, m), np.uint8)
low = H < 40
cls[(sat < 0.28) & (v > 105) & (H < 250)] = 1
cls[(cls == 0) & low & (v > 85)] = 2
cls[(cls == 0) & (H < 6) & (v <= 85)] = 3
cls[(b > gg + 4) & (b > r + 12)] = 4
cls[H <= 0.3] = 4
# majority 3x3 to drop speckle
o = np.stack([np.roll(np.roll(cls, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
cnt = np.stack([(o == k).sum(0) for k in range(5)]); cls = cnt.argmax(0).astype(np.uint8)
np.save(os.path.join(P, 'mid_cls.npy'), cls)
pal = np.array([[40, 90, 40], [190, 190, 190], [170, 200, 90], [90, 100, 50], [40, 80, 160]], np.uint8)
Image.fromarray(pal[cls[::-1]]).resize((600, 600), 0).save(os.path.join(P, 'mid_cls.png'))
print('classes', [round(float((cls == k).mean()), 3) for k in range(5)])
