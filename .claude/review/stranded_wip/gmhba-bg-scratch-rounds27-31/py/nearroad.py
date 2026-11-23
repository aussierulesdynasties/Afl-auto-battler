import sys, json, math
R = json.load(open(sys.argv[1])); cx, cy = float(sys.argv[2]), float(sys.argv[3]); best = []
for r in R:
    p = r['p']
    for (x1, y1), (x2, y2) in zip(p, p[1:]):
        dx, dy = x2 - x1, y2 - y1; L = dx * dx + dy * dy or 1; t = max(0, min(1, ((cx - x1) * dx + (cy - y1) * dy) / L))
        qx, qy = x1 + t * dx, y1 + t * dy; best.append((math.hypot(cx - qx, cy - qy), r['hw'], round(qx, 1), round(qy, 1), round(math.degrees(math.atan2(dy, dx)), 1)))
for b in sorted(best):
    if b[0] < 80 and (70 < abs(b[4]) < 110): print(b)
