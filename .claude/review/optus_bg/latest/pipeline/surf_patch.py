p = 'scene.py'; s = open(p, encoding='utf-8').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a; s = s.replace(a, b)
# ground material: asphalt and water now live on their own meshes; keep the sand detail only
i0 = s.index("_mk = _nt.nodes.new('ShaderNodeTexImage')"); i1 = s.index("_dt = _tile(BGT + 'perth/perth_sand_detail.png', 8.0)")
s = s[:i0] + s[i1:]
# terrain: sink under road and water surfaces so the meshes always sit on top
rep("V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)\n",
"""_SF = json.load(open(os.path.join(D, 'surfaces.json')))
_gi = bpy.data.images.load(os.path.join(D, 'ground_mask.png')); _gi.colorspace_settings.name = 'Non-Color'; _r = _gi.size[1]
_gm = np.empty(len(_gi.pixels), np.float32); _gi.pixels.foreach_get(_gm); _gm = _gm.reshape(_r, _gi.size[0], 4)   # rows run south to north
_ix = np.clip(((X + NE) / (2 * NE) * _r).astype(int), 0, _r - 1); _iy = np.clip(((Y + NE) / (2 * NE) * _r).astype(int), 0, _r - 1)
Z0 = Z.copy()   # the drape height for the surfaces
Z[_gm[_iy, _ix, 0] > 0.05] -= 0.3
for _w in _SF['water']:
    _wv = np.array(_w['v']); 
    if not len(_wv): continue
    _sel = (X > _wv[:, 0].min() - NS) & (X < _wv[:, 0].max() + NS) & (Y > _wv[:, 1].min() - NS) & (Y < _wv[:, 1].max() + NS) & (_gm[_iy, _ix, 1] > 0.05)
    Z[_sel] = np.minimum(Z[_sel], _w['z'] - 0.6)
V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
""")
rep("ob.data.uv_layers.new(name='UVDetail'); _ud.data.foreach_set('uv', (uv * (2 * NE / 4.0)).astype(np.float32).ravel())\nfor p in ob.data.polygons: p.use_smooth = True\n",
"""ob.data.uv_layers.new(name='UVDetail'); _ud.data.foreach_set('uv', (uv * (2 * NE / 4.0)).astype(np.float32).ravel())
for p in ob.data.polygons: p.use_smooth = True

# ---------- roads and water as their own meshes (OSM, surf.py) ----------
def drape(xy):
    gx = (xy[:, 0] + NE) / NS; gy = (xy[:, 1] + NE) / NS
    i0 = np.clip(np.floor(gx).astype(int), 0, n - 2); j0 = np.clip(np.floor(gy).astype(int), 0, n - 2); fx = np.clip(gx - i0, 0, 1); fy = np.clip(gy - j0, 0, 1)
    return (Z0[j0, i0] * (1 - fx) * (1 - fy) + Z0[j0, i0 + 1] * fx * (1 - fy) + Z0[j0 + 1, i0] * (1 - fx) * fy + Z0[j0 + 1, i0 + 1] * fx * fy)
def surf_obj(nm, m, mat, lift, tile, z=None):
    if not m['t']: return None
    xy = np.array(m['v'], float); zz = np.full(len(xy), z) if z is not None else drape(xy) - 0.15 + lift
    o = mk_obj(nm, np.column_stack([xy, zz]).tolist(), m['t'], mat)
    lp = np.array(m['t']).ravel(); set_uv(o.data, (xy[lp] / tile).tolist()); return o
def mat_white(nm, col):
    mm = bpy.data.materials.new(nm); mm.use_nodes = True; bb = mm.node_tree.nodes['Principled BSDF']
    bb.inputs['Base Color'].default_value = (*srgb(col), 1); bb.inputs['Roughness'].default_value = 0.7; return mm
surf_obj('bg_road', _SF['road'], mat_img('road_asphalt', BGT + 'mt/road_asphalt_v2.png', 0.85), 0.05, 8.0)
surf_obj('bg_road_edge', _SF['edge'], mat_white('road_line', (232, 232, 226)), 0.07, 1.0)
surf_obj('bg_road_centre', _SF['centre'], mat_white('road_line', (232, 232, 226)) if 'road_line' not in bpy.data.materials else bpy.data.materials['road_line'], 0.07, 1.0)
_wm = mat_img('swan_water', BGT + 'perth/perth_swan_water.png', 0.08)
for k_, w_ in enumerate(_SF['water']): surf_obj('bg_water_%d' % k_, w_, _wm, 0.0, 60.0, z=w_['z'])
""")
open(p, 'w', encoding='utf-8', newline='').write(s); print('ok')
