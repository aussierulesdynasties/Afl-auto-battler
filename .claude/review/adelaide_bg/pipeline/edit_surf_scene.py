p = 'scene.py'; s = open(p, encoding='utf-8').read()
def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90]); s = s.replace(old, new)

# A. helpers
rep("""def set_uv(me, uvs):
    uv = me.uv_layers.new(name='UVMap'); uv.data.foreach_set('uv', np.asarray(uvs, np.float32).ravel())
""", """def set_uv(me, uvs):
    uv = me.uv_layers.new(name='UVMap'); uv.data.foreach_set('uv', np.asarray(uvs, np.float32).ravel())
def set_uv_box(me, scale):   # UV = object position x scale, projected on each face's dominant axis
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    vi = np.zeros(len(me.loops), int); me.loops.foreach_get('vertex_index', vi)
    nr = np.zeros(len(me.polygons) * 3); me.polygons.foreach_get('normal', nr); nr = np.abs(nr.reshape(-1, 3))
    tot = np.zeros(len(me.polygons), int); me.polygons.foreach_get('loop_total', tot)
    ax = np.repeat(np.argmax(nr, 1), tot); p = co[vi]
    u = np.where(ax == 0, p[:, 1], p[:, 0]); v = np.where(ax == 2, p[:, 1], p[:, 2])
    set_uv(me, np.stack([u, v], 1) * scale)
""")
rep("""    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path)
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = rough""",
"""    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = rough""")

# B. water: sink the terrain 0.15 m under each water surface
rep("""V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
ii = np.arange(n - 1)""", """_SF = json.load(open(os.path.join(D, 'surfaces.json')))
_gi = bpy.data.images.load(os.path.join(D, 'ground_mask.png')); _gi.colorspace_settings.name = 'Non-Color'; _r = _gi.size[1]
_gm = np.empty(len(_gi.pixels), np.float32); _gi.pixels.foreach_get(_gm); _gm = _gm.reshape(_r, _gi.size[0], 4)   # rows run south to north
_ix = np.clip(((X + NE) / (2 * NE) * _r).astype(int), 0, _r - 1); _iy = np.clip(((Y + NE) / (2 * NE) * _r).astype(int), 0, _r - 1)
for _w in _SF['water']:
    _wv = np.array(_w['v'])
    if not len(_wv): continue
    _sel = (X > _wv[:, 0].min() - NS) & (X < _wv[:, 0].max() + NS) & (Y > _wv[:, 1].min() - NS) & (Y < _wv[:, 1].max() + NS) & (_gm[_iy, _ix, 1] > 0.5)
    Z[_sel] = np.minimum(Z[_sel], _w['z'] - 0.15)
Z0 = Z.copy()
V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
ii = np.arange(n - 1)""")

