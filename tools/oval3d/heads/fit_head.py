"""Fit a Tripo head onto the body's neck socket for the 3D oval (row 202, 2d).

Director 2026-11-17: "we have to do this for hundreds of players, your body has to be modular to fit every
head ... have a body with a neck socket and put sockets on all our heads". His plan, as approved: every
head's neck is cut, its cut edge is moved onto the socket's points so there is no gap or
overlap, the bottom 2 cm of his neck tapers into the socket and blends to the body's skin colour, and his
face, jaw and ears stay as scanned. Nothing is set by hand per player.

blender -b --python fit_head.py -- SRC.glb OUT.glb SOCKET.json [TEX_PX]
blender -b --python fit_head.py -- --all SRC_DIR OUT_DIR SOCKET.json [TEX_PX]   (every <pid>.glb)

Steps, all measured on his own head:
- Eye line: the bridge of his nose, the first dip in the face's profile above the nose tip.
- Size: his head's depth at the eye line (nose tip to back of the skull) is set to HEAD_DEPTH, Max Gawn's
  as measured on a photo of him standing against his body (x1.12 on the old fit, 2026-11-17).
- Place: eyes at EYE_FIT on the base body (Gawn's eyes once his head was grown), centred on its skull.
- Cut: on the socket's own line, leaning like it (a neck leans forward). The approved plan said 8 cm below
  the ear; measured, the socket is 12.3 cm below Gawn's ear at the sides (his ear canal level with the
  bottom of his eye socket, 1.5 cm under the eye line), so a cut 8 cm down left a 4.4 cm gap above it.
- Socket: the cut edge goes onto the socket ring (socket.py), and the 2 cm above it eases from the ring
  to his own neck. Every vertex's band share (1 on the ring, 0 from 2 cm up) is written to the vertex
  colour's red, for the game's skin blend and the build morphs (Oval3D._socket_head).
- Skin colour: printed from under the back of his neck and his cheeks, for heads.json.
The texture is cut to TEX_PX (default 2048) and stored as JPEG to keep the APK small.
"""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector, Matrix

HEAD_DEPTH = 0.2551  # Gawn: 0.2278 at the old fit x the photo's 1.12
EYE_FIT = 1.7524     # Gawn's eye line on the base body after the photo's growth
MH_Z = 0.0236        # the base body's skull middle (glTF z; Blender -y)
EAR_BELOW_EYE = 0.015
BAND = 0.02


def eye_line(ob):
    """The bridge of his nose: walk up the front profile from the nose tip to its first dip."""
    from mathutils.bvhtree import BVHTree
    me = ob.data
    co = [v.co for v in me.vertices]
    zmin, crown = min(c.z for c in co), max(c.z for c in co)
    mx = (min(c.x for c in co) + max(c.x for c in co)) / 2.0
    bvh = BVHTree.FromPolygons([c.copy() for c in co], [p.vertices[:] for p in me.polygons])
    h = crown - zmin
    step = h / 140.0
    prof = []
    z = zmin
    while z < crown:
        hit = bvh.ray_cast(Vector((mx, -10.0 * h, z)), Vector((0.0, 1.0, 0.0)))
        prof.append((z, -hit[0].y if hit[0] else None))
        z += step
    # Nose tip: the most forward point between 62% and 20% of the head's height down from the crown.
    win = [(z, f) for z, f in prof if f is not None and crown - 0.62 * h <= z <= crown - 0.2 * h]
    tip = max(win, key=lambda p: p[1])
    # The bridge: the deepest point of the profile in the stretch above the nose tip (35% of the way to
    # the crown), where the forehead has not yet sloped back.
    up = [(z, f) for z, f in prof if f is not None and tip[0] < z <= tip[0] + 0.35 * (crown - tip[0])]
    best = min(up, key=lambda p: p[1])
    return tip[0], best[0]


