import json
s = open('scene.py', encoding='utf-8', newline='').read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:60], s.count(a)); s = s.replace(a, b)
# 5 far land: hand-made farmland tile (600 m) multiplied into the slope/haze vertex colour
rep("ob = mk_obj('bg_far_terrain', VF, FF.tolist(), mat_vcol('far', 0.95))\nlp = FF.ravel()\nset_corner_col(ob.data, np.concatenate([vc[lp], np.ones((len(lp), 1))], 1))",
    "vc = np.clip(vc * 1.3, 0, 1)   # the farmland tile averages 0.76: lift so the mean tone is kept\nob = mk_obj('bg_far_terrain', VF, FF.tolist(), mat_facade('far', os.path.join(HERE, 'tex', 'far_land.png'), 0.95))\nlp = FF.ravel()\nset_corner_col(ob.data, np.concatenate([vc[lp], np.ones((len(lp), 1))], 1))\nset_uv(ob.data, VF[lp, :2] / 600.0)")
# 1 bridges: concrete texture, piers with headstocks under road bridges, steel rail and posts on the parapets
rep("deck_c = lin((204, 204, 199)); rail_c = lin((189, 194, 201))", "deck_c = lin((236, 236, 232)); rail_c = lin((228, 230, 232)); steel_c = lin((120, 126, 132))\n    def box(cx, cy, z0, z1, hx, hy, ang, c):\n        ca_, sa_ = math.cos(ang), math.sin(ang); s0 = len(verts)\n        for zz in (z0, z1):\n            for ox, oy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)): verts.append((cx + ox * ca_ - oy * sa_, cy + ox * sa_ + oy * ca_, zz))\n        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)): faces.append(tuple(s0 + k for k in f)); cols.extend([c] * 4)")
rep("        box_strip(P, z, w, 1.4, deck_c)\n",
"""        box_strip(P, z, w, 1.4, deck_c)
        cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
        for d in np.arange(7.5, cum[-1] - 3, 15.0):   # pier pairs every 15 m with a headstock, down into the bed
            k = min(max(int(np.searchsorted(cum, d)) - 1, 0), len(P) - 2); t = (d - cum[k]) / max(cum[k + 1] - cum[k], 1e-6)
            q = P[k] + (P[k + 1] - P[k]) * t; ang = math.atan2(*(P[k + 1] - P[k])[::-1]); zg = float(height(q[0], q[1]))
            if z - 1.4 - zg < 1.0: continue
            box(q[0], q[1], z - 2.2, z - 1.4, 0.6, w / 2 - 0.5, ang, deck_c)
            for o in (-w / 4, w / 4): box(q[0] - o * math.sin(ang), q[1] + o * math.cos(ang), zg - 3, z - 2.2, 0.45, 0.45, ang, deck_c)
""")
rep("            box_strip(np.array(Q), z + 1.1, 0.25, 1.1, rail_c)\n",
"""            box_strip(np.array(Q), z + 1.1, 0.25, 1.1, rail_c)
            box_strip(np.array(Q), z + 1.5, 0.08, 0.08, steel_c)   # steel top rail on posts every 2.5 m
            cq = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(np.array(Q), axis=0).T))])
            for d in np.arange(0, cq[-1], 2.5):
                k = min(max(int(np.searchsorted(cq, d)) - 1, 0), len(Q) - 2); t = (d - cq[k]) / max(cq[k + 1] - cq[k], 1e-6); q = Q[k] + (Q[k + 1] - Q[k]) * t
                box(q[0], q[1], z + 1.1, z + 1.5, 0.04, 0.04, 0, steel_c)
""")
rep("        ob = mk_obj('bg_bridges', verts, faces, mat_vcol('bridge', 0.8))\n        set_corner_col(ob.data, np.concatenate([np.array(cols), np.ones((len(cols), 1))], 1))",
    "        ob = mk_obj('bg_bridges', verts, faces, mat_facade('bridge', os.path.join(HERE, 'tex', 'concrete.png'), 0.85))\n        set_corner_col(ob.data, np.concatenate([np.array(cols), np.ones((len(cols), 1))], 1)); set_uv_box(ob.data, 0.25)")
