s=open('clsfy.py',encoding='utf-8').read()
o="    _o = np.asarray(img).astype(np.float32); _o[~keep] = _col[~keep]\n"
assert o in s
n=o+'''    # macro texture big enough to read from the orbit camera (the 8 m detail fades out past 400 m), hand-made, no aerial pixels:
    # grass = mowing stripes 6 m wide (+-4 %) and wear patches about 25 m across (+-7 %); paving = 3 m slab modules
    # (+-3 % per slab) with darker joints between bands
    _rg = np.random.default_rng(11)
    _gr = (_o[..., 1] > _o[..., 0] * 1.04) & (_o[..., 1] > _o[..., 2] * 1.15)
    _ang = math.radians(28.0); _u = (_xx * math.cos(_ang) + _yy * math.sin(_ang)) * PX
    _str = np.where((_u // 6.0) % 2 == 0, 1.04, 0.96)
    _pn = _ndi.gaussian_filter(_rg.normal(0, 1, (N, N)), 25.0 / PX / 2); _pn = _pn / (_pn.std() + 1e-6)
    _pt = 1 + 0.07 * np.clip(_pn, -2, 2) / 2
    _o[_gr] *= (_str * _pt)[_gr][:, None]
    if spec.get('aerial_paving_only'):
        _sl = _rg.normal(0, 1, (N // 2 + 1, N // 2 + 1)).repeat(2, 0).repeat(2, 1)[:N, :N]
        _ed = _ndi.grey_dilation(_tb, 3) != _ndi.grey_erosion(_tb, 3)
        _pf = (1 + 0.03 * np.clip(_sl, -2, 2) / 2) * np.where(_ed, 0.9, 1.0)
        _o[_pv] *= _pf[_pv][:, None]
    _o = _o.clip(0, 255)
'''
s=s.replace(o,n,1)
if 'import math' not in s: s='import math\n'+s
open('clsfy.py','w',encoding='utf-8',newline='').write(s)
