# Combine the per-view aisle darkness (aisle2's measure) of every zoom strip for one tier on a global 0.02 deg grid:
# mean over the views that see each bearing, then peaks >= 3 deg apart.  python work/aisleall.py t3 [thr]
import sys, glob, json, numpy as np
from PIL import Image
from scipy.ndimage import uniform_filter1d
t = sys.argv[1]; thr = float(sys.argv[2]) if len(sys.argv) > 2 else 0.4
C = json.load(open('work/cams.json')); N = 18000; S = np.zeros(N); K = np.zeros(N)
starts = {}
for p in glob.glob('work/z_*_%s_p.png' % t):
    v = p.split('z_')[1].rsplit('_%s' % t, 1)[0]
    if v.startswith('n_'):
        b0 = {'n_n': 300, 'n_ne': 0, 'n_e': 50, 'n_se': 90, 'n_s': 135, 'n_sw': 180, 'n_w': 230, 'n_nw': 270}[v]
    elif v.startswith('l'): b0 = C[v][4] - 30
    else: b0 = C[v][4] - 35
    L = np.asarray(Image.open(p).convert('L'), float)[22:]; ok = L > 8
    loc = uniform_filter1d(L, 60, axis=1); sm = uniform_filter1d(L, 7, axis=1)
    d = ((sm < loc - 3) & ok).sum(0) / np.maximum(ok.sum(0), 1); good = ok.sum(0) > 0.5 * L.shape[0]
    bright = (L * ok).sum(0) / np.maximum(ok.sum(0), 1); good &= bright < 150  # skip the light-tower heads
    d = uniform_filter1d(d, 9)
    for i in range(len(d)):
        if not good[i]: continue
        g = int(round(((b0 + i / 50) % 360) * 50)) % N; S[g] += d[i]; K[g] += 1
M = np.where(K > 0, S / np.maximum(K, 1), 0); M = uniform_filter1d(M, 5, mode='wrap')
pick = []
for i in np.argsort(-M):
    if M[i] < thr: break
    if all(min(abs(i - j), N - abs(i - j)) > 150 for j in pick): pick.append(i)
print(' '.join('%.1f' % (i / 50) for i in sorted(pick)))
print('gaps', ' '.join('%.1f' % g for g in np.diff(sorted([i / 50 for i in pick]))))
print('unseen deg:', ' '.join('%d' % b for b in range(360) if K[b * 50:(b + 1) * 50].max() == 0))
