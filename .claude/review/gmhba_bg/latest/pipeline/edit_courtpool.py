import json
g=json.load(open('spec/gmhba.json'))
g['palette']['court_blue']=[70,104,170]; g['palette']['pool']=[120,190,200]
g['paint_poly']=[p for p in g['paint_poly'] if p[0]!='court_blue']+[['court_blue',json.load(open('out/gmhba/court_poly.json'))]]
g['cover']=[c for c in g['cover'] if c[1]!='swimming_pool']+[['leisure','swimming_pool','pool']]
json.dump(g,open('spec/gmhba.json','w'),indent=1)
p='prep.py'; s=open(p,encoding='utf-8',newline='').read()
a="    if 'building' in t and len(pts) > 2: md.polygon(P(pts), fill=0)\n"
b="    if 'building' in t and len(pts) > 2: md.polygon(P(pts), fill=0); md.line(P(pts + pts[:1]), fill=0, width=max(1, int(8 / PX))); rd.polygon(P(pts), fill=255); rd.line(P(pts + pts[:1]), fill=255, width=max(1, int(8 / PX)))   # director 2026-11-20: crowns clear of roofs\n"
assert a in s; s=s.replace(a,b); open(p,'w',encoding='utf-8',newline='').write(s); print('ok')
