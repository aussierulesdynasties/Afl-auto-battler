"""OSM ways whose any segment passes within R m of (x, y). osm_seg.py g x y R"""
import sys, json, math
g = sys.argv[1]; X, Y, R = map(float, sys.argv[2:5])
spec = json.load(open(f'spec/{g}.json')); lat0, lon0 = spec['lat'], spec['lon']
KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
d = json.load(open(f'data/{g}/osm.json', encoding='utf-8'))['elements']
def dist(p, a, b):
    ax, ay = a; bx, by = b; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)
for e in d:
    if e['type'] != 'way' or 'geometry' not in e: continue
    pts = [((q['lon'] - lon0) * KX, (q['lat'] - lat0) * KY) for q in e['geometry'] if q]
    if any(dist((X, Y), a, b) < R for a, b in zip(pts, pts[1:])):
        print(e['id'], e.get('tags', {}))
