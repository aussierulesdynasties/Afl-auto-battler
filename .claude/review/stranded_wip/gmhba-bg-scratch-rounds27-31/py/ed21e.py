def ed(p, pairs):
    s = open(p, encoding='utf-8', newline='').read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a[:60]); s = s.replace(a, b)
    open(p, 'w', encoding='utf-8', newline='').write(s)
ed('scene.py', [
 ("            if U_ is not None: U_ += [(A[i, 0] / 104.0", "            if U_ is not None and RV2: U_ += [(0, s_[i] / 40.0), (1, s_[i] / 40.0), (1, s_[i + 1] / 40.0), (0, s_[i + 1] / 40.0)]\n            elif U_ is not None: U_ += [(A[i, 0] / 104.0"),
 ("    av, af, ac, au, lv, lf = [], [], [], [], [], []", "    av, af, ac, au, lv, lf = [], [], [], [], [], []; RV2 = bool(spec.get('road_v2')); kv, kf = [], []"),
 ("w = RW[r['hw']]; main = RK[r['hw']] >= 3", "w = RW[r['hw']]; main = RK[r['hw']] >= (2 if RV2 else 3)"),
 ("            n0 = len(af); ribbon(q, 0, w, zz, av, af, au); ac += [acol] * 4 * (len(af) - n0)", "            n0 = len(af); ribbon(q, 0, w, zz, av, af, au); ac += [acol] * 4 * (len(af) - n0)\n            if RV2 and RK[r['hw']] <= 4:   # concrete kerb and channel both sides (not on freeways)\n                for sd in (-1, 1): ribbon(q, sd * (w / 2 + 0.3), 0.6, zz + 0.12, kv, kf)"),
 ("ro = mk_obj('bg_roads', av, af, mat_mul('road_asphalt', os.path.join(HERE, 'tex', 'road_asphalt_road.png'), 0.92, 1.0))", "ro = mk_obj('bg_roads', av, af, mat_mul('road_asphalt', os.path.join(HERE, 'tex', 'mt', 'road_lane.png') if RV2 else os.path.join(HERE, 'tex', 'road_asphalt_road.png'), 0.92, 1.0))"),
 ("    if lf:\n        lm = bpy.data.materials.new('road_line')", "    if kf:\n        km_ = bpy.data.materials.new('road_kerb'); km_.use_nodes = True; km_.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*srgb((182, 178, 168)), 1); km_.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.85\n        mk_obj('bg_road_kerbs', kv, kf, km_)\n    if lf:\n        lm = bpy.data.materials.new('road_line')"),
])
print('ok')
