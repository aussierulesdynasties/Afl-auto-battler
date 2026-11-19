# Plain-wall columns of every texture (tex/wallcols.json), for build.py's corner layout: a column is wall when it
# matches the tile's per-row median (no window, mullion or panel edge in it). 20 samples per metre of tile width.
# The "best" column (closest to the median) is what a corner strip shows. Run after paint3.py.
import numpy as np, json, os
from PIL import Image
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex') + '/'
TILE = json.load(open(OUT + 'tiles.json')); W = {}
SP = json.load(open(OUT + 'winspans.json')) if os.path.exists(OUT + 'winspans.json') else {}
for name, (tw, tv) in TILE.items():
    if not os.path.exists(OUT + name + '.png'): continue
    a = np.asarray(Image.open(OUT + name + '.png').convert('RGB')).astype(float)
    n = max(2, int(round(tw * 20))); xs = (np.arange(n) + 0.5) / n * a.shape[1]
    med = np.median(a, 1)  # per-row median colour
    d = np.array([np.abs(a[:, int(x)] - med).mean() for x in xs])
    wall = d < 7.0
    if name in SP and SP[name]:  # windows drawn by paint2/paint3: a column is wall exactly when no window covers it
        uu = (np.arange(n) + 0.5) / n * tw; wall = np.array([not any(a <= u <= b for a, b in SP[name]) for u in uu])
        d = np.where(wall, d, 1e9)
    W[name] = {'n': n, 'wall': [bool(v) for v in wall], 'best': int(np.argmin(d))}
json.dump(W, open(OUT + 'wallcols.json', 'w', newline=''))
# corner strip texture per facade texture (tex/cs_<name>.png): the wall's own plain colour (median of the tile) with
# a faint vertical grain, for the solid strip build.py puts at every sharp corner (director: "a solid strip at every corner")
MJ = json.load(open(os.path.join(os.path.dirname(OUT[:-1]), 'mcg.json')))
FAC = {s_[3] for s_ in MJ['facade']} | {k[i] for k in MJ.get('blocks', []) for i in (5, 6)}
rng = np.random.default_rng(7)
for name in FAC:
    if not os.path.exists(OUT + name + '.png'): continue
    a = np.asarray(Image.open(OUT + name + '.png').convert('RGB')).astype(float); tw, tv = TILE[name]
    c = np.median(a.reshape(-1, 3), 0); h = max(32, int(tv * 40)); w = 24
    g = c[None, None, :] * (1 + rng.normal(0, 0.012, (h, 1, 1)) + rng.normal(0, 0.008, (h, w, 1)))
    g[-max(2, h // 40):] *= 0.9  # foot shadow
    Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).save(OUT + 'cs_' + name + '.png'); TILE['cs_' + name] = (0.6, tv)
json.dump(TILE, open(OUT + 'tiles.json', 'w'))

print(len(W), 'textures;', sum(1 for v in W.values() if not any(v['wall'])), 'with no plain column')
