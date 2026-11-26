# Mixed-species trees (exec'd by scene.py when spec['trees_v2']): shares TR, rng, height, lin, mat_vcol, mk_obj,
# set_uv_box, set_corner_col, HERE, bmesh, np, math, bpy. Each tree gets a species by weight; each species has its own
# crown shape, size range, canopy and bark colour, so the canopy is not one cloned blob.
def _ico(sub):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    v = np.array([q.co[:] for q in bm.verts]); f = [[q.index for q in fc.verts] for fc in bm.faces]; bm.free(); return v, f
def _cone(seg=9):
    v = [(math.cos(2 * math.pi * i / seg), math.sin(2 * math.pi * i / seg), 0.0) for i in range(seg)] + [(0, 0, 1.0), (0, 0, 0.0)]
    f = [(i, (i + 1) % seg, seg) for i in range(seg)] + [((i + 1) % seg, i, seg + 1) for i in range(seg)]
    return np.array(v, float), f
ICO1, ICO1F = _ico(1); CONE, CONEF = _cone()
TRK = np.array([(math.cos(2 * math.pi * i / 6), math.sin(2 * math.pi * i / 6), z) for i in range(6) for z in (0, 1)], float)
TRKF = [(2 * i, 2 * ((i + 1) % 6), 2 * ((i + 1) % 6) + 1, 2 * i + 1) for i in range(6)]
#        weight, size range, canopy rgb, bark rgb
SPECIES = {
 'sugar_gum':   (0.24, (0.8, 1.45), (100, 114, 80), (156, 146, 130)),   # spreading eucalypt, open clumpy crown, grey-olive
 'lemon_gum':   (0.08, (0.8, 1.3), (126, 138, 94), (232, 226, 214)),    # tall pale trunk, high narrow crown
 'elm':         (0.17, (0.75, 1.3), (72, 102, 54), (84, 72, 60)),       # broad round deciduous crown, deep green
 'plane':       (0.10, (0.7, 1.2), (92, 118, 62), (150, 140, 118)),     # rounder, brighter street tree
 'cypress':     (0.08, (0.7, 1.3), (42, 64, 44), (78, 62, 50)),         # dense dark cone (windbreaks, old yards)
 'norfolk':     (0.03, (0.8, 1.3), (50, 76, 52), (96, 82, 66)),         # tiered pine (bay front, old parks)
 'poplar':      (0.03, (0.8, 1.2), (98, 126, 64), (120, 110, 96)),      # narrow column
 'shrub':       (0.27, (0.6, 1.4), (90, 108, 66), (90, 76, 60)),        # wattle, bottlebrush, yard shrubs: low, no clear trunk
}
_names = list(SPECIES); _w = np.array([SPECIES[k][0] for k in _names]); _w /= _w.sum()
if spec.get('real'):   # real place: the trace finds trees, not shrubs; Perth/Adelaide/Melbourne streets are gums, planes and elms
    _w = np.array([SPECIES[k][0] if k in ('sugar_gum', 'lemon_gum', 'elm', 'plane') else 0.0 for k in _names]); _w /= _w.sum()
_pick = rng.choice(len(_names), size=len(TR), p=_w)
G = {k: ([], [], []) for k in _names}   # verts, faces, cols
def _put(k, V, F, c):
    v, f, cl = G[k]; o = len(v); v += V.tolist(); f += [tuple(o + q for q in fc) for fc in F]; cl += [c] * sum(len(fc) for fc in F)
def _rot(V, a): c, s = math.cos(a), math.sin(a); return np.stack([V[:, 0] * c - V[:, 1] * s, V[:, 0] * s + V[:, 1] * c, V[:, 2]], 1)
ICO0, ICO0F = _ico(0)
# the far crown: an octahedron (8 faces), a few pixels at 700 m, so the budget keeps every tree's crown
OCT = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]], float)
OCTF = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
# distance detail (a tree 500 m out is a few pixels on a phone): near trees as built; from LOD_MID their crown is its
# 3 biggest clumps as 20-face blobs; from LOD_FAR one blob the size of the whole crown and no trunk. The budget then
# keeps every tree instead of thinning the canopy.
LOD_MID, LOD_FAR = spec.get('tree_lod_m', (450.0, 1100.0))
_LOD = 0; _BUF = []
def _blob(k, x, y, z, rx, rz, a, col):
    if _LOD:
        _BUF.append((k, x, y, z, rx, rz, a, col)); return
    V = (ICO1 + rng.normal(0, 0.13, ICO1.shape)) * [rx, rx * rng.uniform(0.8, 1.2), rz]; _put(k, _rot(V, a) + [x, y, z], ICO1F, col)
