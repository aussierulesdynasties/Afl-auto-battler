"""Build a stadium background scene in Blender from prep output.
    blender -b -P scene.py -- spec.json
Frame: x east, y north, z up, origin = oval centre at ground level. Saves out/<name>/scene.blend (with the
ground model for renders) and out/<name>/scene_bg.glb (the background only).
"""
import bpy, bmesh, json, math, os, sys
import numpy as np
from mathutils import Vector

SP = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
HERE = os.path.dirname(os.path.dirname(SP)) if os.path.basename(os.path.dirname(SP)) == 'spec' else os.path.dirname(SP)
spec = json.load(open(SP))
name = spec['name']; PAL = spec['palette']
D = os.path.join(HERE, 'data', name, 'prep'); OUT = os.path.join(HERE, 'out', name); os.makedirs(OUT, exist_ok=True)
meta = json.load(open(os.path.join(D, 'meta.json')))
rng = np.random.default_rng(spec.get('seed', 1))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
def srgb(c): return [((v / 255) / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4) for v in c]
def lin(c): return np.array(srgb(c), np.float32)

near = np.load(os.path.join(D, 'near_h.npy')); far = np.load(os.path.join(D, 'far_h.npy'))
NE, NS, FA, FS = meta['near'], meta['near_step'], meta['far'], meta['far_step']
R0 = spec['clear_r_m']
def samp(G, half, step, X, Y):
    fx = (np.asarray(X) + half) / step; fy = (np.asarray(Y) + half) / step
    i = np.clip(np.floor(fx).astype(int), 0, G.shape[1] - 2); j = np.clip(np.floor(fy).astype(int), 0, G.shape[0] - 2)
    ax = np.clip(fx - i, 0, 1); ay = np.clip(fy - j, 0, 1)
    return G[j, i] * (1 - ax) * (1 - ay) + G[j, i + 1] * ax * (1 - ay) + G[j + 1, i] * (1 - ax) * ay + G[j + 1, i + 1] * ax * ay
def height(X, Y):
    X = np.asarray(X, float); Y = np.asarray(Y, float)
    inside = (np.abs(X) < NE) & (np.abs(Y) < NE)
    return np.where(inside, samp(near, NE, NS, X, Y), samp(far, FA, FS, X, Y))

def mk_obj(nm, verts, faces, mat=None):
    me = bpy.data.meshes.new(nm)
    me.from_pydata([tuple(v) for v in verts] if not isinstance(verts, np.ndarray) else verts.tolist(), [], faces)
    me.validate(); me.update()
    ob = bpy.data.objects.new(nm, me); sc.collection.objects.link(ob)
    if mat: me.materials.append(mat)
    return ob
def set_corner_col(me, cols):  # cols: per-loop RGBA float array
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    ca.data.foreach_set('color', np.asarray(cols, np.float32).ravel())
def set_uv(me, uvs):
    uv = me.uv_layers.new(name='UVMap'); uv.data.foreach_set('uv', np.asarray(uvs, np.float32).ravel())
def set_uv_box(me, scale):   # UV = object position x scale, projected on each face's dominant axis
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    vi = np.zeros(len(me.loops), int); me.loops.foreach_get('vertex_index', vi)
    nr = np.zeros(len(me.polygons) * 3); me.polygons.foreach_get('normal', nr); nr = np.abs(nr.reshape(-1, 3))
    tot = np.zeros(len(me.polygons), int); me.polygons.foreach_get('loop_total', tot)
    ax = np.repeat(np.argmax(nr, 1), tot); p = co[vi]
    u = np.where(ax == 0, p[:, 1], p[:, 0]); v = np.where(ax == 2, p[:, 1], p[:, 2])
    set_uv(me, np.stack([u, v], 1) * scale)

def mat_vcol(nm, rough=0.85):
    m = bpy.data.materials.new(nm); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'Col'
    nt.links.new(ca.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = rough
    return m
def mat_img(nm, path, rough=0.9):
    m = bpy.data.materials.new(nm); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path)
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = rough
    return m
