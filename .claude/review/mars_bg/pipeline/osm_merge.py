"""Merge data/<g>/osm_water.json into osm.json: relations become closed ways (outer members stitched into rings); inner rings are
emitted after them with a land tag so they paint back over the water. Keeps osm_orig.json."""
import sys, json, os, shutil
D = 'data/%s/' % sys.argv[1]
if not os.path.exists(D + 'osm_orig.json'): shutil.copy(D + 'osm.json', D + 'osm_orig.json')
base = json.load(open(D + 'osm_orig.json', encoding='utf-8'))
add = json.load(open(D + 'osm_water.json', encoding='utf-8'))['elements']
ids = {(e['type'], e['id']) for e in base['elements']}
els = [e for e in base['elements'] if not (e['type'] == 'relation' and (e['type'], e['id']) in {(a['type'], a['id']) for a in add})]
def stitch(segs):
    segs = [[(p['lat'], p['lon']) for p in s if p] for s in segs]; rings = []
    while segs:
        r = segs.pop(0)
        while r[0] != r[-1]:
            for i, s in enumerate(segs):
                if s[0] == r[-1]: r += s[1:]; segs.pop(i); break
                if s[-1] == r[-1]: r += s[::-1][1:]; segs.pop(i); break
            else: break
        if len(r) > 3: rings.append(r + ([r[0]] if r[0] != r[-1] else []))
    return rings
nid = -1; inner = []
for a in add:
    if a['type'] == 'way':
        if ('way', a['id']) not in ids: els.append(a)
        continue
    t = a.get('tags', {})
    for role, out in (('outer', els), ('inner', inner)):
        if role == 'inner' and t.get('natural') != 'water' and t.get('waterway') != 'riverbank': continue   # a park's hole (the lake) is not an island
        for r in stitch([m['geometry'] for m in a.get('members', []) if m.get('role') == role and m.get('geometry')]):
            tg = dict(t) if role == 'outer' else {'landuse': 'island_fill'}
            out.append({'type': 'way', 'id': nid, 'tags': tg, 'geometry': [{'lat': la, 'lon': lo} for la, lo in r]}); nid -= 1
base['elements'] = els + inner
json.dump(base, open(D + 'osm.json', 'w', encoding='utf-8')); print('merged', len(add), 'rings', -nid - 1, 'inner', len(inner))