# C. ground detail: second sample at 0.37x, rotated 36.87 deg, 50/50; contrast x1.414 round the mean; fade to the mean 150-400 m
rep("""_dt = _nt.nodes.new('ShaderNodeTexImage'); _dt.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'ground_detail.png'))
_mp = _nt.nodes.new('ShaderNodeMapping'); _tc = _nt.nodes.new('ShaderNodeTexCoord')
_mp.inputs['Scale'].default_value = (2 * NE / 4.0, 2 * NE / 4.0, 1)   # one detail tile = 4 m
_nt.links.new(_tc.outputs['UV'], _mp.inputs['Vector']); _nt.links.new(_mp.outputs['Vector'], _dt.inputs['Vector'])
_mx = _nt.nodes.new('ShaderNodeMix'); _mx.data_type = 'RGBA'; _mx.blend_type = 'MULTIPLY'; _mx.inputs['Factor'].default_value = 1.0
_nt.links.new(_base, _mx.inputs[6]); _nt.links.new(_dt.outputs['Color'], _mx.inputs[7])""",
"""_uvd = _nt.nodes.new('ShaderNodeUVMap'); _uvd.uv_map = 'UVDetail'   # UVDetail: 1 unit = 4 m = one detail tile
_dt = _nt.nodes.new('ShaderNodeTexImage'); _dt.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'ground_detail.png'))
_nt.links.new(_uvd.outputs['UV'], _dt.inputs['Vector'])
_DM = 0.651   # linear mean of ground_detail.png
_mp2 = _nt.nodes.new('ShaderNodeMapping'); _mp2.inputs['Scale'].default_value = (0.37,) * 3; _mp2.inputs['Rotation'].default_value = (0, 0, math.radians(36.87))
_nt.links.new(_uvd.outputs['UV'], _mp2.inputs['Vector'])
_dt2 = _nt.nodes.new('ShaderNodeTexImage'); _dt2.image = _dt.image; _nt.links.new(_mp2.outputs['Vector'], _dt2.inputs['Vector'])
_avg = _nt.nodes.new('ShaderNodeMix'); _avg.data_type = 'RGBA'; _avg.inputs['Factor'].default_value = 0.5
_nt.links.new(_dt.outputs['Color'], _avg.inputs[6]); _nt.links.new(_dt2.outputs['Color'], _avg.inputs[7])
_ct = _nt.nodes.new('ShaderNodeMix'); _ct.data_type = 'RGBA'; _ct.blend_type = 'MIX'; _ct.clamp_factor = False; _ct.clamp_result = True; _ct.inputs['Factor'].default_value = 1.414
_ct.inputs[6].default_value = (_DM, _DM, _DM, 1); _nt.links.new(_avg.outputs[2], _ct.inputs[7])   # mean + (c - mean) x 1.414
_cd = _nt.nodes.new('ShaderNodeCameraData'); _mr = _nt.nodes.new('ShaderNodeMapRange')
_mr.inputs['From Min'].default_value = 150.0; _mr.inputs['From Max'].default_value = 400.0
_nt.links.new(_cd.outputs['View Distance'], _mr.inputs['Value'])
_fd = _nt.nodes.new('ShaderNodeMix'); _fd.data_type = 'RGBA'; _fd.inputs[7].default_value = (_DM, _DM, _DM, 1)
_nt.links.new(_mr.outputs['Result'], _fd.inputs['Factor']); _nt.links.new(_ct.outputs[2], _fd.inputs[6])
_mx = _nt.nodes.new('ShaderNodeMix'); _mx.data_type = 'RGBA'; _mx.blend_type = 'MULTIPLY'; _mx.inputs['Factor'].default_value = 1.0
_nt.links.new(_base, _mx.inputs[6]); _nt.links.new(_fd.outputs[2], _mx.inputs[7])""")

