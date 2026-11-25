# Side-view check, computed: the model's edges (from build.py, the shipped plan) projected into Google Earth's
# matched obliques (ob_000/090/180/270: 1200 m out, 50 deg tilt, f 3859 px, aimed at the top-down registration),
# and along each projected edge the strongest image edge searched +-6 m (in metres along the ground, outward
# positive) across it. Reports, per view and per line, the median and rms offset in metres and how many points found
# an edge. Needs no Blender:  python3 obmeasure.py BUILD_PY [OUT_DIR]
import sys, json, math, numpy as np, cv2
from scipy.ndimage import gaussian_filter, map_coordinates
from cam import camera, project
import types
for m in ('bpy', 'bmesh', 'mathutils'): sys.modules.setdefault(m, types.ModuleType(m))   # plan maths only
src = open(sys.argv[1]).read()
here = __import__('os').path.dirname(__import__('os').path.abspath(sys.argv[1])); sys.path.insert(0, here)
cwd = __import__('os').getcwd(); __import__('os').chdir(here)
__file__ = sys.argv[1]; exec(src[:src.index('def roof(col)')]); __file__ = 'obmeasure.py'
__import__('os').chdir(cwd)
OUT = sys.argv[2] if len(sys.argv) > 2 else None
C = json.load(open('cal.json')); DX, DY = C['dx'], C['dy']
F = 3859.0
def stand_of(b):
    s = stand_at(b)
    return s if s and s['kind'] != 'open' else None
def inner(b, s, pad=2.0):
    b0, b1 = s['b0'], s['b1']; q = b % 360
    if q < b0 - 1: q += 360
    return b0 + pad <= q <= b1 - pad
def lines():
    L = {}
    bs = np.arange(0, 360, 0.25)
    for nm in ('field edge', 'roof front', 'roof back', 'wall base'):
        pts = []
        for b in bs:
            s = stand_of(b)
            if nm == 'field edge':
                if not (s is None or inner(b, s, 1.0)) or is_open(b): continue   # turf edge where a stand is behind it
                pts.append((b, rF(b), 0.0, s['name'] if s else '-')); continue
            if s is None or not inner(b, s):
                continue
            if nm == 'roof front': r = roof_front(b); z = roof_top(s, b, r)
            elif nm == 'roof back': r = roof_back(b); z = roof_top(s, b, r)
            else: r = back_r(b); z = 0.0
            pts.append((b, r, z, s['name']))
        L[nm] = pts
    return L
# which side of the bowl each line can be seen on (far: the side the camera looks at; near: under it), the image
# channel it shows in, and the sign of the change going outward (0: either)
SPEC = {'field edge': ('far', 'green', -1), 'roof front': ('far', 'white', +1),
        'roof back': ('both', 'white', -1), 'wall base': ('near', 'gray', 0)}
WIN = {'field edge': 5.0, 'roof front': 5.0, 'roof back': 5.0, 'wall base': 4.0}
def angd(a, b): return abs((a - b + 180) % 360 - 180)
def measure(h, L, delta=0.0, draw=False):
    im = cv2.imread('ge/ob_%03d.png' % h).astype(np.float32)
    B, G, R = im[..., 0], im[..., 1], im[..., 2]
    ch = {'gray': gaussian_filter(im.mean(2), 0.8), 'white': gaussian_filter(im.min(2), 0.8),
          'green': gaussian_filter(G - 0.5 * (R + B), 0.8)}
    cam = list(camera((DX, DY, delta), h, 50, 1200, 15)); cam[4] = F
    res = {}; vis = cv2.imread('ge/ob_%03d.png' % h) if draw else None
    for nm, pts in L.items():
        sideok, cn, sg = SPEC[nm]; chan = ch[cn]; out = []
        for b, r, z, sn in pts:
            far = angd(b, h) < (80 if nm == 'field edge' else 50); near = angd(b, h + 180) < 50
            if not ((sideok in ('far', 'both') and far) or (sideok in ('near', 'both') and near)):
                continue
            u = np.array([math.sin(math.radians(b)), math.cos(math.radians(b)), 0.0])
            P = np.array([r * u[0], r * u[1], z])
            q0 = project(cam, [P])[0]; q1 = project(cam, [P + u])[0]
            t0 = project(cam, [P + np.array([u[1], -u[0], 0]) * 0.5])[0] - q0
            n = np.array([-t0[1], t0[0]]); n /= np.linalg.norm(n)
            ppm = (q1 - q0) @ n
            if abs(ppm) < 0.8 or not (8 < q0[0] < 1272 and 8 < q0[1] < 712):
                continue
            w = WIN[nm]; ss = np.arange(-w - 0.5, w + 0.51, 0.1)
            xy = q0[None, :] + (ss * ppm)[:, None] * n[None, :]
            prof = map_coordinates(chan, [xy[:, 1], xy[:, 0]], order=1, mode='nearest')
            g = np.gradient(prof) / (0.1 * abs(ppm))       # grey levels per pixel across the edge
            gg = g * sg if sg else np.abs(g)
            k = int(np.argmax(gg[5:-5])) + 5
            if gg[k] < 4.0:
                out.append((b, sn, None)); continue
            out.append((b, sn, float(ss[k])))
            if draw:
                cv2.circle(vis, tuple(int(v) for v in q0), 1, (255, 255, 0), -1)
                cv2.circle(vis, tuple(int(v) for v in xy[k]), 1, (0, 255, 0) if abs(ss[k]) <= 2 else (0, 0, 255), -1)
        res[nm] = out
    if draw and OUT:
        cv2.imwrite('%s/ob_%03d_found.jpg' % (OUT, h), vis)
    return res
def solve_delta(h, L):
    """GE aims at its terrain, whose height over the model's field is not known: the one free number per view,
    chosen so the median absolute offset over every line is least."""
    best = None
    for d in np.arange(-6, 6.01, 0.5):
        R = measure(h, L, d); v = np.abs([o[2] for out in R.values() for o in out if o[2] is not None])
        m = np.median(v) if len(v) else 99
        if best is None or m < best[0]: best = (m, d)
    return best[1]
def stat(v):
    v = np.array(v); return 'median %+.2f  rms %.2f  95%% %.2f' % (np.median(v), np.sqrt((v ** 2).mean()), np.percentile(np.abs(v), 95))
if __name__ == '__main__':
    L = lines(); allr = {}; rep = {}
    for h in (0, 90, 180, 270):
        d = solve_delta(h, L); R = measure(h, L, d, draw=True)
        print('view %3d: aim height %+.1f m' % (h, d))
        for nm, out in R.items():
            v = [o[2] for o in out if o[2] is not None]
            if not out: continue
            print('view %3d  %-12s found %3d/%3d  %s' % (h, nm, len(v), len(out), stat(v) if v else '-'))
            allr.setdefault(nm, []).extend(v)
            rep.setdefault(str(h), {})[nm] = {'found': len(v), 'of': len(out), 'offsets': [o for o in out]}
    for nm, v in allr.items():
        print('ALL       %-12s n=%4d  %s   within 2 m: %d%%' % (nm, len(v), stat(v), 100 * np.mean(np.abs(v) <= 2)))
    if OUT:
        json.dump(rep, open('%s/obmeasure.json' % OUT, 'w'))
