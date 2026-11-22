s = open('scene.py', encoding='utf-8', newline='').read()
def rep(a, b):
    global s
    assert a in s, a[:60]; s = s.replace(a, b, 1)
rep("def build_class(cls, tex, tw, th):", "def build_class(cls, tex, tw, th, sel=None, vnorm=False, tag=None):")
rep("        if b['c'] != cls: continue", "        if b['c'] != cls or (sel is not None and not sel(b)): continue")
rep("            v0, v1 = -1.0 / th, (top - base - 1.0) / th", "            v0, v1 = (-1.0 / th, (top - base - 1.0) / th) if not vnorm else (-1.0 / (top - base - 1.0), 1.0)")
rep("kind = 'tile' if (cls == 'house'", "kind = 'metal' if spec.get('all_metal_roofs') else 'tile' if (cls == 'house'")
rep("        def ruv_(x, y): return ((x * ct + y * st) / 3.04, (-x * st + y * ct) / 3.04)", "        RT = 3.0 if spec.get('all_metal_roofs') else 3.04\n        def ruv_(x, y): return ((x * ct + y * st) / RT, (-x * st + y * ct) / RT)")
rep("    ob = mk_obj('bg_bld_' + cls, verts, faces, mat_facade('facade_' + cls, os.path.join(HERE, 'tex', tex)))",
    "    tg = tag or cls\n    ob = mk_obj('bg_bld_' + tg, verts, faces, mat_facade('facade_' + tg, os.path.join(HERE, 'tex', tex)))")
rep("        ro = mk_obj('bg_roof_%s_%s' % (cls, kind), rv, rf, mat_facade('roof_%s_%s' % (cls, kind), os.path.join(HERE, 'tex', 'roof_%s.png' % kind)))",
    "        rtex = 'rw/roof_metal_rib.png' if spec.get('all_metal_roofs') else 'roof_%s.png' % kind\n        ro = mk_obj('bg_roof_%s_%s' % (tg, kind), rv, rf, mat_facade('roof_%s_%s' % (tg, kind), os.path.join(HERE, 'tex', rtex)))")
rep("""build_class('house', 'wall.png', 3.6, 3.2)
build_class('block', 'wall.png', 3.6, 3.2)""", """if spec.get('rw_facades'):
    _CM = json.load(open(os.path.join(HERE, 'tex', 'rw', 'com.json')))
    for _i, _b in enumerate(BL): _b['_i'] = _i
    for _k in range(4): build_class('house', 'rw/queens_%d.png' % _k, 3.6, 1.0, sel=lambda b, k=_k: b['_i'] % 4 == k, vnorm=True, tag='house%d' % _k)
    _big = [b for b in BL if b['c'] == 'block' and b['a'] > 600]
    for _n, _b in enumerate(_big):   # every big building its own facade
        _m = _CM[_n % len(_CM)]; build_class('block', 'rw/com_%d.png' % (_n % len(_CM)), _m['tw'], _m['th'], sel=lambda b, i=_b['_i']: b['_i'] == i, tag='big%d' % _n)
    print('big buildings', len(_big), 'unique facades', min(len(_big), len(_CM)))
    for _k in range(12):   # small blocks: 12 shared facades from the end of the set
        _j = len(_CM) - 1 - _k; _m = _CM[_j]
        build_class('block', 'rw/com_%d.png' % _j, _m['tw'], _m['th'], sel=lambda b, k=_k: b['a'] <= 600 and b['_i'] % 12 == k, tag='blk%d' % _k)
else:
    build_class('house', 'wall.png', 3.6, 3.2)
    build_class('block', 'wall.png', 3.6, 3.2)""")
open('scene.py', 'w', encoding='utf-8', newline='').write(s); print('patched')
