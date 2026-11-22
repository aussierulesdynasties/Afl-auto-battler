"""OpenStreetMap round a ground from the OSM main API (Overpass is not reachable from the cloud).
   python3 osm_fetch.py DATA_DIR LAT LON HALF_M
Writes DATA_DIR/osm.json (Overpass 'out geom tags' shape: ways carry 'geometry', relations carry
members with geometry, tree nodes) and DATA_DIR/osm_parts.json (building:part ways), as the scene
pipeline's prep.py reads them. Tiles of ~400 x 600 m are cached in DATA_DIR/osm_tiles.
Data (c) OpenStreetMap contributors, ODbL."""
import sys, os, math, json, time, urllib.request, urllib.error
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
UA = {'User-Agent': 'ground-backdrop-tool/1.0'}

def get_tile(d, b, depth=0):
    f = os.path.join(d, 't_%.5f_%.5f_%.5f_%.5f.xml' % b)
    if os.path.exists(f) and os.path.getsize(f) > 0: return [f]
    url = 'https://api.openstreetmap.org/api/0.6/map?bbox=%.5f,%.5f,%.5f,%.5f' % b
    for i in range(6):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read()
            open(f, 'wb').write(data); return [f]
        except urllib.error.HTTPError as e:
            if e.code == 400 and depth < 4:   # too many nodes: split in four
                x0, y0, x1, y1 = b; xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
                out = []
                for q in ((x0, y0, xm, ym), (xm, y0, x1, ym), (x0, ym, xm, y1), (xm, ym, x1, y1)): out += get_tile(d, q, depth + 1)
                return out
            print('retry', e, url); time.sleep(5 * (i + 1))
        except Exception as e:
            print('retry', e, url); time.sleep(5 * (i + 1))
    raise SystemExit('failed ' + url)

def main(D, lat, lon, half):
    T = os.path.join(D, 'osm_tiles'); os.makedirs(T, exist_ok=True)
    dlat = half / 110540; dlon = half / (111320 * math.cos(math.radians(lat)))
    SX, SY = 0.0045, 0.0055
    boxes = []
    x = lon - dlon
    while x < lon + dlon:
        y = lat - dlat
        while y < lat + dlat:
            boxes.append((x, y, min(x + SX, lon + dlon), min(y + SY, lat + dlat))); y += SY
        x += SX
    with ThreadPoolExecutor(3) as ex: files = sum(ex.map(lambda b: get_tile(T, b), boxes), [])
    nodes, ways, rels = {}, {}, {}
    for f in files:
        r = ET.parse(f).getroot()
        for n in r.iter('node'):
            i = int(n.get('id'))
            if i not in nodes: nodes[i] = (float(n.get('lat')), float(n.get('lon')), {t.get('k'): t.get('v') for t in n.iter('tag')})
        for w in r.iter('way'):
            ways[int(w.get('id'))] = ([int(nd.get('ref')) for nd in w.iter('nd')], {t.get('k'): t.get('v') for t in w.iter('tag')})
        for rl in r.iter('relation'):
            i = int(rl.get('id'))
            mem = [(m.get('type'), int(m.get('ref')), m.get('role')) for m in rl.iter('member')]
            tg = {t.get('k'): t.get('v') for t in rl.iter('tag')}
            if i in rels: mem = list(dict.fromkeys(rels[i][0] + mem))
            rels[i] = (mem, tg)
    def geom(refs): return [{'lat': nodes[r][0], 'lon': nodes[r][1]} if r in nodes else None for r in refs]
    KEYS = ('building', 'landuse', 'leisure', 'natural', 'waterway', 'highway', 'railway', 'amenity', 'building:part', 'bridge', 'man_made')
    els, parts = [], []
    member_ways = {ref for mem, tg in rels.values() if tg.get('type') in ('multipolygon', 'building') for t, ref, ro in mem if t == 'way'}
    for i, (lat_, lon_, tg) in nodes.items():
        if tg.get('natural') == 'tree': els.append({'type': 'node', 'id': i, 'lat': lat_, 'lon': lon_, 'tags': tg})
    for i, (refs, tg) in ways.items():
        g = geom(refs)
        if not any(g): continue
        e = {'type': 'way', 'id': i, 'nodes': refs, 'geometry': g, 'tags': tg}
        if 'building:part' in tg and 'building' not in tg: parts.append(e)
        if any(k in tg for k in KEYS): els.append(e)
    for i, (mem, tg) in rels.items():
        if tg.get('type') == 'building':
            parts.append({'type': 'relation', 'id': i, 'tags': tg, 'members': [{'type': t, 'ref': r, 'role': ro, 'geometry': geom(ways[r][0])} for t, r, ro in mem if t == 'way' and r in ways]})
            continue
        if tg.get('type') != 'multipolygon' or not any(k in tg for k in KEYS): continue
        ms = [{'type': t, 'ref': r, 'role': ro, 'geometry': geom(ways[r][0])} for t, r, ro in mem if t == 'way' and r in ways]
        if ms: els.append({'type': 'relation', 'id': i, 'tags': tg, 'members': ms})
    json.dump({'elements': els}, open(os.path.join(D, 'osm.json'), 'w', encoding='utf-8'))
    json.dump({'elements': parts}, open(os.path.join(D, 'osm_parts.json'), 'w', encoding='utf-8'))
    print('OSM', len(files), 'tiles', len(els), 'elements', len(parts), 'parts')

if __name__ == '__main__':
    main(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]))
