"""Paved surfaces inside commercial / retail / industrial land, read from the straight-down aerial (reference only: the aerial
gives outlines, never pixels on a model). Dark grey = asphalt (-> 'parking', bays + cars), pale grey = concrete (-> 'paved'),
anything else stays 'yard'. Buildings (prep/buildings.json) and OSM roads are cut out. Outlines at the aerial's 0.6 m,
simplified to 0.6 m, holes kept by zero-width bridges. -> data/<g>/prep/aerial_paint.json [[kind, [[x, y], ...]], ...]
python -E aerial_paving.py cazalys"""
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage import measure as ms
g = sys.argv[1]; D = os.path.join('data', g); P = os.path.join(D, 'prep')
spec = json.load(open(os.path.join('spec', g + '.json')))
sj = json.load(open(os.path.join(D, 'sat.json'))); H, M = sj['half_m'], sj['m_per_px']
A = np.asarray(Image.open(os.path.join(D, 'sat.png')).convert('RGB'), np.float32) / 255; N = A.shape[0]
lat0, lon0 = spec['lat'], spec['lon']; KX = 111320 * math.cos(math.radians(lat0)); KY = 110574
def pix(pts): return [((x + H) / M, (H - y) / M) for x, y in pts]
els = json.load(open(os.path.join(D, 'osm.json'), encoding='utf-8'))['elements']
def xy(p): return ((p['lon'] - lon0) * KX, (p['lat'] - lat0) * KY)
# where: commercial land (the zones the cover table used to paint solid 'paved')
zone = Image.new('L', (N, N), 0); zd = ImageDraw.Draw(zone)
for el in els:
    t = el.get('tags', {})
    if t.get('landuse') in ('commercial', 'retail', 'industrial', 'construction'):
        ways = [el.get('geometry')] if el['type'] == 'way' else [m.get('geometry') for m in el.get('members', []) if m.get('role') == 'outer']
        for gm in ways:
            if gm and len(gm) > 2: zd.polygon(pix([xy(p) for p in gm if p]), fill=255)
zone = np.asarray(zone) > 0
# cut: buildings (+0.6 m) and roads (their drawn width + 1 m)
cut = Image.new('L', (N, N), 0); cd = ImageDraw.Draw(cut)
for b in json.load(open(os.path.join(P, 'buildings.json'))):
    cd.polygon(pix(b['p']), fill=255)
WDR = {'motorway': 22, 'trunk': 18, 'primary': 16, 'secondary': 13, 'tertiary': 11, 'residential': 8, 'unclassified': 8, 'service': 5}
for el in els:
    hw = el.get('tags', {}).get('highway')
    if el['type'] == 'way' and hw in WDR and hw != 'service' and el.get('geometry'):   # service lanes inside a lot are part of it
        cd.line(pix([xy(p) for p in el['geometry'] if p]), fill=255, width=max(1, round((WDR[hw] + 1) / M)))
cut = ndi.binary_dilation(np.asarray(cut) > 0, iterations=1)
r, gg, b = A[..., 0], A[..., 1], A[..., 2]; mx = A.max(2); mn = A.min(2); sat = (mx - mn) / np.maximum(mx, 1e-3)
veg = (gg > r * 1.04) & (gg > b * 1.04)
grey = (sat < 0.22) & ~veg
dark = grey & (mx < 0.42) & (mx > 0.10)   # asphalt; below 0.10 is deep shadow
pale = grey & (mx >= 0.42)
k = int(round(3.0 / M))   # 3 m closing: parked cars and line paint fold into the surface they sit on
def clean(m, area):
    m = ndi.binary_closing(m, iterations=k) & zone & ~cut
    m = ndi.binary_opening(m, iterations=2)
    lab, n = ndi.label(m); sz = ndi.sum(m, lab, range(1, n + 1)) * M * M
    return np.isin(lab, 1 + np.nonzero(sz >= area)[0])
pave = clean(dark | pale, 150)
if os.environ.get('DBG'):
    cx,cy,rr=-140,-150,90; sl=(slice(int((H-cy-rr)/M),int((H-cy+rr)/M)),slice(int((cx-rr+H)/M),int((cx+rr+H)/M)))
    Image.fromarray(np.stack([zone[sl],cut[sl],(dark|pale)[sl]],2).astype(np.uint8)*255).resize((900,900)).save('../dbg_ap.png'); sys.exit()
# kind per lot: asphalt when the lot's grey pixels are mostly dark, else concrete
out = []; stats = {}
pale_big = ndi.binary_opening(pale, iterations=int(round(1.5 / M)))   # parked cars (2 x 4.5 m) drop out; open concrete stays
w = int(round(12 / M)); isdark = ndi.uniform_filter(dark.astype(np.float32), w) >= ndi.uniform_filter(pale_big.astype(np.float32), w)
parts = []
for kind, m in (('parking', pave & isdark), ('paved', pave & ~isdark)):
    m = ndi.binary_opening(m, iterations=2); lab, n = ndi.label(m)
    parts += [(kind, lab, i, sl) for i, sl in enumerate(ndi.find_objects(lab), 1)]
for kind, lab0, i, sl in parts:
    mm = lab0[sl] == i
    if mm.sum() * M * M < 100: continue
    cs = []
    for c in ms.find_contours(np.pad(mm, 1).astype(np.float32), 0.5):
        c = ms.approximate_polygon(c, 0.6 / M)
        if len(c) < 4: continue
        rr = c[:, 0] - 1 + sl[0].start; cc = c[:, 1] - 1 + sl[1].start
        q = np.stack([-H + (cc + 0.5) * M, H - (rr + 0.5) * M], 1)[:-1]
        a = abs(np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])) / 2
        if a >= 20: cs.append((a, q))
    if not cs: continue
    cs.sort(key=lambda t: -t[0])
    if cs[0][0] < 100: continue
    ring = cs[0][1]
    for _, h in cs[1:]:   # holes joined by a zero-width bridge so one ring keeps them open
        d = ((ring[:, None] - h[None]) ** 2).sum(2); a_, b_ = np.unravel_index(d.argmin(), d.shape)
        hh = np.roll(h, -b_, 0); ring = np.vstack([ring[:a_ + 1], hh, hh[:1], ring[a_:]])
    out.append([kind, np.round(ring, 2).tolist()]); stats[kind] = stats.get(kind, 0) + cs[0][0] - sum(t[0] for t in cs[1:])
json.dump(out, open(os.path.join(P, 'aerial_paint.json'), 'w'))
gp = os.path.join(P, 'ground.png'); G = Image.open(gp).convert('RGB'); NE = json.load(open(os.path.join(P, 'meta.json')))['near']; gx = G.size[0] / (2 * NE)
gd = ImageDraw.Draw(G); PAL = spec['palette']
for kind, ring in out: gd.polygon([((x + NE) * gx, (NE - y) * gx) for x, y in ring], fill=tuple(PAL[kind]))
G.save(gp)
print('aerial_paint', len(out), {k: round(v) for k, v in stats.items()}, 'm2; zone', round(zone.sum() * M * M), 'm2')
