# roof_solar to the aerial's measured panels: grey (aerial 140,137,135 on a 253 roof -> 113 grey on the 205 hand-made roof)
# and 13-18% cover (texture had 32% navy): every other panel array dropped back to bare roof.
import numpy as np
from PIL import Image
from scipy import ndimage
a = np.asarray(Image.open('tex/roof_solar_pre10.png').convert('RGB')).astype(float)
pan = (a[..., 2] - a[..., 0]) > 25
lab, n = ndimage.label(pan); keep = np.isin(lab, np.arange(1, n + 1, 2))
roof = np.median(a[~pan], 0)
out = a.copy(); out[pan & ~keep] = roof
g = a[keep].mean(1, keepdims=True); g = (g - g.mean()) * 0.6
out[keep] = np.clip(np.array([113, 111, 110]) + g, 0, 255)
Image.fromarray(out.astype(np.uint8)).save('tex/roof_solar.png'); print('arrays', n, 'cover now', round(keep.mean(), 3))
