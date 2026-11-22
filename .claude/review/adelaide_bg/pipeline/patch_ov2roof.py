import shutil, json
H = 'D:/Temp/claude/b012626c2f559e8f/6855d913-d54b-43b8-92a6-1e4e1b34589b/scratchpad/proto/'
def sub(fn, a, b):
    s = open(H + fn, newline='').read()
    if '\r\n' in s: a, b = a.replace('\n', '\r\n'), b.replace('\n', '\r\n')
    assert s.count(a) == 1, (fn, a[:60], s.count(a))
    open(H + fn, 'w', newline='').write(s.replace(a, b))
shutil.copy(H + 'scene.py', H + 'scene.py.bak_ov2roof'); shutil.copy(H + 'spec/adelaide.json', H + 'spec/adelaide.json.bak_ov2roof')
# Oval No.2: 60 m worn-patch multiplier over the 6 m grain, and the cricket square (sat: ~23 x 24 m at -205.7, 12.2, grey-brown)
a = "surf_obj('bg_oval2_skin', _SF['oval2'], mat_img('oval2_dirt', os.path.join(_TX, 'adl_dry_grain.png'), 0.95), 0.04, 6.0)"
sub('scene.py', a, a + "\n"
    "_om = bpy.data.materials.get('oval2_dirt')\n"
    "if _om:\n"
    "    _ont = _om.node_tree; _ob = _ont.nodes['Principled BSDF']; _src = _ob.inputs['Base Color'].links[0].from_socket\n"
    "    _pt = _ont.nodes.new('ShaderNodeTexImage'); _pt.image = bpy.data.images.load(os.path.join(_TX, 'adl_patch60.png')); _pt.image.colorspace_settings.name = 'Non-Color'\n"
    "    _mp = _ont.nodes.new('ShaderNodeMapping'); _mp.inputs['Scale'].default_value = (0.1, 0.1, 1); _tc = _ont.nodes.new('ShaderNodeUVMap')\n"
    "    _ont.links.new(_tc.outputs['UV'], _mp.inputs['Vector']); _ont.links.new(_mp.outputs['Vector'], _pt.inputs['Vector'])\n"
    "    _m1 = _ont.nodes.new('ShaderNodeMath'); _m1.operation = 'MULTIPLY'; _m1.inputs[1].default_value = 1.25; _ont.links.new(_pt.outputs['Color'], _m1.inputs[0])\n"
    "    _mx = _ont.nodes.new('ShaderNodeMix'); _mx.data_type = 'RGBA'; _mx.blend_type = 'MULTIPLY'; _mx.inputs[0].default_value = 1\n"
    "    _ont.links.new(_src, _mx.inputs[6]); _ont.links.new(_m1.outputs[0], _mx.inputs[7]); _ont.links.new(_mx.outputs[2], _ob.inputs['Base Color'])\n"
    "for _cx, _cy, _w, _h, _ang in spec.get('cricket_squares', []):   # square = grey-brown worked clay over the same grain\n"
    "    _ca, _sa = math.cos(math.radians(_ang)), math.sin(math.radians(_ang))\n"
    "    _q = [(_cx + _ca * a_ * _w / 2 - _sa * b_ * _h / 2, _cy + _sa * a_ * _w / 2 + _ca * b_ * _h / 2) for a_, b_ in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]\n"
    "    surf_obj('bg_cricket_square', {'v': _q, 't': [[0, 1, 2], [0, 2, 3]]}, mat_tint('cricket_square', os.path.join(_TX, 'adl_dry_grain.png'), (0.62, 0.62, 0.56), 0.9), 0.07, 6.0, seg=1.5)")
