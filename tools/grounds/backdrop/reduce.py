"""Cut a stadium's Blender background scene (scene.blend, built by the .claude/review/<ground>_bg
pipeline) down to the match's backdrop: assets/grounds/<slug>/<slug>_backdrop.glb (row 202 2b).
   python reduce.py -- scene.blend out.glb [tex_px] [near_r] [mid_keep] [far_keep]
The stadium model in the scene (every object not named bg_*) is dropped, and so is the scene's
ground under the stadium. Big meshes are decimated, the trees thinned with distance, the ground
bake scaled to tex_px, and everything cut into wedges round the ground (see SECTORS).
Needs the scene's textures where the .blend points (//../../tex, //../../data/<ground>/prep).
"""
import bpy, bmesh, sys, numpy as np, math
a = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = a[0], a[1]
TEX = int(a[2]) if len(a) > 2 else 4096
NEAR_R = float(a[3]) if len(a) > 3 else 350.0     # trees nearer than this are all kept
MID_R = 800.0
MID_KEEP = float(a[4]) if len(a) > 4 else 0.4     # share of trees kept from NEAR_R to MID_R
FAR_KEEP = float(a[5]) if len(a) > 5 else 0.15    # share kept past MID_R
bpy.ops.wm.open_mainfile(filepath=SRC)
for im in bpy.data.images:
    if im.packed_file is None and im.filepath: im.reload()
    if im.size[0] == 0: print("MISSING", im.name)
rng = np.random.default_rng(7)

def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)

# the stadium's footprint: the convex hull of the stadium model (its plaza is its outermost ground), drawn 4 m
# smaller so the scene's ground runs a little under the plaza's edge. The scene's ground inside it
# would lie over the arena.
MODEL = [o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith('bg_')]
HULL = None
if MODEL:
    P = set()
    for o in MODEL:
        co = np.zeros(len(o.data.vertices) * 3); o.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        W_ = np.array(o.matrix_world); co = co @ W_[:3, :3].T + W_[:3, 3]
        P |= set(map(tuple, np.round(co[:, :2], 1)))
    P = sorted(P)
    def cross(o, a_, b_): return (a_[0] - o[0]) * (b_[1] - o[1]) - (a_[1] - o[1]) * (b_[0] - o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    HULL = np.array(lo[:-1] + up[:-1])
    cx, cy = HULL.mean(0)
    d = HULL - [cx, cy]; L = np.hypot(d[:, 0], d[:, 1])[:, None]
    HULL = np.array([cx, cy]) + d * (L - 4.0) / L
    print('footprint hull points', len(HULL))

def under_stadium(x, y):
    if HULL is None: return False
    n = len(HULL)
    for i in range(n):
        a_, b_ = HULL[i], HULL[(i + 1) % n]
        if (b_[0] - a_[0]) * (y - a_[1]) - (b_[1] - a_[1]) * (x - a_[0]) < 0: return False
    return True

for o in [o for o in bpy.data.objects if not o.name.startswith('bg_')]:
    bpy.data.objects.remove(o, do_unlink=True)

g = bpy.data.objects['bg_near_ground']
bm = bmesh.new(); bm.from_mesh(g.data); M = g.matrix_world
kill = [f for f in bm.faces if under_stadium(*(M @ f.calc_center_median()).xy)]
bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(g.data); bm.free()
print('ground faces cut under stadium', len(kill))

def decimate(name, ratio):
    o = bpy.data.objects.get(name)
    if o is None: return
    m = o.modifiers.new('d', 'DECIMATE'); m.ratio = ratio; m.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = o
    with bpy.context.temp_override(object=o, active_object=o):
        bpy.ops.object.modifier_apply(modifier='d')
DECIMATE = {'bg_near_ground': 0.3, 'bg_far_terrain': 0.15, 'bg_far_water': 0.03, 'bg_far_suburb': 0.4,
            'bg_rails': 0.3, 'bg_road_kerbs': 0.25, 'bg_roads': 0.4, 'bg_road_lines': 0.4, 'bg_shore': 0.5}
for n, r in DECIMATE.items():
    decimate(n, r)

# trees: clumps thinned with distance, kept ones grown so the canopy keeps its cover
for o in [o for o in bpy.data.objects if o.name.startswith('bg_trees')]:
    bm = bmesh.new(); bm.from_mesh(o.data)
    lid = bm.faces.layers.int.new('cid') if False else None
    comps = []; seen = set()
    bm.verts.ensure_lookup_table()
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; c = []; seen.add(v.index)
        while st:
            x = st.pop(); c.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
        comps.append(c)
    kill = []; kept = 0
    for c in comps:
        cen = sum((v.co for v in c), c[0].co * 0) / len(c)
        r = math.hypot(cen.x, cen.y)
        keep = 1.0 if r < NEAR_R else (MID_KEEP if r < MID_R else FAR_KEEP)
        if keep < 1.0 and rng.random() > keep:
            kill.extend(c); continue
        kept += 1
        if keep < 1.0:
            sx = 1.3 if keep >= MID_KEEP else 1.6; sz = 1.0 if keep >= MID_KEEP else 1.15
            base = min(v.co.z for v in c)
            for v in c:
                d = v.co - cen
                v.co.x = cen.x + d.x * sx; v.co.y = cen.y + d.y * sx; v.co.z = base + (v.co.z - base) * sz
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(o.data); bm.free()
    print(o.name, 'clumps', len(comps), 'kept', kept)

# fewer draws: objects whose materials are the same (same images, same nodes, same settings) are
# joined into one object with one material. All the trees share one leaf material (their kinds
# differ only in shape and vertex colour). Joined before slicing, so each family is cut once.
import re
def msig(m):
    if m is None or not m.node_tree: return None
    nt = m.node_tree; b = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']
    rough = round(b[0].inputs['Roughness'].default_value, 3) if b else None
    return (tuple(sorted(n.image.filepath for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image)),
            tuple(sorted((n.type, getattr(n, 'blend_type', '')) for n in nt.nodes)), rough)
groups = {}
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    if len(o.data.materials) != 1: continue
    fam = 'bg_trees' if o.name.startswith('bg_trees') else re.sub(r'(_v\d+|\.\d+)$', '', re.sub(r'_v\d+', '', o.name))
    groups.setdefault((fam, msig(o.data.materials[0])), []).append(o)
for (fam, sig), objs in groups.items():
    if len(objs) < 2: continue
    keep = objs[0].data.materials[0]
    for o in objs: o.data.materials[0] = keep
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    objs[0].name = fam + '_joined' if fam != objs[0].name else fam
    print('joined', fam, len(objs))

# slices: every object cut into SECTORS wedges round the ground and an inner and outer ring, so
# the camera draws only the wedges in view and the outer ones drop to their lower detail levels
SECTORS = 8; RING = 700.0
def slice_obj(o, rings=True):
    me = o.data; M = o.matrix_world
    bm = bmesh.new(); bm.from_mesh(me)
    groups = {}
    for f in bm.faces:
        c = M @ f.calc_center_median()
        k = int(((math.atan2(c.y, c.x) + math.pi) / (2 * math.pi)) * SECTORS) % SECTORS
        if rings and math.hypot(c.x, c.y) >= RING: k += SECTORS
        groups.setdefault(k, []).append(f.index)
    bm.free()
    if len(groups) <= 1: return
    for k, idx in groups.items():
        cp = o.copy(); cp.data = me.copy(); cp.name = '%s_s%02d' % (o.name, k)
        bpy.context.scene.collection.objects.link(cp)
        b2 = bmesh.new(); b2.from_mesh(cp.data); b2.faces.ensure_lookup_table()
        keep = set(idx)
        bmesh.ops.delete(b2, geom=[f for f in b2.faces if f.index not in keep], context='FACES')
        b2.to_mesh(cp.data); b2.free()
    bpy.data.objects.remove(o, do_unlink=True)
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'bg_far_terrain' and len(o.data.polygons) > 30000]:
    slice_obj(o, rings=o.name.startswith('bg_trees') or o.name.startswith('bg_bld') or o.name.startswith('bg_roof'))

