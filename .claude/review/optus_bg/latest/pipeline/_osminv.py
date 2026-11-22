import json, collections
E = json.load(open('data/optus/osm.json', encoding='utf-8'))['elements']
c = collections.Counter()
for e in E:
    t = e.get('tags', {})
    if e['type'] in ('way', 'relation'):
        for k in ('landuse', 'leisure', 'natural', 'amenity', 'surface', 'highway', 'area:highway', 'place', 'man_made'):
            if k in t: c[(e['type'], k, t[k], t.get('area', ''))] += 1
for k, v in c.most_common(70): print(v, k)
print(len(E), collections.Counter(e['type'] for e in E))
