p='prep.py'; s=open(p,newline='').read()
old="mask = Image.new('L', (N, N), 0); md = ImageDraw.Draw(mask)"
new="""_td = spec.get('tree_default', 0)   # m^2 per tree on land OSM leaves untagged (satellite shows scattered trees)
mask = Image.new('L', (N, N), 0 if not _td else max(1, min(255, int(40000 / _td)))); md = ImageDraw.Draw(mask)"""
assert old in s; s=s.replace(old,new)
old2="# keep trees off roads, rails, buildings and water"
new2="""for pk, poly in spec.get('paint_poly', []): md.polygon(P([tuple(q) for q in poly]), fill=0)
for el in js:
    t = el.get('tags', {})
    if el['type'] == 'way' and (t.get('amenity') == 'parking' or t.get('leisure') in ('pitch', 'swimming_pool', 'sports_centre')):
        pts = ring(el)
        if len(pts) > 2: md.polygon(P(pts), fill=0)
# keep trees off roads, rails, buildings and water"""
assert old2 in s; s=s.replace(old2,new2,1); open(p,'w',newline='').write(s); print('ok')