# materials: no roughness or metal maps (the backdrop is seen from 200 m and more; the walls' glass
# is in their base texture's alpha, oval3d_backdrop.gdshader). The exporter would bake them into
# extra images, and fails on some.
for m in bpy.data.materials:
    if not m.node_tree: continue
    for l in list(m.node_tree.links):
        if l.to_node.type == 'BSDF_PRINCIPLED' and l.to_socket.name in ('Roughness', 'Metallic', 'Specular IOR Level'):
            m.node_tree.links.remove(l)

# a base colour scaled by a vector-math node after the vertex-colour mix (clad, plaza, pool deck):
# the mix goes straight to the base colour; the exporter cannot carry the node
for m in bpy.data.materials:
    if not m.node_tree: continue
    nt = m.node_tree
    for l in list(nt.links):
        if l.to_node.type == 'BSDF_PRINCIPLED' and l.to_socket.name == 'Base Color' and l.from_node.type == 'VECT_MATH':
            vm = l.from_node; src = [x for x in nt.links if x.to_node == vm and x.from_node.type == 'MIX']
            if src and vm.operation == 'SCALE':
                k = float(vm.inputs['Scale'].default_value)
                nt.links.new(src[0].from_socket, l.to_socket)
                # the mix multiplies vertex colour by texture: the scale goes into the vertex colours
                for o in [o for o in bpy.data.objects if o.type == 'MESH' and m.name in [x.name for x in o.data.materials if x]]:
                    ca = o.data.color_attributes.get('Col')
                    if ca is None: continue
                    c = np.zeros(len(ca.data) * 4, np.float32); ca.data.foreach_get('color', c); c = c.reshape(-1, 4)
                    c[:, :3] *= k; ca.data.foreach_set('color', c.ravel())
                print('base colour scale into vertex colours', m.name, round(k, 3))

# textures: the ground bake down to TEX
for im in bpy.data.images:
    if im.size[0] > TEX:
        im.scale(TEX, TEX); print('scaled', im.name)

tot = 0
for o in bpy.context.scene.objects:
    if o.type == 'MESH': t = tris(o); tot += t
print('TOTAL', tot, 'objects', len([o for o in bpy.data.objects if o.type == 'MESH']))
# two files, each under GitHub's 50 MB: <out>_part1.glb everything but the trees, _part2 the trees
def export(path, objs):
    for o in bpy.context.scene.objects: o.select_set(o in objs)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_image_format='WEBP',
                              export_apply=True, export_vertex_color='ACTIVE', export_all_vertex_colors=False)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
trees = [o for o in meshes if o.name.startswith('bg_trees')]
base = OUT[:-4] if OUT.endswith('.glb') else OUT
export(base + '_part1.glb', [o for o in meshes if o not in trees])
export(base + '_part2.glb', trees)
