import json
s = open('scene.py', encoding='utf-8', newline='').read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:60], s.count(a)); s = s.replace(a, b)
rep("""            if len(g) > 3: polys.append(np.array(g))
    polys += [np.array(p, float) for k, p in spec.get('paint_poly', []) if k == 'parking']""",
"""            if len(g) > 3 and str(el['id']) not in spec.get('park_skip', []): polys.append(np.array(g)); PFILL.append(spec.get('park_fill', {}).get(str(el['id']), 0.35))
    for k, p in spec.get('paint_poly', []):
        if k == 'parking': polys.append(np.array(p, float)); PFILL.append(0.35)""")
rep("    polys = []\n    for el in els:", "    polys = []; PFILL = []   # car fill per car park, copied from the aerial\n    for el in els:")
rep("    for poly in polys:\n        a = _ang(poly); ca, sa", "    for poly, fill in zip(polys, PFILL):\n        a = _ang(poly); ca, sa")
rep("crng.random(len(X_)) < 0.55)", "crng.random(len(X_)) < fill)")
open('scene.py', 'w', encoding='utf-8', newline='').write(s)
p = 'spec/peoplefirst.json'; d = json.load(open(p))
d['paint_poly'] = [['paved', [[-140, 70], [-115, 92], [-60, 95], [0, 95], [50, 100], [85, 85], [100, 40], [110, -20], [150, -55], [165, -95], [158, -113], [110, -107], [41, -117], [0, -125], [-60, -150], [-105, -120], [-115, -60], [-120, 20]]]]
d['park_skip'] = ['355376897']                       # OSM calls it parking; the aerial shows a tree plaza
d['park_fill'] = {'355376917': 0.35, '355377203': 0.05, '52868467': 0.3}
json.dump(d, open(p, 'w')); print('ok')
