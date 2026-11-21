import json
pass
p='scene.py'; t=open(p,encoding='utf-8',newline='').read()
o='_GROUND = ob'; assert t.count(o)==1
t=t.replace(o,'''_GROUND = ob
# shore band: densify the terrain within ~9 m of each water body and slope it evenly over 6 m from the land down to
# that body's level - 0.15 m, so banks no longer step at the terrain grid
import mathutils, mathutils.kdtree, mathutils.bvhtree
_sp, _sz, _wv, _wt = [], [], [], []
for _w in _SF['water']:
    _v = np.array(_w['v'], float); _cnt = {}
    for _t in _w['t']:
        _wt.append([len(_wv) + q for q in _t])
        for _a, _b2 in ((_t[0], _t[1]), (_t[1], _t[2]), (_t[2], _t[0])):
            _k = (min(_a, _b2), max(_a, _b2)); _cnt[_k] = _cnt.get(_k, 0) + 1
    _wv += [(x, y, 0.0) for x, y in _v]
    for (_a, _b2), _c in _cnt.items():
        if _c != 1: continue
        _L = np.linalg.norm(_v[_b2] - _v[_a]); _m = max(1, int(_L / 0.75))
        for _f in np.linspace(0, 1, _m + 1): _sp.append(_v[_a] + (_v[_b2] - _v[_a]) * _f); _sz.append(_w['z'])
_WIN = mathutils.bvhtree.BVHTree.FromPolygons(_wv, _wt) if _wt else None
if _sp:
    _kd = mathutils.kdtree.KDTree(len(_sp))
    for _i, _q in enumerate(_sp): _kd.insert((_q[0], _q[1], 0.0), _i)
    _kd.balance()
    def _near(x, y): _c, _i, _d = _kd.find((x, y, 0.0)); return _d, _sz[_i]
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for _ in range(4):   # 7.5 m grid -> ~0.95 m inside the band
        _ed = [e for e in bm.edges if e.calc_length() > 1.0 and _near(*((e.verts[0].co.xy + e.verts[1].co.xy) / 2))[0] < 9.0]
        if not _ed: break
        bmesh.ops.subdivide_edges(bm, edges=_ed, cuts=1, use_grid_fill=True)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    _nb = 0
    for v_ in bm.verts:
        d_, wz_ = _near(v_.co.x, v_.co.y)
        if d_ > 6.0: continue
        _in = _WIN is not None and _WIN.ray_cast(mathutils.Vector((v_.co.x, v_.co.y, 10.0)), mathutils.Vector((0, 0, -1)))[0] is not None
        lo = wz_ - 0.15
        if _in: v_.co.z = min(v_.co.z, lo)
        else:
            top = float(height(v_.co.x, v_.co.y)) if 'height' in globals() else v_.co.z
            v_.co.z = lo + (max(top, lo) - lo) * (d_ / 6.0); _nb += 1
    bm.to_mesh(ob.data); bm.free(); ob.data.update(); print('shore band verts', _nb, 'ground faces', len(ob.data.polygons))
''')
open(p,'w',encoding='utf-8',newline='').write(t); print('ok')
