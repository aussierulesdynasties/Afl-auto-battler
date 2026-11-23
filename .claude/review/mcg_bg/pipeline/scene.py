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
FORM = None
if spec.get('rail_geo') and os.path.exists(os.path.join(D, 'rails.json')):
    sys.path.insert(0, HERE); import rail_geo, rail_grade
    _j = lambda f: json.load(open(os.path.join(D, f))) if os.path.exists(os.path.join(D, f)) else None
    _KF = np.array(_j('footprint.json')) if spec.get('rail_cut', {}).get('keep_footprint') and _j('footprint.json') else None
    _PL = rail_geo.plan(_j('rails.json'), _KF, spec.get('rail_cut', {}).get('keep_ellipse'), _j('gantries.json'), _j('rail_extra.json'), _j('rail_shift.json'))
    near, _nm, RG_PROF, RG_UNDERS = rail_grade.apply(near, NE, NS, _PL['tracks'], _j('rail_edges.json'), _j('bridges.json') or [], buf=0.0)   # Vicmap kept; only the under-bridge clearance is cut
    import rail_form; FORM = rail_form.build(near, NE, NS, RG_PROF, _j('formation_edges.json'))
    print('formation: %d fine verts, %d bed faces, %d coarse cells replaced' % (len(FORM['V']), FORM['n_bed'], int(FORM['cells'].sum())))
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
if FORM is not None: F = F[~FORM['cells'].ravel()]   # the rail corridor is the fine formation mesh below
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
# rail formation: fine mesh on the graded bed; batters take the bank texture, walls concrete (rail_form.py)
if FORM is not None:
    _FV = FORM['V']; _FF = FORM['F']; _FK = FORM['face_kind']
    _cz = _FV[_FF][:, :, 2]; _span = _cz.max(1) - _cz.min(1)
    _wall = (_FK == 2) & (_span > 0.75 * 0.9)
    _bank = ~_wall & (_span > 0.75 * 0.6)
    for _nm_, _sel, _mat, _box in (('bg_formation', ~_wall & ~_bank, gm, None),
                                   ('bg_formation_banks', _bank, mat_img('bank', os.path.join(HERE, 'tex', 'bank_grass.png'), 0.95), 1 / 8.0),
                                   ('bg_formation_walls', _wall, mat_img('railwall', os.path.join(HERE, 'tex', 'bridge_conc.png'), 0.9), 1 / 4.0)):
        if not _sel.any(): continue
        _ff = _FF[_sel]; _u = np.unique(_ff); _rm = -np.ones(len(_FV), int); _rm[_u] = np.arange(len(_u))
        _o = mk_obj(_nm_, _FV[_u].tolist(), _rm[_ff].tolist(), _mat)
        if _box: set_uv_box(_o.data, _box)
        else:
            _lp = _rm[_ff].ravel(); _vv = _FV[_u]
            set_uv(_o.data, np.stack([(_vv[_lp, 0] + NE) / (2 * NE), (_vv[_lp, 1] + NE) / (2 * NE)], 1))
        for p in _o.data.polygons: p.use_smooth = _box is None
    print('formation faces: bed/flat %d, batter %d, wall %d' % (int((~_wall & ~_bank).sum()), int(_bank.sum()), int(_wall.sum())))

# ---------- far terrain (outside the near square), vertex colours by slope, haze by distance ----------
m = far.shape[0]
gf = np.arange(m) * FS - FA
XF, YF = np.meshgrid(gf, gf)
ZF = far.copy()
gy_, gx_ = np.gradient(ZF, FS); slope = np.hypot(gx_, gy_)
VF = np.stack([XF.ravel(), YF.ravel(), ZF.ravel()], 1)
ii = np.arange(m - 1); I, J = np.meshgrid(ii, ii)
a = (J * m + I).ravel()
FF = np.stack([a, a + 1, a + m + 1, a + m], 1)
cx = (VF[FF[:, 0], 0] + VF[FF[:, 2], 0]) / 2; cy = (VF[FF[:, 0], 1] + VF[FF[:, 2], 1]) / 2
FF = FF[(np.abs(cx) > NE - 1) | (np.abs(cy) > NE - 1)]
noise = rng.random(VF.shape[0])
vc = (lin(PAL['far_flat'])[None] * (1 - noise[:, None] * 0.5) + lin(PAL['far_veg'])[None] * noise[:, None] * 0.5)
st = np.clip((slope.ravel() - 0.12) / 0.2, 0, 1)[:, None]
vc = vc * (1 - st) + lin(PAL['far_steep'])[None] * st
d = np.hypot(VF[:, 0], VF[:, 1])
hz = (1 - np.exp(-d / spec.get('haze_m', 22000)))[:, None] * 0.85
vc = vc * (1 - hz) + lin(PAL['haze'])[None] * hz
ob = mk_obj('bg_far_terrain', VF, FF.tolist(), mat_vcol('far', 0.95))
lp = FF.ravel()
set_corner_col(ob.data, np.concatenate([vc[lp], np.ones((len(lp), 1))], 1))
for p in ob.data.polygons: p.use_smooth = True

