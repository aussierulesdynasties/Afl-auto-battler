p='surf.py'; s=open(p,encoding='utf-8').read()
o="m = tri(p, 10.0); m['z'] = float(min(bz)) - 0.1 if bz else 0.0; out.append(m)"
assert s.count(o)==1; s=s.replace(o,"m = tri(p, 10.0); m['z'] = float(min(bz)) - 0.1 if bz else 0.0; m['body'] = bi + 1; out.append(m)")
open(p,'w',encoding='utf-8').write(s)
p='prep.py'; s=open(p,encoding='utf-8').read()
o="_wmA = np.asarray(_wmI) > 127\n"
assert s.count(o)==1; s=s.replace(o,o+"""_idI = Image.new('L', img.size, 0); _idd = ImageDraw.Draw(_idI)   # which water body each pixel belongs to (1..n), for the terrain sink
for _bi, _g in enumerate(WBODY):
    for _p in parts(_g):
        _idd.polygon(P(list(_p.exterior.coords)), fill=_bi + 1)
        for _h in _p.interiors: _idd.polygon(P(list(_h.coords)), fill=0)
_idI.resize((N // SS, N // SS), Image.NEAREST).save(os.path.join(OUT, 'water_id.png'))
""")
open(p,'w',encoding='utf-8').write(s)
p='scene.py'; s=open(p,encoding='utf-8').read()
o="""for _w in _SF['water']:
    _wv = np.array(_w['v'])
    if not len(_wv): continue
    _sel = (X > _wv[:, 0].min() - NS) & (X < _wv[:, 0].max() + NS) & (Y > _wv[:, 1].min() - NS) & (Y < _wv[:, 1].max() + NS) & (_gm[_iy, _ix, 1] > 0.5)
    Z[_sel] = np.minimum(Z[_sel], _w['z'] - 0.15)
"""
assert s.count(o)==1; s=s.replace(o,"""_WID = np.flipud(np.array(__import__('PIL.Image', fromlist=['Image']).open(os.path.join(D, 'water_id.png')))) if False else None
_wi = bpy.data.images.load(os.path.join(D, 'water_id.png')); _wi.colorspace_settings.name = 'Non-Color'; _wi.alpha_mode = 'NONE'
_wa = np.empty(len(_wi.pixels), np.float32); _wi.pixels.foreach_get(_wa); _wa = np.rint(_wa.reshape(_wi.size[1], _wi.size[0], 4)[..., 0] * 255).astype(int)   # rows south to north
_wid = _wa[np.clip(((Y + NE) / (2 * NE) * _wi.size[1]).astype(int), 0, _wi.size[1] - 1), np.clip(((X + NE) / (2 * NE) * _wi.size[0]).astype(int), 0, _wi.size[0] - 1)]
for _w in _SF['water']:   # sink the terrain 0.15 m under its own water body only
    _sel = _wid == _w['body']
    Z[_sel] = np.minimum(Z[_sel], _w['z'] - 0.15)
""")
open(p,'w',encoding='utf-8').write(s); print('ok')