def mat_mul(nm, path, rough=0.8):
    """one base-colour texture x the vertex colour (the tint), as the trees do; glTF: baseColorTexture x COLOR_0."""
    m = mat_vcol(nm, rough); nt = m.node_tree; b = nt.nodes['Principled BSDF']; vc = b.inputs['Base Color'].links[0].from_socket
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path)
    t.image.alpha_mode = 'NONE'   # the alpha channel is not used here: never let Blender premultiply colour by it
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    nt.links.new(vc, mx.inputs[6]); nt.links.new(t.outputs['Color'], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    return m
def mat_facade(nm, path, rough_wall=0.8):
    """facade: glass where the texture alpha is 1, the building's own colour (vertex colour) elsewhere."""
    m = bpy.data.materials.new(nm); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path)
    ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'Col'
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1
    nt.links.new(ca.outputs['Color'], mul.inputs[6]); nt.links.new(t.outputs['Color'], mul.inputs[7])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    nt.links.new(t.outputs['Alpha'], mix.inputs[0]); nt.links.new(mul.outputs[2], mix.inputs[6]); nt.links.new(t.outputs['Color'], mix.inputs[7])
    nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    rm = nt.nodes.new('ShaderNodeMapRange'); rm.inputs['To Min'].default_value = rough_wall; rm.inputs['To Max'].default_value = 0.13
    nt.links.new(t.outputs['Alpha'], rm.inputs['Value']); nt.links.new(rm.outputs['Result'], b.inputs['Roughness'])
    return m

# ---------- near terrain ----------
# rail corridor flattened to each track's real profile before the mesh is built (rail_grade.py; coordinator OK 2026-11-20)
if spec.get('rail_geo') and os.path.exists(os.path.join(D, 'rails.json')):
    sys.path.insert(0, HERE); import rail_geo, rail_grade
    _j = lambda f: json.load(open(os.path.join(D, f))) if os.path.exists(os.path.join(D, f)) else None
    _KF = np.array(_j('footprint.json')) if spec.get('rail_cut', {}).get('keep_footprint') and _j('footprint.json') else None
    _PL = rail_geo.plan(_j('rails.json'), _KF, spec.get('rail_cut', {}).get('keep_ellipse'), _j('gantries.json'), _j('rail_extra.json'), _j('rail_shift.json'))
    near, _nm, RG_PROF, RG_UNDERS = rail_grade.apply(near, NE, NS, _PL['tracks'], _j('rail_edges.json'), _j('bridges.json') or [])
    print('rail grade: %d near-grid vertices set to the track profile' % _nm)
n = near.shape[0]
g = np.arange(n) * NS - NE
X, Y = np.meshgrid(g, g)
Z = near.copy(); Z[np.hypot(X, Y) < R0 + 5] -= 0.15
# the model's own flat ground (apron) box: sink the terrain under it so no corner pokes through
if spec.get('pad_box_m'):
    hx, hy = spec['pad_box_m']; Z[(np.abs(X) < hx + NS) & (np.abs(Y) < hy + NS)] = np.minimum(Z[(np.abs(X) < hx + NS) & (np.abs(Y) < hy + NS)], -0.3)
V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
ii = np.arange(n - 1)
I, J = np.meshgrid(ii, ii)
a = (J * n + I).ravel()
F = np.stack([a, a + 1, a + n + 1, a + n], 1)
# one texture only (glTF carries one base colour image): ground.png x ground_detail.png (4 m tile, x1.21 lift),
# baked by bake_ground.py into prep/ground_baked.png
_gb = os.path.join(D, 'ground_baked.png'); assert os.path.exists(_gb), 'run bake_ground.py ' + name + ' first'
gm = mat_img('ground', _gb, 0.8)
ob = mk_obj('bg_near_ground', V, F.tolist(), gm)
loops = F.ravel()
uv = np.stack([(V[loops, 0] + NE) / (2 * NE), (V[loops, 1] + NE) / (2 * NE)], 1)
set_uv(ob.data, uv)
for p in ob.data.polygons: p.use_smooth = True
# steep banks: a top-down image stretches down a slope, so faces steeper than ~35 deg move to their own object with
# a box-projected hand-made bank texture (tex/bank_grass.png, 8 m tile)
_nz = np.zeros(len(ob.data.polygons) * 3); ob.data.polygons.foreach_get('normal', _nz); _st = np.abs(_nz.reshape(-1, 3)[:, 2]) < 0.82
if _st.any():
    import bmesh as _bm
    bv = V; bf = F[_st]; used = np.unique(bf); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    ob2 = mk_obj('bg_banks', V[used].tolist(), remap[bf].tolist(), mat_img('bank', os.path.join(HERE, 'tex', 'bank_grass.png'), 0.95))
    set_uv_box(ob2.data, 1 / 8.0)
    for p in ob2.data.polygons: p.use_smooth = True
    for o_ in (ob2,): o_.location.z += 0.05
    print('banks', int(_st.sum()), 'faces')

