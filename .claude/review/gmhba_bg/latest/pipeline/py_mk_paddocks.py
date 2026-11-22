"""Hand-made paddock patchwork for the far land around Geelong: tex/mt/paddocks.png covers the whole far terrain
(-FA..FA both ways, 4096 px, ~15 m/px). Survey-grid rectangular paddocks (300-900 m sides) whose grid angle drifts slowly
across the region; each paddock gets a land use with its own colour: dry golden pasture, green pasture, irrigated green,
ploughed brown, stubble, canola-free crop green, bare red-brown; tonal mottling inside each paddock, darker fence and
shelterbelt lines on the boundaries. Colour is a multiplier around 1 (scene keeps its haze); writes paddocks.mean.
python -E py_mk_paddocks.py <far_extent_m>"""
import os, sys, numpy as np
from PIL import Image, ImageFilter
H = os.path.dirname(os.path.abspath(__file__)); R = np.random.default_rng(31)
FA = float(sys.argv[1]); N = 4096
g = (np.arange(N) + 0.5) / N * 2 * FA - FA
X, Y = np.meshgrid(g, -g)   # row 0 = north (+y), matching UV v = (y+FA)/2FA flipped by Blender's bottom-up v
def smooth(k, cnt, amp):
    f = np.zeros((N, N), np.float32)
    for _ in range(cnt):
        a, b = R.normal(0, k, 2); f += np.cos(a * X / FA + b * Y / FA + R.uniform(0, 6.3))
    return f / np.sqrt(cnt) * amp
ang = 0.12 + smooth(0.8, 4, 0.05)   # survey grid angle drifts
c, s = np.cos(ang), np.sin(ang); U = X * c - Y * s; V = X * s + Y * c
# road-grid blocks ~1.6 km, then each block split into paddocks
bu = np.floor(U / 1609.0); bv = np.floor(V / 1609.0)
h = lambda a, b, k: (np.sin(a * 12.9898 + b * 78.233 + k * 37.719) * 43758.5453) % 1.0
nu = 2 + np.floor(h(bu, bv, 1) * 4); nv = 1 + np.floor(h(bu, bv, 2) * 3)
fu = (U / 1609.0 - bu) * nu; fv = (V / 1609.0 - bv) * nv
pu = np.floor(fu); pv = np.floor(fv); pid = h(bu * 7 + pu, bv * 5 + pv, 3)
#           sRGB                weight
USES = [((196, 176, 118), 0.40),  # dry golden pasture (summer)
        ((150, 150, 96), 0.22),   # tired grey-green pasture
        ((112, 136, 74), 0.08),   # green pasture
        ((86, 122, 62), 0.03),    # irrigated / lucerne
        ((150, 118, 84), 0.10),   # ploughed brown
        ((206, 192, 146), 0.10),  # cereal stubble
        ((124, 98, 72), 0.06)]    # bare red-brown
cw = np.cumsum([w for _, w in USES]); cw /= cw[-1]
ui = np.searchsorted(cw, pid)
col = np.array([u for u, _ in USES], np.float32)[np.clip(ui, 0, len(USES) - 1)]
# measured colour: each paddock takes the median colour of the reference aerial (sat_far.png, 30 m/px) over its own
# area, so the patchwork follows the real dry-brown / olive / green distribution; land use from landuse.npy
SA = np.asarray(Image.open(os.path.join(H, 'data', 'gmhba', 'sat_far.png')).resize((N, N), Image.BILINEAR)).astype(np.float32)
LU = np.asarray(Image.fromarray(np.load(os.path.join(H, 'data', 'gmhba', 'landuse.npy'))).resize((N, N), Image.NEAREST))
key = np.round(pid * 1e6).astype(np.int64) * 7 + (bu * 1009 + bv).astype(np.int64); farm = LU == 0
uk, inv = np.unique(key, return_inverse=True); inv = inv.ravel()
farm = farm & (SA[..., 2] <= SA[..., 0] + 2)   # land-coloured pixels only (no sea, swamp or salt-pan blue)
def _bl(x, r):
    k = 2 * r + 1; q = np.pad(x.astype(np.float64)[::8, ::8], r, mode='edge'); c = np.pad(q.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    o = (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]); return np.asarray(Image.fromarray(o.astype(np.float32), 'F').resize((N, N), Image.BILINEAR))
_fw = _bl(farm, 12); _k = (2 * 12 + 1) ** 2; _fw = _fw / _k; _gm = np.array([np.median(SA[..., c][farm]) for c in range(3)], np.float32)
REG = np.stack([_bl(SA[..., c] * farm, 12) / _k / np.maximum(_fw, 0.05) for c in range(3)], -1)
_tw = np.clip(_fw / 0.3, 0, 1)[..., None]; REG = REG * _tw + _gm * (1 - _tw)   # 1.4 km regional farm colour
for ch in range(3):
    v = SA[..., ch].ravel(); w = farm.ravel().astype(np.float64)
    sm = np.bincount(inv, v * w, len(uk)); cn = np.bincount(inv, w, len(uk))
    tot = np.bincount(inv, None, len(uk)); fr = (cn / np.maximum(tot, 1))[inv].reshape(N, N)
    m = (sm / np.maximum(cn, 1))[inv].reshape(N, N); t = np.clip((fr - 0.2) / 0.4, 0, 1)
    col[..., ch] = (m * t + REG[..., ch] * (1 - t)) * 1.08 + 6   # scene exposure lifts the aerial's dark JPEG midtones slightly
