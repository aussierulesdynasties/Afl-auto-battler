import json, math, numpy as np
f = np.array(json.load(open('data/adelaide/prep/fence_polys.json')), float).reshape(-1, 2)
r = np.hypot(f[:, 0], f[:, 1]); a = np.degrees(np.arctan2(f[:, 1], f[:, 0])) % 360; k = r < 1000
H = np.load('data/adelaide/prep/near_h.npy'); NE = 1500.0; NS = 2 * NE / (H.shape[0] - 1)
def h(x, y): return float(H[min(max(int(round((y + NE) / NS)), 0), H.shape[0] - 1), min(max(int(round((x + NE) / NS)), 0), H.shape[1] - 1)])
base = {"res": [960, 540], "samples": 16, "sun": {"az": 110, "el": 45, "power": 4.5}, "sky": [[0.0, [0.77, 0.84, 0.89]], [0.45, [0.25, 0.49, 0.77]]]}
ring, street = [], []
for b in range(0, 360, 45):
    R = float(r[k & (abs((a - b + 180) % 360 - 180) < 5)].max()); t = math.radians(b); c, s = math.cos(t), math.sin(t)
    lx, ly = R * c, R * s; D_ = 40 if b == 270 else 80; cx, cy = (R + D_) * c, (R + D_) * s
    ring.append({"name": "fence_%d" % b, "cam": [round(cx, 1), round(cy, 1), h(cx, cy) + (25 if b == 270 else 8)], "look": [round(lx, 1), round(ly, 1), h(lx, ly) + 2], "fov_h": 55})
    ex, ey = (R + 15) * c, (R + 15) * s; ox, oy = (R + 215) * c, (R + 215) * s   # street level, looking outward
    street.append({"name": "street_%d" % b, "cam": [round(ex, 1), round(ey, 1), h(ex, ey) + 1.7], "look": [round(ox, 1), round(oy, 1), h(ox, oy) + 3], "fov_h": 70})
json.dump(dict(base, out="fence", views=ring), open('out/adelaide/job_fence.json', 'w'))
json.dump(dict(base, out="street", views=street), open('out/adelaide/job_street.json', 'w'))
print(H.shape, [v["cam"] for v in ring])
