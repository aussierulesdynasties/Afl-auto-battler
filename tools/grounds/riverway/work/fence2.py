# Fence = the dark boundary-fence line on the Esri tile: along each bearing, the darkest pixel within +-7 m of a first-guess
# ellipse (centre 1,-0.2; semi 72 x 84.7, read by eye). Fit an ellipse to the hits, drop outliers (>1.2 m), refit.
import os, json, math, numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = gaussian_filter(np.asarray(Image.open(os.path.join(SP, 'sat', 'esri_025.png')).convert('L'), float), 0.7)
def er(b, e):
    x0, y0, a1, a2, rot = e; t = math.radians(rot); a = math.radians(b); d = np.array([math.sin(a), math.cos(a)])
    c, s = math.cos(t), math.sin(t); R = lambda p: np.array([c*p[0]+s*p[1], -s*p[0]+c*p[1]])
    p = R(np.array([-x0, -y0])); q = R(d); A = (q[0]/a1)**2+(q[1]/a2)**2; B = 2*(p[0]*q[0]/a1**2+p[1]*q[1]/a2**2); C = (p[0]/a1)**2+(p[1]/a2)**2-1
    return (-B+math.sqrt(B*B-4*A*C))/(2*A)
def fit(P):
    x, y = P[:, 0], P[:, 1]; M = np.stack([x*x, x*y, y*y, x, y], 1); A, B, C, D, E = np.linalg.lstsq(M, np.ones(len(x)), rcond=None)[0]
    den = 4*A*C-B*B; x0 = (B*E-2*C*D)/den; y0 = (B*D-2*A*E)/den; th = 0.5*math.atan2(B, A-C); ct, st = math.cos(th), math.sin(th)
    K = 1+A*x0*x0+B*x0*y0+C*y0*y0; Ap = A*ct*ct+B*ct*st+C*st*st; Cp = A*st*st-B*ct*st+C*ct*ct
    return [x0, y0, math.sqrt(K/Ap), math.sqrt(K/Cp), math.degrees(th)]
e = [0.25, -2.1, 72.3, 87.1, 0.0]; hits = []
for b in np.arange(0, 360, 1.0):
    r0 = er(b, e); rs = np.arange(r0-3, r0+3, 0.1); a = math.radians(b)
    v = map_coordinates(L, [(260-rs*math.cos(a))*4, (rs*math.sin(a)+260)*4], order=1)
    k = int(np.argmin(v)); hits.append((b, rs[k], v[k], np.median(v)))
def narrow(b, r):   # a thin line, not a tree shadow: the ground 1.5 m either side is clearly brighter
    a = math.radians(b); f = lambda rr: map_coordinates(L, [[(260-rr*math.cos(a))*4], [(rr*math.sin(a)+260)*4]], order=1)[0]
    c = f(r); return f(r-1.5) - c > 12 and f(r+1.5) - c > 12
P = np.array([[r*math.sin(math.radians(b)), r*math.cos(math.radians(b))] for b, r, v, m in hits if m - v > 18 and narrow(b, r)])
for it in range(3):
    e = fit(P); d = np.array([np.hypot(*p) - er(math.degrees(math.atan2(p[0], p[1])) % 360, e) for p in P]); P = P[np.abs(d) < 1.2]
print('fence ellipse', [round(t, 2) for t in e], 'hits kept', len(P), 'of 360; rms %.2f m' % float(np.sqrt((d[np.abs(d)<1.2]**2).mean())))
json.dump(dict(ell=e, hits=P.tolist()), open(os.path.join(SP, 'work', 'fence.json'), 'w'))