# D + E. UVDetail layer; road, paving, water, Oval No.2 meshes draped on the terrain
rep("""set_uv(ob.data, uv)
for p in ob.data.polygons: p.use_smooth = True
""", """set_uv(ob.data, uv)
_ud = ob.data.uv_layers.new(name='UVDetail'); _ud.data.foreach_set('uv', (uv * (2 * NE / 4.0)).astype(np.float32).ravel())
for p in ob.data.polygons: p.use_smooth = True
_GROUND = ob

# ---------- roads, paving, water and Oval No.2 as their own meshes (OSM, surf.py) ----------
import mathutils, mathutils.bvhtree
_dg = bpy.context.evaluated_depsgraph_get(); _bvh = mathutils.bvhtree.BVHTree.FromObject(_GROUND, _dg)
def drape(xy):   # exact height of the terrain surface: ray down onto the ground mesh
    out = np.empty(len(xy))
    for k, (x, y) in enumerate(xy):
        hit = _bvh.ray_cast(mathutils.Vector((x, y, 500.0)), mathutils.Vector((0, 0, -1)))
        out[k] = hit[0].z if hit[0] is not None else float(height(x, y))
    return out
def surf_obj(nm, m, mat, lift, tile, z=None, seg=2.5):
    if not m['t']: return None
    xy = np.array(m['v'], float)
    o = mk_obj(nm, np.column_stack([xy, np.zeros(len(xy))]).tolist(), m['t'], mat); me = o.data
    if z is None:   # cut every edge to <= seg m so the drape follows the ground inside wide surfaces too
        bm = bmesh.new(); bm.from_mesh(me)
        for _ in range(10):
            long_ = [e for e in bm.edges if e.calc_length() > seg]
            if not long_: break
            bmesh.ops.subdivide_edges(bm, edges=long_, cuts=1, use_grid_fill=False); bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(me); bm.free()
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    co[:, 2] = z if z is not None else drape(co[:, :2]) + lift
    me.vertices.foreach_set('co', co.ravel()); me.update()
    lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
    set_uv(me, co[lv, :2] / tile); print('surface', nm, len(me.polygons), 'tris'); return o
def mat_tint(nm, path, col, rough):   # hand-made texture x a flat colour (linear)
    mm = mat_img(nm, path, rough); nt_ = mm.node_tree; bb = nt_.nodes['Principled BSDF']; src = bb.inputs['Base Color'].links[0].from_socket
    mx = nt_.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs[7].default_value = (*col, 1); nt_.links.new(src, mx.inputs[6]); nt_.links.new(mx.outputs[2], bb.inputs['Base Color'])
    return mm
def mat_white(nm, col):
    mm = bpy.data.materials.new(nm); mm.use_nodes = True; bb = mm.node_tree.nodes['Principled BSDF']
    bb.inputs['Base Color'].default_value = (*srgb(col), 1); bb.inputs['Roughness'].default_value = 0.7; return mm
_TX = os.path.join(HERE, 'tex')
_rl = mat_white('road_line', (232, 232, 226))
surf_obj('bg_road', _SF['road'], mat_tint('road_asphalt', os.path.join(_TX, 'road_asphalt_v2.png'), [c / 0.425 for c in srgb((86, 86, 84))], 0.85), 0.05, 8.0)   # asphalt / its linear mean 0.425
surf_obj('bg_road_edge', _SF['edge'], _rl, 0.07, 1.0)
surf_obj('bg_road_centre', _SF['centre'], _rl, 0.07, 1.0)
surf_obj('bg_paving', _SF['path'], mat_tint('paving', os.path.join(_TX, 'mv_plaza_pavers.png'), [c / 0.534 for c in srgb(PAL['path'])], 0.85), 0.05, 6.0)   # pavers / linear mean 0.534
_wmat = mat_img('torrens_water', os.path.join(_TX, 'adl_torrens_water.png'), 0.35)
for k_, w_ in enumerate(_SF['water']): surf_obj('bg_water_%d' % k_, w_, _wmat, 0.0, 40.0, z=w_['z'])
surf_obj('bg_oval2_skin', _SF['oval2'], mat_img('oval2_dirt', os.path.join(_TX, 'adl_dry_grain.png'), 0.95), 0.04, 6.0)
""")

# F. roofs: >= 1500 m2 roof_far (24 m tile); smaller flat roofs corrugated (3.04 m, ribs along the long axis); roof_col_at tints
rep("""        src = b.get('roof_c'); kind = 'tile' if""", """        src = b.get('roof_c'); kind = 'far' if b.get('a', 0) >= 1500 else 'corr' if not pitched else 'tile' if""")
rep("""        def ruv_(x, y): return ((x * ct + y * st) / 3.04, (-x * st + y * ct) / 3.04)""",
"""        def ruv_(x, y):
            if kind == 'far': return ((x * ct + y * st) / 24.0, (-x * st + y * ct) / 24.0)
            if kind == 'corr': return ((-x * st + y * ct) / 3.04, (x * ct + y * st) / 3.04)   # texture ribs run along v = the long axis
            return ((x * ct + y * st) / 3.04, (-x * st + y * ct) / 3.04)""")
