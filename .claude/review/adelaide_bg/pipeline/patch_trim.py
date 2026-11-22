import shutil
H = 'D:/Temp/claude/b012626c2f559e8f/6855d913-d54b-43b8-92a6-1e4e1b34589b/scratchpad/proto/'
def sub(fn, a, b):
    s = open(H + fn, newline='').read()
    if '\r\n' in s: a, b = a.replace('\n', '\r\n'), b.replace('\n', '\r\n')
    assert s.count(a) == 1, (fn, a[:60], s.count(a))
    open(H + fn, 'w', newline='').write(s.replace(a, b))
shutil.copy(H + 'scene.py', H + 'scene.py.bak_trim')
# after the old face-centre trim (kept as a coarse first pass), cut the base exactly along the fence outline
# (union of fence_polys + 3 m, the same margin as the mask) with an exact boolean: a straight edge, no 0.6 m sawtooth
sub('scene.py', "        bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(o.data); bm.free()\n        print('trimmed', o.name, len(kill), 'faces')",
    "        bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(o.data); bm.free()\n        print('trimmed', o.name, len(kill), 'faces')\n"
    "        _FP = os.path.join(D, 'fence_polys.json')\n"
    "        if os.path.exists(_FP):\n"
    "            from shapely.geometry import Polygon as _Pg\n            from shapely.ops import unary_union as _uu\n"
    "            _U = _uu([_Pg(t) for t in json.load(open(_FP)) if len(t) >= 3]).buffer(3.0)\n"
    "            _U = max(_U.geoms, key=lambda g: g.area) if hasattr(_U, 'geoms') else _U\n"
    "            _ring = list(_Pg(_U.exterior).simplify(0.15).exterior.coords)[:-1]; _k = len(_ring)\n"
    "            _pv = [(x, y, -30.0) for x, y in _ring] + [(x, y, 80.0) for x, y in _ring]\n"
    "            _pf = [list(range(_k))[::-1], list(range(_k, 2 * _k))] + [[i, (i + 1) % _k, _k + (i + 1) % _k, _k + i] for i in range(_k)]\n"
    "            _pm = bpy.data.meshes.new('trim_prism'); _pm.from_pydata(_pv, [], _pf); _pm.update()\n"
    "            _po = bpy.data.objects.new('trim_prism', _pm); bpy.context.scene.collection.objects.link(_po)\n"
    "            _md = o.modifiers.new('fence_cut', 'BOOLEAN'); _md.operation = 'INTERSECT'; _md.solver = 'EXACT'; _md.object = _po\n"
    "            bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=_md.name)\n"
    "            bpy.data.objects.remove(_po); print('fence cut', o.name, _k, 'pts', len(o.data.polygons), 'faces')")
print('ok')
