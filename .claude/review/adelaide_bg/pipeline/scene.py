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
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = rough
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
n = near.shape[0]
g = np.arange(n) * NS - NE
X, Y = np.meshgrid(g, g)
Z = near.copy(); Z[np.hypot(X, Y) < R0 + 5] -= 0.15
# the model's own flat ground (apron) box: sink the terrain under it so no corner pokes through
if spec.get('pad_box_m'):
    hx, hy = spec['pad_box_m']; Z[(np.abs(X) < hx + NS) & (np.abs(Y) < hy + NS)] = np.minimum(Z[(np.abs(X) < hx + NS) & (np.abs(Y) < hy + NS)], -0.3)
_SF = json.load(open(os.path.join(D, 'surfaces.json')))
_gi = bpy.data.images.load(os.path.join(D, 'ground_mask.png')); _gi.colorspace_settings.name = 'Non-Color'; _r = _gi.size[1]
_gm = np.empty(len(_gi.pixels), np.float32); _gi.pixels.foreach_get(_gm); _gm = _gm.reshape(_r, _gi.size[0], 4)   # rows run south to north
_ix = np.clip(((X + NE) / (2 * NE) * _r).astype(int), 0, _r - 1); _iy = np.clip(((Y + NE) / (2 * NE) * _r).astype(int), 0, _r - 1)
_wi = bpy.data.images.load(os.path.join(D, 'water_id.png')); _wi.colorspace_settings.name = 'Non-Color'; _wi.alpha_mode = 'NONE'
_wa = np.empty(len(_wi.pixels), np.float32); _wi.pixels.foreach_get(_wa); _wa = np.rint(_wa.reshape(_wi.size[1], _wi.size[0], 4)[..., 0] * 255).astype(int)   # rows south to north
_wid = _wa[np.clip(((Y + NE) / (2 * NE) * _wi.size[1]).astype(int), 0, _wi.size[1] - 1), np.clip(((X + NE) / (2 * NE) * _wi.size[0]).astype(int), 0, _wi.size[0] - 1)]
for _w in _SF['water']:   # sink the terrain 0.15 m under its own water body only
    _sel = _wid == _w['body']
    Z[_sel] = np.minimum(Z[_sel], _w['z'] - 0.15)
Z0 = Z.copy()
V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
ii = np.arange(n - 1)
I, J = np.meshgrid(ii, ii)
a = (J * n + I).ravel()
F = np.stack([a, a + 1, a + n + 1, a + n], 1)
gm = mat_img('ground', os.path.join(D, 'ground.png'), 0.8)
_nt = gm.node_tree; _b = _nt.nodes['Principled BSDF']; _base = _b.inputs['Base Color'].links[0].from_socket
_uvd = _nt.nodes.new('ShaderNodeUVMap'); _uvd.uv_map = 'UVDetail'   # UVDetail: 1 unit = 4 m = one detail tile
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
_nt.links.new(_base, _mx.inputs[6]); _nt.links.new(_fd.outputs[2], _mx.inputs[7])
_lift = _nt.nodes.new('ShaderNodeMix'); _lift.data_type = 'RGBA'; _lift.blend_type = 'MULTIPLY'; _lift.inputs['Factor'].default_value = 1.0
_lift.inputs[7].default_value = (1.21, 1.21, 1.21, 1)   # 1 / detail mean 0.826 keeps the painted value
_nt.links.new(_mx.outputs[2], _lift.inputs[6]); _nt.links.new(_lift.outputs[2], _b.inputs['Base Color'])
ob = mk_obj('bg_near_ground', V, F.tolist(), gm)
loops = F.ravel()
uv = np.stack([(V[loops, 0] + NE) / (2 * NE), (V[loops, 1] + NE) / (2 * NE)], 1)
set_uv(ob.data, uv)
_ud = ob.data.uv_layers.new(name='UVDetail'); _ud.data.foreach_set('uv', (uv * (2 * NE / 4.0)).astype(np.float32).ravel())
for p in ob.data.polygons: p.use_smooth = True
_GROUND = ob
# shore band: densify the terrain within ~9 m of each water body and slope it evenly over 6 m from the land down to
# that body's level - 0.15 m, so banks no longer step at the terrain grid
import mathutils, mathutils.kdtree, mathutils.bvhtree
_sp, _sz, _wv, _wt = [], [], [], []
for _w in _SF['water']:
    _v = np.array(_w['v'], float); _cnt = {}
    for _t in _w['t']:
        _wt.append([len(_wv) + q for q in _t])
        for _a, _b2 in ((_t[0], _t[1]), (_t[1], _t[2]), (_t[2], _t[0])):
            _k = (min(_a, _b2), max(_a, _b2)); _cnt[_k] = _cnt.get(_k, 0) + 1
    _wv += [(x, y, 0.0) for x, y in _v]
    for (_a, _b2), _c in _cnt.items():
        if _c != 1: continue
        _L = np.linalg.norm(_v[_b2] - _v[_a]); _m = max(1, int(_L / 0.75))
        for _f in np.linspace(0, 1, _m + 1): _sp.append(_v[_a] + (_v[_b2] - _v[_a]) * _f); _sz.append(_w['z'])
