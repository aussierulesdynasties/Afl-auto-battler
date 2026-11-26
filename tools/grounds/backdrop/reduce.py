"""Cut a stadium's Blender background scene (scene.blend, built by the .claude/review/<ground>_bg
pipeline) down to the match's backdrop: assets/grounds/<slug>/<slug>_backdrop.glb (row 202 2b).
   python reduce.py -- scene.blend out.glb [tex_px] [near_r] [mid_keep] [far_keep]
The stadium model in the scene (every object not named bg_*) is dropped, and so is the scene's
ground under the stadium. Big meshes are decimated, the trees thinned with distance, the ground
bake scaled to tex_px, and everything cut into wedges round the ground (see SECTORS).
Needs the scene's textures where the .blend points (//../../tex, //../../data/<ground>/prep).
"""
import bpy, bmesh, sys, os, re, numpy as np, math
a = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = a[0], a[1]
TEX = int(a[2]) if len(a) > 2 else 4096
NEAR_R = float(a[3]) if len(a) > 3 else 350.0     # trees nearer than this are all kept
MID_R = 800.0
MID_KEEP = float(a[4]) if len(a) > 4 else 0.4     # share of trees kept from NEAR_R to MID_R
FAR_KEEP = float(a[5]) if len(a) > 5 else 0.15    # share kept past MID_R
INNER = float(a[6]) if len(a) > 6 else 0.0         # radius round the ground left to the game's own near
                                                    # surroundings (GroundModels.SURROUNDS "outer")
SKYLINE = a[7] if len(a) > 7 else ''                # skyline.json from osm_skyline.py: towers added past INNER
bpy.ops.wm.open_mainfile(filepath=SRC)
for im in bpy.data.images:
    if im.packed_file is None and im.filepath: im.reload()
    if im.size[0] == 0: print("MISSING", im.name)
rng = np.random.default_rng(7)
# BG_YAW (degrees): the scene was built north-up round a copy of the model turned by this much to sit on the
# real map (tools/grounds/backdrop/place.py); turn everything back so the backdrop lies in the model's own frame.
YAW = float(os.environ.get('BG_YAW', '0'))
if YAW:
    import mathutils
    RZ = mathutils.Matrix.Rotation(math.radians(-YAW), 4, 'Z')
    for o in bpy.data.objects:
        if o.parent is None: o.matrix_world = RZ @ o.matrix_world
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = next(o for o in bpy.data.objects if o.type == 'MESH')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True, isolate_users=True)
    print('turned back by', YAW)

def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)

# the stadium's footprint: the convex hull of the stadium model (its plaza is its outermost ground), drawn 4 m
# smaller so the scene's ground runs a little under the plaza's edge. The scene's ground inside it
# would lie over the arena.
# BG_HULL_SKIP: model parts left out of the footprint, because the game hides them where the backdrop is drawn
# (GroundModels.BACKDROP_HIDES: the ground kit's 240 m concourse disc).
SKIP = tuple(n for n in os.environ.get('BG_HULL_SKIP', '').split(',') if n)
MODEL = [o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith('bg_') and not (SKIP and o.name.startswith(SKIP))]
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

SEAMED = ('bg_near_ground', 'bg_far_terrain')
if INNER > 0.0:   # the game draws its own ground, trees and buildings in here: nothing twice
    for o in [o for o in bpy.data.objects if o.type == 'MESH']:
        bm = bmesh.new(); bm.from_mesh(o.data); M = o.matrix_world
        if o.name in SEAMED:   # the ground keeps every face reaching past the circle: no gap at the seam
            kill = [f for f in bm.faces if max((M @ v.co).xy.length for v in f.verts) < INNER]
        else:
            kill = [f for f in bm.faces if (M @ f.calc_center_median()).xy.length < INNER]
        if kill:
            bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(o.data)
        bm.free()
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and len(o.data.polygons) == 0]:
        bpy.data.objects.remove(o, do_unlink=True)

g = bpy.data.objects['bg_near_ground']
bm = bmesh.new(); bm.from_mesh(g.data); M = g.matrix_world
kill = [f for f in bm.faces if under_stadium(*(M @ f.calc_center_median()).xy)]
bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(g.data); bm.free()
print('ground faces cut under stadium', len(kill))

if SKYLINE:
    exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'skyline.py')).read())

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

