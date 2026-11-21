import re
p = 'prep.py'; s = open(p, encoding='utf-8').read()
def rep(old, new):
    global s
    assert s.count(old) == 1, old[:80]; s = s.replace(old, new)
# mp_rings (outer minus inner) next to rel_rings
rep("def match(tags, k, v): return k in tags and (v == '*' or tags[k] in v.split('|'))\n",
"""def match(tags, k, v): return k in tags and (v == '*' or tags[k] in v.split('|'))
def mp_rings(mems):
    \"\"\"join multipolygon member ways (lists of lat/lon dicts) into rings by matching end nodes (open rings close on themselves)\"\"\"
    segs = [[(round(p['lat'], 7), round(p['lon'], 7)) for p in m['geometry'] if p] for m in mems]
    segs = [q for q in segs if len(q) > 1]; out = []
    while segs:
        cur = segs.pop(0)
        while cur[0] != cur[-1]:
            for i, q in enumerate(segs):
                if q[0] == cur[-1]: cur = cur + q[1:]; break
                if q[-1] == cur[-1]: cur = cur + q[::-1][1:]; break
            else: break
            segs.pop(i)
        out.append([xy(a, b) for a, b in cur])
    return out
""")
# courts: colour from the spec; keep the slab hulls for surf.py
rep("                col = 'court_green'\n", "                col = spec.get('court_col', 'court_green')\n")
rep("    print('court slabs', len(set(find(i) for i in range(len(CT)))), 'courts', len(CT))\n",
    "    print('court slabs', len(set(find(i) for i in range(len(CT)))), 'courts', len(CT))\n    _CTSLABS = json.load(open(os.path.join(OUT, 'courts.json')))['slabs']\n")
# river lines: the OSM water polygons are the river now (mesh); streams stay painted
rep("        wd = 40 if t['waterway'] == 'river' else 8\n        dr.line(",
    "        wd = 40 if t['waterway'] == 'river' else 8\n        if t['waterway'] == 'river' and not dry: wd = 0   # river = OSM water polygons as a mesh (surf.py)\n        if wd: dr.line(")
# roads and paths are meshes (surf.py): no paint
rep("""            col = PAL['path'] if hw in ('footway', 'path', 'cycleway', 'pedestrian') else PAL['road']
            dr.line(P(pts), fill=tuple(col), width=max(1, int(wd / PX)))
""", """            pass   # roads and paths are their own crisp meshes (surf.py), never painted
""")
# water_tex tiling out; surfaces in; mud under the water and a 1.5 m shore band; mask for scene.py (G = water)
i0 = s.index("# River Torrens water: tile"); i1 = s.index("# hand-made grain:")
s = s[:i0] + """exec(open(os.path.join(HERE, 'surf.py'), encoding='utf-8').read())   # road, paving, water, Oval No.2 meshes
_wmI = Image.new('L', img.size, 0); _wd = ImageDraw.Draw(_wmI); _mdI = Image.new('L', img.size, 0); _md2 = ImageDraw.Draw(_mdI)
for _p in parts(WATER):
    _wd.polygon(P(list(_p.exterior.coords)), fill=255)
    for _h in _p.interiors: _wd.polygon(P(list(_h.coords)), fill=0)
for _p in parts(WATER.buffer(1.5, quad_segs=3)):
    _md2.polygon(P(list(_p.exterior.coords)), fill=255)
    for _h in _p.interiors: _md2.polygon(P(list(_h.coords)), fill=0)
img.paste((70, 66, 52), (0, 0), _mdI)   # mud under the water and in the 1.5 m shallows
_wmA = np.asarray(_wmI) > 127
Image.fromarray(np.stack([np.zeros_like(_wmA), _wmA, np.zeros_like(_wmA)], 2).astype(np.uint8) * 255).resize((N // SS, N // SS), Image.BILINEAR).save(os.path.join(OUT, 'ground_mask.png'))
print('water px', int(_wmA.sum()))
""" + s[i1:]
# trees: none in water or within 1.5 m of it
rep("mv = np.asarray(mask).astype(np.float32)", """for _p in parts(WATER.buffer(1.5, quad_segs=3)):   # no trees in water or within 1.5 m of it
    md.polygon(P(list(_p.exterior.coords)), fill=0)
mv = np.asarray(mask).astype(np.float32)""")
rep("TR = [[x, y, int(rng.integers(0, len(spec['tree_kinds'])))] for x, y in TR if abs(x) < NEAR and abs(y) < NEAR]",
"""_WP = shapely.prepared.prep(WATER.buffer(1.5)) if not WATER.is_empty else None   # no tree (mapped, traced or street) stands within 1.5 m of water
_n0 = len(TR); TR = [q for q in TR if _WP is None or not _WP.contains(shapely.Point(q[0], q[1]))]; print('trees dropped near water', _n0 - len(TR))
TR = [[x, y, int(rng.integers(0, len(spec['tree_kinds'])))] for x, y in TR if abs(x) < NEAR and abs(y) < NEAR]""")
open(p, 'w', encoding='utf-8').write(s); print('ok')
