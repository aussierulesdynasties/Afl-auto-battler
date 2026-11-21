"""Hand-made shed sheeting that reads from ~500 m. python -E py_mk_shed2.py
tex/mt/roof_shed.png: 1024 px = 12 m square. Ribs 0.2 m, sheet seams every 0.76 m, each sheet its own tone,
one translucent skylight sheet per 12 m, end laps every 6 m, rust/dirt streaks down the valleys.
tex/mt/clad_rib.png: 512 x 1536 px = 4 m wide x 12 m high wall (one tile covers the whole wall height). Vertical ribs, sheet seams, dark plinth and splash dirt at the base, a rail at 2.4 m.
Each writes a .mean (linear mean) for the multiply gain."""
import os, numpy as np
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); O = os.path.join(H, 'tex', 'mt'); R = np.random.default_rng(23)
def lmean(a): return float(((a / 255.0) ** 2.2).mean())
N = 1024; x = (np.arange(N) + 0.5) / N * 12.0; y = x.copy()
ph = np.mod(x, 0.2) / 0.2
prof = np.where(ph < 0.15, 1.30, np.where(ph < 0.5, 1.0 - 0.4 * (ph - 0.15) / 0.35, np.where(ph < 0.65, 0.62, 0.85 + 0.2 * (ph - 0.65) / 0.35)))
sheet = np.floor(x / 0.76).astype(int); tone = 1 + R.uniform(-0.09, 0.09, sheet.max() + 1)
row = prof * tone[sheet] * 160.0
a = np.tile(row[None, :], (N, 1))
a[:, np.mod(x, 0.76) < 0.035] *= 0.62                          # sheet seams
sk = (x > 5.32) & (x < 6.08); a[:, sk] = 214 + 10 * prof[sk]     # skylight sheet
img = np.stack([a, a * 1.01, a * 1.03], -1); img[:, sk, 2] += 8
for ly in (0.0, 6.0):                                           # end laps: shadow under the upper sheet, bright lip above
    i = int(ly / 12 * N); img[i:i + 5] *= 0.58; img[(i - 3) % N:(i - 3) % N + 3] *= 1.15
st = np.zeros((N, N, 3))
for _ in range(140):
    c = int(R.integers(0, 60) * 0.2 / 12 * N + 0.6 * 0.2 / 12 * N); y0 = int(R.choice([0, N // 2]) + R.integers(0, 40)); L = int(R.integers(60, 420))
    col = np.array([0.72, 0.52, 0.38]) if R.random() < 0.5 else np.array([0.70, 0.70, 0.68])
    ys = np.arange(y0, y0 + L) % N; fall = np.linspace(1, 0, L)[:, None]
    for k in range(int(R.integers(3, 8))): st[ys, (c + k) % N] = np.maximum(st[ys, (c + k) % N], fall * (1 - col) * R.uniform(0.6, 1.0))
img = np.clip(img * (1 - st) + R.normal(0, 3, (N, N, 1)), 0, 255).astype(np.uint8)
Image.fromarray(img).save(os.path.join(O, 'roof_shed.png')); open(os.path.join(O, 'roof_shed.mean'), 'w').write('%.4f' % lmean(img.astype(float)))
# wall cladding (v = 0 at the bottom of the texture image's last row: image row N-1 is the base)
M = 1536; MH = 1536; u = (np.arange(M) + 0.5) / M * 12.0; h = (np.arange(MH)[::-1] + 0.5) / MH * 12.0
p2 = np.mod(u, 0.2) / 0.2; pr = np.where(p2 < 0.2, 1.28, np.where(p2 < 0.5, 0.80, np.where(p2 < 0.7, 1.12, 0.92)))
_sh = np.floor(u / 0.76).astype(int); _tn = 1 + R.uniform(-0.12, 0.12, _sh.max() + 1); w = np.tile((pr * _tn[_sh])[None, :] * 170.0, (MH, 1)); w[:, np.mod(u, 0.76) < 0.06] *= 0.45; w[:, (np.mod(u, 0.76) >= 0.06) & (np.mod(u, 0.76) < 0.10)] *= 1.25   # panel laps: dark shadow + lit lip, ~3 px at 500 m
H2 = np.tile(h[:, None], (1, M))
w[H2 < 0.35] = 70                                                # concrete plinth, shadowed
w *= np.where(H2 < 1.2, 0.72 + 0.28 * np.clip((H2 - 0.35) / 0.85, 0, 1), 1.0)   # splash dirt fading upward
w[np.abs(H2 - 2.4) < 0.05] *= 0.55                               # girt rail line
U2 = np.tile(u[None, :], (MH, 1))
def box(u0, u1, h0, h1): return (U2 >= u0) & (U2 < u1) & (H2 >= h0) & (H2 < h1)
rd = box(4.0, 8.0, 0.0, 4.5); w[rd] = 118 * np.where(np.mod(H2[rd], 0.1) < 0.02, 0.78, 1.0)     # roller door, horizontal slats
w[box(3.88, 4.0, 0, 4.6) | box(8.0, 8.12, 0, 4.6)] = 62; w[box(3.88, 8.12, 4.5, 4.85)] = 150; w[box(3.88, 8.12, 4.85, 4.9)] = 60   # guides + hood box
w[box(9.6, 10.5, 0.0, 2.1)] = 92; w[box(9.52, 9.6, 0, 2.18) | box(10.5, 10.58, 0, 2.18) | box(9.52, 10.58, 2.1, 2.18)] = 48   # personnel door + frame
for u0 in (0.25, 11.55):   # downpipes: lit round pipe with a cast shadow, brackets
    w[box(u0, u0 + 0.12, 0.15, 12.0)] = 200; w[box(u0 + 0.12, u0 + 0.18, 0.15, 12.0)] *= 0.5
    for hb in np.arange(1.0, 12.0, 2.0): w[box(u0 - 0.02, u0 + 0.14, hb, hb + 0.05)] = 120
w = np.clip(w + R.normal(0, 3, (MH, M)), 0, 255)
wi = np.stack([w, w, w * 0.99], -1).astype(np.uint8)
Image.fromarray(wi).save(os.path.join(O, 'clad_rib.png')); open(os.path.join(O, 'clad_rib.mean'), 'w').write('%.4f' % lmean(wi.astype(float)))
print('ok', open(os.path.join(O, 'roof_shed.mean')).read(), open(os.path.join(O, 'clad_rib.mean')).read())
