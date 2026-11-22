# exec'd from prep.py: OSM car roads and water polygons as real surfaces (texture session, 2026-11-20).
# Roads: union of every car road's width, asphalt mesh; white edge lines 0.1 m wide set 0.35 m in from each edge;
# broken centre line (3 m on, 9 m off) on two-way roads. Water: OSM water polygons (outer minus inner) as flat meshes.
import shapely, shapely.prepared
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union, substring
from shapely.strtree import STRtree

CLIP = box(-NEAR + 2, -NEAR + 2, NEAR - 2, NEAR - 2)
RW = {'motorway': 22, 'trunk': 18, 'primary': 16, 'secondary': 13, 'tertiary': 11, 'residential': 8, 'unclassified': 8, 'service': 5}
for k_ in list(RW): RW[k_ + '_link'] = RW[k_] * 0.6
ways = []   # (centreline, width, two_way)
for el in js:
    t = el.get('tags', {})
    if el['type'] != 'way': continue
    if t.get('tunnel', 'no') != 'no' or t.get('location') == 'underground' or t.get('covered') == 'yes': continue
    if t.get('bridge') and t.get('bridge') != 'no': continue
    hw = t.get('highway')
    if hw not in RW or t.get('area') == 'yes': continue
    pts = ring(el)
    if len(pts) < 2: continue
    ways.append((LineString(pts), RW[hw], t.get('oneway', 'no') not in ('yes', '1', '-1') and not hw.startswith('service') and not hw.endswith('_link')))
ROAD = unary_union([w.buffer(wd / 2, cap_style='flat', join_style='round', quad_segs=4) for w, wd, _ in ways]).intersection(CLIP)
# round off the flat ends where two roads meet end to end (flat caps leave notches): add round end caps, re-union
ROAD = unary_union([ROAD] + [shapely.Point(c).buffer(wd / 2, quad_segs=4) for w, wd, _ in ways for c in (w.coords[0], w.coords[-1])]).intersection(CLIP)
ROAD = ROAD.buffer(0.3, quad_segs=2).buffer(-0.3, quad_segs=2)   # close slivers between overlapping strips
EDGE = ROAD.buffer(-0.35, quad_segs=2)
EDGE = (EDGE.buffer(0.05, quad_segs=2).difference(EDGE.buffer(-0.05, quad_segs=2))).intersection(ROAD)
tree_ = STRtree([w for w, _, _ in ways])
dashes = []
for i, (w, wd, two) in enumerate(ways):
    if not two or wd < 8: continue
    others = [ways[j] for j in tree_.query(w.buffer(30)) if j != i]
    keep_out = unary_union([o.buffer(ow / 2 + 1.0) for o, ow, _ in others]) if others else None
    L = w.length; s = 0.0
    while s < L:
        d = substring(w, s, min(s + 3.0, L))
        if keep_out is not None: d = d.difference(keep_out)
        if not d.is_empty: dashes.append(d.buffer(0.05, cap_style='flat'))
        s += 12.0
CEN = unary_union(dashes).intersection(EDGE.envelope).intersection(ROAD.buffer(-0.5)) if dashes else Polygon()
# water: every cover class painted 'water' (ways and multipolygon relations)
wpolys = []
for k, v, pk in CLASS:
    if pk != 'water': continue
    for el in js:
        t = el.get('tags', {})
        if not match(t, k, v): continue
        if el['type'] == 'way':
            pts = ring(el)
            if len(pts) > 3 and pts[0] == pts[-1]: wpolys.append(Polygon(pts).buffer(0))
        elif el['type'] == 'relation':
            outer = [Polygon(r).buffer(0) for r in mp_rings([m for m in el.get('members', []) if m.get('role', 'outer') in ('outer', '') and m.get('geometry')]) if len(r) > 3]
            inner = [Polygon(r).buffer(0) for r in mp_rings([m for m in el.get('members', []) if m.get('role') == 'inner' and m.get('geometry')]) if len(r) > 3]
            if outer: wpolys.append(unary_union(outer).difference(unary_union(inner)) if inner else unary_union(outer))
WATER = unary_union(wpolys).intersection(CLIP) if wpolys else Polygon()
ROAD = ROAD.difference(WATER)   # no road surface on open water (bridges are decks in scene.py)
PW = {'footway': 2.5, 'path': 2.0, 'cycleway': 2.5, 'pedestrian': 6.0}
_pl = []
for el in js:
    t = el.get('tags', {})
    if el['type'] != 'way' or t.get('highway') not in PW or t.get('area') == 'yes': continue
    if t.get('tunnel', 'no') != 'no' or t.get('location') == 'underground' or t.get('covered') == 'yes' or (t.get('bridge') and t.get('bridge') != 'no'): continue
    pts = ring(el)
    if len(pts) > 1: _pl.append(LineString(pts).buffer(PW[t['highway']] / 2, quad_segs=3))
