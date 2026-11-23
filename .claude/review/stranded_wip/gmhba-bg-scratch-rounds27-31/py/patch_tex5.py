import sys
p = sys.argv[1]; t = open(p, newline='').read()
a_start = t.index("_wq = np.array("); a_end = t.index("for _nm, _sel, _mt in (")
b = ("_g = np.linspace(-FA, FA, 61); _GX, _GY = np.meshgrid(_g, _g); _wq = np.stack([_GX.ravel(), _GY.ravel(), np.full(_GX.size, ZSEA + 0.3)], 1)\n"
     "_i = np.arange(60); _I, _J = np.meshgrid(_i, _i); _a = (_J * 61 + _I).ravel(); _wf4 = np.stack([_a, _a + 1, _a + 62, _a + 61], 1)\n"
     "_wo = mk_obj('bg_far_water', _wq.tolist(), _wf4.tolist(), mat_vcol('far_water', 0.55))\n"
     "_wh = (1 - np.exp(-np.hypot(_wq[:, 0], _wq[:, 1]) / spec.get('haze_m', 22000)))[:, None] * 0.85\n"
     "_wc = np.array(lin((30, 54, 76)))[None, :3] * (1 - _wh) + np.array(lin(PAL['haze']))[None, :3] * _wh\n"
     "set_corner_col(_wo.data, np.concatenate([_wc[_wf4.ravel()], np.ones((_wf4.size, 1))], 1))\n")
t = t[:a_start] + b + t[a_end:]
open(p, 'w', newline='').write(t); print('ok')