col *= (0.92 + 0.16 * h(bu * 3 + pu, bv * 11 + pv, 4))[..., None]   # each paddock its own shade
col *= (1 + smooth(40, 10, 0.05) + R.normal(0, 0.03, (N, N)))[..., None]   # mottling: stock tracks, damp hollows
# boundaries: fence lines everywhere, about a third carry a dark cypress/sugar-gum shelterbelt
eu = np.minimum(fu - pu, 1 - (fu - pu)) * 1609.0 / nu; ev = np.minimum(fv - pv, 1 - (fv - pv)) * 1609.0 / nv
edge = np.minimum(eu, ev)
belt = h(bu * 13 + np.round(fu), bv * 17 + np.round(fv), 5) < 0.35
road = np.minimum(np.minimum(U / 1609.0 - bu, 1 - (U / 1609.0 - bu)), np.minimum(V / 1609.0 - bv, 1 - (V / 1609.0 - bv))) * 1609.0 < 9
col[(edge < 10) & ~belt] *= 0.86
col[(edge < 22) & belt] = col[(edge < 22) & belt] * 0.25 + np.array((52, 66, 46), np.float32) * 0.75
col[road] = col[road] * 0.4 + np.array((150, 140, 120), np.float32) * 0.6   # gravel/sealed country roads
urb = LU == 1; fo = LU == 2   # towns: grey roof/street speckle on a 100 m block grid; forest: dark canopy clumps
blk = ((np.abs((X % 100) - 50) > 44) | (np.abs((Y % 100) - 50) > 44))
uc = np.array((126, 122, 116), np.float32) * (0.85 + 0.3 * R.random((N, N)))[..., None]; uc[blk] = (100, 100, 98)
SAu = np.asarray(Image.fromarray(SA.astype(np.uint8)).filter(ImageFilter.BoxBlur(6))).astype(np.float32)   # aerial suburb tone over ~180 m: roofs, gardens and street trees together
col[urb] = (SAu * (0.94 + 0.12 * R.random((N, N)))[..., None] * np.where(blk, 0.9, 1.0)[..., None])[urb]   # measured suburb colour, faint street grid
# industrial/commercial estates (OSM): hand-painted sheet-metal roofs, one colour per roof on a ~75 x 45 m lot grid
# (zincalume and Colorbond greys, a few Surfmist whites), asphalt yards and driveways between them
IND = np.asarray(Image.fromarray(np.load(os.path.join(H, 'data', 'gmhba', 'industrial_osm.npy')).astype(np.uint8) * 255).resize((N, N), Image.NEAREST)) > 0
RP = np.array([(170, 172, 170), (186, 186, 180), (140, 144, 142), (226, 226, 220), (98, 104, 108), (78, 82, 80)], np.float32); RW = np.cumsum([0.35, 0.2, 0.15, 0.1, 0.1, 0.1])
lu_, lv_ = np.floor(U / 75.0), np.floor(V / 45.0); rk = h(lu_, lv_, 9); rc = RP[np.clip(np.searchsorted(RW, rk), 0, 5)]
yard = (h(lu_, lv_, 11) < 0.25) | ((U % 75.0) > 62) | ((V % 45.0) > 36)
rc[yard] = (88, 88, 86); col[IND] = rc[IND]
fc = np.array((52, 66, 44), np.float32) * (0.75 + 0.5 * np.clip(1 + smooth(120, 12, 0.5), 0, 2) / 2)[..., None]
col[fo] = fc[fo]
wa = LU == 3; col[wa] = np.array((62, 84, 98), np.float32) * (0.92 + 0.16 * R.random((N, N)))[..., None][wa]   # lakes, salt pans and sea inside the far ring: deep water tone, never aerial glare
col = col * 0.7 + col.mean(2, keepdims=True) * 0.3   # summer haze takes the edge off the colour
im = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5))
a = np.asarray(im).astype(np.float32) / 255; lm = float((a ** 2.2).mean())
im.save(os.path.join(H, 'tex', 'mt', 'paddocks.png')); open(os.path.join(H, 'tex', 'mt', 'paddocks.mean'), 'w').write('%.4f' % lm)
np.save(os.path.join(H, 'tex', 'mt', 'paddocks_belt.npy'), ((edge < 22) & belt)[::8, ::8])   # 512 grid for shelterbelt geometry
print('paddocks', im.size, 'mean', lm)