_WIN = mathutils.bvhtree.BVHTree.FromPolygons(_wv, _wt) if _wt else None
if _sp:
    _kd = mathutils.kdtree.KDTree(len(_sp))
    for _i, _q in enumerate(_sp): _kd.insert((_q[0], _q[1], 0.0), _i)
    _kd.balance()
    def _near(x, y): _c, _i, _d = _kd.find((x, y, 0.0)); return _d, _sz[_i]
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for _ in range(4):   # 7.5 m grid -> ~0.95 m inside the band
        _ed = [e for e in bm.edges if e.calc_length() > 1.0 and _near(*((e.verts[0].co.xy + e.verts[1].co.xy) / 2))[0] < 9.0]
        if not _ed: break
        bmesh.ops.subdivide_edges(bm, edges=_ed, cuts=1, use_grid_fill=True)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    _nb = 0
    for v_ in bm.verts:
        d_, wz_ = _near(v_.co.x, v_.co.y)
        if d_ > 6.0: continue
        _in = _WIN is not None and _WIN.ray_cast(mathutils.Vector((v_.co.x, v_.co.y, 10.0)), mathutils.Vector((0, 0, -1)))[0] is not None
        lo = wz_ - 0.15
        if _in: v_.co.z = min(v_.co.z, lo)
        else:
            top = float(height(v_.co.x, v_.co.y)) if 'height' in globals() else v_.co.z
            v_.co.z = lo + (max(top, lo) - lo) * (d_ / 6.0); _nb += 1
    bm.to_mesh(ob.data); bm.free(); ob.data.update(); print('shore band verts', _nb, 'ground faces', len(ob.data.polygons))


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
            long_ = [e for e in bm.edges if e.calc_length() > (seg if (e.verts[0].co.xy + e.verts[1].co.xy).length < 800 else 3 * NS)]   # fine within 400 m of the oval, terrain-grid size beyond
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
surf_obj('bg_oval2_skin', _SF['oval2'], mat_img('oval2_dirt', os.path.join(_TX, 'adl_oval_grass.png'), 0.95), 0.04, 48.0)
_om = bpy.data.materials.get('oval2_dirt')
if _om:
    _ont = _om.node_tree; _ob = _ont.nodes['Principled BSDF']; _src = _ob.inputs['Base Color'].links[0].from_socket
    _pt = _ont.nodes.new('ShaderNodeTexImage'); _pt.image = bpy.data.images.load(os.path.join(_TX, 'adl_patch60.png')); _pt.image.colorspace_settings.name = 'Non-Color'
    _mp = _ont.nodes.new('ShaderNodeMapping'); _mp.inputs['Scale'].default_value = (0.1, 0.1, 1); _tc = _ont.nodes.new('ShaderNodeUVMap')
    _ont.links.new(_tc.outputs['UV'], _mp.inputs['Vector']); _ont.links.new(_mp.outputs['Vector'], _pt.inputs['Vector'])
    _m1 = _ont.nodes.new('ShaderNodeMath'); _m1.operation = 'MULTIPLY'; _m1.inputs[1].default_value = 1.25; _ont.links.new(_pt.outputs['Color'], _m1.inputs[0])
    _mx = _ont.nodes.new('ShaderNodeMix'); _mx.data_type = 'RGBA'; _mx.blend_type = 'MULTIPLY'; _mx.inputs[0].default_value = 1
    _ont.links.new(_src, _mx.inputs[6]); _ont.links.new(_m1.outputs[0], _mx.inputs[7]); _ont.links.new(_mx.outputs[2], _ob.inputs['Base Color'])
