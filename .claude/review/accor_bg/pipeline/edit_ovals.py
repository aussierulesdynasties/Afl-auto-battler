import re
p = 'prep.py'
s = open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'
# 1. move _obox out of the court_slabs block (unindent) so ovals can use it
a = s.index('    def _obox(pts):')
b = s.index('    HK = []')
blk = s[a:b]
s = s[:a] + s[b:]
ded = nl.join(l[4:] if l.startswith('    ') else l for l in blk.split(nl))
anchor = "if spec.get('court_slabs'):"
s = s.replace(anchor, ded + anchor, 1)
# 2. AFL ovals block before the baseball block
ov = (
"# AFL ovals outside the model: boundary = the OSM pitch outline; lines and posts are built as geometry in scene.py" + nl +
"OV = []" + nl +
"for el in js:" + nl +
"    t = el.get('tags', {})" + nl +
"    if el['type'] != 'way' or t.get('leisure') != 'pitch' or 'australian_football' not in t.get('sport', '') or 'geometry' not in el: continue" + nl +
"    pts = ring(el)" + nl +
"    if len(pts) < 8 or pts[0] != pts[-1]: continue" + nl +
"    Q = np.array(pts[:-1], float)" + nl +
"    if not (200 < np.hypot(*Q.mean(0)) < 1500): continue" + nl +
"    OV.append([_obox(pts[:-1]), [[round(float(x), 2), round(float(y), 2)] for x, y in Q]])" + nl +
"json.dump(OV, open(os.path.join(OUT, 'ovals.json'), 'w'))" + nl +
"print('afl ovals', [o[0] for o in OV])" + nl)
anchor2 = '# baseball: dirt infield'
assert anchor2 in s
s = s.replace(anchor2, ov + anchor2, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
