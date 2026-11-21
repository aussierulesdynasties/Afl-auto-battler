"""Director 2026-11-20 'Yes, fine strip': a 1.5 m land mesh in a band along the traced shore (2 coarse cells, 15 m,
each side); the 7.5 m terrain is sunk under water inside the band so only the fine land and the water show there."""
P = 'scene.py'; s = open(P, newline='').read(); nl = '\r\n' if '\r\n' in s else '\n'
def rep(a, b):
    global s
    a = a.replace('\n', nl); b = b.replace('\n', nl); assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
rep("        Z[_IN & ~_BED] = WZ - 0.2; Z[_BED] = WZ - 3.0\n",
    "        def _dil(m_, k_):\n"
    "            for _ in range(k_):\n"
    "                e_ = m_.copy(); e_[1:] |= m_[:-1]; e_[:-1] |= m_[1:]; e_[:, 1:] |= m_[:, :-1]; e_[:, :-1] |= m_[:, 1:]; m_ = e_\n"
    "            return m_\n"
    "        _BAND = _dil(_IN, 2) & _SAT\n"
    "        Z[_dil(_IN, 1) & _SAT] = WZ - 3.0   # coarse ground sunk under the band; the fine strip is the land there\n")
rep("for p in ob.data.polygons: p.use_smooth = True\nif WZ is not None:\n",
    "for p in ob.data.polygons: p.use_smooth = True\n"
    "if WZ is not None and SH is not None:\n"
    "    _L = np.load(os.path.join(D, 'shore_fine.npy')); _m = _L.shape[0]; _fs = 1.5; _o0 = -700.0\n"
    "    _r, _c = np.nonzero(_L)\n"
    "    _cx = (_c + 0.5) * _fs + _o0; _cy = (_r + 0.5) * _fs + _o0\n"
    "    _ci_ = np.clip(np.round((_cx + NE) / NS).astype(int), 0, n - 1); _cj_ = np.clip(np.round((_cy + NE) / NS).astype(int), 0, n - 1)\n"
    "    _k = _BAND[_cj_, _ci_]; _r, _c = _r[_k], _c[_k]\n"
    "    _vid = np.stack([_r * (_m + 1) + _c, _r * (_m + 1) + _c + 1, (_r + 1) * (_m + 1) + _c + 1, (_r + 1) * (_m + 1) + _c], 1)\n"
    "    _u, _inv = np.unique(_vid.ravel(), return_inverse=True)\n"
    "    _fv = np.stack([(_u % (_m + 1)) * _fs + _o0, (_u // (_m + 1)) * _fs + _o0, np.full(len(_u), WZ + 2.0)], 1)\n"
    "    _ff = _inv.reshape(-1, 4)\n"
    "    fob = mk_obj('bg_shore_land', _fv, _ff.tolist(), gm)\n"
    "    _fl = _ff.ravel(); _fuv = np.stack([(_fv[_fl, 0] + NE) / (2 * NE), (_fv[_fl, 1] + NE) / (2 * NE)], 1)\n"
    "    set_uv(fob.data, _fuv)\n"
    "    _fd = fob.data.uv_layers.new(name='UVDetail'); _fd.data.foreach_set('uv', (_fuv * (2 * NE / 4.0)).astype(np.float32).ravel())\n"
    "    print('shore strip quads', len(_ff))\n"
    "if WZ is not None:\n")
open(P, 'w', newline='').write(s); print('ok')