for _cx, _cy, _w, _h, _ang in spec.get('cricket_squares', []):   # square = grey-brown worked clay over the same grain
    _ca, _sa = math.cos(math.radians(_ang)), math.sin(math.radians(_ang))
    _q = [(_cx + _ca * a_ * _w / 2 - _sa * b_ * _h / 2, _cy + _sa * a_ * _w / 2 + _ca * b_ * _h / 2) for a_, b_ in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
    surf_obj('bg_cricket_square', {'v': _q, 't': [[0, 1, 2], [0, 2, 3]]}, mat_tint('cricket_square', os.path.join(_TX, 'adl_oval_grass.png'), (0.85, 0.82, 0.75), 0.9), 0.07, 12.0, seg=1.5)
for _i, (_x0, _y0, _x1, _y1) in enumerate(spec.get('turf_strips', [])):   # green practice turf on Oval No.2 (aerial)
    surf_obj('bg_turf_strip%d' % _i, {'v': [(_x0, _y0), (_x1, _y0), (_x1, _y1), (_x0, _y1)], 't': [[0, 1, 2], [0, 2, 3]]}, mat_tint('turf_strip', os.path.join(_TX, 'adl_oval_grass.png'), (0.55, 0.95, 0.55), 0.9), 0.07, 12.0, seg=1.5)

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
    deck_c = lin((204, 204, 199)); rail_c = lin((189, 194, 201))
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
                for (qx, qy), zz in zip([(P[i][0] + nx, P[i][1] + ny), (P[i + 1][0] + nx, P[i + 1][1] + ny), (P[i + 1][0] - nx, P[i + 1][1] - ny), (P[i][0] - nx, P[i][1] - ny)], (za, zb, zb, za)): verts.append((qx, qy, zz - 1.0))
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
                    faces.append((s0, s0 + 1, s0 + 2, s0 + 3)); cols.extend([rail_c] * 4)
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
        ob = mk_obj('bg_bridges', verts, faces, mat_vcol('bridge', 0.8))
        set_corner_col(ob.data, np.concatenate([np.array(cols), np.ones((len(cols), 1))], 1))

# ---------- rails: sleeper bed + two steel rails draped on the terrain (broad gauge 1.6 m) ----------
RLP = os.path.join(D, 'rails.json')
if spec.get('rail_geo') and os.path.exists(RLP):
    verts, faces, cols = [], [], []
    bed_c = lin(tuple(PAL.get('track', (70, 64, 60)))); steel_c = lin((168, 170, 172))
    def drape_strip(P, off, w, lift, c):
        # flat ribbon offset sideways by off, w wide, lift above terrain; P densified to <=4 m
        n = len(P); L_ = []
        for i in range(n):
            a_ = P[max(i - 1, 0)]; b_ = P[min(i + 1, n - 1)]
            d_ = b_ - a_; L = max(np.hypot(*d_), 1e-6); L_.append(np.array([-d_[1], d_[0]]) / L)
        N_ = np.array(L_); C = P + N_ * off
        A = C + N_ * w / 2; B = C - N_ * w / 2
        zc = np.max([height(C[:, 0] + N_[:, 0] * o, C[:, 1] + N_[:, 1] * o) for o in (-1.6, 0, 1.6)], 0)
        if RF is not None:   # in the cutting the track bed sits on the smoothed floor, never draped up a bank
            fl = samp(np.nan_to_num(RF, nan=-1e4), NE, NS, C[:, 0], C[:, 1])
            zc = np.where(fl > -100, fl, zc)
        za = zc + lift; zb = zc + lift
        s0 = len(verts)
        for i in range(n):
            verts.append((A[i, 0], A[i, 1], float(za[i]))); verts.append((B[i, 0], B[i, 1], float(zb[i])))
        for i in range(n - 1):
            faces.append((s0 + 2 * i, s0 + 2 * i + 1, s0 + 2 * i + 3, s0 + 2 * i + 2)); cols.extend([c] * 4)
    RF = np.load(os.path.join(D, 'rail_floor.npy')) if os.path.exists(os.path.join(D, 'rail_floor.npy')) else None
    KE = spec.get('rail_cut', {}).get('keep_ellipse')
    CM = np.load(os.path.join(D, 'rail_cm.npy')) if os.path.exists(os.path.join(D, 'rail_cm.npy')) else None
    KFP = os.path.join(D, 'footprint.json')
    KF = np.array(json.load(open(KFP))) if spec.get('rail_cut', {}).get('keep_footprint') and os.path.exists(KFP) else None
    for pts in json.load(open(RLP)):
        P = np.array(pts, float); Q = [P[0]]
        for p2 in P[1:]:
            k = max(1, int(math.ceil(np.hypot(*(p2 - Q[-1])) / 4.0)))
            for j in range(1, k + 1): Q.append(Q[-1] + (p2 - Q[-1]) * (1.0 / (k - j + 1)))
        Q = np.array(Q)
        if KF is not None or KE:   # tracks under the ground model are hidden by it: split them out
            if KF is not None: ok = np.hypot(Q[:, 0], Q[:, 1]) > KF[((np.degrees(np.arctan2(Q[:, 1], Q[:, 0])) % 360) // 2).astype(int)] + 1.0
            else: ex, ey, ea, eb = KE; ok = np.hypot((Q[:, 0] - ex) / ea, (Q[:, 1] - ey) / eb) > 1.04
            if CM is not None:   # never on a bank: only where the cutting floor is flat, or wholly outside the cutting
                cmq = samp(CM, NE, NS, Q[:, 0], Q[:, 1]); ok &= ~((cmq > 0.02) & (cmq < 0.92))
            runs = np.split(np.arange(len(Q)), np.where(np.diff(ok.astype(int)) != 0)[0] + 1)
            segs = [Q[r_] for r_ in runs if ok[r_[0]] and len(r_) > 1 and np.hypot(*np.diff(Q[r_], axis=0).T).sum() > 30]
        else: segs = [Q]
        for Q in segs:
            drape_strip(Q, 0, 2.8, 0.2, bed_c)
            for sd in (-0.8, 0.8): drape_strip(Q, sd, 0.18, 0.32, steel_c)
        continue
        drape_strip(Q, 0, 2.8, 0.2, bed_c)
        for sd in (-0.8, 0.8): drape_strip(Q, sd, 0.18, 0.32, steel_c)
    if faces:
        ob = mk_obj('bg_rails', verts, faces, mat_vcol('rails', 0.6))
        set_corner_col(ob.data, np.concatenate([np.array(cols), np.ones((len(cols), 1))], 1))

# ---------- buildings ----------
BL = json.load(open(os.path.join(D, 'buildings.json')))
def mat_roof(kind):   # hand-made roof texture / its linear mean x the roof colour (vertex colour)
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
def build_class(cls, tex, tw, th, var=None, nvar=1):
    verts, faces, cols, uvs = [], [], [], []
    RF = {'metal': [[], [], [], []], 'tile': [[], [], [], []], 'far': [[], [], [], []], 'corr': [[], [], [], []]}   # roof meshes: verts, faces, cols, uvs
    walls = [lin(c) for c in PAL['walls_' + cls]]
    roofs = [lin(c) for c in PAL['roofs_' + ('house' if cls == 'house' else 'flat')]]
    for b in BL:
        if b['c'] != cls: continue
        if var is not None and int(abs(b['p'][0][0] * 7.31 + b['p'][0][1] * 13.17)) % nvar != var: continue   # facade variant: stable per building
        P = np.array(b['p'], float)
        cxy = P.mean(0)
        base = float(height(cxy[0], cxy[1])) - 1.0
        h = b['h']
        wc = walls[b['wall'] % len(walls)] * (1 + 0.06 * (rng.random() - 0.5))
        rc = roofs[b['roof'] % len(roofs)] * (1 + 0.08 * (rng.random() - 0.5))
        _kov, _sol = None, False
        for _e in spec.get('roof_col_at', []):   # roof colour read off the aerial for named buildings (+ optional kind, 'solar')
            if math.hypot(cxy[0] - _e[0], cxy[1] - _e[1]) < 25: rc = lin(_e[2]); _kov = _e[3] if len(_e) > 3 else None; _sol = 'solar' in _e[4:]
        pitched = cls == 'house' and len(P) <= 8
        rh = min(2.6, math.sqrt(abs(b.get('a', 150))) / 5) if pitched else 0
        top = base + 1.0 + h - rh
        k = len(P); s0 = len(verts)
        for x, y in P: verts.append((x, y, base))
        for x, y in P: verts.append((x, y, top))
        per = 0.0
        for i in range(k):
            j = (i + 1) % k
            L = float(np.hypot(*(P[j] - P[i])))
            faces.append((s0 + i, s0 + j, s0 + k + j, s0 + k + i))
            cols += [wc] * 4
            u0, u1 = per / tw, (per + L) / tw
            v0, v1 = -1.0 / th, (top - base - 1.0) / th
            uvs += [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            per += L
        # roof: own mesh, hand-made texture, planar UVs along the building's longest side (one tile = 3.04 m)
        E = np.diff(np.vstack([P, P[:1]]), axis=0); e = E[np.argmax(np.hypot(E[:, 0], E[:, 1]))]; th_ = math.atan2(e[1], e[0])
        ct, st = math.cos(th_), math.sin(th_)
        src = b.get('roof_c'); kind = 'far' if b.get('a', 0) >= 1500 else 'corr' if not pitched else 'tile' if (cls == 'house' and PAL['roofs_house'][b['roof'] % len(PAL['roofs_house'])][0] > 1.3 * PAL['roofs_house'][b['roof'] % len(PAL['roofs_house'])][1]) else 'metal'
        if cls == 'tower':
            Q = cxy + 0.45 * (P - cxy); q0 = len(verts); pt = top + 4.0
            for x_, y_ in Q: verts.append((x_, y_, top))
            for x_, y_ in Q: verts.append((x_, y_, pt))
            for i in range(k):
                faces.append((q0 + i, q0 + (i + 1) % k, q0 + k + (i + 1) % k, q0 + k + i)); cols += [wc * 0.85] * 4; uvs += [(0.001, 0.999)] * 4
            pr = RF['metal']; p0 = len(pr[0])
            for x_, y_ in Q: pr[0].append((x_, y_, pt)); pr[3].append((x_ / 3.04, y_ / 3.04))
            pr[1].append(tuple(p0 + i for i in range(k))); pr[2].extend([rc] * k)
        if _kov: kind = _kov
        if _sol: SOLAR.append((P.copy(), top, th_))
        rv, rf, rcl, ruv = RF[kind]; r0 = len(rv)
        def ruv_(x, y):
            if kind == 'far': return ((x * ct + y * st) / 24.0, (-x * st + y * ct) / 24.0)
            if kind == 'corr': return ((-x * st + y * ct) / 3.04, (x * ct + y * st) / 3.04)   # texture ribs run along v = the long axis
            return ((x * ct + y * st) / 3.04, (-x * st + y * ct) / 3.04)
        for x, y in P: rv.append((x, y, top)); ruv.append(ruv_(x, y))
        if pitched:
            rv.append((cxy[0], cxy[1], top + rh)); ruv.append(ruv_(cxy[0], cxy[1]))
            for i in range(k):
                rf.append((r0 + i, r0 + (i + 1) % k, r0 + k)); rcl += [rc] * 3
        else:
            rf.append(tuple(r0 + i for i in range(k))); rcl += [rc] * k
    if not faces: return
    _sx = '' if var is None else '_v%d' % var
    ob = mk_obj('bg_bld_' + cls + _sx, verts, faces, mat_facade('facade_' + cls + _sx, os.path.join(HERE, 'tex', tex)))
    set_corner_col(ob.data, np.concatenate([np.array(cols), np.ones((len(cols), 1))], 1))
    set_uv(ob.data, uvs)
    for kind, (rv, rf, rcl, ruv) in RF.items():
        if not rf: continue
        ro = mk_obj('bg_roof_%s_%s' % (cls, kind), rv, rf, mat_roof(kind) if kind in ('far', 'corr') else mat_facade('roof_%s_%s' % (cls, kind), os.path.join(HERE, 'tex', 'roof_%s.png' % kind)))
        set_corner_col(ro.data, np.concatenate([np.array(rcl), np.ones((len(rcl), 1))], 1))
        set_uv(ro.data, [ruv[i] for f_ in rf for i in f_])
SOLAR = []
for b in BL:
    P = np.array(b['p']); x, y = P[:, 0], P[:, 1]
    b['a'] = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
exec(open(os.path.join(HERE, 'landmarks.py'), encoding='utf-8').read())   # hand-built landmarks replace their generic boxes
build_class('house', spec.get('house_wall_tex', 'wall.png'), 3.6, 3.2)
# several hand-made facades per class (tex_towers.py + texture session's city_office/city_far), one per building
for _i, (_t, _w, _h) in enumerate([('wall.png', 3.6, 3.2), ('adl_conc.png', 3.0, 3.6), ('adl_band.png', 6.0, 3.6)]): build_class('block', _t, _w, _h, _i, 3)
for _i, (_t, _w, _h) in enumerate([('cbd_curtain.png', 6.0, 3.6), ('cbd_punched.png', 6.0, 3.6), ('cbd_stone.png', 6.0, 3.6), ('cbd_fins.png', 6.0, 3.6), ('cbd_ribbon.png', 6.0, 3.6)]): build_class('tower', _t, _w, _h, _i, 5)
def _solar_build():   # rows of 1.0 x 1.7 m panels on a 2.2 m grid along the roof's long side, 2.5 m clear of the roof edge, a walkway every 4th row
    SV, SF, SU = [], [], []
    for P, top, th_ in SOLAR:
        ct, st = math.cos(th_), math.sin(th_); E = np.vstack([P, P[:1]])
        U = P @ np.array([ct, st]); W = P @ np.array([-st, ct])
        for i, u in enumerate(np.arange(U.min() + 2.5, U.max() - 2.5, 1.1)):
            for j, w in enumerate(np.arange(W.min() + 2.5, W.max() - 2.5, 2.2)):
                if j % 4 == 3: continue
                x, y = u * ct - w * st, u * st + w * ct
                c = False
                for k in range(len(P)):
                    (x1, y1), (x2, y2) = E[k], E[k + 1]
                    if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c = not c
                if not c: continue
                d = min(np.hypot(*(np.array([x, y]) - (E[k] + np.clip(np.dot(np.array([x, y]) - E[k], E[k + 1] - E[k]) / max(1e-6, np.dot(E[k + 1] - E[k], E[k + 1] - E[k])), 0, 1) * (E[k + 1] - E[k])))) for k in range(len(P)))
                if d < 2.5: continue
                n0 = len(SV)
                for a_, b_ in [(-0.5, -0.85), (0.5, -0.85), (0.5, 0.85), (-0.5, 0.85)]:
                    SV.append((x + a_ * ct - b_ * st, y + a_ * st + b_ * ct, top + 0.18 + 0.12 * (b_ > 0)))
                SF.append([n0, n0 + 1, n0 + 2, n0 + 3]); SU += [(0, 0), (1, 0), (1, 1), (0, 1)]
    if SF:
        o = mk_obj('bg_solar', SV, SF, mat_img('solar', os.path.join(HERE, 'tex', 'adl_solar.png'), 0.25)); set_uv(o.data, SU); print('solar panels', len(SF))
_solar_build()
print('buildings built')

# ---------- trees ----------
KIND = {  # canopy radius, canopy centre height, squash, trunk height, trunk radius, canopy rgb, trunk rgb, ico subdiv
 'ghost_gum': (4.6, 6.8, 0.7, 4.0, 0.22, (132, 140, 96), (236, 230, 218), 1),
 'red_gum': (7.0, 10.0, 0.6, 5.5, 0.45, (112, 122, 86), (160, 152, 140), 1),
 'mulga': (1.5, 1.7, 0.7, 0.9, 0.1, (134, 132, 94), (96, 76, 60), 1),
 'elm': (6.5, 14.0, 0.85, 7.0, 0.5, (72, 98, 54), (76, 64, 54), 1),
 'plane': (5.5, 12.0, 0.9, 6.5, 0.4, (86, 110, 60), (150, 140, 120), 1),
}
TR = json.load(open(os.path.join(D, 'trees.json')))
TR = np.array(TR, float)
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
    for x, y, _ in sel:
        s = rng.uniform(0.75, 1.25); z0 = float(height(x, y)) - 0.2
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
    # leaf clumps (procedural, hand-set): Voronoi cells ~0.35 m darken their edges and bump the crown so it reads as foliage
    lt = nt.nodes.new('ShaderNodeTexImage'); lt.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'leaf_clumps.png'))
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    nt.links.new(vc, mx.inputs[6]); nt.links.new(lt.outputs['Color'], mx.inputs[7])
    lf = nt.nodes.new('ShaderNodeMix'); lf.data_type = 'RGBA'; lf.blend_type = 'MULTIPLY'; lf.inputs['Factor'].default_value = 1.0
    lf.inputs[7].default_value = (1.15, 1.15, 1.15, 1)   # texture stores the clump multiplier / 1.15
    nt.links.new(mx.outputs[2], lf.inputs[6]); nt.links.new(lf.outputs[2], b.inputs['Base Color'])
    ln = nt.nodes.new('ShaderNodeTexImage'); ln.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'leaf_normal.png')); ln.image.colorspace_settings.name = 'Non-Color'
    nm_ = nt.nodes.new('ShaderNodeNormalMap'); nm_.uv_map = 'UVMap'
    nt.links.new(ln.outputs['Color'], nm_.inputs['Color']); nt.links.new(nm_.outputs['Normal'], b.inputs['Normal'])
    ob = mk_obj('bg_trees_' + kn, verts, faces, tm)
    ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))
    set_uv_box(ob.data, 2.8 / 8)   # leaf_clumps.png tile = 8 cells of 1/2.8 m
    cl = []
    for f in faces: pass
    set_corner_col(ob.data, np.concatenate([np.array(cols), np.ones((len(cols), 1))], 1))
