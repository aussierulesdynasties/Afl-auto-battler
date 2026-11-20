"""plangrid.py X0 X1 Y0 Y1 SCALE OUT [ways...]: crop the Esri mosaic to a box in world metres (x east, y north), upscale,
draw a labelled metre grid (every 5 m, labels every 10 m) and optional OSM ways / polygons from a json list"""
import sys, json, numpy as np, cv2
sys.path.insert(0, 'tools'); from esri import m2px, ways
x0, x1, y0, y1, S = map(float, sys.argv[1:6]); out = sys.argv[6]; extra = sys.argv[7:]
m = cv2.imread('esri/mosaic.jpg'); a = m2px(x0, y1); b = m2px(x1, y0)
px0, py0, px1, py1 = int(a[0]), int(a[1]), int(b[0]) + 1, int(b[1]) + 1
c = cv2.resize(m[py0:py1, px0:px1], None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
P = lambda x, y: (int((m2px(x, y)[0] - px0) * S), int((m2px(x, y)[1] - py0) * S))
W = ways()
for e in extra:
    if e.endswith('.json'):
        for poly in json.load(open(e)): cv2.polylines(c, [np.array([P(*p) for p in poly], np.int32)], True, (0, 0, 255), 1)
    else: cv2.polylines(c, [np.array([P(*p) for p in W[e]], np.int32)], False, (255, 0, 255), 1)
for gx in range(int(x0) // 5 * 5, int(x1) + 1, 5):
    X = P(gx, 0)[0]; cv2.line(c, (X, 0), (X, c.shape[0]), (0, 255, 255) if gx % 10 == 0 else (0, 140, 140), 1)
    if gx % 10 == 0: cv2.putText(c, str(gx), (X + 2, 14), 0, 0.45, (0, 255, 255), 1)
for gy in range(int(y0) // 5 * 5, int(y1) + 1, 5):
    Y = P(0, gy)[1]; cv2.line(c, (0, Y), (c.shape[1], Y), (0, 255, 255) if gy % 10 == 0 else (0, 140, 140), 1)
    if gy % 10 == 0: cv2.putText(c, str(gy), (3, Y - 3), 0, 0.45, (0, 255, 255), 1)
cv2.imwrite(out, c); print(out, c.shape)