rep("""    RF = {'metal': [[], [], [], []], 'tile': [[], [], [], []]}""", """    RF = {'metal': [[], [], [], []], 'tile': [[], [], [], []], 'far': [[], [], [], []], 'corr': [[], [], [], []]}""")
rep("""        ro = mk_obj('bg_roof_%s_%s' % (cls, kind), rv, rf, mat_facade('roof_%s_%s' % (cls, kind), os.path.join(HERE, 'tex', 'roof_%s.png' % kind)))""",
"""        ro = mk_obj('bg_roof_%s_%s' % (cls, kind), rv, rf, mat_roof(kind) if kind in ('far', 'corr') else mat_facade('roof_%s_%s' % (cls, kind), os.path.join(HERE, 'tex', 'roof_%s.png' % kind)))""")
rep("""def build_class(cls, tex, tw, th):""", """def mat_roof(kind):   # hand-made roof texture / its linear mean x the roof colour (vertex colour)
    nm = 'roof_' + kind
    if nm in bpy.data.materials: return bpy.data.materials[nm]
    fn, mean = {'far': ('roof_far.png', 0.594), 'corr': ('roof_corrugated.png', 0.544)}[kind]
    m = bpy.data.materials.new(nm); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(HERE, 'tex', fn), check_existing=True)
    ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'Col'
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1
    nt.links.new(ca.outputs['Color'], mul.inputs[6]); nt.links.new(t.outputs['Color'], mul.inputs[7])
    nm_ = nt.nodes.new('ShaderNodeMix'); nm_.data_type = 'RGBA'; nm_.blend_type = 'MULTIPLY'; nm_.inputs[0].default_value = 1
    nm_.inputs[7].default_value = (1 / mean, 1 / mean, 1 / mean, 1); nt.links.new(mul.outputs[2], nm_.inputs[6])
    nt.links.new(nm_.outputs[2], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.7
    return m
def build_class(cls, tex, tw, th):""")

# G. trees: baked leaf clumps (tex/leaf_clumps.png + leaf_normal.png from tex_bake.py) instead of live Voronoi
rep("""    tc = nt.nodes.new('ShaderNodeTexCoord'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 2.8
    vo.feature = 'F1'; nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Max'].default_value = 0.6; mr.inputs['To Min'].default_value = 1.15; mr.inputs['To Max'].default_value = 0.62
    nt.links.new(vo.outputs['Distance'], mr.inputs['Value'])
""", """    lt = nt.nodes.new('ShaderNodeTexImage'); lt.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'leaf_clumps.png'))
""")
rep("""    nt.links.new(vc, mx.inputs[6]); nt.links.new(mr.outputs['Result'], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6; nt.links.new(vo.outputs['Distance'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
""", """    nt.links.new(vc, mx.inputs[6]); nt.links.new(lt.outputs['Color'], mx.inputs[7])
    lf = nt.nodes.new('ShaderNodeMix'); lf.data_type = 'RGBA'; lf.blend_type = 'MULTIPLY'; lf.inputs['Factor'].default_value = 1.0
    lf.inputs[7].default_value = (1.15, 1.15, 1.15, 1)   # texture stores the clump multiplier / 1.15
    nt.links.new(mx.outputs[2], lf.inputs[6]); nt.links.new(lf.outputs[2], b.inputs['Base Color'])
    ln = nt.nodes.new('ShaderNodeTexImage'); ln.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'leaf_normal.png')); ln.image.colorspace_settings.name = 'Non-Color'
    nm_ = nt.nodes.new('ShaderNodeNormalMap'); nm_.uv_map = 'UVMap'
    nt.links.new(ln.outputs['Color'], nm_.inputs['Color']); nt.links.new(nm_.outputs['Normal'], b.inputs['Normal'])
""")
rep("""    ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))
""", """    ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))
    set_uv_box(ob.data, 2.8 / 8)   # leaf_clumps.png tile = 8 cells of 1/2.8 m
""")

# H. GLB keeps the painted ground.png as base colour (glTF cannot carry the detail graph); renders get the full graph
rep("""bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'scene_bg.glb'), export_format='GLB', use_selection=False)
""", """_gt = [n_ for n_ in _nt.nodes if n_.type == 'TEX_IMAGE' and n_.image and n_.image.name.startswith('ground.png')][0]
_nt.links.new(_gt.outputs['Color'], _b.inputs['Base Color'])
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'scene_bg.glb'), export_format='GLB', use_selection=False)
_nt.links.new(_lift.outputs[2], _b.inputs['Base Color'])
""")

# I. courts: baked grain; navy surround slab; each court a (40, 90, 150) playing area 1 m inside its OSM box (2 m between courts)
rep("""        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 900.0; nz.inputs['Detail'].default_value = 4.0
        tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.86; mr.inputs['To Max'].default_value = 1.12
        nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
""", """        gt = nt.nodes.new('ShaderNodeTexImage'); gt.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'court_grain.png'), check_existing=True)   # tex_bake.py, 0.25 m tile
""")
rep("""        mx.inputs[6].default_value = (*srgb(rgb), 1); nt.links.new(mr.outputs['Result'], mx.inputs[7])""",
    """        mx.inputs[6].default_value = (*[1.12 * c for c in srgb(rgb)], 1); nt.links.new(gt.outputs['Color'], mx.inputs[7])   # grain stored / 1.12""")
