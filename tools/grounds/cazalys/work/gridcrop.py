# python work/gridcrop.py x0 x1 y0 y1 out.jpg [scale]: crop of sat/esri_025.png in local metres with a 10 m grid (labels every 20 m) + OSM outlines
import sys, json, cv2, numpy as np
x0, x1, y0, y1 = map(float, sys.argv[1:5]); out = sys.argv[5]; s = float(sys.argv[6]) if len(sys.argv) > 6 else 2
S = cv2.imread('sat/esri_025.png'); O = json.load(open('work/osm_xy.json'))
u = lambda x: int(round((x + 260) * 4)); v = lambda y: int(round((260 - y) * 4))
C = S[v(y1):v(y0), u(x0):u(x1)].copy(); C = cv2.resize(C, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
U = lambda x: int(round((u(x) - u(x0)) * s)); V = lambda y: int(round((v(y) - v(y1)) * s))
for g in range(int(x0 // 10 * 10), int(x1) + 1, 10):
    cv2.line(C, (U(g), 0), (U(g), C.shape[0]), (0, 255, 255) if g % 50 == 0 else (0, 160, 160), 1)
    if g % 20 == 0: cv2.putText(C, str(g), (U(g) + 2, 12), 0, 0.4, (0, 255, 255), 1)
for g in range(int(y0 // 10 * 10), int(y1) + 1, 10):
    cv2.line(C, (0, V(g)), (C.shape[1], V(g)), (0, 255, 255) if g % 50 == 0 else (0, 160, 160), 1)
    if g % 20 == 0: cv2.putText(C, str(g), (2, V(g) - 2), 0, 0.4, (0, 255, 255), 1)
if '--osm' in sys.argv:
    for k, P in O.items():
        p = np.array([[U(a), V(b)] for a, b in P], np.int32); cv2.polylines(C, [p], False, (255, 0, 255), 1)
cv2.imwrite(out, C)
