"""The drone photo of Barossa Park from the south-east (austadiums.com barossa-park.jpg, a reference, not in the repo):
its camera solved from ground lines only, so the photo can measure heights.

    python3 tools/grounds/barossa/photo_camera.py PHOTO     # prints the camera and the heights, work/photo_cam.npy

The fence is traced in the photo (the first white after the field's grass on rays from the oval's middle, a RANSAC
ellipse keeping the points within 2 px) and matched to plan.FENCE; with the east crossing's middle and the south goal
posts' feet (on the long axis, 6.4 m apart, behind posts 6.4 m outside) the camera (place, heading, pitch, roll, focal
length, one radial distortion term) is fitted by least squares. Then each light tower's foot (pixel) is put on the
ground and its head's height read off. 2026-11-22: fence 0.31 px median; heads 30.8-34.6 m; goal posts 14.8 m,
behind posts 9.6 m. Depth along the line of sight is poorly held (a pixel is about a metre on the ground there), so
use it for heights, not plan positions."""
import math
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
sys.path.insert(0, HERE)


def trace_fence(a):

    hsv=cv2.cvtColor(a,cv2.COLOR_BGR2HSV).astype(int)
    H,Sa,V=hsv[...,0],hsv[...,1],hsv[...,2]
    grass=(H>25)&(H<95)&(Sa>80)
    white=(V>150)&(Sa<80)
    cx,cy=735,568
    pts=[]
    for t in np.radians(np.arange(0,360,0.25)):
        dx,dy=np.cos(t),np.sin(t)
        run=0
        for r in np.arange(30,520,0.5):
            x,y=int(round(cx+dx*r)),int(round(cy+dy*r))
            if not(0<=x<a.shape[1] and 0<=y<a.shape[0]): break
            if grass[y,x]: run+=1; continue
            if run>30 and white[y,x]:
                pts.append((cx+dx*r,cy+dy*r)); break
            if run>30 and not grass[y,x]:
                # allow a few off-colour pixels (posts' shadows, mowing) before giving up
                ok=any(grass[int(round(cy+dy*(r+k))),int(round(cx+dx*(r+k)))] for k in (1,2,3,4)) if r+4<520 else False
                if ok: continue
                break
    pts=np.array(pts,np.float32)
    def edist(e,P):
        (x0,y0),(A,B),ang=e
        t=np.radians(ang); c,s=np.cos(t),np.sin(t)
        u=(P[:,0]-x0)*c+(P[:,1]-y0)*s; v=-(P[:,0]-x0)*s+(P[:,1]-y0)*c
        rho=np.hypot(u/(A/2),v/(B/2)); return (rho-1)*np.hypot(u,v)/rho
    rng=np.random.default_rng(1); best=None
    for it in range(3000):
        idx=rng.choice(len(pts),6,replace=False)
        try: e=cv2.fitEllipse(pts[idx])
        except Exception: continue
        if not np.all(np.isfinite(e[1])) or max(e[1])>1400: continue
        n=(np.abs(edist(e,pts))<2.0).sum()
        if best is None or n>best[0]: best=(n,e)
    keep=np.abs(edist(best[1],pts))<2.0
    for it in range(3):
        e=cv2.fitEllipse(pts[keep]); d=edist(e,pts); keep=np.abs(d)<2.0
    print(len(pts),keep.sum(),'rms %.2f px'%np.sqrt(np.mean(d[keep]**2)),e)

    v=a.copy()
    for p in pts[keep]: cv2.circle(v,(int(p[0]),int(p[1])),1,(0,0,255),-1)
    cv2.imwrite(os.path.join(WORK,'photo_fence.jpg'),v)
    return pts[keep]


import plan  # noqa: E402
from scipy.optimize import least_squares  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402
photo = cv2.imread(sys.argv[1])
if photo is None:
    raise SystemExit(__doc__)
Hh, W = photo.shape[:2]
fpx = trace_fence(photo)

def basis(h, p, r):
    h, p, r = map(math.radians, (h, p, r))
    f = np.array([math.sin(h) * math.cos(p), math.cos(h) * math.cos(p), -math.sin(p)])
    rt = np.array([math.cos(h), -math.sin(h), 0.0])
    up = np.cross(rt, f)
    rt2 = rt * math.cos(r) + up * math.sin(r)
    up2 = up * math.cos(r) - rt * math.sin(r)
    return f, rt2, up2

def proj(q, P):
    C = q[:3]; f, rt, up = basis(*q[3:6]); fl = q[6]; k1 = q[7] if len(q) > 7 else 0
    d = np.asarray(P, float) - C
    z = d @ f; x = d @ rt / z; y = d @ up / z
    r2 = x * x + y * y; s = 1 + k1 * r2
    return np.stack([W / 2 + fl * x * s, Hh / 2 - fl * y * s], -1)

