import sys
p = sys.argv[1]; t = open(p, newline='').read()
a = "# mowing stripes and wear on grass"
assert t.count(a) == 1 and 'paved lots: aerial median' not in t
b = """# paved lots: aerial median colour per OSM paved landuse / car park (colour only, never pixels), brightest channel capped at 160
if os.path.exists(_SP):
    _dr2 = ImageDraw.Draw(img); _np = 0
    for el in js:
        tg = el.get('tags', {})
        if el['type'] != 'way' or 'geometry' not in el: continue
        if not (tg.get('amenity') == 'parking' and tg.get('parking', 'surface') == 'surface') and tg.get('landuse') not in ('commercial', 'retail', 'industrial'): continue
        pts = ring(el)
        if len(pts) < 4: continue
        q = [((x + _hm) / _mp, (_hm - y) / _mp) for x, y in pts]
        x0, y0 = [int(min(v)) for v in zip(*q)]; x1, y1 = [int(max(v)) + 1 for v in zip(*q)]
        if x0 < 0 or y0 < 0 or x1 >= _SA.shape[1] or y1 >= _SA.shape[0] or (x1 - x0) * (y1 - y0) > 250000: continue
        mk = Image.new('L', (x1 - x0, y1 - y0)); ImageDraw.Draw(mk).polygon([(u - x0, v - y0) for u, v in q], fill=1)
        px_ = _SA[y0:y1, x0:x1][np.asarray(mk) > 0]
        if len(px_) < 30: continue
        px_ = px_[~((px_[:, 1] > px_[:, 0] + 6) & (px_[:, 1] >= px_[:, 2]))]   # drop tree and grass pixels
        if len(px_) < 30: continue
        md = np.median(px_, 0); md = md * min(1.0, 160.0 / max(md.max(), 1))
        # only repaint pixels already painted paved/parking, so buildings, roads and lawns inside the outline keep their paint
        _mk = Image.new('L', (N, N), 0); ImageDraw.Draw(_mk).polygon(P(pts), fill=255)
        _ar = np.asarray(img).astype(np.int16); _m = np.asarray(_mk) > 0
        for _k in ('paved', 'parking'):
            _sel = _m & (np.abs(_ar - np.array(PAL[_k])).max(-1) < 6)
            _ar[_sel] = md.astype(np.int16)
        img = Image.fromarray(_ar.astype(np.uint8)); _np += 1
    print('paved lots from aerial median', _np)
"""
open(p, 'w', newline='').write(t.replace(a, b + a))
print('ok')