# roofs: roof_col_at [x, y, rgb, kind?, 'solar'?] -> roof kind override (e.g. 'tile' = terracotta tiles) and solar arrays as geometry
sub('scene.py', "        for _x, _y, _c in spec.get('roof_col_at', []):   # roof colour read off the aerial for named buildings\n"
    "            if math.hypot(cxy[0] - _x, cxy[1] - _y) < 25: rc = lin(_c)",
    "        _kov, _sol = None, False\n"
    "        for _e in spec.get('roof_col_at', []):   # roof colour read off the aerial for named buildings (+ optional kind, 'solar')\n"
    "            if math.hypot(cxy[0] - _e[0], cxy[1] - _e[1]) < 25: rc = lin(_e[2]); _kov = _e[3] if len(_e) > 3 else None; _sol = 'solar' in _e[4:]")
sub('scene.py', "        rv, rf, rcl, ruv = RF[kind]; r0 = len(rv)",
    "        if _kov: kind = _kov\n"
    "        if _sol: SOLAR.append((P.copy(), top, th_))\n"
    "        rv, rf, rcl, ruv = RF[kind]; r0 = len(rv)")
sub('scene.py', "for b in BL:\n    P = np.array(b['p']); x, y = P[:, 0], P[:, 1]",
    "SOLAR = []\nfor b in BL:\n    P = np.array(b['p']); x, y = P[:, 0], P[:, 1]")
sub('scene.py', "print('buildings built')",
    "def _solar_build():   # rows of 1.0 x 1.7 m panels on a 2.2 m grid along the roof's long side, 2.5 m clear of the roof edge, a walkway every 4th row\n"
    "    SV, SF, SU = [], [], []\n"
    "    for P, top, th_ in SOLAR:\n"
    "        ct, st = math.cos(th_), math.sin(th_); E = np.vstack([P, P[:1]])\n"
    "        U = P @ np.array([ct, st]); W = P @ np.array([-st, ct])\n"
    "        for i, u in enumerate(np.arange(U.min() + 2.5, U.max() - 2.5, 1.1)):\n"
    "            for j, w in enumerate(np.arange(W.min() + 2.5, W.max() - 2.5, 2.2)):\n"
    "                if j % 4 == 3: continue\n"
    "                x, y = u * ct - w * st, u * st + w * ct\n"
    "                c = False\n"
    "                for k in range(len(P)):\n"
    "                    (x1, y1), (x2, y2) = E[k], E[k + 1]\n"
    "                    if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c = not c\n"
    "                if not c: continue\n"
    "                d = min(np.hypot(*(np.array([x, y]) - (E[k] + np.clip(np.dot(np.array([x, y]) - E[k], E[k + 1] - E[k]) / max(1e-6, np.dot(E[k + 1] - E[k], E[k + 1] - E[k])), 0, 1) * (E[k + 1] - E[k])))) for k in range(len(P)))\n"
    "                if d < 2.5: continue\n"
    "                n0 = len(SV)\n"
    "                for a_, b_ in [(-0.5, -0.85), (0.5, -0.85), (0.5, 0.85), (-0.5, 0.85)]:\n"
    "                    SV.append((x + a_ * ct - b_ * st, y + a_ * st + b_ * ct, top + 0.18 + 0.12 * (b_ > 0)))\n"
    "                SF.append([n0, n0 + 1, n0 + 2, n0 + 3]); SU += [(0, 0), (1, 0), (1, 1), (0, 1)]\n"
    "    if SF:\n"
    "        o = mk_obj('bg_solar', SV, SF, mat_img('solar', os.path.join(HERE, 'tex', 'adl_solar.png'), 0.25)); set_uv(o.data, SU); print('solar panels', len(SF))\n"
    "_solar_build()\nprint('buildings built')")
s = json.load(open(H + 'spec/adelaide.json'))
s['roof_col_at'] = [[-121, -197, [150, 82, 70], 'tile', 'solar'], [-32, -207, [196, 196, 190]]]
s['cricket_squares'] = [[-205.7, 12.2, 23.0, 24.0, 0.0]]
json.dump(s, open(H + 'spec/adelaide.json', 'w'), indent=1)
print('ok')
