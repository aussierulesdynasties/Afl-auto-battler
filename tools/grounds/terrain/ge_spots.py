"""Pick open road spots round a ground for the Google Earth height check (proof/), from OpenStreetMap.

    python3 ge_spots.py <slug> [count]   -> JSON [[name, east_m, north_m], ...] on stdout

Spots are midpoints of road segments (not bridges, tunnels or ramps) 150 to 500 m from the centre
circle, one per sector round it, plus the centre circle itself (the turf, the datum). Map data
(c) OpenStreetMap contributors, ODbL."""
import json, math, sys, urllib.request
import terrain

ROADS = {'primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'living_street'}


def spots(slug, count=8):
    g = terrain.grounds()[slug]
    lat0, lon0 = g['lat'], g['lon']
    kx = 111320.0 * math.cos(math.radians(lat0)); ky = 110574.0
    d = 520.0
    bbox = (lon0 - d / kx, lat0 - d / ky, lon0 + d / kx, lat0 + d / ky)
    url = 'https://api.openstreetmap.org/api/0.6/map.json?bbox=%f,%f,%f,%f' % bbox
    req = urllib.request.Request(url, headers={'User-Agent': 'afl-ground-builder/1.0'})
    js = json.load(urllib.request.urlopen(req, timeout=180))
    nodes = {e['id']: ((e['lon'] - lon0) * kx, (e['lat'] - lat0) * ky) for e in js['elements'] if e['type'] == 'node'}
    cands = []
    for e in js['elements']:
        t = e.get('tags', {})
        if e['type'] != 'way' or t.get('highway') not in ROADS: continue
        if any(t.get(k) not in (None, 'no') for k in ('bridge', 'tunnel', 'covered')) or t.get('layer', '0') != '0': continue
        pts = [nodes[n] for n in e['nodes'] if n in nodes]
        for a, b in zip(pts, pts[1:]):
            if math.hypot(b[0] - a[0], b[1] - a[1]) < 25: continue
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); r = math.hypot(*m)
            if 150 <= r <= 500: cands.append(m)
    out = [['c00', 0.0, 0.0]]
    for k in range(count):
        lo = 2 * math.pi * k / count; hi = 2 * math.pi * (k + 1) / count
        sec = [m for m in cands if lo <= math.atan2(m[1], m[0]) % (2 * math.pi) < hi]
        if not sec: continue
        best = min(sec, key=lambda m: abs(math.hypot(*m) - 300))
        out.append([f's{k:02d}', round(best[0], 1), round(best[1], 1)])
    return out


if __name__ == '__main__':
    print(json.dumps(spots(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 8)))
