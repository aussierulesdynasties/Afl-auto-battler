"""Measure the two 2026 stands (new_se, new_s) in Google Earth's straight-down tiles (Dec 2025), as offsets from the fence
curve along its normal, the frame model/build.py's pol() uses:

  python3 tools/grounds/mars/qa/newstands.py <workdir>          (the trace_* shots compare.py planned and ge_shoot.js took)

- unroll(): resamples a tile onto (bearing, offset from the fence) at an assumed height h, undoing the tile's parallax
  (apparent = nadir + (P - nadir) * H / (H - h), H = 330 m).
- The south-east roof was on by Dec 2025. Its white sheeting's front and back edges, and the front rail ahead of it, are read
  in two tiles (trace_s, trace_e) for h = 0..30 m; the height where the tiles agree is the edge's height, and its offset there
  is its plan position.
- The south stand had only its steel frame and terraces up. Its treads are counted along the offset (light/dark period).
  Its frame's back chord was picked by hand on the unrolled tile at h = 15 m (the roof's measured height); a 3 m error in that
  height moves a pick under 1 m in plan.
Only numbers leave this script: no imagery is kept."""
import json, math, os, sys
import numpy as np
from PIL import Image

LAT0, LON0 = -37.539307, 143.848166
S = 2 * 330 * math.tan(math.radians(17.5)) / 1000.0; H = 330.0
HERE = os.path.dirname(os.path.abspath(__file__))


def fence():
    C = json.load(open(os.path.join(HERE, 'fence_curve.json'))); c = np.array(C['coef']); fc = C['centre']
    t = np.radians(np.arange(0, 360, 0.02)); k = (len(c) - 1) // 2
    r = c[0] + sum(c[2 * j - 1] * np.cos(j * t) + c[2 * j] * np.sin(j * t) for j in range(1, k + 1))
    x, y = fc[0] + r * np.sin(t), fc[1] + r * np.cos(t)
    dx = np.gradient(np.r_[x[-1:], x, x[:1]])[1:-1]; dy = np.gradient(np.r_[y[-1:], y, y[:1]])[1:-1]
    n = np.arctan2(-dy, dx); b = np.degrees(np.arctan2(x, y)) % 360; o = np.argsort(b); b, R, n = b[o], np.hypot(x, y)[o], np.unwrap(n[o])
    return np.r_[b[-1:] - 360, b, b[:1] + 360], np.r_[R[-1:], R, R[:1]], np.r_[n[-1:] - 2 * np.pi, n, n[:1] + 2 * np.pi]


FB, FR, FN = fence()


def pol(b, off):
    b = np.asarray(b, float) % 360; a = np.radians(b); rf = np.interp(b, FB, FR); n = np.interp(b, FB, FN)
    return np.stack([rf * np.sin(a) + off * np.sin(n), rf * np.cos(a) + off * np.cos(n)], -1)


def tile(work, name):
    urls = json.load(open(os.path.join(work, 'urls.json')))
    url = [u for p, u in urls if p.endswith('/' + name + '.png')][0]; lat, lon = [float(x) for x in url.split('@')[1].split(',')[:2]]
    return ((lon - LON0) * 111320.0 * math.cos(math.radians(LAT0)), (lat - LAT0) * 110574.0,
            np.asarray(Image.open(os.path.join(work, 'ge', name + '.png')).convert('RGB')))


def unroll(t, h, b0, b1, o0, o1, db, do):
    e0, n0, im = t; B = np.arange(b0, b1, db); O = np.arange(o0, o1, do); out = np.zeros((len(O), len(B), 3), np.uint8)
    for j, b in enumerate(B):
        p = pol(np.full(len(O), b), O); E = e0 + (p[:, 0] - e0) * H / (H - h); N = n0 + (p[:, 1] - n0) * H / (H - h)
        u = np.round(640 + (E - e0) / S).astype(int); v = np.round(500 - (N - n0) / S - 140).astype(int)
        ok = (u >= 0) & (u < im.shape[1]) & (v >= 0) & (v < im.shape[0]); out[ok, j] = im[v[ok], u[ok]]
    return B, O, out


