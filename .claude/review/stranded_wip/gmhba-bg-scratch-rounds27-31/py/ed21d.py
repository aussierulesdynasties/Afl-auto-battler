import sys
def ed(p, pairs):
    s = open(p, encoding='utf-8', newline='').read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a[:60]); s = s.replace(a, b)
    open(p, 'w', encoding='utf-8', newline='').write(s)
ed('coast21.py', [
 ("_ns += [float(st.ravel()[[a0, a1, a2, a3]].max())] * len(Pq); _nw += list(sd < 0)", "_ns += [float(st.ravel()[[a0, a1, a2, a3]].max())] * len(Pq); _nw += list(sd < 0); _ne += list(edge)"),
 ("_nv, _nf, _nc, _nh, _ns, _nw = [], [], [], [], [], []", "_nv, _nf, _nc, _nh, _ns, _nw, _ne = [], [], [], [], [], [], []"),
 ("    FF = np.concatenate([FF[_keep], np.array(_nf)])", "    FF = np.concatenate([FF[_keep], np.array(_nf)])\n    _ev = np.concatenate([np.zeros(_base, bool), np.array(_ne, bool)]); SHOREF = _ev[FF].any(1)"),
])
ed('scene.py', [
 ("if spec.get('coast_v2'): exec(open(os.path.join(HERE, 'coast21.py'), encoding='utf-8').read())\n", "SHOREF = None\nif spec.get('coast_v2'): exec(open(os.path.join(HERE, 'coast21.py'), encoding='utf-8').read())\nif SHOREF is None: SHOREF = np.zeros(len(FF), bool)\n"),
 ("_sub = (_fc < 5500) & ~_stf & ~WV.ravel()[FF].all(1)", "_sub = (_fc < 5500) & ~_stf & ~WV.ravel()[FF].all(1) & ~SHOREF\nif SHOREF.any():   # sea wall / beach band along the real coastline: its own plain mesh\n    _F = FF[SHOREF]; _o = mk_obj('bg_shore', VF, _F.tolist(), mat_vcol('shore', 0.9)); _l = _F.ravel()\n    _shc = np.array(lin((176, 168, 146)))[None, :3] * (1 - hz) + np.array(lin(PAL['haze']))[None, :3] * hz\n    set_corner_col(_o.data, np.concatenate([_shc[_l], np.ones((len(_l), 1))], 1))"),
 ("FF = FF[~_wf & ~_sub]", "FF = FF[~_wf & ~_sub & ~SHOREF]"),
])
print('ok')
