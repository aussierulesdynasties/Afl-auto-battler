import json, shutil
H = 'D:/Temp/claude/b012626c2f559e8f/6855d913-d54b-43b8-92a6-1e4e1b34589b/scratchpad/proto/'
def sub(fn, a, b):
    s = open(H + fn, newline='').read()
    if '\r\n' in s: a, b = a.replace('\n', '\r\n'), b.replace('\n', '\r\n')
    assert s.count(a) == 1, (fn, a[:60], s.count(a))
    open(H + fn, 'w', newline='').write(s.replace(a, b))
for f in ('prep.py', 'scene.py', 'spec/adelaide.json'): shutil.copy(H + f, H + f + '.bak_court')
# prep: slab = union of the court boxes (+1 m run-off), not the convex hull of the group
sub('prep.py', "        dr.polygon(P(_hull([p for m in mem for p in m[0]])), fill=tuple(PAL[mem[0][1]]))",
    "        for _pp in _slabpolys(mem): dr.polygon(P(_pp), fill=tuple(PAL[mem[0][1]]))")
sub('prep.py', "def _obox(pts):",
    "def _slabpolys(mem):\n    from shapely.geometry import Polygon\n    from shapely.ops import unary_union\n"
    "    U = unary_union([Polygon(m[0]).buffer(1.0, join_style=2) for m in mem]).buffer(0.5, join_style=2).buffer(-0.5, join_style=2)\n"
    "    G = list(U.geoms) if hasattr(U, 'geoms') else [U]\n"
    "    return [[(round(x, 2), round(y, 2)) for x, y in list(g.simplify(0.2).exterior.coords)[:-1]] for g in G]\ndef _obox(pts):")
sub('prep.py', "'slabs': [[mem_[0][1], _hull([p for m in mem_ for p in m[0]])] for mem_ in ([CT[i] for i in range(len(CT)) if find(i) == r] for r in set(find(i) for i in range(len(CT))))]",
    "'slabs': [[mem_[0][1], _pp] for mem_ in ([CT[i] for i in range(len(CT)) if find(i) == r] for r in set(find(i) for i in range(len(CT)))) for _pp in _slabpolys(mem_)]")
# scene: slab polygons are concave now -> triangulate with shapely, not a centre fan; grass courts keep their grass (no blue play quad)
sub('scene.py', "        V = [(x, y, z) for x, y in H] + [(H[:, 0].mean(), H[:, 1].mean(), z)]; c = len(H)\n        set_uv_box(mk_obj('bg_court_slab_' + k, V, [[c, i, (i + 1) % c] for i in range(c)], mats[k]).data, 4.0)   # grain tile 0.25 m",
    "        from shapely.geometry import Polygon as _Pg\n        from shapely.ops import triangulate as _tri\n        _pg = _Pg(H); V, F = [], []\n"
    "        for t in _tri(_pg):\n            if not _pg.contains(t.representative_point()): continue\n"
    "            n0 = len(V); V.extend([(x, y, z) for x, y in list(t.exterior.coords)[:3]]); F.append([n0, n0 + 1, n0 + 2])\n"
    "        set_uv_box(mk_obj('bg_court_slab_' + k, V, F, mats[k]).data, 4.0)")
sub('scene.py', "                o_ = -L_ / 2 + w_ * (i + 0.5); _subs.append((cx + ux * o_, cy + uy * o_, ang + math.pi / 2, W_, w_))\n        else: _subs.append((cx, cy, ang, L_, W_))\n    cj['courts'] = [['play'] + list(q) for q in _subs]",
    "                o_ = -L_ / 2 + w_ * (i + 0.5); _subs.append((k, cx + ux * o_, cy + uy * o_, ang + math.pi / 2, W_, w_))\n        else: _subs.append((k, cx, cy, ang, L_, W_))\n    cj['courts'] = [list(q) for q in _subs]")
sub('scene.py', "        wx, wy = -uy, ux; q_ = len(PV_)\n        PV_.extend(",
    "        wx, wy = -uy, ux; q_ = len(PV_)\n        if k != 'court_grass': PV_.extend(")
sub('scene.py', "for a_, b_ in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]); PF_.append([q_, q_ + 1, q_ + 2, q_ + 3])",
    "for a_, b_ in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]) if k != 'court_grass' else None\n        if k != 'court_grass': PF_.append([q_, q_ + 1, q_ + 2, q_ + 3])")
# spec: the 4 NW courts of the Memorial Drive block are grass on the satellite
s = json.load(open(H + 'spec/adelaide.json'))
s['palette']['court_grass'] = [84, 110, 62]
s['paint_at'] = [[-262.8, -127.8, 'court_grass'], [-247.3, -124.5, 'court_grass'], [-265.0, -93.3, 'court_grass'], [-249.7, -90.2, 'court_grass']]
json.dump(s, open(H + 'spec/adelaide.json', 'w'), indent=1)
print('ok')