# ---------- rails: continuous tracks from merged OSM ways (rail_geo.py), checked top-down on the aerial (rail_check.py) ----------
# per track: ballast shoulder 8 m wide (flush at the edges, 0.12 m crown; neighbours < 6 m apart overlap into one bed),
# sleeper bed 3.2 m (concrete sleepers every 0.65 m, tex/track_bed.png), two steel rails at 1.6 m gauge, contact wire 5.6 m up;
# portal gantries where the aerial shows them (data prep/gantries.json), masts every 37 m on the other lines
RLP = os.path.join(D, 'rails.json')
if spec.get('rail_geo') and os.path.exists(RLP):
    sys.path.insert(0, HERE); import rail_geo
    RF = np.load(os.path.join(D, 'rail_floor.npy')) if os.path.exists(os.path.join(D, 'rail_floor.npy')) else None
    KE = spec.get('rail_cut', {}).get('keep_ellipse')
    KFP = os.path.join(D, 'footprint.json')
    KF = np.array(json.load(open(KFP))) if spec.get('rail_cut', {}).get('keep_footprint') and os.path.exists(KFP) else None
    GP = os.path.join(D, 'gantries.json')
    XP = os.path.join(D, 'rail_extra.json')
    PLAN = rail_geo.plan(json.load(open(RLP)), KF, KE, json.load(open(GP)) if os.path.exists(GP) else None, json.load(open(XP)) if os.path.exists(XP) else None, json.load(open(os.path.join(D, 'rail_shift.json'))) if os.path.exists(os.path.join(D, 'rail_shift.json')) else None)
    ZT = near.copy(); ZT[np.hypot(*np.meshgrid(np.arange(near.shape[0]) * NS - NE, np.arange(near.shape[0]) * NS - NE)) < R0 + 5] -= 0.15
    def zfloor(X, Y):
        # top of the terrain mesh as drawn: the near grid is 7.5 m quads that may split on either diagonal, so take the
        # highest of the bilinear and both triangle surfaces; anything laid on this never has ground poking through
        X = np.asarray(X, float); Y = np.asarray(Y, float); Zt = ZT
        fx = (X + NE) / NS; fy = (Y + NE) / NS
        i = np.clip(np.floor(fx).astype(int), 0, Zt.shape[1] - 2); j = np.clip(np.floor(fy).astype(int), 0, Zt.shape[0] - 2)
        ax = np.clip(fx - i, 0, 1); ay = np.clip(fy - j, 0, 1)
        z00, z10, z01, z11 = Zt[j, i], Zt[j, i + 1], Zt[j + 1, i], Zt[j + 1, i + 1]
        bl = z00 * (1 - ax) * (1 - ay) + z10 * ax * (1 - ay) + z01 * (1 - ax) * ay + z11 * ax * ay
        dA = np.where(ax > ay, z00 + ax * (z10 - z00) + ay * (z11 - z10), z00 + ay * (z01 - z00) + ax * (z11 - z01))
        dB = np.where(ax + ay < 1, z00 + ax * (z10 - z00) + ay * (z01 - z00), z11 + (1 - ax) * (z01 - z11) + (1 - ay) * (z10 - z11))
        inside = (np.abs(X) < NE - NS) & (np.abs(Y) < NE - NS)
        return np.where(inside, np.maximum(np.maximum(bl, dA), dB), height(X, Y))
    balv, balf, baluv = [], [], []; bedv, bedf, beduv = [], [], []; verts, faces, cols = [], [], []
    head_c = lin((205, 207, 210)); web_c = lin((92, 84, 78)); steel_c = lin((112, 96, 84)); wire_c = lin((38, 38, 40))
    def strip(C, N_, offs, lifts, zc, V, F, UV=None, uvf=None, col=None):
        n = len(C); m = len(offs); s0 = len(V)
        for i in range(n):
            for o, l in zip(offs, lifts):
                p = C[i] + N_[i] * o; V.append((p[0], p[1], float(zc[i] + l)))
        for i in range(n - 1):
            for j in range(m - 1):
                f = (s0 + i * m + j, s0 + i * m + j + 1, s0 + (i + 1) * m + j + 1, s0 + (i + 1) * m + j); F.append(f)
                if UV is not None: UV.extend([uvf(V[k]) if callable(uvf) else uvf[(k - s0)] for k in f])
                if col is not None: cols.extend([col[j] if isinstance(col, list) else col] * 4)
    def box(p0, p1, z0, z1, w, c):   # box from p0 to p1 (plan), w wide, z0..z1
        d = np.array(p1, float) - np.array(p0, float); L = max(np.hypot(*d), 1e-6); n = np.array([-d[1], d[0]]) / L * w / 2
        s0 = len(verts)
        for z in (z0, z1):
            for q in (p0 - n, p1 - n, p1 + n, p0 + n): verts.append((q[0], q[1], z))
        for f in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)):
            faces.append(tuple(s0 + k for k in f)); cols.extend([c] * 4)
    for k, Q in enumerate(PLAN['tracks']):
        T = rail_geo.tangents(Q); N_ = np.stack([-T[:, 1], T[:, 0]], 1)
        zc = np.max([zfloor(Q[:, 0] + N_[:, 0] * o, Q[:, 1] + N_[:, 1] * o) for o in (-1.6, 0, 1.6)], 0)
        e = 0.002 * (k % 5)   # neighbours overlap: tiny stagger, same world-planar texture so the join is invisible
        strip(Q, N_, (-4.0, -3.0, 3.0, 4.0), (0.04 + e, 0.16 + e, 0.16 + e, 0.04 + e), zc, balv, balf, baluv, lambda v: (v[0] / 4.0, v[1] / 4.0))
        dist = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))]) / 5.2
        uvb = []
        for i in range(len(Q)): uvb += [(0.152, dist[i]), (0.848, dist[i])]
        strip(Q, N_, (-1.6, 1.6), (0.19, 0.19), zc, bedv, bedf, beduv, uvb)
        for sd in (-0.8, 0.8):   # steel rail: bright worn head on a dark web, standing 0.17 m off the sleepers
            strip(Q, N_, (sd - 0.035, sd + 0.035), (0.36, 0.36), zc, verts, faces, col=head_c)
            for o in (sd - 0.035, sd + 0.035):
                s0 = len(verts)
                for i in range(len(Q)):
                    p = Q[i] + N_[i] * o; verts.append((p[0], p[1], float(zc[i] + 0.36))); verts.append((p[0], p[1], float(zc[i] + 0.19)))
                for i in range(len(Q) - 1):
                    faces.append((s0 + 2 * i, s0 + 2 * i + 1, s0 + 2 * i + 3, s0 + 2 * i + 2)); cols.extend([web_c] * 4)
        pass
    if spec.get('rail_masts', True):
        for a, b, t in PLAN['portals']:   # lattice portal: two posts, twin-chord beam 7.6-8.0 m
            za, zb = float(zfloor(*a)), float(zfloor(*b)); zt = max(za, zb)
            for p, z in ((a, za), (b, zb)): box(p - t * 0.18, p + t * 0.18, z, zt + 8.0, 0.35, steel_c)
            box(a, b, zt + 7.85, zt + 8.0, 0.12, steel_c); box(a, b, zt + 7.25, zt + 7.4, 0.12, steel_c)
            box(a + t * 0.6, b + t * 0.6, zt + 7.85, zt + 8.0, 0.08, steel_c)
            u = (b - a) / max(np.linalg.norm(b - a), 1e-6)   # knee braces post-to-beam, 1.4 m down and 1.4 m along (Richmond photos)
            for p0, sg in ((a, 1.0), (b, -1.0)):
                for k in range(7):
                    box(p0 + u * sg * (0.2 * k), p0 + u * sg * (0.2 * k + 0.25), zt + 5.85 + 0.2 * k, zt + 6.05 + 0.2 * k, 0.1, steel_c)
        for p, c, t in PLAN['cants']:   # single mast, arm out over the track
            z = float(zfloor(*p)); box(p - t * 0.15, p + t * 0.15, z, z + 7.0, 0.3, steel_c); box(p, c, z + 6.4, z + 6.55, 0.1, steel_c)
    # corridor ballast between the edges traced on Esri z19 (prep/rail_edges.json: left/right point every 1 m along the yard),
    # 0.02 m above ground so the track shoulders (0.04+) sit on it; same world-planar texture, so joins don't show
    EP = os.path.join(D, 'rail_edges.json')
    if os.path.exists(EP):
        E = np.array(json.load(open(EP)))
        m = 96; s0 = len(balv)
        for L_, R_ in E:
            for j in range(m + 1):
                p = L_ + (R_ - L_) * j / m; balv.append((float(p[0]), float(p[1]), 0.0))
        FV = np.array(balv[s0:]); FZ = zfloor(FV[:, 0], FV[:, 1]) + 0.02
        for q in range(len(FV)): balv[s0 + q] = (balv[s0 + q][0], balv[s0 + q][1], float(FZ[q]))
        for i in range(len(E) - 1):
            for j in range(m):
                f = (s0 + i * (m + 1) + j, s0 + (i + 1) * (m + 1) + j, s0 + (i + 1) * (m + 1) + j + 1, s0 + i * (m + 1) + j + 1)
                balf.append(f); baluv.extend([(balv[k][0] / 4.0, balv[k][1] / 4.0) for k in f])
    # tram tracks (OSM railway=tram, aligned on z19 at Stop 7C): flush grooved rails, 1.435 m gauge, 0.02 m proud;
    # Stop 7C platforms (OSM outlines) as 0.3 m concrete slabs
    TP = os.path.join(D, 'trams.json'); tram_c = lin((96, 94, 92)); plat_c = lin((172, 170, 164)); ntram = 0
    if os.path.exists(TP):
        for w in json.load(open(TP))['tracks']:
            Q = rail_geo.densify(np.array(w, float), 1.0)
            if len(Q) < 2: continue
            T = rail_geo.tangents(Q); N_ = np.stack([-T[:, 1], T[:, 0]], 1); zc = zfloor(Q[:, 0], Q[:, 1]); ntram += 1
            for sd in (-0.7175, 0.7175): strip(Q, N_, (sd - 0.04, sd + 0.04), (0.07, 0.07), zc, verts, faces, col=tram_c)
    PP = os.path.join(D, 'tram_platforms.json')
    if os.path.exists(PP):
        for poly in json.load(open(PP)):
            C = np.array(poly, float)
            if np.allclose(C[0], C[-1]): C = C[:-1]
            z = float(np.max(zfloor(C[:, 0], C[:, 1]))) + 0.3; zb = float(np.min(zfloor(C[:, 0], C[:, 1]))) - 0.2; s0 = len(verts)
            for p in C: verts.append((p[0], p[1], zb))
            for p in C: verts.append((p[0], p[1], z))
            n = len(C)
            for i in range(n):
                faces.append((s0 + i, s0 + (i + 1) % n, s0 + n + (i + 1) % n, s0 + n + i)); cols.extend([plat_c] * 4)
            faces.append(tuple(s0 + n + i for i in range(n))); cols.extend([plat_c] * n)
    print('rails: %d tram lines, corridor fill %s' % (ntram, os.path.exists(EP)))
    print('rails: %d ways -> %d lines -> %d visible tracks, %d portals, %d masts' % (PLAN['n_ways'], PLAN['n_merged'], len(PLAN['tracks']), len(PLAN['portals']), len(PLAN['cants'])))
    if balf:
        ob = mk_obj('bg_ballast', balv, balf, mat_img('ballast', os.path.join(HERE, 'tex', 'track_ballast.png'), 0.97)); set_uv(ob.data, baluv)
    if bedf:
        ob = mk_obj('bg_trackbed', bedv, bedf, mat_img('trackbed', os.path.join(HERE, 'tex', 'track_bed.png'), 0.95)); set_uv(ob.data, beduv)
    if faces:
        ob = mk_obj('bg_rails', verts, faces, mat_vcol('rails', 0.35))
        set_corner_col(ob.data, np.concatenate([np.array(cols), np.ones((len(cols), 1))], 1))

