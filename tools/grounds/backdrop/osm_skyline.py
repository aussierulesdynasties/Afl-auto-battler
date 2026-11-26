"""Tall buildings round a ground from OpenStreetMap, for the backdrop's skyline (row 202 2b).
   python3 osm_skyline.py fetch OUTDIR LON_MIN LAT_MIN LON_MAX LAT_MAX   # tiles from the OSM main API
   python3 osm_skyline.py parse OUTDIR LAT0 LON0 skyline.json [min_h]     # footprints in metres
Coordinates are metres east and north of (LAT0, LON0), the oval's centre: the frame of the
ground's scene.blend. Buildings shorter than min_h (30 m) are left out. Where a building is drawn
as parts (building:part), its outline is dropped, as OSM 3D renderers do.
Data (c) OpenStreetMap contributors, ODbL (docs/DATA_SOURCES.md).
"""
import sys, os, math, json, re, time, glob, urllib.request
import xml.etree.ElementTree as ET

STEP_LON, STEP_LAT = 0.0045, 0.0055   # about 400 x 600 m: well under the API's 50,000 nodes

def fetch(out, x0, y0, x1, y1):
    os.makedirs(out, exist_ok=True)
    lon = x0
    while lon < x1:
        lat = y0
        while lat < y1:
            f = os.path.join(out, 't_%.4f_%.4f.xml' % (lon, lat))
            if not os.path.exists(f):
                url = 'https://api.openstreetmap.org/api/0.6/map?bbox=%.4f,%.4f,%.4f,%.4f' % (
                    lon, lat, min(lon + STEP_LON, x1), min(lat + STEP_LAT, y1))
                req = urllib.request.Request(url, headers={'User-Agent': 'ground-backdrop-tool/1.0'})
                open(f, 'wb').write(urllib.request.urlopen(req, timeout=120).read())
                time.sleep(1.0)
            lat += STEP_LAT
        lon += STEP_LON

def num(v):
    try: return float(re.findall(r'[\d.]+', v)[0])
    except (TypeError, IndexError): return None

def height(t):
    h = num(t.get('height') or t.get('building:height'))
    if h is None and t.get('building:levels'):
        lv = num(t['building:levels'])
        h = lv * 3.4 + 2 if lv is not None else None
    return h

def inside(x, y, p):
    c = False
    for i in range(len(p)):
        (ax, ay), (bx, by) = p[i], p[i - 1]
        if (ay > y) != (by > y) and x < ax + (bx - ax) * (y - ay) / (by - ay): c = not c
    return c

def parse(src, lat0, lon0, dst, min_h=30.0):
    kx = 111320 * math.cos(math.radians(lat0)); ky = 110540
    nodes, ways, rels = {}, {}, []
    for f in glob.glob(os.path.join(src, 't_*.xml')):
        r = ET.parse(f).getroot()
        for n in r.iter('node'): nodes[n.get('id')] = (float(n.get('lon')), float(n.get('lat')))
        for w in r.iter('way'):
            ways[w.get('id')] = ([nd.get('ref') for nd in w.iter('nd')], {t.get('k'): t.get('v') for t in w.iter('tag')})
        for rl in r.iter('relation'):
            t = {x.get('k'): x.get('v') for x in rl.iter('tag')}
            if t.get('type') == 'multipolygon' and ('building' in t or 'building:part' in t):
                rels.append((t, [m.get('ref') for m in rl.iter('member') if m.get('type') == 'way' and m.get('role') == 'outer']))
    out = []
    def add(ids, t):
        if any(i not in nodes for i in ids): return
        h = height(t)
        if h is None or h < min_h: return
        p = [((nodes[i][0] - lon0) * kx, (nodes[i][1] - lat0) * ky) for i in ids]
        if p[0] == p[-1]: p = p[:-1]
        if len(p) < 3: return
        cx = sum(q[0] for q in p) / len(p); cy = sum(q[1] for q in p) / len(p)
        out.append({'p': [[round(a, 2), round(b, 2)] for a, b in p], 'h': h, 'min': num(t.get('min_height')) or 0.0,
                    'r': math.hypot(cx, cy), 'c': (cx, cy), 'part': 'building:part' in t, 'name': t.get('name', '')})
    for ids, t in ways.values():
        if 'building' in t or 'building:part' in t: add(ids, t)
    for t, outer in rels:
        for w in outer:
            if w in ways: add(ways[w][0], t)
    seen, res = set(), []
    for b in out:   # a way read from two tiles is the same building
        k = (round(b['c'][0]), round(b['c'][1]), round(b['h']), b['min'])
        if k not in seen: seen.add(k); res.append(b)
    parts = [b for b in res if b['part']]
    res = [b for b in res if b['part'] or not any(inside(*q['c'], b['p']) for q in parts)]
    for b in res: del b['c']
    json.dump(res, open(dst, 'w'))
    print(len(res), 'buildings of', min_h, 'm or more; tallest', max(b['h'] for b in res))

if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'fetch': fetch(a[1], *map(float, a[2:6]))
    else: parse(a[1], float(a[2]), float(a[3]), a[4], float(a[5]) if len(a) > 5 else 30.0)
