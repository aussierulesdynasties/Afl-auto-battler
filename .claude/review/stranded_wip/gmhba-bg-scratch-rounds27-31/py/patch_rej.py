import io
def sub(f, a, b):
    s = io.open(f, encoding='utf-8', newline='').read(); assert s.count(a) == 1, (f, a[:50]); io.open(f, 'w', encoding='utf-8', newline='').write(s.replace(a, b))
# prep: pedestrian areas are areas (filled paving), not a 6 m stroke round their outline
sub('prep.py', "        if wd:\n            col = PAL['path']",
 "        if wd and hw == 'pedestrian' and t.get('area') == 'yes' and len(pts) > 3:\n            dr.polygon(P(pts), fill=tuple(PAL['paved'])); wd = None\n        if wd:\n            col = PAL['path']")
# prep: big sheds (block >= 400 m2) take their roof colour from the satellite median inside the footprint
sub('prep.py', "json.dump(BLD, open(os.path.join(OUT, 'buildings.json'), 'w'))",
"""_SP = os.path.join(D, 'sat.png')
if os.path.exists(_SP):
    _sj = json.load(open(os.path.join(D, 'sat.json'))); _SA = np.asarray(Image.open(_SP).convert('RGB')); _hm, _mp = _sj['half_m'], _sj['m_per_px']
    for b in BLD:
        P_ = np.array(b['p']); A_ = 0.5 * abs(np.dot(P_[:, 0], np.roll(P_[:, 1], -1)) - np.dot(P_[:, 1], np.roll(P_[:, 0], -1)))
        if b['c'] != 'block' or A_ < 400: continue
        q = [((x + _hm) / _mp, (_hm - y) / _mp) for x, y in b['p']]
        x0, y0 = [int(min(v)) for v in zip(*q)]; x1, y1 = [int(max(v)) + 1 for v in zip(*q)]
        if x0 < 0 or y0 < 0 or x1 >= _SA.shape[1] or y1 >= _SA.shape[0]: continue
        mk = Image.new('L', (x1 - x0, y1 - y0)); ImageDraw.Draw(mk).polygon([(u - x0, v - y0) for u, v in q], fill=1)
        px = _SA[y0:y1, x0:x1][np.asarray(mk) > 0]
        if len(px) > 20: b['roof_c'] = [int(v) for v in np.median(px, 0)]
json.dump(BLD, open(os.path.join(OUT, 'buildings.json'), 'w'))""")
# scene: sat roof colour; sheds (block >= 400 m2, <= 10 m) clad in ribbed sheet; corrugated roofs multiply (not glass)
sub('scene.py', "        rc = roofs[b['roof'] % len(roofs)] * (1 + 0.08 * (rng.random() - 0.5))",
"        rc = lin(b['roof_c']) if b.get('roof_c') else roofs[b['roof'] % len(roofs)] * (1 + 0.08 * (rng.random() - 0.5))\n        shed = cls == 'block' and b['a'] >= 400 and h <= 10\n        V_, F_, C_, U_ = (CL if shed else (verts, faces, cols, uvs)); TW, TH = (4.0, 4.0) if shed else (tw, th)")
sub('scene.py', "        k = len(P); s0 = len(verts)\n        for x, y in P: verts.append((x, y, base))\n        for x, y in P: verts.append((x, y, top))",
"        k = len(P); s0 = len(V_)\n        for x, y in P: V_.append((x, y, base))\n        for x, y in P: V_.append((x, y, top))")
sub('scene.py', "            faces.append((s0 + i, s0 + j, s0 + k + j, s0 + k + i))\n            cols += [wc] * 4\n            u0, u1 = per / tw, (per + L) / tw\n            v0, v1 = -1.0 / th, (top - base - 1.0) / th\n            uvs += [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]",
"            F_.append((s0 + i, s0 + j, s0 + k + j, s0 + k + i))\n            C_ += [wc] * 4\n            u0, u1 = per / TW, (per + L) / TW\n            v0, v1 = -1.0 / TH, (top - base - 1.0) / TH\n            U_ += [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]")
sub('scene.py', "    roofs = [lin(c) for c in PAL['roofs_' + ('house' if cls == 'house' else 'flat')]]\n",
"    roofs = [lin(c) for c in PAL['roofs_' + ('house' if cls == 'house' else 'flat')]]\n    CL = [[], [], [], []]   # clad shed walls: verts, faces, cols, uvs\n")
sub('scene.py', "        if kind == 'metal' and cls == 'block' and b['a'] >= 400: kind, RT = 'corr', 7.2   # big white sheds: corrugated iron (256 px = 3.6 m)\n        if kind == 'corr' and b['a'] >= 1500: kind, RT = 'far', 24.0",
"        if kind == 'metal' and cls == 'block' and b['a'] >= 400: kind, RT = 'far', 12.0   # sheds: sheet runs along the long axis, multiplied (512 px = 12 m)\n        if kind == 'far' and b['a'] >= 1500: kind, RT = 'far', 24.0")
sub('scene.py', "    if not faces: return\n",
"    if CL[1]:\n        oc = mk_obj('bg_clad_' + cls, CL[0], CL[1], mat_mul('clad_' + cls, os.path.join(HERE, 'tex', 'mt', 'clad_rib.png'), 0.55, 1 / 0.455))\n        set_corner_col(oc.data, np.concatenate([np.array(CL[2]), np.ones((len(CL[2]), 1))], 1)); set_uv(oc.data, CL[3])\n    if not faces: return\n")
print('ok')