# ---------- bridges: deck slab with parapets, top at the higher end of the way ----------
BRP = os.path.join(D, 'bridges.json')
if os.path.exists(BRP):
    verts, faces, cols = [], [], []
    deck_c = lin((240, 238, 234)); rail_c = lin((96, 100, 104)); fb_rail_c = lin((206, 208, 204))
    def box_strip(P, z, w, th, c):
        # one quad strip per segment: top, two sides, bottom
        for (x1, y1), (x2, y2) in zip(P, P[1:]):
            L = math.hypot(x2 - x1, y2 - y1)
            if L < 0.1: continue
            nx, ny = -(y2 - y1) / L * w / 2, (x2 - x1) / L * w / 2
            q = [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)]
            s0 = len(verts)
            for qx, qy in q: verts.append((qx, qy, z))
            for qx, qy in q: verts.append((qx, qy, z - th))
            for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)):
                faces.append(tuple(s0 + i for i in f)); cols.extend([c] * 4)
    for b in json.load(open(BRP)):
        P = np.array(b['p'], float)
        if b.get('rail'): continue   # rail bridges are drawn as track
        if b['w'] <= 6 and np.hypot(*np.diff(P, axis=0).T).sum() < 30: continue   # stair/ramp stubs
        ends = height(P[[0, -1], 0], P[[0, -1], 1])
        z = max(float(ends.max()), 0.0 if np.hypot(*P.mean(0)) < R0 + 60 else float(ends.max())) + 0.3
        if b['w'] <= 6:   # footbridge: draw only where it spans a drop (>2 m under its ends); on flat ground it is a path
            t_ = np.linspace(0, 1, 40)[:, None]; S_ = np.concatenate([P[i] * (1 - t_) + P[i + 1] * t_ for i in range(len(P) - 1)])
            if float(ends.max()) - float(height(S_[:, 0], S_[:, 1]).min()) < 2.0: continue
        w = b['w']
        if b['w'] <= 6:   # footbridge deck: straight ramp between its two end heights, square piers every 25 m down to the ground
            e0, e1 = float(ends[0]) + 0.3, float(ends[1]) + 0.3; cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))]); tot = max(cum[-1], 1e-6)
            for i in range(len(P) - 1):
                za, zb = e0 + (e1 - e0) * cum[i] / tot, e0 + (e1 - e0) * cum[i + 1] / tot
                d_ = P[i + 1] - P[i]; L = np.hypot(*d_)
                if L < 0.1: continue
                nx, ny = -d_[1] / L * w / 2, d_[0] / L * w / 2; s0 = len(verts)
                for (qx, qy), zz in zip([(P[i][0] + nx, P[i][1] + ny), (P[i + 1][0] + nx, P[i + 1][1] + ny), (P[i + 1][0] - nx, P[i + 1][1] - ny), (P[i][0] - nx, P[i][1] - ny)], (za, zb, zb, za)): verts.append((qx, qy, zz))
                for (qx, qy), zz in zip([(P[i][0] + nx, P[i][1] + ny), (P[i + 1][0] + nx, P[i + 1][1] + ny), (P[i + 1][0] - nx, P[i + 1][1] - ny), (P[i][0] - nx, P[i][1] - ny)], (za, zb, zb, za)): verts.append((qx, qy, zz - 1.6))
                for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)): faces.append(tuple(s0 + k for k in f)); cols.extend([deck_c] * 4)
            for d in np.arange(12.5, tot - 5, 25.0):
                k = int(np.searchsorted(cum, d)) - 1; k = min(max(k, 0), len(P) - 2); t = (d - cum[k]) / max(cum[k + 1] - cum[k], 1e-6)
                px, py = P[k] + (P[k + 1] - P[k]) * t; zt = e0 + (e1 - e0) * d / tot - 1.0; zg = float(height(np.array([px]), np.array([py]))[0])
                if zt - zg < 1.0: continue
                s0 = len(verts)
                for zz in (zt, zg - 0.5):
                    for ox, oy in ((-0.4, -0.4), (0.4, -0.4), (0.4, 0.4), (-0.4, 0.4)): verts.append((px + ox, py + oy, zz))
                for f in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)): faces.append(tuple(s0 + k2 for k2 in f)); cols.extend([deck_c] * 4)
            for sd in (-1, 1):   # railings 1.1 m on each edge, following the ramp
                for i in range(len(P) - 1):
                    d_ = P[i + 1] - P[i]; L = np.hypot(*d_)
                    if L < 0.1: continue
                    o = sd * np.array([-d_[1], d_[0]]) / L * (w / 2 - 0.1); za, zb = e0 + (e1 - e0) * cum[i] / tot, e0 + (e1 - e0) * cum[i + 1] / tot; s0 = len(verts)
                    for (qx, qy), zz in zip([P[i] + o, P[i + 1] + o, P[i + 1] + o, P[i] + o], (za, zb, zb + 1.1, za + 1.1)): verts.append((qx, qy, zz))
                    faces.append((s0, s0 + 1, s0 + 2, s0 + 3)); cols.extend([fb_rail_c] * 4)
            continue
        box_strip(P, z, w, 1.4, deck_c)
        for sd in (-1, 1):   # parapets 1.1 m, 0.25 m thick, on each edge
            Q = []
            for i in range(len(P)):
                a_ = P[max(i - 1, 0)]; b_ = P[min(i + 1, len(P) - 1)]
                d_ = b_ - a_; L = max(np.hypot(*d_), 1e-6)
                Q.append(P[i] + sd * np.array([-d_[1], d_[0]]) / L * (w / 2 - 0.125))
            box_strip(np.array(Q), z + 1.1, 0.25, 1.1, rail_c)
    if faces:
        ob = mk_obj('bg_bridges', verts, faces, mat_mul('bridge', os.path.join(HERE, 'tex', 'bridge_conc.png'), 0.85))
        set_corner_col(ob.data, np.concatenate([np.array(cols), np.ones((len(cols), 1))], 1))
        set_uv_box(ob.data, 1 / 12.0)   # hand-made concrete, 12 m tile (tex/bridge_conc.png)

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
        zc = np.where(inside, np.maximum(np.maximum(bl, dA), dB), height(X, Y))
        if FORM is not None:
            zq = FORM['zf'](X, Y); zc = np.where(np.isnan(zq), zc, zq)
        return zc
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
        zc = zfloor(Q[:, 0], Q[:, 1])   # the graded corridor (rail_grade.py) is smooth: one height per row, shared by neighbours
        e = 0.002 * (k % 5)   # neighbours overlap: flat 0.10 top (level with the corridor fill), tiny stagger, same world-planar texture
        strip(Q, N_, (-4.0, -3.0, 3.0, 4.0), (0.03 + e, 0.10 + e, 0.10 + e, 0.03 + e), zc, balv, balf, baluv, lambda v: (v[0] / 4.0, v[1] / 4.0))
        dist = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))]) / 5.2
        # turnouts: a diverging track shares the through track's sleepers until it is 2.6 m clear of it, so no two sleeper
        # beds overlap (rail_geo.turnouts already cut the shared run out of the shorter track)
        own = np.ones(len(Q), bool); L_k = dist[-1]
        for k2, Q2 in enumerate(PLAN['tracks']):
            if k2 == k or len(Q2) < len(Q) or (len(Q2) == len(Q) and k2 > k): continue
            lo, hi = Q.min(0) - 3, Q.max(0) + 3; sel = np.all((Q2 >= lo) & (Q2 <= hi), 1)
            if not sel.any(): continue
            Q2s = Q2[sel]
            for a0 in range(0, len(Q), 512):
                own[a0:a0 + 512] &= np.min(np.hypot(Q[a0:a0 + 512, None, 0] - Q2s[None, :, 0], Q[a0:a0 + 512, None, 1] - Q2s[None, :, 1]), 1) > 1.7
        own &= ~rail_geo.in_turnout(Q, PLAN.get('turnouts', []))   # turnout bearers replace the plain sleepers there
        for r in np.split(np.arange(len(Q)), np.where(np.diff(own.astype(int)) != 0)[0] + 1):
            if not own[r[0]] or len(r) < 2: continue
            uvb = []
            for i in r: uvb += [(0.152, dist[i]), (0.848, dist[i])]
            strip(Q[r], N_[r], (-1.6, 1.6), (0.19, 0.19), zc[r], bedv, bedf, beduv, uvb)
        for sd in (-0.8, 0.8):   # steel rail: bright worn head on a dark web, standing 0.17 m off the sleepers
            strip(Q, N_, (sd - 0.035, sd + 0.035), (0.36, 0.36), zc, verts, faces, col=head_c)
            for o in (sd - 0.035, sd + 0.035):
                s0 = len(verts)
                for i in range(len(Q)):
                    p = Q[i] + N_[i] * o; verts.append((p[0], p[1], float(zc[i] + 0.36))); verts.append((p[0], p[1], float(zc[i] + 0.19)))
                for i in range(len(Q) - 1):
                    faces.append((s0 + 2 * i, s0 + 2 * i + 1, s0 + 2 * i + 3, s0 + 2 * i + 2)); cols.extend([web_c] * 4)
        if spec.get('rail_masts', True): strip(Q, N_, (-0.02, 0.02), (5.6, 5.6), zc, verts, faces, col=wire_c)
    # turnouts (coordinator 2026-11-21): bearers from the template in rail_geo.templates, one shared bed under the switch
    # and closure rails out to 3 m past the frog; crossovers sit on long bearers spanning both roads; steel frog at y = gauge
    tim_c = lin((140, 132, 122)); frog_c = lin((70, 66, 62))
    for o in PLAN.get('turnouts', []):
        p = np.array(o['at']); t = np.array(o['t']); n = np.array(o['n']); a = o['a']; L = o['L']; R = o['R']
        if o['cross']:
            Lx = 2 * L; Dsp = 2 * (L * L / (2 * R))
            for x in np.arange(0.0, Lx + 0.01, 0.65):
                u = p + t * x; z = float(zfloor(*u)); box(u - n * 1.6, u + n * (Dsp + 1.6), z + 0.10, z + 0.20, 0.26, tim_c)
        else:
            for x in np.arange(0.0, L + 3.0, 0.65):
                y = x * x / (2 * R) if x <= L else L * L / (2 * R) + (x - L) * np.tan(a)
                u = p + t * x; z = float(zfloor(*u)); box(u - n * 1.6, u + n * (y + 1.6), z + 0.10, z + 0.20, 0.26, tim_c)
        for f in o['frog']:
            f = np.array(f) - n * 0.8; z = float(zfloor(*f)); box(f - t * 0.9, f + t * 0.9, z + 0.20, z + 0.30, 0.22, frog_c)
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
        FV = np.array(balv[s0:]); FZ = zfloor(FV[:, 0], FV[:, 1]) + 0.10
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

