"""Plan-session ask: flat roof 48 m tile = standing-seam bays (seam every 0.6 m, bay laps every 12 m), skylight rows,
ponding stains. Alpha 0: multiplies the roof's vertex colour."""
from PIL import Image; import numpy as np
R = np.random.default_rng(5); N = 1024; s = N / 48.0
A = np.ones((N, N, 4), np.float32) * 255; A[..., 3] = 0
n = np.kron(R.random((N // 32, N // 32)), np.ones((32, 32))); A[..., :3] *= (0.9 + 0.1 * n)[..., None]
for b in range(4):   # four 12 m bays, each a slightly different sheet shade
    A[:, int(b * 12 * s):int((b + 1) * 12 * s), :3] *= R.uniform(0.88, 1.0)
    A[:, int(b * 12 * s):int(b * 12 * s) + 4, :3] *= 0.6
for i in range(80): x = int(i * 0.6 * s); A[:, x:x + 2, :3] *= 0.8; A[:, x + 2:x + 3, :3] *= 1.08
for b in range(4):   # skylight strips down each bay: 1.4 m x 3 m every 8 m
    for j in range(6):
        x0 = int((b * 12 + 5.3) * s); y0 = int((j * 8 + 2.5) * s)
        A[y0:y0 + int(3 * s), x0:x0 + int(1.4 * s), :3] = (0.30 * 255, 0.36 * 255, 0.42 * 255)
        A[y0:y0 + int(3 * s), x0 - 2:x0, :3] = 0.95 * 255
yy, xx = np.ogrid[:N, :N]
for _ in range(10):
    cx, cy, r = R.integers(0, N), R.integers(0, N), R.integers(40, 140)
    d = np.hypot(((xx - cx + N // 2) % N) - N // 2, ((yy - cy + N // 2) % N) - N // 2) / r
    A[..., :3] *= (1 - 0.2 * np.clip(1 - d, 0, 1) ** 1.5)[..., None]
Image.fromarray(np.clip(A, 0, 255).astype(np.uint8), 'RGBA').save('tex/roof_membrane.png')
Image.fromarray(np.clip(A[::2, ::2, :3], 0, 255).astype(np.uint8)).save('out/marvel/close/membrane48.png'); print('ok')
