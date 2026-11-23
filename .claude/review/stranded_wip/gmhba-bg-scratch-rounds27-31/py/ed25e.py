import sys
p = sys.argv[1]; s = open(p, encoding='utf-8', newline='').read()
s = s.replace("np.linspace(-FA, FA, 241)", "np.linspace(-FA, FA, 481)").replace("_i = np.arange(240)", "_i = np.arange(480)").replace("_J * 241 + _I", "_J * 481 + _I").replace("_a + 242, _a + 241", "_a + 482, _a + 481")
a = "_wh = (1 - np.exp(-_r / spec.get('haze_m', 22000)))[:, None] * 0.85\n"
assert a in s
b = """_WC = np.load(os.path.join(D, 'water_col.npy')); _wr = np.clip(((FA - _wq[:, 1]) / 30).astype(int), 0, 1999); _wcl = np.clip(((_wq[:, 0] + FA) / 30).astype(int), 0, 1999)
_LU = np.load(os.path.join(D, 'landuse.npy')); _ref = np.array([lin(c)[:3] for c in [_WC[_LU == 3].mean(0)]])[0]
_ms = np.array([lin(c)[:3] for c in _WC[_wr, _wcl]]) / _ref   # measured tone relative to the bay mean: shallows, banks, channels
_wc = _wc * np.clip(_ms, 0.55, 1.8) ** 0.7
""" + a
s = s.replace(a, b); open(p, 'w', encoding='utf-8', newline='').write(s); print('ok')
