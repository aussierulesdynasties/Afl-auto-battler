# Least-squares ray intersection of picks.  Z0=-3 python work/tri2.py "name=v:u:w,v:u:w;name2=..."
import sys, numpy as np, math; sys.path.insert(0, 'work'); import gecam as G
def ray(v, u, w):
    c = G.cam(v); d = c['fwd'] * c['f'] + c['right'] * (u - c['W'] / 2) - c['up'] * (w - c['H'] / 2); d /= np.linalg.norm(d); C = c['C'].copy(); C[2] -= G.Z0; return C, d
for item in sys.argv[1].split(';'):
    nm, ps = item.split('='); rs = []
    for p in ps.split(','):
        v, u, w = p.split(':'); rs.append(ray(v, float(u), float(w)))
    A = np.zeros((3, 3)); b = np.zeros(3)
    for C, d in rs: M = np.eye(3) - np.outer(d, d); A += M; b += M @ C
    X = np.linalg.solve(A, b); res = [np.linalg.norm((np.eye(3) - np.outer(d, d)) @ (X - C)) for C, d in rs]
    print(nm, X.round(1), 'b', round(math.degrees(math.atan2(X[0], X[1])) % 360, 1), 'r', round(math.hypot(X[0], X[1]), 1), 'res', np.round(res, 2))
