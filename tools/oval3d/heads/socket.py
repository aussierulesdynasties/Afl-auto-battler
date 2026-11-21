"""The neck socket on the MetaHuman body (row 202, 2d; director 2026-11-17: "have a body with a neck socket
and put sockets on all our heads").

blender -b --python socket.py -- BODY.glb OUT.json

The socket is one of the body's own edge loops round the neck: the highest whole ring round it (above it
the loops run into the jaw), just under the MetaHuman's chin at the front and at the hairline at the back.
Every man wears the body's own neck up to there, so no head's neck is stretched to fit (director
2026-11-18: "plug and play head to body socket system"; the old ring sat on the collar). The body keeps
everything below it; every head is cut and fitted onto it (fit_head.py), and the game takes the body's
head off above it (Oval3D._without_head).

OUT.json: {"ring": [[x, y, z], ...]} in the body's rest space (glTF: y up, face toward +z), in order
round the neck, and "centre": the middle of the neck the ring goes round.
"""
import bpy, bmesh, sys, math, json
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
body, out = a[0], a[1]
SKIN, GUERNSEY = "ARD_skin", "ARD_guernsey"
CLEAR = 0.01  # the ring stays at least this far above the collar everywhere (metres)
# UNDER (metres): the collar join instead (director 2026-11-18, "Prove it on two"): the ring is the highest whole
# loop that stays at least this far UNDER the guernsey's neck edge all the way round, so the jumper hides the join
# and every man keeps his own neck down to it.
import os
UNDER = float(os.environ["UNDER"]) if os.environ.get("UNDER") else None
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


if UNDER is not None:
    # The collar join: the guernsey's open neck edge, traced round in 56 steps (its highest open edge point
    # within 4 degrees of each step), lowered UNDER and drawn 3 mm in, so his neck goes down inside the jumper.
    # The body has no skin under the jumper, so this ring is the jumper's edge, not one of the body's loops.
    edge = []
    for e in bm.edges:
        if sum(1 for f in e.link_faces if f.material_index == g_i) == 1:  # its edge (the skin may meet it there)
            for i in range(5):
                c = e.verts[0].co.lerp(e.verts[1].co, i / 4.0)
                if c.z > 1.45 and math.hypot(c.x, c.y) < 0.13:
                    edge.append(c.copy())
    pcx = sum(c.x for c in edge) / len(edge)
    pcy = sum(c.y for c in edge) / len(edge)
    pts = []
    for k in range(56):
        t = 360.0 * k / 56
        near = [c for c in edge if abs((math.degrees(math.atan2(c.x - pcx, -(c.y - pcy))) - t + 180) % 360 - 180) < 4]
        top = max(near, key=lambda c: c.z)
        d = Vector((top.x - pcx, top.y - pcy, 0.0))
        r = d.length
        pts.append(Vector((pcx, pcy, top.z - UNDER)) + d.normalized() * (r - 0.003))
    print("collar edge: front %.4f back %.4f, ring %d points %.4f..%.4f" % (
        pts[0].z + UNDER, pts[28].z + UNDER, len(pts), min(p.z for p in pts), max(p.z for p in pts)))
    gl = lambda c: [round(c.x, 6), round(c.z, 6), round(-c.y, 6)]
    cz = sum(p.z for p in pts) / len(pts)
    json.dump({"ring": [gl(p) for p in pts], "centre": [round(pcx, 6), round(cz, 6), round(-pcy, 6)]},
              open(out, "w", newline=""), indent=1)
    print("SOCKET %d points -> %s" % (len(pts), out))
    sys.exit(0)


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


# Loops through the back of the neck (x 0); the highest whole one that stays on the neck and clear of
# the collar.
seeds = sorted((v for v in bm.verts if abs(v.co.x) < 0.002 and v.co.y > 0 and (1.40 if UNDER is not None else 1.55) < v.co.z < 1.75
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
        over = max(v.co.z - collar[int(ang(v.co) // 10) % 36] for v in L)
        if UNDER is None and clear >= CLEAR:
            ring = L
        if UNDER is not None and over <= -UNDER and max(abs(v.co.x) for v in L) < 0.09:
            ring = L
if ring is None:
    sys.exit("no neck loop clear of the collar" if UNDER is None else "no neck loop under the collar")
cx = sum(v.co.x for v in ring) / len(ring)
cy = sum(v.co.y for v in ring) / len(ring)
cz = sum(v.co.z for v in ring) / len(ring)
ring.sort(key=lambda v: ang(v.co))
gl = lambda c: [round(c.x, 6), round(c.z, 6), round(-c.y, 6)]  # Blender z up -> glTF y up
json.dump({"ring": [gl(v.co) for v in ring], "centre": [round(cx, 6), round(cz, 6), round(-cy, 6)]},
          open(out, "w", newline=""), indent=1)
print("SOCKET %d points -> %s" % (len(ring), out))