# ---------- buildings ----------
BL = json.load(open(os.path.join(D, 'buildings.json')))
_RC = json.load(open(os.path.join(D, 'roof_class.json'))) if os.path.exists(os.path.join(D, 'roof_class.json')) else None
if _RC and len(_RC['per_building']) != len(BL): raise SystemExit('roof_class.json is stale: rerun roofs_mcg.py after prep')
if _RC:
    for b, c in zip(BL, _RC['per_building']): b['rk'] = c
_HIP = json.load(open(os.path.join(D, 'roof_hip.json'))) if os.path.exists(os.path.join(D, 'roof_hip.json')) else {}
for i_, h_ in _HIP.items(): BL[int(i_)]['hip'] = h_   # L / U / courtyard houses: hipped roof mesh (roofs_mcg.py)
# measured heights (reference only, CC BY 4.0): City of Yarra 3D buildings 2015 and City of Melbourne 2023 footprints;
# h = measured ridge above ground (hscripts/measure.py). Unmeasured buildings keep the OSM value until their storeys are logged.
_HM = json.load(open(os.path.join(D, 'heights_measured.json'))) if os.path.exists(os.path.join(D, 'heights_measured.json')) else {}
for i_, m_ in _HM.items():
    if m_['ridge'] >= 2.5: BL[int(i_)]['h'] = m_['ridge']; BL[int(i_)]['hsrc'] = m_['src']
    rt_ = m_.get('roof')   # City of Melbourne measured roof type wins over the footprint-shape guess
    if rt_ in ('Flat', 'Shed'): BL[int(i_)]['flat'] = True; BL[int(i_)].pop('hip', None)
    elif rt_ == 'Gable' and not BL[int(i_)].get('hip', {}).get('terrace'): BL[int(i_)].pop('hip', None)
BL = [b for b in BL if b.get('name') != 'Team Merchandise']
# Regency Towers (265 Exhibition St): the OSM block at one 123 m height is replaced by CoM 2023's measured tiers (prep/regency.json):
# stone podium 23.5 m, wing 42 m, towers 93-108 m, plant to 112.5 m; balcony stacks are separate geometry (built below)
_RG = json.load(open(os.path.join(D, 'regency.json'))) if os.path.exists(os.path.join(D, 'regency.json')) else None
if _RG:
    _r0 = next(b for b in BL if 'Regency Towers' in b.get('name', ''))
    BL = [b for b in BL if b is not _r0]
    for t_ in _RG['tiers']:
        BL.append(dict(_r0, p=t_['p'], h=t_['h'], name={'regpod': 'Regency podium', 'plant': 'Regency Towers plant'}.get(t_['tex'], 'Regency Towers'), hsrc='com2023'))   # stray merch hut on the concourse (aerial: a van-sized kiosk, not a building)
