# Triangulate 3D points (model frame: z up from the field) from pixel picks in the GE views ge/<v>.png.
# Usage: Z0=-3 python work/tri.py "l000:u:v l090:u:v ..." [...]  -> x y z, bearing, radius, rms px
import sys, math, numpy as np; sys.path.insert(0, 'work'); import gecam as G, earthcam as E
def ray(v, u, w):
    c = G.cam(v); dx = (u - c['W'] / 2) / c['f']; dy = -(w - c['H'] / 2) / c['f']
    r = c['fwd'] + dx * c['right'] + dy * c['up']; o = c['C'].copy(); o[2] -= G.Z0; return o, r / np.linalg.norm(r)
def tri(P):
    A = np.zeros((3, 3)); b = np.zeros(3)
    for v, u, w in P:
        o, d = ray(v, u, w); M = np.eye(3) - np.outer(d, d); A += M; b += M @ o
    X = np.linalg.solve(A, b)
    e = [np.linalg.norm(G.P(v, X) - [u, w]) for v, u, w in P]
    return X, float(np.sqrt(np.mean(np.square(e))))
if __name__ == '__main__':
    for a in sys.argv[1:]:
        P = [(s.split(':')[0], float(s.split(':')[1]), float(s.split(':')[2])) for s in a.split()]
        X, e = tri(P); b = math.degrees(math.atan2(X[0], X[1])) % 360
        print(' '.join(f'{x:.1f}' for x in X), f'b {b:.1f} r {math.hypot(X[0], X[1]):.1f}', f'rms {e:.1f}px')
