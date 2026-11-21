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
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path, check_existing=True)
    ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'Col'
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1
    nt.links.new(ca.outputs['Color'], mul.inputs[6]); nt.links.new(t.outputs['Color'], mul.inputs[7])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    nt.links.new(t.outputs['Alpha'], mix.inputs[0]); nt.links.new(mul.outputs[2], mix.inputs[6]); nt.links.new(t.outputs['Color'], mix.inputs[7])
    nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    rm = nt.nodes.new('ShaderNodeMapRange'); rm.inputs['To Min'].default_value = rough_wall; rm.inputs['To Max'].default_value = 0.13
    import numpy as _np
    _px = _np.empty(len(t.image.pixels), _np.float32); t.image.pixels.foreach_get(_px)
    if t.image.channels == 4 and _px[3::4].max() > 0.01: nt.links.new(t.outputs['Alpha'], rm.inputs['Value']); nt.links.new(rm.outputs['Result'], b.inputs['Roughness'])
    else: b.inputs['Roughness'].default_value = rough_wall   # no glass in this texture: constant roughness, so the GLB gets no flat grey roughness image
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
Z0 = Z.copy()   # the drape height for the surfaces
_rd = _gm[_iy, _ix, 0] > 0.05
for _k in range(2):   # grow one grid cell each pass: a narrow road between grid points still gets sunk ground round it
    _g = _rd.copy(); _g[1:] |= _rd[:-1]; _g[:-1] |= _rd[1:]; _g[:, 1:] |= _rd[:, :-1]; _g[:, :-1] |= _rd[:, 1:]; _rd = _g
Z[_rd & False] -= 0.0   # (no sink: roads are ray-cast onto the terrain surface below)
for _w in _SF['water']:
    _wv = np.array(_w['v']); 
    if not len(_wv): continue
    _sel = (X > _wv[:, 0].min() - NS) & (X < _wv[:, 0].max() + NS) & (Y > _wv[:, 1].min() - NS) & (Y < _wv[:, 1].max() + NS) & (_gm[_iy, _ix, 1] > 0.5)
    if not _w.get('still'):
        Z[_sel] = np.minimum(Z[_sel], _w['z'] - 0.15); continue
    # still pond: grade, don't sink (texture session 2026-11-20). Bed 0.15 under the water; a 10 m ring rises linearly
    # from water + 0.1 at the shore to the natural height at its outer edge
    _b = (X > _wv[:, 0].min() - 12) & (X < _wv[:, 0].max() + 12) & (Y > _wv[:, 1].min() - 12) & (Y < _wv[:, 1].max() + 12)
    _in = _b & (_gm[_iy, _ix, 1] > 0.5)
    if not _in.any(): continue
    _P = np.column_stack([X[_in], Y[_in]]); _out = _b & ~_in
    _Q = np.column_stack([X[_out], Y[_out]])
    _d = np.sqrt(((_Q[:, None, :] - _P[None, :, :]) ** 2).sum(-1)).min(1) - NS / 2   # metres from the shore
    _t = np.clip(_d / 10.0, 0, 1); _zs = _w['z'] + 0.1
    _zo = Z[_out]; _r = _d < 10.0
    _zo[_r] = (_zs + (_zo - _zs) * _t)[_r]; Z[_out] = _zo
    Z[_in] = _w['z'] - 0.15
    Z0[_b] = Z[_b]   # reeds and paths drape on the graded bank
V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
ii = np.arange(n - 1)
I, J = np.meshgrid(ii, ii)
a = (J * n + I).ravel()
F = np.stack([a, a + 1, a + n + 1, a + n], 1)
gm = mat_img('ground', os.path.join(D, 'ground.png'), 0.8)
_nt = gm.node_tree; _b = _nt.nodes['Principled BSDF']; _base = _b.inputs['Base Color'].links[0].from_socket
BGT = 'D:/Temp/claude/2117a0e07442304a/b457f311-065b-4525-9ffd-7c62765dd586/scratchpad/bgtex/'
_uvd = _nt.nodes.new('ShaderNodeUVMap'); _uvd.uv_map = 'UVDetail'   # UVDetail: 1 unit = 4 m
def _tile(path, metres):
    mp = _nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (4.0 / metres,) * 3
    _nt.links.new(_uvd.outputs['UV'], mp.inputs['Vector'])
    t = _nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path, check_existing=True); _nt.links.new(mp.outputs['Vector'], t.inputs['Vector']); return t
