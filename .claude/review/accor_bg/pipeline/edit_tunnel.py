p = 'prep.py'
s = open(p, encoding='utf-8', newline='').read()
nl = "\r\n" if "\r\n" in s else "\n"
U = "t.get('tunnel', 'no') != 'no' or t.get('location') == 'underground' or str(t.get('layer', '0')).startswith('-')"
old1 = "# linear features" + nl + "for el in js:" + nl + "    t = el.get('tags', {})" + nl + "    if el['type'] != 'way': continue" + nl
assert s.count(old1) == 1
s = s.replace(old1, old1 + "    if " + U + ": continue   # tunnels and culverts are underground: nothing on the surface" + nl)
old2 = "    if t.get('highway') in ('motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'residential', 'service', 'unclassified') or t.get('railway'):"
assert s.count(old2) == 1
s = s.replace(old2, old2.replace("    if t.get('highway')", "    if not (" + U + ") and (t.get('highway')").replace("or t.get('railway'):", "or t.get('railway')):"))
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
