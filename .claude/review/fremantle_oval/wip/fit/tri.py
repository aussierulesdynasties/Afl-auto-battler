import numpy as np, json, sys
sys.path.insert(0, 'fit'); from cam import *
from scipy.optimize import least_squares
C = {k: json.load(open(f'fit/{f}')) for k, f in (('a02', 'cam_a02s0.json'), ('g34', 'cam_g34h.json'))}
def tri(obs, x0=(-15, -100, 10)):
    def r(X):
        out = []
        for k, (u, v) in obs.items():
            c = C[k]; out.extend(proj(c['p'], np.array([X]), c['W'] / 2, c['H'] / 2)[0] - np.array([u, v]))
        return np.array(out)
    b = least_squares(r, x0); return b.x, b.fun
if __name__ == '__main__':
    for name, o in json.loads(sys.argv[1]).items():
        X, f = tri(o); print(name, np.round(X, 2), 'resid', np.round(f, 1))
