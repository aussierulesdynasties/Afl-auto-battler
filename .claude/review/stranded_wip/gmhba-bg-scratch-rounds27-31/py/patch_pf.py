import sys
p = sys.argv[1]; t = open(p, newline='').read()
def rep(a, b):
    global t
    assert t.count(a) == 1, a[:60]; t = t.replace(a, b)
# per-building facade variants
rep("def build_class(cls, tex, tw, th):\n", "def build_class(cls, tex, tw, th, var=None):\n")
rep("        if b['c'] != cls: continue\n", "        if b['c'] != cls: continue\n        if var and (b['_i'] * 7919) % var[1] != var[0]: continue\n")
rep("    if CL[1]:\n        oc = mk_obj('bg_clad_' + cls,", "    sfx = '' if not var else '_v%d' % var[0]\n    if CL[1]:\n        oc = mk_obj('bg_clad_' + cls + sfx,")
rep("    ob = mk_obj('bg_bld_' + cls, verts, faces, mat_facade('facade_' + cls,", "    ob = mk_obj('bg_bld_' + cls + sfx, verts, faces, mat_facade('facade_' + cls + sfx,")
rep("        ro = mk_obj('bg_roof_%s_%s' % (cls, kind), rv,", "        ro = mk_obj('bg_roof_%s_%s%s' % (cls, kind, sfx), rv,")
rep("for b in BL:\n    P = np.array(b['p']); x, y = P[:, 0], P[:, 1]\n", "for _i, b in enumerate(BL):\n    b['_i'] = _i; P = np.array(b['p']); x, y = P[:, 0], P[:, 1]\n")
rep("build_class('house', 'house_wall.png', 3.6, 3.2)\nbuild_class('block', 'wall.png', 3.6, 3.2)\n",
    "for _v in range(8): build_class('house', 'fac/h%d.png' % _v, 3.6, 3.2, (_v, 8))   # hand-made facade per building (py_mk_facades.py)\n"
    "for _v in range(12): build_class('block', 'fac/b%d.png' % _v, 3.6, 3.2, (_v, 12))\n")
# roads: People First asphalt, one 104 m seamless tile (repeat break), 40 m mottle in vertex colour
rep("if U_ is not None: U_ += [(-w / 2 / 8.0, s_[i] / 8.0), (w / 2 / 8.0, s_[i] / 8.0), (w / 2 / 8.0, s_[i + 1] / 8.0), (-w / 2 / 8.0, s_[i + 1] / 8.0)]",
    "if U_ is not None: U_ += [(A[i, 0] / 104.0, A[i, 1] / 104.0), (B[i, 0] / 104.0, B[i, 1] / 104.0), (B[i + 1, 0] / 104.0, B[i + 1, 1] / 104.0), (A[i + 1, 0] / 104.0, A[i + 1, 1] / 104.0)]")
rep("        ro = mk_obj('bg_roads', av, af, mat_mul('road_asphalt', os.path.join(HERE, 'tex', 'mt', 'road_asphalt_v2.png'), 0.9, 1 / 0.425))\n        set_corner_col(ro.data, np.concatenate([np.array(ac), np.ones((len(ac), 1))], 1)); set_uv(ro.data, au)\n",
    "        ro = mk_obj('bg_roads', av, af, mat_mul('road_asphalt', os.path.join(HERE, 'tex', 'road_asphalt_road.png'), 0.92, 1.0))\n"
    "        from mathutils import noise as _nz\n"
    "        _P = np.array(av)[:, :2]; _n = np.array([_nz.noise(Vector((x / 40.0, y / 40.0, 0.5))) + 0.5 * _nz.noise(Vector((x / 20.0, y / 20.0, 7.5))) for x, y in _P]) / 1.5\n"
    "        _m = 0.85 + 0.15 * np.clip(_n * 0.5 + 0.5, 0, 1)\n"
    "        set_corner_col(ro.data, np.stack([_m, _m, _m, np.ones_like(_m)], 1)); set_uv(ro.data, au)\n")
# rails: ballast and sleepers texture on the bed (hand-made tile, 2.8 m across x 2.4 m along)
rep("    if faces:\n        ob = mk_obj('bg_rails', verts, faces, mat_vcol('rails', 0.6))\n        set_corner_col(ob.data, np.concatenate([np.array(cols), np.ones((len(cols), 1))], 1))\n",
    "    if faces:\n        BI = [i for i, c in enumerate(cols[::4]) if c is bed_c]; SI = [i for i, c in enumerate(cols[::4]) if c is not bed_c]\n"
    "        bv, bf, bu = [], [], []\n"
    "        for i in BI:\n"
    "            f = faces[i]; q = [verts[j] for j in f]; L0 = sum(math.dist(verts[faces[k][0]][:2], verts[faces[k][3]][:2]) for k in range(max(0, i - 1), i)) if False else 0\n"
    "            n = len(bv); bv += q; bf.append((n, n + 1, n + 2, n + 3))\n"
    "            s0 = BS[i]; s1 = s0 + math.dist(q[0][:2], q[3][:2]); bu += [(0, s0 / 2.4), (1, s0 / 2.4), (1, s1 / 2.4), (0, s1 / 2.4)]\n"
    "        if bf:\n"
    "            bo = mk_obj('bg_rail_bed', bv, bf, mat_mul('rail_bed', os.path.join(HERE, 'tex', 'mt', 'rail_bed.png'), 0.9, 1 / RB_MEAN)); set_uv(bo.data, bu)\n"
    "            set_corner_col(bo.data, np.ones((len(bu), 4)))\n"
    "        sv = [v for i in SI for v in [verts[j] for j in faces[i]]]; sf = [(4 * k, 4 * k + 1, 4 * k + 2, 4 * k + 3) for k in range(len(SI))]\n"
    "        if sf:\n"
    "            ob = mk_obj('bg_rails', sv, sf, mat_vcol('rails', 0.35)); set_corner_col(ob.data, np.tile(list(steel_c) + [1.0], (len(sv), 1)))\n")
# along-track distance per bed face, recorded in drape_strip
rep("        for i in range(n - 1):\n            faces.append((s0 + 2 * i, s0 + 2 * i + 1, s0 + 2 * i + 3, s0 + 2 * i + 2)); cols.extend([c] * 4)\n",
    "        sacc = 0.0\n        for i in range(n - 1):\n            faces.append((s0 + 2 * i, s0 + 2 * i + 1, s0 + 2 * i + 3, s0 + 2 * i + 2)); cols.extend([c] * 4); BS.append(sacc); sacc += float(np.hypot(*(P[i + 1] - P[i])))\n")
rep("    verts, faces, cols = [], [], []\n    bed_c = ", "    verts, faces, cols, BS = [], [], [], []\n    RB_MEAN = float(open(os.path.join(HERE, 'tex', 'mt', 'rail_bed.mean')).read())\n    bed_c = ")
open(p, 'w', newline='').write(t); print('ok')
