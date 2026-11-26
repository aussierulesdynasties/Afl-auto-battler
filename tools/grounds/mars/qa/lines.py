"""Project the model's ring lines (fence, seat front, back row, roof front and back edges, back-wall base) into
Google Earth's oblique shots through the calibrated camera, and measure how far each sits from Google Earth's edge.

  python3 tools/grounds/mars/qa/lines.py <workdir> <outdir> view [view ...]

The camera is ge_compare.py's (35 deg vertical over the 1000 px window, centred on it, so f = 1585.8 px; the crop
keeps rows 140-860; the look-at point at Google Earth's turf, ge_alt), lifted where Google Earth lifted it. Each line
is sampled every metre; at each visible sample the strongest brightness edge within 12 px across the line is taken
as Google Earth's, and the offset is turned into metres at that sample's distance (depth / f). A sample is skipped
where no edge is clear (gradient under 18 grey levels a pixel). Prints, per view and line, the median offset and the
90th percentile in metres, and draws the lines (and the found edges) on the shot."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..')); sys.path.insert(0, os.path.join(HERE, '..', 'model'))
import compare as C
import ge_compare as G
import build as B

F = 500.0 / math.tan(math.radians(17.5))
SEARCH, MIN_GRAD = 12, 18.0


def camera(v, work):
    g = G.GROUNDS['mars']; e, n, u = v['at']
    h, t, d = math.radians(v['h']), math.radians(v['t']), v['d']
    dirv = np.array([math.sin(t) * math.sin(h), math.sin(t) * math.cos(h), -math.cos(t)])
    cam = np.array([e, n, u]) - d * dirv; tgt = np.array([e, n, u], float)
    ro = G.readouts(os.path.join(work, 'ge', v['name'] + '_cam.png'))
    if ro and ro[0][0] is not None:
        lift = ro[0][0] - g['ge_alt'] - cam[2]
        if abs(lift) > 1.5: cam[2] += lift; tgt[2] += lift
    return cam, tgt


def project(cam, tgt, P):
    fwd = tgt - cam; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 0, 1.0]); right /= np.linalg.norm(right); up = np.cross(right, fwd)
    q = P - cam; z = q @ fwd
    return np.stack([640 + F * (q @ right) / z, 360 - F * (q @ up) / z], 1), z


def rings():
    """name -> list of polylines [(x, y, z), ...] in model metres (x east, y north, z up from the turf)"""
    L = {'fence top': [[(*B.pol(b, B.fence_r(b)), B.D['fence_h']) for b in np.arange(0, 360.01, 0.5)]]}
    for S in B.D['stands']:
        if S['kind'] != 'single': continue
        bs = np.arange(S['b0'], S['b1'] + 1e-6, 0.5)
        zs, zr = S['z_seat'], S['z_roof']
        def ring(rfun, z):
            return [(*B.pol(b, rfun(b)), z) for b in bs]
        L.setdefault('seat front', []).append(ring(lambda b: B.fence_r(b % 360) + S['seat_front'], zs[0]))
        L.setdefault('roof front', []).append(ring(lambda b: B.interp(S['roof'], b)[0], zr[0]))
        L.setdefault('roof back', []).append(ring(lambda b: B.interp(S['roof'], b)[1], zr[1]))
        rb = lambda b: (B.fence_r(b % 360) + S['back_rel']) if 'back_rel' in S else B.interp(S['roof'], b)[1] - S['back_in']
        L.setdefault('back wall base', []).append(ring(rb, 0.0))
    return L


def measure(img, pts, z):
    g = np.asarray(img.convert('L')).astype(float); hgt, wid = g.shape
    out = []; found = []
    for i in range(1, len(pts) - 1):
        p = pts[i]; t = pts[i + 1] - pts[i - 1]
        if np.linalg.norm(t) < 1e-6 or z[i] <= 0: continue
        nrm = np.array([-t[1], t[0]]) / np.linalg.norm(t)
        ks = np.arange(-SEARCH, SEARCH + 1)
        q = p[None, :] + ks[:, None] * nrm[None, :]
        if (q[:, 0] < 2).any() or (q[:, 0] > wid - 3).any() or (q[:, 1] < 70).any() or (q[:, 1] > hgt - 3).any():
            continue
        prof = g[np.round(q[:, 1]).astype(int), np.round(q[:, 0]).astype(int)]
        grad = np.abs(np.gradient(prof))
        k = int(np.argmax(grad))
        if grad[k] < MIN_GRAD: continue
        out.append(ks[k] * z[i] / F); found.append(q[k])
    return np.array(out), found


def main(work, outd, names):
    os.makedirs(outd, exist_ok=True)
    views = {v['name']: v for v in json.load(open(os.path.join(HERE, 'views.json')))}
    for v in views.values():
        a = v.get('at', [0, 0, 0]); v['at'] = [a[0] + C.FIT[0], a[1] - C.FIT[1], a[2]]
    L = rings(); col = {'fence top': (255, 0, 255), 'seat front': (0, 255, 255), 'roof front': (255, 255, 0),
                         'roof back': (255, 128, 0), 'back wall base': (0, 255, 0)}
    rep = {}
    for nm in names:
        v = views[nm]; cam, tgt = camera(v, work)
        img = Image.open(os.path.join(work, 'ge', nm + '.png')).convert('RGB'); d = ImageDraw.Draw(img)
        rep[nm] = {}
        for k, polys in L.items():
            allo = []
            for poly in polys:
                P = np.array(poly, float); px, z = project(cam, tgt, P)
                keep = z > 1
                d.line([tuple(p) for p in px[keep]], fill=col[k], width=1)
                o, found = measure(img, px, z)
                for f in found: d.point(tuple(f), fill=(255, 255, 255))
                allo += list(o)
            if len(allo) >= 10:
                a = np.array(allo)
                rep[nm][k] = {'n': len(a), 'median_m': round(float(np.median(a)), 2), 'p90_abs_m': round(float(np.percentile(np.abs(a), 90)), 2)}
        img.save(os.path.join(outd, nm + '_lines.png'))
        print(nm, json.dumps(rep[nm]))
    return rep


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