def build_class(cls, tex, tw, th, sel=None, tag='', wall_cols=None):
    verts, faces, cols, uvs = [], [], [], []
    RF = {'metal': [[], [], [], []], 'tile': [[], [], [], []], 'big': [[], [], [], []]}   # roof meshes: verts, faces, cols, uvs
    walls = [lin(c) for c in (wall_cols or PAL['walls_' + cls])]
    roofs = [lin(c) for c in PAL['roofs_' + ('house' if cls == 'house' else 'flat')]]
    for b in BL:
        if b['c'] != cls or (sel is not None and not sel(b)): continue
        P = np.array(b['p'], float)
        cxy = P.mean(0)
        base = float(height(cxy[0], cxy[1])) - 1.0
        h = b['h']
        wc = walls[b['wall'] % len(walls)] * (1 + 0.06 * (rng.random() - 0.5))
        rc = roofs[b['roof'] % len(roofs)] * (1 + 0.08 * (rng.random() - 0.5))
        hip = b.get('hip') if cls == 'house' else None
        pitched = cls == 'house' and hip is None and not b.get('flat')
        if pitched:   # ridge along the footprint's long axis (min-area box over its edge directions), pitch 28 deg, ridge <= 4 m
            best = None
            for i in range(len(P)):
                e_ = P[(i + 1) % len(P)] - P[i]; n_ = float(np.hypot(*e_))
                if n_ < 0.5: continue
                ax_ = e_ / n_; pv = np.array([-ax_[1], ax_[0]]); uu = P @ ax_; vv = P @ pv
                ar = (uu.max() - uu.min()) * (vv.max() - vv.min())
                if (uu.max() - uu.min()) < (vv.max() - vv.min()): ax_, pv = pv, -ax_; uu, vv = P @ ax_, P @ pv
                if best is None or ar < best[0]: best = (ar, ax_, pv, vv.min(), vv.max())
            _, AX, PV, vlo, vhi = best; VC = (vlo + vhi) / 2; HW = max(0.5, (vhi - vlo) / 2)
            rh = min(4.0, HW * math.tan(math.radians(28)))
            Q = []   # ring with the ridge crossings inserted
            for i in range(len(P)):
                p_, q_ = P[i], P[(i + 1) % len(P)]; d0, d1 = p_ @ PV - VC, q_ @ PV - VC; Q.append(p_)
                if d0 * d1 < 0: Q.append(p_ + (q_ - p_) * (d0 / (d0 - d1)))
            P = np.array(Q)
        else: rh = hip['rh'] if hip else 0
        top = base + 1.0 + h - rh
        def zt(x, y): return top + rh * (1 - abs(x * PV[0] + y * PV[1] - VC) / HW) if pitched else top
        k = len(P); s0 = len(verts)
        for x, y in P: verts.append((x, y, base))
        for x, y in P: verts.append((x, y, zt(x, y)))
        per = 0.0
        for i in range(k):
            j = (i + 1) % k
            L = float(np.hypot(*(P[j] - P[i])))
            faces.append((s0 + i, s0 + j, s0 + k + j, s0 + k + i))
            cols += [wc] * 4
            u0, u1 = per / tw, (per + L) / tw
            v0 = -1.0 / th
            uvs += [(u0, v0), (u1, v0), (u1, (zt(*P[j]) - base - 1.0) / th), (u0, (zt(*P[i]) - base - 1.0) / th)]
            per += L
        # roof: own mesh, hand-made texture, planar UVs along the building's longest side (one tile = 3.04 m)
        E = np.diff(np.vstack([P, P[:1]]), axis=0); e = E[np.argmax(np.hypot(E[:, 0], E[:, 1]))]; th_ = math.atan2(e[1], e[0])
        ct, st = math.cos(th_), math.sin(th_)
        if pitched: ct, st = float(AX[0]), float(AX[1])
        rk = b.get('rk') if _RC else None
        if rk: kind = _RC['classes'][rk][0]; rc = lin(_RC['classes'][rk][1]) * (1 + 0.06 * (rng.random() - 0.5))   # aerial picks the hand-made class only
        elif True: kind = None
        if kind is None: kind = 'tile' if (cls == 'house' and PAL['roofs_house'][b['roof'] % len(PAL['roofs_house'])][0] > 1.3 * PAL['roofs_house'][b['roof'] % len(PAL['roofs_house'])][1]) else 'metal'
        if kind == 'metal' and not pitched and b.get('a', 0) > 1200:   # large flat roof: 48 m tile with bays, skylights and plant that read from far
            kind = 'big'; rc = np.ones(3) * (1 + 0.1 * (rng.random() - 0.5))
        rv, rf, rcl, ruv = RF[kind]; r0 = len(rv); tl = 48.0 if kind == 'big' else 3.04
        def ruv_(x, y): return ((x * ct + y * st) / tl, (-x * st + y * ct) / tl)
        for x, y in P: rv.append((x, y, zt(x, y))); ruv.append(ruv_(x, y))
        if hip:   # hipped roof mesh over the whole footprint, eaves at the wall top
            del rv[r0:]; del ruv[r0:]
            for x, y, dz in hip['v']: rv.append((x, y, top + dz)); ruv.append(ruv_(x, y))
            for f_ in hip['f']: rf.append(tuple(r0 + i for i in f_)); rcl += [rc] * 3
        elif pitched:   # two planar slopes: the ring split at the ridge line, each half one n-gon
            side = P @ PV - VC
            for sg in (1, -1):
                hf = [r0 + i for i in range(k) if sg * side[i] >= -1e-6]
                if len(hf) >= 3: rf.append(tuple(hf)); rcl += [rc] * len(hf)
        else:
            rf.append(tuple(r0 + i for i in range(k))); rcl += [rc] * k
    if not faces: return
    fm = mat_mul('facade_' + cls + tag, os.path.join(HERE, 'tex', tex), 0.5) if tex in ('city_office.png', 'city_far.png') or tex.startswith('fac_') or tex.startswith('twr_') else mat_facade('facade_' + cls, os.path.join(HERE, 'tex', tex))
    ob = mk_obj('bg_bld_' + cls + tag, verts, faces, fm)
    set_corner_col(ob.data, np.concatenate([np.array(cols), np.ones((len(cols), 1))], 1))
    set_uv(ob.data, uvs)
    for kind, (rv, rf, rcl, ruv) in RF.items():
        if not rf: continue
        rtex = spec.get('roof_metal_tex', 'roof_metal.png') if kind == 'metal' else 'roof_%s.png' % kind
        if kind == 'big': rtex = 'roof_corrugated.png'; rtex_big = True
        else: rtex_big = False   # traeger: roof_corrugated.png (3.04 m tile)
        rmat = mat_mul('roof_%s%s_%s' % (cls, tag, kind), os.path.join(HERE, 'tex', 'roof_big.png' if rtex_big else rtex), 0.55) if rtex == 'roof_corrugated.png' else mat_facade('roof_%s%s_%s' % (cls, tag, kind), os.path.join(HERE, 'tex', rtex))
        ro = mk_obj('bg_roof_%s%s_%s' % (cls, tag, kind), rv, rf, rmat)
        set_corner_col(ro.data, np.concatenate([np.array(rcl), np.ones((len(rcl), 1))], 1))
        set_uv(ro.data, [ruv[i] for f_ in rf for i in f_])
for b in BL:
    P = np.array(b['p']); x, y = P[:, 0], P[:, 1]
    b['a'] = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
