# per-band check vs the aerial (reference only): aerial colour inside vs a 2 m ring outside, and edge offset:
# the polygon is grown/shrunk by -3..+3 m; the offset whose boundary sits on the strongest aerial colour gradient is the edge error.
import json, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
NEAR = 1500; SR = 0.5; X0, X1, Y0, Y1 = 80, 260, -50, 135
sat = Image.open('data/optus/sat.png').convert('RGB')
cr = np.asarray(sat.crop((int((X0+NEAR)/SR), int((NEAR-Y1)/SR), int((X1+NEAR)/SR), int((NEAR-Y0)/SR)))).astype(np.float32)
g = sum(np.hypot(ndi.sobel(ndi.gaussian_filter(cr[..., c], 1), 0), ndi.sobel(ndi.gaussian_filter(cr[..., c], 1), 1)) for c in range(3))
d = json.load(open('spec/optus_fc_hand.json')); tones = json.load(open('spec/optus.json'))['forecourt_tones']
def mask(p):
    im = Image.new('L', (cr.shape[1], cr.shape[0])); ImageDraw.Draw(im).polygon([((x-X0)/SR, (Y1-y)/SR) for x, y in p], fill=1); return np.asarray(im) > 0
rows = []
for kind, items in (('band', d['bands']), ('planter', d['planters'])):
    for i, b in enumerate(items):
        m = mask(b['pts']); dt_in = ndi.distance_transform_edt(m) * SR; dt_out = ndi.distance_transform_edt(~m) * SR
        sd = dt_out - dt_in   # signed distance, negative inside
        prof = [(o, g[(np.abs(sd - o) < 0.5)].mean()) for o in np.arange(-3, 3.01, 0.5)]
        best = max(prof, key=lambda t: t[1]); base = dict(prof)[0.0]
        inside = cr[m].mean(0); ring = cr[(sd > 0.5) & (sd < 2.5)].mean(0)
        t = tones[b['tone']] if kind == 'band' else None
        rows.append((kind, i, round(best[0], 1), round(best[1] / max(base, 1e-6), 2), inside.round().astype(int).tolist(), ring.round().astype(int).tolist(), t))
for r in rows: print('%-7s %2d edge_off %+4.1f m (gain %.2f) aerial in %s ring %s model %s' % r)
offs = [abs(r[2]) for r in rows]; print('overlay error: mean %.2f m, max %.1f m, n %d' % (np.mean(offs), max(offs), len(offs)))
