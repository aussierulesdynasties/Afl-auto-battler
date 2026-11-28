"""Correct a measured turf-edge trace against the kit's own satellite mosaic, in chosen sectors only.

python3 tools/grounds/legacy/retrace_mosaic.py <slug> <turf_enu.json> <out.json> <mode> <b0-b1> [<b0-b1> ...] [--clip lo,hi]

The Google Earth history trace (measuring pass) can sit off the grass edge where the edge is unclear on its frames:
at Hands Oval it runs 2-4 m out behind the east benches, at Summit Park on the outer side of the 2 m grey path in the
south-west (found by the PC's rebuild check, 2026-11-28). This walks each trace point along its normal on the kit
mosaic (`tools/grounds/<slug>/work/sat.png`, made by kit/sat.py, the frame the model plan is drawn in) and finds:

- mode `green`: the last field-green sample, with the field's greenness taken 9-14 m inside the point (copes with
  dry patches); fooled by stand shadow, so do not use it on a shadowed side;
- mode `grey`: the inner edge of a grey path ring (low saturation, bright, 0.7-3.5 m wide) beyond the grass.

With --clip, finds outside [lo, hi] m are dropped (a box or shelter on the line). Shifts are median-filtered round the loop and applied only inside the given bearing sectors (degrees from north about
the trace centroid), tapered to zero over 10 degrees at each sector end. Elsewhere the trace is kept. Check the result
by eye on zoomed boards before using it.
"""
import json, math, sys
import numpy as np, cv2
from scipy.ndimage import median_filter

slug, src, out, mode = sys.argv[1:5]
args = sys.argv[5:]; CLIP = None
if '--clip' in args: i = args.index('--clip'); CLIP = [float(v) for v in args[i + 1].split(',')]; del args[i:i + 2]
sectors = [tuple(float(v) for v in s.split('-')) for s in args]
G = f'tools/grounds/{slug}'
D = json.load(open(f'{G}/model/{slug}.json')); H = D['half']
img = cv2.GaussianBlur(cv2.imread(f'{G}/work/sat.png'), (3, 3), 0)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(float); f = img.astype(float); exg = 2 * f[..., 1] - f[..., 2] - f[..., 0]
O = np.array(json.load(open(src))['outline_enu_m'], float); c = O.mean(0)
t = np.roll(O, -1, 0) - np.roll(O, 1, 0); n = np.stack([t[:, 1], -t[:, 0]], 1); n /= np.linalg.norm(n, axis=1)[:, None]
n *= np.sign(np.sum((O - c) * n, 1))[:, None]
def at(a, p): return a[int(round((H - p[1]) * 4)), int(round((p[0] + H) * 4))]

ss = np.arange(-8, 5.01, 0.25); offs = np.full(len(O), np.nan); ok = np.zeros(len(O), bool)
for i, (p, nn) in enumerate(zip(O, n)):
    if mode == 'green':
        ins = [p + nn * s for s in np.arange(-14, -9, 0.5)]
        hr = np.median([at(hsv[..., 0], q) for q in ins]); er = np.median([at(exg, q) for q in ins])
        if er < 8: continue
        grass = np.array([at(exg, p + nn * s) / er > 0.45 and abs(at(hsv[..., 0], p + nn * s) - hr) < 14 for s in ss])
        k = 0
        while k < len(ss) and grass[k]: k += 1
        if 0 < k < len(ss): offs[i] = ss[k] - 0.125; ok[i] = True
    else:
        grey = np.array([at(hsv[..., 1], p + nn * s) < 45 and at(hsv[..., 2], p + nn * s) > 90 for s in ss])
        for k in range(len(ss) - 3):
            if grey[k:k + 3].all():
                e = k
                while e < len(ss) and grey[e]: e += 1
                if 0.7 < (e - k) * 0.25 < 3.5: offs[i] = ss[k] - 0.125; ok[i] = True
                break
med = median_filter(np.nan_to_num(offs, nan=0.0), size=15, mode='wrap')
good = ok & (np.abs(offs - med) < (1.0 if mode == 'green' else 0.75))
if CLIP: good &= (offs >= CLIP[0]) & (offs <= CLIP[1])   # a building or box on the line is not the edge
idx = np.arange(len(O)); sm = median_filter(np.interp(idx, idx[good], offs[good], period=len(O)), size=9, mode='wrap')

b = np.degrees(np.arctan2(O[:, 0] - c[0], O[:, 1] - c[1])) % 360
def w(bb):
    best = 0.0
    for b0, b1 in sectors:
        d0 = (bb - b0) % 360; L = (b1 - b0) % 360
        if d0 <= L: best = max(best, min(1.0, d0 / 10, (L - d0) / 10))
    return best
W = np.array([w(x) for x in b])
new = O + n * (sm * W)[:, None]
json.dump({'outline_enu_m': [[round(float(x), 3), round(float(y), 3)] for x, y in new],
           'how': f'{src} corrected on the kit mosaic, mode {mode}, sectors {sys.argv[5:]} (tools/grounds/legacy/retrace_mosaic.py)'},
          open(out, 'w'), indent=0)
print(f'{slug}: {good.sum()} of {len(O)} points found on the mosaic')
for b0 in range(0, 360, 30):
    m = (b >= b0) & (b < b0 + 30)
    print(f'  {b0:3d}-{b0 + 30:3d}: applied shift median {np.median(sm[m] * W[m]):+.2f} m (mosaic says {np.median(sm[m]):+.2f})')
