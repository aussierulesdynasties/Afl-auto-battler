"""Solve a photo camera from pixel<->3D matches. fitcam.py g spec.json -> writes job. spec: {name,img:[W,H],x0:[x,y,yaw_deg,pitch_deg,fov_h],pts:[[u,v,X,Y,Z],...],eye:1.6,out_res:[w,h],fix_xy:false}"""
import sys, json, math, numpy as np
from scipy.optimize import least_squares
g, sp = sys.argv[1:3]; S = json.load(open(sp)); D = 'data/%s/prep/' % g; m = json.load(open(D + 'meta.json'))
near = np.load(D + 'near_h.npy'); NE, NS = m['near'], m['near_step']
def h(x, y):
    fx, fy = (x + NE) / NS, (y + NE) / NS; i, j = int(fx), int(fy); ax, ay = fx - i, fy - j
    return float(near[j, i] * (1 - ax) * (1 - ay) + near[j, i + 1] * ax * (1 - ay) + near[j + 1, i] * (1 - ax) * ay + near[j + 1, i + 1] * ax * ay)
W, H = S['img']; P = np.array(S['pts'], float); eye = S.get('eye', 1.6)
def proj(p):
    x, y, yaw, pit, fov = p; cy = H / 2
    if S.get("shift"): cy, pit = pit, 0.0
    z = h(x, y) + eye
    yw, pt = math.radians(yaw), math.radians(pit); f = W / 2 / math.tan(math.radians(fov) / 2)
    fwd = np.array([math.cos(pt) * math.cos(yw), math.cos(pt) * math.sin(yw), math.sin(pt)])
    rt = np.array([math.sin(yw), -math.cos(yw), 0.0]); up = np.cross(rt, fwd)
    d = P[:, 2:5] - [x, y, z]; zc = d @ fwd
    return np.stack([W / 2 + f * (d @ rt) / zc, cy - f * (d @ up) / zc], 1), z, fwd
def res(p):
    if S.get('fix_xy'): p = [S['x0'][0], S['x0'][1]] + list(p)
    return (proj(p)[0] - P[:, :2]).ravel()
x0 = S['x0'][2:] if S.get('fix_xy') else S['x0']
r = least_squares(res, x0); p = ([S['x0'][0], S['x0'][1]] + list(r.x)) if S.get('fix_xy') else list(r.x)
uv, z, fwd = proj(p); err = np.hypot(*(uv - P[:, :2]).T)
print('fit', [round(v, 2) for v in p], 'z', round(z, 2), 'px err', err.round(1), 'rms', round(float(np.sqrt((err ** 2).mean())), 1))
cam = [p[0], p[1], z]; look = list(np.array(cam) + fwd * 100)
J = json.load(open('out/%s/ov_%s.json' % (g, S['name']))); J['views'] = [{'name': S['name'], 'cam': cam, 'look': look, 'fov_h': p[4], 'shift': [0, (p[3] - H / 2) / max(W, H) if S.get('shift') else 0]}]
json.dump(J, open('out/%s/ov_%s.json' % (g, S['name']), 'w')); print('written')
