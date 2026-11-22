import json, numpy as np
d = json.load(open('spec/optus_fc_hand.json'))
def area(p): p = np.array(p, float); return 0.5 * abs(np.dot(p[:, 0], np.roll(p[:, 1], 1)) - np.dot(p[:, 1], np.roll(p[:, 0], 1)))
print('bands', len(d['bands']), 'tones', np.bincount([b['tone'] for b in d['bands']]).tolist())
for i, b in enumerate(d['bands']):
    p = np.array(b['pts']); a = area(p); per = np.linalg.norm(np.diff(np.vstack([p, p[:1]]), axis=0), axis=1).sum()
    print('band %2d tone %d area %6.0f m2 mean width %4.1f m' % (i, b['tone'], a, 2 * a / per * 2 / 2))
for i, q in enumerate(d['planters']):
    p = np.array(q['pts']); print('planter %d %4.1f x %4.1f m area %5.1f m2 trees %d' % (i, *(p.max(0) - p.min(0)), area(p), len(q['trees'])))
