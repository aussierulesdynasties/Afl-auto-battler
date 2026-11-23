"""Render Melbourne Park arenas alone (landmarks arenas block) on the baked ground. blender -b -P arena_view.py -- spec/mcg.json CX CY OUTPREFIX"""
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
A = sys.argv[sys.argv.index('--') + 1:]; CX, CY = float(A[1]), float(A[2]); PRE = os.path.abspath(A[3])
spec['landmarks'] = ['arenas']
GD = D; BL = json.load(open(os.path.join(D, 'buildings.json')))
exec(open(os.path.join(HERE, 'landmarks.py'), encoding='utf-8').read().replace("MAT[key])", "MAT.get(key, MAT['white']))"))   # viewer only: tolerate other agents' unfinished tower materials
# ground: 400 m square of the baked ground under the arena
gi = bpy.data.images.load(os.path.join(GD, 'ground_baked.png')); m = bpy.data.materials.new('g'); m.use_nodes = True
t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = gi; m.node_tree.links.new(t.outputs['Color'], m.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
H_ = 250; z0 = float(height(CX, CY)) - 1.0
gx_ = np.arange(CX - H_, CX + H_ + 0.1, 5.0); gy_ = np.arange(CY - H_, CY + H_ + 0.1, 5.0); n_ = len(gx_)   # real terrain, 5 m grid
XX, YY = np.meshgrid(gx_, gy_); ZZ = height(XX, YY) - 1.05
V = [(float(XX[j, i]), float(YY[j, i]), float(ZZ[j, i])) for j in range(n_) for i in range(n_)]
F = [(j * n_ + i, j * n_ + i + 1, (j + 1) * n_ + i + 1, (j + 1) * n_ + i) for j in range(n_ - 1) for i in range(n_ - 1)]
ob = mk_obj('ground', V, F, m); ob.data.shade_smooth()   # flat 5 m facets on the lumpy DEM read as a checker
set_uv(ob.data, [((x + NE) / (2 * NE), (y + NE) / (2 * NE)) for f_ in F for (x, y, _) in [V[k] for k in f_]])
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 4; sun.rotation_euler = (math.radians(40), 0, math.radians(30))
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.6, 0.7, 0.85, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.8
sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
sc.render.resolution_x, sc.render.resolution_y = 1400, 1050; sc.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
from mathutils import Vector
def shot(nm, eye, ortho=None):
    cam.location = eye; d = Vector((CX, CY, z0 + 12)) - Vector(eye); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho: cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho; cam.rotation_euler = (0, 0, 0)
    else: cam.data.type = 'PERSP'; cam.data.lens = 35
    sc.render.filepath = PRE + nm + '.png'; bpy.ops.render.render(write_still=True)
shot('_top', (CX, CY, z0 + 400), ortho=200 if len(A) < 5 else float(A[4]))
shot('_obl_sw', (CX - 160, CY - 170, z0 + 90))
shot('_obl_ne', (CX + 170, CY + 150, z0 + 70))
shot('_obl_s', (CX + 20, CY - 230, z0 + 45))
if len(A) > 5:
    for k_, e_ in enumerate(json.loads(A[5])): shot('_g%d' % k_, (e_[0], e_[1], z0 + e_[2]))
