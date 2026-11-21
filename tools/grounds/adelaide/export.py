"""Adelaide Oval for the game (row 202 2b): the merged model's parts (.claude/review/adelaide/model/*.ply, from
gen.py, #1856) as one GLB, plus its instanced seats in the GroundModels format (seat_tmpl.bin, seats_<colour>.bin).
Each part is split by material kind (the PLY alpha channel, kind * 20) into one material per kind: the vertex colour
(the colours read off the photos) times that kind's tiling hand-painted detail (paint.py), UVs in metres / tile.
  python3 tools/grounds/adelaide/paint.py
  blender -b --python tools/grounds/adelaide/export.py -- <out_dir>"""
import bpy, bmesh, os, sys, glob, json, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SRC = os.path.join(REPO, '.claude', 'review', 'adelaide', 'model')
TEX = os.path.join(HERE, 'tex'); TILES = {int(k): v for k, v in json.load(open(os.path.join(TEX, 'tiles.json'))).items()}
out = os.path.abspath(sys.argv[sys.argv.index('--') + 1]); os.makedirs(out, exist_ok=True)
ROUGH = {0: 0.8, 1: 0.85, 2: 0.9, 3: 0.45, 4: 0.35, 5: 0.15, 6: 0.85, 7: 0.9, 8: 0.5, 9: 0.7, 10: 0.42, 11: 0.85, 12: 0.92, 13: 0.6}
METAL = {4: 0.4, 5: 0.3, 10: 0.5}
NAMES = {0: 'paint', 1: 'paving', 2: 'concrete', 3: 'membrane', 4: 'steel', 5: 'glass', 6: 'brick', 7: 'grass', 8: 'fins',
         9: 'timber', 10: 'copper', 11: 'stone', 12: 'turf', 13: 'scoreboard'}
bpy.ops.wm.read_factory_settings(use_empty=True)
MATS = {}


