import sys
p = sys.argv[1]; t = open(p, newline='').read()
def R(a, b):
    global t
    assert t.count(a) == 1, a[:70]; t = t.replace(a, b)
R("0.45 * np.array(rc)[:3] + 0.55 * np.array(lin((150, 152, 150)))[:3], np.array(lin((168, 168, 166)))[:3])",
  "0.35 * np.array(rc)[:3] + 0.65 * np.array(lin((120, 123, 124)))[:3], np.array(lin((134, 135, 134)))[:3])")
# water: one flat plane at sea level; drowned cells sink below it so the shoreline follows the terrain contour
R("VF[WV.ravel(), 2] = ZSEA\n", "VF[WV.ravel(), 2] = ZSEA - 4.0\n")
R("_wf = WV.ravel()[FF].all(1);", "_wf = np.zeros(len(FF), bool);")
R("for _nm, _sel, _mt in (('bg_far_water', _wf, mat_vcol('far_water', 0.12)), ",
  "_wq = np.array([(-FA, -FA, ZSEA + 0.3), (FA, -FA, ZSEA + 0.3), (FA, FA, ZSEA + 0.3), (-FA, FA, ZSEA + 0.3)])\n"
  "_wo = mk_obj('bg_far_water', _wq.tolist(), [(0, 1, 2, 3)], mat_vcol('far_water', 0.55))\n"
  "_wh = (1 - np.exp(-np.hypot(_wq[:, 0], _wq[:, 1]) / spec.get('haze_m', 22000)))[:, None] * 0.85\n"
  "set_corner_col(_wo.data, np.concatenate([np.array(lin((30, 54, 76)))[None, :3] * 1 + 0 * _wh, np.ones((4, 1))], 1))\n"
  "for _nm, _sel, _mt in (")
R("    if _sel.any():\n        _F = FF[_sel]", "    if _sel.any():\n        _F = FF[_sel]")
R("_sub = ~_wf & (_fc < 9000) & ~_stf", "_sub = (_fc < 5500) & ~_stf & ~WV.ravel()[FF].all(1)")
open(p, 'w', newline='').write(t); print('ok')
