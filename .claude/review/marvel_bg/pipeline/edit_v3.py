"""v3 code edits (texture session FAIL 2026-11-20): facade families, podium storey, parapets, roof kinds
(membrane / shed ribs / car-park deck), wider rail bed, kerbs + lane lines, paving everywhere default ground shows."""
import json, shutil
def sub(path, pairs):
    shutil.copy(path, path + '.bak_v3')
    s = open(path, newline='').read(); nl = '\r\n' if '\r\n' in s else '\n'
    for a, b in pairs:
        a = a.replace('\n', nl); b = b.replace('\n', nl)
        assert s.count(a) == 1, (path, a[:70]); s = s.replace(a, b)
    open(path, 'w', newline='').write(s)

sub('facade_mix.py', [
 (" 'panel': [(204, 120, 62), (86, 108, 138), (224, 222, 216), (70, 70, 72),",
  " 'banded': [(186, 180, 168), (150, 146, 138), (204, 196, 180), (132, 128, 122), (172, 160, 140)],\n 'panel': [(204, 120, 62), (86, 108, 138), (150, 152, 150), (70, 70, 72),"),
 (" 'glass': [(44, 46, 50), (70, 74, 80), (36, 36, 38), (92, 96, 102)],",
  " 'glass': [(44, 46, 50), (70, 74, 80), (36, 36, 38), (92, 96, 102), (110, 96, 80), (60, 72, 84), (128, 124, 116), (84, 60, 52)],"),
 ("GLASS = [(1.0 / 16, f_) for f_ in ['glass_dark', 'glass_teal', 'glass_bronze', 'glass_grey'] + ['glass_' + t + '_' + l for t in ['navy', 'slate', 'green', 'blue', 'smoke', 'silver'] for l in 'ab']]",
  "_GL = sorted(f_ for f_ in FCS if f_.startswith('glass_')); GLASS = [(1.0 / len(_GL), f_) for f_ in _GL]\nBANDED = [(1.0 / 3, 'banded_' + l) for l in 'abc']"),
 ("elif b['c'] == 'tower': f = _pick(r, [(0.66, None), (0.22, 'panel'), (0.12, 'concrete')]) or _pick(r2, GLASS)",
  "elif b['c'] == 'tower': f = _pick(r, [(0.5, None), (0.22, 'B'), (0.14, 'panel'), (0.14, 'concrete')]) or _pick(r2, GLASS)"),
 ("_pick(r, [(0.2, 'glass_grey'), (0.1, 'glass_dark'), (0.35, 'concrete'), (0.35, 'panel')])",
  "(_pick(r, [(0.3, None), (0.25, 'B'), (0.25, 'concrete'), (0.2, 'panel')]) or _pick(r2, GLASS))"),
 ("    b['fam'] = f\n    fam_c = 'glass' if f.startswith('glass') else f",
  "    if f == 'B': f = _pick(r2, BANDED)\n    b['fam'] = f\n    fam_c = 'glass' if f.startswith('glass') else 'banded' if f.startswith('banded') else f"),
 ("        if f in ('plant', 'rail_bed'): continue", "        if f in ('plant', 'rail_bed', 'parapet'): continue"),
])

