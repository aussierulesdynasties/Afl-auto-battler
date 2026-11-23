s = open('pools.py', encoding='utf-8', newline='').read()
s = s.replace("    from matplotlib.path import Path as _MP\n", """    def _pip(P, X):   # even-odd point-in-polygon, vectorised over points X
        r = np.zeros(len(X), bool); x, y = X[:, 0], X[:, 1]
        for i in range(len(P)):
            (x1, y1), (x2, y2) = P[i - 1], P[i]
            c = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1); r ^= c
        return r
""")
s = s.replace("_in = _MP(_P).contains_points(_gv[:, :2], radius=-0.5)", "_in = _pip(_P, _gv[:, :2])")
open('pools.py', 'w', encoding='utf-8', newline='').write(s); print('ok', '_MP' in s)