rep("""    for k, hull in cj['slabs']:
        H = np.array(hull, float); z = height(H[:, 0], H[:, 1]).max() + 0.04
        V = [(x, y, z) for x, y in H] + [(H[:, 0].mean(), H[:, 1].mean(), z)]; c = len(H)
        mk_obj('bg_court_slab_' + k, V, [[c, i, (i + 1) % c] for i in range(c)], mats[k])
""", """    _SL = []
    for k, hull in cj['slabs']:
        H = np.array(hull, float); z = height(H[:, 0], H[:, 1]).max() + 0.04; _SL.append((H, z))
        V = [(x, y, z) for x, y in H] + [(H[:, 0].mean(), H[:, 1].mean(), z)]; c = len(H)
        set_uv_box(mk_obj('bg_court_slab_' + k, V, [[c, i, (i + 1) % c] for i in range(c)], mats[k]).data, 4.0)   # grain tile 0.25 m
    def _inpoly(x, y, poly):
        c = False; n_ = len(poly)
        for i in range(n_):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n_]
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c = not c
        return c
    def _zslab(x, y):
        for H, zz in _SL:
            if _inpoly(x, y, H): return zz
        return float(height(np.array([x]), np.array([y]))[0]) + 0.04
    _play = court_mat('court_play', PAL.get('court_play', (40, 90, 150))); PV_, PF_ = [], []
    _subs = []
    for k, cx, cy, ang, L_, W_ in cj['courts']:
        ux, uy = math.cos(ang), math.sin(ang)
        if W_ >= 30:   # one OSM box round several courts side by side: split it, each court runs along the box's short side
            n_ = max(1, int(round(L_ / 17.0))); w_ = L_ / n_
            for i in range(n_):
                o_ = -L_ / 2 + w_ * (i + 0.5); _subs.append((cx + ux * o_, cy + uy * o_, ang + math.pi / 2, W_, w_))
        else: _subs.append((cx, cy, ang, L_, W_))
    cj['courts'] = [['play'] + list(q) for q in _subs]
""")
rep("""        ux, uy = math.cos(ang), math.sin(ang); z = float(height(np.array([cx]), np.array([cy]))[0]) + 0.05; nc += 1
""", """        ux, uy = math.cos(ang), math.sin(ang); zs = _zslab(cx, cy); nc += 1
        hl, hw = max(L_ / 2 - 1.0, min(L_ / 2, 12.185)), max(W_ / 2 - 1.0, min(W_ / 2, 5.785))   # 1 m inside the box; never inside the doubles lines
        wx, wy = -uy, ux; q_ = len(PV_)
        PV_.extend([(cx + ux * a_ * hl + wx * b_ * hw, cy + uy * a_ * hl + wy * b_ * hw, zs + 0.01) for a_, b_ in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]); PF_.append([q_, q_ + 1, q_ + 2, q_ + 3])
        z = zs + 0.02
""")
rep("""            NV.extend([(cx + wx * yy, cy + wy * yy, z), (cx + wx * yy, cy + wy * yy, z + hh)])""",
    """            NV.extend([(cx + wx * yy, cy + wy * yy, zs), (cx + wx * yy, cy + wy * yy, zs + hh)])""")
rep("""    if LV: mk_obj('bg_court_lines', LV, LF, white)""", """    if PV_: set_uv_box(mk_obj('bg_court_play', PV_, PF_, _play).data, 4.0)
    if LV: mk_obj('bg_court_lines', LV, LF, white)""")
open(p, 'w', encoding='utf-8').write(s); print('ok')
s = open(p, encoding='utf-8').read()
rep("        if L_ < 23.5 or W_ < 10.8: continue   # OSM box smaller than a doubles court: no lines rather than wrong ones\n",
    "        if L_ < 23.5 or W_ < 10.5: continue   # OSM box smaller than a doubles court: no lines rather than wrong ones\n")
open(p, 'w', encoding='utf-8').write(s); print('ok2')