_dt = _tile(BGT + 'perth/perth_sand_detail.png', 8.0)
_mx = _nt.nodes.new('ShaderNodeMix'); _mx.data_type = 'RGBA'; _mx.blend_type = 'MULTIPLY'; _mx.inputs['Factor'].default_value = 1.0
# texture session 2026-11-20: break the 8 m repeat and fade the detail with distance (GODOT TODO: same in the ground shader)
_mp2 = _nt.nodes.new('ShaderNodeMapping'); _mp2.inputs['Scale'].default_value = (4.0 * 0.37 / 8.0,) * 3; _mp2.inputs['Rotation'].default_value = (0, 0, math.radians(36.87))
_nt.links.new(_uvd.outputs['UV'], _mp2.inputs['Vector'])
_dt2 = _nt.nodes.new('ShaderNodeTexImage'); _dt2.image = _dt.image; _nt.links.new(_mp2.outputs['Vector'], _dt2.inputs['Vector'])
_avg = _nt.nodes.new('ShaderNodeMix'); _avg.data_type = 'RGBA'; _avg.inputs['Factor'].default_value = 0.5
_nt.links.new(_dt.outputs['Color'], _avg.inputs[6]); _nt.links.new(_dt2.outputs['Color'], _avg.inputs[7])
# contrast back: mean + (c - mean) x 1.414 (averaging two unrelated samples cuts the spread by sqrt 2)
_ct = _nt.nodes.new('ShaderNodeMix'); _ct.data_type = 'RGBA'; _ct.blend_type = 'MIX'; _ct.clamp_result = True; _ct.inputs['Factor'].default_value = 1.414
_ct.inputs[6].default_value = (0.563, 0.563, 0.563, 1); _nt.links.new(_avg.outputs[2], _ct.inputs[7])
_ct.clamp_factor = False
# fade to the mean from 150 m to 400 m from the camera
_cd = _nt.nodes.new('ShaderNodeCameraData'); _mr = _nt.nodes.new('ShaderNodeMapRange')
_mr.inputs['From Min'].default_value = 150.0; _mr.inputs['From Max'].default_value = 400.0
_nt.links.new(_cd.outputs['View Distance'], _mr.inputs['Value'])
_fd = _nt.nodes.new('ShaderNodeMix'); _fd.data_type = 'RGBA'; _fd.inputs[7].default_value = (0.563, 0.563, 0.563, 1)
_nt.links.new(_mr.outputs['Result'], _fd.inputs['Factor']); _nt.links.new(_ct.outputs[2], _fd.inputs[6])
_nt.links.new(_base, _mx.inputs[6]); _nt.links.new(_fd.outputs[2], _mx.inputs[7])
_lift = _nt.nodes.new('ShaderNodeMix'); _lift.data_type = 'RGBA'; _lift.blend_type = 'MULTIPLY'; _lift.inputs['Factor'].default_value = 1.0
_lift.inputs[7].default_value = (1.78, 1.78, 1.78, 1)   # 1 / sand detail mean 0.563 keeps the painted value
_nt.links.new(_mx.outputs[2], _lift.inputs[6]); _nt.links.new(_lift.outputs[2], _b.inputs['Base Color'])
ob = mk_obj('bg_near_ground', V, F.tolist(), gm)
loops = F.ravel()
uv = np.stack([(V[loops, 0] + NE) / (2 * NE), (V[loops, 1] + NE) / (2 * NE)], 1)
set_uv(ob.data, uv)
_ud = ob.data.uv_layers.new(name='UVDetail'); _ud.data.foreach_set('uv', (uv * (2 * NE / 4.0)).astype(np.float32).ravel())
for p in ob.data.polygons: p.use_smooth = True

# ---------- roads and water as their own meshes (OSM, surf.py) ----------
import mathutils, mathutils.bvhtree
_dg = bpy.context.evaluated_depsgraph_get(); ob.data.calc_loop_triangles(); _bvh = mathutils.bvhtree.BVHTree.FromObject(ob, _dg)
def drape(xy):
    gx = (xy[:, 0] + NE) / NS; gy = (xy[:, 1] + NE) / NS
    i0 = np.clip(np.floor(gx).astype(int), 0, n - 2); j0 = np.clip(np.floor(gy).astype(int), 0, n - 2); fx = np.clip(gx - i0, 0, 1); fy = np.clip(gy - j0, 0, 1)
    out = np.empty(len(xy))   # exact height of the terrain surface: ray down onto the ground mesh
    for k, (x, y) in enumerate(xy):
        hit = _bvh.ray_cast(mathutils.Vector((x, y, 500.0)), mathutils.Vector((0, 0, -1)))
        out[k] = hit[0].z if hit[0] is not None else Z0[j0[k], i0[k]]
    return out
