"""Top-down check of rail_geo against the MCG aerial: beds, rails, portals drawn at true scale over sat.png."""
import json, os, sys, numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rail_geo
D = os.path.join(HERE, 'data', 'mcg', 'prep'); OUT = os.path.join(HERE, 'out', 'mcg', 'rails')
spec = json.load(open(os.path.join(HERE, 'spec', 'mcg.json')))
KF = np.array(json.load(open(os.path.join(D, 'footprint.json')))) if spec.get('rail_cut', {}).get('keep_footprint') else None
pl = rail_geo.plan(json.load(open(os.path.join(D, 'rails.json'))), KF, spec.get('rail_cut', {}).get('keep_ellipse'), json.load(open(os.path.join(D, 'gantries.json'))), json.load(open(os.path.join(D, 'rail_extra.json'))), json.load(open(os.path.join(D, 'rail_shift.json'))))
print('ways', pl['n_ways'], '-> lines', pl['n_merged'], '-> visible runs', len(pl['tracks']), 'portals', len(pl['portals']), 'cantilevers', len(pl['cants']))
L = [np.hypot(*np.diff(Q, axis=0).T).sum() for Q in pl['tracks']]
print('run lengths m: min %.1f median %.1f max %.1f, total %.0f' % (min(L), np.median(L), max(L), sum(L)))
im = Image.open(os.path.join(HERE, 'data', 'mcg', 'sat.png')).convert('RGB'); ov = im.copy(); d = ImageDraw.Draw(ov)
f = lambda p: ((p[0] + 700) / 0.5, (700 - p[1]) / 0.5)
for Q in pl['tracks']:
    T = rail_geo.tangents(Q); N = np.stack([-T[:, 1], T[:, 0]], 1)
    for o, col, w in ((0, (255, 200, 0), 1), (-0.8, (0, 255, 255), 1), (0.8, (0, 255, 255), 1)):
        d.line([f(p) for p in Q + N * o], fill=col, width=w)
    d.ellipse([f(Q[0])[0] - 3, f(Q[0])[1] - 3, f(Q[0])[0] + 3, f(Q[0])[1] + 3], outline=(255, 0, 255))
    d.ellipse([f(Q[-1])[0] - 3, f(Q[-1])[1] - 3, f(Q[-1])[0] + 3, f(Q[-1])[1] + 3], outline=(255, 0, 255))
for a, b, t in pl['portals']: d.line([f(a), f(b)], fill=(255, 0, 0), width=2)
for p, c, t in pl['cants']: d.line([f(p), f(c)], fill=(255, 128, 0), width=2)
ov.save(os.path.join(OUT, 'geo_ovl.png'))
for k, (x0, y0, x1, y1) in {'w': (0, 600, 1100, 1300), 'mid': (900, 1150, 2000, 1850), 'e': (1800, 1700, 2800, 2400), 'n': (300, 0, 2200, 300)}.items():
    ov.crop((x0, y0, x1, y1)).save(os.path.join(OUT, 'geo_%s.png' % k))
json.dump(dict(tracks=[Q.round(2).tolist() for Q in pl['tracks']]), open(os.path.join(OUT, 'plan_tracks.json'), 'w'))