exec(open(os.path.join(HERE, 'landmarks.py'), encoding='utf-8').read())   # hand-built landmarks replace their generic boxes
# houses: Victorian terraces, rendered (cream / stone / ochre / grey) or red face brick; aerial roof classes give the roofs
build_class('house', 'fac_render.png', 3.6, 3.2, lambda b: b['wall'] % 3 != 0, '_render', [(255, 252, 240), (236, 226, 204), (228, 206, 170), (214, 214, 208)])
build_class('house', 'fac_brick.png', 3.6, 3.2, lambda b: b['wall'] % 3 == 0, '_brick', [(255, 255, 255), (236, 226, 218)])
def _far(b): return float(np.hypot(*np.mean(b['p'], 0))) > 1000
# facade family from the building's real OSM name and type (prep keeps kind/name): each family a hand-made tile
def fam(b):
    n = b.get('name', ''); k = b.get('kind', '')
    if any(w in n for w in ('Arena', 'Tennis Centre', 'Vitality')) or k in ('sports_hall', 'stadium', 'warehouse', 'industrial', 'sports_centre'): return 'clad'
    if k in ('church', 'house', 'terrace', 'detached', 'semidetached_house') or any(w in n for w in ('Church', 'Hall', 'House', 'Bishopscourt', 'Terraces', 'Tennis Club', 'Library')): return 'brick'
    if k in ('apartments', 'hotel', 'residential', 'dormitory'): return 'apart'
    if k in ('yes', '') and b['h'] <= 9: return 'brick'
    return 'office'
FAM = {'brick': ('fac_brick.png', [(255, 255, 255), (236, 226, 218), (214, 200, 196)]),
       'office': ('fac_office.png', [(255, 255, 255), (240, 238, 230), (226, 230, 236)]),
       'apart': ('fac_apart.png', [(255, 255, 255), (246, 240, 228), (232, 236, 238)]),
       'clad': ('fac_clad.png', [(255, 255, 255), (232, 238, 246), (220, 224, 226)])}
for f_, (tx_, wc_) in FAM.items():
    build_class('block', tx_, 3.6, 3.2, lambda b, f_=f_: fam(b) == f_, '_' + f_, wc_)
    build_class('tower', tx_, 3.6, 3.2, lambda b, f_=f_: not _far(b) and fam(b) == f_ and f_ != 'office', '_' + f_, wc_)
# CBD towers: each gets its own hand-made curtain wall (3.0 m bay x 3.6 m floor), named towers from their photos, the rest spread by id
TWR_NAMED = {'120 Collins': 'c120', '101 Collins': 'c101', 'ANZ Tower': 'cplace', 'Nauru House': 'nauru', '1 Spring Street': 'spring', 'TAC House': 'tac', 'Casselden': 'cass', 'SX1': 'sx1', 'Sapphire by': 'sapph', 'HWT Tower': 'hwt', 'Regency Towers': 'regency', 'Regency podium': 'regpod'}
TWR_FH = {'tac': 3.6, 'cass': 3.6, 'cplace': 185 / 46, 'cplace35': 185 / 50, 'spring': 4.0, 'sx1': 161 / 39, 'sapph': 215 / 60, 'hwt': 111 / 26, 'regency': 3.1, 'regpod': 23.5 / 6}   # floor height = roof / floor count (Wikipedia infobox); 1 Spring St: 26 floors counted on spring1.jpg above an 18 m podium
TWR_SPREAD = ['blue', 'silver', 'green', 'blue', 'silver']
def twr(b):
    for k_, v_ in TWR_NAMED.items():
        if k_ in b.get('name', ''): return v_
    c_ = np.mean(b['p'], 0)
    if math.hypot(c_[0] + 939, c_[1] - 681) < 15 and b.get('h', 0) > 180: return 'cplace35'   # Sofitel, 35 Collins (unnamed in OSM)
    return TWR_SPREAD[int(abs(c_[0] * 7.3 + c_[1] * 3.1)) % len(TWR_SPREAD)]
for t_ in sorted(set(TWR_NAMED.values()) | set(TWR_SPREAD) | {'cplace35'}):
    build_class('tower', 'twr_%s.png' % t_.replace('35', ''), 6.0 if 'cplace' in t_ else 3.0, TWR_FH.get(t_, 3.6), lambda b, t_=t_: (t_ in TWR_FH or _far(b) or fam(b) == 'office') and twr(b) == t_, '_' + t_, [(255, 255, 255)])
if _RG:   # Regency balcony stacks (r5.jpg, regency.jpg): per floor a 0.22 m pale slab + 1.0 m black balustrade on the open edges;
    # black steel crown frame (posts + two rings) 6.2 m over each corner stack (regency.jpg: two floors of open frame above the roof)
    sv_, sf_, sc_ = [], [], []; rv_, rf_, rc_ = [], [], []
    SLAB = lin((205, 196, 182)); RAIL = lin((34, 38, 42))
    def _prism(V, F, Cl, ring_, z0, z1, col):
        k = len(ring_); s0 = len(V)
        for x, y in ring_: V.append((x, y, z0))
        for x, y in ring_: V.append((x, y, z1))
        for i in range(k): F.append((s0 + i, s0 + (i + 1) % k, s0 + k + (i + 1) % k, s0 + k + i)); Cl += [col] * 4
        F.append(tuple(s0 + k + i for i in range(k))); Cl += [col] * k
        F.append(tuple(s0 + i for i in reversed(range(k)))); Cl += [col] * k
    def _rail(V, F, Cl, a, b, z0, z1, col, t=0.06):
        a = np.array(a, float); b = np.array(b, float); d = b - a; L = float(np.hypot(*d))
        if L < 0.05: return
        n = np.array([-d[1], d[0]]) / L * t / 2
        _prism(V, F, Cl, [tuple(a - n), tuple(b - n), tuple(b + n), tuple(a + n)], z0, z1, col)
    for st in _RG['balc']:
        P_ = st['p']; c_ = np.mean(P_, 0); g0 = float(height(c_[0], c_[1])) - 1.0 + 1.0
        nfl = int((st['z1'] - st['z0']) / _RG['floor_h'] + 1e-6)
        for f in range(1, nfl + 1):
            z = g0 + st['z0'] + f * _RG['floor_h'] - _RG['floor_h']
            if z > g0 + st['z1'] - 1.2: break
            _prism(sv_, sf_, sc_, P_, z, z + 0.22, SLAB)
            for k in st['rail']: _rail(rv_, rf_, rc_, P_[k], P_[(k + 1) % len(P_)], z + 0.22, z + 1.22, RAIL)
        if len(st['rail']) >= 4:   # corner stack: crown frame
            zr = g0 + st['z1']
            for k in st['rail']:
                x, y = P_[k]; _rail(rv_, rf_, rc_, (x - 0.08, y), (x + 0.08, y), zr, zr + 6.2, RAIL, 0.16)
                for zz in (zr + 3.1, zr + 6.2): _rail(rv_, rf_, rc_, P_[k], P_[(k + 1) % len(P_)], zz - 0.15, zz, RAIL, 0.12)
    for nm_, V, F, Cl in (('bg_regency_slabs', sv_, sf_, sc_), ('bg_regency_rails', rv_, rf_, rc_)):
        ob = mk_obj(nm_, V, F, mat_vcol(nm_ + '_m', 0.7 if 'slab' in nm_ else 0.35))
        set_corner_col(ob.data, np.concatenate([np.array(Cl), np.ones((len(Cl), 1))], 1))
    print('regency balconies', len(sf_), 'slab faces', len(rf_), 'rail faces')
