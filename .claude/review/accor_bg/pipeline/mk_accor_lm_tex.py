"""Hand-made textures for the Accor landmarks (ref: Google Images 2026-11-20). python -E mk_accor_lm_tex.py"""
import numpy as np
from PIL import Image
rng = np.random.default_rng(9)
def save(a, n): Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save('tex/%s.png' % n)
# ribbed metal roof, 8 m tile, rib every 0.5 m (arena roof: light grey; station shells: pale grey)
for n, col in (('acc_roof_arena', (58, 62, 68)), ('acc_shell', (196, 198, 196)), ('acc_station', (138, 144, 148))):
    a = np.full((512, 512, 3), col, np.float32) + rng.normal(0, 2, (512, 512, 1))
    for x in range(0, 512, 32): a[:, x:x + 3] *= 0.8; a[:, x + 3:x + 5] *= 1.08
    if n == 'acc_roof_arena':
        for y in range(0, 512, 128): a[y:y + 4] *= 0.7   # panel joints
    save(a, n)
# Dome: white sheet with meridian ribs every 2 m (u) and ring purlins every 4 m (v), 8 m tile
a = np.full((512, 512, 3), (236, 236, 232), np.float32) + rng.normal(0, 2, (512, 512, 1))
for y in range(0, 512, 256): a[y:y + 5] *= 0.86   # ring steps only, no meridian ribs (photo)
save(a, 'acc_dome')
# glass curtain wall with white mullions every 1.5 m, transoms every 4 m; 6 x 8 m tile
a = np.zeros((512, 384, 3), np.float32); g = np.linspace(0, 1, 512)[:, None, None]
a[:] = np.array([92, 118, 138]) * (0.85 + 0.3 * g) + rng.normal(0, 2, (512, 384, 1))
for x in range(0, 384, 96): a[:, x:x + 6] = (220, 222, 224)
for y in range(0, 512, 256): a[y:y + 8] = (220, 222, 224)
save(a, 'acc_glass')
# Dome drum: blue cladding panels, 3 m panel lines
a = np.full((256, 256, 3), (70, 104, 140), np.float32) + rng.normal(0, 2, (256, 256, 1))
for x in range(0, 256, 96): a[:, x:x + 2] *= 0.8
save(a, 'acc_drum')
print('ok')
# Showground front block: red brick, 0.25 x 0.075 m courses with mortar, 6 m tile (photo pass 2026-11-21)
a = np.full((512, 512, 3), (164, 84, 58), np.float32) * (0.92 + 0.16 * rng.random((512, 512, 1)))
for y in range(0, 512, 6): a[y:y + 1] = (196, 186, 170)
for y in range(0, 512, 12):
    for x in range(0 if (y // 12) % 2 else 10, 512, 21): a[y:y + 12, x:x + 1] = (196, 186, 170)
for y in range(0, 512, 128): a[y:y + 30, :] = (60, 70, 78)   # window band every 3 m
save(a, 'acc_brick')
a = np.full((512, 512, 3), (40, 120, 190), np.float32) + rng.normal(0, 3, (512, 512, 1))
for y in range(0, 512, 64): a[y:y + 4] *= 0.8
save(a, 'acc_bluetower')
