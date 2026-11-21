"""Fit a Tripo head onto the body under his jaw (row 202, 2d; director 2026-11-18, "Build it": every head is cut
under his own jaw and the body's own neck rises to meet it, so no Tripo neck, shoulders or shirt is ever used).

blender -b --python fit_jaw.py -- SRC.glb OUT.glb SOCKET.json [TEX_PX]
blender -b --python fit_jaw.py -- --all SRC_DIR OUT_DIR SOCKET.json [TEX_PX]   (every <pid>.glb)

The same for every head, nothing set by hand:
- Size and place: as fit_head.py (his depth at the eye line = HEAD_DEPTH x his scale, eyes on the body's).
- The cut: under his jaw. Down his face's front profile from the chin, the first point 2.5 cm behind the
  chin's front is where the jaw turns into the throat; the cut runs through it, leaning like the body's
  neck ring (socket.py: under the body's chin at the front, the hairline at the back). Everything of his
  below it (neck, shoulders, a shirt, the beard's hanging ends) is gone.
- The neck: a tube from the body's ring up to his cut edge, every point of his edge joined to the ring
  point straight below it, rising straight up off the ring and easing in or out to his edge. It is the
  body's skin: the vertex colour's red is its share of the body (1 on the ring, 0 at his jaw), so it bends
  with the body's neck bones and takes the build morphs (Oval3D.socket_head); its green 1 draws it in the
  body's skin colour.
- The colour: his cheek's colour goes to heads.json (the body's skin); his face blends to it over the
  1.5 cm above the cut (not hair), so no line shows where his jaw meets the neck.
"""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fit_head as F

BEHIND = 0.025   # the jaw's turn: this far behind the chin's front
ROWS = 6         # the neck tube's rows
FADE = 0.015     # his face blends to the body's skin over this height above the cut
MIN_NECK = 0.01  # the shortest neck between ring and cut (a head whose cut falls lower is lifted)


