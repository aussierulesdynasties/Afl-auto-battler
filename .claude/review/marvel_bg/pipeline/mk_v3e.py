"""Panel family: continuous ribbon window per floor (no dot grid at range), coloured panel band between; darker yard."""
from PIL import Image; import numpy as np, json
R = np.random.default_rng(41); N = 512; SZ = json.load(open('tex/fc_sizes.json'))
bay, fl = 2.0, 3.4; tw, th = 4 * bay, 4 * fl; P = lambda m, t: int(round(m / t * N))
B = np.zeros((N, N, 4), np.float32); B[..., :3] = 255 * (0.9 + 0.1 * np.kron(R.random((64, 64)), np.ones((8, 8))))[..., None]
for f in range(4):
    for b in range(4): B[P(f * fl, th):P((f + 1) * fl, th), P(b * bay, tw):P(b * bay, tw) + 2, :3] *= 0.75
    ya, yb = P(f * fl + 1.2, th), P(f * fl + 3.0, th); c = np.array([42, 50, 60]) * R.uniform(0.85, 1.15)
    B[ya:yb, :, :3] = c * np.linspace(1.15, 0.85, yb - ya)[:, None, None]; B[ya:yb, :, 3] = 255
    for b in range(8): x = P(b * 1.0, tw); B[ya:yb, x:x + 2, 3] = 0; B[ya:yb, x:x + 2, :3] = 120
Image.fromarray(np.clip(B, 0, 255).astype(np.uint8), 'RGBA').save('tex/fc_panel.png'); SZ['panel'] = [tw, th]
json.dump(SZ, open('tex/fc_sizes.json', 'w'), indent=1)
A = np.array(Image.open('tex/rail_bed.png')).astype(np.float32); sh = (np.abs(A - [140, 132, 118]).max(2) < 30); A[sh] *= 0.68
Image.fromarray(np.clip(A, 0, 255).astype(np.uint8)).save('tex/rail_bed.png')
s = json.load(open('spec/marvel.json')); s['palette']['ballast'] = [94, 88, 80]; json.dump(s, open('spec/marvel.json', 'w'), indent=1); print('ok')
