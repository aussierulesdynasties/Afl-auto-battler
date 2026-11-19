# satellite with the model's edges drawn on top (red), cropped like the sat crops
import sys, numpy as np
from PIL import Image, ImageFilter
r = Image.open(sys.argv[1]).convert('RGBA'); s = Image.open(sys.argv[2]).convert('RGB')
a = np.asarray(r).astype(float); L = a[..., :3].mean(-1) * a[..., 3] / 255
g = np.hypot(np.diff(L, axis=0, prepend=0), np.diff(L, axis=1, prepend=0)) + 255 * np.hypot(np.diff(a[..., 3], axis=0, prepend=0), np.diff(a[..., 3], axis=1, prepend=0)) / 255
m = g > 40
o = np.asarray(s).copy(); o[m] = (255, 30, 30)
Image.fromarray(o).crop((80, 80, 1520, 1520)).save(sys.argv[3])
