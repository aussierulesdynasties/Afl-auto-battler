"""Draw OSM outlines + model roof edges + tower axes over photo B through camB.json."""
import numpy as np, json, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def R(yaw, pt, roll):
    import math
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pt), math.sin(pt), math.cos(roll), math.sin(roll)
    f = np.array([cy * cp, sy * cp, sp]); r = np.array([sy, -cy, 0.0]); u = np.cross(r, f)
    return np.array([cr * r + sr * u, -sr * r + cr * u, f])
def proj(p, X):
    X = np.atleast_2d(X); d = (X - p[:3]) @ R(*p[3:6]).T
    return np.stack([p[7] + p[6] * d[:, 0] / d[:, 2], p[8] - p[6] * d[:, 1] / d[:, 2]], 1), d[:, 2]
cam = json.load(open(os.path.join(ROOT, sys.argv[1] if len(sys.argv) > 1 else 'camB.json'))); p = np.array(cam['p'])
im = Image.open(os.path.join(ROOT, 'photos/sweetlime_2024.jpg')).convert('RGB'); d = ImageDraw.Draw(im)
g = json.load(open(os.path.join(ROOT, 'osm/geo2.json')))['ways']
for k, w in g.items():
    xy = np.array(w['xy']); c = xy.mean(0)
    if np.abs(c).max() > 450: continue
    t = w['tags']
    if not ('building' in t or t.get('leisure') or t.get('highway') or t.get('waterway') or t.get('natural') == 'water'): continue
    P, z = proj(p, np.c_[xy, np.zeros(len(xy))])
    if (z < 1).any(): continue
    col = (0, 255, 255) if t.get('leisure') else (255, 0, 255) if 'building' in t else (255, 255, 0)
    d.line([tuple(q) for q in P], fill=col, width=2)
G = json.load(open(os.path.join(ROOT, 'osm/geo.json')))
for tid, x, y in G['towers'][:4]:
    P, z = proj(p, np.array([[x, y, 0], [x, y, 64.9]])); d.line([tuple(q) for q in P], fill=(255, 0, 0), width=3)
for q in json.load(open(os.path.join(ROOT, 'ptsB.json'))):
    P, z = proj(p, np.array([q[1]])); u = q[0]
    d.ellipse([u[0] - 6, u[1] - 6, u[0] + 6, u[1] + 6], outline=(0, 255, 0), width=2); d.line([tuple(u), tuple(P[0])], fill=(0, 255, 0), width=2)
im.save(os.path.join(ROOT, 'grid', sys.argv[2] if len(sys.argv) > 2 else 'B_ovl.png'))
