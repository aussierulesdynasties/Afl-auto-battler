import io
f = 'prep.py'; s = io.open(f, encoding='utf-8', newline='').read()
a = "        if b['c'] != 'block' or A_ < 400: continue"
b = "        if b['c'] == 'tower' or (b['c'] == 'block' and A_ < 400): continue"
assert s.count(a) == 1; s = s.replace(a, b)
a = "        if len(px) > 20: b['roof_c'] = [int(v) for v in np.median(px, 0)]"
b = "        if len(px) > 20:\n            md = np.median(px, 0)\n            if not (md[1] > md[0] + 6 and md[1] >= md[2]): b['roof_c'] = [int(v) for v in md]   # tree-covered roofs keep the palette"
assert s.count(a) == 1; s = s.replace(a, b)
io.open(f, 'w', encoding='utf-8', newline='').write(s); print('ok')