t = np.linspace(0, 2 * math.pi, 4000, endpoint=False)
cx, cy, a1, a2, rot = plan.FENCE
th = math.radians(rot)
# FENCE: a1 across, a2 along; rot = long axis bearing (east of north)
fe = cx + a1 * np.cos(t) * math.cos(th) - a2 * np.sin(t) * math.sin(th)
fn = cy + a1 * np.cos(t) * math.sin(th) + a2 * np.sin(t) * math.cos(th)
FEN = np.stack([fe, fn, np.zeros_like(fe)], 1)
ax = np.array([-math.sin(th), math.cos(th)]); ac = np.array([math.cos(th), math.sin(th)])
ZEB = (np.array([78.8, -24.5, 0.15]), np.array([991.0, 729.0]))
POSTB = np.array([(451.75, 683), (484.5, 694.5), (519, 707), (554.25, 720)])
POSTT = np.array([(446.25, 625.5), (477.5, 605.5), (512, 615.75), (550.5, 658.75)])

def posts(q, sgn, end):
    d = q[8]; hb, hg = q[9], q[10]
    c = np.array([cx, cy]) + ax * end * (a2 - d)
    xs = np.array([-9.6, -3.2, 3.2, 9.6]) * sgn
    B = np.array([[*(c + ac * x), 0.0] for x in xs]); T = B.copy(); T[:, 2] = [hb, hg, hg, hb]
    return B, T

def res(q, sgn, end):
    pf = proj(q, FEN)
    ok = np.ones(len(pf), bool)
    tree = cKDTree(pf)
    dd, _ = tree.query(fpx)
    r = [dd / 1.0]
    r.append((proj(q, ZEB[0][None])[0] - ZEB[1]) / 3.0)
    B, T = posts(q, sgn, end)
    r.append(((proj(q, B) - POSTB) / 1.5).ravel())
    r.append(((proj(q, T) - POSTT) / 1.5).ravel())
    return np.concatenate(r)

best = None
lo=[-1000,-1000,30,200,5,-15,400,-0.5,2,3,5]; hi=[1000,1000,600,360,80,15,4000,0.5,20,20,25]
for sgn in (1, -1):
    for end in (-1,):
        for hd in (300, 312, 324, 336):
            for dist in (200, 300, 400):
                cam = np.array([cx, cy]) - dist * np.array([math.sin(math.radians(hd)), math.cos(math.radians(hd))])
                q0 = np.array([cam[0], cam[1], 0.5*dist, hd, 25, 0, 1000, 0, 9, 8, 14], float)
                try:
                    s = least_squares(res, q0, args=(sgn, end), loss='soft_l1', f_scale=2.0, max_nfev=3000, bounds=(lo,hi))
                except Exception as e:
                    continue
                c = np.sum(res(s.x, sgn, end) ** 2)
                if best is None or c < best[0]:
                    best = (c, s.x, sgn, end)
c, q, sgn, end = best
r = res(q, sgn, end)
nf = len(fpx)
print('sgn', sgn, 'end', end, 'cost', round(c, 1))
print('camera E N U %.1f %.1f %.1f  heading %.1f pitch %.1f roll %.2f  f %.0f k1 %.3f' % tuple(q[:8]))
print('fence px residual: median %.2f, 90%% %.2f' % (np.median(r[:nf]), np.percentile(r[:nf], 90)))
print('zebra px', np.round(r[nf:nf + 2] * 3, 2), ' posts base px', np.round(r[nf + 2:nf + 10] * 1.5, 1))
print('goal line %.1f m in from fence ends; behind posts %.1f m, goal posts %.1f m tall' % (q[8], q[9], q[10]))
np.save(os.path.join(WORK, 'photo_cam.npy'), q)

TOWERS_PX = {"north-north-east": ((1117, 465), (1137, 325)), "south-south-west": ((329, 537), (307, 380)),
             "north-west": ((798, 377), (800, 270)), "east-south-east": ((927.5, 725), (940, 510))}
for k, (b, hp) in TOWERS_PX.items():
    g = least_squares(lambda p: proj(q, np.array([[p[0], p[1], 0.3]]))[0] - np.array(b, float), [0, 0]).x
    h = least_squares(lambda z: proj(q, np.array([[g[0], g[1], z[0]]]))[0] - np.array(hp, float), [20.0]).x[0]
    print("tower %-17s foot (%.1f, %.1f), head %.1f m up" % (k, g[0], g[1], h))
