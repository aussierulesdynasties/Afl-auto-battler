# offset between aerial and model top view per 350 m tile (phase correlation of water masks): model needs shift (dx, dy) m
import numpy as np
exec(open('meas_water.py').read().split('inter=')[0])
def pc(a, b):
    F = np.fft.fft2(a - a.mean()) * np.conj(np.fft.fft2(b - b.mean())); r = np.fft.ifft2(F / (np.abs(F) + 1e-6)).real
    i, j = np.unravel_index(np.argmax(r), r.shape); n = a.shape[0]
    return ((j + n // 2) % n - n // 2), ((i + n // 2) % n - n // 2), r.max()
for ty in range(4):
    for tx in range(4):
        sl = (slice(ty * 350, ty * 350 + 350), slice(tx * 350, tx * 350 + 350))
        A, B = ws[sl].astype(float), wm[sl].astype(float)
        if A.mean() < 0.03 or B.mean() < 0.03: continue
        dx, dy, q = pc(A, B)
        print('tile x', tx * 350 - 700, 'y', 700 - ty * 350, 'aerial is model shifted by dx', dx, 'm  dy', -dy, 'm  peak', round(q, 3))
