"""Fix two self-check faults: (1) Harbour Esplanade is split into several parallel OSM ways, so 'one row each side'
came out as 4+ rows: keep only pines at least kerb-1 m from every street line, and one pine per 6 m.
(2) The bank ramp shows as pale wedges: add a vertical quay wall on every water/land cell edge, water-1 m to water+2 m."""
P = 'scene.py'
s = open(P, newline='').read(); nl = '\r\n' if '\r\n' in s else '\n'
def rep(a, b):
    global s
    a = a.replace('\n', nl); b = b.replace('\n', nl); assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
rep("    if _new: TR = np.concatenate([TR, np.array(_new, float)]); _np = len(_new)\n",
    "    _new = [p_ for p_ in _new if _dseg(p_[0], p_[1]) >= _off - 1.0]   # outer kerbs only (street drawn as several ways)\n"
    "    _keep = []\n"
    "    for p_ in _new:\n"
    "        if all(math.hypot(p_[0] - q_[0], p_[1] - q_[1]) >= 6.0 for q_ in _keep): _keep.append(p_)\n"
    "    _new = _keep\n"
    "    if _new: TR = np.concatenate([TR, np.array(_new, float)]); _np = len(_new)\n")
rep("    print('water cells', len(wf), 'z', WZ)\n",
    "    print('water cells', len(wf), 'z', WZ)\n"
    "    qv = []; qf = []; quv = []\n"
    "    for j, i in _ix:\n"
    "        cx, cy = i * NS - NE, j * NS - NE; h_ = NS / 2\n"
    "        for dj, di, (ax, ay, bx, by) in ((0, 1, (cx + h_, cy - h_, cx + h_, cy + h_)), (0, -1, (cx - h_, cy + h_, cx - h_, cy - h_)),\n"
    "                                         (1, 0, (cx + h_, cy + h_, cx - h_, cy + h_)), (-1, 0, (cx - h_, cy - h_, cx + h_, cy - h_))):\n"
    "            jj, ii = j + dj, i + di\n"
    "            if 0 <= jj < n and 0 <= ii < n and not WG[jj, ii]:\n"
    "                o = len(qv); qv += [(ax, ay, WZ - 1), (bx, by, WZ - 1), (bx, by, WZ + 2), (ax, ay, WZ + 2)]; qf.append((o, o + 1, o + 2, o + 3))\n"
    "                quv += [(0, 0), (NS / 4, 0), (NS / 4, 0.75), (0, 0.75)]\n"
    "    if qf:\n"
    "        qob = mk_obj('bg_quay', qv, qf, mat_img('quay', os.path.join(HERE, 'tex', 'wall.png'), 0.9))\n"
    "        set_uv(qob.data, np.array(quv, float)); print('quay faces', len(qf))\n")
open(P, 'w', newline='').write(s); print('ok')
