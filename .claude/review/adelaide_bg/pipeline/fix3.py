import json, math
s = json.load(open('spec/adelaide.json')); lat0, lon0 = s['lat'], s['lon']; KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
js = json.load(open('data/adelaide/osm.json', encoding='utf-8'))['elements']
e = [e for e in js if e.get('id') == 1116828761][0]
ring = [[round((q['lon'] - lon0) * KX, 1), round((q['lat'] - lat0) * KY, 1)] for q in e['geometry']]
P = s['palette']; P['dry_turf'] = [168, 150, 112]; P['court_blue'] = [58, 96, 168]
s['paint_poly'] = [['dry_turf', ring],
                   ['court_blue', [[-255, -120], [-145, -120], [-145, -200], [-255, -200]]],
                   ['lawn', [[-260, -60], [-140, -60], [-140, -118], [-260, -118]]]]
s['roof_col_at'] = [[-80, -185, [150, 82, 70]], [-25, -200, [228, 228, 222]]]
json.dump(s, open('spec/adelaide.json', 'w'), indent=1)
print(len(ring), min(p[0] for p in ring), max(p[0] for p in ring), min(p[1] for p in ring), max(p[1] for p in ring))
p = 'scene.py'; t = open(p, encoding='utf-8', newline='').read()
o = "        rc = roofs[b['roof'] % len(roofs)] * (1 + 0.08 * (rng.random() - 0.5))\n"
n = o + "        for _x, _y, _c in spec.get('roof_col_at', []):   # roof colour read off the aerial for named buildings\n            if math.hypot(cxy[0] - _x, cxy[1] - _y) < 25: rc = lin(_c)\n"
assert o in t and 'roof_col_at' not in t; open(p, 'w', encoding='utf-8', newline='').write(t.replace(o, n, 1))
