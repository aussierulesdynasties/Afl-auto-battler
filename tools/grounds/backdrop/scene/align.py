"""Real oval (OSM AFL/cricket pitch nearest the centre) vs the model's FIT ellipse."""
import os, json, math, re, sys
import numpy as np
G = json.load(open(os.environ.get('WORK', '/home/user/work') + '/geo/grounds.json'))
src = open(os.environ.get('REPO', '/home/user/Afl-auto-battler') + '/scripts/ui/match/GroundModels.gd').read()
FIT = {m[0]: [float(v) for v in m[1].split(',')] for m in re.findall(r'"(\w+)": \[([-\d., ]+)\],', src.split('const FIT')[1].split('}')[0])}
out = {}
for g, (lat, lon) in G.items():
    try: els = json.load(open(os.environ.get('WORK', '/home/user/work') + '/data/%s/osm.json' % g))['elements']
    except FileNotFoundError: continue
    KX = 111320 * math.cos(math.radians(lat)); KY = 110540
    best = None
    for e in els:
        t = e['tags']
        if e['type'] != 'way' or t.get('leisure') not in ('pitch', 'stadium'): continue
        if t.get('leisure') == 'pitch' and not re.search('australian_football|cricket', t.get('sport', '')): continue
        p = np.array([((q['lon'] - lon) * KX, (q['lat'] - lat) * KY) for q in e['geometry'] if q])
        if len(p) < 8: continue
        c = p.mean(0); span = np.ptp(p, 0).max()
        q_ = p - c; w_, v_ = np.linalg.eigh(np.cov(q_.T)); pr = q_ @ v_
        L_, W_ = np.ptp(pr[:, 1]) / 2, np.ptp(pr[:, 0]) / 2
        if not (65 < L_ < 115 and 50 < W_ < 95 and L_ / W_ > 1.08): continue
        d = np.hypot(*c)
        if d < 300 and (best is None or d < best[0]): best = (d, c, p, t)
    if best is None: print(g, 'no pitch'); continue
    d, c, p, t = best
    q = p - c; w, v = np.linalg.eigh(np.cov(q.T)); ax = v[:, 1]
    th = math.degrees(math.atan2(ax[1], ax[0]))  # ccw from east
    proj = q @ v; L = np.ptp(proj[:, 1]) / 2; Wd = np.ptp(proj[:, 0]) / 2
    fit_geo = -FIT[g][3] if g in FIT else None   # model angle as ccw-from-east if model is north-up
    dif = ((th - fit_geo + 90) % 180) - 90 if fit_geo is not None else None
    out[g] = dict(c=[round(c[0], 1), round(c[1], 1)], th=round(th, 1), half=[round(L, 1), round(Wd, 1)], fit=FIT.get(g), diff=round(dif, 1) if dif is not None else None)
    print('%-14s centre off %5.1f m  real axis %6.1f  half %5.1f x %5.1f   model half %5.1f x %5.1f  axis diff %6.1f' % (g, d, th, L, Wd, FIT[g][4], FIT[g][5], dif))
json.dump(out, open(os.environ.get('WORK', '/home/user/work') + '/geo/align.json', 'w'), indent=1)
