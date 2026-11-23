"""Pool check board: satellite crop | scene ortho | blend, model outlines drawn; table of pool L x W x heading
from satellite water blobs vs model OSM pools. usage: poolboard.py proto_dir top.png out.png  (frame centre -165,-160, 200 m)"""
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
P = sys.argv[1]; CX, CY, Wm = -165.0, -160.0, 200.0
Image.MAX_IMAGE_PIXELS = None
S = Image.open(os.path.join(P, 'data/gmhba/sat.png')).convert('RGB'); sj = json.load(open(os.path.join(P, 'data/gmhba/sat.json')))
h, mp = sj['half_m'], sj['m_per_px']
box = ((CX - Wm / 2 + h) / mp, (h - CY - Wm / 2) / mp, (CX + Wm / 2 + h) / mp, (h - CY + Wm / 2) / mp)
Sc = S.crop(tuple(int(round(b)) for b in box)).resize((1000, 1000), Image.LANCZOS)
T = Image.open(sys.argv[2]).convert('RGB').resize((1000, 1000))
k = 1000 / Wm
def px(x, y): return ((x - CX) * k + 500, 500 - (y - CY) * k)
spec = json.load(open(os.path.join(P, 'spec/gmhba.json'))); la0, lo0 = spec['lat'], spec['lon']; KX = 111320 * math.cos(math.radians(la0))
pools = []
for e in json.load(open(os.path.join(P, 'data/gmhba/osm.json'), encoding='utf-8'))['elements']:
    if e.get('type') != 'way' or e.get('tags', {}).get('leisure') != 'swimming_pool' or not e.get('geometry'): continue
    A = np.array([((g['lon'] - lo0) * KX, (g['lat'] - la0) * 110540) for g in e['geometry'] if g])
    m = A.mean(0)
    if abs(m[0] - CX) < Wm / 2 and abs(m[1] - CY) < Wm / 2: pools.append((e['id'], A))
def rect(A):
    best = None
    for i in range(len(A) - 1):
        d = A[i + 1] - A[i]; n = np.hypot(*d)
        if n < 1e-6: continue
        u = d / n; v = np.array([-u[1], u[0]]); a, b = A @ u, A @ v; ar = np.ptp(a) * np.ptp(b)
        if best is None or ar < best[0]: best = (ar, np.ptp(a), np.ptp(b), math.degrees(math.atan2(u[1], u[0])))
    _, L, W, hd = best
    if W > L: L, W, hd = W, L, hd + 90
    return L, W, hd % 180
# satellite water: bright cyan/blue pixels, connected blobs > 20 m2
a = np.asarray(Sc).astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
wm = (b > 150) & (b > r + 25) & (g > r + 10)
lab = np.zeros(wm.shape, int); nl = 0
from collections import deque
for y0, x0 in zip(*np.nonzero(wm)):
    if lab[y0, x0]: continue
    nl += 1; q = deque([(y0, x0)]); lab[y0, x0] = nl
    while q:
        y, x = q.popleft()
        for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= yy < 1000 and 0 <= xx < 1000 and wm[yy, xx] and not lab[yy, xx]: lab[yy, xx] = nl; q.append((yy, xx))
blobs = []
for i in range(1, nl + 1):
    ys, xs = np.nonzero(lab == i)
    if len(xs) / k / k < 20: continue
    X = np.stack([xs / k + CX - 500 / k, CY + (500 - ys) / k], 1)
    # hull for rect fit
    Xs = X[np.lexsort((X[:, 1], X[:, 0]))]
    def half(pts):
        hl = []
        for p in pts:
            while len(hl) >= 2 and ((hl[-1][0] - hl[-2][0]) * (p[1] - hl[-2][1]) - (hl[-1][1] - hl[-2][1]) * (p[0] - hl[-2][0])) <= 0: hl.pop()
            hl.append(p)
        return hl
    H = np.array(half(Xs)[:-1] + half(Xs[::-1])[:-1]); H = np.vstack([H, H[:1]])
    blobs.append((X.mean(0), len(xs) / k / k, rect(H)))
rows = []
for pid, A in pools:
    L, W, hd = rect(A); c = A.mean(0)
    near = min(blobs, key=lambda bb: np.hypot(*(bb[0] - c))) if blobs else None
    d = np.hypot(*(near[0] - c)) if near else 99
    rows.append((pid, c, (L, W, hd), near[2] if near and d < 12 else None, d))
D = Image.blend(T, Sc, 0.5)
for im in (Sc, T, D):
    dr = ImageDraw.Draw(im)
    for pid, A in pools: dr.line([px(*p) for p in A] + [px(*A[0])], fill=(255, 40, 40), width=3)
board = Image.new('RGB', (3000, 1000 + 40 + 30 * (len(rows) + 2)), (20, 20, 20))
for i, im in enumerate((Sc, T, D)): board.paste(im, (i * 1000, 40))
dr = ImageDraw.Draw(board)
dr.text((10, 10), 'Esri satellite (spec origin -38.1579976,144.3546774)  |  scene ortho, md5 b68541441d07655ce15d598e1c1d841c  |  50/50 blend.  Red = model pool outlines (OSM)', fill=(255, 255, 255))
y = 1050; dr.text((10, y), 'pool id        centre(x,y)     MODEL L x W m  heading   |  SATELLITE L x W m  heading   | dL dW  verdict', fill=(255, 255, 0))
for pid, c, mo, sa, d in rows:
    y += 30
    if sa:
        ok = abs(mo[0] - sa[0]) <= 2.0 and abs(mo[1] - sa[1]) <= 2.0 and min(abs(mo[2] - sa[2]), 180 - abs(mo[2] - sa[2])) <= 5
        t = '%-12s (%5.0f,%5.0f)  %5.1f x %5.1f  %5.1f   |  %5.1f x %5.1f  %5.1f   | %+.1f %+.1f  %s' % (pid, c[0], c[1], mo[0], mo[1], mo[2], sa[0], sa[1], sa[2], mo[0] - sa[0], mo[1] - sa[1], 'MATCH' if ok else 'FAIL')
    else:
        t = '%-12s (%5.0f,%5.0f)  %5.1f x %5.1f  %5.1f   |  no water blob within 12 m  | FAIL (check by eye)' % (pid, c[0], c[1], *mo)
    dr.text((10, y), t, fill=(255, 255, 255)); print(t)
print('sat blobs', [(round(b[0][0]), round(b[0][1]), round(b[1])) for b in blobs])
board.save(sys.argv[3])