print('buildings built')

# ---------- trees ----------
KIND = {  # canopy radius, canopy centre height, squash, trunk height, trunk radius, canopy rgb, trunk rgb, ico subdiv
 'ghost_gum': (4.6, 6.8, 0.7, 4.0, 0.22, (132, 140, 96), (236, 230, 218), 1),
 'red_gum': (7.0, 10.0, 0.6, 5.5, 0.45, (112, 122, 86), (160, 152, 140), 1),
 'mulga': (1.5, 1.7, 0.7, 0.9, 0.1, (134, 132, 94), (96, 76, 60), 1),
 'elm': (6.5, 14.0, 0.85, 7.0, 0.5, (72, 98, 54), (76, 64, 54), 1),
 'plane': (5.5, 12.0, 0.9, 6.5, 0.4, (86, 110, 60), (150, 140, 120), 1),
}
_tm = os.path.join(D, 'trees_mcg.json')   # crown-by-crown set from the aerial (trees_mcg.py) when it exists
TR = json.load(open(_tm if os.path.exists(_tm) else os.path.join(D, 'trees.json')))
TR = np.array([list(t[:3]) + [t[3] if len(t) > 3 else 1.0] for t in TR], float)
r = np.hypot(TR[:, 0], TR[:, 1])
cap = spec.get('tree_cap', 30000)
near_keep = r < 700
p_far = max(0.0, min(1.0, (cap - near_keep.sum()) / max(1, (~near_keep).sum())))
TR = TR[near_keep | (rng.random(len(TR)) < p_far)]
print('trees kept', len(TR))
kinds = spec['tree_kinds']
for ki, kn in enumerate(kinds):
    cr, ch, sq, th_, tr_, ccol, tcol, sub = KIND[kn]
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    cv = np.array([v.co[:] for v in bm.verts]); cf = [[v.index for v in f.verts] for f in bm.faces]; bm.free()
    cv = cv + rng.normal(0, 0.12, cv.shape)  # lumpy canopy
    tv = []; tf = []
    for i in range(6):
        a0 = 2 * math.pi * i / 6; tv += [(math.cos(a0), math.sin(a0), 0), (math.cos(a0), math.sin(a0), 1)]
    for i in range(6):
        j = (i + 1) % 6; tf.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    tv = np.array(tv)
    sel = TR[TR[:, 2] == ki]
    verts, faces, cols = [], [], []
    for x, y, _, sc in sel:
        s = sc * rng.uniform(0.9, 1.1); z0 = float(height(x, y)) - 0.2
        rot = rng.uniform(0, 2 * math.pi); c, sn = math.cos(rot), math.sin(rot)
        o = len(verts)
        T = tv * [tr_ * s, tr_ * s, th_ * s + 0.5 * cr * s] + [x, y, z0]
        verts += T.tolist(); faces += [tuple(o + q for q in f) for f in tf]
        cols += [lin(tcol)] * (4 * len(tf))
        tint = lin(ccol) * (1 + 0.16 * (rng.random() - 0.5))
        for bi in range(4):
            o = len(verts)
            br = cr * s * rng.uniform(0.45, 0.62)
            off = rng.normal(0, 0.5 * cr * s, 2); dz = rng.uniform(-0.45, 0.3) * cr * s
            Cv = cv * [br, br, br * sq]
            Cv = np.stack([Cv[:, 0] * c - Cv[:, 1] * sn, Cv[:, 0] * sn + Cv[:, 1] * c, Cv[:, 2]], 1) + [x + off[0], y + off[1], z0 + ch * s + dz]
            verts += Cv.tolist(); faces += [tuple(o + q for q in f) for f in cf]
            cols += [tint * rng.uniform(0.92, 1.08)] * (3 * len(cf))
    if not faces: continue
    tm = mat_vcol('tree_' + kn, 0.9); nt = tm.node_tree; b = nt.nodes['Principled BSDF']; vc = b.inputs['Base Color'].links[0].from_socket
    # leaf clumps (hand-made tex/leaf_clumps.png, tex_bake.py): cells ~0.35 m darken their edges and bump the crown so it reads as foliage
    lt = nt.nodes.new('ShaderNodeTexImage'); lt.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'leaf_clumps.png'))
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    nt.links.new(vc, mx.inputs[6]); nt.links.new(lt.outputs['Color'], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    ln = nt.nodes.new('ShaderNodeTexImage'); ln.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'leaf_normal.png')); ln.image.colorspace_settings.name = 'Non-Color'
    nm_ = nt.nodes.new('ShaderNodeNormalMap'); nm_.uv_map = 'UVMap'
    nt.links.new(ln.outputs['Color'], nm_.inputs['Color']); nt.links.new(nm_.outputs['Normal'], b.inputs['Normal'])
    ob = mk_obj('bg_trees_' + kn, verts, faces, tm)
    ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))
    set_uv_box(ob.data, 2.8 / 8)   # leaf_clumps.png tile = 8 cells of 1/2.8 m
    cl = []
    for f in faces: pass
    cols = np.array(cols) * 1.15   # texture stores the clump multiplier / 1.15; the x1.15 lives in the vertex colours
    if cols.max() > 1: print('WARN tree colour over 1', kn, cols.max())
    set_corner_col(ob.data, np.concatenate([np.clip(cols, 0, 1), np.ones((len(cols), 1))], 1))
print('trees built')

