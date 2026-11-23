s=open('clsfy.py',encoding='utf-8').read()
a=s.index("    _ang = math.radians(28.0)"); b=s.index("    if spec.get('aerial_paving_only'):\n        _sl")
n='''    _pn = _ndi.gaussian_filter(_rg.normal(0, 1, (N, N)), 25.0 / PX / 2); _pn = _pn / (_pn.std() + 1e-6)
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
'''
s=s[:a]+n+s[b:]
s=s.replace("    _o[_gr] *= (_str * _pt)[_gr][:, None]\n","")
open('clsfy.py','w',encoding='utf-8',newline='').write(s)
