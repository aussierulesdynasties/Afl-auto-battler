"""signC.py: photo C pixel -> first model surface hit (ray through the fitted camC14), to place the ground's own signs"""
import json, sys, os, glob, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plyread import readply
c = json.load(open('camC14.json')); Cx, Cy, Cz, yaw, pit, roll, fo, cx, cy = c['p']; ky = c['ky']
f = np.array([np.cos(yaw) * np.cos(pit), np.sin(yaw) * np.cos(pit), np.sin(pit)]); r = np.array([np.sin(yaw), -np.cos(yaw), 0.0]); u = np.cross(r, f)
MESH = {}
for fn in glob.glob('model/*.ply'):
    V, T = readply(fn, faces=True); MESH[os.path.basename(fn)] = V[T]
def hit(px, py):
    py = py / ky; d = f + (px - cx) / fo * r - (py - cy) / fo * u; d /= np.linalg.norm(d); o = np.array([Cx, Cy, Cz])
    best = (1e9, None, None)
    for k, A in MESH.items():
        e1, e2 = A[:, 1] - A[:, 0], A[:, 2] - A[:, 0]; p = np.cross(d, e2); det = (e1 * p).sum(1)
        ok = np.abs(det) > 1e-9; inv = np.where(ok, 1 / np.where(ok, det, 1), 0); s = o - A[:, 0]
        a = (s * p).sum(1) * inv; q = np.cross(s, e1); b = (q * d).sum(1) * inv; t = (q * e2).sum(1) * inv
        g = ok & (a >= 0) & (b >= 0) & (a + b <= 1) & (t > 0.5)
        if g.any():
            i = np.argmin(np.where(g, t, 1e9))
            if t[i] < best[0]: n = np.cross(e1[i], e2[i]); best = (t[i], k, n / np.linalg.norm(n))
    return o + d * best[0], best[1], best[2]
if __name__ == '__main__':
    for a in sys.argv[1:]:
        x, y = map(float, a.split(',')); P, k, n = hit(x, y); print(a, k, np.round(P, 2), np.round(n, 2))