print('trees built')

# ---------- export background, then add the ground model for renders ----------
_gt = [n_ for n_ in _nt.nodes if n_.type == 'TEX_IMAGE' and n_.image and n_.image.name.startswith('ground.png')][0]
_nt.links.new(_gt.outputs['Color'], _b.inputs['Base Color'])
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'scene_bg.glb'), export_format='GLB', use_selection=False)
_nt.links.new(_lift.outputs[2], _b.inputs['Base Color'])
glb = os.path.normpath(os.path.join(HERE, spec['glb']))
if spec.get('model_blend'):   # model with its own (Blender) materials: link its objects in
    with bpy.data.libraries.load(os.path.normpath(os.path.join(HERE, spec['model_blend']))) as (_src, _dst): _dst.objects = list(_src.objects)
    for _o in _dst.objects: bpy.context.scene.collection.objects.link(_o)
else: bpy.ops.import_scene.gltf(filepath=glb)
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
        _FP = os.path.join(D, 'fence_outline.json')   # fence_outline.py (system python: Blender has no shapely)
        if os.path.exists(_FP):
            _ring = [tuple(q) for q in json.load(open(_FP))]; _k = len(_ring)
            if sum(_ring[i][0] * _ring[(i + 1) % _k][1] - _ring[(i + 1) % _k][0] * _ring[i][1] for i in range(_k)) < 0: _ring = _ring[::-1]   # CCW so the prism faces point out
            _pv = [(x, y, -30.0) for x, y in _ring] + [(x, y, 80.0) for x, y in _ring]
            _pf = [list(range(_k))[::-1], list(range(_k, 2 * _k))] + [[i, (i + 1) % _k, _k + (i + 1) % _k, _k + i] for i in range(_k)]
            _pm = bpy.data.meshes.new('trim_prism'); _pm.from_pydata(_pv, [], _pf); _pm.update()
            _po = bpy.data.objects.new('trim_prism', _pm); bpy.context.scene.collection.objects.link(_po)
            _md = o.modifiers.new('fence_cut', 'BOOLEAN'); _md.operation = 'INTERSECT'; _md.solver = 'EXACT'; _md.object = _po
            bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=_md.name)
            bpy.data.objects.remove(_po); print('fence cut', o.name, _k, 'pts', len(o.data.polygons), 'faces')
