"""Pitch-anchored placement: the model's fence centre goes on the real oval's centre (OSM pitch), its long axis on
the real one's (either way round, +-12 deg); the stands' plan picks the way round and the fine turn by overlap with
OSM buildings. Grounds without a mapped pitch keep the free fit (register.py) when it moved under 60 m."""
import os, json, math, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
G = json.load(open(os.environ.get('WORK', '/home/user/work') + '/geo/grounds.json')); A = json.load(open(os.environ.get('WORK', '/home/user/work') + '/geo/align.json')); R0 = json.load(open(os.environ.get('WORK', '/home/user/work') + '/geo/reg.json'))
N = 700; out = {}
for g in G:
    lat, lon = G[g]; KX = 111320 * math.cos(math.radians(lat)); KY = 110540
    els = json.load(open(os.environ.get('WORK', '/home/user/work') + '/data/%s/osm.json' % g))['elements']
    B = Image.new('L', (N, N), 0); d = ImageDraw.Draw(B)
    def px(q): return ((q['lon'] - lon) * KX + N / 2, N / 2 - (q['lat'] - lat) * KY)
    for e in els:
        if 'building' in e['tags']:
            for ring in ([e['geometry']] if e['type'] == 'way' else [m['geometry'] for m in e.get('members', []) if m['role'] == 'outer']):
                pts = [px(q) for q in ring if q]
                if len(pts) > 2: d.polygon(pts, fill=255)
    B = np.asarray(B) > 0
    P = np.load(os.environ.get('WORK', '/home/user/work') + '/geo/plan_%s.npy' % g).astype(np.float32)
    a = A.get(g)
    if a is None:
        r = R0[g]; s_e = (r['origin'][1] - lon) * KX; s_n = (r['origin'][0] - lat) * KY
        if math.hypot(s_e, s_n) < 60: out[g] = dict(origin=r['origin'], yaw=r['yaw'] if r['yaw'] <= 180 else r['yaw'] - 360, how='free fit', score=r['score'])
        else: out[g] = dict(origin=[lat, lon], yaw=0.0, how='guess (no pitch, free fit moved %.0f m)' % math.hypot(s_e, s_n), score=0)
        print(g, out[g]); continue
    fx, fz = a['fit'][0], a['fit'][1]; ce, cn = a['c']; best = None; fam = {}
    for base in (a['diff'], a['diff'] + 180):
        for yaw in np.arange(base - 12, base + 12.01, 1.0):
            Rm = ndimage.rotate(P, yaw, reshape=False, order=0) > 0
            r = math.radians(yaw); e_ = fx * math.cos(r) + fz * math.sin(r); n_ = fx * math.sin(r) - fz * math.cos(r)
            for dx in range(-6, 7, 2):
                for dy in range(-6, 7, 2):
                    sx = int(round(ce - e_)) + dx; sy = int(round(-(cn - n_))) + dy
                    Rs = np.roll(np.roll(Rm, sy, 0), sx, 1)
                    s = (Rs & B).sum() / math.sqrt(Rm.sum() * max(B.sum(), 1))
                    if best is None or s > best[0]: best = (s, yaw, sx, sy, Rs)
                    k = base == a['diff']; fam[k] = max(fam.get(k, 0), s)
    s, yaw, sx, sy, Rs = best
    yaw = ((yaw + 180) % 360) - 180
    out[g] = dict(origin=[round(lat - sy / KY, 7), round(lon + sx / KX, 7)], yaw=float(yaw), how='pitch', score=round(float(s), 3), flip_scores=[round(float(fam[True]), 3), round(float(fam[False]), 3)])
    print('%-14s yaw %6.1f  shift e %4d n %4d  score %.2f  (as-is %.2f / turned 180 %.2f)' % (g, yaw, sx, -sy, s, fam[True], fam[False]), flush=True)
    im = np.zeros((N, N, 3), np.uint8); im[B] = (90, 90, 200); im[Rs] += np.array((150, 120, 0), np.uint8)
    Image.fromarray(im).save(os.environ.get('WORK', '/home/user/work') + '/geo/reg2_%s.png' % g)
json.dump(out, open(os.environ.get('WORK', '/home/user/work') + '/geo/place.json', 'w'), indent=1)
