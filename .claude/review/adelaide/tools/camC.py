"""Camera C (east_gate_2023.jpg, 3840x2160): level camera (verticals vertical). Bearings from vertical edges with
plan xy (towers from OSM, gate box corners from Esri), then height scale from ground points."""
import numpy as np, json, math
from scipy.optimize import least_squares
W, H = 3840, 2160
B = [((105.29, -75.82), 480, 'SE tower shaft'), ((65.65, 112.08), 3428, 'NE tower shaft'),
     ((136.6, -17.7), 2110, 'box south edge'), ((136.6, 2.7), 2810, 'box north edge')]
def uof(q, xy):
    Cx, Cy, yaw, f = q; dx, dy = xy[0] - Cx, xy[1] - Cy
    fwd = dx * math.cos(yaw) + dy * math.sin(yaw); rgt = dx * math.sin(yaw) - dy * math.cos(yaw)
    return W / 2 + f * rgt / fwd, fwd
def res(q): return [uof(q, b[0])[0] - b[1] for b in B]
best = None
for Cx in (170, 200, 250, 300):
    for Cy in (-30, -10, 10):
        r = least_squares(res, [Cx, Cy, math.pi, 1500])
        if best is None or r.cost < best.cost: best = r
q = best.x; print('C', np.round(q[:2], 1), 'yaw deg', round(math.degrees(q[2]), 1), 'f', round(q[3]), 'res', np.round(res(q), 1))
json.dump({'q': list(q)}, open('camC_plan.json', 'w'))