# courts as real geometry: slab per group (hand-made grain), white lines at ITF dimensions, net (no ground paint blur)
CJ = os.path.join(D, 'courts.json')
if os.path.exists(CJ):
    cj = json.load(open(CJ))
    def court_mat(nm, rgb):
        m = bpy.data.materials.new(nm); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
        gt = nt.nodes.new('ShaderNodeTexImage'); gt.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'court_grain.png'), check_existing=True)   # tex_bake.py, 0.25 m tile
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs[6].default_value = (*[1.12 * c for c in srgb(rgb)], 1); nt.links.new(gt.outputs['Color'], mx.inputs[7])   # grain stored / 1.12
        nt.links.new(mx.outputs[2], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.75
        return m
    mats = {k: court_mat('court_' + k, v) for k, v in cj['pal'].items()}
    _SL = []
    for k, hull in cj['slabs']:
        H = np.array(hull, float); z = height(H[:, 0], H[:, 1]).max() + 0.04; _SL.append((H, z))
        V = [(x, y, z) for x, y in H]   # slab outline is concave now (union of court boxes): ear-clip it
        F = [list(t) for t in mathutils.geometry.tessellate_polygon([[mathutils.Vector(v) for v in V]])]
        set_uv_box(mk_obj('bg_court_slab_' + k, V, F, mats[k]).data, 4.0)
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
                o_ = -L_ / 2 + w_ * (i + 0.5); _subs.append((k, cx + ux * o_, cy + uy * o_, ang + math.pi / 2, W_, w_))
        else: _subs.append((k, cx, cy, ang, L_, W_))
    cj['courts'] = [list(q) for q in _subs]
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
        if L_ < 23.5 or W_ < 10.5: continue   # OSM box smaller than a doubles court: no lines rather than wrong ones
        ux, uy = math.cos(ang), math.sin(ang); zs = _zslab(cx, cy); nc += 1
        hl, hw = max(L_ / 2 - 1.0, min(L_ / 2, 12.185)), max(W_ / 2 - 1.0, min(W_ / 2, 5.785))   # 1 m inside the box; never inside the doubles lines
        wx, wy = -uy, ux; q_ = len(PV_)
        if k != 'court_grass': PV_.extend([(cx + ux * a_ * hl + wx * b_ * hw, cy + uy * a_ * hl + wy * b_ * hw, zs + 0.01) for a_, b_ in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]) if k != 'court_grass' else None
        if k != 'court_grass': PF_.append([q_, q_ + 1, q_ + 2, q_ + 3])
        z = zs + 0.02
        X, Y, SY, SV = 11.885, 5.485, 4.115, 6.40
        for a, b, c_, d in [(-X, -Y, X, -Y), (-X, Y, X, Y), (-X, -Y, -X, Y), (X, -Y, X, Y), (-X, -SY, X, -SY), (-X, SY, X, SY),
                            (-SV, -SY, -SV, SY), (SV, -SY, SV, SY), (-SV, 0, SV, 0), (-X, 0, -X + 0.1, 0), (X - 0.1, 0, X, 0)]:
            seg(cx, cy, ux, uy, a, b, c_, d, z)
        wx, wy = -uy, ux; n = len(NV)   # net: 0.914 m at the centre strap, posts 0.914 m outside the doubles lines
        for yy, hh in [(-Y - 0.914, 1.07), (0, 0.914), (Y + 0.914, 1.07)]:
            NV.extend([(cx + wx * yy, cy + wy * yy, zs), (cx + wx * yy, cy + wy * yy, zs + hh)])
        NF.extend([[n, n + 2, n + 3, n + 1], [n + 2, n + 4, n + 5, n + 3]])
    for cx, cy, ang, L_, W_ in cj.get('hockey', []):   # FIH pitch 91.4 x 55 m on a run-off slab (the OSM box)
        ux, uy = math.cos(ang), math.sin(ang); wx, wy = -uy, ux; z0 = float(height(np.array([cx]), np.array([cy]))[0])
        def quad(hl, hw, z, nm, mat):
            V = [(cx + ux * a * hl + wx * b * hw, cy + uy * a * hl + wy * b * hw, z) for a, b in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
            mk_obj(nm, V, [[0, 1, 2, 3]], mat)
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
    if PV_: set_uv_box(mk_obj('bg_court_play', PV_, PF_, _play).data, 4.0)
    if LV: mk_obj('bg_court_lines', LV, LF, white)
    if NV: mk_obj('bg_court_nets', NV, NF, net)
    print('courts', len(cj['slabs']), 'slabs', nc, 'lined')
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
