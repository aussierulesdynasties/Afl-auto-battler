"""project plan polygons (metres) at given heights into photo C; draws them on grid/projC.jpg"""
import numpy as np, json, math, sys
from PIL import Image, ImageDraw
sys.path.insert(0, 'tools')
def R(yaw, pt, roll):
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pt), math.sin(pt), math.cos(roll), math.sin(roll)
    f = np.array([cy * cp, sy * cp, sp]); r = np.array([sy, -cy, 0.0]); u = np.cross(r, f)
    return np.array([cr * r + sr * u, -sr * r + cr * u, f])
import os
CAMF = os.environ.get('CAMC', 'camC4.json'); cam = json.load(open(CAMF)); p = cam['p']
def proj(X):
    if cam.get('model') == 'cyl':   # photo C is a cylindrical panorama, verticals corrected (fitC4.py)
        d = (np.array(X, float) - [p[0], p[1], 1.6]) @ R(p[2], 0, 0).T; rho = np.hypot(d[:, 0], d[:, 2])
        return np.stack([1920 + p[3] * np.arctan2(d[:, 0], d[:, 2]), p[4] - p[3] * d[:, 1] / rho], 1)
    d = (np.array(X, float) - p[:3]) @ R(*p[3:6]).T
    return np.stack([p[7] + p[6] * d[:, 0] / d[:, 2], (p[8] - p[6] * d[:, 1] / d[:, 2]) * cam.get('ky', 1.0)], 1)
if __name__ == '__main__':
    polys = json.load(open(sys.argv[1]))
    im = Image.open('close/east_gate_2023.jpg').convert('RGB'); d = ImageDraw.Draw(im)
    for P, z0, z1, col in polys:
        for z in (z0, z1):
            U = proj([(x, y, z) for x, y in P + P[:1]]); d.line([tuple(u) for u in U], fill=tuple(col), width=5)
        for x, y in P:
            U = proj([(x, y, z0), (x, y, z1)]); d.line([tuple(u) for u in U], fill=tuple(col), width=3)
    im.resize((1600, 900)).save('grid/projC.jpg')
