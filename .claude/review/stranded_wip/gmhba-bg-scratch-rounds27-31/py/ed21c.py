import sys
p = sys.argv[1]; s = open(p, encoding='utf-8', newline='').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
rep("vc = vc * (1 - hz) + lin(PAL['haze'])[None] * hz\n", "vc = vc * (1 - hz) + lin(PAL['haze'])[None] * hz\nif spec.get('coast_v2'): exec(open(os.path.join(HERE, 'coast21.py'), encoding='utf-8').read())\n")
rep("_wo = mk_obj('bg_far_water', _wq.tolist(), _wf4.tolist(), mat_vcol('far_water', 0.9)); _wo.active_material", "if spec.get('coast_v2'): exec(open(os.path.join(HERE, 'water21.py'), encoding='utf-8').read())\nelse:\n  _wo = mk_obj('bg_far_water', _wq.tolist(), _wf4.tolist(), mat_vcol('far_water', 0.9)); _wo.active_material")
rep("_wh = (1 - np.exp(-np.hypot(_wq[:, 0], _wq[:, 1]) / spec.get('haze_m', 22000)))[:, None] * 0.85\n_wc", "  _wh = (1 - np.exp(-np.hypot(_wq[:, 0], _wq[:, 1]) / spec.get('haze_m', 22000)))[:, None] * 0.85\n  _wc")
rep("set_corner_col(_wo.data, np.concatenate([_wc[_wf4.ravel()], np.ones((_wf4.size, 1))], 1))", "  set_corner_col(_wo.data, np.concatenate([_wc[_wf4.ravel()], np.ones((_wf4.size, 1))], 1))")
open(p, 'w', encoding='utf-8', newline='').write(s); print('ok')
