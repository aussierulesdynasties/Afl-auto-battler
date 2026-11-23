s = open('prep.py', encoding='utf-8', newline='').read()
a = 'or t.get("building") in ("roof", "grandstand", "stadium"): continue'
assert a in s; s = s.replace(a, 'or t.get("building") in ("grandstand", "stadium"): continue')
a = "                    wall=int(rng.integers(0, len(PAL['walls_' + cls])))))\n"
assert a in s; s = s.replace(a, a + "    if kind == 'roof': BLD[-1]['open'] = 1; BLD[-1]['c'] = 'block'   # OSM building=roof: open canopy (roof on posts)\n")
open('prep.py', 'w', encoding='utf-8', newline='').write(s)
s = open('scene.py', encoding='utf-8', newline='').read()
a = "        top = base + 1.0 + h - rh\n"
assert a in s; s = s.replace(a, a + "        _gb = base\n        if b.get('open'): base = top - 1.4; shed = False; V_, F_, C_, U_ = verts, faces, cols, uvs; TW, TH = tw, th   # canopy: 0.4 m fascia only\n", 1)
a = "        # roof: own mesh, hand-made texture"
assert a in s; s = s.replace(a, """        if b.get('open'):   # steel posts at each corner, ground to roof
            for x, y in P:
                o = len(V_); d = 0.08
                for zz in (_gb + 0.5, top):
                    V_ += [(x - d, y - d, zz), (x + d, y - d, zz), (x + d, y + d, zz), (x - d, y + d, zz)]
                F_ += [(o, o + 1, o + 5, o + 4), (o + 1, o + 2, o + 6, o + 5), (o + 2, o + 3, o + 7, o + 6), (o + 3, o, o + 4, o + 7)]
                C_ += [lin([120, 122, 124])] * 16; U_ += [(0, 0)] * 16
""" + a, 1)
open('scene.py', 'w', encoding='utf-8', newline='').write(s); print('ok')
