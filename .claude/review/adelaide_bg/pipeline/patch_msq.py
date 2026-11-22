import json, shutil
H = 'D:/Temp/claude/b012626c2f559e8f/6855d913-d54b-43b8-92a6-1e4e1b34589b/scratchpad/proto/'
s = open(H + 'prep.py', newline='').read(); nl = '\r\n' if '\r\n' in s else '\n'
a = "json.dump(BLD, open(os.path.join(OUT, 'buildings.json'), 'w'))"
assert s.count(a) == 1
shutil.copy(H + 'prep.py', H + 'prep.py.bak_msq')
b = "for _p, _h in spec.get('extra_buildings', []):   # towers newer than OSM, traced on the aerial, height from published source" + nl + \
    "    BLD.append(dict(p=_p, h=_h, c='tower', roof=1, wall=int(rng.integers(0, len(PAL['walls_tower'])))))" + nl + a
open(H + 'prep.py', 'w', newline='').write(s.replace(a, b))
sp = json.load(open(H + 'spec/adelaide.json'))
shutil.copy(H + 'spec/adelaide.json', H + 'spec/adelaide.json.bak_msq')
sp['extra_buildings'] = [[[[140, -1525], [195, -1525], [195, -1485], [140, -1485]], 133.2]]   # Market Square North, 133.2 m (Wikipedia list), footprint off the aerial
json.dump(sp, open(H + 'spec/adelaide.json', 'w'), indent=1)
print('ok')