# courts as real geometry: slab per group (hand-made grain), white lines at ITF dimensions, net (no ground paint blur)
CJ = os.path.join(D, 'courts.json')
if os.path.exists(CJ):
    cj = json.load(open(CJ))
    CC = {}
    def court_mat(nm, rgb):   # court_grain.png (0.25 m tile, stored / 1.25) x the court colour x1.25 carried in vertex colour
        fc = [1.25 * c for c in srgb(rgb)]
        if max(fc) > 1: print('WARN court colour over 1, clamped', nm, fc)
        m = mat_mul(nm, os.path.join(HERE, 'tex', 'court_grain.png'), 0.75); CC[m.name] = [min(1.0, c) for c in fc] + [1.0]
        return m
    def tint(ob):
        me = ob.data; set_corner_col(me, np.tile(CC[me.materials[0].name], (len(me.loops), 1))); return ob
    mats = {k: court_mat('court_' + k, v) for k, v in cj['pal'].items()}
    for k, hull in cj['slabs']:
        H = np.array(hull, float); z = height(H[:, 0], H[:, 1]).max() + 0.04
        V = [(x, y, z) for x, y in H] + [(H[:, 0].mean(), H[:, 1].mean(), z)]; c = len(H)
        set_uv_box(tint(mk_obj('bg_court_slab_' + k, V, [[c, i, (i + 1) % c] for i in range(c)], mats[k])).data, 4.0)   # grain tile 0.25 m
    white = bpy.data.materials.new('court_line'); white.use_nodes = True; white.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.86, 0.86, 0.84, 1)
    net = bpy.data.materials.new('court_net'); net.use_nodes = True; nb = net.node_tree.nodes['Principled BSDF']
    nb.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1); nb.inputs['Alpha'].default_value = 0.55
    LV, LF, NV, NF = [], [], [], []
    def seg(cx, cy, ux, uy, x0, y0, x1, y1, z, w=0.05):
        wx, wy = -uy, ux; P0 = (cx + ux * x0 + wx * y0, cy + uy * x0 + wy * y0); P1 = (cx + ux * x1 + wx * y1, cy + uy * x1 + wy * y1)
        dx, dy = P1[0] - P0[0], P1[1] - P0[1]; L = math.hypot(dx, dy); nx, ny = -dy / L * w / 2, dx / L * w / 2; n = len(LV)
        LV.extend([(P0[0] + nx, P0[1] + ny, z), (P1[0] + nx, P1[1] + ny, z), (P1[0] - nx, P1[1] - ny, z), (P0[0] - nx, P0[1] - ny, z)]); LF.append([n, n + 1, n + 2, n + 3])
    nc = 0
    for k, cx, cy, ang, L_, W_ in cj['courts']:
        if L_ < 23.5 or W_ < 10.8: continue   # OSM box smaller than a doubles court: no lines rather than wrong ones
        ux, uy = math.cos(ang), math.sin(ang); _cx_ = np.array([cx + ux * i * L_ / 2 - uy * j * W_ / 2 for i in (-1, 1) for j in (-1, 1)]); _cy_ = np.array([cy + uy * i * L_ / 2 + ux * j * W_ / 2 for i in (-1, 1) for j in (-1, 1)])
        z = float(height(_cx_, _cy_).max()) + 0.05; nc += 1
        X, Y, SY, SV = 11.885, 5.485, 4.115, 6.40
        for a, b, c_, d in [(-X, -Y, X, -Y), (-X, Y, X, Y), (-X, -Y, -X, Y), (X, -Y, X, Y), (-X, -SY, X, -SY), (-X, SY, X, SY),
                            (-SV, -SY, -SV, SY), (SV, -SY, SV, SY), (-SV, 0, SV, 0), (-X, 0, -X + 0.1, 0), (X - 0.1, 0, X, 0)]:
            seg(cx, cy, ux, uy, a, b, c_, d, z)
        wx, wy = -uy, ux; n = len(NV)   # net: 0.914 m at the centre strap, posts 0.914 m outside the doubles lines
        for yy, hh in [(-Y - 0.914, 1.07), (0, 0.914), (Y + 0.914, 1.07)]:
            NV.extend([(cx + wx * yy, cy + wy * yy, z), (cx + wx * yy, cy + wy * yy, z + hh)])
        NF.extend([[n, n + 2, n + 3, n + 1], [n + 2, n + 4, n + 5, n + 3]])
    for cx, cy, ang, L_, W_ in cj.get('hockey', []):   # FIH pitch 91.4 x 55 m on a run-off slab (the OSM box)
        ux, uy = math.cos(ang), math.sin(ang); wx, wy = -uy, ux; z0 = float(height(np.array([cx]), np.array([cy]))[0])
        def quad(hl, hw, z, nm, mat):
            V = [(cx + ux * a * hl + wx * b * hw, cy + uy * a * hl + wy * b * hw, z) for a, b in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
            set_uv_box(tint(mk_obj(nm, V, [[0, 1, 2, 3]], mat)).data, 4.0)
        quad(L_ / 2, W_ / 2, z0 + 0.04, 'bg_hockey_runoff', mats['turf_runoff'])
        HX, HY = 45.7, 27.5; quad(HX, HY, z0 + 0.05, 'bg_hockey_field', mats['turf_blue']); z = z0 + 0.06
        for a, b, c_, d in [(-HX, -HY, HX, -HY), (-HX, HY, HX, HY), (-HX, -HY, -HX, HY), (HX, -HY, HX, HY), (0, -HY, 0, HY),
                            (-HX + 22.9, -HY, -HX + 22.9, HY), (HX - 22.9, -HY, HX - 22.9, HY)]:
            seg(cx, cy, ux, uy, a, b, c_, d, z, 0.075)
        for sgn in (-1, 1):   # shooting circle: 14.63 m quarter arcs from each post (1.83 m off centre) joined by 3.66 m; dashed 5 m line
            for r, dash in [(14.63, False), (19.63, True)]:
                pts = [(sgn * (HX - r * math.cos(t)), -1.83 - r * math.sin(t)) for t in np.linspace(math.pi / 2, 0, 16)] +                       [(sgn * (HX - r * math.cos(t)), 1.83 + r * math.sin(t)) for t in np.linspace(0, math.pi / 2, 16)]
                for i, ((a, b), (c_, d)) in enumerate(zip(pts, pts[1:])):
                    if dash and i % 3: continue
                    seg(cx, cy, ux, uy, a, b, c_, d, z, 0.075)
        print('hockey pitch', round(L_, 1), round(W_, 1))
    if LV: mk_obj('bg_court_lines', LV, LF, white)
    if NV: mk_obj('bg_court_nets', NV, NF, net)
    print('courts', len(cj['slabs']), 'slabs', nc, 'lined')
# ---------- export background, then add the ground model for renders ----------
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'scene_bg.glb'), export_format='GLB', use_selection=False)
glb = os.path.normpath(os.path.join(HERE, spec['glb']))
bpy.ops.import_scene.gltf(filepath=glb)
if spec.get('seats_dir'):   # seats the game instances (MultiMesh) at load, not in the GLB
    import sys; sys.path.insert(0, HERE); from add_seats import add_seats; add_seats(os.path.normpath(os.path.join(HERE, spec['seats_dir'])))
