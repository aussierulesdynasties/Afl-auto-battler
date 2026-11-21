"""Orbit-range readability pass (1.85 px/m at 600 m): stronger rail-bed contrast, punched concrete with big windows in
clear floor rows, dark glass skylights, shed roofs with 1 m sheet-run tone bands."""
from PIL import Image; import numpy as np, json
R = np.random.default_rng(31); N = 512
SZ = json.load(open('tex/fc_sizes.json'))
# rail bed: very dark ballast bed, mid sleepers, bright running rails (texture-level), gravel shoulders
W, L = 4.4, 2.6; A = np.zeros((N, N, 3), np.float32); n = R.random((N, N)); sx = lambda m: int(m / W * N)
A[:] = np.array([40, 37, 34]) * (0.75 + 0.5 * n[..., None])
for k in range(4):
    y = int((k * 0.65 + 0.2) / L * N); h = int(0.26 / L * N); A[y:y + h, sx(0.95):sx(3.45)] = (112, 108, 102)
for xr in (1.4, 3.0):
    x = sx(xr); A[:, x - 7:x + 7] = (26, 22, 20); A[:, x - 3:x + 3] = (190, 188, 184)
edge = np.clip(np.minimum(np.arange(N), N - 1 - np.arange(N)) / sx(0.35), 0, 1)
A[:] = A * edge[None, :, None] + np.array([140, 132, 118]) * (1 - edge[None, :, None])
Image.fromarray(np.clip(A, 0, 255).astype(np.uint8)).save('tex/rail_bed.png')
# concrete: 3.0 m bays, 2.6 x 2.1 m windows, dark slab band each floor
def punched(name, brick=False):
    bay, fl = 3.0, 3.4; tw, th = 4 * bay, 4 * fl; P = lambda m, t: int(round(m / t * N))
    B = np.zeros((N, N, 4), np.float32); B[..., :3] = 255 * (0.88 + 0.12 * np.kron(R.random((64, 64)), np.ones((8, 8))))[..., None]
    if brick:
        for r in range(0, N, 6): B[r:r + 1, :, :3] *= 0.8
    for f in range(4):
        y0 = P(f * fl, th); B[y0:y0 + P(0.35, th), :, :3] *= 0.7
        for b in range(4):
            x0, x1 = P(b * bay + 0.2, tw), P(b * bay + 2.8, tw); ya, yb = P(f * fl + 0.8, th), P(f * fl + 2.9, th)
            c = np.array([40, 48, 58]) * R.uniform(0.8, 1.2); g = np.linspace(1.15, 0.85, yb - ya)[:, None, None]
            B[ya:yb, x0:x1, :3] = c * g; B[ya:yb, x0:x1, 3] = 255
            m = (x0 + x1) // 2; B[ya:yb, m - 1:m + 2, 3] = 0; B[ya:yb, m - 1:m + 2, :3] = 140
    Image.fromarray(np.clip(B, 0, 255).astype(np.uint8), 'RGBA').save('tex/fc_%s.png' % name); SZ[name] = [tw, th]
punched('concrete'); punched('brick', True)
json.dump(SZ, open('tex/fc_sizes.json', 'w'), indent=1)
# skylights: real glass (alpha 255) in the 48 m membrane
M = np.array(Image.open('tex/roof_membrane.png')).astype(np.float32); sk = (M[..., 0] < 0.33 * 255) & (M[..., 2] > M[..., 0] + 10)
M[sk, :3] = (46, 56, 68); M[sk, 3] = 255; Image.fromarray(M.astype(np.uint8), 'RGBA').save('tex/roof_membrane.png'); print('sky px', sk.sum())
# shed: 1 m sheet-run tone bands so the ribbing reads at range
S = np.array(Image.open('tex/roof_shed.png')).astype(np.float32); s = N / 24.0
for i in range(24):
    if i % 2: S[:, int(i * s):int((i + 1) * s), :3] *= 0.86
Image.fromarray(np.clip(S, 0, 255).astype(np.uint8), 'RGBA').save('tex/roof_shed.png'); print('ok')
