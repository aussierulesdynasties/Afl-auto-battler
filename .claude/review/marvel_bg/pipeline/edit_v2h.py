"""Orbit crops: pale streaks across the rail yard = OSM service roads (5 m) in street asphalt, glaring on dark ballast.
Service roads keep their place but are drawn darker (vertex colour x0.6, worn yard asphalt)."""
def sub(path, pairs):
    s = open(path, newline='').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, a[:60]); s = s.replace(a, b)
    open(path, 'w', newline='').write(s)
sub('roads_pf.py', [
 ("        roads.append((_dens(P, 1.5), WDR[hw], two))", "        roads.append((_dens(P, 1.5), WDR[hw], two)); SERV.append(hw == 'service')"),
 ("    roads = []\n", "    roads = []; SERV = []\n"),
 ("    RV, RF_, LV, LF = [], [], [], []\n", "    RV, RF_, LV, LF = [], [], [], []; DK = []\n"),
 ("        for r in _runs(ok): _ribbon(Q[r], 0, w, 0.04, RV, RF_)\n",
  "        _v0 = len(RV)\n        for r in _runs(ok): _ribbon(Q[r], 0, w, 0.04, RV, RF_)\n        if SERV[ri]: DK.append((_v0, len(RV)))\n"),
 ("set_uv(ob.data, co[vi, :2] / TILE); _mottle(ob.data, co)",
  "set_uv(ob.data, co[vi, :2] / TILE); _mottle(ob.data, co)\n"
  "        _f = np.ones(len(RV))\n        for a_, b_ in DK: _f[a_:b_] = 0.6\n"
  "        _cc = np.zeros(len(ob.data.loops) * 4); ob.data.color_attributes['Col'].data.foreach_get('color', _cc); _cc = _cc.reshape(-1, 4)\n"
  "        _cc[:, :3] *= _f[vi][:, None]; ob.data.color_attributes['Col'].data.foreach_set('color', _cc.ravel())"),
])
print('ok')
