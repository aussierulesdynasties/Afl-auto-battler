import json, numpy as np
T = np.array(json.load(open('data/accor/towers.json'))); FP = np.array(json.load(open('data/accor/prep/footprint.json')))
keep = []
for t in T:
    if any(np.hypot(*(t[:2] - k[:2])) < 8 for k in keep): continue
    keep.append(t)
K = np.array(keep); r = np.hypot(K[:, 0], K[:, 1]); b = ((np.degrees(np.arctan2(K[:, 1], K[:, 0])) % 360) // 2).astype(int)
inside = r < FP[b]
for t, i, rr in zip(K, inside, r):
    p = ((t[0] / 0.5 + 1000) * 1400 / 2000, (1000 - t[1] / 0.5) * 1400 / 2000)
    print('IN ' if i else 'OUT', [round(v, 1) for v in t], 'r', round(rr), 'sat1km px', [round(v) for v in p])
print('raw', len(T), 'deduped', len(K), 'outside roof', int((~inside).sum()))