def mat(k):
    if k in MATS: return MATS[k]
    m = bpy.data.materials.new('ao_' + NAMES[k]); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes['Principled BSDF']
    im = bpy.data.images.load(os.path.join(TEX, 'k%d.png' % k)); t = nt.nodes.new('ShaderNodeTexImage'); t.image = im
    vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
    nt.links.new(t.outputs['Color'], mx.inputs[6]); nt.links.new(vc.outputs['Color'], mx.inputs[7])
    nt.links.new(mx.outputs[2], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = ROUGH.get(k, 0.8); bs.inputs['Metallic'].default_value = METAL.get(k, 0.0)
    MATS[k] = m; return m


# ground.ply (gen.py's flat lawn, 6 km a side) stays out: the land round the ground is GroundModels.SURROUNDS,
# painted from OpenStreetMap (surrounds.py), which needs nothing of the model's past its walls.
for f in sorted(glob.glob(os.path.join(SRC, '*.ply'))):
    if os.path.basename(f) == 'ground.ply':
        continue
    bpy.ops.wm.ply_import(filepath=f); o = bpy.context.selected_objects[0]; me = o.data
    o.name = me.name = 'ao_' + os.path.splitext(os.path.basename(f))[0]
    ca = me.color_attributes[0]; ca.name = 'Col'
    n = len(ca.data); col = np.zeros(n * 4, np.float32); ca.data.foreach_get('color', col); col = col.reshape(-1, 4)
    lin = ca.data_type == 'FLOAT_COLOR'
    a = col[:, 3] if not lin else col[:, 3]   # alpha is never colour-managed
    kind = np.rint(a * 255 / 20).astype(int)
    if ca.domain == 'POINT':
        vk = kind
    col[:, 3] = 1.0; ca.data.foreach_set('color', col.ravel())   # alpha back to opaque: it only carried the kind
    pk = np.zeros(len(me.polygons), int)
    for p in me.polygons: pk[p.index] = vk[p.vertices[0]] if ca.domain == 'POINT' else kind[p.loop_start]
    ks = sorted(set(pk.tolist()))
    for k in ks: me.materials.append(mat(k))
    idx = {k: i for i, k in enumerate(ks)}; me.polygons.foreach_set('material_index', np.array([idx[k] for k in pk], np.int32))
    # UVs: metres -> tiles, per face by its kind
    uvl = me.uv_layers[0]; uv = np.zeros(len(uvl.data) * 2, np.float32); uvl.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    for p in me.polygons:
        tu, tv = TILES[int(pk[p.index])]
        for li in p.loop_indices: uv[li, 0] /= tu; uv[li, 1] /= tv
    uvl.data.foreach_set('uv', uv.ravel())
    bpy.context.view_layer.objects.active = o
    try: bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    except Exception as e: print('smooth', e)
    print(o.name, len(me.polygons), 'faces, kinds', ks)

# The model leaves the field out (a hole in the lawn inside the boundary): a grass floor under it, 0.3 m down, so any
# gap between the match's turf and the stands shows grass, never the sky under the world.
me = bpy.data.meshes.new('ao_floor'); H = 107.0   # a disc just past where the surrounds' map starts (105 m)
me.from_pydata([(H * math.cos(a * math.pi / 32), H * math.sin(a * math.pi / 32), -0.3) for a in range(64)], [], [tuple(range(64))])
ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT'); g = [pow(c / 255, 2.2) for c in (88, 104, 56)]
for e in ca.data: e.color = (*g, 1.0)
uv = me.uv_layers.new(); tu, tv = TILES[7]
for li, l in enumerate(me.loops): co = me.vertices[l.vertex_index].co; uv.data[li].uv = (co.x / tu, co.y / tv)
me.materials.append(mat(7)); fl = bpy.data.objects.new('ao_floor', me); bpy.context.scene.collection.objects.link(fl)

for o in bpy.context.scene.objects: o.select_set(o.type == 'MESH')
bpy.ops.export_scene.gltf(filepath=os.path.join(out, 'adelaide.glb'), export_format='GLB', use_selection=True,
                          export_cameras=False, export_lights=False, export_vertex_color='ACTIVE',
                          export_image_format='WEBP' if os.environ.get('WEBP') else 'AUTO')

# seats: one shell (inst/seat_shell.ply) on every seat point (inst/seats.npz: pos, yaw, colour), glTF axes
C = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0.0]])   # Blender (x, y, z) -> glTF (x, z, -y)
L = open(os.path.join(SRC, 'inst', 'seat_shell.ply')).read().split('\n'); h = L.index('end_header')
nv = int([l for l in L if l.startswith('element vertex')][0].split()[2]); nf = int([l for l in L if l.startswith('element face')][0].split()[2])
V = np.array([[float(x) for x in l.split()[:3]] for l in L[h + 1:h + 1 + nv]])
tri = []
for l in L[h + 1 + nv:h + 1 + nv + nf]:
    q = [int(x) for x in l.split()[1:]]
    for i in range(1, len(q) - 1): tri += [V[q[0]], V[q[i]], V[q[i + 1]]]
(np.array(tri) @ C.T).astype('<f4').tofile(os.path.join(out, 'seat_tmpl.bin'))
D = [np.load(os.path.join(SRC, 'inst', f)) for f in ('seats.npz', 'seats_hill.npz') if os.path.exists(os.path.join(SRC, 'inst', f))]
P, Y, CC = (np.concatenate([d[k] for d in D]) for k in ('pos', 'yaw', 'col'))   # the stands' seats and the Hill's (hill.py)
NAME = {(35, 55, 77): 'seat_ao_navy', (70, 70, 75): 'seat_ao_charcoal', (100, 116, 114): 'seat_ao_slate',
        (95, 118, 112): 'seat_ao_sage', (150, 45, 50): 'seat_ao_red', (200, 62, 36): 'seat_ao_orange'}
for f in glob.glob(os.path.join(out, 'seats_*.bin')): os.remove(f)
for key, nm in NAME.items():
    sel = np.all(CC == np.array(key), axis=1); rows = []
    for p, y in zip(P[sel], Y[sel]):
        c, s = math.cos(y), math.sin(y); A = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
        rows.append(np.hstack([C @ A @ C.T, (C @ p)[:, None]]).ravel())
    if rows: np.array(rows).astype('<f4').tofile(os.path.join(out, 'seats_%s.bin' % nm))
    print(nm, len(rows))
print('done', out)
