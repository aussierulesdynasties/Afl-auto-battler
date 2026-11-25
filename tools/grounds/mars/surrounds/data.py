"""Mars Stadium's surroundings, from open data, 3.8 km a side round the ground.

    python3 tools/grounds/mars/surrounds/data.py OSM_DIR CHM.npy [ESRI_1M.png]

OSM_DIR: OpenStreetMap API map calls over the area (fetch.py writes them). CHM.npy: the Meta/WRI 1 m canopy
height window (fetch.py). ESRI_1M.png (optional, reference only, never committed): a north-up 1 m mosaic
used only to pick each roof's colour from a fixed palette of real roofing colours; without it every roof
takes its kind's commonest colour.

Writes:
  assets/grounds/mars/surrounds.webp  the ground painted from OSM (roads, rail, grass, parks, car parks,
                                      Lake Wendouree), 1.25 m a pixel, read by GroundModels.SURROUNDS
  assets/grounds/mars/trees.bin       every tree: x, z, height, canopy radius, shade (model metres, float32)
  tools/grounds/mars/surrounds/buildings.json  every building footprint with its kind, eave height and
                                      roof/wall colour index, for build_bpy.py to raise with real roofs
Model frame: x east, y north, origin the OSM pitch centroid (work/geo.py); GroundModels' z is -y.
Map data (c) OpenStreetMap contributors, ODbL. Canopy: Meta and WRI, High Resolution Canopy Height Maps,
CC BY 4.0.
"""
import glob, json, math, os, sys
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'work'))
from geo import ll2xy, LAT0, LON0

OUT = os.path.join(HERE, '..', '..', '..', '..', 'assets', 'grounds', 'mars')
RES = 1.25                 # m a pixel
SIZE = 3072                # pixels a side: 3,840 m
HALF = SIZE * RES / 2
MODEL_R = 95.0             # the ring starts here, under the stands; the model draws the stadium

BASE = (122, 128, 86)      # Ballarat's dry-summer verges and backyards (GE Dec 2025)
LAWN = (104, 124, 72)
PITCH = (88, 122, 60)
ASPHALT = (92, 92, 94)
PARKING = (108, 106, 104)
PATH = (168, 162, 148)
PAVED = (150, 148, 142)
BALLAST = (118, 108, 96)
RAIL = (70, 62, 56)
WATER = (58, 78, 88)
URBAN = (126, 126, 112)    # the town past the map's edge
YARD = (112, 120, 84)      # house blocks: lawn, gardens, sheds
WOOD = (74, 92, 56)
BARE = (166, 140, 108)     # earthworks and quarry ground (the workshops' east yard, GE Dec 2025)
TRACK = (52, 92, 160)      # the athletics centre's blue track (Sept 2026 aerial)
CONCOURSE = (158, 156, 150)

WIDTH = {"motorway": 16, "trunk": 14, "primary": 12, "secondary": 11, "tertiary": 9,
         "residential": 7.5, "unclassified": 6, "service": 4.5, "living_street": 5,
         "pedestrian": 4, "footway": 2.0, "path": 1.8, "cycleway": 2.4, "steps": 2.0, "track": 3}

# Real roof colours (Colorbond range and tiles), picked per roof from the reference mosaic.
ROOFS = [(150, 74, 54), (118, 62, 50), (170, 172, 170), (138, 140, 136), (96, 100, 100), (60, 62, 64),
         (214, 212, 200), (112, 80, 64), (86, 98, 80), (66, 80, 98)]
ROOF_NAMES = ['terracotta tile', 'dark red tile', 'zincalume', 'windspray', 'basalt', 'monument', 'surfmist',
              'ironstone', 'cottage green', 'deep ocean']


