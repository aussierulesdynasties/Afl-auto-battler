"""Hand-made tower facades tex/fac/t0-5.png (256 px = one 3.6 m bay x 3.2 m floor): spandrel band (alpha 0, tinted by the tower's colour),
window band (alpha 1, tinted glass), mullions. python -E py_mk_tower_fac.py"""
import os, numpy as np
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(5)
GL = [(28, 40, 52), (34, 52, 58), (46, 42, 36), (26, 34, 46), (40, 50, 60), (30, 46, 44)]
SP = [0.38, 0.30, 0.45, 0.34, 0.42, 0.28]   # spandrel share of each floor
MU = [2, 3, 2, 1, 2, 3]                     # mullions per bay
N = 256
for k in range(6):
    a = np.zeros((N, N, 4), float); s = int(N * SP[k])
    a[:, :, :3] = 226; a[:, :, 3] = 0
    a[:s, :, :3] -= np.linspace(0, 18, s)[:, None, None]        # spandrel darkens toward its lower edge
    a[s:, :, :3] = GL[k]; a[s:, :, 3] = 255
    a[s:, :, :3] += np.linspace(14, 0, N - s)[:, None, None]      # sky gradient in the glass
    for j in range(MU[k] + 1):
        x = int(j * N / (MU[k] + 1)); a[s:, max(0, x - 3):x + 3, :3] = 200; a[s:, max(0, x - 3):x + 3, 3] = 0
    a[s:s + 4, :, :3] = 120; a[s:s + 4, :, 3] = 0; a[:3, :, :3] = 150
    a[:, :, :3] += rng.normal(0, 3, (N, N, 1))
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(H, 'tex', 'fac', 't%d.png' % k))
print('ok')