def fit(src, out, socket, tex_px):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    ob = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
    for o in bpy.context.scene.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    tip, eye_y = eye_line(ob)
    # Blender z up = glTF y; Blender -y = glTF +z.
    co = [v.co.copy() for v in ob.data.vertices]
    tol = (max(c.z for c in co) - min(c.z for c in co)) / 70.0
    band = [c for c in co if abs(c.z - eye_y) < tol]
    depth = max(-c.y for c in band) - min(-c.y for c in band)
    top = [c for c in co if c.z > eye_y]
    mid_fwd = (min(-c.y for c in top) + max(-c.y for c in top)) / 2.0
    mid_x = (min(c.x for c in top) + max(c.x for c in top)) / 2.0
    s = HEAD_DEPTH / depth
    print("nose tip", tip, "eye line", eye_y, "depth", depth, "scale", s)
    ob.data.transform(Matrix.Translation(Vector((0.0, -MH_Z, EYE_FIT))) @ Matrix.Scale(s, 4)
                      @ Matrix.Translation(Vector((-mid_x, mid_fwd, -eye_y))))
    # The socket ring in Blender space, in order round the neck, and the plane it leans on.
    sk = json.load(open(socket))
    ring = [Vector((p[0], -p[2], p[1])) for p in sk["ring"]]
    cx = sum(p.x for p in ring) / len(ring)
    cy = sum(p.y for p in ring) / len(ring)
    # Least squares z = a (x - cx) + b (y - cy) + c over the ring.
    sxx = sum((p.x - cx) ** 2 for p in ring)
    syy = sum((p.y - cy) ** 2 for p in ring)
    sxy = sum((p.x - cx) * (p.y - cy) for p in ring)
    sxz = sum((p.x - cx) * p.z for p in ring)
    syz = sum((p.y - cy) * p.z for p in ring)
    det = sxx * syy - sxy * sxy
    pa = (sxz * syy - syz * sxy) / det
    pb = (syz * sxx - sxz * sxy) / det
    pc = sum(p.z for p in ring) / len(ring)
    plane = lambda x, y: pa * (x - cx) + pb * (y - cy) + pc
    off = 0.0  # the cut runs on the socket's own line
    print("socket lean (deg): forward %.1f, sideways %.1f; at the sides %.1f cm below his ear" % (
        math.degrees(math.atan(-pb)), math.degrees(math.atan(pa)), 100 * (EYE_FIT - EAR_BELOW_EYE - pc)))

    def ang(x, y):
        return math.atan2(x - cx, -(y - cy)) % (2 * math.pi)

    ra = sorted(((ang(p.x, p.y), math.hypot(p.x - cx, p.y - cy), p.z) for p in ring))

    def ring_at(t):  # the ring's radius and height at angle t, between its two nearest points
        for i in range(len(ra)):
            a0, r0, z0 = ra[i]
            a1, r1, z1 = ra[(i + 1) % len(ra)]
            if i == len(ra) - 1:
                a1 += 2 * math.pi
            tt = t + 2 * math.pi if t < a0 else t
            if a0 <= tt <= a1:
                w = (tt - a0) / (a1 - a0)
                return r0 + (r1 - r0) * w, z0 + (z1 - z0) * w
        return ra[0][1], ra[0][2]

    # Cut on the socket's line, leaning like the socket.
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    n = Vector((-pa, -pb, 1.0)).normalized()
    co0 = Vector((cx, cy, pc + off))
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co0, plane_no=n,
                           clear_inner=True)
    bm.to_mesh(ob.data)
    bm.free()
    me = ob.data
    # His neck's cut edge, in 5-degree steps round the neck: its radius there.
    edge = {}
    for v in me.vertices:
        c = v.co
        if abs(c.z - (plane(c.x, c.y) + off)) < 1e-4:
            k = int(math.degrees(ang(c.x, c.y)) // 5) % 72
            edge.setdefault(k, []).append(math.hypot(c.x - cx, c.y - cy))
    print("cut edge: %d points, %d of 72 steps round the neck" % (sum(len(x) for x in edge.values()), len(edge)))
    er = {k: sum(x) / len(x) for k, x in edge.items()}

    def edge_r(t):
        k = int(math.degrees(t) // 5) % 72
        for d in range(36):
            for kk in ((k + d) % 72, (k - d) % 72):
                if kk in er:
                    return er[kk]
        return 0.06

    if os.environ.get("FIT_DEBUG"):
        for deg in range(0, 360, 20):
            t = math.radians(deg)
            rr, rz = ring_at(t)
            print("DBG %3d ring r %.4f z %.4f plane %.4f edge r %.4f" % (
                deg, rr, rz, plane(cx + rr * math.sin(t), cy - rr * math.cos(t)), edge_r(t)))
    # The band: from the cut edge (share 1) to 2 cm up (0). Each point moves down by the gap between the
    # cut and the socket at its angle, and in or out by the ring's radius over his neck's, by its share.
    share = [0.0] * len(me.vertices)
    rs, hs = [], []
    for v in me.vertices:
        c = v.co
        pz = plane(c.x, c.y) + off
        u = c.z - pz
        if u >= BAND:
            continue
        t = ang(c.x, c.y)
        w = max(0.0, min(1.0, 1.0 - u / BAND))
        w = w * w * (3.0 - 2.0 * w)
        rr, rz = ring_at(t)
        r = math.hypot(c.x - cx, c.y - cy)
        f = 1.0 + w * (rr / max(1e-4, edge_r(t)) - 1.0)
        rs.append(rr / max(1e-4, edge_r(t)))
        c.x = cx + (c.x - cx) * f
        c.y = cy + (c.y - cy) * f
        c.z += w * (rz - pz)
        hs.append(rz - pz)
        share[v.index] = w
    if rs:
        print("neck to socket: radius x%.2f-%.2f, height %.1f to %.1f cm" % (
            min(rs), max(rs), 100 * min(hs), 100 * max(hs)))
    # The share in the vertex colour's red.
    col = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    for i, w in enumerate(share):
        col.data[i].color = (w, 0.0, 0.0, 1.0)
    # His skin colour, under the back of his neck and on his cheeks (heads.json takes the clear one).
    img = next((i for i in bpy.data.images if i.size[0] > 0), None)
    if img is not None:
        w, h = img.size
        px = img.pixels[:]
        uv = me.uv_layers.active.data
        places = {
            "neck": lambda c: EYE_FIT - 0.13 < c.z < EYE_FIT - 0.07 and -c.y < MH_Z - 0.04,
            "cheek": lambda c: EYE_FIT - 0.04 < c.z < EYE_FIT - 0.02 and 0.045 < abs(c.x) < 0.07 and -c.y > MH_Z + 0.03,
        }
        for name, inside in places.items():
            acc, k = [0.0, 0.0, 0.0], 0
            for poly in me.polygons:
                for li in poly.loop_indices:
                    if inside(me.vertices[me.loops[li].vertex_index].co):
                        uu, vv = uv[li].uv
                        i = (min(h - 1, max(0, int(vv * h))) * w + min(w - 1, max(0, int(uu * w)))) * 4
                        for j in range(3):
                            acc[j] += px[i + j]
                        k += 1
            if k:
                print("SKIN %s #%02x%02x%02x from %d" % (name, *(round(255 * acc[j] / k) for j in range(3)), k))
    for img in bpy.data.images:
        if img.size[0] > tex_px:
            img.scale(tex_px, tex_px)
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_image_format="JPEG",
                              export_jpeg_quality=90, export_yup=True, export_vertex_color="ACTIVE",
                              export_all_vertex_colors=False)
    print("OUT", out, "tris", sum(len(p.vertices) - 2 for p in me.polygons))


a = sys.argv[sys.argv.index("--") + 1:]
if a[0] == "--all":
    src_dir, out_dir, socket = a[1], a[2], a[3]
    px = int(a[4]) if len(a) > 4 else 2048
    for f in sorted(os.listdir(src_dir)):
        if f.endswith(".glb"):
            print("HEAD", f)
            fit(os.path.join(src_dir, f), os.path.join(out_dir, f), socket, px)
else:
    fit(a[0], a[1], a[2], int(a[3]) if len(a) > 3 else 2048)
