# Measure each building's roof colour from the straight-down satellite (reference measurement only: one median RGB
# per roof, applied as a tint over the hand-made roof textures). Writes roof_c into buildings.json and the hand-made
# textures' mean colours into roof_tex_mean.json, so scene.py can tint each texture to the measured tone.
import json, sys, numpy as np
from PIL import Image, ImageDraw
g = sys.argv[1]; D = f'data/{g}/prep'
sat = Image.open(f'data/{g}/sat.png').convert('RGB'); A = np.asarray(sat)
meta = json.load(open(f'data/{g}/sat.json')); half, mpp = meta['half_m'], meta['m_per_px']
BL = json.load(open(f'{D}/buildings.json')); n = 0
for b in BL:
    P = np.array(b['p'], float); c = P.mean(0); Q = c + (P - c) * 0.75   # inner 75%: skip eaves, shadows, walls
    px = [((x + half) / mpp, (half - y) / mpp) for x, y in Q]
    xs, ys = [p[0] for p in px], [p[1] for p in px]
    x0, y0, x1, y1 = int(min(xs)), int(min(ys)), int(max(xs)) + 1, int(max(ys)) + 1
    if x0 < 0 or y0 < 0 or x1 >= A.shape[1] or y1 >= A.shape[0]: continue
    m = Image.new('L', (x1 - x0, y1 - y0)); ImageDraw.Draw(m).polygon([(x - x0, y - y0) for x, y in px], fill=1)
    m = np.asarray(m, bool)
    if m.sum() < 6: continue
    b['roof_c'] = [int(v) for v in np.median(A[y0:y1, x0:x1][m], axis=0)]; n += 1
json.dump(BL, open(f'{D}/buildings.json', 'w'))
TM = {k: [float(v) for v in np.asarray(Image.open(f'tex/roof_{k}.png').convert('RGB'), float).reshape(-1, 3).mean(0)] for k in ('metal', 'tile', 'shed', 'solar')}
json.dump(TM, open(f'{D}/roof_tex_mean.json', 'w')); print('roofs measured', n, 'of', len(BL)); print(TM)
