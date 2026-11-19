# photo pixel of an old-model point (old camera camfit8) -> world point at the same height through the new camera (camfit10)
import numpy as np, json
from scipy.optimize import least_squares
exec(open('cam.py').read())
P8 = np.array(json.load(open('camfit8.json'))['p']); P10 = np.array(json.load(open('camfit10.json'))['p'])
def px(X, p=P8): return proj(p, [X])[0]
def remap(x, y, z):
    u = px((x, y, z)); s = least_squares(lambda q: proj(P10, [[q[0], q[1], z]])[0] - u, [x, y]); return tuple(np.round(s.x, 2)), tuple(np.round(u, 1))
if __name__ == '__main__':
    for nm, pts, z in [('F', [(111.1, 93.3), (93.1, 98.2), (86.1, 100.0), (67.1, 104.6)], 0), ('N', [(134.7, 78.7), (131.3, 86.6), (122.3, 83.1)], 8.5),
                       ('Ftop', [(111.1, 93.3), (93.1, 98.2)], 24)]:
        for p in pts: print(nm, p, z, remap(*p, z))
