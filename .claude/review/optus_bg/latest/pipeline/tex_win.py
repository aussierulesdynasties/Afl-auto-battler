"""Hand-made facade textures (no photo pixels). RGBA: alpha 1 = glass, 0 = wall (wall takes the building's own colour).
tower.png: one tile = 3.0 m wide x 3.6 m (one storey) curtain wall.  wall.png: one tile = 3.6 m x 3.2 m punched window.
"""
import os, sys
import numpy as np
from PIL import Image
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(4)

def glass(h, w, top=(0.21, 0.28, 0.35), bot=(0.10, 0.13, 0.17)):
    t = np.linspace(0, 1, h)[:, None, None]
    g = np.array(top)[None, None] * (1 - t) + np.array(bot)[None, None] * t
    return np.repeat(g, w, axis=1)

N = 256
# tower: mullions every 1.5 m, spandrel band 0.9 m per storey
A = np.zeros((N, N, 4)); A[..., :3] = 0.75; A[..., 3] = 0
pxm = N / 3.6  # px per metre vertically
gl = glass(N - int(0.9 * pxm), N)
A[int(0.9 * pxm):, :, :3] = gl; A[int(0.9 * pxm):, :, 3] = 1
for x in (0, N // 2):
    A[:, max(0, x - 3):x + 3, 3] = 0; A[:, max(0, x - 3):x + 3, :3] = 0.75
A[int(0.9 * pxm) - 3:int(0.9 * pxm) + 2, :, 3] = 0
A[..., :3] *= (1 + 0.04 * (rng.random((N, N, 1)) - 0.5))
Image.fromarray((np.clip(A, 0, 1) * 255).astype(np.uint8), 'RGBA').save(os.path.join(out, 'tower.png'))

# wall: one window 1.6 m x 1.5 m, sill at 0.9 m, centred
B = np.zeros((N, N, 4)); B[..., :3] = 1.0; B[..., 3] = 0
sx = N / 3.6; sy = N / 3.2
x0, x1 = int((1.8 - 0.8) * sx), int((1.8 + 0.8) * sx)
y0, y1 = N - int(2.4 * sy), N - int(0.9 * sy)   # image row 0 = top
B[y0:y1, x0:x1, :3] = glass(y1 - y0, x1 - x0); B[y0:y1, x0:x1, 3] = 1
B[y1:y1 + 4, x0 - 4:x1 + 4, 3] = 0; B[y1:y1 + 4, x0 - 4:x1 + 4, :3] = 0.86  # sill
B[..., :3] *= (1 + 0.05 * (rng.random((N, N, 1)) - 0.5))
Image.fromarray((np.clip(B, 0, 1) * 255).astype(np.uint8), 'RGBA').save(os.path.join(out, 'wall.png'))
print('ok')
