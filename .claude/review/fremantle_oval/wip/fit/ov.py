# ov.py photo render x0 y0 x1 y1 out [scale]: photo | render over photo at 55% | render outline on photo, grid every 50 px
import sys, cv2, numpy as np
ph = cv2.imread(sys.argv[1]); rn = cv2.imread(sys.argv[2], cv2.IMREAD_UNCHANGED)
x0, y0, x1, y1 = map(int, sys.argv[3:7]); out = sys.argv[7]; k = float(sys.argv[8]) if len(sys.argv) > 8 else 1.0
if rn.shape[:2] != ph.shape[:2]: rn = cv2.resize(rn, (ph.shape[1], ph.shape[0]))
a = rn[..., 3:4].astype(float) / 255 if rn.shape[2] == 4 else np.ones(rn.shape[:2] + (1,))
P = ph[y0:y1, x0:x1].astype(float); R = rn[y0:y1, x0:x1, :3].astype(float); A = a[y0:y1, x0:x1]
blend = (P * (1 - 0.55 * A) + R * 0.55 * A).astype(np.uint8)
g = cv2.cvtColor(rn[y0:y1, x0:x1, :3], cv2.COLOR_BGR2GRAY)
e = cv2.Canny(g, 30, 90) | cv2.Canny((A[..., 0] * 255).astype(np.uint8), 50, 150)
line = ph[y0:y1, x0:x1].copy(); line[e > 0] = (255, 0, 255)
tiles = []
for t in (ph[y0:y1, x0:x1].copy(), blend, line):
    t = cv2.resize(t, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
    for gx in range((x0 // 50 + 1) * 50, x1, 50):
        X = int((gx - x0) * k); cv2.line(t, (X, 0), (X, 6), (0, 255, 255), 1); cv2.putText(t, str(gx), (X + 2, 14), 0, 0.4, (0, 255, 255), 1)
    for gy in range((y0 // 50 + 1) * 50, y1, 50):
        Y = int((gy - y0) * k); cv2.line(t, (0, Y), (6, Y), (0, 255, 255), 1); cv2.putText(t, str(gy), (8, Y + 4), 0, 0.4, (0, 255, 255), 1)
    tiles.append(t)
sep = np.full((tiles[0].shape[0], 8, 3), 30, np.uint8)
v = sys.argv[9] if len(sys.argv) > 9 else 'h'
if v == 'v':
    sep = np.full((8, tiles[0].shape[1], 3), 30, np.uint8); cv2.imwrite(out, np.vstack([tiles[0], sep, tiles[1], sep, tiles[2]]))
else: cv2.imwrite(out, np.hstack([tiles[0], sep, tiles[1], sep, tiles[2]]))
