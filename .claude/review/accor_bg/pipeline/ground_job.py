"""Rewrite a job so cam/look z are metres above the terrain at that x,y. ground_job.py g in.json out.json"""
import sys, json, numpy as np
g, a, b = sys.argv[1:4]; D = 'data/%s/prep/' % g; m = json.load(open(D + 'meta.json'))
near = np.load(D + 'near_h.npy'); NE, NS = m['near'], m['near_step']
def h(x, y):
    fx, fy = (x + NE) / NS, (y + NE) / NS; i, j = int(fx), int(fy); ax, ay = fx - i, fy - j
    return float(near[j, i] * (1 - ax) * (1 - ay) + near[j, i + 1] * ax * (1 - ay) + near[j + 1, i] * (1 - ax) * ay + near[j + 1, i + 1] * ax * ay)
J = json.load(open(a))
for v in J['views']:
    for k in ('cam', 'look'):
        if k in v: v[k][2] += h(v[k][0], v[k][1]); print(v['name'], k, round(v[k][2], 1))
json.dump(J, open(b, 'w'))
