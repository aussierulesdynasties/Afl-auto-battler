"""Tree canopy traced from the straight-down satellite (reference only): dark, green-leaning pixels. Writes a 1 m/px
mask PNG for viewing and data/<g>/prep/canopy.npy (bool, row 0 = north edge)."""
import sys, json, numpy as np
from PIL import Image, ImageFilter
g = sys.argv[1]; a = np.asarray(Image.open(f'data/{g}/sat.png').convert('RGB'), float)
meta = json.load(open(f'data/{g}/sat.json')); print(meta)
R, G, B = a[..., 0], a[..., 1], a[..., 2]; L = a.mean(2)
exg = 2 * G - R - B
_li = Image.fromarray(L.astype(np.uint8)); _sm = _li.resize((_li.width // 8, _li.height // 8), Image.BOX).filter(ImageFilter.MedianFilter(5))
Lb = np.asarray(_sm.resize(_li.size, Image.BILINEAR), float)   # local ground level (~20 m median)
can = ((exg > -4) & (L < 70) & (L < Lb - 12)) | ((exg > 8) & (exg < 70) & (L < 62) & (G > B + 10))   # 2nd term: dense forest where the local median is itself canopy
m = Image.fromarray((can * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5))
m.save(f'data/{g}/prep/canopy.png'); np.save(f'data/{g}/prep/canopy.npy', np.asarray(m) > 127)
print('canopy frac', round(float((np.asarray(m) > 127).mean()), 3))
