"""The yard's white lines are access=private footways (staff walkways between tracks, gravel in reality). Paint private
footways/paths in the ballast colour; public paths keep PAL path."""
p = 'prep.py'; s = open(p, newline='').read()
a = "col = PAL['path'] if hw in ('footway', 'path', 'cycleway', 'pedestrian') else PAL['road']"
assert s.count(a) == 1
s = s.replace(a, a + "\n            if hw in ('footway', 'path') and t.get('access') == 'private': col = PAL['ballast']   # yard staff walkways: gravel".replace('\n', '\r\n' if '\r\n' in s else '\n'))
open(p, 'w', newline='').write(s); print('ok')
