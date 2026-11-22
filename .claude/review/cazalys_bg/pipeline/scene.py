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
if spec.get('aerial_paint'):   # aerial_paving.py: real lots traced from the aerial (outlines only)
    spec['paint_poly'] = spec.get('paint_poly', []) + json.load(open(os.path.join(os.path.dirname(os.path.dirname(SP)), 'data', name, 'prep', 'aerial_paint.json')))
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

# ---------- far terrain (outside the near square): vertex colours by slope and curvature (dark gullies, light ridges),
# hand-painted rainforest canopy tile (tex/canopy.png, 60 m) multiplied over them, haze by distance ----------
MID = meta.get('mid', 0); MS = meta.get('mid_step', 0)
def terrain_ring(nm, H, step, half, hole, cls=None):
    m = H.shape[0]
    gf = np.arange(m) * step - half
    XF, YF = np.meshgrid(gf, gf)
    ZF = H.copy()
    for _ in range(4):   # DEM spikes (cones): a point far above its 4 neighbours takes their mean
        nb = (np.roll(ZF, 1, 0) + np.roll(ZF, -1, 0) + np.roll(ZF, 1, 1) + np.roll(ZF, -1, 1)) / 4
        sp = (ZF - nb) > 0.6 * step; ZF[sp] = nb[sp]
    sea_z = -meta['base']
    sea = ZF <= sea_z + 0.3
    ZF[sea] = sea_z - 0.5   # sea surface, flat at sea level
    gy_, gx_ = np.gradient(ZF, step); slope = np.hypot(gx_, gy_)
    lap = (np.roll(ZF, 1, 0) + np.roll(ZF, -1, 0) + np.roll(ZF, 1, 1) + np.roll(ZF, -1, 1) - 4 * ZF) / step   # >0 gully, <0 ridge
    VF = np.stack([XF.ravel(), YF.ravel(), ZF.ravel()], 1)
    ii = np.arange(m - 1); I, J = np.meshgrid(ii, ii)
    a = (J * m + I).ravel()
    FF = np.stack([a, a + 1, a + m + 1, a + m], 1)
    cx = (VF[FF[:, 0], 0] + VF[FF[:, 2], 0]) / 2; cy = (VF[FF[:, 0], 1] + VF[FF[:, 2], 1]) / 2
    FF = FF[(np.abs(cx) > hole - 1) | (np.abs(cy) > hole - 1)]
    noise = rng.random(VF.shape[0])
    vc = (lin(PAL['far_flat'])[None] * (1 - noise[:, None] * 0.5) + lin(PAL['far_veg'])[None] * noise[:, None] * 0.5)
    st = np.clip((slope.ravel() - 0.12) / 0.2, 0, 1)[:, None]
    vc = vc * (1 - st) + lin(PAL['far_steep'])[None] * st
    cv = np.clip(lap.ravel() * 4, -1, 1)[:, None] * st            # only on the slopes
    vc = vc * (1 - 0.45 * np.clip(cv, 0, 1)) * (1 + 0.55 * np.clip(-cv, 0, 1))
    sv = sea.ravel()
    shore = (np.hypot(*np.gradient(sea.astype(float))) > 0).ravel()
    sc = lin(PAL.get('sea', [52, 92, 104]))[None] * (1 - 0.15 * noise[:, None])
    vc[sv] = sc[sv]; vc[shore & ~sv] = vc[shore & ~sv] * 0.5 + lin(PAL.get('mangrove', [62, 84, 52]))[None] * 0.5
    d = np.hypot(VF[:, 0], VF[:, 1])
    hz = (1 - np.exp(-d / spec.get('haze_m', 22000)))[:, None] * 0.85
    vc = vc * (1 - hz) + lin(PAL['haze'])[None] * hz
    fs = sv[FF].all(1)   # all-sea quads: own object, plain water colour (no canopy tile)
    if fs.any():
        so = mk_obj(nm + '_sea', VF, FF[fs].tolist(), mat_vcol(nm + '_sea', 0.35))
        lps = FF[fs].ravel(); set_corner_col(so.data, np.concatenate([vc[lps], np.ones((len(lps), 1))], 1))
    FF = FF[~fs]
    can = os.path.join(HERE, 'tex', 'canopy.png')
    # land classes from the reference aerial (landclass.py): 0 forest, 1 suburb, 2 cane, 3 mangrove -> own hand-painted tile each
    fc = cls.ravel()[FF[:, 0]] if cls is not None else np.zeros(len(FF), int)
    shade = np.clip(1 - hz * 0, 0, 1)
    white = (np.ones_like(vc) * (1 - hz) + lin(PAL['haze'])[None] * hz)
    mang = vc * 0.55 + lin(PAL.get('mangrove', [62, 84, 52]))[None] * 0.45 * (1 - hz) + lin(PAL['haze'])[None] * 0.45 * hz
    fcx = (VF[FF[:, 0], 0] + VF[FF[:, 2], 0]) / 2; fcy = (VF[FF[:, 0], 1] + VF[FF[:, 2], 1]) / 2; fd = np.hypot(fcx, fcy)
    # suburb and cane: repeat-broken tiles (tex_landuse.py, big tile 13x), fading to their average from 2.5 to 6 km
    bands = ((0, 2500, ''), (2500, 3700, '_f1'), (3700, 4850, '_f2'), (4850, 6000, '_f3'), (6000, 1e9, '_flat'))
    sets = [(0, '', 'canopy.png', 60.0, vc, None), (3, '_mangrove', 'canopy.png', 30.0, mang, None)]
    for k, base_, T in ((1, 'suburb', 120.0), (2, 'cane', 480.0)):
        for lo_, hi_, bs in bands: sets.append((k, '_' + base_ + bs, base_ + '_rb' + bs + '.png', 13 * T, white, (lo_, hi_)))
    for k, sfx, tex, tile, col, band in sets:
        m_ = (fc == k) if k else ((fc == 0) | (fc == 4))
        if band: m_ = m_ & (fd >= band[0]) & (fd < band[1])
        sel = FF[m_]
        if not len(sel): continue
        if sfx.endswith('_flat'):
            av = json.load(open(os.path.join(HERE, 'tex', 'landuse_avg.json')))[tex.split('_')[0]]
            ob = mk_obj(nm + sfx, VF, sel.tolist(), mat_vcol(nm + sfx, 0.95)); lp = sel.ravel()
            set_corner_col(ob.data, np.concatenate([(col * lin(av)[None])[lp], np.ones((len(lp), 1))], 1))
            for p in ob.data.polygons: p.use_smooth = True
            continue
        tp = os.path.join(HERE, 'tex', tex)
        ob = mk_obj(nm + sfx, VF, sel.tolist(), mat_facade(nm + sfx, tp, 0.95))
        lp = sel.ravel()
        set_corner_col(ob.data, np.concatenate([col[lp], np.ones((len(lp), 1))], 1))
        set_uv(ob.data, VF[lp, :2] / tile)
        for p in ob.data.polygons: p.use_smooth = True
if MID:
    _mc = os.path.join(D, 'mid_cls.npy')
    terrain_ring('bg_mid_terrain', np.load(os.path.join(D, 'mid_h.npy')), MS, MID, NE, np.load(_mc) if os.path.exists(_mc) else None)
