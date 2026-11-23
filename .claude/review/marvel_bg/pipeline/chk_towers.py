import json, math, collections
BL = json.load(open('data/marvel/prep/buildings.json'))
print(BL[0].keys())
C = collections.Counter()
for b in BL:
    if b['c'] != 'tower': continue
    P = b.get('p') or b.get('pts')
    x = sum(p[0] for p in P) / len(P); y = sum(p[1] for p in P) / len(P)
    if math.hypot(x, y) > 800: continue
    C[(b.get('k'), b.get('mat'), b.get('col'))] += 1
for k, v in C.most_common(25): print(v, k)
for b in BL:
    if b['c'] == 'tower' and b['k'] == 'apartments':
        P = b['p']; x = sum(p[0] for p in P) / len(P); y = sum(p[1] for p in P) / len(P)
        if 250 < math.hypot(x, y) < 450: print('T', round(x), round(y), b['h']); break