# the seam with the game's own ground (a flat disc at z 0 out to INNER): the scene's ground ends on
# the circle at the disc's height, and the coarse far terrain inside it sinks out of sight
if INNER > 0.0:
    for n in SEAMED:
        o = bpy.data.objects.get(n)
        if o is None: continue
        Mi = o.matrix_world.inverted(); M = o.matrix_world
        for v in o.data.vertices:
            w = M @ v.co; r = w.xy.length
            if r >= INNER: continue
            if n == 'bg_near_ground':
                k = INNER / max(r, 1e-3); w.x *= k; w.y *= k; w.z = -0.1
            else:
                w.z = min(w.z, -5.0)
            v.co = Mi @ w

# trees: clumps thinned with distance, kept ones grown so the canopy keeps its cover. With
# BG_BUDGET (triangles for the whole backdrop) the mid and far keep shares shrink together so the
# trees take at most 45% of it, and the other big flat meshes are decimated to fit the rest.
BUDGET = int(os.environ.get('BG_BUDGET', '0'))
def _tris_all(objs): return sum(tris(o) for o in objs)
tree_objs = [o for o in bpy.data.objects if o.name.startswith('bg_trees')]
scans = []
for o in tree_objs:
    bm = bmesh.new(); bm.from_mesh(o.data)
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
    scans.append((o, bm, comps))
zone = [0, 0, 0]
for o, bm, comps in scans:
    per = tris(o) / max(1, len(comps))
    for c in comps:
        cen = sum((v.co for v in c), c[0].co * 0) / len(c); r = math.hypot(cen.x, cen.y)
        zone[0 if r < NEAR_R else (1 if r < MID_R else 2)] += per
SCALE = 1.0
if BUDGET:
    want = 0.45 * BUDGET
    thin = MID_KEEP * zone[1] + FAR_KEEP * zone[2]
    if zone[0] + thin > want and thin > 0:
        SCALE = max(0.05, (want - min(zone[0], 0.5 * want)) / thin)
    print('tree tris near/mid/far', [int(z) for z in zone], 'keep scale', round(SCALE, 3))
mid_k, far_k = min(1.0, MID_KEEP * SCALE), min(1.0, FAR_KEEP * SCALE)
near_k = 1.0 if zone[0] <= 0.5 * max(1, 0.45 * BUDGET) or not BUDGET else 0.5 * 0.45 * BUDGET / zone[0]
for o, bm, comps in scans:
    kill = []; kept = 0
    for c in comps:
        cen = sum((v.co for v in c), c[0].co * 0) / len(c)
        r = math.hypot(cen.x, cen.y)
        keep = near_k if r < NEAR_R else (mid_k if r < MID_R else far_k)
        if keep < 1.0 and rng.random() > keep:
            kill.extend(c); continue
        kept += 1
        if r >= NEAR_R:   # thinned: the kept ones grow to keep the canopy's cover
            sx = 1.3 if r < MID_R else 1.6; sz = 1.0 if r < MID_R else 1.15
            base = min(v.co.z for v in c)
            for v in c:
                d = v.co - cen
                v.co.x = cen.x + d.x * sx; v.co.y = cen.y + d.y * sx; v.co.z = base + (v.co.z - base) * sz
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(o.data); bm.free()
    print(o.name, 'clumps', len(comps), 'kept', kept)

