"""Marvel rejection 2026-11-20 ("the train tracks and the buildings are hideous"), relayed by the plan session:
- each building gets its own facade family (dark/teal/bronze/grey glass, concrete, brick, panels, cladding, carpark)
  from its OSM kind/material/colour, its own wall colour, and rooftop plant on flat roofs;
- rail yard: textured 3.2 m bed (ballast, sleepers, rails), steel rails lifted, overhead wire masts, platforms;
- Southern Cross station: undulating wave roof on its footprint, glass sides."""
import json
P = 'scene.py'; s = open(P, newline='').read(); nl = '\r\n' if '\r\n' in s else '\n'
def rep(a, b):
    global s
    a = a.replace('\n', nl); b = b.replace('\n', nl); assert s.count(a) == 1, a[:70]; s = s.replace(a, b)

# ---- rails: textured bed in its own mesh, rails lifted, masts ----
rep("    def drape_strip(P, off, w, lift, c):\n",
    "    BV, BF, BC, BU = [], [], [], []; MV, MF, MC = [], [], []\n"
    "    def drape_strip(P, off, w, lift, c, uvL=None):\n")
rep("        for i in range(n - 1):\n            faces.append((s0 + 2 * i, s0 + 2 * i + 1, s0 + 2 * i + 3, s0 + 2 * i + 2)); cols.extend([c] * 4)\n",
    "        sd_ = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])\n"
    "        for i in range(n - 1):\n            faces.append((s0 + 2 * i, s0 + 2 * i + 1, s0 + 2 * i + 3, s0 + 2 * i + 2)); cols.extend([c] * 4)\n"
    "            if uvL: BU.extend([(0, sd_[i] / uvL), (1, sd_[i] / uvL), (1, sd_[i + 1] / uvL), (0, sd_[i + 1] / uvL)])\n"
    "        return C, N_, zc\n")
rep("        for Q in segs:\n            drape_strip(Q, 0, 2.8, 0.2, bed_c)\n            for sd in (-0.8, 0.8): drape_strip(Q, sd, 0.18, 0.32, steel_c)\n        continue\n",
    "        ALLSEG.extend(segs)\n        continue\n")
rep("    for pts in json.load(open(RLP)):\n        P = np.array(pts, float); Q = [P[0]]\n",
    "    ALLSEG = []\n    for pts in json.load(open(RLP)):\n        P = np.array(pts, float); Q = [P[0]]\n")
rep("    if faces:\n        ob = mk_obj('bg_rails', verts, faces, mat_vcol('rails', 0.6))\n",
    "    _HG = {}   # 2 m grid of every track centreline point: masts never stand on a neighbouring track\n"
    "    for si, Q in enumerate(ALLSEG):\n"
    "        for q in Q: _HG.setdefault((int(q[0] // 2), int(q[1] // 2)), []).append((si, q))\n"
    "    def _clear(p, si):\n"
    "        gx, gy = int(p[0] // 2), int(p[1] // 2)\n"
    "        for dx in (-2, -1, 0, 1, 2):\n"
    "            for dy in (-2, -1, 0, 1, 2):\n"
    "                for sj, q in _HG.get((gx + dx, gy + dy), []):\n"
    "                    if sj != si and np.hypot(*(q - p)) < 2.3: return False\n"
    "        return True\n"
    "    def mbox(cx, cy, z0, sx, sy, sz, ang, c):\n"
    "        ca_, sa_ = math.cos(ang), math.sin(ang); s0 = len(MV)\n"
    "        for zz in (z0, z0 + sz):\n"
    "            for u_, v_ in ((-1, -1), (1, -1), (1, 1), (-1, 1)):\n"
    "                MV.append((cx + ca_ * u_ * sx / 2 - sa_ * v_ * sy / 2, cy + sa_ * u_ * sx / 2 + ca_ * v_ * sy / 2, zz))\n"
    "        for f_ in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)):\n"
    "            MF.append(tuple(s0 + i for i in f_)); MC.extend([c] * 4)\n"
    "    mast_c = lin((150, 152, 150)); sp_ = spec.get('mast_m', 60.0)\n"
    "    for si, Q in enumerate(ALLSEG):\n"
    "        verts, faces, cols = BV, BF, BC\n"
    "        C_, N_, zc_ = drape_strip(Q, 0, 3.2, 0.12, bed_c, uvL=2.6)\n"
    "        verts, faces, cols = RV, RF_, RC\n"
    "        for sd in (-0.8, 0.8): drape_strip(Q, sd, 0.12, 0.3, steel_c)\n"
    "        sd_ = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])\n"
    "        for d_ in np.arange(sp_ / 2 + (si * 17) % 23, sd_[-1], sp_):\n"
    "            i = int(np.searchsorted(sd_, d_)); i = min(i, len(Q) - 1)\n"
    "            for side in (1, -1):\n"
    "                p = C_[i] + N_[i] * 2.7 * side\n"
    "                if _clear(p, si):\n"
    "                    ang = math.atan2(N_[i][1], N_[i][0]); z = float(zc_[i])\n"
    "                    mbox(p[0], p[1], z, 0.35, 0.35, 7.6, ang, mast_c)\n"
    "                    a0 = C_[i] + N_[i] * 0.9 * side; mid = (p + a0) / 2\n"
    "                    mbox(mid[0], mid[1], z + 6.9, 1.8, 0.14, 0.14, ang, mast_c)\n"
    "                    break\n"
    "    if BF:\n"
    "        ob = mk_obj('bg_rail_bed', BV, BF, mat_img('rail_bed', os.path.join(HERE, 'tex', 'rail_bed.png'), 0.95)); set_uv(ob.data, BU)\n"
    "    if MF:\n"
    "        ob = mk_obj('bg_rail_masts', MV, MF, mat_vcol('rail_masts', 0.5))\n"
    "        set_corner_col(ob.data, np.concatenate([np.array(MC), np.ones((len(MC), 1))], 1))\n"
    "    verts, faces, cols = RV, RF_, RC\n"
    "    if faces:\n        ob = mk_obj('bg_rails', verts, faces, mat_vcol('rails', 0.6))\n")
