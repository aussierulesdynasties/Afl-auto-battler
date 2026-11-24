"""Find Mars Stadium's light-tower heads in Google Earth's straight-down tiles and place each tower by parallax.

  python3 tools/grounds/mars/qa/towers.py <workdir>

A tower's lamp head is a compact cluster of white lamps. Straight down from H = 330 m, a head h metres up shows
pushed out from each tile's centre by h / (H - h) of its distance, by a different amount in each tile, so two or
more tiles give its true plan position and its height (least squares). Each guess is a rough plan position; the
head is the bright blob nearest it in each tile."""
import json, math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import trace as T

H = 330.0
HEAD_H = 37.7          # W's head, fixed by four tiles
GUESS = {'E': (97.0, 15.0), 'W': (-104.0, -32.0), 'NW': (-57.0, 70.0)}


def heads(work, name, guess, tiles):
    obs = []
    for n in tiles:
        e0, n0, *_ = T.tile(work, n)
        im = np.asarray(Image.open(os.path.join(work, 'ge', n + '.png')).convert('RGB')).astype(int)
        # the head shows pushed out: search round where a 40 m head would show
        ge, gn = guess; f = H / (H - 40.0)
        u0 = 640 + (e0 + (ge - e0) * f - e0) / T.S; v0 = 500 - (n0 + (gn - n0) * f - n0) / T.S - 140
        r = 70; a, b = int(v0) - r, int(u0) - r
        if a < 60 or b < 0 or a + 2 * r > im.shape[0] or b + 2 * r > im.shape[1]:
            continue
        w = im[a:a + 2 * r, b:b + 2 * r]
        lamp = (w.min(2) > 170) & (w.max(2) - w.min(2) < 60)
        lab, k = ndimage.label(ndimage.binary_closing(lamp, iterations=2))
        best = None
        for i in range(1, k + 1):
            ys, xs = np.nonzero(lab == i)
            if not (25 <= len(ys) <= 900) or max(np.ptp(ys), np.ptp(xs)) > 45:
                continue            # lamps: a head 2-9 m across; roofs are far bigger
            d = math.hypot(xs.mean() + b - u0, ys.mean() + a - v0)
            if best is None or d < best[0]:
                best = (d, xs.mean() + b, ys.mean() + a)
        if best:
            E = e0 + (best[1] - 640) * T.S; N = n0 - (best[2] + 140 - 500) * T.S
            obs.append((n, e0, n0, E, N))
    while True:
        r = solve(obs)
        if r is None or r[0] <= 3.0 or len(obs) <= 2:
            break
        obs.pop(int(np.argmax(r[3])))     # a tile that picked the wrong blob
    if r is None:
        return None, obs
    rms, P, k, _ = r
    # where the tiles' nadirs are close together the height is poorly fixed: then take the best-fixed tower's height
    # (W, four tiles) and place the head from each tile with it; the spread says how well it is placed
    k0 = H / (H - HEAD_H)
    each = np.array([(e0 + (E - e0) / k0, n0 + (N - n0) / k0) for _, e0, n0, E, N in obs])
    Q = each.mean(0)
    return {'e': round(float(P[0]), 2), 'n': round(float(P[1]), 2), 'head_h': round(float(H - H / k), 1),
            'tiles': len(obs), 'rms_px': round(float(rms), 2),
            'at_head_h': [round(float(Q[0]), 2), round(float(Q[1]), 2)],
            'spread_m': round(float(np.max(np.hypot(*(each - Q).T))), 2)}, obs


def solve(obs):
    if len(obs) < 2:
        return None
    # apparent = nadir + (P - nadir) * H / (H - h): solve for P and k = H / (H - h)
    best = None
    for k in np.arange(1.0, 1.25, 0.0005):
        P = np.mean([(e0 + (E - e0) / k, n0 + (N - n0) / k) for _, e0, n0, E, N in obs], 0)
        res = sum(math.hypot(e0 + (P[0] - e0) * k - E, n0 + (P[1] - n0) * k - N) ** 2 for _, e0, n0, E, N in obs)
        if best is None or res < best[0]:
            best = (res, P, k)
    res, P, k = best
    each = [math.hypot(e0 + (P[0] - e0) * k - E, n0 + (P[1] - n0) * k - N) / T.S for _, e0, n0, E, N in obs]
    return math.sqrt(res / len(obs)) / T.S, P, k, each


def main(work):
    tiles = sorted(f[:-4] for f in os.listdir(os.path.join(work, 'ge')) if (f.startswith('trace_') or f == 'top.png') and f.endswith('.png') and '_cam' not in f)
    out = {}
    for name, g in GUESS.items():
        r, obs = heads(work, name, g, tiles)
        out[name] = r
        print(name, r, [o[0] for o in obs])
    return out


if __name__ == '__main__':
    main(sys.argv[1])
