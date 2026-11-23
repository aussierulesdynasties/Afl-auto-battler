"""Prep a stadium background scene from OSM + terrain tiles (plain Python, PIL + numpy).
usage: prep.py spec.json
Writes data/<name>/prep/: ground.png (hand-painted ground cover, near square),
near_h.npy, far_h.npy (heights, m, relative to ground centre), buildings.json, trees.json, meta.json
Frame: x east, y north (metres), origin = the ground's oval centre.
"""
import sys, os, json, math, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

spec = json.load(open(sys.argv[1]))
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, 'data', spec['name'])
OUT = os.path.join(D, 'prep'); os.makedirs(OUT, exist_ok=True)
lat0, lon0 = spec['lat'], spec['lon']
KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
def xy(lat, lon): return ((lon - lon0) * KX, (lat - lat0) * KY)
rng = np.random.default_rng(spec.get('seed', 1))
PAL = spec['palette']

# ---------------- terrain ----------------
def tile_xy(lat, lon, z):
    n = 2 ** z
    return (lon + 180) / 360 * n, (1 - np.arcsinh(np.tan(np.radians(lat))) / np.pi) / 2 * n
def mosaic(z):
    fs = glob.glob(os.path.join(D, 'tiles', f'{z}_*.png'))
    xs = [int(f.split('_')[-2]) for f in fs]; ys = [int(f.split('_')[-1][:-4]) for f in fs]
    x0, y0 = min(xs), min(ys)
    M = np.zeros(((max(ys) - y0 + 1) * 256, (max(xs) - x0 + 1) * 256), np.float32)
    for f, x, y in zip(fs, xs, ys):
        a = np.asarray(Image.open(f).convert('RGB')).astype(np.float32)
        M[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    # the tiles carry spikes and pits (masts, bad cells: a 300 m cone beside the WACA, 2.5 km at York Park, often in
    # clusters): a cell further than a cliff from the median of the 5 x 5 cells round it takes that median
    from scipy.ndimage import median_filter
    T = 30.0 if z >= 14 else 80.0
    for _ in range(3):
        med = median_filter(M, size=5, mode='nearest'); bad = np.abs(M - med) > T
        if not bad.any(): break
        print('terrain z%d: %d spike cells smoothed' % (z, bad.sum()))
        M = np.where(bad, med, M)
    return M, x0, y0
def sampler(z):
    M, x0, y0 = mosaic(z)
    def h(X, Y):  # metres grid -> height (bilinear)
        lat = lat0 + Y / KY; lon = lon0 + X / KX
        tx, ty = tile_xy(lat, lon, z)
        px = (tx - x0) * 256 - 0.5; py = (ty - y0) * 256 - 0.5
        i = np.clip(np.floor(px).astype(int), 0, M.shape[1] - 2); j = np.clip(np.floor(py).astype(int), 0, M.shape[0] - 2)
        fx = np.clip(px - i, 0, 1); fy = np.clip(py - j, 0, 1)
        return (M[j, i] * (1 - fx) * (1 - fy) + M[j, i + 1] * fx * (1 - fy) + M[j + 1, i] * (1 - fx) * fy + M[j + 1, i + 1] * fx * fy)
    return h
hn, hf = sampler(14), sampler(12)
NEAR = spec['near_half_m']; NS = spec['near_step_m']
g = np.arange(-NEAR, NEAR + 1e-6, NS)
X, Y = np.meshgrid(g, g)
base = float(hn(np.array([0.0]), np.array([0.0]))[0])
near = hn(X, Y) - base
np.save(os.path.join(OUT, 'near_raw.npy'), near.astype(np.float32))
# flatten the stadium pad: 0 inside the clear ring, blend to real terrain over 250 m
r = np.hypot(X, Y); R0 = spec['clear_r_m']
w = np.clip((r - R0) / 250.0, 0, 1); w = w * w * (3 - 2 * w)
near = near * w
BANK = None
if spec.get('rail_cut'):
    rc = spec['rail_cut']
    js0 = json.load(open(os.path.join(D, 'osm.json'), encoding='utf-8'))['elements']
    nG = len(g); SU = 4; cm = Image.new('L', (nG * SU, nG * SU), 0); cd = ImageDraw.Draw(cm)
    def G(pts): return [((x + NEAR) / NS * SU + SU / 2, (y + NEAR) / NS * SU + SU / 2) for x, y in pts]   # grid rows run south -> north
    for el in js0:
        t = el.get('tags', {})
        if el['type'] != 'way' or not el.get('geometry'): continue
        pts = [xy(q['lat'], q['lon']) for q in el['geometry'] if q]
        if t.get('landuse') == 'railway' and len(pts) > 2: cd.polygon(G(pts), fill=255)
        if t.get('railway') == 'rail' and 'tunnel' not in t and 'bridge' not in t and len(pts) > 1:
            cd.line(G(pts), fill=255, width=max(1, int(round(rc.get('half_w', 8) * 2 / NS * SU))))
    from PIL import ImageFilter
    cm = cm.filter(ImageFilter.GaussianBlur(rc.get('bank_m', 6) / NS * SU)).resize((nG, nG), Image.BOX)
    cmask = np.asarray(cm).astype(np.float32) / 255
    cmask = np.clip((cmask - 0.12) / 0.45, 0, 1); cmask = cmask * cmask * (3 - 2 * cmask)  # flat floor, smooth bank
    fade = np.clip((rc['r_end'] - r) / (rc['r_end'] - rc['r_full']), 0, 1)
    FP = os.path.join(OUT, 'footprint.json')
    if rc.get('keep_footprint') and os.path.exists(FP):   # the ground model's own outline stays on solid ground
        RK = np.array(json.load(open(FP)))[((np.degrees(np.arctan2(Y, X)) % 360) // 2).astype(int)]
        cmask = cmask * np.clip((np.hypot(X, Y) - RK - 1.5) / rc.get("keep_bank_m", 2.0), 0, 1)
    if rc.get('keep_ellipse') and not rc.get('keep_footprint'):   # the ground model's own plaza stays on solid ground
        ex, ey, ea, eb = rc['keep_ellipse']
        q = np.hypot((X - ex) / ea, (Y - ey) / eb); cmask = cmask * np.clip((q - 1.0) / 0.035, 0, 1)
    # cutting floor follows a heavily smoothed ground (the raw DEM carries sheds and noise), not the raw cells
    def sblur(A, sig):
        k = np.exp(-0.5 * (np.arange(-3 * sig, 3 * sig + 1) / sig) ** 2); k /= k.sum()
        P = np.pad(A, len(k) // 2, mode='edge')
        P = np.apply_along_axis(lambda v: np.convolve(v, k, 'valid'), 0, P)
        return np.apply_along_axis(lambda v: np.convolve(v, k, 'valid'), 1, P)
    floor = sblur(near, max(1, int(round(60 / NS)))) - rc['depth']
    m_ = cmask * fade
    near = near * (1 - m_) + np.minimum(floor, near) * m_
    np.save(os.path.join(OUT, 'rail_cm.npy'), cmask.astype(np.float32))
    np.save(os.path.join(OUT, 'rail_floor.npy'), np.where(m_ > 0.02, near, np.nan).astype(np.float32))
    gy_, gx_ = np.gradient(near, NS)
    BANK = np.clip((np.hypot(gx_, gy_) - 0.12) / 0.2, 0, 1) * (m_ > 0.01)   # cutting side walls, grid rows S->N
np.save(os.path.join(OUT, 'near_h.npy'), near.astype(np.float32))
FAR = spec['far_half_m']; FS = spec['far_step_m']
gf = np.arange(-FAR, FAR + 1e-6, FS)
XF, YF = np.meshgrid(gf, gf)
far = hf(XF, YF) - base
np.save(os.path.join(OUT, 'far_h.npy'), far.astype(np.float32))
print('terrain', near.shape, far.shape, 'near range', near.min(), near.max(), 'far max', far.max())

# ---------------- OSM ----------------
js = json.load(open(os.path.join(D, 'osm.json'), encoding='utf-8'))['elements']
def ring(el):
    g = el.get('geometry') or []
    return [xy(p['lat'], p['lon']) for p in g if p]
def area(pts):
    a = 0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]): a += x1 * y2 - x2 * y1
    return a / 2

# ground cover image (near square), painted class by class in a fixed order
SS = spec.get('ground_ss', 2); PX = spec['ground_m_per_px'] / SS; N = int(2 * NEAR / PX)
def P(pts): return [((x + NEAR) / PX, (NEAR - y) / PX) for x, y in pts]
img = Image.new('RGB', (N, N), tuple(PAL['ground_default']))
dr = ImageDraw.Draw(img)
CLASS = spec['cover']  # list of [tagkey, tagvalue-or-*, palette key]
if spec.get('rivers_dry'): CLASS = [[k, v, 'sand' if pk == 'water' else pk] for k, v, pk in CLASS]
# open land: blend the default ground with a second cover by soft noise (patches 30-150 m)
if spec.get('open_mix'):
    def soft(cells, seed):
        r = np.random.default_rng(seed)
        return np.asarray(Image.fromarray((r.random((cells, cells)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)).astype(np.float32) / 255
    mix = 0.6 * soft(int(2 * NEAR / 150), 11) + 0.4 * soft(int(2 * NEAR / 35), 12)
    mk, lo, hi = spec['open_mix']
    t_ = 0.75 * np.clip((mix - lo) / (hi - lo), 0, 1)
    # steep slopes (from the real terrain) paint as rock
    gy_, gx_ = np.gradient(near, NS)
    sl = np.hypot(gx_, gy_)
    slI = np.asarray(Image.fromarray(np.clip(sl[::-1] * 255 / 1.5, 0, 255).astype(np.uint8)).resize((N, N), Image.BILINEAR)).astype(np.float32) * 1.5 / 255
    rk = np.clip((slI - 0.18) / 0.25, 0, 1)
    t_ = t_[..., None]; rk = rk[..., None]
    base_rgb = np.array(PAL['ground_default'], np.float32)[None, None, :] * (1 - t_) + np.array(PAL[mk], np.float32)[None, None, :] * t_
    base_rgb = base_rgb * (1 - rk) + np.array(PAL['rock'], np.float32)[None, None, :] * rk
    img = Image.fromarray(base_rgb.astype(np.uint8)); dr = ImageDraw.Draw(img)
def match(tags, k, v): return k in tags and (v == '*' or tags[k] in v.split('|'))
for k, v, pk in CLASS:
    for el in js:
        t = el.get('tags', {})
        if el['type'] == 'way' and match(t, k, v):
            pts = ring(el)
            if len(pts) > 2 and pts[0] == pts[-1]: dr.polygon(P(pts), fill=tuple(PAL[pk]))
        if el['type'] == 'relation' and match(t, k, v):
            for m in el.get('members', []):
                if m.get('role') == 'outer' and m.get('geometry'):
                    pts = [xy(p['lat'], p['lon']) for p in m['geometry'] if p]
                    if len(pts) > 2: dr.polygon(P(pts), fill=tuple(PAL[pk]))
            for m in el.get('members', []):   # islands (inner rings) keep the land under them (Heirisson Island)
                if m.get('role') == 'inner' and m.get('geometry'):
                    pts = [xy(p['lat'], p['lon']) for p in m['geometry'] if p]
                    if len(pts) > 2: dr.polygon(P(pts), fill=tuple(PAL['ground_default']))
# per-ground surface fixes from the reference photo: the OSM polygon whose centre is within 8 m of a point takes that colour
# lawn under the model: inside its fence outline (+3 m), or its pad box
FO = os.path.join(OUT, 'fence_mask.npy')
if spec.get('trim_base') and os.path.exists(FO):
    FM = Image.fromarray((np.load(FO) * 255).astype(np.uint8)); x0_, y0_ = P([(-260, 260)])[0]; x1_, y1_ = P([(260, -260)])[0]
    FM = FM.resize((max(1, round(x1_ - x0_)), max(1, round(y1_ - y0_))), Image.NEAREST)
    img.paste(Image.new('RGB', FM.size, tuple(PAL['lawn'])), (round(x0_), round(y0_)), FM)
elif spec.get('pad_box_m'):
    hx_, hy_ = spec['pad_box_m']; dr.rectangle([P([(-hx_, hy_)])[0], P([(hx_, -hy_)])[0]], fill=tuple(PAL['lawn']))
# surfaces traced from the straight-down satellite (metres, scene frame): [palkey, [[x, y], ...]]
for pk, poly in spec.get('paint_poly', []): dr.polygon(P([tuple(q) for q in poly]), fill=tuple(PAL[pk]))
for px_, py_, pk in spec.get('paint_at', []):
    for el in js:
        if el['type'] != 'way' or 'geometry' not in el: continue
        pts = ring(el)
        if len(pts) < 4 or pts[0] != pts[-1]: continue
        cx = sum(q[0] for q in pts[:-1]) / (len(pts) - 1); cy = sum(q[1] for q in pts[:-1]) / (len(pts) - 1)
        if math.hypot(cx - px_, cy - py_) < 8: dr.polygon(P(pts), fill=tuple(PAL[pk]))
# real place (spec 'real'): the aerial's ground colours on soft cover, and its tree canopy (real.py)
if spec.get('real'):
    import real as _real
    _S = _real.sat(D)
    if _S is not None:
        _SAr, _hr, _mr = _S
        _bp = [ring(el) for el in js if el['type'] == 'way' and 'building' in el.get('tags', {}) and 'geometry' in el]
        _tm = _real.canopy(_SAr); np.save(os.path.join(OUT, 'canopy.npy'), _tm)
        _cf = _real.colour_field(_SAr, _hr, _mr, [q for q in _bp if len(q) > 2], _tm)
        _HARD = [k for k in ('paved', 'parking', 'ballast', 'water', 'track', 'court_blue', 'court_navy', 'court_green', 'pool',
                             'infield', 'turf_blue', 'turf_runoff', 'road', 'path', 'netball') if k in PAL]
        _a0 = np.asarray(img).astype(np.int16); _hard = np.zeros(_a0.shape[:2], bool)
        for k in _HARD: _hard |= np.all(_a0 == np.array(PAL[k], np.int16)[None, None], -1)
        # mapped water, for scene.py's lift (the aerial's dark lawns come close to the water colour)
        _wm = np.all(_a0 == np.array(PAL['water'], np.int16)[None, None], -1)
        np.save(os.path.join(OUT, 'water_mask.npy'), _wm[::SS, ::SS])
        # field sampled at each ground pixel (the field spans the aerial's extent; outside it the palette stays)
        _gx = (np.arange(N) + 0.5) * PX - NEAR; _cell = _hr * 2 / _cf.shape[1]
        _fj = np.clip(((_gx + _hr) / _cell - 0.5), 0, _cf.shape[1] - 1); _fi = np.clip(((_hr - (NEAR - (np.arange(N) + 0.5) * PX)) / _cell - 0.5), 0, _cf.shape[0] - 1)
        from scipy.ndimage import map_coordinates
        _II, _JJ = np.meshgrid(_fi, _fj, indexing='ij')
        _F = np.stack([map_coordinates(_cf[..., k], [_II, _JJ], order=1) for k in range(3)], -1)
        _inside = (np.abs(_gx)[None, :] < _hr) & (np.abs(NEAR - (np.arange(N) + 0.5) * PX)[:, None] < _hr)
        _soft = (~_hard) & _inside
        _a0 = _a0.astype(np.float32)
        # crisp, per-place colours: every patch of soft ground bounded by roads, paths, buildings or a change of cover
        # takes the median of the aerial's open ground inside it (no trees, roofs, shadow); big patches keep a little
        # of the local field so a dry corner of a park still reads dry. Patches the aerial can't see open keep the field.
        from scipy import ndimage as _nd
        _ai = np.clip(((_hr - (NEAR - (np.arange(N) + 0.5) * PX)) / _mr).astype(int), 0, _SAr.shape[0] - 1)
        _aj = np.clip(((_gx + _hr) / _mr).astype(int), 0, _SAr.shape[1] - 1)
        _AS = _SAr[_ai[:, None], _aj[None, :]].astype(np.float32)
        _bm = Image.new('L', (_SAr.shape[1], _SAr.shape[0]), 0); _bd = ImageDraw.Draw(_bm)
        for q in _bp:
            if len(q) > 2: _bd.polygon([((x + _hr) / _mr, (_hr - y) / _mr) for x, y in q], fill=255)
        _Si = _SAr.astype(np.int16)
        _pool = (_Si[..., 2] > _Si[..., 1] + 8) & (_Si[..., 2] > _Si[..., 0] + 25)   # pools, blue roofs and courts: never ground
        _bad = (np.asarray(_bm.filter(ImageFilter.MaxFilter(5))) > 0) | _tm | _real.shade(_SAr) | _pool
        _ok = _soft & ~_bad[_ai[:, None], _aj[None, :]]
        _key = (_a0[..., 0].astype(np.int64) * 65536 + _a0[..., 1].astype(np.int64) * 256 + _a0[..., 2].astype(np.int64))
        # every mapped area (park, garden, school, lot...) is its own patch, smaller areas drawn over bigger ones
        _ar = []
        for el in js:
            tg = el.get('tags', {})
            if el['type'] != 'way' or 'geometry' not in el or 'building' in tg or 'highway' in tg: continue
            if not any(k in tg for k in ('landuse', 'leisure', 'amenity', 'natural', 'surface', 'place', 'man_made', 'tourism')): continue
            q = ring(el)
            if len(q) > 3 and q[0] == q[-1]: _ar.append((abs(area(q)), q, tg))
        _RI = Image.new('I', (N, N), 0); _rd = ImageDraw.Draw(_RI)
        _TWN = Image.new('L', (N, N), 0); _td_ = ImageDraw.Draw(_TWN)   # town land: house and shop blocks
        for k_, (_, q, tg_) in enumerate(sorted(_ar, key=lambda t: -t[0])):
            _rd.polygon(P(q), fill=k_ + 1)
            _td_.polygon(P(q), fill=255 if tg_.get('landuse') in ('residential', 'commercial', 'retail', 'industrial') else 0)
        _key = _key * 100000 + np.asarray(_RI).astype(np.int64)
        _LB = np.zeros(_soft.shape, np.int64); _nl = 0
        for kv in np.unique(_key[_soft]):
            l_, n_ = _nd.label(_soft & (_key == kv)); _LB[l_ > 0] = l_[l_ > 0] + _nl; _nl += n_
        _cnt = np.bincount(_LB[_ok].ravel(), minlength=_nl + 1); _tot = np.bincount(_LB[_soft].ravel(), minlength=_nl + 1)
        _idx = np.arange(1, _nl + 1)
        _med = np.stack([_nd.median(_AS[..., k], np.where(_ok, _LB, 0), _idx) for k in range(3)], -1) if _nl else np.zeros((0, 3))
        _med = np.nan_to_num(_med) * np.minimum(1.0, 175.0 / np.maximum(_med.max(-1, keepdims=True), 1))
        _good = np.concatenate([[False], (_cnt[1:] >= np.maximum(6, 0.08 * _tot[1:]))])
        _MC = np.zeros((_nl + 1, 3), np.float32); _MC[1:] = _med
        # town land (house blocks, shops, unmapped land between roads): one shared colour, the median of all of it, so
        # the blocks don't read as a quilt; Sentinel-2 then gives each street its light and dark
        _town = _soft & ((np.asarray(_RI) == 0) | (np.asarray(_TWN) > 0))
        # unmapped land counts as town only where it is built up (house blocks nobody tagged); open unmapped land (a
        # stadium plaza, a park's edge) keeps its own aerial colour
        _bmg = (np.asarray(_bm) > 0)[_ai[:, None], _aj[None, :]].astype(np.float32)
        _bmg = _nd.uniform_filter(_bmg, int(30 / PX) | 1)   # roofs within ~15 m
        _blk = np.bincount(_LB.ravel(), weights=_bmg.ravel(), minlength=_nl + 1) / np.maximum(np.bincount(_LB.ravel(), minlength=_nl + 1), 1)
        _town &= (np.asarray(_TWN) > 0) | (_blk[_LB] > 0.12)
        _tw_ok = _ok & _town
        if _tw_ok.sum() > 100:
            _tc = np.median(_AS[_tw_ok], 0); _tc = _tc * min(1.0, 175.0 / max(float(_tc.max()), 1))
            _tfrac = np.bincount(_LB[_town].ravel(), minlength=_nl + 1) / np.maximum(np.bincount(_LB.ravel(), minlength=_nl + 1), 1)
            # ...unless the block is plainly not house land (a sand site, a bare lot): it keeps its own colour
            _own = _good & (np.abs(_MC - _tc).mean(-1) > 30) & (_cnt >= 40)
            _tw = (_tfrac > 0.5) & ~_own
            _MC[_tw] = _tc; _good = _good | _tw; _good[0] = False
            print('town blocks keeping their own colour', int(((_tfrac > 0.5) & _own).sum()))
            print('town land colour', [int(v) for v in _tc])
        # a patch the shade test empties (grey asphalt, a trotting track's sand in low sun) takes the median of all its
        # open pixels instead: still its own colour, never the blurred field
        _bad2 = (np.asarray(_bm.filter(ImageFilter.MaxFilter(5))) > 0) | _tm | _pool
        _ok2 = _soft & ~_bad2[_ai[:, None], _aj[None, :]]
        _cnt2 = np.bincount(_LB[_ok2].ravel(), minlength=_nl + 1)
        _need = np.nonzero(~_good & (_cnt2 >= np.maximum(6, 0.08 * _tot)))[0]; _need = _need[_need > 0]
        if len(_need):
            _m2 = np.stack([_nd.median(_AS[..., k], np.where(_ok2, _LB, 0), _need) for k in range(3)], -1)
            _MC[_need] = np.nan_to_num(_m2) * np.minimum(1.0, 175.0 / np.maximum(_m2.max(-1, keepdims=True), 1)); _good[_need] = True
        # big patches (unmapped city land, a whole park) vary inside: the patch's colour is modulated by Sentinel-2's
        # 10 m colours (DEA, CC BY 4.0) relative to the patch's own Sentinel-2 median, so a dry corner reads dry
        _areaM = _tot * PX * PX; _wf = np.clip((_areaM - 8000) / 12000, 0, 1)
        _use = _soft & _good[_LB]
        _S2p = os.path.join(os.environ.get('WORK', '/home/user/work'), 's2', spec['name'] + '.npy')
        if os.path.exists(_S2p):
            _S2 = np.load(_S2p); _s2j = json.load(open(_S2p[:-4] + '.json')); _sh, _sm = _s2j['half_m'], _s2j['m_per_px']
            # only 10 m cells of open ground count (roofs, trees, pools and shade masked out), the rest filled from them
            _bad2 = np.asarray(Image.fromarray(((_bad) * 255).astype(np.uint8)).resize((_S2.shape[1], _S2.shape[0]), Image.BOX)).astype(np.float32) / 255 \
                if abs(_hr - _sh) < 1 and _SAr.shape[0] == int(2 * _hr / _mr) else np.zeros(_S2.shape[:2], np.float32)
            _v2 = (_bad2 < 0.3) & np.isfinite(_S2).all(-1)
            from scipy.ndimage import gaussian_filter as _gf
            _w2 = _gf(_v2.astype(np.float32), 1.0) + 1e-6
            _f2 = np.stack([_gf(np.where(_v2, _S2[..., c], 0), 1.0) for c in range(3)], -1) / _w2[..., None]
            _S2 = np.where(_v2[..., None], _S2, np.where((_w2 > 0.05)[..., None], _f2, np.nan))
            from scipy.ndimage import map_coordinates as _mc
            _yy = NEAR - (np.arange(N) + 0.5) * PX
            _si = np.clip((_sh - _yy) / _sm - 0.5, 0, _S2.shape[0] - 1); _sj = np.clip((_gx + _sh) / _sm - 0.5, 0, _S2.shape[1] - 1)
            _SI, _SJ = np.meshgrid(_si, _sj, indexing='ij')
            _S2g = np.stack([_mc(np.nan_to_num(_S2[..., c], nan=-1), [_SI, _SJ], order=1) for c in range(3)], -1)
            _s2ok = _use & (_S2g.min(-1) > 0)
            _s2med = np.stack([_nd.median(_S2g[..., c], np.where(_s2ok, _LB, 0), _idx) for c in range(3)], -1) if _nl else np.zeros((0, 3))
            _S2M = np.ones((_nl + 1, 3), np.float32); _S2M[1:] = np.nan_to_num(_s2med, nan=1.0); _S2M[_S2M <= 0] = 1.0
            _r = np.ones(_soft.shape + (3,), np.float32)
            _q = _S2g[_s2ok] / _S2M[_LB[_s2ok]]; _lq = _q.mean(-1, keepdims=True)
            _r[_s2ok] = np.clip(_lq, 0.9, 1.1)   # light and dark only: a hue shift read as smears
            _r = np.stack([_gf(_r[..., c], 6 / PX) for c in range(3)], -1)   # no 10 m stair steps
            # only unmapped land (city blocks) varies: a mapped park, track or ground keeps one clean colour, with edges
            _unm = _town
            _r = 1 + (_r - 1) * (_wf[_LB] * _unm)[..., None]
            _a0[_use] = _MC[_LB[_use]] * _r[_use]
            print('sentinel-2 variation inside big patches')
        else:
            _a0[_use] = _MC[_LB[_use]]
        # gardens: town land between the houses is lawn, dry grass or bare earth, and paving, in the aerial's own
        # proportions where it stands (each cell classed from the aerial, blended over ~2.5 m), each class in its
        # town-wide median colour; light and dark from above are kept. Classes only: no aerial pixel is copied.
        if _tw_ok.sum() > 100:
            _Ai = _AS.astype(np.int16); _R_, _G_, _B_ = _Ai[..., 0], _Ai[..., 1], _Ai[..., 2]
            _cl = np.where((_G_ > _R_ + 5) & (_G_ > _B_ + 5), 0, np.where((_R_ > _B_ + 14) & (_R_ < _G_ + 22), 1, 2))   # lawn, dry/bare, paved
            _see = _ok & ~(_R_ >= _G_ + 22)                          # terracotta roofs the outlines miss are not ground
            _tt = _town & _use
            _cc = []
            for k_ in range(3):
                _m_ = _tw_ok & _see & (_cl == k_)
                _cc.append(np.median(_AS[_m_], 0) if _m_.sum() > 50 else _tc)
            _cc = np.array([c * min(1.0, 175.0 / max(float(c.max()), 1)) for c in _cc], np.float32)
            # soft proportions: each class's share in the cell's neighbourhood (open ground only), unseen cells take the town mix
            _sh_ = []
            for k_ in range(3):
                _num = _nd.gaussian_filter(((_cl == k_) & _see).astype(np.float32), 2.5 / PX); _sh_.append(_num)
            _sh_ = np.stack(_sh_, -1); _den = _sh_.sum(-1, keepdims=True)
            _mix = np.bincount(_cl[_tw_ok & _see].ravel(), minlength=3).astype(np.float32); _mix /= _mix.sum()
            _wv = np.clip(_den / 0.25, 0, 1); _sh_ = _wv * _sh_ / np.maximum(_den, 1e-6) + (1 - _wv) * _mix[None, None, :]
            _gc = (_sh_[..., :, None] * _cc[None, None]).sum(-2)
            _rat = _a0 / np.maximum(_MC[_LB][..., :], 1)          # the Sentinel-2 light and dark already applied
            _tt = _tt & (np.abs(_MC[_LB] - _tc).max(-1) < 0.5)       # blocks that took the shared town colour
            _a0[_tt] = _gc[_tt] * np.clip(_rat[_tt], 0.85, 1.15)
            print('gardens: lawn / dry / paved colours', [[int(v) for v in c] for c in _cc], 'town mix', [round(float(v), 2) for v in _mix])
        # open unmapped land (a stadium's plaza, a park's paved edges): lawn, terracotta paving, grey paving and dry
        # ground where the aerial shows each, blended over ~2 m, each in its median colour on this land. One median
        # for the whole patch painted a plaza that is grey on one side and terracotta on the other one beige.
        _opn = _soft & _use & (np.asarray(_RI) == 0) & ~_town
        if _opn.sum() > 500:
            _Ai = _AS.astype(np.int16); _R_, _G_, _B_ = _Ai[..., 0], _Ai[..., 1], _Ai[..., 2]
            _cl = np.where((_G_ > _R_ + 5) & (_G_ > _B_ + 5), 0, np.where((_R_ > _G_ + 16) & (_R_ > _B_ + 24), 1, np.where(_R_ > _B_ + 14, 2, 3)))
            _cc = []
            for k_ in range(4):
                _m_ = _opn & _ok & (_cl == k_)
                _cc.append(np.median(_AS[_m_], 0) if _m_.sum() > 30 else np.median(_AS[_opn & _ok], 0) if (_opn & _ok).sum() > 30 else _MC[_LB][_opn].mean(0))
            _cc = np.array([c * min(1.0, 185.0 / max(float(c.max()), 1)) for c in _cc], np.float32)
            _sh_ = np.stack([_nd.gaussian_filter(((_cl == k_) & _ok).astype(np.float32), 2.0 / PX) for k_ in range(4)], -1)
            _den = _sh_.sum(-1, keepdims=True); _wv = np.clip(_den / 0.25, 0, 1)
            _gc = (_sh_[..., :, None] * _cc[None, None]).sum(-2) / np.maximum(_den, 1e-6)
            _a0[_opn] = (_wv * _gc + (1 - _wv) * _a0[..., :3])[_opn]
            print('open land: lawn / terracotta / dry / grey', [[int(v) for v in c] for c in _cc])
        _rest = _soft & ~_use; _a0[_rest] = _F[_rest]
        print('real ground patches', _nl, 'coloured from their own aerial median', int(_good.sum()))
        img = Image.fromarray(np.clip(_a0, 0, 255).astype(np.uint8)); dr = ImageDraw.Draw(img)
        print('real ground: aerial colours on', round(100 * _soft.mean()), '% of the ground; canopy', round(100 * _tm.mean(), 1), '%')
if spec.get('netball_courts'):   # Kardinia netball block (outline traced on the satellite; not mapped in OSM): slab + courts as geometry
    _nb = spec['netball_courts']; json.dump({'slabs': [['court_blue', _nb['slab']]], 'courts': _nb['courts'], 'pal': {'court_blue': PAL['court_blue'], 'netball': PAL['netball']}}, open(os.path.join(OUT, 'courts.json'), 'w'))
# tennis courts: courts within 6 m of each other share one slab (as built), white lines on top
def _hull(pts):
    pts = sorted(set(pts))
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]
def _obox(pts):
    Q = np.array(pts, float); best = None
    for i in range(len(Q)):
        d = Q[(i + 1) % len(Q)] - Q[i]
        if np.hypot(*d) < 0.5: continue
        u = d / np.hypot(*d); w = np.array([-u[1], u[0]]); a = Q @ u; b = Q @ w
        area = (a.max() - a.min()) * (b.max() - b.min())
        if best is None or area < best[0]:
            c = u * (a.max() + a.min()) / 2 + w * (b.max() + b.min()) / 2; L_, W_ = a.max() - a.min(), b.max() - b.min()
            best = (area, c, u if L_ >= W_ else w, max(L_, W_), min(L_, W_))
    if best is None:   # a degenerate outline (all corners within 0.5 m): a 1 m box at its centre
        c = Q.mean(0); best = (1.0, c, np.array([1.0, 0.0]), 1.0, 1.0)
    return [round(float(best[1][0]), 2), round(float(best[1][1]), 2), round(float(math.atan2(best[2][1], best[2][0])), 4), round(float(best[3]), 2), round(float(best[4]), 2)]
if spec.get('court_slabs'):
    CT = []
    for el in js:
        if el['type'] == 'way' and el.get('tags', {}).get('sport') == 'tennis' and 'geometry' in el:
            pts = ring(el)
            if len(pts) >= 4 and pts[0] == pts[-1] and math.hypot(*pts[0]) < 400:
                cx = sum(q[0] for q in pts[:-1]) / (len(pts) - 1); cy = sum(q[1] for q in pts[:-1]) / (len(pts) - 1)
                col = 'court_green'
                for px_, py_, pk in spec.get('paint_at', []):
                    if math.hypot(cx - px_, cy - py_) < 8: col = pk
                CT.append([pts[:-1], col])
    grp = list(range(len(CT)))
    def find(i):
        while grp[i] != i: i = grp[i]
        return i
    for i in range(len(CT)):
        for j in range(i + 1, len(CT)):
            if CT[i][1] == CT[j][1] and min(math.hypot(p[0] - q[0], p[1] - q[1]) for p in CT[i][0] for q in CT[j][0]) < 6: grp[find(i)] = find(j)
    for r in set(find(i) for i in range(len(CT))):
        mem = [CT[i] for i in range(len(CT)) if find(i) == r]
        dr.polygon(P(_hull([p for m in mem for p in m[0]])), fill=tuple(PAL[mem[0][1]]))
    for pts, col in CT:   # boundary line of each court, 5 cm-ish (1 px) white
        dr.line(P(pts + [pts[0]]), fill=(236, 236, 230), width=1)
    # geometry for scene.py: slab hull per group and each court's oriented box (lines are drawn as real geometry there)
    HK = []
    for hx_, hy_ in spec.get('hockey_at', []):   # hockey pitch: OSM pitch outline nearest this point (layout traced on the satellite)
        for el in js:
            if el['type'] == 'way' and el.get('tags', {}).get('leisure') == 'pitch' and 'geometry' in el:
                pts = ring(el)
                if len(pts) >= 4 and pts[0] == pts[-1]:
                    cx = sum(q[0] for q in pts[:-1]) / (len(pts) - 1); cy = sum(q[1] for q in pts[:-1]) / (len(pts) - 1)
                    if math.hypot(cx - hx_, cy - hy_) < 15: HK.append(_obox(pts[:-1]))
    print('hockey', HK)
    json.dump({'hockey': HK, 'slabs': [[mem_[0][1], _hull([p for m in mem_ for p in m[0]])] for mem_ in ([CT[i] for i in range(len(CT)) if find(i) == r] for r in set(find(i) for i in range(len(CT))))],
               'courts': [[col] + _obox(pts) for pts, col in CT], 'pal': dict({k: PAL[k] for k in set(c for _, c in CT)}, **{k: PAL[k] for k in ('turf_blue', 'turf_runoff') if k in PAL})},
              open(os.path.join(OUT, 'courts.json'), 'w'))
    print('court slabs', len(set(find(i) for i in range(len(CT)))), 'courts', len(CT))
# AFL ovals outside the model: boundary = the OSM pitch outline; lines and posts are built as geometry in scene.py
OV = []
for el in js:
    t = el.get('tags', {})
    if el['type'] != 'way' or t.get('leisure') != 'pitch' or 'australian_football' not in t.get('sport', '') or 'geometry' not in el: continue
    pts = ring(el)
    if len(pts) < 8 or pts[0] != pts[-1]: continue
    Q = np.array(pts[:-1], float)
    if not (200 < np.hypot(*Q.mean(0)) < 1500): continue
    OV.append([_obox(pts[:-1]), [[round(float(x), 2), round(float(y), 2)] for x, y in Q]])
json.dump(OV, open(os.path.join(OUT, 'ovals.json'), 'w'))
print('afl ovals', [o[0] for o in OV])
# baseball: dirt infield drawn from home plate (the pitch outline's sharpest corner, foul lines along its two edges)
for el in js:
    t = el.get('tags', {})
    if el['type'] != 'way' or t.get('sport') != 'baseball' or 'geometry' not in el: continue
    pts = ring(el)
    if len(pts) < 4 or pts[0] != pts[-1]: continue
    Q = np.array(pts[:-1], float); n_ = len(Q); best = None
    for i in range(n_):
        u = Q[i - 1] - Q[i]; w = Q[(i + 1) % n_] - Q[i]
        ang = math.acos(np.clip(np.dot(u, w) / (np.linalg.norm(u) * np.linalg.norm(w) + 1e-9), -1, 1))
        if best is None or ang < best[0]: best = (ang, i)
    H = Q[best[1]]; d_ = Q.mean(0) - H; a0 = math.atan2(d_[1], d_[0])
    if spec.get('baseball'):   # home plate and facing read off the reference photo
        bb = spec['baseball']
        if np.hypot(*(Q.mean(0) - np.array(bb['home']))) > 120: continue
        H = np.array(bb['home'], float); a0 = math.radians(bb['dir'])
    elif np.hypot(*Q.mean(0)) < 600: continue   # no photo for this field: leave it plain grass
    def pol(r, a): return (H[0] + r * math.cos(a), H[1] + r * math.sin(a))
    skin = [tuple(H)] + [pol(18.44 * math.cos(math.radians(x)) + math.sqrt(29.0 ** 2 - (18.44 * math.sin(math.radians(x))) ** 2), a0 + math.radians(x)) for x in np.linspace(-45, 45, 31)]   # grass line: 29 m arc round the mound, out to the foul lines
    dr.polygon(P(skin), fill=tuple(PAL['infield']))
    b = 27.43; g = 1.4   # grass square inside the base paths
    sq = [pol(g * 1.414, a0), pol(b - g, a0 - math.pi / 4), pol(b * 1.414 - g * 1.414, a0), pol(b - g, a0 + math.pi / 4)]
    sq = [pol(g * 1.414, a0), (H[0] + (b - g) * math.cos(a0 - math.pi / 4) + g * math.cos(a0 + math.pi / 4), H[1] + (b - g) * math.sin(a0 - math.pi / 4) + g * math.sin(a0 + math.pi / 4)),
          pol((b - g) * 1.414, a0), (H[0] + (b - g) * math.cos(a0 + math.pi / 4) + g * math.cos(a0 - math.pi / 4), H[1] + (b - g) * math.sin(a0 + math.pi / 4) + g * math.sin(a0 - math.pi / 4))]
    dr.polygon(P(sq), fill=tuple(PAL['lawn']))
    for (cx_, cy_), rr in ((pol(18.44, a0), 2.7), (tuple(H), 4.0)):
        dr.ellipse([((cx_ - rr + NEAR) / PX, (NEAR - cy_ - rr) / PX), ((cx_ + rr + NEAR) / PX, (NEAR - cy_ + rr) / PX)], fill=tuple(PAL['infield']))
    print('baseball home', H.round(1), 'dir', round(math.degrees(a0)))
# under the stadium model: grass, so any gap in the model's surface shows grass, never park dirt
pass  # pad lawn moved above paint_at
# cemeteries (real place): their aisle paths are not painted as paths
from shapely.geometry import Polygon as _SPo, Point as _SPt
from shapely.ops import unary_union as _SUu
_CEMP = [_SPo(ring(el)) for el in js if el['type'] == 'way' and (el.get('tags', {}).get('landuse') == 'cemetery' or el.get('tags', {}).get('amenity') == 'grave_yard') and len(ring(el)) >= 4]
_CEMP = _SUu([q if q.is_valid else q.buffer(0) for q in _CEMP]) if _CEMP else None
# linear features
for el in js:
    t = el.get('tags', {})
    if el['type'] != 'way': continue
    if t.get('tunnel', 'no') != 'no' or t.get('location') == 'underground' or t.get('covered') == 'yes': continue   # tunnels and culverts are underground: nothing on the surface
    pts = ring(el)
    if len(pts) < 2: continue
    if 'waterway' in t and t['waterway'] in ('river', 'stream', 'canal'):
        dry = t.get('intermittent') == 'yes' or spec.get('rivers_dry')
        wd = 40 if t['waterway'] == 'river' else 8
        dr.line(P(pts), fill=tuple(PAL['sand' if dry else 'water']), width=max(1, int(wd / PX)))
    hw = t.get('highway')
    if hw and t.get('bridge') and t.get('bridge') != 'no': hw = None
    if hw == 'service' and t.get('service') == 'parking_aisle' and spec.get('real'): hw = None   # a lot's aisles are its own asphalt (cars.py, pools.py)
    if hw in ('path', 'footway') and spec.get('real') and _CEMP is not None and _CEMP.contains(_SPt(*np.mean(pts, 0))): hw = None   # a cemetery's grave aisles: not paved paths (pools.py stands the headstone rows on them)
    if hw:
        wd = {'motorway': 22, 'trunk': 18, 'primary': 16, 'secondary': 13, 'tertiary': 11, 'residential': 8,
              'unclassified': 8, 'service': 5, 'footway': 2.5, 'path': 2, 'cycleway': 2.5, 'pedestrian': 6}.get(hw)
        if wd and hw == 'pedestrian' and t.get('area') == 'yes' and len(pts) > 3:
            dr.polygon(P(pts), fill=tuple(PAL['paved'])); wd = None
        if wd:
            col = PAL['path'] if hw in ('footway', 'path', 'cycleway', 'pedestrian') else PAL['road']
            dr.line(P(pts), fill=tuple(col), width=max(1, int(wd / PX)))
    if t.get('railway') in ('rail', 'light_rail', 'tram') and 'tunnel' not in t:
        if t['railway'] == 'rail': dr.line(P(pts), fill=tuple(PAL['ballast']), width=max(1, int(6 / PX)))
        if t['railway'] != 'rail' or not spec.get('rail_geo'):
            dr.line(P(pts), fill=tuple(PAL.get('track', PAL['road'])), width=max(1, int(1.8 / PX)))
# cutting banks: one plain grass colour (a top-down picture smears on a 6 m wall)
if BANK is not None:
    bm = Image.fromarray((np.flipud(BANK) * 255).astype(np.uint8)).resize((N, N), Image.BILINEAR)
    bw = (np.asarray(bm).astype(np.float32) / 255)[..., None]
    bc = np.array(PAL.get('bank', [int(c * 0.88) for c in PAL['lawn']]), np.float32)[None, None]
    img = Image.fromarray((np.asarray(img).astype(np.float32) * (1 - bw) + bc * bw).astype(np.uint8))
_SP = os.path.join(D, 'sat.png')
if os.path.exists(_SP):
    _sj = json.load(open(os.path.join(D, 'sat.json'))); _SA = np.asarray(Image.open(_SP).convert('RGB')); _hm, _mp = _sj['half_m'], _sj['m_per_px']
# paved lots: aerial median colour per OSM paved landuse / car park (colour only, never pixels), brightest channel capped at 160
if os.path.exists(_SP):
    _AR = np.asarray(img).astype(np.int16).copy(); _np = 0
    for el in js:
        tg = el.get('tags', {})
        if el['type'] != 'way' or 'geometry' not in el: continue
        if not (tg.get('amenity') == 'parking' and tg.get('parking', 'surface') == 'surface') and tg.get('landuse') not in ('commercial', 'retail', 'industrial'): continue
        pts = ring(el)
        if len(pts) < 4: continue
        q = [((x + _hm) / _mp, (_hm - y) / _mp) for x, y in pts]
        x0, y0 = [int(min(v)) for v in zip(*q)]; x1, y1 = [int(max(v)) + 1 for v in zip(*q)]
        if x0 < 0 or y0 < 0 or x1 >= _SA.shape[1] or y1 >= _SA.shape[0] or (x1 - x0) * (y1 - y0) > 250000: continue
        mk = Image.new('L', (x1 - x0, y1 - y0)); ImageDraw.Draw(mk).polygon([(u - x0, v - y0) for u, v in q], fill=1)
        px_ = _SA[y0:y1, x0:x1][np.asarray(mk) > 0]
        if len(px_) < 30: continue
        px_ = px_[~((px_[:, 1] > px_[:, 0] + 6) & (px_[:, 1] >= px_[:, 2]))]   # drop tree and grass pixels
        if len(px_) < 30: continue
        md = np.median(px_, 0); md = md * min(1.0, 160.0 / max(md.max(), 1))
        # only repaint pixels already painted paved/parking, so buildings, roads and lawns inside the outline keep their paint
        Q_ = P(pts); u0, v0 = [max(0, int(min(c))) for c in zip(*Q_)]; u1, v1 = [min(N, int(max(c)) + 2) for c in zip(*Q_)]
        if u1 <= u0 or v1 <= v0: continue
        _mk = Image.new('L', (u1 - u0, v1 - v0), 0); ImageDraw.Draw(_mk).polygon([(u - u0, v - v0) for u, v in Q_], fill=255)
        _sub = _AR[v0:v1, u0:u1]; _m = np.asarray(_mk) > 0
        for _k in ('paved', 'parking'):
            _sel = _m & (np.abs(_sub - np.array(PAL[_k])).max(-1) < 6)
            _sub[_sel] = md.astype(np.int16)
            if not _sel.any(): continue
            _jj, _ii = np.nonzero(_sel); _X = (u0 + _ii + 0.5) * PX - NEAR; _Y = NEAR - (v0 + _jj + 0.5) * PX   # MCG _lots structure, in world metres
            _Q = np.array(pts, float); _E = np.diff(_Q, axis=0); _e = _E[np.argmax(np.hypot(_E[:, 0], _E[:, 1]))]; _th = math.atan2(_e[1], _e[0])
            _vv = -_X * math.sin(_th) + _Y * math.cos(_th); _uu = _X * math.cos(_th) + _Y * math.sin(_th)
            if tg.get('amenity') == 'parking':
                _f = np.ones_like(_uu)   # the lot's own colour; its lines and cars are modelled over it (cars.py, pools.py)
            else:
                _kk = (np.floor(_uu / 6.0) * 7919 + np.floor(_vv / 6.0) * 104729).astype(np.int64); _f = 0.94 + 0.12 * ((_kk * 2654435761) % 1000) / 1000.0
                _f = np.where((np.mod(_uu, 6.0) < 0.5) | (np.mod(_vv, 6.0) < 0.5), _f * 0.86, _f)   # 6 m slabs
            _sub[_jj, _ii] = np.clip(_sub[_jj, _ii] * _f[:, None], 0, 255).astype(np.int16)
        _np += 1
    img = Image.fromarray(np.clip(_AR, 0, 255).astype(np.uint8))
    print('paved lots from aerial median', _np)
# mowing stripes and wear on grass (hand-made, aerial used only to place them)
_a = np.asarray(img).astype(np.float32); _L = np.array(PAL['lawn'], np.float32)
_g = (np.abs(_a - _L).max(-1) < 34).astype(np.float32)   # lawn-coloured pixels only
_st = Image.new('L', (N, N), 128); _sd = ImageDraw.Draw(_st)
for el in js:   # every OSM pitch: 8 m stripes along its long axis, clipped to the pitch
    tg = el.get('tags', {})
    if el['type'] != 'way' or tg.get('leisure') != 'pitch' or 'geometry' not in el: continue
    pts = ring(el)
    if len(pts) < 4: continue
    cx, cy, ang, L_, W_ = _obox(pts[:-1] if pts[0] == pts[-1] else pts)
    ux, uy = math.cos(ang), math.sin(ang); wx, wy = -uy, ux
    pm = Image.new('L', (N, N), 0); ImageDraw.Draw(pm).polygon(P(pts), fill=255)
    sm = Image.new('L', (N, N), 128); smd = ImageDraw.Draw(sm); k = 0; off = -W_ / 2 - 8
    while off < W_ / 2 + 8:
        q = [(cx + ux * s_ + wx * o_, cy + uy * s_ + wy * o_) for s_, o_ in ((-L_, off), (L_, off), (L_, off + 8), (-L_, off + 8))]
        smd.polygon(P(q), fill=146 if k % 2 else 110); k += 1; off += 8
    _st.paste(sm, (0, 0), pm)
_s = (np.asarray(_st).astype(np.float32) - 128) / 128 * 0.5   # +-7 %
_w = np.asarray(Image.fromarray((rng.random((N // 53 + 1, N // 53 + 1)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)).astype(np.float32) / 255
_w = np.clip((_w - 0.62) / 0.3, 0, 1) * 0.45   # patchy dry wear, ~40 m blobs, up to 45 % toward dry grass
if spec.get('real'): _w[:] = 0   # real place: the aerial's own colours already say where the grass is dry
_dry = np.array(PAL.get('lawn_dry', [150, 140, 92]), np.float32)
for (cx, cy, ang, L_, W_), _q in OV:   # oval wear: centre square and both goal squares
    for s_, rx, ry in ((0, 28, 22), (-L_ / 2 + 9, 12, 9), (L_ / 2 - 9, 12, 9)):
        ex, ey = cx + math.cos(ang) * s_, cy + math.sin(ang) * s_
        em = Image.new('L', (N, N), 0); ImageDraw.Draw(em).ellipse(P([(ex - rx, ey + ry), (ex + rx, ey - ry)]), fill=255)
        em = np.asarray(em.filter(ImageFilter.GaussianBlur(6 / PX))).astype(np.float32) / 255; _w = np.maximum(_w, em * 0.55)
_a = _a * (1 - _g * _w)[..., None] + _dry[None, None] * (_g * _w)[..., None]
_a *= (1 + 0.26 * _s * _g)[..., None]
img = Image.fromarray(np.clip(_a, 0, 255).astype(np.uint8))
# hand-made grain: per-pixel value noise, never photo pixels
a = np.asarray(img).astype(np.float32)
n1 = np.asarray(Image.fromarray((rng.random((N // 16 + 1, N // 16 + 1)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)).astype(np.float32) / 255 - 0.5
n2 = rng.random((N, N)).astype(np.float32) - 0.5
a *= (1 + 0.09 * n1 + 0.03 * n2)[..., None]
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((N // SS, N // SS), Image.LANCZOS).save(os.path.join(OUT, 'ground.png'))

# bridges: road, foot and rail bridges become raised decks in scene.py
BR = []
WD = {'motorway': 22, 'trunk': 18, 'primary': 16, 'secondary': 13, 'tertiary': 11, 'residential': 8, 'unclassified': 8,
      'service': 5, 'footway': 4, 'path': 3, 'cycleway': 4, 'pedestrian': 6}
for el in js:
    t = el.get('tags', {})
    if el['type'] != 'way' or not t.get('bridge') or t.get('bridge') == 'no': continue
    w = WD.get(t.get('highway')) or (9 if t.get('railway') == 'rail' else None)
    if not w: continue
    pts = ring(el)
    if len(pts) > 1 and all(abs(x) < NEAR and abs(y) < NEAR for x, y in pts):
        BR.append(dict(p=[[round(x, 2), round(y, 2)] for x, y in pts], w=w, rail=t.get('railway') == 'rail'))
json.dump(BR, open(os.path.join(OUT, 'bridges.json'), 'w'))
# rails: surface tracks become 3D sleepers + steel in scene.py (crisp at any camera distance)
RL = []
for el in js:
    t = el.get('tags', {})
    if el['type'] != 'way' or t.get('railway') != 'rail' or 'tunnel' in t: continue
    # rail bridges are track too (sleepers + steel), never a white slab
    pts = ring(el)
    if len(pts) > 1 and all(abs(x) < NEAR and abs(y) < NEAR for x, y in pts):
        RL.append([[round(x, 2), round(y, 2)] for x, y in pts])
json.dump(RL, open(os.path.join(OUT, 'rails.json'), 'w'))
# roads: asphalt ribbons with lane lines in scene.py (texture pass, director OK 2026-11-20 "Build all three")
RD = []
for el in js:
    t = el.get('tags', {}); hw = t.get('highway')
    if el['type'] != 'way' or hw not in ('motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'service'): continue
    if (t.get('bridge') and t.get('bridge') != 'no') or (t.get('tunnel', 'no') != 'no') or t.get('covered') == 'yes': continue
    if hw == 'service' and t.get('service') == 'parking_aisle' and spec.get('real'): continue
    pts = ring(el); run = []
    for x, y in pts + [(1e9, 1e9)]:
        if abs(x) < NEAR and abs(y) < NEAR: run.append([round(x, 2), round(y, 2)]); continue
        if len(run) > 1: RD.append(dict(hw=hw, p=run, oneway=t.get('oneway') == 'yes'))
        run = []
json.dump(RD, open(os.path.join(OUT, 'roads.json'), 'w')); print('roads', len(RD))
print('rails', len(RL))
print('bridges', len(BR))

# buildings
BLD = []
# OSM building:part ways carry the real tower heights (a tower's outline often holds only its podium height)
_PJ = os.path.join(D, 'osm_parts.json')
PARTS = [dict(e, tags=dict(e.get('tags', {}), building='part')) for e in json.load(open(_PJ, encoding='utf-8'))['elements'] if e['type'] == 'way' and 'building' not in e.get('tags', {})] if os.path.exists(_PJ) else []
print('building parts', len(PARTS))
LV = spec['levels_default']
_OVH = None
if spec.get('real'):
    import real as _real
    _OVH = _real.overture_heights(spec['name'], xy)
_IND = None
if spec.get('real'):   # industrial land: an untagged building there is a shed or a works
    from shapely.geometry import Polygon as _SPoly, Point as _SPt
    from shapely.ops import unary_union as _SU
    _SHEDK = ('industrial', 'warehouse', 'shed', 'manufacture', 'hangar', 'barn', 'farm_auxiliary', 'storage_tank', 'factory', 'depot', 'transportation')
    _ip = []
    for el in js:
        if el['type'] == 'way' and el.get('tags', {}).get('landuse') in ('industrial', 'railway'):
            _r = ring(el)
            if len(_r) >= 4:
                try: _ip.append(_SPoly(_r).buffer(0))
                except Exception: pass
    _IND = _SU(_ip) if _ip else None
# real place: buildings OSM has not mapped yet (whole suburbs in places) from Overture's other sources (Microsoft and
# Google footprints traced from imagery, Esri community maps), where no OSM outline covers them
OVB = []
if spec.get('real'):
    _ovp = os.path.join(os.environ.get('WORK', '/home/user/work'), 'overture', spec['name'] + '.json')
    if os.path.exists(_ovp):
        from shapely import wkt as _OW
        from shapely.strtree import STRtree as _STR
        from shapely.geometry import Polygon as _OPo
        _op = []
        for el in js + PARTS:
            if el['type'] == 'way' and 'building' in el.get('tags', {}):
                _r = ring(el)
                if len(_r) >= 4:
                    try: _op.append(_OPo(_r).buffer(0))
                    except Exception: pass
        _otree = _STR(_op) if _op else None
        for r in json.load(open(_ovp)):
            if r['src'] == 'OpenStreetMap': continue
            try: g_ = _OW.loads(r['wkt'])
            except Exception: continue
            if g_.geom_type == 'MultiPolygon': g_ = max(g_.geoms, key=lambda q: q.area)
            if g_.geom_type != 'Polygon': continue
            ll = list(g_.exterior.coords)
            loc = [xy(y, x) for x, y in ll]
            cx_ = sum(q[0] for q in loc) / len(loc); cy_ = sum(q[1] for q in loc) / len(loc)
            if abs(cx_) > NEAR or abs(cy_) > NEAR: continue
            qp = _OPo(loc).buffer(0)
            if qp.area < 12: continue
            if _otree is not None and any(_op[i].intersection(qp).area > 0.3 * qp.area for i in _otree.query(qp)): continue
            tg = {'building': 'yes', 'source': 'overture:' + str(r['src'])}
            hh = r['height'] or (r['num_floors'] * 3.4 + 1.0 if r['num_floors'] else None)
            if hh: tg['height'] = str(round(float(hh), 1))
            OVB.append({'type': 'way', 'id': 'ov' + str(r['id']), 'tags': tg, 'geometry': [{'lat': y, 'lon': x} for x, y in ll]})
    print('overture-only buildings', len(OVB))
skip_r = spec["clear_r_m"]; _FPP = os.path.join(OUT, "footprint.json"); _FPR = np.array(json.load(open(_FPP))) if os.path.exists(_FPP) else None
for el in js + PARTS + OVB:
    t = el.get('tags', {})
    if el['type'] != 'way' or 'building' not in t: continue
    pts = ring(el)
    if len(pts) < 4: continue
    pts = pts[:-1] if pts[0] == pts[-1] else pts
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    if abs(cx) > NEAR or abs(cy) > NEAR: continue
    if ((any(math.hypot(px_, py_) < _FPR[int((math.degrees(math.atan2(py_, px_)) % 360) // 2)] + 2 for px_, py_ in pts)) if _FPR is not None else math.hypot(cx, cy) < skip_r) or t.get("building") in ("grandstand", "stadium"): continue
    if t.get('layer', '0').startswith('-') or t.get('location') == 'underground': continue
    h = None
    try: h = float(str(t.get('height', '')).split()[0])
    except Exception: pass
    if h is None and 'building:levels' in t:
        try: h = float(t['building:levels']) * 3.4 + 1.0
        except Exception: pass
    kind = t['building']
    if h is None and _OVH is not None: h = _OVH(cx, cy, pts)
    if h is None: h = LV.get(kind, LV['*'])
    if area(pts) < 0: pts = pts[::-1]
    A = abs(area(pts))
    if A < 12: continue
    cls = 'tower' if h >= 25 else ('house' if (A < 350 and h < 9) else 'block')
    BLD.append(dict(p=[[round(x, 2), round(y, 2)] for x, y in pts], h=round(h, 1), c=cls,
                    roof=int(rng.integers(0, len(PAL['roofs_' + ('house' if cls == 'house' else 'flat')]))),
                    wall=int(rng.integers(0, len(PAL['walls_' + cls])))))
    if spec.get('real') and cls == 'tower':   # real place: Perth/Hobart/Sydney towers read light; flats and hotels cream, offices pale glass
        _wt = PAL['walls_tower']; _lum = [sum(c) for c in _wt]
        _light = [i for i in range(len(_wt)) if _lum[i] > 420]
        _cream = [i for i in _light if _wt[i][0] >= _wt[i][2]] or _light
        _glass = [i for i in _light if _wt[i][2] > _wt[i][0]] or _light
        BLD[-1]['wall'] = int(rng.choice(_cream if kind in ('apartments', 'residential', 'hotel', 'dormitory') else _glass if kind in ('office', 'commercial', 'government') else _light))
    if kind == 'roof': BLD[-1]['open'] = 1; BLD[-1]['c'] = 'block'   # OSM building=roof: open canopy (roof on posts)
    if spec.get('real'):   # real place: only sheds, works and warehouses get clad walls and sheet roofs (scene.py)
        BLD[-1]['shed'] = int(kind in _SHEDK or (kind == 'yes' and _IND is not None and _IND.contains(_SPt(cx, cy))))
# real place: a lot mapped as one outline but built as a tower on a podium (Google Earth views) is split into its
# parts: ["split", [x, y], [[u0, u1, v0, v1, h, wall_rgb|null], ...]], u along the lot's long side from its west end,
# v across it from its south side, as fractions of the lot's oriented box
for _e in spec.get('real_lm', []):
    if _e[0] != 'split': continue
    _bi = min(range(len(BLD)), key=lambda i: math.hypot(*(np.mean(BLD[i]['p'], 0) - np.array(_e[1]))))
    _b = BLD.pop(_bi); _P = np.array(_b['p'], float); _c = _P.mean(0)
    _cv = np.cov((_P - _c).T); _w, _vv = np.linalg.eigh(_cv); _U = _vv[:, 1]; _U = _U if _U[0] >= 0 else -_U; _Vn = np.array([-_U[1], _U[0]])
    if _Vn[1] < 0: _Vn = -_Vn
    _pu = (_P - _c) @ _U; _pv = (_P - _c) @ _Vn
    for _k, (u0, u1, v0, v1, h, wc) in enumerate(_e[2]):
        _q = []
        for uu, vv in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
            _q.append(_c + (_pu.min() + uu * np.ptp(_pu)) * _U + (_pv.min() + vv * np.ptp(_pv)) * _Vn)
        if area([tuple(q) for q in _q]) < 0: _q = _q[::-1]
        nb = dict(_b, p=[[round(float(x), 2), round(float(y), 2)] for x, y in _q], h=float(h), c='tower' if h >= 25 else 'block')
        nb['wall'] = int(rng.integers(0, len(PAL['walls_' + nb['c']])))
        if wc: nb['wall_rgb'] = wc
        BLD.append(nb)
    print('split', _e[1], len(_e[2]), 'parts')
_SP = os.path.join(D, 'sat.png')
if os.path.exists(_SP):
    _sj = json.load(open(os.path.join(D, 'sat.json'))); _SA = np.asarray(Image.open(_SP).convert('RGB')); _hm, _mp = _sj['half_m'], _sj['m_per_px']
    for b in BLD:
        P_ = np.array(b['p']); A_ = 0.5 * abs(np.dot(P_[:, 0], np.roll(P_[:, 1], -1)) - np.dot(P_[:, 1], np.roll(P_[:, 0], -1)))
        if b['c'] == 'tower' or (b['c'] == 'block' and A_ < 400 and not spec.get('real')): continue
        q = [((x + _hm) / _mp, (_hm - y) / _mp) for x, y in b['p']]
        x0, y0 = [int(min(v)) for v in zip(*q)]; x1, y1 = [int(max(v)) + 1 for v in zip(*q)]
        if x0 < 0 or y0 < 0 or x1 >= _SA.shape[1] or y1 >= _SA.shape[0]: continue
        mk = Image.new('L', (x1 - x0, y1 - y0)); ImageDraw.Draw(mk).polygon([(u - x0, v - y0) for u, v in q], fill=1)
        px = _SA[y0:y1, x0:x1][np.asarray(mk) > 0]
        if len(px) > 20:
            md = np.median(px, 0)
            _cap = 175.0 if (spec.get('real') and b['c'] == 'block') else 185.0   # flat roofs: the aerial's glare off membrane is not their colour
            if not (md[1] > md[0] + 6 and md[1] >= md[2]): b['roof_c'] = [int(v * min(1.0, _cap / max(md))) for v in md]   # tree-covered roofs keep the palette
json.dump(BLD, open(os.path.join(OUT, 'buildings.json'), 'w'))
print('buildings', len(BLD), 'towers', sum(b['c'] == 'tower' for b in BLD))

# trees: OSM trees + scatter over tree-bearing cover + street trees
TR = []
for el in js:
    if el['type'] == 'node' and el.get('tags', {}).get('natural') == 'tree':
        x, y = xy(el['lat'], el['lon'])
        if math.hypot(x, y) > skip_r: TR.append([round(x, 1), round(y, 1)])
_td = spec.get('tree_default', 0)   # m^2 per tree on land OSM leaves untagged (satellite shows scattered trees)
_CN = os.path.join(OUT, 'canopy.npy'); CAN = np.load(_CN) if os.path.exists(_CN) else None   # trees traced from the satellite
if CAN is not None: _td = _td or 40000   # canopy mode: every untagged spot may hold a tree; the trace decides
mask = Image.new('L', (N, N), 0 if not _td else max(1, min(255, int(40000 / _td)))); md = ImageDraw.Draw(mask)
for k, v, dens in spec['tree_fill']:  # dens = m^2 per tree, 0 = clear (carves out)
    for el in js:
        t = el.get('tags', {})
        if el['type'] == 'way' and match(t, k, v):
            pts = ring(el)
            if len(pts) > 2: md.polygon(P(pts), fill=0 if dens == 0 else max(1, min(255, int(40000 / dens))))
for pk, poly in spec.get('paint_poly', []): md.polygon(P([tuple(q) for q in poly]), fill=0)
for el in js:
    t = el.get('tags', {})
    if el['type'] == 'way' and (t.get('amenity') == 'parking' or t.get('leisure') in ('pitch', 'swimming_pool', 'sports_centre')):
        pts = ring(el)
        if len(pts) > 2: md.polygon(P(pts), fill=0)
# keep trees off roads, rails, buildings and water
rdm = Image.new('L', (N, N), 0); rd = ImageDraw.Draw(rdm)
for el in js:
    t = el.get('tags', {})
    if el['type'] != 'way': continue
    pts = ring(el)
    if len(pts) < 2: continue
    if 'building' in t and len(pts) > 2: md.polygon(P(pts), fill=0); md.line(P(pts + pts[:1]), fill=0, width=max(1, int((3 if spec.get('real') else 8) / PX))); rd.polygon(P(pts), fill=255); rd.line(P(pts + pts[:1]), fill=255, width=max(1, int(8 / PX)))   # director 2026-11-20: crowns clear of roofs
    if not (t.get('tunnel', 'no') != 'no' or t.get('location') == 'underground' or t.get('covered') == 'yes') and (t.get('highway') in ('motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'residential', 'service', 'unclassified') or t.get('railway')):
        _hw = t.get('highway'); _dl = {'motorway': 4, 'trunk': 4, 'primary': 4, 'secondary': 4}.get(_hw, 2)
        try: _ln = int(str(t.get('lanes', _dl)).split(';')[0])
        except Exception: _ln = _dl
        _w = 14 if t.get('railway') else _ln * 7.5   # director 2026-11-20: clear the full road width (4 lanes ~ 30 m)
        if spec.get('real') and not t.get('railway'): _w = _ln * 3.5 + 1.5   # real place: the aerial's crowns stand on the verges, so only the carriageway is clear
        md.line(P(pts), fill=0, width=max(1, int(_w / PX))); rd.line(P(pts), fill=255, width=max(1, int(_w / PX)))
mv = np.asarray(mask).astype(np.float32)   # stores 40000 / (m^2 per tree), 0 = no trees
cell = 6.0
gx = np.arange(-NEAR + cell / 2, NEAR, cell)
GX, GY = np.meshgrid(gx, gx)
GX = GX + rng.uniform(-cell / 2, cell / 2, GX.shape); GY = GY + rng.uniform(-cell / 2, cell / 2, GY.shape)
ix = np.clip(((GX + NEAR) / PX).astype(int), 0, N - 1); iy = np.clip(((NEAR - GY) / PX).astype(int), 0, N - 1)
v = mv[iy, ix]
prob = np.where(v > 0, cell * cell * v / 40000.0, 0)   # cell area / (m^2 per tree)
keep = (rng.random(GX.shape) < np.clip(prob, 0, 1)) & (np.hypot(GX, GY) > skip_r) & (np.hypot(GX, GY) < spec['tree_r_m'])
if CAN is not None:   # inside the satellite's extent a tree stands where the trace shows crown in this 6 m cell
    _sj = json.load(open(os.path.join(HERE, 'data', spec['name'], 'sat.json'))); _h, _m = _sj['half_m'], _sj['m_per_px']
    _ci = ((_h - GY) / _m).astype(int); _cj = ((GX + _h) / _m).astype(int); _in = (np.abs(GX) < _h - 3) & (np.abs(GY) < _h - 3)
    _cs = np.cumsum(np.cumsum(np.pad(CAN.astype(np.float32), ((1, 0), (1, 0))), 0), 1); _r = int(3 / _m)
    _i0 = np.clip(_ci - _r, 0, CAN.shape[0]); _i1 = np.clip(_ci + _r, 0, CAN.shape[0]); _j0 = np.clip(_cj - _r, 0, CAN.shape[1]); _j1 = np.clip(_cj + _r, 0, CAN.shape[1])
    _frac = (_cs[_i1, _j1] - _cs[_i0, _j1] - _cs[_i1, _j0] + _cs[_i0, _j0]) / np.maximum(1, (_i1 - _i0) * (_j1 - _j0))
    _ft = 0.3 if spec.get('real') else 0.45   # real place: a garden tree's 5 m crown fills a third of its 6 m cell
    keep = np.where(_in, (_frac > _ft) & (v > 0) & (np.hypot(GX, GY) > skip_r), keep)
    print('canopy trees', int((_in & keep).sum()))
for x, y in zip(GX[keep], GY[keep]): TR.append([round(float(x), 1), round(float(y), 1)])
# street trees along residential streets
if spec.get('street_trees'):
    for el in js:
        t = el.get('tags', {})
        if el['type'] != 'way' or t.get('highway') not in ('residential', 'tertiary', 'secondary'): continue
        pts = ring(el)
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            L = math.hypot(x2 - x1, y2 - y1)
            if L < 1: continue
            nx, ny = -(y2 - y1) / L, (x2 - x1) / L
            try: _ow = int(str(t.get('lanes', 4 if t.get('highway') == 'secondary' else 2)).split(';')[0]) * 3.75 + 2
            except Exception: _ow = 9.5
            for s in np.arange(5, L, spec['street_trees']):
                px, py = x1 + (x2 - x1) * s / L, y1 + (y2 - y1) * s / L
                for sd in (-1, 1):
                    qx, qy = px + sd * nx * _ow, py + sd * ny * _ow
                    if spec['tree_r_m'] > math.hypot(qx, qy) > skip_r and rng.random() < 0.8:
                        TR.append([round(qx, 1), round(qy, 1)])
_RD = np.asarray(rdm); _n0 = len(TR)
TR = [q for q in TR if not (abs(q[0]) < NEAR and abs(q[1]) < NEAR and _RD[min(N - 1, int((NEAR - q[1]) / PX)), min(N - 1, int((q[0] + NEAR) / PX))])]
print('mapped trees on roads removed', _n0 - len(TR))
TR = [[x, y, int(rng.integers(0, len(spec['tree_kinds'])))] for x, y in TR if abs(x) < NEAR and abs(y) < NEAR]
if spec.get('real') and CAN is not None:   # real place: each crown takes the aerial's colour where it stands
    _SAt = np.asarray(Image.open(os.path.join(HERE, 'data', spec['name'], 'sat.png')).convert('RGB')).astype(np.float32)
    _sj = json.load(open(os.path.join(HERE, 'data', spec['name'], 'sat.json'))); _h, _m = _sj['half_m'], _sj['m_per_px']; _r = max(1, int(4 / _m))
    for q in TR:
        i_, j_ = int((_h - q[1]) / _m), int((q[0] + _h) / _m)
        if not (_r <= i_ < CAN.shape[0] - _r and _r <= j_ < CAN.shape[1] - _r): q += [-1, -1, -1]; continue
        cm = CAN[i_ - _r:i_ + _r + 1, j_ - _r:j_ + _r + 1]
        if cm.sum() < 4: q += [-1, -1, -1]; continue
        c_ = np.median(_SAt[i_ - _r:i_ + _r + 1, j_ - _r:j_ + _r + 1][cm], 0) * 1.3   # the aerial's crowns sit in their own shade
        q += [int(min(200, v)) for v in c_]
json.dump(TR, open(os.path.join(OUT, 'trees.json'), 'w'))
json.dump(dict(base=base, near=NEAR, near_step=NS, far=FAR, far_step=FS), open(os.path.join(OUT, 'meta.json'), 'w'))
print('trees', len(TR))
