"""intersect a photo ray with the west stand's outer wall (vertical faces): wallray.py A|B u v [u v ...]"""
import numpy as np, json, sys
exec(open('tools/tri.py').read().split('pA =')[0])
G = json.load(open('osm/geo.json', encoding='utf-8'))
way = lambda w: np.array(G['ways'][str(w)], float)
PC = way(4681536)[:-1].mean(0)
S = json.load(open('spec.json')); P = way(S['stands'][0]['way'])
cam = {'A': 'cam.json', 'B': 'camB.json'}[sys.argv[1]]; p = json.load(open(cam))['p']
a = list(map(float, sys.argv[2:]))
for u, v in zip(a[::2], a[1::2]):
    o, d = ray(p, u, v); best = None
    for i in range(len(P) - 1):
        A, B = P[i], P[i + 1]; e = B - A
        M = np.array([[d[0], -e[0]], [d[1], -e[1]]])
        if abs(np.linalg.det(M)) < 1e-9: continue
        t, s = np.linalg.solve(M, A - o[:2])
        if 0 <= s <= 1 and t > 0 and (best is None or t < best[0]):
            mid = (A + B) / 2; n = np.array([e[1], -e[0]]); back = n @ (mid - PC) > 0
            best = (t, i, back)
    if best is None: print(u, v, 'miss'); continue
    X = o + best[0] * d
    print(f'{u:.0f},{v:.0f} -> ({X[0]:.1f},{X[1]:.1f}) z {X[2]:.1f} edge {best[1]}')