def surf_obj(nm, m, mat, lift, tile, z=None):
    if not m['t']: return None
    xy = np.array(m['v'], float); zz = np.full(len(xy), z) if z is not None else drape(xy) - 0.15 + lift
    o = mk_obj(nm, np.column_stack([xy, zz]).tolist(), m['t'], mat)
    me = o.data; lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)   # validate() may drop faces: UVs from the mesh itself
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    set_uv(me, co[lv, :2] / tile); return o
def mat_white(nm, col):
    mm = bpy.data.materials.new(nm); mm.use_nodes = True; bb = mm.node_tree.nodes['Principled BSDF']
    bb.inputs['Base Color'].default_value = (*srgb(col), 1); bb.inputs['Roughness'].default_value = 0.7; return mm
_ra = mat_img('road_asphalt', BGT + 'mt/road_asphalt_v2.png', 0.85); _rn = _ra.node_tree; _rb = _rn.nodes['Principled BSDF']; _rs = _rb.inputs['Base Color'].links[0].from_socket
_rm = _rn.nodes.new('ShaderNodeMix'); _rm.data_type = 'RGBA'; _rm.blend_type = 'MULTIPLY'; _rm.inputs['Factor'].default_value = 1.0
_rm.inputs[7].default_value = (*[c * 2.32 for c in srgb(PAL['road'])], 1)   # painted road colour x asphalt detail / its linear mean
_rn.links.new(_rs, _rm.inputs[6]); _rn.links.new(_rm.outputs[2], _rb.inputs['Base Color'])
surf_obj('bg_road', _SF['road'], _ra, 0.23, 8.0)
surf_obj('bg_road_edge', _SF['edge'], mat_white('road_line', (232, 232, 226)), 0.25, 1.0)
surf_obj('bg_road_centre', _SF['centre'], mat_white('road_line', (232, 232, 226)) if 'road_line' not in bpy.data.materials else bpy.data.materials['road_line'], 0.25, 1.0)
def mat_tint(nm, path, col, rough, ior=None):   # hand-made texture x a flat colour
    mm = mat_img(nm, path, rough); nt_ = mm.node_tree; bb = nt_.nodes['Principled BSDF']; src = bb.inputs['Base Color'].links[0].from_socket
    mx = nt_.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs[7].default_value = (*col, 1); nt_.links.new(src, mx.inputs[6]); nt_.links.new(mx.outputs[2], bb.inputs['Base Color'])
    if ior:
        bb.inputs['IOR'].default_value = ior
        if nm == 'pond_water': return mm   # still ponds: no ripple bump
        bp = nt_.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.inputs['Distance'].default_value = 0.05   # ripples from the water texture: no mirror slab
        nt_.links.new(src.node.outputs['Color'], bp.inputs['Height']); nt_.links.new(bp.outputs['Normal'], bb.inputs['Normal'])
    return mm
_wm = mat_tint('swan_water', BGT + 'perth/perth_swan_water.png', (1, 1, 1), 0.15, 1.33)
_wp = mat_tint('pond_water', BGT + 'perth/perth_swan_water.png', (1.334, 0.73, 0.267), 0.55, 1.33)   # still pond: texture tinted to mean albedo (48,70,62)
for k_, w_ in enumerate(_SF['water']): surf_obj('bg_water_%d' % k_, w_, _wp if w_.get('still') else _wm, 0.0, 60.0, z=w_['z'])
_mud = mat_tint('pond_mud', BGT + 'perth/perth_sand_detail.png', [c * 1.78 for c in srgb((70, 66, 52))], 0.95)   # shallows read mud, not pale grass
for k_, w_ in enumerate(_SF['water']):
    if w_.get('still'): surf_obj('bg_pond_mud_%d' % k_, w_, _mud, 0.0, 8.0, z=w_['z'] - 0.12)
