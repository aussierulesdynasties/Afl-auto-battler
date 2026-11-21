"""Wrap the MetaHuman's own head onto a player's Tripo head (row 202, 2d).

Director 2026-11-18: "we should be trying to make our heads behave like the one we cut off the Unreal model,
being roughly the same size and operate the same way that head did"; the wrap was chosen and is proved on
Gawn and Cross before the rest. The MetaHuman head (the body's own skin above the socket ring) is moved
point by point onto his Tripo head's surface, and his Tripo colours are copied onto it by Blender's bake
(each pixel takes the colour of the nearest point of his Tripo surface). His join is the body's own: the
ring's points do not move, the pull grows over the 5 cm above it.

blender -b --python wrap_head.py -- BODY.glb TRIPO.glb OUT.glb SOCKET.json [TEX_PX]

Steps:
- Head: the body's skin faces above the socket ring, welded; the inside of the mouth and nostrils (faces
  that see only the head itself) removed, and every hole but the ring closed (eyes, mouth).
- Size and place: his Tripo head scaled so its depth at the eye line (front-most less back-most surface
  hit, lines fired across the eye line) equals the MetaHuman's, his eye line on the MetaHuman's and his
  skull centred on it.
- Wrap: each point moves toward the nearest point of his surface; the moves are smoothed over their
  neighbours (so no point folds over another), in three rounds of less smoothing, the last exact.
- Colour: a 2K bake of his Tripo colours onto the wrapped head; the body's neck takes his cheek's colour.
"""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

a = sys.argv[sys.argv.index("--") + 1:]
BODY, SRC, OUT, SOCKET = a[0], a[1], a[2], a[3]
TEX_PX = int(a[4]) if len(a) > 4 else 2048
RISE = 0.05   # the pull grows from nothing at the ring to full over this height
BAND = 0.02   # the vertex colour's share band (1 on the ring, 0 from 2 cm up), as fit_head.py writes

# The eye-line finder is fit_head.py's own.
_ns = {}
_fh = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fit_head.py")).read()
exec(_fh[:_fh.index("def hair_points")], _ns)
eye_line = _ns["eye_line"]


def surface_depth(ob, eye_z):
    """Front-most less back-most surface hit, lines fired across the eye line (fit_head.py's measure)."""
    co = [v.co for v in ob.data.vertices]
    hh = max(c.z for c in co) - min(c.z for c in co)
    bvh = BVHTree.FromPolygons([c.copy() for c in co], [p.vertices[:] for p in ob.data.polygons])
    mx = (min(c.x for c in co) + max(c.x for c in co)) / 2.0
    fr, bk = [], []
    for i in range(-4, 5):
        for j in range(-3, 4):
            x, z = mx + j * hh / 140.0, eye_z + i * hh / 280.0
            hf = bvh.ray_cast(Vector((x, -10.0, z)), Vector((0.0, 1.0, 0.0)))
            hb = bvh.ray_cast(Vector((x, 10.0, z)), Vector((0.0, -1.0, 0.0)))
            if hf[0] is not None:
                fr.append(-hf[0].y)
            if hb[0] is not None:
                bk.append(-hb[0].y)
    top = [c for c in co if c.z > eye_z]
    mid_fwd = (min(-c.y for c in top) + max(-c.y for c in top)) / 2.0
    mid_x = (min(c.x for c in top) + max(c.x for c in top)) / 2.0
    return max(fr) - min(bk), mid_x, mid_fwd