if BUDGET:   # the rest: big flat meshes decimated (buildings stay whole: boxes do not decimate well)
    meshes_ = [o for o in bpy.data.objects if o.type == 'MESH']
    rest = [o for o in meshes_ if not o.name.startswith('bg_trees')]
    flat = [o for o in rest if not re.match(r'bg_(bld|roof|clad|flash|lm_)', o.name) and tris(o) > 3000]
    room = BUDGET - _tris_all(tree_objs) - _tris_all([o for o in rest if o not in flat])
    have = _tris_all(flat)
    if have > room > 0:
        g = max(0.08, room / have)
        for o in flat: decimate(o.name, g)
        print('budget: flat meshes decimated to', round(g, 3))
    blds = [o for o in rest if o not in flat]
    if _tris_all(blds) > 0.35 * BUDGET:   # too many houses: far ones go, each wall with its own roof
        from mathutils.kdtree import KDTree
        def comps_of(o):
            bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
            seen = set(); out = []
            bm.faces.ensure_lookup_table()
            for f in bm.faces:
                if f.index in seen: continue
                st = [f]; c = []; seen.add(f.index)
                while st:
                    x = st.pop(); c.append(x.index)
                    for e in x.edges:
                        for y in e.link_faces:
                            if y.index not in seen: seen.add(y.index); st.append(y)
                cen = sum((bm.faces[i].calc_center_median() for i in c), bm.faces[c[0]].calc_center_median() * 0) / len(c)
                out.append((c, cen))
            bm.free(); return out
        walls = [(o, comps_of(o)) for o in blds if re.match(r'bg_(bld|clad|flash)', o.name)]
        roofs = [(o, comps_of(o)) for o in blds if o.name.startswith('bg_roof')]
        far_t = sum(len(c) for o, cs in walls + roofs for c, cen in cs if cen.xy.length > 600.0)
        over = _tris_all(blds) - 0.35 * BUDGET
        keep = max(0.1, 1.0 - over / max(1, far_t * 2))   # faces ~ two triangles
        kd = KDTree(sum(len(cs) for o, cs in walls)); allw = []
        for o, cs in walls:
            for c, cen in cs:
                drop = cen.xy.length > 600.0 and rng.random() > keep
                kd.insert((cen.x, cen.y, 0.0), len(allw)); allw.append(drop)
        kd.balance()
        def cut(o, cs, drops):
            kill = set(i for (c, cen), d in zip(cs, drops) if d for i in c)
            if not kill: return
            bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.faces[i] for i in kill], context='FACES'); bm.to_mesh(o.data); bm.free()
        i = 0
        for o, cs in walls:
            cut(o, cs, allw[i:i + len(cs)]); i += len(cs)
        for o, cs in roofs:
            cut(o, cs, [allw[kd.find((cen.x, cen.y, 0.0))[1]] if allw else False for c, cen in cs])
        print('budget: far buildings kept', round(keep, 3))
    print('budget: buildings', _tris_all(blds), 'trees', _tris_all(tree_objs))

# fewer draws: objects whose materials are the same (same images, same nodes, same settings) are
# joined into one object with one material. All the trees share one leaf material (their kinds
# differ only in shape and vertex colour). Joined before slicing, so each family is cut once.
import re
# fewer looks, fewer draws: a family drawn in several texture variants (bg_bld_house_v0..v7) keeps
# only VARIANTS of them (each building keeps its own vertex colour, so the street still varies);
# small numbered things (netball courts, pool parts) and the towers share one
VARIANTS = int(os.environ.get('BG_VARIANTS', '0'))
if VARIANTS > 0:
    for o in bpy.data.objects:
        m_ = re.match(r'^(bg_netball|bg_pool)_(\d+)$', o.name)
        if m_: o.name = '%s_v%s' % m_.groups()
    fams = {}
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and len(o.data.materials) == 1]:
        m_ = re.match(r'^(.+)_v(\d+)$', o.name)
        if m_: fams.setdefault(m_.group(1), []).append((int(m_.group(2)), o))
    for f, vs in fams.items():
        vs.sort(key=lambda t: t[0])
        keep = VARIANTS if f in ('bg_bld_house', 'bg_bld_block') else 1
        for i, (_, o) in enumerate(vs):
            o.data.materials[0] = vs[i % keep][1].data.materials[0]
        print('variants', f, len(vs), '->', min(keep, len(vs)))

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
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.name not in ('bg_far_terrain', 'bg_road_kerbs') and len(o.data.polygons) > int(os.environ.get('BG_SLICE', '30000'))]:
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

# textures: the ground bake down to TEX; one- and two-channel images made RGBA (webp holds no grey)
for im in list(bpy.data.images):
    if im.size[0] > TEX:
        im.scale(TEX, TEX); print('scaled', im.name)
    if im.size[0] > 0 and (im.channels < 3 or im.depth in (8, 16)):   # grey files (depth 8/16)
        w, h = im.size; ch = im.channels
        px = np.zeros(len(im.pixels), np.float32); im.pixels.foreach_get(px); px = px.reshape(-1, ch)
        rgba = np.ones((len(px), 4), np.float32); rgba[:, :3] = px[:, :1]
        if ch == 2: rgba[:, 3] = px[:, 1]
        nim = bpy.data.images.new(im.name + '_rgb', w, h, alpha=True); nim.pixels.foreach_set(rgba.ravel())
        nim.pack(); im.user_remap(nim); print('grey image made RGBA', im.name)

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