_SD = BGT + 'perth/perth_sand_detail.png'
_ro = surf_obj('bg_reed', _SF['reed'], mat_tint('reed_fringe', _SD, [c * 0.85 * 1.78 for c in srgb(PAL['lawn'])], 0.9), 0.06, 8.0)   # lawn darkened 15%
if _ro:   # reed clumps over the water sit just above it
    for _w in _SF['water']:
        if not _w.get('still'): continue
        _wv = np.array(_w['v'])
        for _v in _ro.data.vertices:
            if _wv[:, 0].min() - 3 < _v.co.x < _wv[:, 0].max() + 3 and _wv[:, 1].min() - 3 < _v.co.y < _wv[:, 1].max() + 3: _v.co.z = max(_v.co.z, _w['z'] + 0.04)
surf_obj('bg_path', _SF['path'], mat_tint('footpath', _SD, [c * 1.78 for c in srgb(PAL['path'])], 0.85), 0.08, 8.0)

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
    def drape_strip(P, off, w, lift, c, wall=0):
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
        if c is None:   # track bed: textured (tex/track_bed.png, 3.4 m across x 5.44 m along)
            s0 = len(bedv); dist = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(C, axis=0).T))]) / 5.44
            for i in range(n):
                bedv.append((A[i, 0], A[i, 1], float(za[i]))); bedv.append((B[i, 0], B[i, 1], float(zb[i])))
            for i in range(n - 1):
                bedf.append((s0 + 2 * i, s0 + 2 * i + 1, s0 + 2 * i + 3, s0 + 2 * i + 2))
                beduv.extend([(0, dist[i]), (1, dist[i]), (1, dist[i + 1]), (0, dist[i + 1])])
            return zc
        s0 = len(verts)
        for i in range(n):
            verts.append((A[i, 0], A[i, 1], float(za[i]))); verts.append((B[i, 0], B[i, 1], float(zb[i])))
        for i in range(n - 1):
            faces.append((s0 + 2 * i, s0 + 2 * i + 1, s0 + 2 * i + 3, s0 + 2 * i + 2)); cols.extend([c] * 4)
        if wall:   # rail: steel sides down to the sleepers (a raised rail, not a painted line)
            s1 = len(verts)
            for i in range(n):
                verts.append((A[i, 0], A[i, 1], float(za[i] - wall))); verts.append((B[i, 0], B[i, 1], float(zb[i] - wall)))
            for i in range(n - 1):
                faces.append((s0 + 2 * i, s0 + 2 * i + 2, s1 + 2 * i + 2, s1 + 2 * i)); cols.extend([c] * 4)
                faces.append((s0 + 2 * i + 1, s1 + 2 * i + 1, s1 + 2 * i + 3, s0 + 2 * i + 3)); cols.extend([c * 0.55] * 4)
        return zc
    bedv, bedf, beduv = [], [], []
    mast_c = lin((150, 152, 150)); wire_c = lin((40, 40, 42))
    def box(x, y, z0, z1, hx, hy, ang, c):   # upright box centred (x, y), rotated ang
        ca, sa = math.cos(ang), math.sin(ang); s0 = len(verts)
        for z in (z0, z1):
            for ux, uy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
                verts.append((x + ux * ca - uy * sa, y + ux * sa + uy * ca, z))
        for f in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)):
            faces.append(tuple(s0 + k for k in f)); cols.extend([c] * 4)
    def masts(Q, zc):   # overhead wiring: a steel mast every 60 m beside the track, arm across, contact wire 5.5 m up
        d = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])
        for s in np.arange(30, d[-1] - 5, 60):
            i = int(np.searchsorted(d, s)); i = min(max(i, 1), len(Q) - 1)
            t = Q[i] - Q[i - 1]; t = t / max(np.hypot(*t), 1e-6); nrm = np.array([-t[1], t[0]]); ang = math.atan2(t[1], t[0])
            p = Q[i] + nrm * 2.6; z = float(zc[i])
            box(p[0], p[1], z, z + 7.2, 0.14, 0.14, ang, mast_c)
            a = Q[i] + nrm * 1.3; box(a[0], a[1], z + 6.6, z + 6.8, 0.06, 1.35, ang, mast_c)
        drape_strip(Q, 0, 0.06, 5.5, wire_c)
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
            zc = drape_strip(Q, 0, 3.4, 0.2, None)
            for sd in (-0.8, 0.8): drape_strip(Q, sd, 0.08, 0.36, steel_c, wall=0.16)
            if spec.get('rail_masts', True): masts(Q, zc)
        continue
        drape_strip(Q, 0, 2.8, 0.2, bed_c)
        for sd in (-0.8, 0.8): drape_strip(Q, sd, 0.18, 0.32, steel_c)
    if bedf:
        ob = mk_obj('bg_trackbed', bedv, bedf, mat_img('trackbed', os.path.join(HERE, 'tex', 'track_bed.png'), 0.95))
        set_uv(ob.data, beduv)
    if faces:
        ob = mk_obj('bg_rails', verts, faces, mat_vcol('rails', 0.6))
        set_corner_col(ob.data, np.concatenate([np.array(cols), np.ones((len(cols), 1))], 1))