PATH = unary_union(_pl).intersection(CLIP).difference(ROAD.buffer(0.05)).difference(WATER) if _pl else Polygon()
# no footpath over the forecourt paving: the aerial shows the plaza paved edge to edge (fc_overlay alpha)
try:
    import json as _js2; from skimage.measure import find_contours as _fcn
    _fj = _js2.load(open(os.path.join(OUT, 'forecourt.json'))); _fa = np.asarray(Image.open(os.path.join(OUT, 'forecourt.png')))[::10, ::10, 3]
    _fp = [Polygon([(_fj['x0'] + c[1] * 1.0, _fj['y1'] - c[0] * 1.0) for c in cc]) for cc in _fcn(np.pad(_fa, 1).astype(float), 128) if len(cc) > 3]
    _FC = unary_union([q.buffer(0) for q in _fp if q.buffer(0).area > 50])
    _FCi = _FC.buffer(-1.0); PATH = PATH.difference(_FCi); ROAD = ROAD.difference(_FCi); EDGE = EDGE.difference(_FCi); CEN = CEN.difference(_FCi); print("fc clip area", round(_FCi.area))
except Exception as _e: print('fc path clip skipped', _e)
import random as _rnd; _rnd.seed(7)
_cl = []   # irregular reed clumps reaching up to ~0.5 m (some 1 m) into the water, so the shoreline breaks up
for _wp in parts(WATER) if False else getattr(WATER, 'geoms', [WATER]):
    if _wp.is_empty or _wp.area >= 200000: continue
    _ring = _wp.exterior; _s = 0.0
    while _s < _ring.length:
        _pt = _ring.interpolate(_s); _cl.append(_pt.buffer(_rnd.uniform(0.3, 1.1), quad_segs=3)); _s += _rnd.uniform(1.0, 4.0)
_STILL = unary_union([g for g in getattr(WATER, 'geoms', [WATER]) if not g.is_empty and g.area < 200000]) if wpolys else Polygon()
REED = unary_union([WATER.buffer(1.5, quad_segs=3).difference(WATER), _STILL.difference(_STILL.buffer(-0.5)), unary_union(_cl).intersection(_STILL) if _cl else Polygon()]).difference(ROAD).difference(PATH).intersection(CLIP)   # 1.5 m fringe + 0.5 m overlap + clumps on still ponds

def parts(g):
    return [p for p in getattr(g, 'geoms', [g]) if p.geom_type == 'Polygon' and not p.is_empty and p.area > 0.05]
def tri(g, seg):
    """constrained Delaunay mesh of a polygon set; boundaries cut to <= seg m so the drape follows the ground"""
    V, T, idx = [], [], {}
    for p in parts(g):
        p = shapely.segmentize(shapely.set_precision(p, 0.01), seg)
        try: _tg = shapely.constrained_delaunay_triangles(p).geoms
        except Exception:
            p = p.simplify(0.05).buffer(0); _tg = shapely.constrained_delaunay_triangles(p).geoms if p.geom_type == "Polygon" else []
        for tr in _tg:
            c = list(tr.exterior.coords)[:3]; f = []
            for x, y in c:
                key = (round(x, 3), round(y, 3))
                if key not in idx: idx[key] = len(V); V.append(key)
                f.append(idx[key])
            T.append(f)
    return {'v': V, 't': T}
def water_mesh(g):
    out = []
    for p in parts(g):
        bz = [float(height_at(x, y)) for x, y in shapely.segmentize(p.exterior, 10).coords]
        m = tri(p, 10.0); m['z'] = float(min(bz)) - 0.05 if bz else 0.0; m['still'] = p.area < 200000; out.append(m)   # lowest shore point - 5 cm; ponds are still water, the Swan is not   # the water sits at its lowest shore point
    return out
def height_at(x, y):
    i = min(max(int(round((y + NEAR) / NS_)), 0), near.shape[0] - 1); j = min(max(int(round((x + NEAR) / NS_)), 0), near.shape[1] - 1)
    return near[i, j]
NS_ = 2 * NEAR / (near.shape[0] - 1)
SURF = {'path': tri(PATH, 3.0), 'reed': tri(REED, 3.0), 'road': tri(ROAD, 4.0), 'edge': tri(EDGE, 4.0), 'centre': tri(CEN, 4.0), 'water': water_mesh(WATER)}
json.dump(SURF, open(os.path.join(OUT, 'surfaces.json'), 'w'))
print('surfaces: road tris', len(SURF['road']['t']), 'edge', len(SURF['edge']['t']), 'centre', len(SURF['centre']['t']), 'water parts', len(SURF['water']))