# 2 huts: small buildings round the ground (club sheds, kiosks) get walls with a roller door, window and weatherboards
rep("build_class('house', 'wall.png', 3.6, 3.2)", "for b in BL:\n    if b['c'] == 'house' and np.hypot(*np.array(b['p']).mean(0)) < spec.get('hut_r', 320): b['c'] = 'hut'\nbuild_class('house', 'wall.png', 3.6, 3.2)\nbuild_class('hut', 'wall_hut.png', 6.0, 3.2)")
# 3 aprons: own asphalt tile (32 m) with patches, oil stains, walkway lines and bay ticks; concrete kerbs round aprons and car parks
rep("m_road, 'bg_paved', TILE, 0.03, hole=spec.get('pave_hole'))",
    "m_apron, 'bg_paved', 32.0, 0.03, hole=spec.get('pave_hole'))")
rep("    m_road = mat_img_vc('road_asphalt', _tint(PAL['road'], 'road_asphalt_road.png'), 0.92)",
    "    m_road = mat_img_vc('road_asphalt', _tint(PAL['road'], 'road_asphalt_road.png'), 0.92)\n    m_apron = mat_img_vc('apron', os.path.join(HERE, 'tex', 'apron.png'), 0.9)")
rep("            if mat in (m_park, m_road) or nm == 'bg_carparks_pale': _mottle(ob.data, co)",
    "            if mat in (m_park, m_road, m_apron) or nm == 'bg_carparks_pale': _mottle(ob.data, co)")
rep("    m_pale = mat_img_vc(", """    KV, KF_, KC = [], [], []; kc = list(lin((196, 194, 188))) + [1.0]   # kerbs: 0.3 m wide, 0.15 m high, on every apron and car park outline
    for poly in [np.array(p, float) for k, p in spec.get('paint_poly', []) if k == 'paved'] + list(polys):
        Q = np.vstack([poly, poly[:1]]); D_ = []
        for p0, p1 in zip(Q, Q[1:]):
            m_ = max(1, int(np.hypot(*(p1 - p0)) // 3)); D_ += [p0 + (p1 - p0) * t for t in np.arange(m_) / m_]
        D_ = np.array(D_ + [Q[-1]]); z_ = height(D_[:, 0], D_[:, 1]) + 0.03
        for i in range(len(D_) - 1):
            e_ = D_[i + 1] - D_[i]; L_ = np.hypot(*e_)
            if L_ < 0.05: continue
            nx, ny = -e_[1] / L_ * 0.15, e_[0] / L_ * 0.15; s0 = len(KV)
            for zz in (z_[i] - 0.1, z_[i] + 0.15):
                KV += [(D_[i][0] + nx, D_[i][1] + ny, zz if i == i else 0), (D_[i + 1][0] + nx, D_[i + 1][1] + ny, zz - z_[i] + z_[i + 1]), (D_[i + 1][0] - nx, D_[i + 1][1] - ny, zz - z_[i] + z_[i + 1]), (D_[i][0] - nx, D_[i][1] - ny, zz)]
            for f in ((4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6)): KF_.append(tuple(s0 + k for k in f)); KC += [kc] * 4
    if KF_:
        ob = mk_obj('bg_kerbs', KV, KF_, mat_vcol('kerb', 0.8)); set_corner_col(ob.data, np.array(KC))
    m_pale = mat_img_vc(""")
open('scene.py', 'w', encoding='utf-8', newline='').write(s)
# palette: zincalume roof greys (no white boxes), hut wall colours
sp = 'spec/peoplefirst.json'; d = json.load(open(sp)); p = d['palette']
p['roofs_flat'] = [[178, 182, 184], [158, 162, 164], [140, 144, 148]]
p['roofs_house'] = [c if c != [206, 206, 198] else [170, 172, 168] for c in p['roofs_house']]
p['walls_hut'] = [[204, 210, 202], [214, 202, 178], [178, 190, 172], [200, 180, 152]]
json.dump(d, open(sp, 'w')); print('ok')