# ---------- buildings ----------
BL = json.load(open(os.path.join(D, 'buildings.json')))
def build_class(cls, tex, tw, th, keep=lambda b: True, tag='', wcol=None):
    verts, faces, cols, uvs = [], [], [], []
    RF = {'metal': [[], [], [], []], 'tile': [[], [], [], []]}   # roof meshes: verts, faces, cols, uvs
    walls = [lin(c) for c in PAL['walls_' + cls]]
    roofs = [lin(c) for c in PAL['roofs_' + ('house' if cls == 'house' else 'flat')]]
    for b in BL:
        if b['c'] != cls or not keep(b): continue
        P = np.array(b['p'], float)
        cxy = P.mean(0)
        base = float(height(cxy[0], cxy[1])) - 1.0
        h = b['h']
        wc = (lin(wcol) if wcol else walls[b['wall'] % len(walls)]) * (1 + 0.06 * (rng.random() - 0.5))
        rc = (lin(b['roof_c']) / 0.62 if b.get('roof_c') else roofs[b['roof'] % len(roofs)]) * (1 + 0.08 * (rng.random() - 0.5))   # aerial roof colour / roof texture mean
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
        src = b.get('roof_c'); kind = 'tile' if (cls == 'house' and PAL['roofs_house'][b['roof'] % len(PAL['roofs_house'])][0] > 1.3 * PAL['roofs_house'][b['roof'] % len(PAL['roofs_house'])][1]) else 'metal'
        rv, rf, rcl, ruv = RF[kind]; r0 = len(rv)
        def ruv_(x, y): return ((x * ct + y * st) / 3.04, (-x * st + y * ct) / 3.04)
        for x, y in P: rv.append((x, y, top)); ruv.append(ruv_(x, y))
        if pitched:
            rv.append((cxy[0], cxy[1], top + rh)); ruv.append(ruv_(cxy[0], cxy[1]))
            for i in range(k):
                rf.append((r0 + i, r0 + (i + 1) % k, r0 + k)); rcl += [rc] * 3
        else:
            rf.append(tuple(r0 + i for i in range(k))); rcl += [rc] * k
    if not faces: return
    ob = mk_obj('bg_bld_' + cls + tag, verts, faces, mat_facade('facade_' + cls + tag, tex if os.path.isabs(tex) else os.path.join(HERE, 'tex', tex)))
    set_corner_col(ob.data, np.concatenate([np.array(cols), np.ones((len(cols), 1))], 1))
    set_uv(ob.data, uvs)
    for kind, (rv, rf, rcl, ruv) in RF.items():
        if not rf: continue
        ro = mk_obj('bg_roof_%s%s_%s' % (cls, tag, kind), rv, rf, mat_facade('roof_%s_%s' % (cls, kind), os.path.join(HERE, 'tex', 'roof_%s.png' % kind)))
        set_corner_col(ro.data, np.concatenate([np.array(rcl), np.ones((len(rcl), 1))], 1))
        set_uv(ro.data, [ruv[i] for f_ in rf for i in f_])
for b in BL:
    P = np.array(b['p']); x, y = P[:, 0], P[:, 1]
    b['a'] = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
exec(open(os.path.join(HERE, 'landmarks.py'), encoding='utf-8').read())   # hand-built landmarks replace their generic boxes
_lime = lambda b: b['wall'] % 3 == 0   # one low-rise building in three: cream limestone (texture session)
_far = lambda b: float(np.hypot(*np.array(b['p'], float).mean(0))) > 1000.0
_shed = lambda b: b['a'] < 80 and b['c'] != 'tower'   # small sheds and kiosks: corrugated sheeting + roller door (texture session: no plain boxes)
for _cl in ('house', 'block'):
    build_class(_cl, 'fac_shed.png', 6.0, 4.5, keep=_shed, tag='_shed')
