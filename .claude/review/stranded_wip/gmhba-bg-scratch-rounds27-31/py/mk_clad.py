"""Hand-made profiled-sheet cladding: 512 px = 4 m wide, vertical ribs every 0.5 m, panel seam every 2 m height."""
import numpy as np
from PIL import Image
N = 512; x = np.arange(N); r = np.random.default_rng(7)
t = (x % 64) / 64.0
prof = np.select([t < 0.12, t < 0.2, t < 0.62, t < 0.7], [1.0, 1.0 - (t - 0.12) / 0.08 * 0.35, 0.65 + 0.1 * np.sin((t - 0.2) / 0.42 * np.pi), 0.65 + (t - 0.62) / 0.08 * 0.35], 1.0)
img = np.tile(prof, (N, 1))
img *= 1 + 0.04 * (np.asarray(Image.fromarray((r.random((33, 33)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)) / 255 - 0.5)
img[(np.arange(N) % 256) < 3, :] *= 0.8   # horizontal panel lap
img *= 0.9 + 0.1 * r.random((N, N)) ** 4
v = np.clip(img * 225, 0, 255).astype(np.uint8)
Image.fromarray(np.dstack([v, v, v])).save('proto/tex/mt/clad_rib.png')
a = (v / 255.0) ** 2.2; print('lin mean', round(float(a.mean()), 3), 'std', round(float(v.std()), 1))