def _flush():
    global _BUF
    if not _BUF: return
    B = np.array([[b[1], b[2], b[3], b[4], b[5]] for b in _BUF]); k = _BUF[0][0]; col = _BUF[0][7]
    lo = np.min(B[:, :3] - B[:, [3, 3, 4]], 0); hi = np.max(B[:, :3] + B[:, [3, 3, 4]], 0)
    if _LOD == 1:   # the whole crown as one 20-face blob
        c = (lo + hi) / 2; r = (hi - lo) / 2 * 0.92
        V = (ICO0 + rng.normal(0, 0.06, ICO0.shape)) * r; _put(k, _rot(V, _BUF[0][6]) + c, ICO0F, col)
    else:   # far: crowns merged by cell, one 8-face blob over the cell's canopy (every tree's cover kept)
        _cs = 30.0 if math.hypot(lo[0] + hi[0], lo[1] + hi[1]) < 2 * 1100 else 48.0   # 30 m cells, 48 m past 1.1 km
        key = ('elm' if 'elm' in G else k, int(math.floor((lo[0] + hi[0]) / 2 / _cs)), int(math.floor((lo[1] + hi[1]) / 2 / _cs)))
        m = _FAR.get(key)
        _ca = (hi[0] - lo[0]) * (hi[1] - lo[1]) * 0.78
        _zc, _zr = (lo[2] + hi[2]) / 2, (hi[2] - lo[2]) / 2   # this tree's crown: its middle height and half its depth
        _xc, _yc = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
        _sm = np.array([1, _xc, _yc, _zc, _xc * _xc, _xc * _yc, _yc * _yc, _xc * _zc, _yc * _zc])   # for the slope's plane
        if m is None: _FAR[key] = [lo.copy(), hi.copy(), np.array(col, float), 1, _BUF[0][6], _ca, _zc, _zr, _sm]
        else: m[0] = np.minimum(m[0], lo); m[1] = np.maximum(m[1], hi); m[2] += col; m[3] += 1; m[5] += _ca; m[6] += _zc; m[7] += _zr; m[8] = m[8] + _sm
    _BUF = []
_FAR = {}
def _far_flush():
    for (k, _, _), (lo, hi, cs, n, a, ca, zc, zr, sm) in _FAR.items():
        c = (lo + hi) / 2; r = (hi - lo) / 2 * 0.9
        f = min(1.0, math.sqrt(ca / max(1.0, 0.78 * (hi[0] - lo[0]) * (hi[1] - lo[1]))))   # the blob covers what the crowns covered
        # its height is the crowns' own depth at their mean height, not the cell's whole height range: on a hillside
        # that range takes in the slope and the blob stood up as a spike, so ridges read as a sawtooth
        c[2] = zc / n; r = np.array([r[0] * f, r[1] * f, min(r[2], 1.15 * zr / n)])
        V = _rot((OCT + rng.normal(0, 0.05, OCT.shape)) * r, a)
        # laid along the slope: the plane through the crowns' middles (a flat blob on a steep town belt stood out of the
        # hill as a dark shelf, shards on the skyline)
        N_, X_, Y_, Z_, XX, XY, YY, XZ, YZ = sm; gx_ = gy_ = 0.0
        if N_ >= 3:
            A_ = np.array([[XX - X_ * X_ / N_, XY - X_ * Y_ / N_], [XY - X_ * Y_ / N_, YY - Y_ * Y_ / N_]])
            b_ = np.array([XZ - X_ * Z_ / N_, YZ - Y_ * Z_ / N_])
            if abs(np.linalg.det(A_)) > 1e-3 * max(1.0, A_.trace()) ** 2: gx_, gy_ = np.clip(np.linalg.solve(A_, b_), -1.5, 1.5)
        c[0], c[1] = X_ / N_, Y_ / N_
        V[:, 2] += gx_ * V[:, 0] + gy_ * V[:, 1]
        _put(k, V + c, OCTF, tuple(cs / n))
def _trunk(k, x, y, z, r, h, col, lean=(0, 0)):
    if _LOD: return
    V = TRK * [r, r, h]; V[6:, :] = V[6:, :]; V[1::2, 0] += lean[0]; V[1::2, 1] += lean[1]; _put(k, V + [x, y, z], TRKF, col)
