"""Grass traced from the straight-down satellite (reference only, director 2026-11-20 "Trace grass"): green-leaning
ground pixels -> data/<g>/prep/grass.npy (bool, row 0 = north edge, sat.json frame) and grass.png for viewing."""
import sys, json, numpy as np
from PIL import Image, ImageFilter
g = sys.argv[1]; a = np.asarray(Image.open(f'data/{g}/sat.png').convert('RGB'), float)
R, G, B = a[..., 0], a[..., 1], a[..., 2]; exg = 2 * G - R - B
m = Image.fromarray(((exg > 18) * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5))
m.save(f'data/{g}/prep/grass.png'); np.save(f'data/{g}/prep/grass.npy', np.asarray(m) > 127)
print('grass frac', round(float((np.asarray(m) > 127).mean()), 3))
