"""A closed ground's surroundings as they were: the OSM snapshot of that date (ohsome_snap.py), plus today's
buildings that the snapshot lacks only because they were mapped later, i.e. whose roof in the era's aerial
(sat_<era>.png) matches today's aerial (sat_now.png). Writes osm.json; today's stays as osm_now.json.
usage: era_merge.py g era_date_tag (e.g. subiaco 2018)"""
import sys, os, json, math, shutil
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon
from shapely.strtree import STRtree
g, tag = sys.argv[1], sys.argv[2]
W = os.environ.get('WORK', '/home/user/work'); D = os.path.join(W, 'data', g); PD = os.path.join(W, 'proto', 'data', g)
spec = json.load(open(os.path.join(W, 'proto', 'spec', g + '.json')))
lat0, lon0 = spec['lat'], spec['lon']; KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
if not os.path.exists(os.path.join(D, 'osm_now.json')): shutil.copy(os.path.join(D, 'osm.json'), os.path.join(D, 'osm_now.json'))
NOW = json.load(open(os.path.join(D, 'osm_now.json')))['elements']
OLD = json.load(open(os.path.join(D, 'osm_%s.json' % tag)))['elements']
for e in OLD:   # tagging since retired: a riverbank or reservoir area is water today
    t = e.get('tags', {})
    if t.get('waterway') == 'riverbank': t.update(natural='water', water='river')
    if t.get('landuse') in ('reservoir', 'basin'): t.update(natural='water')
sj = json.load(open(os.path.join(PD, 'sat.json'))); hm, mp = sj['half_m'], sj['m_per_px']
SA_OLD = np.asarray(Image.open(os.path.join(PD, 'sat_%s.png' % tag)).convert('RGB')).astype(np.float32)
SA_NOW = np.asarray(Image.open(os.path.join(PD, 'sat_now.png')).convert('RGB')).astype(np.float32)
# the two aerials differ in colour cast (Ikon's 2013 release is green-tinted: grey roofs read as plants), so the era's
# is matched to today's per channel (mean and spread over the whole frame) before any colour test
_m = SA_OLD.reshape(-1, 3); _n = SA_NOW.reshape(-1, 3)
SA_OLD = np.clip((SA_OLD - _m.mean(0)) / (_m.std(0) + 1e-6) * _n.std(0) + _n.mean(0), 0, 255)
def poly(el):
    pts = [((p['lon'] - lon0) * KX, (p['lat'] - lat0) * KY) for p in el.get('geometry') or [] if p]
    if len(pts) < 4: return None
    try: q = Polygon(pts).buffer(0)
    except Exception: return None
    return q if q.area > 4 else None
def bld(E): return [(e, poly(e)) for e in E if e['type'] == 'way' and 'building' in e.get('tags', {})]
OB = [(e, q) for e, q in bld(OLD) if q is not None]
tree = STRtree([q for _, q in OB])
def med(SA, q):
    xs, ys = q.exterior.xy
    U = [(x + hm) / mp for x in xs]; V = [(hm - y) / mp for y in ys]
    x0, y0, x1, y1 = int(min(U)), int(min(V)), int(max(U)) + 1, int(max(V)) + 1
    if x0 < 0 or y0 < 0 or x1 >= SA.shape[1] or y1 >= SA.shape[0]: return None
    mk = Image.new('L', (x1 - x0, y1 - y0)); ImageDraw.Draw(mk).polygon([(u - x0, v - y0) for u, v in zip(U, V)], fill=1)
    px = SA[y0:y1, x0:x1][np.asarray(mk) > 0]
    return np.median(px, 0) if len(px) >= 6 else None
def frac(SA, q, paved):
    xs, ys = q.exterior.xy
    U = [(x + hm) / mp for x in xs]; V = [(hm - y) / mp for y in ys]
    x0, y0, x1, y1 = int(min(U)), int(min(V)), int(max(U)) + 1, int(max(V)) + 1
    if x0 < 0 or y0 < 0 or x1 >= SA.shape[1] or y1 >= SA.shape[0]: return None
    mk = Image.new('L', (x1 - x0, y1 - y0)); ImageDraw.Draw(mk).polygon([(u - x0, v - y0) for u, v in zip(U, V)], fill=1)
    px = SA[y0:y1, x0:x1][np.asarray(mk) > 0]
    if len(px) < 6: return None
    R, G, B = px[:, 0], px[:, 1], px[:, 2]; Vv = px.max(1)
    veg = (2 * G - R - B > 12) & (Vv < 170)
    bare = (R - B > 25) & (R - G < 28) & (Vv > 100)
    asph = (px.max(1) - px.min(1) < 18) & (Vv > 55) & (Vv < 135)
    return float((veg | bare | (asph & paved)).mean())
oldids = {e['id'] for e, _ in OB}
keep, drop, late = 0, 0, 0
add = []
for e, q in bld(NOW):
    if e['id'] in oldids or q is None: continue
    hit = any(OB[i][1].intersection(q).area > 0.3 * min(q.area, OB[i][1].area) for i in tree.query(q))
    if hit: continue   # redrawn since: the era's outline stands
    big = q.area >= 1500   # asphalt counts as open ground only under a big block: a house's iron roof reads as asphalt
    fr, fn = frac(SA_OLD, q, big), frac(SA_NOW, q, big)
    if fr is None or fn is None: add.append(e); late += 1; continue   # beyond the era's aerial: nothing to check it against, so it stands
    # built since = open ground then (plants, bare sand, or car-park asphalt under a big block, over 60% of the outline) and not now (under
    # 40%): a new house on a garden lot, the college on the old car park. Open in both years (a shed under backyard
    # trees, a grey roof that reads as asphalt) or roofed in both (a centre rebuilt on its old site) says it stood.
    # House-sized ones always stand: at 0.5 m the two aerials' colour casts and lean flip iron and tiled roofs into
    # "plants" or "sand" one house in ten (checked by eye at Ikon Park, 2013 vs 2026), far more often than a house
    # really went up. A new block on a garden or car park is what changes the skyline, and that test holds.
    stood = not big or not (fr >= 0.6 and fn < 0.4)
    if stood: add.append(e); late += 1
    else: drop += 1
out = OLD + add
json.dump({'elements': out}, open(os.path.join(D, 'osm.json'), 'w'))
print('era', tag, 'old buildings', len(OB), 'late-mapped kept', late, 'built since dropped', drop)
