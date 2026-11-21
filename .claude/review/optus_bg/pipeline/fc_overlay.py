# exec'd from clsfy.py after the forecourt mask _pv exists.
# Forecourt overlay (plan session 2026-11-20): the paving bands are traced from the aerial as smooth curves
# (each tone's vote field is Gaussian-smoothed at aerial resolution; the band edge is the curve where two
# fields cross, rendered anti-aliased at 0.1 m/px), then every band is filled with a hand-made slab tile:
# 1.2 x 0.6 m slabs in stretcher bond, 4 cm darker joints, +-4 % per-slab tone. No aerial pixel is used as colour.
import json as _json
_FR = 0.1   # m per texture pixel
_ys, _xs = np.nonzero(_pv)
_x0 = -NEAR + _xs.min() * PX - 4; _x1 = -NEAR + (_xs.max() + 1) * PX + 4
_y1 = NEAR - _ys.min() * PX + 4; _y0 = NEAR - (_ys.max() + 1) * PX - 4
_W = int((_x1 - _x0) / _FR); _H = int((_y1 - _y0) / _FR)
_sat = Image.open(_sp).convert('RGB'); _SR = 2 * NEAR / _sat.size[0]
_crop = _sat.crop((int((_x0 + NEAR) / _SR), int((NEAR - _y1) / _SR), int((_x1 + NEAR) / _SR), int((NEAR - _y0) / _SR)))
_cr = np.asarray(_crop).astype(np.float32) / 255
_ref2 = np.array([[0.70, 0.50, 0.46], [0.80, 0.73, 0.64], [0.58, 0.55, 0.53]], np.float32)
_t2 = ((_cr[..., None, :] - _ref2[None, None]) ** 2).sum(-1).argmin(-1); _ok2 = _cr.mean(2) >= 0.32
_sg = 6.0 / _SR   # 6 m: bands are 4-15 m wide, so this keeps them and removes speckle
_F = np.stack([_ndi.gaussian_filter(((_t2 == k) & _ok2).astype(np.float32), _sg) * (1.0, 0.85, 0.75)[k] for k in range(3)], -1)
_F = np.stack([np.asarray(Image.fromarray(_F[..., k]).resize((_W, _H), Image.BICUBIC)) for k in range(3)], -1)
# soft argmax: weight each tone by how far its field leads, so curve edges are anti-aliased (about 0.3 m wide)
_mx = _F.max(-1, keepdims=True); _wt = np.exp((_F - _mx) / (0.02 * _mx.clip(1e-3) + 1e-4)); _wt /= _wt.sum(-1, keepdims=True)
_tones = np.array(spec['forecourt_tones'], np.float32)
# bands traced at 1.5 m from the aerial (every salmon, beige and grey band, islands under 6 m2 merged away);
# each tone's field is upsampled bicubic to 0.1 m and the band edge is where the fields cross: smooth curves
_gf = _ndi.gaussian_filter; _Lc = _cr.mean(2); _rbc = (_cr[..., 0] - _cr[..., 2]) / (_Lc + 1e-3)
_pw = ((_Lc > 0.40) & ~((_cr[..., 1] > _cr[..., 0]) & (_cr[..., 1] > _cr[..., 2]))).astype(np.float32)
_lmn = lambda x: _gf(x * _pw, 12 / _SR) / (_gf(_pw, 12 / _SR) + 1e-3)
_scb = (_gf(_Lc, 0.4 / _SR) - _lmn(_Lc)) * 3 - (_gf(_rbc, 0.4 / _SR) - _lmn(_rbc))   # beige ribbon = lighter and less red than its 12 m surround
_G = np.stack([_gf((_scb <= 0).astype(np.float32), 0.75 / _SR), _gf((_scb > 0).astype(np.float32), 0.75 / _SR), np.zeros_like(_Lc)], -1)
_lb2 = _G.argmax(-1)
for _k in range(3):
    _l, _n = _ndi.label(_lb2 == _k); _sz = _ndi.sum(np.ones_like(_l), _l, range(1, _n + 1))
    _small = np.isin(_l, 1 + np.nonzero(_sz * _SR * _SR < 6)[0])
    if _small.any(): _G2 = _G.copy(); _G2[..., _k] = -1; _lb2[_small] = _G2[_small].argmax(-1)
_G = np.stack([_ndi.gaussian_filter((_lb2 == k).astype(np.float32), 0.8 / _SR) for k in range(3)], -1)
_G = np.stack([np.asarray(Image.fromarray(_G[..., k]).resize((_W, _H), Image.BICUBIC)) for k in range(3)], -1)
_mx = _G.max(-1, keepdims=True); _wt = np.exp((_G - _mx) / 0.03); _wt /= _wt.sum(-1, keepdims=True)
_rgb = (_wt[..., :, None] * _tones[None, None]).sum(-2)
# slab tile
_yy, _xx = np.mgrid[0:_H, 0:_W].astype(np.float32) * _FR
_row = np.floor(_yy / 0.6); _xs2 = _xx + (_row % 2) * 0.6; _sc = np.floor(_xs2 / 1.2)
_jt = np.minimum(np.minimum(_yy % 0.6, 0.6 - _yy % 0.6), np.minimum(_xs2 % 1.2, 1.2 - _xs2 % 1.2)) < 0.03
_hs = np.sin(_row * 12.9898 + _sc * 78.233) * 43758.5453; _hs = (_hs - np.floor(_hs)) * 2 - 1
_rgb *= (1 + 0.04 * _hs)[..., None]
_rgb *= np.where(_jt, 0.78, 1.0)[..., None]
# band edges: a darker 8 cm border course where tones change
_lab = _wt.argmax(-1); _be = (_ndi.grey_dilation(_lab, 2) != _ndi.grey_erosion(_lab, 2))
_rgb *= np.where(_be, 0.85, 1.0)[..., None]
# alpha: the forecourt mask, upsampled smooth
_m = _pv[_ys.min():_ys.max() + 1, _xs.min():_xs.max() + 1].astype(np.float32)
_m = np.pad(_m, int(4 / PX))
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
_out = np.dstack([_rgb.clip(0, 255), _al * 255]).astype(np.uint8)
Image.fromarray(_out, 'RGBA').save(os.path.join(OUT, 'forecourt.png'))
_json.dump({'x0': _x0, 'x1': _x1, 'y0': _y0, 'y1': _y1}, open(os.path.join(OUT, 'forecourt.json'), 'w'))
print('forecourt overlay', _W, _H, round(_x0), round(_x1), round(_y0), round(_y1))