rep("    bed_c = lin(tuple(PAL.get('track', (70, 64, 60)))); steel_c = lin((168, 170, 172))\n",
    "    bed_c = lin(tuple(PAL.get('track', (70, 64, 60)))); steel_c = lin((150, 150, 152))\n    RV, RF_, RC = [], [], []\n")

# ---- buildings: per-building facade family, own colour, rooftop plant ----
rep("        wc = walls[b['wall'] % len(walls)] * (1 + 0.06 * (rng.random() - 0.5))\n",
    "        wc = (lin(b['wc']) if 'wc' in b else walls[b['wall'] % len(walls)]) * (1 + 0.06 * (rng.random() - 0.5))\n")
rep("        else:\n            rf.append(tuple(r0 + i for i in range(k))); rcl += [rc] * k\n",
    "        else:\n            rf.append(tuple(r0 + i for i in range(k))); rcl += [rc] * k\n"
    "            if spec.get('roof_plant') and cls in ('block', 'tower') and 'rc' not in b and b.get('fam') != 'carpark' and b.get('a', 0) >= 150:\n"
    "                roof_plant(P, cxy, top, th_, cls == 'tower', b['a'])\n")
rep("# ---------- buildings ----------\n",
    "# ---------- buildings ----------\n"
    "PL = [[], [], [], []]   # rooftop plant: verts, faces, cols, uvs\n"
    "def roof_plant(P, cxy, top, ang, tower, A):\n"
    "    ca_, sa_ = math.cos(ang), math.sin(ang)\n"
    "    boxes = [(cxy[0], cxy[1], 7.0, 6.0, 4.2)] if tower else []   # lift overrun\n"
    "    for _ in range(min(4, 1 + int(A / 700))):\n"
    "        q = P[int(rng.integers(0, len(P)))]; f = rng.uniform(0.15, 0.45); c_ = cxy + (q - cxy) * f\n"
    "        boxes.append((c_[0], c_[1], rng.uniform(2.5, 6.5), rng.uniform(2.0, 5.0), rng.uniform(1.6, 3.2)))\n"
    "    for cx, cy, sx, sy, sz in boxes:\n"
    "        c = lin([(196, 198, 196), (150, 152, 152), (118, 120, 122), (212, 210, 204)][int(rng.integers(0, 4))])\n"
    "        V, F, C, U = PL; s0 = len(V)\n"
    "        for zz in (top, top + sz):\n"
    "            for u_, v_ in ((-1, -1), (1, -1), (1, 1), (-1, 1)):\n"
    "                V.append((cx + ca_ * u_ * sx / 2 - sa_ * v_ * sy / 2, cy + sa_ * u_ * sx / 2 + ca_ * v_ * sy / 2, zz))\n"
    "        for f_, w_ in (((0, 1, 5, 4), sx), ((1, 2, 6, 5), sy), ((2, 3, 7, 6), sx), ((3, 0, 4, 7), sy), ((4, 5, 6, 7), 0)):\n"
    "            F.append(tuple(s0 + i for i in f_)); C.extend([c] * 4)\n"
    "            U.extend([(0, 0), (w_ / 3, 0), (w_ / 3, sz / 3), (0, sz / 3)] if w_ else [(0.02, 0.02)] * 4)\n")
rep("print('buildings built')\n",
    "if PL[1]:\n"
    "    ob = mk_obj('bg_roof_plant', PL[0], PL[1], mat_facade('roof_plant', os.path.join(HERE, 'tex', 'fc_plant.png')))\n"
    "    set_corner_col(ob.data, np.concatenate([np.array(PL[2]), np.ones((len(PL[2]), 1))], 1)); set_uv(ob.data, PL[3])\n"
    "print('buildings built')\n")
rep("build_class('house', 'wall.png', 3.6, 3.2)\nif 'block_tex' in spec:\n",
    "build_class('house', 'wall.png', 3.6, 3.2)\n"
    "if spec.get('facade_mix'):\n"
    "    exec(open(os.path.join(HERE, 'facade_mix.py'), encoding='utf-8').read())\n"
    "elif 'block_tex' in spec:\n")
rep("_FAR = spec.get('tower_far_m', 1e9)\ndef _d(b): return float(np.hypot(*np.array(b['p'], float).mean(0)))\nbuild_class('tower',",
    "_FAR = spec.get('tower_far_m', 1e9)\ndef _d(b): return float(np.hypot(*np.array(b['p'], float).mean(0)))\nif not spec.get('facade_mix'): build_class('tower',")
rep("if 'tower_far_tex' in spec: build_class(", "if 'tower_far_tex' in spec and not spec.get('facade_mix'): build_class(")
open(P, 'w', newline='').write(s)

J = json.load(open('spec/marvel.json'))
J['facade_mix'] = True; J['roof_plant'] = True; J['mast_m'] = 60.0; J['ballast_track_m'] = 4.0
J['palette']['ballast'] = [100, 92, 84]; J['palette']['ballast_track'] = [72, 66, 60]
J['palette']['roofs_flat'] = [[219, 222, 217], [138, 138, 135], [160, 158, 150], [98, 100, 102], [178, 170, 152], [120, 124, 118]]
json.dump(J, open('spec/marvel.json', 'w'), indent=1); print('ok')
