# exec'd from clsfy.py after the forecourt mask _pv exists.
# Forecourt overlay (plan session 2026-11-20): the paving bands are traced from the aerial as smooth curves
# (each tone's vote field is Gaussian-smoothed at aerial resolution; the band edge is the curve where two
# fields cross, rendered anti-aliased at 0.1 m/px), then every band is filled with a hand-made slab tile:
# 1.2 x 0.6 m slabs in stretcher bond, 4 cm darker joints, +-4 % per-slab tone. No aerial pixel is used as colour.
import json as _json
_FR = 0.1   # m per texture pixel
_ys, _xs = np.nonzero(_pv)
_x0 = -NEAR + _xs.min() * PX - 10; _x1 = -NEAR + (_xs.max() + 1) * PX + 10
_y1 = NEAR - _ys.min() * PX + 10; _y0 = NEAR - (_ys.max() + 1) * PX - 10
_W = int((_x1 - _x0) / _FR); _H = int((_y1 - _y0) / _FR)
_sat = Image.open(_sp).convert('RGB'); _SR = 2 * NEAR / _sat.size[0]
_crop = _sat.crop((int((_x0 + NEAR) / _SR), int((NEAR - _y1) / _SR), int((_x1 + NEAR) / _SR), int((NEAR - _y0) / _SR)))
_cr = np.asarray(_crop).astype(np.float32) / 255
_ref2 = np.array([[0.70, 0.50, 0.46], [0.80, 0.73, 0.64], [0.58, 0.55, 0.53]], np.float32)
_Lc = _cr.mean(2)
_pw = ((_Lc > 0.40) & ~((_cr[..., 1] > _cr[..., 0]) & (_cr[..., 1] > _cr[..., 2]))).astype(np.float32)
# bands: hand-digitised polygons (spec/optus_fc_hand.json, traced by eye from the aerial on a 10 m grid). Each band is
# filled crisp (4x supersampled edge) over a salmon base; no aerial pixel and no noise mask is used.
from PIL import ImageDraw as _IDw
_HJ = _json.load(open(os.path.join(HERE, 'spec', 'optus_fc_hand.json')))
_tones = np.array(spec['forecourt_tones'], np.float32)
_SS = 4; _lim = Image.new('L', (_W * _SS // 2, _H * _SS // 2), 0); _dr = _IDw.Draw(_lim)
_pxs = lambda x, y: ((x - _x0) / _FR * _SS / 2, (_y1 - y) / _FR * _SS / 2)
for _b in _HJ['bands']:
    _dr.polygon([_pxs(x, y) for x, y in _b['pts']], fill=_b['tone'] + 1)
    for _h in _b.get('holes', []): _dr.polygon([_pxs(x, y) for x, y in _h], fill=0)
_lab = np.asarray(_lim.resize((_W, _H), Image.NEAREST)).astype(np.int16) - 1; _lab[_lab < 0] = 0
_rgb = _tones[_lab]
# hand-made paver: 1.2 x 0.6 m slabs in stretcher bond laid along each band, 4 cm darker joints, +-5 % per-slab tone
_yy, _xx = np.mgrid[0:_H, 0:_W].astype(np.float32) * _FR
_row = np.floor(_yy / 0.6); _xs2 = _xx + (_row % 2) * 0.6; _sc = np.floor(_xs2 / 1.2)
_jt = np.minimum(np.minimum(_yy % 0.6, 0.6 - _yy % 0.6), np.minimum(_xs2 % 1.2, 1.2 - _xs2 % 1.2)) < 0.025
_hs = np.sin(_row * 12.9898 + _sc * 78.233) * 43758.5453; _hs = (_hs - np.floor(_hs)) * 2 - 1
_rgb *= (1 + 0.05 * _hs)[..., None]
_rgb *= np.where(_jt, 0.80, 1.0)[..., None]
# band edges: a crisp 15 cm darker border course where the tone changes
_be = (_ndi.grey_dilation(_lab, 3) != _ndi.grey_erosion(_lab, 3))
_rgb *= np.where(_be, 0.86, 1.0)[..., None]
# planters: soil/mulch bed inside each planter outline (rims and shrubs are meshes in fc_scene.py)
_plm = Image.new('L', (_W, _H), 0); _dp = _IDw.Draw(_plm)
for _p in _HJ['planters']: _dp.polygon([((x - _x0) / _FR, (_y1 - y) / _FR) for x, y in _p['pts']], fill=255)
_plm = np.asarray(_plm) > 127; _rgb[_plm] = np.array([74, 58, 44], np.float32) * (1 + 0.08 * _hs[_plm])[:, None]
# alpha: the forecourt mask, upsampled smooth
_m = _pv[_ys.min():_ys.max() + 1, _xs.min():_xs.max() + 1].astype(np.float32)
_m = np.pad(_m, int(10 / PX))
_al = np.asarray(Image.fromarray(_ndi.gaussian_filter(_m, 0.6)).resize((_W, _H), Image.BILINEAR))
# the real paving also runs outside the OSM plaza: add aerial paving (one of the three tones, not green, not dark)
# that touches the plaza, cleaned with a 2 m open/close and kept within the bbox
_d2 = ((_cr[..., None, :] - _ref2[None, None]) ** 2).sum(-1).min(-1)
_ap = (_pw > 0) & (_cr.std(2) < 0.12)
_ap = _ndi.binary_closing(_ndi.binary_opening(_ap, iterations=2), iterations=3)
_apU = np.asarray(Image.fromarray(_ap.astype(np.uint8) * 255).resize((_W, _H), Image.BILINEAR)) > 127
_pl = _al > 0.5
_lab3, _n3 = _ndi.label(_apU | _pl)
_keepl = np.unique(_lab3[_pl]); _keepl = _keepl[_keepl > 0]
_all = np.isin(_lab3, _keepl) & (_ndi.distance_transform_edt(~_pl) * _FR < 25)
_al = np.maximum(_al, _ndi.gaussian_filter(_all.astype(np.float32), 3))
_al = np.clip((_al - 0.5) * 4 + 0.5, 0, 1)
# hand-traced plaza outline (spec/<ground>_fc_hand.json 'outline'): inside its bbox the paving edge is the traced line, not aerial pixels
if 'outline' in _HJ:
    _oi = Image.new('L', (_W * 2, _H * 2), 0); _IDw.Draw(_oi).polygon([((x - _x0) / _FR * 2, (_y1 - y) / _FR * 2) for x, y in _HJ['outline']], fill=255)
    _om = np.asarray(_oi.resize((_W, _H), Image.LANCZOS)).astype(np.float32) / 255
    _ox = np.array(_HJ['outline'], float); _inb = ((_xx + _x0) >= _ox[:, 0].min()) & ((_y1 - _yy) >= _ox[:, 1].min())
    _al = np.where(_inb, _om, _al)
# lawn, beds and tree canopy inside the plaza outline are not paving: open the overlay there so the terrain layer's
# lawn/bed classes show. Vegetation from the z19 aerial (reference only): green (a* < -3) or dark beds (L < 42), 1 m open/close.
_vp = os.path.join(HERE, 'data', 'optus', 'sat_hi_plaza.png')
if os.path.exists(_vp) and 'outline' in _HJ:
    from skimage import color as _skc
    _vl = _skc.rgb2lab(_ndi.gaussian_filter(np.asarray(Image.open(_vp).convert('RGB')) / 255.0, (2, 2, 0)))
    _veg = (_vl[..., 1] < -3) | (_vl[..., 0] < 42) | ((_vl[..., 0] < 52) & (_vl[..., 2] > 15))   # green, dark, brown mulch
    _veg = _ndi.binary_closing(_ndi.binary_opening(_veg, iterations=8), iterations=8)
    _VR, _VX0, _VY1 = 0.125, 80.0, 135.0
    _gx = ((_xx + _x0) - _VX0) / _VR; _gy = (_VY1 - (_y1 - _yy)) / _VR
    _ok = (_gx >= 0) & (_gy >= 0) & (_gx < _veg.shape[1] - 1) & (_gy < _veg.shape[0] - 1)
    _vv = np.zeros(_al.shape, bool); _vv[_ok] = _veg[_gy[_ok].astype(int), _gx[_ok].astype(int)]
    for _p in _HJ['planters'] + [{'pts': b['pts']} for b in _HJ['bands'] if b.get('tone') == 3]:   # planter beds keep their own mulch fill and rims
        _pm = Image.new('L', (_W, _H), 0); _IDw.Draw(_pm).polygon([((x - _x0) / _FR, (_y1 - y) / _FR) for x, y in _p['pts']], fill=255); _vv &= ~(np.asarray(_pm) > 127)
    # each vegetation area gets its own fill in this layer (not the terrain underneath): lawn where the aerial is green
    # and open (L >= 45, 0.5 m open), mulch bed under canopy and in the beds; trees stand on it as meshes
    _sl, _sn = _ndi.label(_vv); _sz = np.bincount(_sl.ravel()) * _FR * _FR; _sz[0] = 1e9; _vv &= (_sz >= 6)[_sl]   # drop specks < 6 m2 (bollard and person shadows)
    _gr = np.zeros(_al.shape, bool); _gq = _vl[..., 1] < -3; _gr[_ok] = _gq[_gy[_ok].astype(int), _gx[_ok].astype(int)]
    _sl, _sn = _ndi.label(_vv); _sz = np.bincount(_sl.ravel()) * _FR * _FR; _hg = np.bincount(_sl.ravel(), _gr.ravel()) > 0
    _kp = (_sz >= 25) | _hg; _kp[0] = False; _vv &= _kp[_sl]   # a shadow is never a bed: a patch needs green in it or >= 25 m2
    _lw = np.zeros(_al.shape, bool); _gl = _ndi.binary_opening((_vl[..., 1] < -3) & (_vl[..., 0] >= 45), iterations=4)
    _lw[_ok] = _gl[_gy[_ok].astype(int), _gx[_ok].astype(int)]; _lw &= _vv
    _vlab, _vn = _ndi.label(_vv); _ls = _ndi.mean(_lw, _vlab, np.arange(1, _vn + 1)) if _vn else np.zeros(0)   # a patch that is >= 25 % open lawn is a lawn (tree shade on grass is grass)
    _lw = _vv & np.concatenate([[False], _ls >= 0.25])[_vlab]
    _rgb[_vv & ~_lw] = np.array([74, 58, 44], np.float32) * (1 + 0.08 * _hs[_vv & ~_lw])[:, None]
    _rgb[_lw] = np.array(spec['palette']['lawn'], np.float32) * (1 + 0.06 * _hs[_lw])[:, None]
    print('fc veg lawn m2', int(_lw.sum() * _FR * _FR), 'bed m2', int((_vv & ~_lw).sum() * _FR * _FR))
    print('fc veg cut m2', int(_vv.sum() * _FR * _FR))
# south edge (hand trace on z19 sat_hi_south.png, 10 m grid): terraced planters, access road, tree mound, car-park
# turnaround and island, stair. Each surface is painted by hand-made fill; terrace walls and the hut are meshes (fc_scene.py)
if 'south' in _HJ:
    _SC = {'mulch_gold': (150, 122, 74), 'lawn': tuple(spec['palette']['lawn']), 'bed': (74, 58, 44), 'concrete': (178, 174, 166), 'asphalt': (74, 76, 78), 'stair': (170, 166, 158)}
    _oi2 = Image.new('L', (_W, _H), 0); _IDw.Draw(_oi2).polygon([((x - _x0) / _FR, (_y1 - y) / _FR) for x, y in _HJ['outline']], fill=255); _inO = np.asarray(_oi2) > 127
    for _p in _HJ['south']:
        _pm = Image.new('L', (_W * 2, _H * 2), 0); _IDw.Draw(_pm).polygon([((x - _x0) / _FR * 2, (_y1 - y) / _FR * 2) for x, y in _p['pts']], fill=255)
        _pf = np.asarray(_pm.resize((_W, _H), Image.LANCZOS)).astype(np.float32) / 255; _pk = _pf > 0.5
        _cl = np.array(_SC[_p['kind']], np.float32)
        if _p['kind'] in ('concrete', 'stair'): _tx = (1 + 0.04 * _hs) * np.where(_jt, 0.85, 1.0)
        elif _p['kind'] == 'asphalt': _tx = 1 + 0.03 * _hs
        else: _tx = 1 + 0.08 * _hs
        if _p['kind'] == 'stair': _tx = _tx * np.where((_yy % 0.4) < 0.08, 0.7, 1.0)   # step nosings every 0.4 m
        _pk &= ~(_inO if _p['kind'] != 'mulch_gold' else np.zeros_like(_pk)); _rgb[_pk] = _cl[None] * _tx[_pk][:, None]; _al = np.where(_pk, 1.0, _al)
    print('south surfaces', len(_HJ['south']))
# stadium fence: no plaza paving inside the stadium's outer ellipse (centre (-16, 0), 143 x 128 m half axes, read off the aerial)
_al = _al * ((((_xx + _x0 + 16) / 143) ** 2 + ((_y1 - _yy + 16 * 0) / 128) ** 2) > 1)
_out = np.dstack([_rgb.clip(0, 255), _al * 255]).astype(np.uint8)
Image.fromarray(_out, 'RGBA').save(os.path.join(OUT, 'forecourt.png'))
_json.dump({'x0': _x0, 'x1': _x1, 'y0': _y0, 'y1': _y1}, open(os.path.join(OUT, 'forecourt.json'), 'w'))
print('forecourt overlay', _W, _H, round(_x0), round(_x1), round(_y0), round(_y1))
