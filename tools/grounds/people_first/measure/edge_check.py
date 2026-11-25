"""Score a roof outline against the satellite's edges: for every 0.25 deg, the distance from our edge to the nearest
place on that ray where the image steps from roof-bright to darker (a drop of DROP grey levels within 0.8 m, going
outward). Lenient like the shape audit's 'within 2 m' (busy ground can offer a near edge), so read it with the overlay.
Usage: edge_check.py outline.npy [label]   (outline.npy: rows angle_deg, radius_m in the roof frame)"""
import json, math, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, '..', 'src')
S = json.load(open(os.path.join(SRC, 'sat.json'))); D = json.load(open(os.path.join(SRC, 'geo_n.json'))); SH = D['roofshift']; M = S['mpp']
SAT = os.environ.get('PF_SAT', '/mnt/project-files/people-first-rebuild/review-imagery/reference/sat.png')
L = np.asarray(Image.open(SAT).convert('L')).astype(float); DROP = float(os.environ.get('DROP', 45))
def lum(x, y):
    u = S['px'] + x / M; v = S['py'] - y / M; i, j = int(v), int(u); fv, fu = v - i, u - j
    return (L[i, j] * (1 - fu) + L[i, j + 1] * fu) * (1 - fv) + (L[i + 1, j] * (1 - fu) + L[i + 1, j + 1] * fu) * fv
def score(A, R):
    out = []
    for a, r in zip(A, R):
        t = math.radians(a); rs = np.arange(r - 10, r + 10, 0.1)
        l = np.array([lum(SH[0] + q * math.cos(t), SH[1] + q * math.sin(t)) for q in rs])
        d = l[:-8] - l[8:]; e = rs[4:-4][(d > DROP) & (l[:-8] > 150)]
        out.append(np.abs(e - r).min() if len(e) else 10.0)
    return np.array(out)
if __name__ == '__main__':
    A, R = np.load(sys.argv[1])[:2]; e = score(A, R)
    print('%s: median %.2f m, within 1 m %.0f%%, within 2 m %.0f%%, 90%% within %.2f m' % (
        sys.argv[2] if len(sys.argv) > 2 else sys.argv[1], np.median(e), 100 * np.mean(e < 1), 100 * np.mean(e < 2), np.percentile(e, 90)))
    for lo in range(124, 397, 30):
        s = (A >= lo) & (A < lo + 30); print('  %3d-%3d deg: median %.2f m, within 2 m %.0f%%' % (lo % 360, (lo + 30) % 360, np.median(e[s]), 100 * np.mean(e[s] < 2)))