sub('scene.py', [
 # roof kinds
 ("    RF = {'metal': [[], [], [], []], 'tile': [[], [], [], []], 'big': [[], [], [], []]}",
  "    RF = {k_: [[], [], [], []] for k_ in ('metal', 'tile', 'big', 'shed', 'deck')}"),
 ("        if not pitched and (cls == 'tower' or b.get('a', 0) >= spec.get('roof_big_m2', 1e12)): kind = 'big'\n        rs = spec.get('roof_big_m', 24.0) if kind == 'big' else 3.04",
  "        if not pitched and (cls == 'tower' or b.get('a', 0) >= spec.get('roof_big_m2', 1e12)): kind = 'big'\n"
  "        if cls == 'block' and (b.get('fam') == 'cladding' or 'rc' in b): kind = 'shed'\n"
  "        if b.get('fam') == 'carpark': kind = 'deck'\n"
  "        rs = {'big': 24.0, 'shed': 24.0, 'deck': 32.0}.get(kind, 3.04)"),
 ("os.path.join(HERE, 'tex', 'roof_%s.png' % {'metal': 'corrugated', 'big': 'far'}.get(kind, kind))",
  "os.path.join(HERE, 'tex', 'roof_%s.png' % {'metal': 'corrugated', 'big': 'membrane'}.get(kind, kind))"),
 # podium: bottom storey darker on blocks/towers >= 12 m
 ("            faces.append((s0 + i, s0 + j, s0 + k + j, s0 + k + i))\n            cols += [wc] * 4\n            u0, u1 = per / tw, (per + L) / tw\n            v0, v1 = -1.0 / th, (top - base - 1.0) / th\n            uvs += [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]",
  "            u0, u1 = per / tw, (per + L) / tw\n"
  "            v0, v1 = -1.0 / th, (top - base - 1.0) / th\n"
  "            if s0p is not None:   # podium storey: own quad, darker\n"
  "                vp = (zp - base - 1.0) / th\n"
  "                faces.append((s0 + i, s0 + j, s0p + j, s0p + i)); cols += [wc * 0.5] * 4; uvs += [(u0, v0), (u1, v0), (u1, vp), (u0, vp)]\n"
  "                faces.append((s0p + i, s0p + j, s0 + k + j, s0 + k + i)); cols += [wc] * 4; uvs += [(u0, vp), (u1, vp), (u1, v1), (u0, v1)]\n"
  "            else:\n"
  "                faces.append((s0 + i, s0 + j, s0 + k + j, s0 + k + i)); cols += [wc] * 4; uvs += [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]"),
 ("        for x, y in P: verts.append((x, y, top))\n        per = 0.0",
  "        for x, y in P: verts.append((x, y, top))\n"
  "        s0p = None\n"
  "        if cls in ('block', 'tower') and h >= 12 and b.get('fam') not in (None, 'carpark', 'cladding'):\n"
  "            zp = base + 1.0 + min(5.0, 0.3 * h); s0p = len(verts)\n"
  "            for x, y in P: verts.append((x, y, zp))\n"
  "        per = 0.0"),
 # parapet ring on flat roofs of blocks and towers
 ("            rf.append(tuple(r0 + i for i in range(k))); rcl += [rc] * k\n",
  "            rf.append(tuple(r0 + i for i in range(k))); rcl += [rc] * k\n"
  "            if cls in ('block', 'tower') and kind != 'shed': parapet(P, cxy, top, wc * 0.85)\n"),
 ("PL = [[], [], [], []]   # rooftop plant: verts, faces, cols, uvs\n",
  "PL = [[], [], [], []]   # rooftop plant: verts, faces, cols, uvs\n"
  "PP = [[], [], [], []]   # parapets: verts, faces, cols, uvs\n"
  "def parapet(P, cxy, top, c, hp=1.1, t=0.3):\n"
  "    V, F, C, U = PP; k = len(P); d = np.maximum(np.hypot(*(P - cxy).T), t + 0.5)[:, None]\n"
  "    Q = cxy + (P - cxy) * (1 - t / d); s0 = len(V); per = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(np.vstack([P, P[:1]]), axis=0).T))])\n"
  "    for ring, z in ((P, top - 0.2), (P, top + hp), (Q, top + hp), (Q, top - 0.2)):\n"
  "        for x, y in ring: V.append((x, y, z))\n"
  "    for i in range(k):\n"
  "        j = (i + 1) % k; ua, ub = per[i] / 6.0, per[i + 1] / 6.0\n"
  "        for r_, (va, vb) in enumerate(((0, 1.1), (1.1, 1.2), (1.1, 0))):\n"
  "            F.append((s0 + r_ * k + i, s0 + r_ * k + j, s0 + (r_ + 1) * k + j, s0 + (r_ + 1) * k + i)); C.extend([c] * 4)\n"
  "            U.extend([(ua, va / 1.2), (ub, va / 1.2), (ub, vb / 1.2), (ua, vb / 1.2)])\n"),
 ("    set_corner_col(ob.data, np.concatenate([np.array(PL[2]), np.ones((len(PL[2]), 1))], 1)); set_uv(ob.data, PL[3])\n",
  "    set_corner_col(ob.data, np.concatenate([np.array(PL[2]), np.ones((len(PL[2]), 1))], 1)); set_uv(ob.data, PL[3])\n"
  "if PP[1]:\n"
  "    ob = mk_obj('bg_parapets', PP[0], PP[1], mat_facade('parapet', os.path.join(HERE, 'tex', 'fc_parapet.png')))\n"
  "    set_corner_col(ob.data, np.concatenate([np.array(PP[2]), np.ones((len(PP[2]), 1))], 1)); set_uv(ob.data, PP[3])\n"),
 # rail bed: 4.4 m wide (tile 4.4 m)
 ("        C_, N_, zc_ = drape_strip(Q, 0, 3.2, 0.12, bed_c, uvL=2.6)", "        C_, N_, zc_ = drape_strip(Q, 0, 4.4, 0.12, bed_c, uvL=2.6)"),
])

