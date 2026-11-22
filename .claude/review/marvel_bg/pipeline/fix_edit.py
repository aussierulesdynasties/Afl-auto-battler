P = 'edit_water_pine.py'; s = open(P).read()
old = s[s.index("    from scipy import ndimage as _nd"):s.index("    Z[WG] = np.minimum")]
new = '''    _im = bpy.data.images.load(os.path.join(D, 'ground.png')); _w, _h = _im.size
    _G = (np.array(_im.pixels[:], np.float32).reshape(_h, _w, 4)[..., :3] * 255).round()   # rows bottom-up = south first
    _W = np.abs(_G - np.array(spec['palette']['water'], np.float32)).sum(2) < 12
    _ri = (np.arange(n) * _h / n).astype(int); _ci = (np.arange(n) * _w / n).astype(int)
    WG = _W[_ri][:, _ci]
    _d = WG.copy()
    for _ in range(2):
        _e = _d.copy(); _e[1:] |= _d[:-1]; _e[:-1] |= _d[1:]; _e[:, 1:] |= _d[:, :-1]; _e[:, :-1] |= _d[:, 1:]; _d = _e
    _rim = _d & ~WG
'''
s = s.replace(old, new); open(P, 'w').write(s); print('patched')
