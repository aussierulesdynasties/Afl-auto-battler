"""Texture session FAIL 2 (towers read identical at range): six tower facades, each with one big feature >= 3 m that
survives 1.85 px/m. Glass is opaque colour (alpha 255) so the tower's mean colour comes from the facade, not the sky.
Also coarse plaza paving (1.2 m slabs, 6 m banding) normalised to mean 192 for the ground's paver multiply."""
from PIL import Image; import numpy as np, json
R = np.random.default_rng(57); N = 512; SZ = json.load(open('tex/fc_sizes.json'))
def P(m, t): return int(round(m / t * N))
def base(lo=0.9):
    A = np.zeros((N, N, 4), np.float32); A[..., :3] = 255 * (lo + (1 - lo) * np.kron(R.random((64, 64)), np.ones((8, 8))))[..., None]; return A
def glass(A, y0, y1, x0, x1, c, grad=0.25):
    g = np.linspace(1 + grad, 1 - grad, max(1, y1 - y0))[:, None, None]
    A[y0:y1, x0:x1, :3] = np.clip(np.array(c, np.float32) * g, 0, 255); A[y0:y1, x0:x1, 3] = 255
def save(n, A, tw, th): Image.fromarray(np.clip(A, 0, 255).astype(np.uint8), 'RGBA').save('tex/fc_%s.png' % n); SZ[n] = [tw, th]

# 1-3: banded glass (spandrel band 1.3 m = wall colour, glass 2.4 m): blue-green, charcoal, bronze
for n, c in (('tw_bluegreen', (52, 96, 98)), ('tw_charcoal', (30, 33, 38)), ('tw_bronze', (92, 70, 50))):
    fl = 3.7; tw, th = 12.0, 4 * fl; A = base()
    for f in range(4):
        y0 = P(f * fl, th); glass(A, y0 + P(1.3, th), P((f + 1) * fl, th), 0, N, c, 0.12)
        for x in range(0, N, P(1.5, tw)): A[y0 + P(1.3, th):P((f + 1) * fl, th), x:x + 2, :3] *= 0.8
    save(n, A, tw, th)
# 4: full-height glass curtain with a reflection gradient over 4 floors, slim mullions only
fl = 3.6; tw, th = 12.0, 4 * fl; A = base(); glass(A, 0, N, 0, N, (56, 70, 86), 0.1)
for x in range(0, N, P(1.5, tw)): A[:, x:x + 2, :3] *= 0.75
for f in range(4): A[P(f * fl, th):P(f * fl, th) + 2, :, :3] *= 0.8
save('tw_curtain', A, tw, th)
# 5: warm sandstone / 6: white concrete, deep dark window bands 2.0 m
for n in ('tw_sandstone', 'tw_white'):
    fl = 3.5; tw, th = 12.0, 4 * fl; A = base(0.86)
    for f in range(4):
        ya, yb = P(f * fl + 1.2, th), P(f * fl + 3.2, th); glass(A, ya, yb, 0, N, (28, 32, 38), 0.1)
        for x in range(0, N, P(3.0, tw)): A[ya:yb, x:x + 4, 3] = 0; A[ya:yb, x:x + 4, :3] = 200
    save(n, A, tw, th)
# 7: vertical fins: glass with 0.5 m wall-colour fins every 3 m
fl = 3.6; tw, th = 12.0, 4 * fl; A = base(); glass(A, 0, N, 0, N, (40, 58, 70), 0.2)
for x in range(0, N, P(3.0, tw)): A[:, x:x + P(0.5, tw), 3] = 0; A[:, x:x + P(0.5, tw), :3] = 245
for f in range(4): A[P(f * fl, th):P(f * fl, th) + 3, :, :3] *= 0.7
save('tw_fins', A, tw, th)
json.dump(SZ, open('tex/fc_sizes.json', 'w'), indent=1)

# plaza paving: 12 m tile, 1.2 m slabs with 3 cm joints, a darker 1.2 m band every 6 m, slab tone variation
T = 12.0; M = 1024; s = M / T; A = np.zeros((M, M, 3), np.float32)
for i in range(10):
    for j in range(10):
        A[int(j * 1.2 * s):int((j + 1) * 1.2 * s), int(i * 1.2 * s):int((i + 1) * 1.2 * s)] = R.uniform(0.9, 1.05)
for j in (0, 5): A[int(j * 1.2 * s):int((j + 1) * 1.2 * s)] *= 0.78
for k in range(11):
    A[int(k * 1.2 * s):int(k * 1.2 * s) + 3] *= 0.55; A[:, int(k * 1.2 * s):int(k * 1.2 * s) + 3] *= 0.55
A *= (0.94 + 0.06 * R.random((M, M)))[..., None]
A = A / A.mean() * 192; Image.fromarray(np.clip(A, 0, 255).astype(np.uint8)).save('tex/v3_plaza.png'); print('ok', A.mean())
