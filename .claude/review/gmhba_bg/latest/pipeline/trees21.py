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
_pick = rng.choice(len(_names), size=len(TR), p=_w)
G = {k: ([], [], []) for k in _names}   # verts, faces, cols
def _put(k, V, F, c):
    v, f, cl = G[k]; o = len(v); v += V.tolist(); f += [tuple(o + q for q in fc) for fc in F]; cl += [c] * sum(len(fc) for fc in F)
def _rot(V, a): c, s = math.cos(a), math.sin(a); return np.stack([V[:, 0] * c - V[:, 1] * s, V[:, 0] * s + V[:, 1] * c, V[:, 2]], 1)
def _blob(k, x, y, z, rx, rz, a, col):
    V = (ICO1 + rng.normal(0, 0.13, ICO1.shape)) * [rx, rx * rng.uniform(0.8, 1.2), rz]; _put(k, _rot(V, a) + [x, y, z], ICO1F, col)
def _trunk(k, x, y, z, r, h, col, lean=(0, 0)):
    V = TRK * [r, r, h]; V[6:, :] = V[6:, :]; V[1::2, 0] += lean[0]; V[1::2, 1] += lean[1]; _put(k, V + [x, y, z], TRKF, col)
for (x, y, _k), si in zip(TR, _pick):
    k = _names[si]; _, (s0, s1), cc, bc = SPECIES[k]; s = rng.uniform(s0, s1); z0 = float(height(x, y)) - 0.2; a = rng.uniform(0, 2 * math.pi)
    jit = rng.uniform(0.86, 1.14); hue = rng.uniform(-0.05, 0.05)
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
