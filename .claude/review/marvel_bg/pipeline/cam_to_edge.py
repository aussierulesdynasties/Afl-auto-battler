"""Walk the p4/p5 cameras along their view line (toward look) until 1 m short of the traced quay line (shore.json).
The photos show water from the frame bottom, so the photographer stood at the edge."""
import json
from shapely.geometry import Polygon, Point
W = [Polygon(p) for p in json.load(open('data/marvel/prep/shore.json'))['polys']]
for job in ('p4', 'p5'):
    P = f'out/marvel/job_{job}_w.json'; J = json.load(open(P)); v = J['views'][0]
    cx, cy = v['cam'][:2]; lx, ly = v['look'][:2]; L = ((lx - cx) ** 2 + (ly - cy) ** 2) ** 0.5; ux, uy = (lx - cx) / L, (ly - cy) / L
    t = 0.0
    while t < 60 and not any(w.contains(Point(cx + ux * (t + 1), cy + uy * (t + 1))) for w in W): t += 0.25
    if t >= 60:   # view line never crosses water: walk back instead
        t = 0.0
        while t > -60 and not any(w.contains(Point(cx + ux * (t - 1), cy + uy * (t - 1))) for w in W): t -= 0.25
    v['cam'][0] = round(cx + ux * t, 2); v['cam'][1] = round(cy + uy * t, 2)
    json.dump(J, open(P, 'w')); print(job, 'moved', t, 'm ->', v['cam'])
