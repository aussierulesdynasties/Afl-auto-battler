import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
def rep(p, pairs):
    s = open(p, newline='').read()
    for a, b in pairs:
        if b in s and a not in s: continue
        assert a in s, (p, a[:60]); s = s.replace(a, b)
    open(p, 'w', newline='').write(s)
rep('tex_facade_atlas.py', [("img[..., :3] *= (0.86 + 0.14 * (1 - yy / H))[..., None][::-1] if False else (0.88 + 0.12 * (yy / H))[..., None][::-1]",
                             "img[..., :3] *= (1.0 - 0.12 * (yy / H))[..., None]   # grime toward the base")])
rep('scene.py', [
("def build_class(cls, tex, tw, th):\n    verts",
 "ATL = json.load(open(os.path.join(D, 'atlas_cells.json'))) if os.path.exists(os.path.join(D, 'atlas_cells.json')) else None\ndef build_class(cls, tex, tw, th):\n    if ATL is not None and os.path.exists(os.path.join(D, 'atlas_%s.png' % cls)): tex = os.path.join(D, 'atlas_%s.png' % cls)\n    verts"),
("    for b in BL:\n        if b['c'] != cls: continue",
 "    for bi, b in enumerate(BL):\n        if b['c'] != cls: continue\n        cell = ATL.get(str(bi)) if ATL is not None else None"),
("        per = 0.0\n        for i in range(k):",
 "        per = 0.0\n        PER = float(np.hypot(*np.diff(np.vstack([P, P[:1]]), axis=0).T).sum())\n        if cell: wc = np.ones(3)\n        for i in range(k):"),
("            u0, u1 = per / tw, (per + L) / tw\n            v0, v1 = -1.0 / th, (top - base - 1.0) / th",
 "            if cell:\n                cu0, cv0, cu1, cv1 = cell\n                u0, u1 = cu0 + (cu1 - cu0) * per / PER, cu0 + (cu1 - cu0) * (per + L) / PER\n                v0, v1 = cv0, cv1\n            else:\n                u0, u1 = per / tw, (per + L) / tw\n                v0, v1 = -1.0 / th, (top - base - 1.0) / th"),
("mat_facade('facade_' + cls, os.path.join(HERE, 'tex', tex))",
 "mat_facade('facade_' + cls, tex if os.path.isabs(tex) else os.path.join(HERE, 'tex', tex))"),
])
print('patched')
