# Roof edges of a bowl on the satellite: along each bearing (every 'step' deg) from the fence outward, the first run of
# bright roof (inner edge) and where the bright run ends (outer edge), small gaps bridged. Prints a [b, r_in, r_out]
# table, smoothed, for a polar stand's 'roof'. python3 kit/edges.py tools/grounds/<slug> b0 b1 [step] [min_v] [max_s] [gap_m]
import sys, os, json, math, numpy as np, cv2
G = os.path.abspath(sys.argv[1]); SLUG = os.path.basename(G); D = json.load(open(os.path.join(G, 'model', SLUG + '.json')))
b0, b1 = float(sys.argv[2]), float(sys.argv[3]); st = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0
mv = int(sys.argv[5]) if len(sys.argv) > 5 else 185; ms = int(sys.argv[6]) if len(sys.argv) > 6 else 45; gap = float(sys.argv[7]) if len(sys.argv) > 7 else 3.0
H = D.get('half', 260); S = cv2.GaussianBlur(cv2.imread(os.path.join(G, 'work', 'sat.png')), (5, 5), 0); hsv = cv2.cvtColor(S, cv2.COLOR_BGR2HSV).astype(int)
fx, fy, a1, a2, rot = D['fence']; t = math.radians(rot)
def fence_r(b):
    a = math.radians(b); d = np.array((math.sin(a), math.cos(a))); c, s = math.cos(t), math.sin(t)
    tr = lambda p: np.array([c * p[0] + s * p[1], -s * p[0] + c * p[1]]); p = tr(np.array([-fx, -fy])); q = tr(d)
    A = (q[0] / a1) ** 2 + (q[1] / a2) ** 2; B = 2 * (p[0] * q[0] / a1 ** 2 + p[1] * q[1] / a2 ** 2); C = (p[0] / a1) ** 2 + (p[1] / a2) ** 2 - 1
    return (-B + math.sqrt(B * B - 4 * A * C)) / (2 * A)
rows = []
for b in np.arange(b0, b1 + 1e-6, st):
    a = math.radians(b); rf = fence_r(b % 360); rs = np.arange(rf + 3, min(rf + 90, H * 0.98), 0.25); white = []
    for r in rs:
        x, y = r * math.sin(a), r * math.cos(a); h, s_, v = hsv[int(round((H - y) * 4)), int(round((x + H) * 4))]; white.append(v >= mv and s_ <= ms)
    white = np.array(white); ri = ro = None; k = 0; n = len(white)
    while k < n:
        if white[k] and white[k:k + 12].mean() > 0.8: ri = rs[k]; break
        k += 1
    if ri is None: continue
    last = k; miss = 0
    for j in range(k, n):
        if white[j]: last = j; miss = 0
        else:
            miss += 1
            if miss * 0.25 > gap: break
    ro = rs[last]; rows.append([float(b), float(ri), float(ro)])
R = np.array(rows)
for k in (1, 2):   # median smooth
    R[:, k] = [np.median(R[max(0, i - 2):i + 3, k]) for i in range(len(R))]
print(json.dumps([[round(b, 1), round(i, 2), round(o, 2)] for b, i, o in R]))
