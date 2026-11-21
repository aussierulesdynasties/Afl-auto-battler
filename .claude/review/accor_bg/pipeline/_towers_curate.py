# 19 Olympic Boulevard towers, checked one by one on the aerial (out/accor/towers_board.png, north.png).
# Each entry = cap centre (m). Base box = cap - (6.4, 16.0) m (measured: towers 9/10 and 20/21).
import json, numpy as np
T = json.load(open('data/accor/towers.json')); keep = []
for t in T:
    if not any(np.hypot(t[0] - k[0], t[1] - k[1]) < 8 for k in keep): keep.append(t)
OFF = np.array([6.4, 16.0])
caps = [keep[i][:2] for i in (1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 16, 19, 20, 24, 25)]
caps += [list(np.array(keep[i][:2]) + OFF) for i in (22, 23)]        # detector hit the base box, cap is 17 m NNE
caps += [[-102.5, 530.0]]                                            # north tower, outside the traced paving (north.png)
json.dump([[round(float(a), 1), round(float(b), 1)] for a, b in caps], open('data/accor/towers_curated.json', 'w'))
print('towers', len(caps))