def import_one(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        o.select_set(False)
    return new


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# --- The MetaHuman head: the body's skin above the ring.
body_objs = import_one(BODY)
body = max((o for o in body_objs if o.type == "MESH"), key=lambda o: len(o.data.vertices))
sk = json.load(open(SOCKET))
ring_pts = [Vector((p[0], -p[2], p[1])) for p in sk["ring"]]  # glTF y up -> Blender z up
bm = bmesh.new()
bm.from_mesh(body.data)
bm.transform(body.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=4e-4)  # the hair shell's edge onto the skin
bm.verts.ensure_lookup_table()
mats = [m.name for m in body.data.materials]
skin_i = mats.index("ARD_skin")
hair_i = mats.index("ARD_hair")
head_mats = (skin_i, hair_i)  # the MetaHuman skin has no crown: its hair shell is the top of his skull
kd = KDTree(len(bm.verts))
for v in bm.verts:
    kd.insert(v.co, v.index)
kd.balance()
ring_v = set()
for p in ring_pts:
    co, i, d = kd.find(p)
    if d < 1e-3:
        ring_v.add(i)
print("ring: %d of %d socket points found on the body" % (len(ring_v), len(ring_pts)))
# Flood from the crown over skin faces, never across a ring edge.
crown = max((f for f in bm.faces if f.material_index == skin_i), key=lambda f: f.calc_center_median().z)
keep, todo = {crown}, [crown]
while todo:
    f = todo.pop()
    for e in f.edges:
        if e.verts[0].index in ring_v and e.verts[1].index in ring_v:
            continue
        for g in e.link_faces:
            if g not in keep and g.material_index in head_mats:
                keep.add(g)
                todo.append(g)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in keep], context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
print("MetaHuman head: %d faces above the ring" % len(bm.faces))
# The inside of his mouth and nostrils: faces whose lines out (along the normal and tilted 45 degrees four
# ways) all hit the head itself.
bm.normal_update()
tree = BVHTree.FromBMesh(bm)
inner = []
for f in bm.faces:
    n = f.normal
    if n.length < 0.5:
        continue
    t1 = n.orthogonal().normalized()
    t2 = n.cross(t1)
    o = f.calc_center_median() + n * 0.0005
    if all(tree.ray_cast(o, (n + d).normalized(), 0.2)[0] is not None
           for d in (Vector(), t1, -t1, t2, -t2)):
        inner.append(f)
bmesh.ops.delete(bm, geom=inner, context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
bm.verts.ensure_lookup_table()
ring_v = set(v.index for v in bm.verts if min((v.co - p).length for p in ring_pts) < 1e-3)
holes = [e for e in bm.edges if e.is_boundary and not (e.verts[0].index in ring_v and e.verts[1].index in ring_v)]
lay = bm.faces.layers.int.new("fill")  # made before the fill: a new layer drops earlier face handles
for f in bmesh.ops.holes_fill(bm, edges=holes, sides=0)["faces"]:
    f[lay] = 1
bmesh.ops.triangulate(bm, faces=bm.faces[:])
# Each closed hole (eyes, mouth, nostrils) gets points inside, so the wrap can shape it and its colour doesn't smear.
for _ in range(2):
    es = [e for e in bm.edges if e.link_faces and all(g[lay] for g in e.link_faces)]
    bmesh.ops.subdivide_edges(bm, edges=es, cuts=1, use_grid_fill=False)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if f[lay]])
bm.faces.layers.int.remove(lay)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])  # the hair shell is wound the other way to the skin
print("inside removed: %d faces; %d hole edges closed" % (len(inner), len(holes)))
me = bpy.data.meshes.new("head")
bm.to_mesh(me)
bm.free()
head = bpy.data.objects.new("head", me)
sc.collection.objects.link(head)
for o in body_objs:
    bpy.data.objects.remove(o, do_unlink=True)
for uvl in list(me.uv_layers):
    me.uv_layers.remove(uvl)
# The MetaHuman's own shading directions travel with its points: cleared, so his face is lit (and baked) by
# its own shape, not by the MetaHuman's hairline and eyelids.
for at in [a.name for a in me.attributes if a.name in ("custom_normal", "sharp_face", "sharp_edge")]:
    me.attributes.remove(me.attributes[at])
for poly in me.polygons:
    poly.use_smooth = True
print("custom normals left:", me.has_custom_normals)
ring_ix = [v.index for v in me.vertices if min((v.co - p).length for p in ring_pts) < 1e-3]

