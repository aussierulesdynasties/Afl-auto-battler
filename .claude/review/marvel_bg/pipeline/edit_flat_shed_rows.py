"""Director 2026-11-20: flatten land within flat_r_m to boardwalk (water + 2 m); untagged buildings < 100 m2 = 4 m shed,
dark grey roof; Norfolk pines = one row per kerb, 12 m apart (replacing every tree within 12 m of the street)."""
def patch(P, pairs):
    s = open(P, newline='').read(); nl = '\r\n' if '\r\n' in s else '\n'
    for a, b in pairs:
        a = a.replace('\n', nl); b = b.replace('\n', nl)
        assert s.count(a) == 1, (P, a[:60], s.count(a)); s = s.replace(a, b)
    open(P, 'w', newline='').write(s)

patch('prep.py', [(
"    cls = 'tower' if h >= 25 else ('house' if (A < 350 and h < 9) else 'block')\n",
"    cls = 'tower' if h >= 25 else ('house' if (A < 350 and h < 9) else 'block')\n"
"    shed = untagged and A < spec.get('shed_max_m2', 0)\n"
"    if shed: h, cls = 4.0, 'block'   # untagged small building: single-storey shed\n"), (
"    if h is None: h = LV.get(kind, LV['*'])\n",
"    untagged = h is None\n    if h is None: h = LV.get(kind, LV['*'])\n"), (
"                    wall=int(rng.integers(0, len(PAL['walls_' + cls])))))\n",
"                    wall=int(rng.integers(0, len(PAL['walls_' + cls])))))\n"
"    if shed: BLD[-1]['rc'] = spec['shed_roof']\n")])

patch('scene.py', [(
"        rc = roofs[b['roof'] % len(roofs)] * (1 + 0.08 * (rng.random() - 0.5))\n",
"        rc = roofs[b['roof'] % len(roofs)] * (1 + 0.08 * (rng.random() - 0.5))\n"
"        if 'rc' in b: rc = lin(b['rc'])\n"), (
"NE, NS, FA, FS = meta['near'], meta['near_step'], meta['far'], meta['far_step']\n",
"NE, NS, FA, FS = meta['near'], meta['near_step'], meta['far'], meta['far_step']\n"
"if spec.get('flat_r_m') and spec.get('water_z_m') is not None:   # flat reclaimed land: level at boardwalk height\n"
"    _g = np.arange(near.shape[0]) * NS - NE; _X, _Y = np.meshgrid(_g, _g)\n"
"    near[np.hypot(_X, _Y) < spec['flat_r_m']] = spec['water_z_m'] + 2.0\n"), (
"    for row in TR:\n        if _dseg(row[0], row[1]) < spec.get('pine_dist_m', 12): row[2] = _k; _np += 1\n",
"    TR = TR[np.array([_dseg(r_[0], r_[1]) >= spec.get('pine_dist_m', 12) for r_ in TR], bool)]   # clear the street\n"
"    _new = []; _off = spec.get('pine_kerb_m', 8.0); _sp = spec.get('pine_space_m', 12.0)\n"
"    for (ax, ay), (bx, by) in _segs:\n"
"        Lg = math.hypot(bx - ax, by - ay)\n"
"        if Lg < 1: continue\n"
"        ux, uy = (bx - ax) / Lg, (by - ay) / Lg\n"
"        for t_ in np.arange(_sp / 2, Lg, _sp):\n"
"            for sd in (-1, 1):\n"
"                px, py = ax + ux * t_ - uy * _off * sd, ay + uy * t_ + ux * _off * sd\n"
"                if math.hypot(px, py) < 700 and abs(px) < NE - NS and abs(py) < NE - NS:\n"
"                    i_, j_ = int(round((px + NE) / NS)), int(round((py + NE) / NS))\n"
"                    if WZ is None or not WG[j_, i_]: _new.append([px, py, _k])\n"
"    if _new: TR = np.concatenate([TR, np.array(_new, float)]); _np = len(_new)\n")])
print('ok')
