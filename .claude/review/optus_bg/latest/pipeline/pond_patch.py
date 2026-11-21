def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a); s = s.replace(a, b)
    open(p, 'w', encoding='utf-8', newline='').write(s)
edit('tex_landmarks.py', [("white_grid('lm_metropol.png', 3.2, 3.45, (232, 232, 228), (58, 70, 84), 1.5, 1.7, 3.2, 0.9)",
"""def ribbon(nm, tw, th, wall, glass_c, band, sill, mull):
    # one floor: a continuous dark glass ribbon `band` m high over a white spandrel, faint mullions every `mull` m
    W, H = int(tw * PX), int(th * PX); a = np.zeros((H, W, 3), np.float32) + np.array(wall, np.float32)
    a += noise(H, W, 5)[..., None]
    y0 = int((th - sill - band) * PX); y1 = y0 + int(band * PX)
    g = np.zeros((y1 - y0, W, 3), np.float32) + np.array(glass_c, np.float32)
    g += noise(y1 - y0, W, 6)[..., None] + np.linspace(14, -6, y1 - y0)[:, None, None]   # sky reflection brighter at the top
    for k in range(int(round(tw / mull))): x = int(k * mull * PX); g[:, x:x + 3] = np.array(wall, np.float32) * 0.62
    a[y0:y1] = g; a[y0:y0 + int(0.1 * PX)] *= 0.72; a[y1:y1 + int(0.06 * PX)] *= 0.86   # head shadow, sill line
    save(nm, a, [tw, th])
ribbon('lm_metropol.png', 3.0, 3.45, (232, 232, 228), (52, 64, 78), 1.2, 1.0, 1.5)   # texture session: horizontal glass bands, white spandrels""")])
edit('prep.py', [("""            col = PAL['path'] if hw in ('footway', 'path', 'cycleway', 'pedestrian') else PAL['road']
            dr.line(P(pts), fill=tuple(col), width=max(1, int(wd / PX)))""",
"""            if hw not in ('footway', 'path', 'cycleway', 'pedestrian'):   # paths are their own crisp mesh (surf.py), never a blurred paint line
                dr.line(P(pts), fill=tuple(PAL['road']), width=max(1, int(wd / PX)))""")])
edit('surf.py', [("ROAD = ROAD.difference(WATER)   # no road surface on open water (bridges are decks in scene.py)",
"""ROAD = ROAD.difference(WATER)   # no road surface on open water (bridges are decks in scene.py)
PW = {'footway': 2.5, 'path': 2.0, 'cycleway': 2.5, 'pedestrian': 6.0}
_pl = []
for el in js:
    t = el.get('tags', {})
    if el['type'] != 'way' or t.get('highway') not in PW or t.get('area') == 'yes': continue
    if t.get('tunnel', 'no') != 'no' or t.get('location') == 'underground' or t.get('covered') == 'yes' or (t.get('bridge') and t.get('bridge') != 'no'): continue
    pts = ring(el)
    if len(pts) > 1: _pl.append(LineString(pts).buffer(PW[t['highway']] / 2, quad_segs=3))
PATH = unary_union(_pl).intersection(CLIP).difference(ROAD.buffer(0.05)).difference(WATER) if _pl else Polygon()
REED = WATER.buffer(1.5, quad_segs=3).difference(WATER).difference(ROAD).difference(PATH).intersection(CLIP)   # 1.5 m reed and grass fringe on every bank"""),
("        m = tri(p, 10.0); m['z'] = float(min(bz)) - 0.1 if bz else 0.0; out.append(m)",
 "        m = tri(p, 10.0); m['z'] = float(min(bz)) - 0.05 if bz else 0.0; m['still'] = p.area < 200000; out.append(m)   # lowest shore point - 5 cm; ponds are still water, the Swan is not"),
("SURF = {'road': tri(ROAD, 4.0),", "SURF = {'path': tri(PATH, 3.0), 'reed': tri(REED, 3.0), 'road': tri(ROAD, 4.0),")])
edit('scene.py', [("    Z[_sel] = np.minimum(Z[_sel], _w['z'] - 0.6)", "    Z[_sel] = np.minimum(Z[_sel], _w['z'] - 0.15)   # only grid points inside the water, 15 cm under it: shallow banks"),
("& (_gm[_iy, _ix, 1] > 0.05)", "& (_gm[_iy, _ix, 1] > 0.5)"),
("""_wm = mat_img('swan_water', BGT + 'perth/perth_swan_water.png', 0.08)
for k_, w_ in enumerate(_SF['water']): surf_obj('bg_water_%d' % k_, w_, _wm, 0.0, 60.0, z=w_['z'])""",
"""def mat_tint(nm, path, col, rough, ior=None):   # hand-made texture x a flat colour
    mm = mat_img(nm, path, rough); nt_ = mm.node_tree; bb = nt_.nodes['Principled BSDF']; src = bb.inputs['Base Color'].links[0].from_socket
    mx = nt_.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs[7].default_value = (*col, 1); nt_.links.new(src, mx.inputs[6]); nt_.links.new(mx.outputs[2], bb.inputs['Base Color'])
    if ior: bb.inputs['IOR'].default_value = ior
    return mm
_wm = mat_tint('swan_water', BGT + 'perth/perth_swan_water.png', (1, 1, 1), 0.15, 1.33)
_wp = mat_tint('pond_water', BGT + 'perth/perth_swan_water.png', (0.7, 0.7, 0.7), 0.15, 1.33)   # still ponds: base x 0.7
for k_, w_ in enumerate(_SF['water']): surf_obj('bg_water_%d' % k_, w_, _wp if w_.get('still') else _wm, 0.0, 60.0, z=w_['z'])
_SD = BGT + 'perth/perth_sand_detail.png'
surf_obj('bg_reed', _SF['reed'], mat_tint('reed_fringe', _SD, [c * 0.85 * 1.78 for c in srgb(PAL['lawn'])], 0.9), 0.06, 8.0)   # lawn darkened 15%
surf_obj('bg_path', _SF['path'], mat_tint('footpath', _SD, [c * 1.78 for c in srgb(PAL['path'])], 0.85), 0.08, 8.0)""")])
print('ok')
