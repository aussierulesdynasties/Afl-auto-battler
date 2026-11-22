p='surf.py'; s=open(p,encoding='utf-8').read()
def rep(o,n):
    global s; assert s.count(o)==1,o[:60]; s=s.replace(o,n)
rep("""        if g_ is not None and not g_.is_empty: wpolys.append(g_)
WATER = unary_union(wpolys).intersection(CLIP) if wpolys else Polygon()""",
"""        if g_ is not None and not g_.is_empty: wpolys.append(g_)
# each OSM water body keeps its own level (Torrens Lake sits above the weir, the river below it): overlaps go to the first
WBODY, _seen = [], Polygon()
for g_ in wpolys:
    g_ = g_.intersection(CLIP).difference(_seen)
    if g_.area > 1.0: WBODY.append(g_); _seen = _seen.union(g_)
WATER = unary_union(WBODY) if WBODY else Polygon()""")
rep("""def water_mesh(g):
    out = []
    for p in parts(g):
        bz = [float(height_at(x, y)) for x, y in shapely.segmentize(p.exterior, 5).coords]""",
"""def water_mesh(bodies):
    out = []
    for bi, g in enumerate(bodies):
      _oth = unary_union([q for bj, q in enumerate(bodies) if bj != bi]).buffer(3.0) if len(bodies) > 1 else Polygon()
      _op = shapely.prepared.prep(_oth)
      for p in parts(g):
        # lowest shore point: shore against land only (not where it meets another water body, e.g. the weir, or the map edge)
        _sp = [(x, y) for x, y in shapely.segmentize(p.exterior, 5).coords if not _op.contains(shapely.Point(x, y)) and max(abs(x), abs(y)) < NEAR - 5]
        bz = [float(height_at(x, y)) for x, y in (_sp or list(p.exterior.coords))]""")
rep("'water': water_mesh(WATER)", "'water': water_mesh(WBODY)")
open(p,'w',encoding='utf-8').write(s); print('ok')