for _v in 'abcd':   # each building its own hand-made facade (tex_facades.py), picked by its index
    for _cl in ('house', 'block'):
        build_class(_cl, 'fac_low_%s.png' % _v, 3.6, 3.2, keep=lambda b, v=_v: not _lime(b) and not _shed(b) and 'abcd'[(b['wall'] // 3 + len(b['p'])) % 4] == v, tag='_' + _v)
build_class('house', BGT + 'perth/perth_limestone.png', 3.6, 3.2, keep=lambda b: _lime(b) and not _shed(b), tag='_lime', wcol=(215, 200, 165))
build_class('block', BGT + 'perth/perth_limestone.png', 3.6, 3.2, keep=lambda b: _lime(b) and not _shed(b), tag='_lime', wcol=(215, 200, 165))
for _v in 'abcd':
    build_class('tower', 'fac_tow_%s.png' % _v, 3.0, 3.6, keep=lambda b, v=_v: not _far(b) and 'abcd'[(b['wall'] + len(b['p'])) % 4] == v, tag='_' + _v)
build_class('tower', BGT + 'mt/city_far.png', 12.0, 14.4, keep=_far, tag='_far')
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
_hj = os.path.join(HERE, 'spec', os.path.basename(SP).replace('.json', '_fc_hand.json'))
if os.path.exists(_hj):   # plaza planter trees from the hand trace (spec/<ground>_fc_hand.json), if the canopy pass missed them
    _pt = [t for p in json.load(open(_hj))['planters'] for t in p['trees']]
    _pt = [t for t in _pt if len(TR) == 0 or np.hypot(TR[:, 0] - t[0], TR[:, 1] - t[1]).min() > 3]
    if _pt: TR = np.vstack([TR, np.array([[x, y, spec['tree_kinds'].index(json.load(open(_hj)).get('planter_tree_kind', spec['tree_kinds'][0]))] for x, y in _pt], float)])
    print('planter trees added', len(_pt))
r = np.hypot(TR[:, 0], TR[:, 1])
cap = spec.get('tree_cap', 30000)
near_keep = r < 700
p_far = max(0.0, min(1.0, (cap - near_keep.sum()) / max(1, (~near_keep).sum())))
TR = TR[near_keep | (rng.random(len(TR)) < p_far)]
print('trees kept', len(TR))
kinds = spec['tree_kinds']
for ki, kn in enumerate(kinds):
    cr, ch, sq, th_, tr_, ccol, tcol, sub = KIND[kn]
    def proto_(sd, smooth):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sd, radius=1.0)
        v_ = np.array([v.co[:] for v in bm.verts]); f_ = [[v.index for v in f.verts] for f in bm.faces]; bm.free()
        if not smooth: return v_ + rng.normal(0, 0.12, v_.shape), f_   # far trees: lumpy low-poly canopy
        # near trees: a rounded irregular crown of a core plus 8 clumps (eucalypt foliage masses) with gaps between them
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        u_ = np.array([v.co[:] for v in bm.verts]); g_ = [[v.index for v in f.verts] for f in bm.faces]; bm.free()
        V_, F_ = [], []
        for j in range(9):
            d = rng.normal(0, 1, 3); d /= np.linalg.norm(d); d[2] *= 0.7
            c_ = d * (0.0 if j == 0 else rng.uniform(0.28, 0.42)); r_ = 0.62 if j == 0 else rng.uniform(0.4, 0.55)
            k_ = rng.normal(0, 1, (3, 3)) * 2.0; ph = rng.uniform(0, 2 * math.pi, 3)
            w_ = u_ * (1 + 0.1 * np.sin(u_ @ k_.T + ph).sum(1, keepdims=True) / 1.7) * [r_, r_, r_ * 0.8] + c_
            o_ = len(V_); V_ += w_.tolist(); F_ += [[o_ + q for q in f] for f in g_]
        return np.array(V_), F_
    CVS = [proto_(sub, False), proto_(3, True)]
    cv, cf = CVS[0]
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
        tint = lin(ccol) * (1 + 0.16 * (rng.random() - 0.5)); cv, cf = CVS[1 if math.hypot(x, y) < spec.get('tree_hi_r_m', 400) else 0]
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
# the GLB keeps the painted ground.png as base colour (glTF cannot carry the detail / mask graph); renders get the full graph
_gt = [n for n in _nt.nodes if n.type == 'TEX_IMAGE' and n.image and n.image.name.startswith('ground.png')][0]
_nt.links.new(_gt.outputs['Color'], _b.inputs['Base Color'])
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'scene_bg.glb'), export_format='GLB', use_selection=False)
_nt.links.new(_lift.outputs[2], _b.inputs['Base Color'])
glb = os.path.normpath(os.path.join(HERE, spec['glb']))
bpy.ops.import_scene.gltf(filepath=glb)
_sg = glb.replace('.glb', '_seats.glb')
if os.path.exists(_sg): bpy.ops.import_scene.gltf(filepath=_sg)   # 3D seats ship as a second file
_sd = glb.replace('.glb', '_seats')   # Oval3D loader format: seat_tmpl.bin (one seat, float32 xyz tris) + one 3x4 transform per seat
if os.path.isdir(_sd):
    _T = np.fromfile(os.path.join(_sd, 'seat_tmpl.bin'), np.float32).reshape(-1, 3)
    _SC = {'lo_blue': (0.802, 0.807, 0.841), 'lo_tan': (0.892, 0.824, 0.751), 'mid_blue': (0.920, 0.858, 0.794),
           'mid_tan': (1.0, 0.875, 0.704), 'up_blue': (0.653, 0.705, 0.782), 'up_tan': (0.743, 0.722, 0.693)}   # Oval3D.gd SEAT_COLOURS (sRGB)
    for _k, _c in _SC.items():
        _M = np.fromfile(os.path.join(_sd, 'seats_seat_%s.bin' % _k), np.float32).reshape(-1, 3, 4)
        _W = np.einsum('nij,vj->nvi', _M[:, :, :3], _T) + _M[:, None, :, 3]
        _W = np.stack([_W[..., 0], -_W[..., 2], _W[..., 1]], -1).reshape(-1, 3)   # Godot Y-up -> Blender Z-up
        _F = np.arange(len(_W)).reshape(-1, 3)
        _me = bpy.data.meshes.new('seats_' + _k); _me.from_pydata(_W.tolist(), [], _F.tolist())
        _o = bpy.data.objects.new('seats_' + _k, _me); bpy.context.scene.collection.objects.link(_o)
        _mt = bpy.data.materials.new('seat_' + _k); _mt.use_nodes = True
        _mt.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = tuple(lin(np.array(_c) * 255)) + (1,) if False else tuple(float(((v + 0.055) / 1.055) ** 2.4) for v in _c) + (1,)
        _mt.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.55
        _me.materials.append(_mt)
        print('seats', _k, len(_M))
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
# courts as real geometry: slab per group (hand-made grain), white lines at ITF dimensions, net (no ground paint blur)
CJ = os.path.join(D, 'courts.json')
if os.path.exists(CJ):
    cj = json.load(open(CJ))
    def court_mat(nm, rgb):
        m = bpy.data.materials.new(nm); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
        gt = nt.nodes.new('ShaderNodeTexImage'); gt.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'court_grain.png'))   # tex_bake.py, 0.25 m tile
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs[6].default_value = (*[1.12 * c for c in srgb(rgb)], 1); nt.links.new(gt.outputs['Color'], mx.inputs[7])   # grain stored / 1.12
        nt.links.new(mx.outputs[2], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.75
        return m
    mats = {k: court_mat('court_' + k, v) for k, v in cj['pal'].items()}
    for k, hull in cj['slabs']:
        H = np.array(hull, float); z = height(H[:, 0], H[:, 1]).max() + 0.04
        V = [(x, y, z) for x, y in H] + [(H[:, 0].mean(), H[:, 1].mean(), z)]; c = len(H)
        set_uv_box(mk_obj('bg_court_slab_' + k, V, [[c, i, (i + 1) % c] for i in range(c)], mats[k]).data, 4.0)   # grain tile 0.25 m
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
        ux, uy = math.cos(ang), math.sin(ang); z = float(height(np.array([cx]), np.array([cy]))[0]) + 0.05; nc += 1
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
exec(open('fc_scene.py').read())
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'scene.blend'))
print('SAVED', OUT)
