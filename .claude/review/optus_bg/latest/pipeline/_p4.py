s = open('prep.py', encoding='utf-8').read()
a = "json.dump(BLD, open(os.path.join(OUT, 'buildings.json'), 'w'))"
assert s.count(a) == 1
s = s.replace(a, """# roof colour: the median aerial colour inside each footprint (one picked colour per roof, never the aerial's pixels)
_sp_ = os.path.join(os.path.dirname(OUT), 'sat.png')
if spec.get('cover_from_aerial') and os.path.exists(_sp_):
    _SA = np.asarray(Image.open(_sp_).convert('RGB')); _SN = _SA.shape[0]; _SM = 2 * NEAR / _SN
    for b_ in BLD:
        P_ = np.array(b_['p'], float); cx_ = (P_[:, 0] + NEAR) / _SM; cy_ = (NEAR - P_[:, 1]) / _SM
        x0_, x1_, y0_, y1_ = int(max(cx_.min(), 0)), int(min(cx_.max() + 1, _SN)), int(max(cy_.min(), 0)), int(min(cy_.max() + 1, _SN))
        if x1_ - x0_ < 2 or y1_ - y0_ < 2: continue
        m_ = Image.new('L', (x1_ - x0_, y1_ - y0_)); ImageDraw.Draw(m_).polygon(list(zip(cx_ - x0_, cy_ - y0_)), fill=255)
        m_ = np.asarray(m_.filter(ImageFilter.MinFilter(5))) > 0   # stay clear of the edges (walls, shadows)
        px_ = _SA[y0_:y1_, x0_:x1_][m_]
        if len(px_) < 8: continue
        px_ = px_[px_.max(1) > 50]   # drop shadow pixels
        if len(px_) < 8: continue
        b_['roof_c'] = [int(v) for v in np.median(px_, 0)]
""" + a)
if 'ImageFilter' not in s.split('\n', 30)[-1] and 'import ImageFilter' not in s and ', ImageFilter' not in s:
    s = s.replace('from PIL import Image, ImageDraw', 'from PIL import Image, ImageDraw, ImageFilter', 1)
assert 'ImageFilter' in s.split("_sp_ =")[0], 'import'
open('prep.py', 'w', encoding='utf-8', newline='').write(s)
c = open('scene.py', encoding='utf-8').read()
o = "        rc = roofs[b['roof'] % len(roofs)] * (1 + 0.08 * (rng.random() - 0.5))"
assert c.count(o) == 1
c = c.replace(o, "        rc = (lin(b['roof_c']) / 0.62 if b.get('roof_c') else roofs[b['roof'] % len(roofs)]) * (1 + 0.08 * (rng.random() - 0.5))   # aerial roof colour / roof texture mean")
open('scene.py', 'w', encoding='utf-8', newline='').write(c); print('ok')