# --- His Tripo head, sized and placed on the MetaHuman's.
mh_tip, mh_eye = eye_line(head)
mh_depth, mh_x, mh_fwd = surface_depth(head, mh_eye)
src_objs = import_one(SRC)
tri = [o for o in src_objs if o.type == "MESH"][0]
bpy.context.view_layer.objects.active = tri
tri.select_set(True)
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
tri.select_set(False)
t_tip, t_eye = eye_line(tri)
t_depth, t_x, t_fwd = surface_depth(tri, t_eye)
# His size is fit_head.py's: his depth at the eye line = HEAD_DEPTH x his heads.json "scale" (default HEAD_SCALE).
_pid = os.path.splitext(os.path.basename(OUT))[0]
_hj = os.path.join(os.path.dirname(OUT), "heads.json")
_scale = float((json.load(open(_hj)) if os.path.exists(_hj) else {}).get(_pid, {}).get("scale", _ns["HEAD_SCALE"]))
s = _ns["HEAD_DEPTH"] * _scale / t_depth
tri.data.transform(Matrix.Translation(Vector((mh_x, -mh_fwd, mh_eye))) @ Matrix.Scale(s, 4)
                   @ Matrix.Translation(Vector((-t_x, t_fwd, -t_eye))))
print("size: his depth %.3f -> %.3f (scale %.2f), MetaHuman %.3f; eye line %.3f" % (t_depth, t_depth * s, _scale, mh_depth, mh_eye))

# --- The wrap.
ring_c = sum(ring_pts, Vector()) / len(ring_pts)


def ring_z(c):  # the ring's height at this point's angle round the neck
    t = math.atan2(c.x - ring_c.x, -(c.y - ring_c.y))
    best = min(ring_pts, key=lambda p: abs((math.atan2(p.x - ring_c.x, -(p.y - ring_c.y)) - t + math.pi)
                                           % (2 * math.pi) - math.pi))
    return best.z


wt = []
for v in me.vertices:
    u = max(0.0, min(1.0, (v.co.z - ring_z(v.co)) / RISE))
    wt.append(u * u * (3.0 - 2.0 * u))
for i in ring_ix:
    wt[i] = 0.0
tbvh = BVHTree.FromPolygons([v.co.copy() for v in tri.data.vertices], [p.vertices[:] for p in tri.data.polygons])
nb = [[] for _ in me.vertices]
for e in me.edges:
    i, j = e.vertices
    nb[i].append(j)
    nb[j].append(i)
# Smooth the MetaHuman head into a plain shape first (his shape replaces it): its hairline lip, eyelids, nostrils
# and ear folds would otherwise fold over when laid on his surface. The join band keeps its shape.
for _ in range(40):
    mid = [sum((me.vertices[j].co for j in nb[i]), Vector()) / len(nb[i]) if nb[i] else me.vertices[i].co.copy()
           for i in range(len(me.vertices))]
    for i, v in enumerate(me.vertices):
        v.co = v.co.lerp(mid[i], 0.5 * wt[i])


def onto(co):
    """The nearest spot of his surface."""
    h = tbvh.find_nearest(co)
    return h[0] if h[0] is not None else co


# Rounds: every point toward the nearest spot of his surface, the moves smoothed over neighbours (less each round,
# the last exact), then relaxed toward the neighbours' middle and put back on, which unfolds small creases.
for rnd, smooth in enumerate((12, 4, 0)):
    disp = [onto(v.co) - v.co for v in me.vertices]
    for _ in range(smooth):
        disp = [(disp[i] + sum((disp[j] for j in nb[i]), Vector())) / (1 + len(nb[i])) for i in range(len(disp))]
    for i, v in enumerate(me.vertices):
        v.co += disp[i] * wt[i]
    print("wrap round %d (smoothing %d): mean move %.2f mm" % (
        rnd + 1, smooth, 1000 * sum(d.length * w for d, w in zip(disp, wt)) / max(1, len(disp))))