FO = os.path.join(D, 'fence_mask.npy')
if spec.get('trim_base') and os.path.exists(FO):   # the model's square base stops at its fence (scene copy only, the GLB is untouched)
    FM = np.load(FO); FN = FM.shape[0]
    _p = np.pad(FM, 8, mode='edge'); _dil = np.zeros_like(FM); _ero = np.ones_like(FM)
    for di in range(-8, 9, 2):
        for dj in range(-8, 9, 2):
            sh = _p[8 + di:8 + di + FN, 8 + dj:8 + dj + FN]; _dil |= sh; _ero &= sh
    FB = _dil & ~_ero
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.name.split('.')[0] in spec['trim_base']]:
        bm = bmesh.new(); bm.from_mesh(o.data); M = o.matrix_world
        def _band(p):   # within ~4 m of the trim line: refine there so the cut edge follows the mask, not a 3 m sawtooth
            i, j = int((260 - p.y) / 0.5), int((p.x + 260) / 0.5)
            return 0 <= i < FN and 0 <= j < FN and FB[i, j]
        for _ in range(16):   # split long fan triangles (UVs interpolate) so the cut follows the mask, not a face centre
            long_ = []
            for e in bm.edges:
                a_, b_ = M @ e.verts[0].co, M @ e.verts[1].co; L_ = (a_ - b_).length
                if L_ > 3.0 or (L_ > 0.6 and _band((a_ + b_) / 2)): long_.append(e)
            if not long_: break
            bmesh.ops.subdivide_edges(bm, edges=long_, cuts=1, use_grid_fill=False)
            bmesh.ops.triangulate(bm, faces=bm.faces[:])
        kill = []
        for f in bm.faces:
            c = M @ f.calc_center_median(); i, j = int((260 - c.y) / 0.5), int((c.x + 260) / 0.5)
            if not (0 <= i < FN and 0 <= j < FN and FM[i, j]): kill.append(f)
        bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(o.data); bm.free()
        print('trimmed', o.name, len(kill), 'faces')
# AFL ovals outside the model: OSM outline = boundary line; AFL Laws markings (centre square 50 m, circles 3 m / 10 m with the
# dividing line parallel to the goal lines, goal squares 9 x 6.4 m, 50 m arcs from the centre of each goal line); goal and behind posts 6.4 m apart, no nets
OJ = os.path.join(D, 'ovals.json')
if os.path.exists(OJ):
    ovs = json.load(open(OJ))
    wm = bpy.data.materials.new('oval_line'); wm.use_nodes = True; wm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.86, 0.86, 0.84, 1)
    pm = bpy.data.materials.new('oval_post'); pm.use_nodes = True; pm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.9, 0.9, 0.88, 1)
    OLV, OLF, PV, PF = [], [], [], []
    def wseg(P0, P1, z, w=0.10):
        dx, dy = P1[0] - P0[0], P1[1] - P0[1]; L = math.hypot(dx, dy)
        if L < 1e-6: return
        if L > 3.0:   # split so the line follows the ground between terrain grid points
            k = int(math.ceil(L / 3.0))
            for i in range(k): wseg((P0[0] + dx * i / k, P0[1] + dy * i / k), (P0[0] + dx * (i + 1) / k, P0[1] + dy * (i + 1) / k), z, w)
            return
        nx, ny = -dy / L * w / 2, dx / L * w / 2; n = len(OLV)
        z0_, z1_ = (float(v) + 0.08 for v in height(np.array([P0[0], P1[0]]), np.array([P0[1], P1[1]])))   # draped: ground height at each end
        OLV.extend([(P0[0] + nx, P0[1] + ny, z0_), (P1[0] + nx, P1[1] + ny, z1_), (P1[0] - nx, P1[1] - ny, z1_), (P0[0] - nx, P0[1] - ny, z0_)]); OLF.append([n, n + 1, n + 2, n + 3])
    def inside(x, y, poly):
        c = False; n = len(poly)
        for i in range(n):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c = not c
        return c
    def post(x, y, z, h, r=0.15):
        n = len(PV); k = 8
        for zz in (z, z + h):
            PV.extend([(x + r * math.cos(2 * math.pi * i / k), y + r * math.sin(2 * math.pi * i / k), zz) for i in range(k)])
        PF.extend([[n + i, n + (i + 1) % k, n + k + (i + 1) % k, n + k + i] for i in range(k)]); PF.append([n + k + i for i in range(k)])
    for (cx, cy, ang, L_, W_), poly in ovs:
        ux, uy = math.cos(ang), math.sin(ang); wx, wy = -uy, ux
        z = float(height(np.array([cx]), np.array([cy]))[0]) + 0.03
        def W(a, b): return (cx + ux * a + wx * b, cy + uy * a + wy * b)
        def L(a, b, c_, d): wseg(W(a, b), W(c_, d), z)
        for i in range(len(poly)): wseg(poly[i], poly[(i + 1) % len(poly)], z)   # boundary line
        hl = L_ / 2
        for a, b, c_, d in [(-25, -25, 25, -25), (25, -25, 25, 25), (25, 25, -25, 25), (-25, 25, -25, -25), (0, -5, 0, 5)]: L(a, b, c_, d)
        for r in (1.5, 5.0):
            pts = [(r * math.cos(t), r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 33)]
            for (a, b), (c_, d) in zip(pts, pts[1:]): L(a, b, c_, d)
        for sg in (-1, 1):
            g = sg * hl
            for a, b, c_, d in [(g, -3.2, g - sg * 9, -3.2), (g - sg * 9, -3.2, g - sg * 9, 3.2), (g - sg * 9, 3.2, g, 3.2), (g, -9.6, g, 9.6)]: L(a, b, c_, d)
            arc = [(g - sg * 50 * math.cos(t), 50 * math.sin(t)) for t in np.linspace(-math.pi / 2, math.pi / 2, 61)]
            for (a, b), (c_, d) in zip(arc, arc[1:]):
                if inside(*W(a, b), poly) and inside(*W(c_, d), poly): L(a, b, c_, d)
            for b, h in [(-9.6, 6.5), (-3.2, 12.0), (3.2, 12.0), (9.6, 6.5)]: post(*W(g, b), z - 0.03, h)
        print('afl oval', round(cx), round(cy), 'length', round(L_, 1), 'width', round(W_, 1))
    if OLV: mk_obj('bg_oval_lines', OLV, OLF, wm)
    if PV: mk_obj('bg_oval_posts', PV, PF, pm)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'scene.blend'))
print('SAVED', OUT)