sub('roads_pf.py', [
 ("    RV, RF_, LV, LF = [], [], [], []; DK = []", "    RV, RF_, LV, LF = [], [], [], []; DK = []; KV, KF = [], []"),
 ("        if SERV[ri]: DK.append((_v0, len(RV)))\n        if not two: continue\n        Ql = _dens(Q, 0.5)",
  "        if SERV[ri]: DK.append((_v0, len(RV)))\n"
  "        if SERV[ri]: continue\n"
  "        for sd in (-1, 1):   # kerb and gutter: 0.35 m light concrete strip at each edge\n"
  "            for r in _runs(ok): _ribbon(Q[r], sd * (w / 2 + 0.1), 0.35, 0.12, KV, KF)\n"
  "        Ql = _dens(Q, 0.5)"),
 ("        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Ql, axis=0).T))])   # centre: 3 m dash, 9 m gap\n        for r in _runs(okl & ((s % 12.0) < 3.0)): _ribbon(Ql[r], 0, 0.10, 0.06, LV, LF)",
  "        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Ql, axis=0).T))])   # centre: 3 m dash, 9 m gap\n"
  "        if two:\n"
  "            for r in _runs(okl & ((s % 12.0) < 3.0)): _ribbon(Ql[r], 0, 0.10, 0.06, LV, LF)\n"
  "        else:   # multi-lane: 3.5 m lanes, dashed lane lines between them\n"
  "            nl_ = max(2, int(round((w - 1.0) / 3.5)))\n"
  "            for li in range(1, nl_):\n"
  "                for r in _runs(okl & ((s % 12.0) < 3.0)): _ribbon(Ql[r], -w / 2 + 0.5 + li * (w - 1.0) / nl_, 0.10, 0.06, LV, LF)"),
 ("        ob = mk_obj('bg_road_lines', LV, LF, m_line); set_corner_col(ob.data, np.tile(LC, (len(LF) * 4, 1)))",
  "        ob = mk_obj('bg_road_lines', LV, LF, m_line); set_corner_col(ob.data, np.tile(LC, (len(LF) * 4, 1)))\n"
  "    if KF:\n"
  "        ob = mk_obj('bg_kerbs', KV, KF, m_line); set_corner_col(ob.data, np.tile(list(lin((168, 164, 156))) + [1.0], (len(KF) * 4, 1)))"),
])

sub('mk_pave_mask.py', [("m|=dflt&inside", "m|=dflt   # v3: paving wherever default ground shows (texture session: no flat grey fills)")])
s = json.load(open('spec/marvel.json')); shutil.copy('spec/marvel.json', 'spec/marvel.json.bak_v3')
s['palette']['ballast'] = [128, 120, 108]; s['palette']['ballast_track'] = [62, 57, 52]; s['ballast_track_m'] = 5.0
json.dump(s, open('spec/marvel.json', 'w'), indent=1); print('ok')
