H = 'D:/Temp/claude/b012626c2f559e8f/6855d913-d54b-43b8-92a6-1e4e1b34589b/scratchpad/proto/'
def sub(fn, a, b):
    s = open(H + fn, newline='').read()
    if '\r\n' in s: a, b = a.replace('\n', '\r\n'), b.replace('\n', '\r\n')
    assert s.count(a) == 1, (fn, a[:60], s.count(a))
    open(H + fn, 'w', newline='').write(s.replace(a, b))
sub('scene.py', "        _FP = os.path.join(D, 'fence_polys.json')\n        if os.path.exists(_FP):\n"
    "            from shapely.geometry import Polygon as _Pg\n            from shapely.ops import unary_union as _uu\n"
    "            _U = _uu([_Pg(t) for t in json.load(open(_FP)) if len(t) >= 3]).buffer(3.0)\n"
    "            _U = max(_U.geoms, key=lambda g: g.area) if hasattr(_U, 'geoms') else _U\n"
    "            _ring = list(_Pg(_U.exterior).simplify(0.15).exterior.coords)[:-1]; _k = len(_ring)\n",
    "        _FP = os.path.join(D, 'fence_outline.json')   # fence_outline.py (system python: Blender has no shapely)\n        if os.path.exists(_FP):\n"
    "            _ring = [tuple(q) for q in json.load(open(_FP))]; _k = len(_ring)\n"
    "            if sum(_ring[i][0] * _ring[(i + 1) % _k][1] - _ring[(i + 1) % _k][0] * _ring[i][1] for i in range(_k)) < 0: _ring = _ring[::-1]   # CCW so the prism faces point out\n")
sub('scene.py', "        from shapely.geometry import Polygon as _Pg\n        from shapely.ops import triangulate as _tri\n        _pg = _Pg(H); V, F = [], []\n"
    "        for t in _tri(_pg):\n            if not _pg.contains(t.representative_point()): continue\n"
    "            n0 = len(V); V.extend([(x, y, z) for x, y in list(t.exterior.coords)[:3]]); F.append([n0, n0 + 1, n0 + 2])\n",
    "        V = [(x, y, z) for x, y in H]   # slab outline is concave now (union of court boxes): ear-clip it\n"
    "        F = [list(t) for t in mathutils.geometry.tessellate_polygon([[mathutils.Vector(v) for v in V]])]\n")
s = open(H + 'build.sh', newline='').read()
a = "C:/Python314/python.exe -E fence_mask.py data/$g/prep/fence_polys.json data/$g/prep/fence_mask.npy;"
assert s.count(a) == 1
open(H + 'build.sh', 'w', newline='').write(s.replace(a, a + " C:/Python314/python.exe -E fence_outline.py data/$g/prep/fence_polys.json data/$g/prep/fence_outline.json;"))
print('ok')