def load(d):
    nodes, trees, ways, rels, by = {}, [], [], [], {}
    for f in sorted(glob.glob(os.path.join(d, '*.osm'))):
        r = ET.parse(f).getroot()
        for n in r.iter('node'):
            xy = ll2xy(float(n.get('lat')), float(n.get('lon'))); nodes[n.get('id')] = xy
            t = {x.get('k'): x.get('v') for x in n.iter('tag')}
            if t.get('natural') == 'tree': trees.append(xy)
        for w in r.iter('way'):
            if w.get('id') in by: continue
            t = {x.get('k'): x.get('v') for x in w.iter('tag')}
            by[w.get('id')] = ([nd.get('ref') for nd in w.iter('nd')], t)
        for rl in r.iter('relation'):
            t = {x.get('k'): x.get('v') for x in rl.iter('tag')}
            if t.get('type') == 'multipolygon':
                rels.append((t, [(m.get('ref'), m.get('role')) for m in rl.iter('member') if m.get('type') == 'way']))
    pts = lambda refs: [nodes[x] for x in refs if x in nodes]
    for wid, (refs, t) in by.items():
        ways.append((int(wid), t, pts(refs)))
    seen = set()
    for t, mem in rels:
        outer = [pts(by[r][0]) for r, role in mem if r in by and role == 'outer']
        for ring in _join(outer):
            key = (t.get('name'), len(ring))
            if key in seen: continue
            seen.add(key); ways.append((0, t, ring))
    return list(dict.fromkeys(trees)), ways


def _join(parts):
    """outer-member ways joined end to end into closed rings"""
    parts = [list(p) for p in parts if len(p) > 1]; rings = []
    while parts:
        r = parts.pop(0)
        while r[0] != r[-1]:
            for i, p in enumerate(parts):
                if p[0] == r[-1]: r += p[1:]; parts.pop(i); break
                if p[-1] == r[-1]: r += p[::-1][1:]; parts.pop(i); break
            else:
                break
        if r[0] == r[-1] and len(r) > 3: rings.append(r)
    return rings


def px(p):
    return ((p[0] + HALF) / RES, (HALF - p[1]) / RES)


def area_colour(t):
    if t.get('natural') == 'water' or t.get('water') or t.get('leisure') == 'swimming_pool':
        return WATER
    if t.get('amenity') == 'parking':
        return PARKING
    if t.get('sport') in ('athletics', 'running') and t.get('leisure') in ('track', 'pitch', 'sports_centre'):   # not the lake's rowing course
        return TRACK
    if t.get('leisure') == 'pitch' or t.get('leisure') == 'golf_course' or t.get('golf'):
        return PITCH if t.get('golf') not in ('rough',) else LAWN
    if t.get('natural') in ('wood', 'scrub') or t.get('landuse') == 'forest':
        return WOOD
    if t.get('natural') == 'wetland':
        return (86, 104, 70)
    if t.get('landuse') in ('grass', 'meadow', 'recreation_ground', 'cemetery') or t.get('leisure') in ('garden', 'park', 'playground'):
        return LAWN
    if t.get('landuse') == 'railway':
        return BALLAST
    if t.get('landuse') in ('quarry', 'construction', 'brownfield', 'landfill'):
        return BARE
    if t.get('landuse') == 'residential':
        return YARD
    if t.get('landuse') in ('retail', 'commercial', 'industrial') or t.get('area:highway') or t.get('amenity') in ('school', 'hospital'):
        return PAVED
    if t.get('highway') == 'pedestrian' and t.get('area') == 'yes':
        return PAVED
    return None


def _area(p):
    a = np.array(p); return 0.5 * float(np.sum(a[:-1, 0] * a[1:, 1] - a[1:, 0] * a[:-1, 1]))


