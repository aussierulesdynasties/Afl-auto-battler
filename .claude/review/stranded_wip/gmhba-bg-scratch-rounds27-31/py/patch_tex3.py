import sys
p = sys.argv[1]; t = open(p, newline='').read()
def R(a, b, n=1):
    global t
    assert t.count(a) == n, (a[:60], t.count(a)); t = t.replace(a, b)
# --- sheds: 6 m corrugated tile, grey tone, flashing ---
R("        if kind == 'metal' and cls == 'block' and b['a'] >= 400: kind, RT = 'far', 12.0",
  "        if kind == 'metal' and cls == 'block' and b['a'] >= 400: kind, RT = 'far', 6.0")
R("        if kind == 'far' and b['a'] >= 1500: kind, RT = 'far', 24.0", "        if kind == 'far' and b['a'] >= 1500: kind, RT = 'far', 6.0")
R("        rv, rf, rcl, ruv = RF[kind]; r0 = len(rv)\n",
  "        if kind == 'far': rc = np.minimum(0.45 * np.array(rc)[:3] + 0.55 * np.array(lin((150, 152, 150)))[:3], np.array(lin((168, 168, 166)))[:3])   # zincalume grey, never paper white\n        rv, rf, rcl, ruv = RF[kind]; r0 = len(rv)\n")
R("            rf.append(tuple(r0 + i for i in range(k))); rcl += [rc] * k\n",
  "            rf.append(tuple(r0 + i for i in range(k))); rcl += [rc] * k\n"
  "            if kind == 'far':   # roof-edge flashing: a 0.36 m folded strip along every edge\n"
  "                for i_ in range(len(P)):\n"
  "                    p0, p1 = P[i_], P[(i_ + 1) % len(P)]; e_ = p1 - p0; L_ = float(np.hypot(*e_))\n"
  "                    if L_ < 0.05: continue\n"
  "                    nr = np.array([e_[1], -e_[0]]) / L_ * 0.18; o_ = len(FLS[0])\n"
  "                    for q in (p0 - nr, p1 - nr, p1 + nr, p0 + nr): FLS[0].append((q[0], q[1], top + 0.07))\n"
  "                    FLS[1].append((o_, o_ + 1, o_ + 2, o_ + 3)); FLS[2] += [lin((112, 116, 118))] * 4\n")
R("    CL = [[], [], [], []]   # clad shed walls", "    FLS = [[], [], []]\n    CL = [[], [], [], []]   # clad shed walls")
R("mat_mul('roof_%s_far' % cls, os.path.join(HERE, 'tex', 'mt', 'roof_far.png'), 0.6, 1 / 0.594)",
  "mat_mul('roof_%s_far' % cls, os.path.join(HERE, 'tex', 'mt', 'roof_shed.png'), 0.55, 1 / float(open(os.path.join(HERE, 'tex', 'mt', 'roof_shed.mean')).read()))")
R("    if not faces: return\n",
  "    if FLS[1]:\n        fo = mk_obj('bg_flash_' + cls + sfx, FLS[0], FLS[1], mat_vcol('flash_' + cls + sfx, 0.5))\n        set_corner_col(fo.data, np.concatenate([np.array([c[:3] for c in FLS[2]]), np.ones((len(FLS[2]), 1))], 1))\n    if not faces: return\n")
# --- towers: block facade variants, per-tower colour ---
R("build_class('tower', 'tower.png', 3.0, 3.6)\nbuild_class('tower_far', 'mt/city_far.png', 12.0, 7.2)\n",
  "PAL['walls_tower'] = list(PAL['walls_tower']) + [[150, 146, 138], [118, 124, 132], [176, 170, 158], [92, 104, 112], [196, 190, 176], [138, 120, 104]]; PAL['walls_tower_far'] = PAL['walls_tower']\n"
  "for _v in range(12): build_class('tower', 'fac/b%d.png' % _v, 3.6, 3.2, (_v, 12)); build_class('tower_far', 'fac/b%d.png' % _v, 3.6, 3.2, (_v, 12))\n")
# --- far terrain: Corio Bay water + suburb texture out to the haze ---
R("d = np.hypot(VF[:, 0], VF[:, 1])\nhz = ",
  "_zr = np.round(ZF * 2) / 2; _vals, _cnt = np.unique(_zr[ZF < np.percentile(ZF, 60)], return_counts=True); ZSEA = float(_vals[np.argmax(_cnt)])\n"
  "WV = (np.abs(ZF - ZSEA) < 1.0) & (slope < 0.004)\n"
  "from scipy import ndimage as _ndi\n"
  "WV = _ndi.binary_opening(WV, iterations=1); WV = _ndi.binary_fill_holes(WV) & (np.abs(ZF - ZSEA) < 2.0)\n"
  "_lab, _nl = _ndi.label(WV); _sz = np.bincount(_lab.ravel()); _keep = np.zeros(_nl + 1, bool); _keep[1:] = _sz[1:] >= 12; WV = _keep[_lab]\n"
  "_shore = WV & ~_ndi.binary_erosion(WV); _sand = ~WV & _ndi.binary_dilation(WV)\n"
  "vc = vc.copy(); vc[WV.ravel()] = lin((34, 58, 82))[:3]; vc[_shore.ravel()] = lin((60, 92, 110))[:3]; vc[_sand.ravel()] = lin((172, 164, 134))[:3]\n"
  "VF[WV.ravel(), 2] = ZSEA\n"
  "print('far water cells', int(WV.sum()), 'sea z', ZSEA)\n"
  "d = np.hypot(VF[:, 0], VF[:, 1])\nhz = ")
R("ob = mk_obj('bg_far_terrain', VF, FF.tolist(), mat_vcol('far', 0.95))\nlp = FF.ravel()\nset_corner_col(ob.data, np.concatenate([vc[lp], np.ones((len(lp), 1))], 1))\n",
  "_wf = WV.ravel()[FF].all(1); _fc = np.hypot((VF[FF[:, 0], 0] + VF[FF[:, 2], 0]) / 2, (VF[FF[:, 0], 1] + VF[FF[:, 2], 1]) / 2)\n"
  "_stf = (st.ravel()[FF].max(1) > 0.5)\n"
  "_sub = ~_wf & (_fc < 9000) & ~_stf\n"
  "for _nm, _sel, _mt in (('bg_far_water', _wf, mat_vcol('far_water', 0.12)), ('bg_far_suburb', _sub, mat_mul('far_suburb', os.path.join(HERE, 'tex', 'mt', 'far_suburb.png'), 0.9, 1 / float(open(os.path.join(HERE, 'tex', 'mt', 'far_suburb.mean')).read())))):\n"
  "    if _sel.any():\n"
  "        _F = FF[_sel]; _o = mk_obj(_nm, VF, _F.tolist(), _mt); _l = _F.ravel()\n"
  "        set_corner_col(_o.data, np.concatenate([vc[_l], np.ones((len(_l), 1))], 1)); set_uv(_o.data, np.stack([VF[_l, 0] / 250.0, VF[_l, 1] / 250.0], 1))\n"
  "FF = FF[~_wf & ~_sub]\n"
  "ob = mk_obj('bg_far_terrain', VF, FF.tolist(), mat_vcol('far', 0.95))\nlp = FF.ravel()\nset_corner_col(ob.data, np.concatenate([vc[lp], np.ones((len(lp), 1))], 1))\n")
open(p, 'w', newline='').write(t); print('patched')
