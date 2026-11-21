# Median seat colour per tier per 10 deg from the far-side zoom strips (photo unwraps, 50 px/deg, start heading+145).
import os, glob, numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
acc = {}
for f in glob.glob(os.path.join(HERE, 'z_f*_t?_p.png')):
    n = os.path.basename(f); h = int(n[3:6]); t = n[7:9]; b0 = (h + 145) % 360
    A = np.asarray(Image.open(f).convert('RGB')).astype(float)[14:]
    for x0 in range(0, A.shape[1], 50):
        b = int((b0 + x0 / 50) % 360) // 10 * 10
        P = A[:, x0:x0 + 50].reshape(-1, 3); s = P.sum(1)
        P = P[(s > 60) & (s < 420)]
        if len(P) > 500: acc.setdefault((t, b), []).append(np.median(P, 0))
for t in ('t1', 't2', 't3'):
    print(t, ' '.join('%d:%s' % (b, ','.join('%d' % c for c in np.median(acc[(t, b)], 0))) for b in range(0, 360, 10) if (t, b) in acc))
