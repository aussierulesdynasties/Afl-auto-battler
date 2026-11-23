s = open('pools.py', encoding='utf-8', newline='').read()
a = "    v, f, uv = _D; o = len(v); v += [(x, y, _z) for x, y in _dk]"
assert a in s
s = s.replace(a, "    _SINK.append((_dk.copy(), _z))\n" + a, 1)
s = s.replace("_FL = ([], [])", "_FL = ([], []); _SINK = []", 1)
b = "    if _FL[1]: mk_obj('bg_pool_floorlines'"
assert b in s
s = s.replace(b, """    # basin cut: near-ground vertices inside each deck drop 0.35 m under it, so the deck sits flush and the
    # recessed water is not hidden by terrain (deck edge 4 m out covers the dip)
    from matplotlib.path import Path as _MP
    _g = bpy.data.objects['bg_near_ground'].data; _gv = np.zeros(len(_g.vertices) * 3); _g.vertices.foreach_get('co', _gv); _gv = _gv.reshape(-1, 3)
    _ns = 0
    for _P, _zp in _SINK:
        _in = _MP(_P).contains_points(_gv[:, :2], radius=-0.5); _ns += int(_in.sum()); _gv[_in, 2] = np.minimum(_gv[_in, 2], _zp - 0.35)
    _g.vertices.foreach_set('co', _gv.ravel()); _g.update(); print('pool ground verts sunk', _ns)
""" + b, 1)
open('pools.py', 'w', encoding='utf-8', newline='').write(s); print('ok')
