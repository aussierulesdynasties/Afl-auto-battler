# Trace check: the satellite mosaic with a metre grid and the model's plan drawn over it (fence ellipse, stands' fronts
# and backs, banks, buildings, boxes, towers, screen). python3 kit/plan.py tools/grounds/<slug> [x0 y0 x1 y1] [out.png]
# Grid lines every 10 m, labelled every 50 m (x east, y north from the fence centre).
import sys, os, math, json, numpy as np, cv2
G = os.path.abspath(sys.argv[1]); SLUG = os.path.basename(G); D = json.load(open(os.path.join(G, 'model', SLUG + '.json')))
HALF = D.get('half', 260); S = cv2.imread(os.path.join(G, 'work', 'sat.png'))
box = [float(v) for v in sys.argv[2:6]] if len(sys.argv) >= 6 else [-HALF, -HALF, HALF, HALF]
out = sys.argv[6] if len(sys.argv) >= 7 else os.path.join(G, 'work', 'plan.png')
sc = 1600 / (box[2] - box[0])   # px per m in the output
x0, y0, x1, y1 = box
crop = S[int((HALF - y1) * 4):int((HALF - y0) * 4), int((x0 + HALF) * 4):int((x1 + HALF) * 4)]
img = cv2.resize(crop, (int((x1 - x0) * sc), int((y1 - y0) * sc)), interpolation=cv2.INTER_CUBIC)
P = lambda x, y: (int((x - x0) * sc), int((y1 - y) * sc))
for g in range(int(math.ceil(x0 / 10)) * 10, int(x1) + 1, 10):
    cv2.line(img, P(g, y0), P(g, y1), (0, 255, 255) if g % 50 == 0 else (0, 160, 160), 1)
    if g % 50 == 0: cv2.putText(img, str(g), (P(g, y1)[0] + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
for g in range(int(math.ceil(y0 / 10)) * 10, int(y1) + 1, 10):
    cv2.line(img, P(x0, g), P(x1, g), (0, 255, 255) if g % 50 == 0 else (0, 160, 160), 1)
    if g % 50 == 0: cv2.putText(img, str(g), (2, P(x0, g)[1] - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
fx, fy, a1, a2, rot = D['fence']; t = math.radians(rot)
def fpt(u): return fx + a1 * math.cos(u) * math.cos(t) - a2 * math.sin(u) * math.sin(t), fy + a1 * math.cos(u) * math.sin(t) + a2 * math.sin(u) * math.cos(t)
pts = np.array([P(*fpt(2 * math.pi * k / 360)) for k in range(361)], np.int32); cv2.polylines(img, [pts], False, (255, 0, 255), 2)
def fence_r(b):
    a = math.radians(b); d = np.array((math.sin(a), math.cos(a))); c, s = math.cos(t), math.sin(t)
    tr = lambda p: np.array([c * p[0] + s * p[1], -s * p[0] + c * p[1]]); p = tr(np.array([-fx, -fy])); q = tr(d)
    A = (q[0] / a1) ** 2 + (q[1] / a2) ** 2; B = 2 * (p[0] * q[0] / a1 ** 2 + p[1] * q[1] / a2 ** 2); C = (p[0] / a1) ** 2 + (p[1] / a2) ** 2 - 1
    return (-B + math.sqrt(B * B - 4 * A * C)) / (2 * A)
pol = lambda b, r: (r * math.sin(math.radians(b)), r * math.cos(math.radians(b)))
for St in D['stands']:
    if St['kind'] == 'straight':
        A, Bp = np.array(St['a']), np.array(St['b']); u = (Bp - A) / np.linalg.norm(Bp - A); nn = np.array([u[1], -u[0]])
        if np.dot(nn, (A + Bp) / 2) < 0: nn = -nn
        Dp = St['depth'] + 0.3; cv2.polylines(img, [np.array([P(*q) for q in (A, Bp, Bp + nn * Dp, A + nn * Dp)], np.int32)], True, (0, 0, 255), 2)
        cv2.putText(img, St['name'], P(*((A + Bp) / 2 - nn * 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2); continue
    for key in ('roof', 'back', 'bank', 'block'):
        if key not in St: continue
        tab = np.array(St[key], float)
        for k in range(1, tab.shape[1]):
            pts = np.array([P(*pol(b, r)) for b, r in zip(tab[:, 0], tab[:, k])], np.int32)
            cv2.polylines(img, [pts], False, (0, 0, 255) if k == tab.shape[1] - 1 else (0, 140, 255), 2)
    for b in (St['b0'], St['b1']):
        cv2.line(img, P(*pol(b, fence_r(b % 360))), P(*pol(b, fence_r(b % 360) + 45)), (255, 255, 0), 1)
    bm = 0.5 * (St['b0'] + St['b1']); cv2.putText(img, St['name'], P(*pol(bm, fence_r(bm % 360) + 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
E = D.get('extras', {})
def rect(c, L, W, a):
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    return [(c[0] + su * L / 2 * ca - sv * W / 2 * sa, c[1] + su * L / 2 * sa + sv * W / 2 * ca) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
for B in E.get('boxes', []) + E.get('buildings', []) + E.get('shelters', []):
    cv2.polylines(img, [np.array([P(*p) for p in rect(B['c'], B['L'], B['W'], B['a'])], np.int32)], True, (0, 255, 0), 2)
for Pp in E.get('polys', []):
    cv2.polylines(img, [np.array([P(*p) for p in Pp['p']], np.int32)], True, (0, 255, 0), 2)
for Tw in D.get('towers', []): cv2.circle(img, P(*Tw['xy']), 6, (255, 0, 0), 2)
if E.get('screen'): cv2.line(img, P(*E['screen']['left']), P(*E['screen']['right']), (255, 128, 0), 3)
tf = os.path.join(G, 'work', 'fence_trace.json')
if os.path.exists(tf):
    for b, r in json.load(open(tf))['trace']: cv2.circle(img, P(*pol(b, r)), 3, (0, 255, 0), -1)
cv2.imwrite(out, img); print(out, img.shape)
