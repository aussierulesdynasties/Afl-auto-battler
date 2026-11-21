p='prep.py';s=open(p,newline='').read()
old="for x, y in zip(GX[keep], GY[keep]): TR.append([round(float(x), 1), round(float(y), 1)])\n"
new=old+'''# plaza tree beds (hand outline): a tree on each 5 m cell whose z19 crown cover (dark canopy) is over half, planters excluded
_hp = os.path.join(HERE, 'data', spec['name'], 'sat_hi_plaza.png'); _hj = os.path.join(HERE, 'spec', spec['name'] + '_fc_hand.json')
if os.path.exists(_hp) and os.path.exists(_hj):
    from skimage import color as _skc2
    from scipy import ndimage
    from matplotlib.path import Path as _MP
    _HJ2 = json.load(open(_hj)); _Lh = _skc2.rgb2lab(np.asarray(Image.open(_hp).convert('RGB')) / 255.0)[..., 0]
    _cv = ndimage.binary_opening(ndimage.gaussian_filter(_Lh, 2) < 40, iterations=6)
    _op = _MP(_HJ2['outline']); _pps = [_MP(q['pts']) for q in _HJ2['planters']]; _n0 = len(TR)
    for _yy in np.arange(-40, 126, 5.0):
        for _xx in np.arange(90, 247, 5.0):
            _x, _y = _xx + rng.uniform(-1.5, 1.5), _yy + rng.uniform(-1.5, 1.5)
            if not _op.contains_point((_x, _y)) or any(q.contains_point((_x, _y)) for q in _pps): continue
            _r0, _c0 = int((135 - _y) / 0.125), int((_x - 80) / 0.125)
            if _cv[max(0, _r0 - 20):_r0 + 20, max(0, _c0 - 20):_c0 + 20].mean() > 0.5: TR.append([round(_x, 1), round(_y, 1)])
    print('plaza bed trees', len(TR) - _n0)
'''
assert old in s; s=s.replace(old,new,1); open(p,'w',newline='').write(s)
