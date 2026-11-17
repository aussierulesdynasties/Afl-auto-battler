"""The neck socket on the MetaHuman body (row 202, 2d; director 2026-11-17: "have a body with a neck socket
and put sockets on all our heads").

blender -b --python socket.py -- BODY.glb OUT.json

The socket is one of the body's own edge loops round the neck: the lowest whole ring that is clear of the
guernsey collar all the way round, so the seam is skin on skin just above the collar. The body keeps
everything below it; every head is cut and fitted onto it (fit_head.py), and the game takes the body's
head off above it (Oval3D._without_head).

OUT.json: {"ring": [[x, y, z], ...]} in the body's rest space (glTF: y up, face toward +z), in order
round the neck, and "centre": the middle of the neck the ring goes round.
"""
import bpy, bmesh, sys, math, json
a = sys.argv[sys.argv.index("--") + 1:]
body, out = a[0], a[1]
SKIN, GUERNSEY = "ARD_skin", "ARD_guernsey"
CLEAR = 0.01  # the ring stays at least this far above the collar everywhere (metres)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=body)
ob = max((o for o in bpy.context.scene.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
mats = [m.name for m in ob.data.materials]
skin_i, g_i = mats.index(SKIN), mats.index(GUERNSEY)
bm = bmesh.new()
bm.from_mesh(ob.data)
# glTF splits vertices at seams and stores triangles: weld and rejoin the quads to see the loops.
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
bmesh.ops.join_triangles(bm, faces=bm.faces[:], angle_face_threshold=math.radians(40),
                         angle_shape_threshold=math.radians(40))
bm.verts.ensure_lookup_table()


def ang(c):  # 0 = his front (Blender -y), 90 = his left (+x)
    return math.degrees(math.atan2(c.x, -c.y)) % 360


# The collar's top edge round the neck, in 10-degree steps.
collar = [0.0] * 36
for f in bm.faces:
    if f.material_index != g_i:
        continue
    for v in f.verts:
        c = v.co
        if c.z > 1.45 and math.hypot(c.x, c.y) < 0.13:
            k = int(ang(c) // 10) % 36
            collar[k] = max(collar[k], c.z)


def loop_from(v, e):
    ring, cur, ce = [v], v, e
    for _ in range(400):
        nv = ce.other_vert(cur)
        if nv == v:
            return ring
        ring.append(nv)
        if len(nv.link_edges) != 4:
            return None
        fs = set(ce.link_faces)
        nxt = [x for x in nv.link_edges if x != ce and not (set(x.link_faces) & fs)]
        if len(nxt) != 1:
            return None
        cur, ce = nv, nxt[0]
    return None


# Loops through the back of the neck (x 0), lowest first.
seeds = sorted((v for v in bm.verts if abs(v.co.x) < 0.002 and v.co.y > 0 and 1.55 < v.co.z < 1.75
                and any(f.material_index == skin_i for f in v.link_faces)), key=lambda v: v.co.z)
ring = None
for s in seeds:
    for e in s.link_edges:
        if abs(e.other_vert(s).co.z - s.co.z) > 0.006:
            continue
        L = loop_from(s, e)
        if L is None or max(abs(v.co.x) for v in L) > 0.09:
            continue
        clear = min(v.co.z - collar[int(ang(v.co) // 10) % 36] for v in L)
        print("loop of %d at the nape %.4f, throat %.4f, clear of the collar by %.4f" % (
            len(L), s.co.z, min(v.co.z for v in L), clear))
        if clear >= CLEAR:
            ring = L
            break
    if ring:
        break
if ring is None:
    sys.exit("no neck loop clear of the collar")
cx = sum(v.co.x for v in ring) / len(ring)
cy = sum(v.co.y for v in ring) / len(ring)
cz = sum(v.co.z for v in ring) / len(ring)
ring.sort(key=lambda v: ang(v.co))
gl = lambda c: [round(c.x, 6), round(c.z, 6), round(-c.y, 6)]  # Blender z up -> glTF y up
json.dump({"ring": [gl(v.co) for v in ring], "centre": [round(cx, 6), round(cz, 6), round(-cy, 6)]},
          open(out, "w", newline=""), indent=1)
print("SOCKET %d points -> %s" % (len(ring), out))
