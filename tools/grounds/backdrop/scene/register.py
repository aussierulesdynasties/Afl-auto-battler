"""Find where each ground model sits on the real map: rotate its plan (model_plan.py) and slide it over the
OSM building footprints round the ground until they overlap best. Writes geo/reg.json and an overlay per ground."""
import os, json, math, sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from numpy.fft import rfft2, irfft2
G = json.load(open(os.environ.get('WORK', '/home/user/work') + '/geo/grounds.json'))
N = 700; out = json.load(open(os.environ.get('WORK', '/home/user/work') + '/geo/reg.json')) if len(sys.argv) > 2 else {}
for g in (sys.argv[1:2] if len(sys.argv) > 1 and sys.argv[1] != 'all' else G):
    lat, lon = G[g]; KX = 111320 * math.cos(math.radians(lat)); KY = 110540
    els = json.load(open(os.environ.get('WORK', '/home/user/work') + '/data/%s/osm.json' % g))['elements']
    B = Image.new('L', (N, N), 0); d = ImageDraw.Draw(B)
    def px(q): return ((q['lon'] - lon) * KX + N / 2, N / 2 - (q['lat'] - lat) * KY)
    for e in els:
        t = e['tags']
        if 'building' in t or t.get('leisure') == 'stadium' and False:
            if e['type'] == 'way':
                pts = [px(q) for q in e['geometry'] if q]
                if len(pts) > 2: d.polygon(pts, fill=255)
            else:
                for m in e.get('members', []):
                    if m['role'] == 'outer':
                        pts = [px(q) for q in m['geometry'] if q]
                        if len(pts) > 2: d.polygon(pts, fill=255)
    B = np.asarray(B) > 0
    P = np.load(os.environ.get('WORK', '/home/user/work') + '/geo/plan_%s.npy' % g).astype(np.float32)
    BF = rfft2(B.astype(np.float32), s=(2 * N, 2 * N))
    best = None
    for yaw in np.arange(0, 360, 1.0):
        R = ndimage.rotate(P, yaw, reshape=False, order=0)   # positive = counter-clockwise on the map
        c = irfft2(BF * np.conj(rfft2(R, s=(2 * N, 2 * N))))
        c = np.roll(np.roll(c, 300, 0), 300, 1)[:600, :600]   # shifts -300..299
        i = np.unravel_index(np.argmax(c), c.shape); s = c[i] / math.sqrt(R.sum() * max(B.sum(), 1))
        if best is None or s > best[0]: best = (s, yaw, i[1] - 300, i[0] - 300, R)
    s, yaw, dx, dy, R = best
    # model origin on the map: image centre shifted by (dx, dy) px; east = dx, north = -dy
    oe, on = float(dx), float(-dy)
    out[g] = dict(score=round(float(s), 3), yaw=float(yaw), origin=[round(lat + on / KY, 7), round(lon + oe / KX, 7)], cover=int(P.sum()))
    print('%-14s score %.2f yaw %5.1f shift e %4d n %4d' % (g, s, yaw if yaw <= 180 else yaw - 360, dx, -dy), flush=True)
    im = np.zeros((N, N, 3), np.uint8); im[B] = (90, 90, 200); Rs = np.roll(np.roll(R, dy, 0), dx, 1) > 0; im[Rs] += np.array((150, 120, 0), np.uint8)
    Image.fromarray(im).save(os.environ.get('WORK', '/home/user/work') + '/geo/reg_%s.png' % g)
json.dump(out, open(os.environ.get('WORK', '/home/user/work') + '/geo/reg.json', 'w'), indent=1)