def white_edges(col, O, do):
    """front and back of the first run of roof sheeting (bluish white) at least 3 m long"""
    W = (col.min(1) > 150) & (col[:, 2] >= col[:, 0] + 5); k = 0
    while k < len(W):
        if W[k]:
            m = k
            while m < len(W) and W[m]: m += 1
            if (m - k) * do >= 3.0: return O[k], O[m - 1]
            k = m
        else: k += 1
    return None, None


def front_rail(col, O, do):
    """the first bright rail after 1.5 m of dark (the roof's front, over the shadowed stand)"""
    g = col.mean(1); n = int(1.5 / do)
    for k in range(n, len(g)):
        if g[k] > 150 and (g[k - n:k] < 80).mean() > 0.8: return O[k]
    return None


def parallax(tiles, b0, b1, step, read, do=0.05):
    """for each bearing: the height (0..30 m) where both tiles agree on the edge read() finds, and the edge's offset there"""
    best = {}
    for h in np.arange(0, 30.01, 0.5):
        per = []
        for t in tiles:
            B, O, a = unroll(t, h, b0, b1 + 1e-6, -5, 45, step, do); per.append([read(a[:, j].astype(int), O, do) for j in range(len(B))])
        for j, b in enumerate(B):
            v = [p[j] for p in per]
            if None not in v and (b not in best or np.ptp(v) < best[b][0]): best[b] = (float(np.ptp(v)), float(h), float(np.mean(v)))
    return best


def treads(t, b, o0=3, o1=34):
    """the treads seen along bearing b (light tread tops between dark risers): count, first and last offset, and their
    spacing over the whole run (a tread the edge search misses widens a single gap but not this)"""
    B, O, a = unroll(t, 8.0, b, b + 0.01, 0, 35, 0.25, 0.05)   # at the terraces' middle height (about 5 to 11 m up)
    col = np.convolve(a[:, 0].astype(float).mean(1), np.ones(5) / 5, 'same')
    seg = (O > o0) & (O < o1); x = col[seg]; o = O[seg]; pk = []
    for k in range(6, len(x) - 6):
        if x[k] == x[k - 6:k + 7].max() and x[k] > np.median(x[max(0, k - 30):k + 30]) + 12 and (not pk or o[k] - o[pk[-1]] >= 0.5): pk.append(k)
    p = o[pk]; p = p[(p > 7) & (p < 31)]
    return len(p), float(p.min()), float(p.max()), float((p.max() - p.min()) / max(1, len(p) - 1))


def main(work, only=''):
    ts, te = tile(work, 'trace_s'), tile(work, 'trace_e')
    if only == 'treads': return print_treads(ts)
    print('South-east roof (trace_s + trace_e), offsets from the fence along its normal:')
    rail = parallax([ts, te], 101, 139, 2, lambda c, O, d: front_rail(c, O, d))
    fr = parallax([ts, te], 101, 139, 2, lambda c, O, d: white_edges(c, O, d)[0])
    bk = parallax([ts, te], 101, 139, 2, lambda c, O, d: white_edges(c, O, d)[1])
    for b in sorted(rail):
        r, f, k = rail[b], fr.get(b), bk.get(b)
        print('  b %5.1f  front rail %5.2f m out at %4.1f m up (tiles agree to %.2f m);  sheeting %5.2f to %5.2f m out at %4.1f / %4.1f m up'
              % (b, r[2], r[1], r[0], f[2] if f else -1, k[2] if k else -1, f[1] if f else -1, k[1] if k else -1))
    print_treads(ts)


def print_treads(ts):
    print('South stand treads (trace_s, Dec 2025, its upper terraces laid), read at 8 m up:')
    for b in (157.5, 161.0, 163.5, 166.0, 172.0, 174.0):
        print('  b %5.1f  %d treads from %.1f to %.1f m out, %.2f m apart on average' % ((b,) + treads(ts, b)))


if __name__ == '__main__':
    main(*sys.argv[1:3])