GR = []
for _ti, _t in enumerate(PLAN['tracks']):
    _Q = rail_geo.densify(np.array(_t, float), 1.0); _z = zfloor(_Q[:, 0], _Q[:, 1]); _near = (np.abs(_Q[:, 0]) < NE - NS) & (np.abs(_Q[:, 1]) < NE - NS)
    if _near.sum() < 20: continue
    _k = np.ones(11) / 11; _zs = np.convolve(np.pad(_z, 5, mode='edge'), _k, 'valid'); _g = np.abs(np.diff(_zs))[_near[1:]][5:-5] if _near.sum() > 30 else np.array([0])
    _K = np.ones(101) / 101; _zl = np.convolve(np.pad(_z, 50, mode='edge'), _K, 'valid'); _hump = (_z - _zl)[_near]
    _i = int(np.argmax(np.abs(np.diff(_zs)) * _near[1:]))
    GR.append(dict(track=_ti, n=int(_near.sum()), max_grade=float(_g.max()) if len(_g) else 0, p95_grade=float(np.percentile(_g, 95)) if len(_g) else 0, hump_up=float(_hump.max()), hump_dn=float(_hump.min()), at=[round(float(_Q[_i, 0]), 1), round(float(_Q[_i, 1]), 1)]))
CL = []
for _S, _u, _hw in RG_UNDERS:
    for _t in PLAN['tracks']:
        _Q = rail_geo.densify(np.array(_t, float), 1.0); _D = np.hypot(_Q[:, None, 0] - _S[None, :, 0], _Q[:, None, 1] - _S[None, :, 1])
        _jj = np.argmin(_D, 1); _h = _D[np.arange(len(_Q)), _jj] < _hw
        if _h.any(): CL.append(float(np.min(_u[_jj[_h]] - zfloor(_Q[_h, 0], _Q[_h, 1]) - 0.36)))
