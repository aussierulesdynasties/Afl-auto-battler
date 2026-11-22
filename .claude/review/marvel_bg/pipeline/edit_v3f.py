"""Towers: tw_* families with a fixed real palette (OSM wall colours ignored); big blocks too. Plaza paving 12 m tile.
Planters and grass strips on paved ground within 450 m of the stadium."""
import json, shutil
def sub(path, pairs):
    shutil.copy(path, path + '.bak_v3f'); s = open(path, newline='').read(); nl = '\r\n' if '\r\n' in s else '\n'
    for a, b in pairs:
        a = a.replace('\n', nl); b = b.replace('\n', nl); assert s.count(a) == 1, (path, a[:60]); s = s.replace(a, b)
    open(path, 'w', newline='').write(s)
sub('facade_mix.py', [
 ("    b['wc'] = c or WCOL[fam_c][int(r2 * 997) % len(WCOL[fam_c])]\n",
  "    b['wc'] = c or WCOL[fam_c][int(r2 * 997) % len(WCOL[fam_c])]\n"
  "    if f != 'carpark' and (b['c'] == 'tower' or h >= 25):   # v3f: towers and big blocks: one big readable feature, real palette\n"
  "        tf = _pick(r2, [(0.17, 'tw_bluegreen'), (0.17, 'tw_charcoal'), (0.14, 'tw_bronze'), (0.14, 'tw_curtain'), (0.13, 'tw_sandstone'), (0.13, 'tw_white'), (0.12, 'tw_fins')])\n"
  "        b['fam'] = tf; b['wc'] = TWC[tf][int(r * 997) % len(TWC[tf])]\n"),
 ("NAMED = {", "TWC = {'tw_bluegreen': [(72, 78, 82), (150, 148, 142)], 'tw_charcoal': [(52, 54, 58), (120, 118, 114)], 'tw_bronze': [(84, 70, 58), (160, 140, 112)],\n"
  "       'tw_curtain': [(60, 70, 84), (90, 96, 104)], 'tw_sandstone': [(198, 170, 126), (182, 152, 112), (206, 184, 146)], 'tw_white': [(228, 226, 220), (214, 212, 206)],\n"
  "       'tw_fins': [(232, 232, 228), (150, 156, 162), (196, 176, 140)]}\nNAMED = {"),
])
sub('scene.py', [
 ("print('buildings built')\n",
  "print('buildings built')\n"
  "# v3f planters + grass strips on paved ground near the stadium (pave mask), 26 m jittered grid\n"
  "if os.path.exists(_pm):\n"
  "    _mi = bpy.data.images.load(_pm); _mw, _mh = _mi.size; _MP = np.array(_mi.pixels[:], np.float32).reshape(_mh, _mw, 4)[..., 0]\n"
  "    _BB = [np.array(b_['p'], float) for b_ in BL]; _BC = np.array([p_.mean(0) for p_ in _BB]); _BR = np.array([np.hypot(*(p_ - p_.mean(0)).T).max() for p_ in _BB])\n"
  "    PV, PF, PC = [], [], []; _rg = np.random.default_rng(9)\n"
  "    for gx in np.arange(-450, 450, 26.0):\n"
  "        for gy in np.arange(-450, 450, 26.0):\n"
  "            x, y = gx + _rg.uniform(-8, 8), gy + _rg.uniform(-8, 8)\n"
  "            if np.hypot(x, y) < 150 or np.hypot(x, y) > 450: continue\n"
  "            ix, iy = int((x + NE) / (2 * NE) * _mw), int((y + NE) / (2 * NE) * _mh)\n"
  "            if _MP[iy, ix] < 0.5 or (np.hypot(*(_BC - (x, y)).T) < _BR + 4).any(): continue\n"
  "            grass = _rg.random() < 0.5; sx_, sy_, sz_ = (1.6, 14.0, 0.15) if grass else (2.2, 5.0, 0.6)\n"
  "            a_ = _rg.choice([0, math.pi / 2]) + _rg.uniform(-0.05, 0.05); ca_, sa_ = math.cos(a_), math.sin(a_); z0 = float(height(x, y)); s0 = len(PV)\n"
  "            for zz in (z0 - 0.2, z0 + sz_):\n"
  "                for u_, v_ in ((-1, -1), (1, -1), (1, 1), (-1, 1)): PV.append((x + ca_ * u_ * sx_ / 2 - sa_ * v_ * sy_ / 2, y + sa_ * u_ * sx_ / 2 + ca_ * v_ * sy_ / 2, zz))\n"
  "            side = lin((80, 104, 56)) if grass else lin((170, 164, 152)); top = lin((86, 118, 58)) if grass else lin((70, 96, 52))\n"
  "            for f_ in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)): PF.append(tuple(s0 + i for i in f_)); PC.extend([side] * 4)\n"
  "            PF.append(tuple(s0 + i for i in (4, 5, 6, 7))); PC.extend([top] * 4)\n"
  "    if PF:\n"
  "        ob = mk_obj('bg_planters', PV, PF, mat_vcol('planters', 0.85)); set_corner_col(ob.data, np.concatenate([np.array(PC), np.ones((len(PC), 1))], 1))\n"
  "    print('planters', len(PF) // 5)\n"),
])
s = json.load(open('spec/marvel.json')); s['pave_tex'] = ['v3_plaza.png', 12.0]; json.dump(s, open('spec/marvel.json', 'w'), indent=1); print('ok')
