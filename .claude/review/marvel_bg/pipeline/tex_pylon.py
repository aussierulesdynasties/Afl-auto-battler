"""mv_pylon.png: plain grey bridge-pylon cladding, hand-made (no photo pixels). Alpha 0 = wall colour (no glass).
Tile 4 x 4 m: 2 m panels, dark 3 cm joints, per-panel tone, fine grain, rain streaks below each horizontal joint."""
import numpy as np
from PIL import Image
r = np.random.default_rng(140); N = 512; px = N / 4.0
a = np.full((N, N), 200.0)
for i in range(2):
    for j in range(2):
        a[i*256:(i+1)*256, j*256:(j+1)*256] += r.normal(0, 7)
a += r.normal(0, 5, (N, N))
for k in range(N):   # streaks: fade down from each horizontal joint
    pass
y = np.arange(N)[:, None] % 256
a -= 14 * np.exp(-y / 60.0) * (r.random((1, N)) > 0.6)
for c in (0, 256): a[c:c+4, :] = 120; a[:, c:c+4] = 120
a = np.clip(a, 0, 255)
rgb = np.stack([a, a * 1.0, a * 0.98], -1); al = np.zeros((N, N, 1))
Image.fromarray(np.concatenate([rgb, al], -1).astype(np.uint8), 'RGBA').save('tex/mv_pylon.png')
print('mv_pylon.png grey std %.1f' % a.std())
