p = 'prep.py'
s = open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'
old = "# buildings" + nl + "BLD = []" + nl
assert s.count(old) == 1
new = old + ("# OSM building:part ways carry the real tower heights (a tower's outline often holds only its podium height)" + nl +
"_PJ = os.path.join(D, 'osm_parts.json')" + nl +
"PARTS = [dict(e, tags=dict(e.get('tags', {}), building='part')) for e in json.load(open(_PJ, encoding='utf-8'))['elements'] if e['type'] == 'way' and 'building' not in e.get('tags', {})] if os.path.exists(_PJ) else []" + nl +
"print('building parts', len(PARTS))" + nl)
s = s.replace(old, new)
old2 = "for el in js:" + nl + "    t = el.get('tags', {})" + nl + "    if el['type'] != 'way' or 'building' not in t: continue"
assert s.count(old2) == 1
s = s.replace(old2, old2.replace("for el in js:", "for el in js + PARTS:"))
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