for _t, si in zip(TR, _pick):
    x, y = _t[0], _t[1]
    _flush(); _d = math.hypot(x, y); _LOD = 0 if _d < LOD_MID else (1 if _d < LOD_FAR else 2)
    k = _names[si]; _, (s0, s1), cc, bc = SPECIES[k]; s = rng.uniform(s0, s1); z0 = float(height(x, y)) - 0.2; a = rng.uniform(0, 2 * math.pi)
    jit = rng.uniform(0.86, 1.14); hue = rng.uniform(-0.05, 0.05)
    if len(_t) >= 6 and _t[3] >= 0: cc = tuple(_t[3:6])   # real place: the crown's colour from the aerial
    col = lin(cc) * jit * np.array([1 + hue, 1, 1 - hue], np.float32); bark = lin(bc) * rng.uniform(0.9, 1.1)
    if k == 'sugar_gum':   # forked trunk, 5-7 flattened clumps spread wide and at different heights
        H = 7.5 * s; _trunk(k, x, y, z0, 0.38 * s, H * 0.75, bark)
        for i in range(rng.integers(5, 8)):
            t = a + i * 2.4; rr = rng.uniform(1.5, 4.2) * s
            _blob(k, x + math.cos(t) * rr, y + math.sin(t) * rr, z0 + H + rng.uniform(-1.6, 2.2) * s, rng.uniform(1.6, 2.6) * s, rng.uniform(0.9, 1.4) * s, t, col * rng.uniform(0.9, 1.1))
            _trunk(k, x, y, z0 + H * 0.6, 0.14 * s, H * 0.5, bark, (math.cos(t) * rr * 0.8, math.sin(t) * rr * 0.8))
    elif k == 'lemon_gum':
        H = 11.0 * s; _trunk(k, x, y, z0, 0.26 * s, H, bark, (rng.normal(0, 0.4), rng.normal(0, 0.4)))
        for i in range(3):
            t = a + i * 2.1; _blob(k, x + math.cos(t) * 1.4 * s, y + math.sin(t) * 1.4 * s, z0 + H + rng.uniform(-0.5, 2.5) * s, rng.uniform(1.5, 2.2) * s, rng.uniform(1.5, 2.2) * s, t, col)
    elif k in ('elm', 'plane'):
        R = (5.2 if k == 'elm' else 4.4) * s; H = (5.0 if k == 'elm' else 4.2) * s; _trunk(k, x, y, z0, 0.36 * s, H + R * 0.5, bark)
        for i in range(5):
            o = rng.normal(0, 0.38 * R, 2); _blob(k, x + o[0], y + o[1], z0 + H + R * rng.uniform(0.55, 1.0), R * rng.uniform(0.5, 0.65), R * rng.uniform(0.42, 0.55), a + i, col * rng.uniform(0.92, 1.08))
    elif k == 'cypress':
        H = 9.0 * s; R = 2.6 * s; _trunk(k, x, y, z0, 0.3 * s, 1.2, bark)
        _put(k, _rot(CONE * [R, R, H] + rng.normal(0, 0.12, CONE.shape) * [R, R, 0], a) + [x, y, z0 + 0.6], CONEF, col)
        _blob(k, x, y, z0 + H * 0.3, R * 1.05, H * 0.32, a, col * 0.95)
    elif k == 'norfolk':
        H = 18.0 * s; _trunk(k, x, y, z0, 0.32 * s, H, bark)
        for i in range(5):
            f = i / 5.0; R = (4.0 - 3.0 * f) * s; zt = z0 + H * (0.35 + 0.13 * i)
            _put(k, _rot(CONE * [R, R, 2.2 * s], a + i) + [x, y, zt], CONEF, col * (0.9 + 0.05 * i))
    elif k == 'poplar':
        H = 13.0 * s; _trunk(k, x, y, z0, 0.25 * s, 3.0, bark); _blob(k, x, y, z0 + H * 0.55, 1.7 * s, H * 0.48, a, col)
    else:   # shrub
        for i in range(rng.integers(1, 4)):
            o = rng.normal(0, 0.8 * s, 2); _blob(k, x + o[0], y + o[1], z0 + 1.1 * s, rng.uniform(1.1, 1.8) * s, rng.uniform(0.8, 1.2) * s, a + i, col)
_flush(); _far_flush()
for k, (verts, faces, cols) in G.items():
    if not faces: continue
    tm = mat_vcol('tree_' + k, 0.9); nt = tm.node_tree; b = nt.nodes['Principled BSDF']; vc = b.inputs['Base Color'].links[0].from_socket
    lt = nt.nodes.new('ShaderNodeTexImage'); lt.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'leaf_clumps.png'))
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    nt.links.new(vc, mx.inputs[6]); nt.links.new(lt.outputs['Color'], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    ln = nt.nodes.new('ShaderNodeTexImage'); ln.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'leaf_normal.png')); ln.image.colorspace_settings.name = 'Non-Color'
    nm_ = nt.nodes.new('ShaderNodeNormalMap'); nm_.uv_map = 'UVMap'
    nt.links.new(ln.outputs['Color'], nm_.inputs['Color']); nt.links.new(nm_.outputs['Normal'], b.inputs['Normal'])
    ob = mk_obj('bg_trees_' + k, verts, faces, tm)
    ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))
    set_uv_box(ob.data, 2.8 / 8)
    cols = np.clip(np.array(cols) * 1.15, 0, 1)
    set_corner_col(ob.data, np.concatenate([cols, np.ones((len(cols), 1))], 1))
    print('trees', k, len(faces), 'faces')
