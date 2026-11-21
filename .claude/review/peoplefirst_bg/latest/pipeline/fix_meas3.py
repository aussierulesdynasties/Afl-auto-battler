p='meas_table.py'; s=open(p,encoding='utf-8').read()
a="enumerate([q for q in spec['paint_poly'] if q[0] == 'water'])"
b="enumerate([(q[0], [list(c) for c in list(__import__('shapely.geometry',fromlist=['Polygon']).Polygon(q[1]).buffer(4, join_style=2).exterior.coords)[:-1]]) for q in __import__('json').load(open('spec/peoplefirst_pre10c.json'))['paint_poly'] if q[0] == 'water'])"
assert s.count(a)==1; s=s.replace(a,b)
s=s.replace("'model water inside trace %.0f%%' % (100 * (m & W2).sum() / max(1, m.sum()))","'model/aerial %.0f%% (original trace +4 m)' % (100 * (m & W2).sum() / max(1, (m & W1).sum()))")
open(p,'w',encoding='utf-8').write(s); print('ok')