def fit(src, out, socket, tex_px):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    ob = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
    for o in bpy.context.scene.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    tip, eye_y = F.eye_line(ob)
    co = [v.co.copy() for v in ob.data.vertices]
    hh = max(c.z for c in co) - min(c.z for c in co)
    bvh = BVHTree.FromPolygons([c.copy() for c in co], [p.vertices[:] for p in ob.data.polygons])
    mx0 = (min(c.x for c in co) + max(c.x for c in co)) / 2.0
    fronts, backs = [], []
    for i in range(-4, 5):
        for j in range(-3, 4):
            x, z = mx0 + j * hh / 140.0, eye_y + i * hh / 280.0
            hf = bvh.ray_cast(Vector((x, -10.0 * hh, z)), Vector((0.0, 1.0, 0.0)))
            hb = bvh.ray_cast(Vector((x, 10.0 * hh, z)), Vector((0.0, -1.0, 0.0)))
            if hf[0] is not None:
                fronts.append(-hf[0].y)
            if hb[0] is not None:
                backs.append(-hb[0].y)
    depth = max(fronts) - min(backs)
    top = [c for c in co if c.z > eye_y]
    mid_fwd = (min(-c.y for c in top) + max(-c.y for c in top)) / 2.0
    mid_x = (min(c.x for c in top) + max(c.x for c in top)) / 2.0
    pid = os.path.splitext(os.path.basename(out))[0]
    hj = os.path.join(os.path.dirname(out), "heads.json")
    info = json.load(open(hj)) if os.path.exists(hj) else {}
    s = F.HEAD_DEPTH / depth * float(info.get(pid, {}).get("scale", F.HEAD_SCALE))
    lift = 0.0
    xf = lambda lift: (Matrix.Translation(Vector((0.0, -F.MH_Z, F.EYE_FIT + lift))) @ Matrix.Scale(s, 4)
                       @ Matrix.Translation(Vector((-mid_x, mid_fwd, -eye_y))))
    ob.data.transform(xf(0.0))
    tip = (tip - eye_y) * s + F.EYE_FIT
    me = ob.data

    # The body's ring and its lean.
    sk = json.load(open(socket))
    ring = [Vector((p[0], -p[2], p[1])) for p in sk["ring"]]
    cx = sum(p.x for p in ring) / len(ring)
    cy = sum(p.y for p in ring) / len(ring)
    sxx = sum((p.x - cx) ** 2 for p in ring)
    syy = sum((p.y - cy) ** 2 for p in ring)
    sxy = sum((p.x - cx) * (p.y - cy) for p in ring)
    sxz = sum((p.x - cx) * p.z for p in ring)
    syz = sum((p.y - cy) * p.z for p in ring)
    det = sxx * syy - sxy * sxy
    pa = (sxz * syy - syz * sxy) / det
    pb = (syz * sxx - sxz * sxy) / det
    pc = sum(p.z for p in ring) / len(ring)
    ang = lambda x, y: math.atan2(x - cx, -(y - cy)) % (2 * math.pi)
    ra = sorted((ang(p.x, p.y), math.hypot(p.x - cx, p.y - cy), p.z) for p in ring)

    def ring_at(t):
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

    # His jaw's turn, on his front profile.
    bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [p.vertices[:] for p in me.polygons])
    prof = []
    z = tip - 0.02
    while z > tip - 0.20:
        hit = bvh.ray_cast(Vector((0.0, -5.0, z)), Vector((0.0, 1.0, 0.0)))
        prof.append((z, -hit[0].y if hit[0] else None))
        z -= 0.002
    chin = max((p for p in prof if p[1] is not None and tip - 0.10 <= p[0] <= tip - 0.05), key=lambda p: p[1])
    turn = next(p for p in prof if p[0] < chin[0] and p[1] is not None and p[1] < chin[1] - BEHIND)
    jz, jy = turn[0], -turn[1]
    off = jz - (pa * (0.0 - cx) + pb * (jy - cy) + pc)
    gaps = []
    for t in range(0, 360, 10):
        rr, rz = ring_at(math.radians(t))
        x, y = cx + rr * math.sin(math.radians(t)), cy - rr * math.cos(math.radians(t))
        gaps.append(pa * (x - cx) + pb * (y - cy) + pc + off - rz)
    print("chin %.4f (front %.4f), jaw turn %.4f, %.1f cm under the eye line; neck between ring and cut %.1f-%.1f cm" % (
        chin[0], chin[1], jz, 100 * (F.EYE_FIT - jz), 100 * min(gaps), 100 * max(gaps)))
    if min(gaps) < MIN_NECK:
        lift = MIN_NECK - min(gaps)
        me.transform(Matrix.Translation(Vector((0.0, 0.0, lift))))
        off += lift
        print("LIFT %.1f cm: his jaw fell below the ring" % (100 * lift))
    plane = lambda x, y: pa * (x - cx) + pb * (y - cy) + pc + off

    # His cheek colour (the body's skin), before the cut.
    img = next((i for i in bpy.data.images if i.size[0] > 0), None)
    W, H = img.size
    px = img.pixels[:]
    uvl = me.uv_layers.active.data
    acc, k = [0.0, 0.0, 0.0], 0
    lum = {}
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            c = me.vertices[vi].co
            uu, vv = uvl[li].uv
            i = (min(H - 1, max(0, int(vv * H))) * W + min(W - 1, max(0, int(uu * W)))) * 4
            lum[vi] = (px[i] + px[i + 1] + px[i + 2]) / 3.0
            if F.EYE_FIT + lift - 0.04 < c.z < F.EYE_FIT + lift - 0.02 and 0.045 < abs(c.x) < 0.07 and -c.y > F.MH_Z + 0.03:
                for j in range(3):
                    acc[j] += px[i + j]
                k += 1
    cheek = [a / k for a in acc]
    hexc = "#%02x%02x%02x" % tuple(round(255 * a) for a in cheek)
    print("SKIN cheek %s from %d" % (hexc, k))
    info.setdefault(pid, {})["skin"] = hexc
    json.dump(info, open(hj, "w", newline=""))
    cheek_l = sum(cheek) / 3.0

    # The cut.
    bm = bmesh.new()
    bm.from_mesh(me)
    n = Vector((-pa, -pb, 1.0)).normalized()
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                           plane_co=Vector((cx, cy, pc + off)), plane_no=n, clear_inner=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bm.verts.ensure_lookup_table()
    on = lambda v: abs(v.co.z - plane(v.co.x, v.co.y)) < 2e-4
    # His cut edge: the longest closed chain of open edges on the cut (his neck's cross-section; the beard's
    # cut cards make small chains of their own).
    nb = {}
    for e in bm.edges:
        if e.is_boundary and on(e.verts[0]) and on(e.verts[1]):
            for a, b in ((e.verts[0], e.verts[1]), (e.verts[1], e.verts[0])):
                nb.setdefault(a, []).append(b)
    seen, loops = set(), []
    for v0 in nb:
        if v0 in seen:
            continue
        L, prev, cur = [v0], None, v0
        seen.add(v0)
        while True:
            nxt = [w for w in nb[cur] if w is not prev and w not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            L.append(cur)
        loops.append(L)
    edge = max(loops, key=len)
    closed = edge[0] in nb[edge[-1]]
    print("cut edge: %d points (%s), %d other chains" % (len(edge), "closed" if closed else "OPEN", len(loops) - 1))
    if ang(edge[1].co.x, edge[1].co.y) < ang(edge[0].co.x, edge[0].co.y) and abs(
            ang(edge[1].co.x, edge[1].co.y) - ang(edge[0].co.x, edge[0].co.y)) < math.pi:
        edge.reverse()
    # The neck tube: row 0 on the ring, row ROWS his edge.
    uv_lay = bm.loops.layers.uv.active
    rows = []
    for v in edge:
        t = ang(v.co.x, v.co.y)
        r1 = math.hypot(v.co.x - cx, v.co.y - cy)
        z1 = v.co.z
        r0, z0 = ring_at(t)
        col = []
        for kk in range(ROWS):
            u = kk / ROWS
            h = u * u * (3.0 - 2.0 * u)
            r = r0 + (r1 - r0) * h
            col.append(bm.verts.new((cx + r * math.sin(t), cy - r * math.cos(t), z0 + (z1 - z0) * u)))
        col.append(v)
        rows.append(col)
    tube = []
    m = len(rows)
    for i in range(m if closed else m - 1):
        a, b = rows[i], rows[(i + 1) % m]
        for kk in range(ROWS):
            q = [a[kk], b[kk], b[kk + 1], a[kk + 1]]
            try:
                f = bm.faces.new(q)
            except ValueError:
                continue
            nrm = (q[1].co - q[0].co).cross(q[3].co - q[0].co)
            mid = sum((p.co for p in q), Vector()) / 4.0
            if nrm.dot(Vector((mid.x - cx, mid.y - cy, 0.0))) < 0:
                f.normal_flip()
            f.smooth = True
            tube.append(f)
    tube_v = set(p for col in rows for p in col[:ROWS])
    share = {}
    for col in rows:
        for kk in range(ROWS):
            share[col[kk]] = 1.0 - kk / ROWS
    print("neck tube: %d faces" % len(tube))
    bm.to_mesh(me)
    bm.free()
    me = ob.data
    # Vertex colours: red the body's share, green the body's skin colour.
    colr = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    # Find tube points again by position (to_mesh keeps order: new points come after the old ones).
    nold = len(me.vertices) - len(tube_v)
    uvl = me.uv_layers.active.data
    lum = {}
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            if vi < nold and vi not in lum:
                uu, vv = uvl[li].uv
                i = (min(H - 1, max(0, int(vv * H))) * W + min(W - 1, max(0, int(uu * W)))) * 4
                lum[vi] = (px[i] + px[i + 1] + px[i + 2]) / 3.0
    for i, v in enumerate(me.vertices):
        c = v.co
        if i >= nold:
            continue
        d = c.z - plane(c.x, c.y)
        g = max(0.0, 1.0 - d / FADE) if d < FADE else 0.0
        if g > 0.0 and lum.get(i, cheek_l) < 0.5 * cheek_l:
            g = 0.0
        colr.data[i].color = (0.0, g, 0.0, 1.0)
    # The tube's own points: share from their height between the ring and the cut.
    for i in range(nold, len(me.vertices)):
        c = me.vertices[i].co
        t = ang(c.x, c.y)
        r0, z0 = ring_at(t)
        z1 = plane(c.x, c.y)
        u = (c.z - z0) / max(1e-5, z1 - z0)
        colr.data[i].color = (max(0.0, min(1.0, 1.0 - u)), 1.0, 0.0, 1.0)
    for img in bpy.data.images:
        if img.size[0] > tex_px:
            img.scale(tex_px, tex_px)
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_image_format="JPEG",
                              export_jpeg_quality=90, export_yup=True, export_vertex_color="ACTIVE",
                              export_all_vertex_colors=False)
    print("OUT", out, "tris", sum(len(p.vertices) - 2 for p in me.polygons))


a = sys.argv[sys.argv.index("--") + 1:]
if a[0] == "--all":
    for f in sorted(os.listdir(a[1])):
        if f.endswith(".glb"):
            print("HEAD", f)
            fit(os.path.join(a[1], f), os.path.join(a[2], f), a[3], int(a[4]) if len(a) > 4 else 2048)
else:
    fit(a[0], a[1], a[2], int(a[3]) if len(a) > 3 else 2048)