for _ in range(10):
    mid = [sum((me.vertices[j].co for j in nb[i]), Vector()) / len(nb[i]) if nb[i] else me.vertices[i].co.copy()
           for i in range(len(me.vertices))]
    for i, v in enumerate(me.vertices):
        if wt[i] > 0.0:
            v.co = v.co.lerp(onto(v.co.lerp(mid[i], 0.5)), wt[i])
gap = [tbvh.find_nearest(v.co)[3] for v, w in zip(me.vertices, wt) if w > 0.99]
print("wrapped: %d points on his surface, off it by at most %.1f mm" % (len(gap), 1000 * max(gap)))

# --- His colours: the head wears his own Tripo texture (nothing is re-drawn). Each face of the wrapped head takes the
# one triangle of his surface under its middle, and all its corners read the texture from that same triangle (past its
# edge where a corner sits beyond it), so no face ever spans two pieces of his texture sheet.
from mathutils.geometry import barycentric_transform
tme = tri.data
tme.calc_loop_triangles()
tuv = tme.uv_layers.active.data
lts = tme.loop_triangles
lbvh = BVHTree.FromPolygons([v.co.copy() for v in tme.vertices], [lt.vertices[:] for lt in lts])
me.uv_layers.new(name="UVMap")
uvd = me.uv_layers.active.data
for poly in me.polygons:
    c = sum((me.vertices[i].co for i in poly.vertices), Vector()) / len(poly.vertices)
    lt = lts[lbvh.find_nearest(c)[2]]
    A, B, C = (tme.vertices[i].co for i in lt.vertices)
    a, b, cc = (tuv[li].uv.to_3d() for li in lt.loops)
    for li in poly.loop_indices:
        q = barycentric_transform(me.vertices[me.loops[li].vertex_index].co, A, B, C, a, b, cc)
        uvd[li].uv = (q.x, q.y)
mat = tri.data.materials[0]
me.materials.append(mat)
img = [n.image for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image][0]
img.pack()
TEX_PX = img.size[0]
# His cheek's colour for the body's neck (heads.json "skin").
px = img.pixels[:]
acc, k = [0.0, 0.0, 0.0], 0
for poly in me.polygons:
    for li in poly.loop_indices:
        c = me.vertices[me.loops[li].vertex_index].co
        if mh_eye - 0.04 < c.z < mh_eye - 0.02 and 0.045 < abs(c.x - mh_x) < 0.07 and c.y < 0.0:
            uu, vv = uvd[li].uv
            i = (min(TEX_PX - 1, int(vv * TEX_PX)) * TEX_PX + min(TEX_PX - 1, int(uu * TEX_PX))) * 4
            for j in range(3):
                acc[j] += px[i + j]
            k += 1
hexc = "#%02x%02x%02x" % tuple(round(255 * min(1.0, acc[j] / max(1, k))) for j in range(3))
print("SKIN cheek %s from %d" % (hexc, k))
pid = os.path.splitext(os.path.basename(OUT))[0]
hj = os.path.join(os.path.dirname(OUT), "heads.json")
info = json.load(open(hj)) if os.path.exists(hj) else {}
info.setdefault(pid, {})["skin"] = hexc
json.dump(info, open(hj, "w", newline=""))
# The share band in the vertex colour, as fit_head.py writes it: red 1 on the ring to 0 from 2 cm up,
# green his skin blend (the body's skin over the band's bottom 70%).
col = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
for i, v in enumerate(me.vertices):
    u = max(0.0, v.co.z - ring_z(v.co))
    w = max(0.0, min(1.0, 1.0 - u / BAND))
    w = w * w * (3.0 - 2.0 * w)
    col.data[i].color = (w, min(1.0, max(0.0, 1.0 - u / BAND) / 0.3), 0.0, 1.0)
bpy.data.objects.remove(tri, do_unlink=True)
for o in list(sc.objects):
    o.select_set(o == head)
img.file_format = "JPEG"
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_image_format="JPEG",
                          export_jpeg_quality=90, export_yup=True, export_vertex_color="ACTIVE",
                          export_all_vertex_colors=False)
print("OUT", OUT, "tris", len(me.polygons))
