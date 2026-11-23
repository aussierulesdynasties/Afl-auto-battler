import json, math, numpy as np
BL = json.load(open('data/optus/prep/buildings.json'))
for i, b in enumerate(BL):
    P = np.array(b['p']); c = P.mean(0)
    if math.hypot(c[0] - 500, c[1] + 930) < 260:
        x, y = P[:, 0], P[:, 1]; a = 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        print(i, np.round(c, 1), 'h', b['h'], 'area', round(a), 'bbox', np.round(P.min(0)), np.round(P.max(0)))
