import math, numpy as np
T = np.array([437., -908.]); P = np.array([564., -943.]); W = np.array([446., -1092.])
def brg(c, q): d = q - c; return math.degrees(math.atan2(d[1], d[0]))
hits = []
for x in range(-1400, 1401, 20):
    for y in range(-1400, 1401, 20):
        c = np.array([x, y], float); dp = np.linalg.norm(P - c)
        if not 600 < dp < 1100: continue
        s = brg(c, T) - brg(c, P)   # >0: P clockwise of T = P to the right
        s = (s + 180) % 360 - 180
        if abs(s - 5.4) < 1.0: hits.append((x, y, round(dp), round(s, 1), round(brg(c, P), 1)))
for h in hits[::max(1, len(hits) // 40)]: print(h)
print(len(hits))
