import re
P = 'scene.py'
s = open(P, newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'
def L(t): return t.replace('\n', nl)

# 1) water mask + bank, right after the pad_box sink
anchor = "V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)" + nl + "ii = np.arange(n - 1)"
assert s.count(anchor) == 1
water = L('''# water: a flat surface at spec water_z_m over every cell painted water; bed kept 3 m under it, a 15 m land rim at boardwalk height (water + 2 m)
WZ = spec.get('water_z_m')
if WZ is not None:
    _im = bpy.data.images.load(os.path.join(D, 'ground.png')); _w, _h = _im.size
    _G = (np.array(_im.pixels[:], np.float32).reshape(_h, _w, 4)[..., :3] * 255).round()   # rows bottom-up = south first
    _W = np.abs(_G - np.array(spec['palette']['water'], np.float32)).sum(2) < 12
    _ri = (np.arange(n) * _h / n).astype(int); _ci = (np.arange(n) * _w / n).astype(int)
    WG = _W[_ri][:, _ci]
    _d = WG.copy()
    for _ in range(2):
        _e = _d.copy(); _e[1:] |= _d[:-1]; _e[:-1] |= _d[1:]; _e[:, 1:] |= _d[:, :-1]; _e[:, :-1] |= _d[:, 1:]; _d = _e
    _rim = _d & ~WG
    Z[WG] = np.minimum(Z[WG], WZ - 3.0); Z[_rim] = np.maximum(Z[_rim], WZ + 2.0)
''')
s = s.replace(anchor, water + anchor)

# 2) water mesh after the near ground object
anchor2 = "for p in ob.data.polygons: p.use_smooth = True" + nl + nl + "# ---------- far terrain"
assert s.count(anchor2) == 1, s.count(anchor2)
wm = L('''if WZ is not None:
    _ix = np.argwhere(WG); wv = []; wf = []
    for j, i in _ix:
        x0, y0 = i * NS - NE - NS / 2, j * NS - NE - NS / 2; o = len(wv)
        wv += [(x0, y0, WZ), (x0 + NS, y0, WZ), (x0 + NS, y0 + NS, WZ), (x0, y0 + NS, WZ)]; wf.append((o, o + 1, o + 2, o + 3))
    wmat = mat_img('water', os.path.join(HERE, 'tex', 'mv_water.png'), 0.06)
    _wn = wmat.node_tree; _wb = _wn.nodes['Principled BSDF']
    _nn = _wn.nodes.new('ShaderNodeTexImage'); _nn.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'mv_water_n.png')); _nn.image.colorspace_settings.name = 'Non-Color'
    _nm = _wn.nodes.new('ShaderNodeNormalMap'); _nm.inputs['Strength'].default_value = 0.6
    _wn.links.new(_nn.outputs['Color'], _nm.inputs['Color']); _wn.links.new(_nm.outputs['Normal'], _wb.inputs['Normal'])
    wob = mk_obj('bg_water', wv, wf, wmat)
    _wl = np.array(wf).ravel(); _WV = np.array(wv)
    set_uv(wob.data, np.stack([_WV[_wl, 0] / 16.0, _WV[_wl, 1] / 16.0], 1))   # one tile = 16 m
    print('water cells', len(wf), 'z', WZ)
''')
s = s.replace(anchor2, "for p in ob.data.polygons: p.use_smooth = True" + nl + wm + nl + "# ---------- far terrain")

# 3) Norfolk Island pines on named streets (spec pine_streets), straight trunk + flat tiers
a3 = "kinds = spec['tree_kinds']" + nl
assert s.count(a3) == 1
pine = L('''kinds = list(spec['tree_kinds'])
if spec.get('pine_streets'):
    _O = json.load(open(os.path.join(os.path.dirname(D.rstrip('/\\\\')), 'osm.json'), encoding='utf8'))['elements']
    _segs = []
    for e in _O:
        t = e.get('tags', {})
        if e['type'] == 'way' and t.get('highway') and t.get('name') in spec['pine_streets'] and e.get('geometry'):
            q = [((p['lon'] - spec['lon']) * 111320 * math.cos(math.radians(spec['lat'])), (p['lat'] - spec['lat']) * 110996) for p in e['geometry']]
            _segs += list(zip(q[:-1], q[1:]))
    A = np.array([a for a, b in _segs]); B_ = np.array([b for a, b in _segs]); dd = B_ - A
    def _dseg(x, y):
        tt = np.clip(((x - A[:, 0]) * dd[:, 0] + (y - A[:, 1]) * dd[:, 1]) / np.maximum((dd ** 2).sum(1), 1e-6), 0, 1)
        return np.hypot(A[:, 0] + tt * dd[:, 0] - x, A[:, 1] + tt * dd[:, 1] - y).min()
    kinds.append('norfolk'); _k = len(kinds) - 1; _np = 0
    for row in TR:
        if _dseg(row[0], row[1]) < spec.get('pine_dist_m', 12): row[2] = _k; _np += 1
    print('norfolk pines', _np, 'segments', len(_segs))
''')
s = s.replace(a3, pine)

# Norfolk shape inside the per-tree loop
a4 = "        s = rng.uniform(0.75, 1.25); z0 = float(height(x, y)) - 0.2" + nl
assert s.count(a4) == 1
nf = L('''        if kn == 'norfolk':
            s = rng.uniform(0.85, 1.15); z0 = float(height(x, y)) - 0.2; Ht = 18.0 * s
            o = len(verts); T = tv * [0.3 * s, 0.3 * s, Ht] + [x, y, z0]
            verts += T.tolist(); faces += [tuple(o + q for q in f) for f in tf]; cols += [lin(tcol)] * (4 * len(tf))
            nt_ = 7
            for k in range(nt_):                      # flat whorls, widest low, 1 m at the top
                fz = 0.35 + 0.62 * k / (nt_ - 1); rr = (3.6 - 2.6 * k / (nt_ - 1)) * s * rng.uniform(0.9, 1.1)
                o = len(verts); Cv = cv * [rr, rr, 0.55 * s] + [x, y, z0 + Ht * fz]
                verts += Cv.tolist(); faces += [tuple(o + q for q in f) for f in cf]
                cols += [lin(ccol) * rng.uniform(0.9, 1.08)] * (3 * len(cf))
            continue
''')
s = s.replace(a4, nf + a4)
# KIND entry
a5 = " 'plane': (5.5, 12.0, 0.9, 6.5, 0.4, (86, 110, 60), (150, 140, 120), 1)," + nl
assert s.count(a5) == 1
s = s.replace(a5, a5 + " 'norfolk': (3.6, 12.0, 0.2, 18.0, 0.3, (52, 80, 50), (112, 96, 82), 1)," + nl)
open(P, 'w', newline='').write(s)
print('ok')