print('clearance: %d crossings, min %.2f m, under 6.2: %d' % (len(CL), min(CL) if CL else -1, sum(c < 6.2 for c in CL)))
json.dump(GR, open(os.path.join(os.path.dirname(SP), '..', 'out', 'mcg', 'rails', 'grade.json'), 'w'), indent=0)
# ---------- rails-only check renders (not part of the build) ----------
import mathutils
sc = bpy.context.scene
try: sc.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception: sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.65, 0.8, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.8
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 4; so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so); so.rotation_euler = (0.7, 0.2, 0.8)
def shot(nm, eye, look, ortho=None, lens=35):
    cd = bpy.data.cameras.new(nm); co = bpy.data.objects.new(nm, cd); sc.collection.objects.link(co)
    co.location = eye; d = mathutils.Vector(look) - mathutils.Vector(eye); co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cd.clip_end = 3000; cd.lens = lens
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    sc.camera = co; sc.render.filepath = os.path.join(OUT, 'rails', 'nw_' + nm + '.png'); bpy.ops.render.render(write_still=True); print('SHOT', nm)
def gz(x, y): return float(zfloor(x, y))
for nm, (x0, y0, x1, y1) in {'top_mcg': (-200, -330, 20, -110), 'top_west': (-640, -80, -420, 140), 'top_rich': (320, -520, 540, -300)}.items():
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; sc.render.resolution_x = sc.render.resolution_y = 1760
    shot(nm, (cx, cy, gz(cx, cy) + 400), (cx, cy, gz(cx, cy)), ortho=x1 - x0)
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
x, y = -130.0, -120.0; shot('eye17', (x, y, gz(x, y) + 1.7), (x + 40, y - 30, gz(x, y) + 0.5), lens=28)
x, y = -260.0, -60.0; shot('eye30', (x, y, gz(x, y) + 30), (x + 120, y - 90, gz(x, y)), lens=30)
