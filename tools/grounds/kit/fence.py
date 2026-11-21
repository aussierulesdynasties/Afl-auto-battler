# Boundary fence: the edge of the field's grass, traced on work/sat.png along each bearing from the origin, then an
# ellipse fitted with the outliers (paths, shadows, a lighter bank) dropped. python3 kit/fence.py tools/grounds/<slug> [r_min r_max]
# Prints the fit and writes work/fence_trace.json; the ellipse goes into <slug>.json 'fence' by hand once checked on kit/plan.py.
import sys, os, json, math, numpy as np, cv2
G = os.path.abspath(sys.argv[1]); SLUG = os.path.basename(G); D = json.load(open(os.path.join(G, 'model', SLUG + '.json')))
r0, r1 = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (50, 110)
H = D.get('half', 260); S = cv2.imread(os.path.join(G, 'work', 'sat.png')); S = cv2.GaussianBlur(S, (9, 9), 0)
hsv = cv2.cvtColor(S, cv2.COLOR_BGR2HSV).astype(int)
ref = hsv[int(H * 4) - 80:int(H * 4) + 80, int(H * 4) - 80:int(H * 4) + 80].reshape(-1, 3); hm, sm, vm = np.median(ref, 0)
tol = D.get('fence_tol', (20, 80, 55))
def field(x, y):
    h, s, v = hsv[int(round((H - y) * 4)), int(round((x + H) * 4))]
    return abs(h - hm) < tol[0] and abs(s - sm) < tol[1] and abs(v - vm) < tol[2]
pts = []
for b in np.arange(0, 360, 1.0):
    a = math.radians(b); run = 0
    for r in np.arange(r0, r1, 0.25):
        if not field(r * math.sin(a), r * math.cos(a)):
            run += 1
            if run >= 12: pts.append((b, r - 12 * 0.25)); break
        else: run = 0
P = np.array([[r * math.sin(math.radians(b)), r * math.cos(math.radians(b))] for b, r in pts])
keep = np.ones(len(P), bool)
for it in range(6):
    x, y = P[keep, 0], P[keep, 1]
    M = np.stack([x * x, x * y, y * y, x, y], 1); c = np.linalg.lstsq(M, np.ones(len(x)), rcond=None)[0]
    A, B, C, Dd, E = c; den = 4 * A * C - B * B; x0 = (B * E - 2 * C * Dd) / den; y0 = (B * Dd - 2 * A * E) / den
    th = 0.5 * math.atan2(B, A - C); ct, st = math.cos(th), math.sin(th)
    K = 1 + A * x0 * x0 + B * x0 * y0 + C * y0 * y0
    Ap = A * ct * ct + B * ct * st + C * st * st; Cp = A * st * st - B * ct * st + C * ct * ct
    a1, a2 = math.sqrt(K / Ap), math.sqrt(K / Cp)
    u = (P[:, 0] - x0) * ct + (P[:, 1] - y0) * st; v = -(P[:, 0] - x0) * st + (P[:, 1] - y0) * ct
    res = (np.sqrt((u / a1) ** 2 + (v / a2) ** 2) - 1) * 0.5 * (a1 + a2)
    keep = np.abs(res) < max(1.0, 2.5 * np.std(res[keep])) if it < 5 else np.abs(res) < 1.5
print('ellipse centre %.2f %.2f semi %.2f %.2f rot %.2f deg; kept %d of %d; rms %.2f m' % (x0, y0, a1, a2, math.degrees(th), keep.sum(), len(P), np.sqrt(np.mean(res[keep] ** 2))))
json.dump(dict(trace=pts, ell=[x0, y0, a1, a2, math.degrees(th)]), open(os.path.join(G, 'work', 'fence_trace.json'), 'w'))