def paint(ways):
    rng = np.random.default_rng(7)
    n1 = np.asarray(Image.fromarray((rng.random((96, 96)) * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.BICUBIC), float) / 255
    n2 = np.asarray(Image.fromarray((rng.random((384, 384)) * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.BICUBIC), float) / 255
    mott = (n1 - 0.5) * 0.2 + (n2 - 0.5) * 0.12
    im = Image.fromarray(np.clip(np.array(BASE, float) * (1 + mott[..., None]), 0, 255).astype(np.uint8), 'RGB')
    d = ImageDraw.Draw(im)
    poly = lambda p: [px(q) for q in p]
    areas = [(t, p) for _, t, p in ways if len(p) > 3 and p[0] == p[-1] and area_colour(t)]
    areas.sort(key=lambda a: -abs(_area(a[1])))
    for t, p in areas:
        d.polygon(poly(p), fill=area_colour(t))
        if area_colour(t) == TRACK:   # a running track is a 10 m lane ring round a grass infield
            c = np.mean(p[:-1], axis=0); r = np.mean([math.hypot(*(np.subtract(q, c))) for q in p[:-1]])
            d.polygon(poly([tuple(c + (np.subtract(q, c)) * (1 - 10.0 / r)) for q in p]), fill=PITCH)
    for _, t, p in ways:   # rail: ballast bed, then the rails
        if t.get('railway') in ('rail', 'siding', 'yard', 'spur') or (t.get('railway') == 'rail'):
            if len(p) > 1: d.line(poly(p), fill=BALLAST, width=max(2, int(round(4.4 / RES))), joint='curve')
    for _, t, p in ways:
        if t.get('railway') in ('rail', 'siding', 'yard', 'spur') and len(p) > 1:
            d.line(poly(p), fill=RAIL, width=1)
    order = sorted([(WIDTH.get(t.get('highway'), 0), t, p) for _, t, p in ways
                    if t.get('highway') in WIDTH and len(p) > 1 and t.get('tunnel') != 'yes' and t.get('area') != 'yes'],
                   key=lambda a: a[0])
    for w, t, p in order:
        fill = PATH if w < 4.4 else ASPHALT
        if t.get('highway') == 'service' and t.get('service') == 'parking_aisle': fill = PARKING
        d.line(poly(p), fill=fill, width=max(1, int(round(w / RES))), joint='curve')
    arr = np.asarray(im, float)
    arr += ((rng.random((SIZE, SIZE)) - 0.5) * 8)[..., None]
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    r = np.hypot(xx - SIZE / 2, yy - SIZE / 2) * RES
    edge = np.clip((r - (HALF - 40)) / 30, 0, 1)[..., None]
    arr = arr * (1 - edge) + np.array(URBAN, float) * edge
    # the engine lights the ring with the full sun and no shade (GroundModels._add_surrounds): 12 % down so it
    # matches the ground's GE tone in a match render
    return Image.fromarray(np.clip(arr * 0.88, 0, 255).astype(np.uint8), 'RGB')


# ---- trees ----
def chm_trees(chm, osm_trees, keep_out):
    """tree tops from the 1 m canopy height model (local maxima over 3 m, 5 m apart) and every OSM tree the
    canopy model missed; none inside the stadium's own buildings"""
    from scipy import ndimage
    a = chm.astype(float); n = a.shape[0]; res = 2 * HALF_CHM / n
    g = ndimage.gaussian_filter(a, 0.8)
    pk = (g == ndimage.maximum_filter(g, size=5)) & (g > 3.0)
    ys, xs = np.nonzero(pk)
    out = []
    for i, j in zip(ys, xs):
        x = -HALF_CHM + (j + 0.5) * res; y = HALF_CHM - (i + 0.5) * res
        if abs(x) > HALF - 30 or abs(y) > HALF - 30 or keep_out(x, y): continue
        h = float(g[i, j])
        cr = float(np.count_nonzero(a[max(0, i - 6):i + 7, max(0, j - 6):j + 7] > 0.5 * h)) * res * res
        out.append((x, y, h, max(1.5, min(0.55 * h, math.sqrt(cr / math.pi)))))
    have = np.array([(x, y) for x, y, _, _ in out]) if out else np.zeros((0, 2))
    for x, y in osm_trees:
        if abs(x) > HALF - 30 or abs(y) > HALF - 30 or keep_out(x, y): continue
        if len(have) and np.min(np.hypot(have[:, 0] - x, have[:, 1] - y)) < 4.0: continue
        out.append((x, y, 9.0, 3.6))
    return out


HALF_CHM = 1900.0   # fetch.py reads the canopy +-1,900 m round the ground (Web Mercator window, north up)


# ---- buildings ----
def kind(t, area):
    b = t.get('building', 'yes')
    if b in ('house', 'residential', 'detached', 'semidetached_house', 'bungalow'): return 'house'
    if b in ('garage', 'carport', 'shed') or area < 30: return 'shed'
    if b in ('industrial', 'warehouse', 'factory'): return 'industrial'
    if b in ('school', 'commercial', 'retail', 'office', 'hospital', 'church', 'civic', 'public', 'sports_centre', 'university', 'college'): return b if b == 'church' else 'commercial'
    if area > 420: return 'industrial'   # untagged big sheds (the workshops, warehouses): metal gable bays
    return 'house'


def eave(t, k):
    try: return float(t['height'].replace('m', '').strip()) - 1.5
    except (KeyError, ValueError): pass
    try: return float(t['building:levels']) * 3.0
    except (KeyError, ValueError): pass
    return {'house': 2.8, 'shed': 2.3, 'industrial': 6.5, 'commercial': 4.5, 'church': 6.0}[k]


def roof_colour(esri, p, k):
    if esri is None:
        return {'house': 3, 'shed': 2, 'industrial': 2, 'commercial': 3, 'church': 1}[k]
    E = esri.shape[0] / 2; P = [(x + E, E - y) for x, y in p]
    i0, j0 = int(min(q[1] for q in P)) - 2, int(min(q[0] for q in P)) - 2
    i1, j1 = int(max(q[1] for q in P)) + 3, int(max(q[0] for q in P)) + 3
    if i0 < 0 or j0 < 0 or i1 > esri.shape[0] or j1 > esri.shape[1]: return roof_colour(None, p, k)
    m = Image.new('L', (j1 - j0, i1 - i0), 0)
    ImageDraw.Draw(m).polygon([(u - j0, v - i0) for u, v in P], fill=255)
    m = np.asarray(m.filter(ImageFilter.MinFilter(3))) > 0
    if m.sum() < 4: return roof_colour(None, p, k)
    c = np.median(esri[i0:i1, j0:j1][m], axis=0)
    return int(np.argmin([np.sum((np.array(R) - c) ** 2) for R in ROOFS]))


def buildings(ways, esri, keep_out):
    out = []
    for wid, t, p in ways:
        if 'building' not in t or len(p) < 4 or p[0] != p[-1] or t.get('building') in ('roof', 'grandstand'): continue
        q = p[:-1]
        if max(max(abs(x), abs(y)) for x, y in q) > HALF - 20: continue
        cx, cy = np.mean(q, axis=0)
        if keep_out(cx, cy) or wid in (128280661, 1271589372): continue   # the club and its canopy are in the model
        a = abs(_area(p)); k = kind(t, a)
        if a > 8000 and (t.get('leisure') or t.get('amenity')): continue   # a site outline tagged as a building (athletics centre)
        out.append({'id': wid, 'p': [[round(x, 2), round(y, 2)] for x, y in q], 'kind': k, 'eave': round(eave(t, k), 2),
                    'roof': roof_colour(esri, q, k), 'wall': int(abs(hash((round(cx), round(cy)))) % 6)})
    return out


def _inside(P, x, y):
    c = False
    for (x0, y0), (x1, y1) in zip(P, P[1:] + P[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0): c = not c
    return c


def main():
    osm_dir, chm_path = sys.argv[1], sys.argv[2]
    esri = np.asarray(Image.open(sys.argv[3]).convert('RGB'), float) if len(sys.argv) > 3 else None
    trees, ways = load(osm_dir)
    stad = [p for wid, t, p in ways if wid == 1065737814][0]
    keep_out = lambda x, y: math.hypot(x, y) < 112 or (math.hypot(x, y) < 140 and _inside(stad, x, y))
    im = paint(ways)
    d = ImageDraw.Draw(im)   # the stadium precinct inside the model's concourse: the concourse's paving colour
    d.ellipse([px((-MODEL_R, MODEL_R)), px((MODEL_R, -MODEL_R))], fill=CONCOURSE)
    os.makedirs(OUT, exist_ok=True)
    im.save(os.path.join(OUT, 'surrounds.webp'), quality=86, method=6)
    T = chm_trees(np.load(chm_path), trees, keep_out)
    rng = np.random.default_rng(11)
    tb = np.array([(x, -y, h, r, rng.random()) for x, y, h, r in T], '<f4')
    tb.tofile(os.path.join(OUT, 'trees.bin'))
    B = buildings(ways, esri, keep_out)
    json.dump({'source': 'OpenStreetMap contributors (ODbL); roof colours picked from a fixed palette', 'roofs': ROOF_NAMES,
               'buildings': B}, open(os.path.join(HERE, 'buildings.json'), 'w'), separators=(',', ':'))
    print('map', im.size, 'trees', len(tb), 'buildings', len(B))


if __name__ == '__main__':
    main()