terrain_ring('bg_far_terrain', far, FS, FA, MID or NE)

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
def build_class(cls, tex, tw, th):
    ATLAS = spec.get('facade_atlas') and cls in ('house', 'block')
    if ATLAS: tex = spec['facade_atlas']
    verts, faces, cols, uvs = [], [], [], []
    RF = {'metal': [[], [], [], []], 'tile': [[], [], [], []], 'shed': [[], [], [], []], 'solar': [[], [], [], []]}   # roof meshes: verts, faces, cols, uvs
    walls = [lin(c) for c in PAL['walls_' + cls]]
    roofs = [lin(c) for c in PAL['roofs_' + ('house' if cls == 'house' else 'flat')]]
    for b in BL:
        if b['c'] != cls: continue
        P = np.array(b['p'], float)
        cxy = P.mean(0)
        base = float(height(cxy[0], cxy[1])) - 1.0
        h = b['h'] + (2.4 if cls == 'house' and b.get('id', 0) % 4 == 1 else 0.0)   # about a quarter of Cairns houses are highset on stumps
        wc = walls[b['wall'] % len(walls)] * (1 + 0.06 * (rng.random() - 0.5))
        rc = roofs[b['roof'] % len(roofs)] * (1 + 0.08 * (rng.random() - 0.5))
        pitched = cls == 'house' and len(P) <= 8
        rh = min(3.2, math.sqrt(abs(b.get('a', 150))) / 5 * (0.75 + 0.5 * ((b.get('id', 0) * 2654435761) % 1000) / 1000)) if pitched else 0   # pitch varies house to house
        top = base + 1.0 + h - rh
        par = 0.6 if cls == 'block' else 0.0   # parapet lip round flat roofs, as on the aerial
        k = len(P); s0 = len(verts)
        for x, y in P: verts.append((x, y, base))
        for x, y in P: verts.append((x, y, top + par))
        per = 0.0
        if ATLAS:   # own facade: one hand-painted atlas cell per building, walls split into bays x storeys mapped to it
            del verts[s0:]; cell = (b.get('id', len(verts)) * 7919 + int(rng.integers(0, 8))) % 8 + (0 if cls == 'house' else 8)
            if cls == 'house': cell = (1, 2, 5, 6, 1, 2, 5, 0)[cell]   # glazed windows; louvre cell only 1 in 8
            cu, cv_ = (cell % 4) / 4, 1 - (cell // 4 + 1) / 4; e_ = 2 / 1024
            ns = max(1, int(round((top + par - base - 1.0) / 3.2)))
            for i in range(k):
                j = (i + 1) % k; L = float(np.hypot(*(P[j] - P[i])))
                if L < 0.05: continue
                nb = max(1, int(round(L / 3.6)))
                for bi in range(nb):
                    a0 = P[i] + (P[j] - P[i]) * (bi / nb); a1 = P[i] + (P[j] - P[i]) * ((bi + 1) / nb)
                    for si in range(ns):
                        z0 = base + 1.0 + (top + par - base - 1.0) * si / ns; z1 = base + 1.0 + (top + par - base - 1.0) * (si + 1) / ns
                        if si == 0: z0 = base
                        o = len(verts); verts += [(a0[0], a0[1], z0), (a1[0], a1[1], z0), (a1[0], a1[1], z1), (a0[0], a0[1], z1)]
                        faces.append((o, o + 1, o + 2, o + 3)); cols += [wc] * 4
                        u0, u1 = cu + e_, cu + 0.25 - e_; v0, v1 = cv_ + e_, cv_ + 0.25 - e_
                        uvs += [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        else:
          for i in range(k):
            j = (i + 1) % k
            L = float(np.hypot(*(P[j] - P[i])))
            faces.append((s0 + i, s0 + j, s0 + k + j, s0 + k + i))
            cols += [wc] * 4
            u0, u1 = per / tw, (per + L) / tw
            v0, v1 = -1.0 / th, (top + par - base - 1.0) / th
            uvs += [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            per += L
        # roof: own mesh, hand-made texture, planar UVs along the building's longest side (one tile = 3.04 m)
        E = np.diff(np.vstack([P, P[:1]]), axis=0); e = E[np.argmax(np.hypot(E[:, 0], E[:, 1]))]; th_ = math.atan2(e[1], e[0])
        ct, st = math.cos(th_), math.sin(th_)
        src = b.get('roof_c'); kind = 'solar' if b.get('solar') else 'shed' if cls == 'block' else 'tile' if (cls == 'house' and PAL['roofs_house'][b['roof'] % len(PAL['roofs_house'])][0] > 1.3 * PAL['roofs_house'][b['roof'] % len(PAL['roofs_house'])][1]) else 'metal'
        rv, rf, rcl, ruv = RF[kind]; r0 = len(rv)
        RT = {'solar': 48.0, 'shed': 12.0}.get(kind, 3.04)
        def ruv_(x, y): return ((x * ct + y * st) / RT, (-x * st + y * ct) / RT)
        if pitched:   # 0.6 m eaves past the walls, as on Cairns houses
            sc_ = 1 + 0.6 / max(1.0, float(np.min(np.ptp(P, 0))) / 2); P = cxy + (P - cxy) * sc_
        for x, y in P: rv.append((x, y, top - (0.25 if pitched else 0))); ruv.append(ruv_(x, y))
        if pitched and k == 4:   # hip roof with a ridge along the long axis, as on the aerial and Street View (not a pyramid)
            Lu = (P - cxy) @ [ct, st]; ext = Lu.max() - Lu.min(); wid = float(np.ptp((P - cxy) @ [-st, ct]))
            hr = max(0.0, (ext - wid) / 2) * (1.0 if b.get('id', 0) % 3 else 0.85)
            ra = (cxy[0] - ct * hr, cxy[1] - st * hr, top + rh); rb = (cxy[0] + ct * hr, cxy[1] + st * hr, top + rh)
            rv += [ra, rb]; ruv += [ruv_(ra[0], ra[1]), ruv_(rb[0], rb[1])]
            for i in range(4):
                j = (i + 1) % 4; mu = (Lu[i] + Lu[j]) / 2
                if abs(Lu[i] - Lu[j]) > 0.5 * ext:   # long side: trapezoid up to the ridge
                    ia, ib = (r0 + 4, r0 + 5) if Lu[i] < Lu[j] else (r0 + 5, r0 + 4)
                    rf.append((r0 + i, r0 + j, ib, ia)); rcl += [rc] * 4
                else:   # end: triangle to the nearer ridge end
                    rf.append((r0 + i, r0 + j, r0 + 4 if mu < 0 else r0 + 5)); rcl += [rc] * 3
        elif pitched:
            rv.append((cxy[0], cxy[1], top + rh)); ruv.append(ruv_(cxy[0], cxy[1]))
            for i in range(k):
                rf.append((r0 + i, r0 + (i + 1) % k, r0 + k)); rcl += [rc] * 3
        else:
            rf.append(tuple(r0 + i for i in range(k))); rcl += [rc] * k
    if not faces: return
    ob = mk_obj('bg_bld_' + cls, verts, faces, mat_facade('facade_' + cls, os.path.join(HERE, 'tex', tex)))
    set_corner_col(ob.data, np.concatenate([np.array(cols), np.ones((len(cols), 1))], 1))
    set_uv(ob.data, uvs)
    for kind, (rv, rf, rcl, ruv) in RF.items():
        if not rf: continue
        ro = mk_obj('bg_roof_%s_%s' % (cls, kind), rv, rf, mat_facade('roof_%s_%s' % (cls, kind), os.path.join(HERE, 'tex', spec.get('roof_tex', {}).get(kind, 'roof_%s.png' % kind))))
        set_corner_col(ro.data, np.concatenate([np.array(rcl), np.ones((len(rcl), 1))], 1))
        set_uv(ro.data, [ruv[i] for f_ in rf for i in f_])
for _i, b in enumerate(BL):
    b.setdefault('id', _i)
    P = np.array(b['p']); x, y = P[:, 0], P[:, 1]
    b['a'] = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
    c_ = P.mean(0)
    if any(math.hypot(c_[0] - sx, c_[1] - sy) < 25 for sx, sy in spec.get('solar_roofs', [])): b['solar'] = 1
exec(open(os.path.join(HERE, 'landmarks.py'), encoding='utf-8').read())   # hand-built landmarks replace their generic boxes
build_class('house', 'wall.png', 3.6, 3.2)
build_class('block', 'wall_shed.png', 7.2, 6.0)   # commercial: plinth, cladding, high window band, fascia
build_class('tower', 'tower.png', 3.0, 3.6)
print('buildings built')

# ---------- trees ----------
KIND = {  # canopy radius, canopy centre height, squash, trunk height, trunk radius, canopy rgb, trunk rgb, ico subdiv
 'ghost_gum': (4.6, 6.8, 0.7, 4.0, 0.22, (132, 140, 96), (236, 230, 218), 1),
 'red_gum': (7.0, 10.0, 0.6, 5.5, 0.45, (112, 122, 86), (160, 152, 140), 1),
 'mulga': (1.5, 1.7, 0.7, 0.9, 0.1, (134, 132, 94), (96, 76, 60), 1),
 'elm': (6.5, 14.0, 0.85, 7.0, 0.5, (72, 98, 54), (76, 64, 54), 1),
 'plane': (5.5, 12.0, 0.9, 6.5, 0.4, (86, 110, 60), (150, 140, 120), 1),
 'raintree': (7.5, 9.0, 0.68, 4.5, 0.5, (70, 104, 52), (110, 100, 88), 2),
 'fig': (6.5, 9.0, 0.7, 4.0, 0.6, (56, 88, 46), (140, 132, 118), 2),
 'palm': (2.6, 9.5, 0.35, 8.5, 0.17, (96, 126, 60), (150, 140, 120), 1),
 'paperbark': (4.2, 8.0, 0.8, 4.5, 0.3, (88, 112, 70), (206, 198, 184), 1),
}
TR = json.load(open(os.path.join(D, 'trees.json')))
TR = np.array(TR, float)
r = np.hypot(TR[:, 0], TR[:, 1])
_FPP = os.path.join(D, 'footprint.json')
if os.path.exists(_FPP):   # nothing grows inside the ground model's outline
    _F = np.array(json.load(open(_FPP))); _b = ((np.degrees(np.arctan2(TR[:, 1], TR[:, 0])) % 360) // (360 / len(_F))).astype(int) % len(_F)
    TR = TR[r > _F[_b] + 4]; r = np.hypot(TR[:, 0], TR[:, 1])
cap = spec.get('tree_cap', 30000)
near_keep = r < 700
p_far = max(0.0, min(1.0, (cap - near_keep.sum()) / max(1, (~near_keep).sum())))
TR = TR[near_keep | (rng.random(len(TR)) < p_far)]
print('trees kept', len(TR))
kinds = spec['tree_kinds']
# Trees as alpha cards (texture session v10 item 1): broad crowns = leaf-cluster cards (tex/leaf_card.png) scattered over an
# open shell with sky through the gaps, lower/inner cards darker; palms = trunk + 6-10 drooping frond strips (tex/frond.png).
def mat_card(nm, tex):
    m = mat_vcol(nm, 0.8); nt = m.node_tree; b = nt.nodes['Principled BSDF']; vc = b.inputs['Base Color'].links[0].from_socket
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(HERE, 'tex', tex))
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    nt.links.new(vc, mx.inputs[6]); nt.links.new(t.outputs['Color'], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    rd = nt.nodes.new('ShaderNodeMath'); rd.operation = 'ROUND'   # glTF exporter reads Round(alpha) as alphaMode MASK, cutoff 0.5
    nt.links.new(t.outputs['Alpha'], rd.inputs[0]); nt.links.new(rd.outputs[0], b.inputs['Alpha'])
    m.use_backface_culling = False
    try: m.surface_render_method = 'DITHERED'
    except Exception: m.blend_method = 'CLIP'
    return m
def basis(n):
    n = n / np.linalg.norm(n); u = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.95 else np.cross(n, [1.0, 0, 0])
    u /= np.linalg.norm(u); return u, np.cross(n, u)
TRUNK = []
for i in range(6):
    a0 = 2 * math.pi * i / 6; TRUNK.append((math.cos(a0), math.sin(a0)))
def prism(p0, p1, r0, r1, verts, faces, cols, uvs, col):
    d = np.array(p1) - p0; u, w = basis(d); o = len(verts)
    for c_, s_ in TRUNK:
        verts.append((np.array(p0) + (u * c_ + w * s_) * r0).tolist()); verts.append((np.array(p1) + (u * c_ + w * s_) * r1).tolist())
    for i in range(6):
        j = (i + 1) % 6; faces.append((o + 2 * i, o + 2 * j, o + 2 * j + 1, o + 2 * i + 1)); cols += [col] * 4; uvs += [(0, 0), (0.02, 0), (0.02, 0.02), (0, 0.02)]
for ki, kn in enumerate(kinds):
    cr, ch, sq, th_, tr_, ccol, tcol, sub = KIND[kn]
    sel = TR[TR[:, 2] == ki]
    tv, tf, tc, tu = [], [], [], []   # trunks + limbs (vertex colour only; uv parked in an opaque corner of the card)
    verts, faces, cols, uvs = [], [], [], []
    palm = kn == 'palm'
    for x, y, _ in sel:
        s = rng.uniform(0.75, 1.25); z0 = float(height(x, y)) - 0.2; nearby = math.hypot(x, y) < 700
        tint = lin(ccol) * (1 + 0.16 * (rng.random() - 0.5)); tcl = list(lin(tcol)) + [1]
        if palm:
            lean = rng.normal(0, 0.04, 2); top = np.array([x + lean[0] * th_ * s, y + lean[1] * th_ * s, z0 + th_ * s])
            prism([x, y, z0], top.tolist(), tr_ * s * 1.15, tr_ * s * 0.85, tv, tf, tc, tu, tcl)
            nf = int(rng.integers(6, 11)) if nearby else 6; L = cr * s * 1.7; Wd = 0.55 * s
            for k in range(nf):
                az = 2 * math.pi * k / nf + rng.uniform(-0.25, 0.25); up = rng.uniform(0.2, 0.9)   # some fronds lift, some droop
                dh = np.array([math.cos(az), math.sin(az), 0.0]); side = np.array([-math.sin(az), math.cos(az), 0.0])
                o = len(verts); NS_ = 4
                for j in range(NS_ + 1):
                    t = j / NS_; c_ = top + dh * L * t + np.array([0, 0, L * (up * t - 0.95 * t * t)])
                    wj = Wd * (0.35 + 0.65 * math.sin(math.pi * min(1, t * 1.1 + 0.08)))
                    sh = 0.62 + 0.38 * t   # base of the frond (inside the crown) darker
                    for sd in (-1, 1):
                        verts.append((c_ + side * wj * sd + np.array([0, 0, -0.12 * wj])).tolist()); uvs.append(((sd + 1) / 2, t)); cols.append(list(tint * 1.25 * sh) + [1])
                for j in range(NS_):
                    faces.append((o + 2 * j, o + 2 * j + 1, o + 2 * j + 3, o + 2 * j + 2))
            continue
        top = [x, y, z0 + th_ * s]; prism([x, y, z0], top, tr_ * s, tr_ * s * 0.7, tv, tf, tc, tu, tcl)
        cc = np.array([x, y, z0 + ch * s]); R = cr * s
        for k in range(3):   # main limbs into the crown
            a_ = rng.uniform(0, 2 * math.pi) + k * 2.1; e = cc + [0.55 * R * math.cos(a_), 0.55 * R * math.sin(a_), 0.15 * R * sq]
            prism(top, e.tolist(), tr_ * s * 0.55, tr_ * s * 0.2, tv, tf, tc, tu, tcl)
        nc = 80 if nearby else 20; sz = R * (0.3 if nearby else 0.5)
        for k in range(nc):
            dv = rng.normal(0, 1, 3); dv[2] = abs(dv[2]) * 0.9 - 0.25; dv /= np.linalg.norm(dv)
            rad = rng.uniform(0.55, 1.0) if k % 4 else rng.uniform(0.15, 0.5)
            c_ = cc + dv * [R * rad, R * rad, R * sq * rad]
            n = dv + rng.normal(0, 0.6, 3); n[2] *= 0.35; u, w = basis(n); h = sz * rng.uniform(0.8, 1.2) / 2   # n[2] squashed: cards stay near upright so none reads as a flat disc from below
            sh = (0.5 + 0.5 * np.clip((dv[2] + 0.4) / 1.2, 0, 1)) * (0.75 + 0.25 * rad)   # lower and inner cards darker
            o = len(verts)
            for q, (a1, b1) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
                p = c_ + (u * a1 + w * b1) * h; verts.append(p.tolist()); uvs.append(((a1 + 1) / 2, (b1 + 1) / 2))
                cols.append(list(tint * 1.25 * sh * (0.8 if p[2] < c_[2] else 1.0)) + [1])   # card undersides darker
            faces.append((o, o + 1, o + 2, o + 3))
    if not faces: continue
    ob = mk_obj('bg_trees_' + kn, verts, faces, mat_card('tree_' + kn, 'frond.png' if palm else 'leaf_card.png'))
    set_uv(ob.data, [uvs[i] for f in faces for i in f]); set_corner_col(ob.data, np.clip([cols[i] for f in faces for i in f], 0, 1))
    if tf:
        ob2 = mk_obj('bg_trunks_' + kn, tv, tf, mat_vcol('trunk_' + kn, 0.9)); set_corner_col(ob2.data, np.array(tc)); ob2.data.polygons.foreach_set('use_smooth', [True] * len(ob2.data.polygons))
_gp = os.path.join(HERE, 'data', name, 'prep', 'entrance_garden.json')   # club-entrance garden island (builder's measurements, outside the fence)
if os.path.exists(_gp):
    G_ = json.load(open(_gp))['garden']; gv, gf, gc, gu = [], [], [], []; pv, pf, pc, pu = [], [], [], []
    ca_, sa_ = math.cos(math.radians(G_['a'])), math.sin(math.radians(G_['a'])); cx_, cy_ = G_['c']; zg = float(height(cx_, cy_))
    def _gxy(u_, v_): return (cx_ + u_ * ca_ - v_ * sa_, cy_ + u_ * sa_ + v_ * ca_)
    def _gbox(hl, hw, z0, z1, col):   # rounded-off island approximated by an octagon
        o = len(gv); ring = [(hl * math.cos(t) / max(abs(math.cos(t)), abs(math.sin(t)) * hl / hw) * 0.98, hw * math.sin(t) / max(abs(math.sin(t)), abs(math.cos(t)) * hw / hl) * 0.98) for t in np.linspace(0, 2 * math.pi, 9)[:-1] + math.pi / 8]
        for z in (z0, z1): gv.extend((*_gxy(*p), z) for p in ring)
        for i in range(8): gf.append((o + i, o + (i + 1) % 8, o + 8 + (i + 1) % 8, o + 8 + i)); gc.extend([col] * 4)
        gf.append(tuple(o + 8 + i for i in range(8))); gc.extend([col] * 8)
    KERB, MULCH, SHRUB = list(lin((200, 198, 190))) + [1], list(lin((92, 66, 48))) + [1], (70, 110, 52)
    _gbox(G_['L'] / 2, G_['W'] / 2, zg - 0.1, zg + 0.15, KERB); _gbox(G_['L'] / 2 - 0.2, G_['W'] / 2 - 0.2, zg + 0.1, zg + 0.22, MULCH)
    grng = np.random.default_rng(7)
    for k in range(G_['shrubs']):   # 14 rounded shrubs, two loose rows along the island
        u_ = (k // 2 + 0.5) / ((G_['shrubs'] + 1) // 2) * (G_['L'] - 2) - (G_['L'] - 2) / 2; v_ = (1 if k % 2 else -1) * G_['W'] * 0.22 + grng.uniform(-.3, .3)
        x_, y_ = _gxy(u_, v_); r_ = grng.uniform(0.45, 0.7); o = len(gv); sc_ = list(lin(SHRUB) * grng.uniform(0.85, 1.15)) + [1]
        for i in range(3):
            for j in range(6):
                th = math.pi * (i + 0.5) / 3 * 0.5; ph = 2 * math.pi * j / 6; gv.append((x_ + r_ * math.sin(th + .3) * math.cos(ph), y_ + r_ * math.sin(th + .3) * math.sin(ph), zg + 0.22 + r_ * 0.9 * math.cos(th + .3)))
        gv.append((x_, y_, zg + 0.22 + r_ * 0.95))
        for i in range(2):
            for j in range(6): gf.append((o + i * 6 + j, o + i * 6 + (j + 1) % 6, o + (i + 1) * 6 + (j + 1) % 6, o + (i + 1) * 6 + j)); gc.extend([sc_] * 4)
        for j in range(6): gf.append((o + 18, o + j, o + (j + 1) % 6)); gc.extend([sc_] * 3)
    ob = mk_obj('bg_entrance_garden', gv, gf, mat_vcol('entrance_garden', 0.9)); set_corner_col(ob.data, np.array(gc))
    fv, ff, fu, fc = [], [], [], []; STEM = list(lin((178, 52, 40))) + [1]; PTRUNK = list(lin((128, 118, 100))) + [1]; FROND = lin((96, 126, 60))   # lipstick palm: red crownshaft/stems (entrance photo)
    for (x_, y_, h_) in G_['palms']:
        nst = 3 if h_ < 6 else 1   # small palms clump; the tall one is a single stem
        for st in range(nst):
            bx, by = x_ + 0.4 * math.cos(st * 2.1) * (nst > 1), y_ + 0.4 * math.sin(st * 2.1) * (nst > 1); hh = h_ * (1 - 0.15 * st)
            top = np.array([bx + 0.15 * (st - 1), by, zg + 0.2 + hh])
            cs = (top - np.array([0, 0, 1.3])).tolist()
            prism([bx, by, zg + 0.2], cs, 0.09, 0.08, pv, pf, pc, pu, PTRUNK)   # grey ringed trunk
            prism(cs, top.tolist(), 0.11, 0.10, pv, pf, pc, pu, STEM)   # red crownshaft only
            for k in range(7):
                az = 2 * math.pi * k / 7 + st; L = 2.0 + 0.15 * hh; dh = np.array([math.cos(az), math.sin(az), 0.0]); side = np.array([-math.sin(az), math.cos(az), 0.0])
                o = len(fv)
                for j in range(5):
                    t = j / 4; c_ = top + dh * L * t + np.array([0, 0, L * (1.1 * t - 0.6 * t * t)]); wj = 0.6 * math.sin(math.pi * min(1, t * 1.1 + 0.08))
                    for sd in (-1, 1): fv.append((c_ + side * wj * sd).tolist()); fu.append(((sd + 1) / 2, t)); fc.append(list(FROND * (0.7 + 0.3 * t)) + [1])
                for j in range(4): ff.append((o + 2 * j, o + 2 * j + 1, o + 2 * j + 3, o + 2 * j + 2))
    if ff:
        ob3 = mk_obj('bg_entrance_palm_fronds', fv, ff, mat_card('entrance_fronds', 'frond.png'))
        set_uv(ob3.data, [fu[i] for f in ff for i in f]); set_corner_col(ob3.data, np.clip([fc[i] for f in ff for i in f], 0, 1))
    print('entrance garden', G_['shrubs'], 'shrubs', len(G_['palms']), 'palms')
    if pf: ob2 = mk_obj('bg_entrance_palm_stems', pv, pf, mat_vcol('entrance_palm_stems', 0.7)); set_corner_col(ob2.data, np.array(pc))
print('trees built')

# ---------- roads and car parks: asphalt surfaces (road_asphalt.png, 512 px = 7.2 m) and white lines ----------
if spec.get('road_mesh'):
    from mathutils.geometry import tessellate_polygon
    lat0, lon0 = spec['lat'], spec['lon']; KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
    def _xy(p): return ((p['lon'] - lon0) * KX, (p['lat'] - lat0) * KY)
    _FP = np.array(json.load(open(os.path.join(D, 'footprint.json'))))
    def _outside(Q, pad=1.0):   # True where a point is clear of the ground model's footprint
        b = ((np.degrees(np.arctan2(Q[:, 1], Q[:, 0])) % 360) // (360 / len(_FP))).astype(int) % len(_FP)
        return np.hypot(Q[:, 0], Q[:, 1]) > _FP[b] + pad
    def _dens(P, step):
        Q = [P[0]]
        for p2 in P[1:]:
            k = max(1, int(math.ceil(np.hypot(*(p2 - Q[-1])) / step))); a = Q[-1]
            for j in range(1, k + 1): Q.append(a + (p2 - a) * (j / k))
        return np.array(Q)
    def _tint(rgb, fn): return os.path.join(HERE, 'tex', fn)   # made by mk_road_tex.py (Blender has no PIL)
    TILE = 104.0   # one seamless tile: asphalt at 8 m mixed with a rotated 20.8 m sample (mk_road_tex.py)
    from mathutils import noise as _nz
    def _mottle(me, co):   # 40 m noise (2 octaves, roughness 0.5) ramped 0.85-1.0 into vertex colour; glTF multiplies COLOR_0 into the base colour
        vi = np.zeros(len(me.loops), int); me.loops.foreach_get('vertex_index', vi); P_ = co[vi]
        n = np.array([_nz.noise(Vector((x / 40.0, y / 40.0, 0.5))) + 0.5 * _nz.noise(Vector((x / 20.0, y / 20.0, 7.5))) for x, y in P_[:, :2]]) / 1.5
        v = 0.895 + 0.06 * np.clip(n * 0.5 + 0.5, 0, 1)   # +-3% about the old 0.925 mean (texture session v7 item 3)
        set_corner_col(me, np.stack([v, v, v, np.ones_like(v)], 1))
    def mat_img_vc(nm, path, rough):
        m = mat_img(nm, path, rough); nt = m.node_tree; b = nt.nodes['Principled BSDF']; t = [x for x in nt.nodes if x.type == 'TEX_IMAGE'][0]
        ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'Col'
        mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1
        nt.links.new(t.outputs['Color'], mul.inputs[6]); nt.links.new(ca.outputs['Color'], mul.inputs[7]); nt.links.new(mul.outputs[2], b.inputs['Base Color'])
        return m
    m_road = mat_img_vc('road_asphalt', _tint(PAL['road'], 'road_asphalt_road.png'), 0.92)
    m_park = mat_img_vc('park_asphalt', os.path.join(HERE, 'tex', 'park_bays.png'), 0.92)
    def _inpoly(poly, px, py):
        ins = np.zeros(len(px), bool); j = len(poly) - 1
        for i in range(len(poly)):
            xi, yi = poly[i]; xj, yj = poly[j]
            ins ^= ((yi > py) != (yj > py)) & (px < (xj - xi) * (py - yi) / ((yj - yi) or 1e-9) + xi); j = i
        return ins
    def _ang(poly):
        E = np.diff(np.vstack([poly, poly[:1]]), axis=0); e = E[np.argmax(np.hypot(E[:, 0], E[:, 1]))]; return math.atan2(e[1], e[0])
    els_ = json.load(open(os.path.join(HERE, 'data', name, 'osm.json'), encoding='utf-8'))['elements']
    PPOL = [np.array([_xy(p) for p in (el.get('geometry') or []) if p]) for el in els_ if el.get('type') == 'way' and el.get('tags', {}).get('amenity') == 'parking' and el.get('tags', {}).get('parking', 'surface') == 'surface' and len(el.get('geometry') or []) > 3]
    PPOL += [np.array(p, float) for k, p in spec.get('paint_poly', []) if k == 'parking']
    m_line = mat_vcol('road_lines', 0.7); LC = list(lin((236, 236, 230))) + [1.0]
    WDR = {'motorway': 22, 'trunk': 18, 'primary': 16, 'secondary': 13, 'tertiary': 11, 'residential': 8, 'unclassified': 8, 'service': 5}
    TWO = ('secondary', 'tertiary', 'residential', 'unclassified')
    els = json.load(open(os.path.join(HERE, 'data', name, 'osm.json'), encoding='utf-8'))['elements']
    roads = []
    for el in els:
        t = el.get('tags', {}); hw = t.get('highway')
        if el.get('type') != 'way' or hw not in WDR: continue
        if t.get('tunnel', 'no') != 'no' or (t.get('bridge') and t.get('bridge') != 'no') or t.get('area') == 'yes': continue
        P = np.array([_xy(p) for p in (el.get('geometry') or []) if p], float)
        if len(P) < 2 or np.abs(P).max() > NE - 5: P = P[(np.abs(P) < NE - 5).all(1)] if len(P) else P
        if len(P) < 2: continue
        if hw == 'service' and any(_inpoly(pp, P[:, 0], P[:, 1]).mean() > 0.5 for pp in PPOL): continue   # aisles: the bay texture draws them
        two = hw in TWO and t.get('oneway', 'no') == 'no' and t.get('lanes', '2') == '2'
        roads.append((_dens(P, 1.5), WDR[hw], two))
    # coverage hash: every road centreline sample, so lines stop where another road crosses (junctions)
    CELL = 12.0; H_ = {}
    for ri, (Q, w, _) in enumerate(roads):
        T = np.gradient(Q, axis=0); T = T / np.maximum(np.hypot(T[:, 0], T[:, 1]), 1e-6)[:, None]
        for q, tq in zip(Q, T): H_.setdefault((int(q[0] // CELL), int(q[1] // CELL)), []).append((ri, q[0], q[1], w, tq[0], tq[1]))
    def _clear(ri, x, y, tx, ty):   # a crossing road (more than 30 deg off this one's heading) blanks the lines near it
        cx, cy = int(x // CELL), int(y // CELL)
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for rj, qx, qy, w, ux, uy in H_.get((cx + i, cy + j), ()):
                    if rj != ri and abs(tx * ux + ty * uy) < 0.866 and math.hypot(x - qx, y - qy) < w / 2 + 1.5: return False
        return True
    def _ribbon(Q, off, w, lift, V, F, UV=None):
        n = len(Q); N_ = []
        for i in range(n):
            d_ = Q[min(i + 1, n - 1)] - Q[max(i - 1, 0)]; L = max(np.hypot(*d_), 1e-6); N_.append(np.array([-d_[1], d_[0]]) / L)
        N_ = np.array(N_); C = Q + N_ * off; m = max(1, int(math.ceil(w / 1.5))); s0 = len(V)   # a column every 1.5 m across, so the strip follows the ground's crown
        for k in range(m + 1):
            X = C + N_ * (w / 2 - w * k / m); z = height(X[:, 0], X[:, 1]) + lift
            V.extend((float(X[i, 0]), float(X[i, 1]), float(z[i])) for i in range(n))
        for k in range(m):
            for i in range(n - 1):
                F.append((s0 + k * n + i, s0 + (k + 1) * n + i, s0 + (k + 1) * n + i + 1, s0 + k * n + i + 1))
    def _runs(ok):
        return [r for r in np.split(np.arange(len(ok)), np.where(np.diff(ok.astype(int)) != 0)[0] + 1) if ok[r[0]] and len(r) > 1]
    RV, RF_, LV, LF = [], [], [], []
    for ri, (Q, w, two) in enumerate(roads):
        ok = _outside(Q)
        for r in _runs(ok): _ribbon(Q[r], 0, w, 0.04, RV, RF_)
        if not two: continue
        Ql = _dens(Q, 0.5); Tl = np.gradient(Ql, axis=0); Tl = Tl / np.maximum(np.hypot(Tl[:, 0], Tl[:, 1]), 1e-6)[:, None]
        okl = _outside(Ql, 2.0) & np.array([_clear(ri, x, y, a, b) for (x, y), (a, b) in zip(Ql, Tl)])
        for sd in (-1, 1):   # edge lines 0.1 m wide, 0.3 m inside each edge
            for r in _runs(okl): _ribbon(Ql[r], sd * (w / 2 - 0.35), 0.10, 0.06, LV, LF)
        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Ql, axis=0).T))])   # centre: 3 m dash, 9 m gap
        for r in _runs(okl & ((s % 12.0) < 3.0)): _ribbon(Ql[r], 0, 0.10, 0.06, LV, LF)
    if RF_:
        ob = mk_obj('bg_roads', RV, RF_, m_road); co = np.array(RV); ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))
        vi = np.zeros(len(ob.data.loops), int); ob.data.loops.foreach_get('vertex_index', vi); set_uv(ob.data, co[vi, :2] / TILE); _mottle(ob.data, co)
    if LF:
        ob = mk_obj('bg_road_lines', LV, LF, m_line); set_corner_col(ob.data, np.tile(LC, (len(LF) * 4, 1)))
    # car parks: OSM amenity=parking plus the spec's traced parking, a 1 m grid inside each outline draped on the terrain
    polys = []; PFILL = []   # car fill per car park, copied from the aerial
    for el in els:
        t = el.get('tags', {})
        if el.get('type') == 'way' and t.get('amenity') == 'parking' and t.get('parking', 'surface') == 'surface':
            g = [_xy(p) for p in (el.get('geometry') or []) if p]
            if len(g) > 3 and str(el['id']) not in spec.get('park_skip', []): polys.append(np.array(g)); PFILL.append(spec.get('park_fill', {}).get(str(el['id']), 0.35))
    for k, p in spec.get('paint_poly', []):
        if k == 'parking': polys.append(np.array(p, float)); PFILL.append(0.35)
    def _clipsq(poly, x, y):   # the polygon clipped to the 1 m square at (x, y) (Sutherland-Hodgman, square is convex)
        out = [tuple(q) for q in poly]
        for ax, sg, c in ((0, 1, x), (0, -1, x + 1), (1, 1, y), (1, -1, y + 1)):
            if not out: break
            inp, out = out, []
            for k in range(len(inp)):
                a, b = inp[k - 1], inp[k]; ia = (a[ax] - c) * sg >= 0; ib = (b[ax] - c) * sg >= 0
                if ia != ib:
                    t = (c - a[ax]) / (b[ax] - a[ax]); out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
                if ib: out.append(b)
        return out
    def _drape(polys, mat, nm, tile, lift, bays=False, hole=None):   # 1 m grid inside each outline; edge cells cut to the true outline
        PV, PF = [], []; AN = []
        for poly in polys:
            pv0 = len(PV)
            x0, y0 = np.floor(poly.min(0)); x1, y1 = np.ceil(poly.max(0))
            xs = np.arange(x0, x1 + 1); ys = np.arange(y0, y1 + 1); GX, GY = np.meshgrid(xs, ys)
            px, py = GX.ravel(), GY.ravel(); ins = np.zeros(len(px), bool); j = len(poly) - 1
            for i in range(len(poly)):   # even-odd ray test
                xi, yi = poly[i]; xj, yj = poly[j]
                ins ^= ((yi > py) != (yj > py)) & (px < (xj - xi) * (py - yi) / ((yj - yi) or 1e-9) + xi); j = i
            ins = ins.reshape(GX.shape)
            q = ins[:-1, :-1] & ins[1:, :-1] & ins[:-1, 1:] & ins[1:, 1:]
            E = _dens(np.vstack([poly, poly[:1]]), 0.25); edge = set(zip((np.floor(E[:, 0]) - x0).astype(int), (np.floor(E[:, 1]) - y0).astype(int)))
            part = (ins[:-1, :-1] | ins[1:, :-1] | ins[:-1, 1:] | ins[1:, 1:]) & ~q   # cells the outline only grazes at a corner
            edge |= set(zip(*np.nonzero(part.T)))
            for ii, jj in edge:
                if 0 <= jj < q.shape[0] and 0 <= ii < q.shape[1]: q[jj, ii] = False
            if hole:   # cells whose centre is inside the ellipse are left out
                cx_ = GX[:-1, :-1] + 0.5; cy_ = GY[:-1, :-1] + 0.5; inh = (cx_ / hole[0]) ** 2 + (cy_ / hole[1]) ** 2 < 1
                q &= ~inh; edge = {(ii, jj) for ii, jj in edge if not (0 <= jj < inh.shape[0] and 0 <= ii < inh.shape[1] and inh[jj, ii])}
            if q.any():
                Z = height(GX, GY) + lift; idx = -np.ones(GX.shape, int); used = np.zeros(GX.shape, bool)
                used[:-1, :-1] |= q; used[1:, :-1] |= q; used[:-1, 1:] |= q; used[1:, 1:] |= q
                s0 = len(PV); idx[used] = s0 + np.arange(used.sum())
                PV.extend(zip(GX[used], GY[used], Z[used]))
                jj_, ii_ = np.nonzero(q)
                PF.extend(zip(idx[jj_, ii_], idx[jj_, ii_ + 1], idx[jj_ + 1, ii_ + 1], idx[jj_ + 1, ii_]))
            for ii, jj in edge:   # boundary cells: the outline clipped to the cell, vertices on the true outline
                c = _clipsq(poly, x0 + ii, y0 + jj)
                c = [v for k, v in enumerate(c) if math.hypot(v[0] - c[k - 1][0], v[1] - c[k - 1][1]) > 1e-4]   # drop repeated points
                if len(c) < 3: continue
                C = np.array(c); z = height(C[:, 0], C[:, 1]) + lift; s0 = len(PV)
                PV.extend(zip(C[:, 0], C[:, 1], z))
                T = tessellate_polygon([[Vector((a, b, 0)) for a, b in c]]) or [(0, k, k + 1) for k in range(1, len(c) - 1)]
                for tri in T: PF.append(tuple(s0 + t for t in tri))
            AN += [_ang(poly)] * (len(PV) - pv0)
        if PF:
            ob = mk_obj(nm, [tuple(map(float, v)) for v in PV], [tuple(map(int, f)) for f in PF], mat); co = np.array(PV, float); ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))
            vi = np.zeros(len(ob.data.loops), int); ob.data.loops.foreach_get('vertex_index', vi)
            if bays:   # u along the car park's long side (12 bays = 31.2 m), v across (two bay rows and an aisle = 34.8 m)
                A = np.array(AN)[vi]; X_, Y_ = co[vi, 0], co[vi, 1]
                set_uv(ob.data, np.stack([(X_ * np.cos(A) + Y_ * np.sin(A)) / 31.2, (-X_ * np.sin(A) + Y_ * np.cos(A)) / 34.8], 1))
            else: set_uv(ob.data, co[vi, :2] / tile)
            if mat in (m_park, m_road) or nm in ('bg_carparks_pale', 'bg_paved'): _mottle(ob.data, co)
        return PF
    PF = _drape(polys, m_park, 'bg_carparks', TILE, 0.02, bays=True)   # 2 cm under the roads (0.04) so they never fight
    # parked cars in the bays, about half full as on the aerial; none within 3 m of a road edge or 4 m of the outline
    RS = np.vstack([Q for Q, w, _ in roads]); RW_ = np.concatenate([[w] * len(Q) for Q, w, _ in roads])
    CC = [(236, 236, 234)] * 5 + [(196, 198, 200)] * 3 + [(120, 122, 126), (34, 36, 40), (34, 36, 40), (60, 76, 120), (150, 40, 36)]
    CV, CF, CCol = [], [], []; crng = np.random.default_rng(11); TYRE, GLASS = list(lin((26, 26, 28))) + [1.0], list(lin((44, 52, 62))) + [1.0]
    for poly, fill in zip(polys, PFILL):
        a = _ang(poly); ca, sa = math.cos(a), math.sin(a)
        R = np.stack([poly[:, 0] * ca + poly[:, 1] * sa, -poly[:, 0] * sa + poly[:, 1] * ca], 1)
        us = np.arange(math.floor(R[:, 0].min() / 2.6) * 2.6, R[:, 0].max(), 2.6)
        vs = [v for v0 in np.arange(math.floor(R[:, 1].min() / 34.8) * 34.8, R[:, 1].max(), 17.4) for v in (v0 + 2.7, v0 + 8.1)]
        GU, GV = np.meshgrid(us, vs); GU, GV = GU.ravel(), GV.ravel()
        X_ = GU * ca - GV * sa; Y_ = GU * sa + GV * ca
        ok = _inpoly(poly, X_, Y_) & (crng.random(len(X_)) < fill)
        for dx, dy in ((4, 0), (-4, 0), (0, 4), (0, -4)): ok &= _inpoly(poly, X_ + dx, Y_ + dy)
        for x, y in zip(X_[ok], Y_[ok]):
            d = np.hypot(RS[:, 0] - x, RS[:, 1] - y)
            if (d < RW_ / 2 + 3).any(): continue
            z = float(height(x, y)) + 0.02; col = list(lin(CC[crng.integers(len(CC))])) + [1.0]
            s0 = len(CV)
            tall = crng.random() < 0.35   # utes/SUVs (common in Cairns car parks) sit taller
            RINGS = ((z + 0.08, 0.84, 2.15, 0), (z + 0.38, 0.9, 2.3, 0), (z + 0.86, 0.9, 2.25, 0), (z + (1.0 if tall else 0.92), 0.82, 1.75 if tall else 1.55, -0.15), (z + (1.75 if tall else 1.42), 0.72, 1.3 if tall else 1.0, -0.25))
            BAND = (TYRE, col, col, GLASS)   # tyres, lower body, bonnet/boot slope, tinted glasshouse; roof cap in body colour
            for zz, hw, hl, off in RINGS:
                for pw, pl in ((-hw, -hl), (hw, -hl), (hw, hl), (-hw, hl)):   # pl along the bay (across the car park's long side), pw across
                    pl += off; CV.append((x + pw * ca - pl * sa, y + pw * sa + pl * ca, zz))
            for b_ in range(4):
                for i in range(4): CF.append((s0 + 4 * b_ + i, s0 + 4 * b_ + (i + 1) % 4, s0 + 4 * b_ + 4 + (i + 1) % 4, s0 + 4 * b_ + 4 + i)); CCol += [BAND[b_]] * 4
            CF.append((s0 + 16, s0 + 17, s0 + 18, s0 + 19)); CCol += [col] * 4
    if CF:
        ob = mk_obj('bg_cars', CV, CF, mat_vcol('cars', 0.4)); set_corner_col(ob.data, np.array(CCol))
    print('cars', len(CF) // 17)
    _sp = os.path.join(D, 'solar.json')   # solar-shade canopies traced from the aerial: dark panel deck at 4 m on steel posts
    if os.path.exists(_sp):
        SV, SF, SC = [], [], []; PANEL, STEEL, FRAME = (30, 42, 72), (150, 154, 158), (190, 192, 194)
        def _box(pts, z0, z1, col):
            s0 = len(SV)
            for z in (z0, z1): SV.extend((x, y, z) for x, y in pts)
            for i in range(4): SF.append((s0 + i, s0 + (i + 1) % 4, s0 + 4 + (i + 1) % 4, s0 + 4 + i)); SC.extend([col] * 4)
            SF.append((s0 + 4, s0 + 5, s0 + 6, s0 + 7)); SC.extend([col] * 4)
        for q in json.load(open(_sp)):
            q = np.array(q, float); zb = float(np.mean([height(x, y) for x, y in q]))
            c = q.mean(0); e = [np.linalg.norm(q[(i + 1) % 4] - q[i]) for i in range(4)]; k = int(np.argmax(e[:2]))
            Q4 = [q[(k + i) % 4] for i in range(4)]   # P(s,t): s along the long edge, t across; deck pitched 0.9 m across (photos: mono slope)
            def _P(s_, t_): return (1 - s_) * (1 - t_) * Q4[0] + s_ * (1 - t_) * Q4[1] + s_ * t_ * Q4[2] + (1 - s_) * t_ * Q4[3]
            def _z(t_): return zb + 3.6 + 0.9 * t_
            Ls, Lt = e[k], e[(k + 1) % 4]; ns, nt = max(1, int(Ls / 1.04)), max(1, int(Lt / 1.72))   # modules 1.0 x 1.7 m, 4 cm frame gaps
            for i in range(ns):
                for j in range(nt):
                    s0 = len(SV); ga, gb = 0.02 / Ls, 0.02 / Lt
                    for (s_, t_) in (((i / ns) + ga, (j / nt) + gb), (((i + 1) / ns) - ga, (j / nt) + gb), (((i + 1) / ns) - ga, ((j + 1) / nt) - gb), ((i / ns) + ga, ((j + 1) / nt) - gb)):
                        SV.append((*_P(s_, t_), _z(t_)))
                    SF.append((s0, s0 + 1, s0 + 2, s0 + 3)); SC.extend([PANEL] * 4)
            a, b = (q[k] + q[(k + 3) % 4]) / 2, (q[(k + 1) % 4] + q[(k + 2) % 4]) / 2   # spine along the long side
            nps = max(2, int(np.linalg.norm(b - a) / 7.8) + 1)
            for t in np.linspace(0.04, 0.96, nps):
                px, py = a + (b - a) * t
                _box([(px - .15, py - .15), (px + .15, py - .15), (px + .15, py + .15), (px - .15, py + .15)], zb, zb + 3.95, STEEL)
                r0, r1 = _P(t, 0.0), _P(t, 1.0); d_ = (r1 - r0); n_ = np.array([-d_[1], d_[0]]) / (np.linalg.norm(d_) or 1) * 0.08   # rafter across the deck at each post
                s0 = len(SV)
                for (pp, zz) in ((r0 - n_, _z(0) - 0.3), (r0 + n_, _z(0) - 0.3), (r1 + n_, _z(1) - 0.3), (r1 - n_, _z(1) - 0.3), (r0 - n_, _z(0) - 0.07), (r0 + n_, _z(0) - 0.07), (r1 + n_, _z(1) - 0.07), (r1 - n_, _z(1) - 0.07)):
                    SV.append((pp[0], pp[1], zz))
                for i in range(4): SF.append((s0 + i, s0 + (i + 1) % 4, s0 + 4 + (i + 1) % 4, s0 + 4 + i)); SC.extend([STEEL] * 4)
            _box([(a[0] - .1, a[1] - .1), (b[0] - .1, b[1] - .1), (b[0] + .1, b[1] + .1), (a[0] + .1, a[1] + .1)], zb + 3.75, zb + 4.0, STEEL)
        ob = mk_obj('bg_solar_shades', SV, SF, mat_vcol('solar', 0.35)); set_corner_col(ob.data, np.array([list(lin(c)) + [1.0] for c in SC]))
        print('solar canopies', len(json.load(open(_sp))))
    m_fc = mat_img_vc('paved_concrete', _tint(PAL['paved'], 'road_asphalt_paved.png'), 0.9)   # pale concrete, not road asphalt
    PF2 = _drape([np.array(p, float) for k, p in spec.get('paint_poly', []) if k == 'paved'], m_fc, 'bg_paved', TILE, 0.03, hole=spec.get('pave_hole'))
    m_pale = mat_img_vc('park_pale', os.path.join(HERE, 'tex', 'park_bays_pale.png'), 0.92)   # the bare concrete end of the SW car park
    _drape([np.array(p, float) for k, p in spec.get('paint_poly', []) if k == 'parking_pale'], m_pale, 'bg_carparks_pale', TILE, 0.025, bays=True)
    print('paved faces', len(PF2))
    # house yards: concrete driveway from each house to its nearest road; 1.8 m Colorbond side/back fences (not on the street side)
    DV, DF, DC = [], [], []; DRV, FEN = list(lin((150, 148, 142))) + [1.0], list(lin((110, 116, 108))) + [1.0]
    HC = np.array([np.array(b['p'], float).mean(0) for b in BL if b['c'] == 'house'])
    for b in BL:
        if b['c'] != 'house': continue
        P = np.array(b['p'], float); c = P.mean(0)
        d = np.hypot(RS[:, 0] - c[0], RS[:, 1] - c[1]); i = int(np.argmin(d))
        if d[i] > 45: continue
        u = (RS[i] - c) / d[i]; n = np.array([-u[1], u[0]])
        ext = float(((P - c) @ u).max()); r0 = c + u * ext; r1 = RS[i] - u * (RW_[i] / 2)
        if (r1 - c) @ u > ext + 0.5:   # driveway 3 m wide, 4 samples so it follows the ground
            o = len(DV); off = 0.6 * float(((P - c) @ n).max()) * (1 if b['id'] % 2 else -1)
            for t in np.linspace(0, 1, 4):
                q = r0 + (r1 - r0) * t + n * off
                for sd in (-1.4, 1.4): DV.append((q[0] + n[0] * sd, q[1] + n[1] * sd, float(height(q[0] + n[0] * sd, q[1] + n[1] * sd)) + 0.06))
            for k in range(3): DF.append((o + 2 * k, o + 2 * k + 1, o + 2 * k + 3, o + 2 * k + 2)); DC += [DRV] * 4
        hw_ = float(np.abs((P - c) @ n).max()) + 2.5; hb = float(-((P - c) @ u).min()) + 4.0; hf = ext + 1.0
        corners = [c + n * hw_ + u * hf, c + n * hw_ - u * hb, c - n * hw_ - u * hb, c - n * hw_ + u * hf]
        for a_, b_ in ((0, 1), (1, 2), (2, 3)):   # two sides and the back; the street side stays open
            A, B = corners[a_], corners[b_]; L = float(np.linalg.norm(B - A)); ns_ = max(1, int(L / 3))
            for k in range(ns_):
                p0 = A + (B - A) * k / ns_; p1 = A + (B - A) * (k + 1) / ns_; m = (p0 + p1) / 2
                dd = np.hypot(HC[:, 0] - m[0], HC[:, 1] - m[1]); dd = dd[dd > 0.5]
                if len(dd) and dd.min() < 5: continue   # shared boundary near a neighbour's house: skip, never cut through it
                if (np.hypot(RS[:, 0] - m[0], RS[:, 1] - m[1]) < RW_ / 2 + 1).any(): continue
                z0, z1 = float(height(*p0)), float(height(*p1)); o = len(DV)
                DV += [(p0[0], p0[1], z0), (p1[0], p1[1], z1), (p1[0], p1[1], z1 + 1.8), (p0[0], p0[1], z0 + 1.8)]
                DF.append((o, o + 1, o + 2, o + 3)); DC += [FEN] * 4
    if DF:
        ob = mk_obj('bg_yards', DV, DF, mat_vcol('yards', 0.8)); set_corner_col(ob.data, np.array(DC))
    print('yards built', len(DF))
    print('roads', len(roads), 'road faces', len(RF_), 'line faces', len(LF), 'car park faces', len(PF))

# ---------- export background, then add the ground model for renders ----------
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'scene_bg.glb'), export_format='GLB', use_selection=False)
glb = os.path.normpath(os.path.join(HERE, spec['glb']))
if os.path.exists(glb): bpy.ops.import_scene.gltf(filepath=glb)
else: print("NO GROUND GLB", glb)
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
        fc = [1.25 * c for c in srgb(rgb)]
        if max(fc) > 1: print('WARN court colour over 1, clamped', nm, fc)
        mx.inputs[6].default_value = (*[min(1.0, c) for c in fc], 1); nt.links.new(gt.outputs['Color'], mx.inputs[7])   # grain stored / 1.25
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
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'scene.blend'))
print('SAVED', OUT)
