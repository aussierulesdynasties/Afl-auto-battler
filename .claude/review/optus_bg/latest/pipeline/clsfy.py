import math
# exec'd from prep.py (plan session 2026-11-20: "copy the aerial"). The aerial is read as a map only: each ground pixel
# gets a cover class from the aerial's colour there (lawn, turf, dry grass, garden bed, sand, brick paving, concrete,
# asphalt, bare ground), and the class is painted in a hand-made palette colour. No aerial pixel reaches the ground image.
_sp = os.path.join(os.path.dirname(OUT), 'sat.png')
if spec.get('cover_from_aerial') and os.path.exists(_sp):
    from scipy import ndimage as _ndi
    _s = np.asarray(Image.open(_sp).convert('RGB').resize((N, N), Image.BILINEAR)).astype(np.float32) / 255
    _s = _ndi.uniform_filter(_s, (3, 3, 1))
    r_, g_, b_ = _s[..., 0], _s[..., 1], _s[..., 2]
    V_ = _s.max(2); S_ = (V_ - _s.min(2)) / np.maximum(V_, 1e-3)
    CP = spec['aerial_classes']   # name -> colour (hand-picked)
    names = list(CP)
    cls = np.full((N, N), names.index('ground'), np.int16)
    veg = (g_ > r_ * 1.03) & (g_ > b_ * 1.05)
    cls[(S_ < 0.14) & (V_ >= 0.38)] = names.index('concrete')
    cls[(S_ < 0.14) & (V_ < 0.38)] = names.index('asphalt')
    cls[~veg & (V_ > 0.60) & (S_ >= 0.10) & (S_ < 0.45) & (g_ < r_ * 0.90)] = names.index('sand')
    red = ~veg & (r_ > g_ * 1.08) & (b_ > g_ * 0.80) & (S_ >= 0.12) & (V_ >= 0.50)   # paving: pinker than sand (blue nearer green)
    cls[red & (r_ >= g_ * 1.18)] = names.index('brick_light')
    cls[red & (r_ < g_ * 1.18)] = names.index('brick_dark')
    cls[(b_ > r_ * 1.15) & (b_ > g_ * 1.02) & (V_ > 0.3)] = names.index('court')
    cls[~veg & ~red & (g_ >= r_ * 0.90) & (b_ < g_ * 0.80) & (S_ >= 0.14)] = names.index('dry_grass')   # pale summer lawn: greener than sand
    cls[veg & (V_ < 0.26)] = names.index('bed')
    cls[veg & (V_ >= 0.26) & (g_ < r_ * 1.12)] = names.index('dry_grass')
    cls[veg & (V_ >= 0.26) & (g_ >= r_ * 1.12)] = names.index('lawn')
    cls[veg & (V_ >= 0.42) & (g_ >= r_ * 1.22)] = names.index('turf')
    # the stadium roof (white in the aerial) hides the concourse under it: paint that as the forecourt paving
    _yy, _xx = np.mgrid[0:N, 0:N]; _rr = np.hypot((_xx + 0.5) * PX - NEAR, NEAR - (_yy + 0.5) * PX)
    _roof = (_rr < R0 + 40) & (V_ > 0.72) & (S_ < 0.14)
    _roof = _ndi.binary_dilation(_roof, iterations=4) & (_rr < R0 + 45)
    cls[_roof] = names.index('brick_dark')
    # clean speckle: majority of each 5 x 5 (about 4 m)
    def _major(cl, w):
        bv = np.full((N, N), -1.0, np.float32); bc = cl.copy()
        for k in range(len(names)):
            f = _ndi.uniform_filter((cl == k).astype(np.float32), w); m = f > bv; bv[m] = f[m]; bc[m] = k
        return bc
    _c15 = _major(cls, 15); _c5 = _major(cls, 5)
    # paving keeps its finer pattern (the forecourt's flowing pink, salmon and grey bands are 4-15 m wide)
    _pav = np.isin(_c15, [names.index('brick_light'), names.index('brick_dark'), names.index('concrete')])
    cls = _c5   # 3.75 m smoothing everywhere: paths and beds keep their shape (15 px gave soft blobs)
    _col = np.array([CP[k] for k in names], np.float32)[cls]
    _a = np.asarray(img).astype(np.int16)
    keep = np.zeros((N, N), bool)
    if spec.get('aerial_paving_only'):   # OSM decides the cover; the aerial only sets the paving band pattern inside OSM paved areas
        _pv = np.zeros((N, N), bool)
        for _k in ('plaza',): _pv |= np.all(_a == PAL[_k], 2)
        keep |= ~_pv
        # forecourt (aerial): broad flowing bands of salmon, cream and taupe paving. Each pixel of the unblurred aerial
        # votes for its nearest tone (trees and shadows, L < 0.32, don't vote); each tone's votes are Gaussian-smoothed
        # (sigma 5 px = 7.5 m; cream x0.85, taupe x0.75 so the salmon field dominates as in the aerial) and the strongest wins: smooth band outlines instead of majority-filter blotches.
        _raw = np.asarray(Image.open(_sp).convert('RGB').resize((N, N), Image.LANCZOS)).astype(np.float32) / 255
        _ref = np.array([[0.70, 0.50, 0.46], [0.80, 0.73, 0.64], [0.58, 0.55, 0.53]], np.float32)
        _t = ((_raw[..., None, :] - _ref[None, None]) ** 2).sum(-1).argmin(-1); _ok = _raw.mean(2) >= 0.32
        _vs = np.stack([_ndi.gaussian_filter(((_t == k) & _ok).astype(np.float32), 5.0) * (1.0, 0.85, 0.75)[k] for k in range(3)], -1)
        _tb = np.zeros(_vs.shape[:2], int)   # no aerial band pattern: plain salmon base; bands come only from the hand trace (fc_overlay.py)
        _pal = np.array(spec['forecourt_tones'], np.float32)
        _col = np.where(_pv[..., None], _pal[_tb], _col)
        exec(open('fc_overlay.py').read())
    for _k in ('road', 'water', 'ballast', 'track'):
        keep |= np.all(_a == PAL[_k], 2)
    _o = np.asarray(img).astype(np.float32); _o[~keep] = _col[~keep]
    # macro texture big enough to read from the orbit camera (the 8 m detail fades out past 400 m), hand-made, no aerial pixels:
    # grass = mowing stripes 6 m wide (+-4 %) and wear patches about 25 m across (+-7 %); paving = 3 m slab modules
    # (+-3 % per slab) with darker joints between bands
    _rg = np.random.default_rng(11)
    _gr = (_o[..., 1] > _o[..., 0] * 1.04) & (_o[..., 1] > _o[..., 2] * 1.15)
    _pn = _ndi.gaussian_filter(_rg.normal(0, 1, (N, N)), 25.0 / PX / 2); _pn = _pn / (_pn.std() + 1e-6)
    _pt = 1 + 0.07 * np.clip(_pn, -2, 2) / 2
    _o[_gr] *= _pt[_gr][:, None]   # wear patches on all grass
    # mowing stripes on true lawns only, each lawn mown along its own long axis
    _lw = (_o[..., 1] > _o[..., 0] * 1.15) & (_o[..., 1] > _o[..., 2] * 1.35)
    _lb, _nl = _ndi.label(_lw)
    for _i, _sl_ in enumerate(_ndi.find_objects(_lb)):
        _m = _lb[_sl_] == _i + 1
        if _m.sum() < 60: continue
        _y, _x = np.nonzero(_m); _x = _x - _x.mean(); _y = _y - _y.mean()
        _ev = np.linalg.eigh(np.cov(np.vstack([_x, _y])))[1][:, -1]
        _yy2, _xx2 = np.mgrid[_sl_]
        _u = (_xx2 * _ev[1] - _yy2 * _ev[0]) * PX   # across the long axis: stripes run along it
        _f = np.where((_u // 6.0) % 2 == 0, 1.045, 0.955)
        _blk = _o[_sl_]; _blk[_m] *= _f[_m][:, None]
    if spec.get('aerial_paving_only'):
        _sl = _rg.normal(0, 1, (N // 2 + 1, N // 2 + 1)).repeat(2, 0).repeat(2, 1)[:N, :N]
        _ed = _ndi.grey_dilation(_tb, 3) != _ndi.grey_erosion(_tb, 3)
        _pf = (1 + 0.03 * np.clip(_sl, -2, 2) / 2) * np.where(_ed, 0.9, 1.0)
        _o[_pv] *= _pf[_pv][:, None]
    _o = _o.clip(0, 255)
    img = Image.fromarray(_o.astype(np.uint8))   # (hard class edges kept: the mask below matches palette colours exactly)
    print('aerial classes:', {k: round(float((cls == i).mean()) * 100, 1) for i, k in enumerate(names)})
