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
BAND = float(os.environ.get("BAND", "0.06"))  # the shape band: his neck eases onto the socket over 6 cm (director 2026-11-19, "Yes, every head": over 2 cm it left a crease)
SKIN_BAND = float(os.environ.get("SKIN_BAND", "0.02"))  # the colour join: his skin turns to the body's over the bottom 2 cm only (the back of it is hair)
# Per head, from the director's eye (2026-11-17, Gawn: "shrink it slightly and add some neck"):
# HEAD_SCALE shrinks or grows the head, NECK (metres) lifts it and adds that much neck above the socket.
HEAD_SCALE = float(os.environ.get("HEAD_SCALE", "0.9"))
NECK = float(os.environ.get("NECK", "0.035"))
# A head's own size or lift, where the director picked one (heads.json "scale": Pickett 0.8, 2026-11-18).


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


def hair_points(me):
    """The points whose texture is under half as bright as his neck skin (the back of his neck, the 4 cm
    above his mesh's bottom; the brighter quarter's edge, so the hair over it does not count)."""
    img = next((i for i in bpy.data.images if i.size[0] > 0), None)
    if img is None:
        return set()
    w, h = img.size
    px = img.pixels[:]
    uv = me.uv_layers.active.data
    lum = {}
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            if vi not in lum:
                uu, vv = uv[li].uv
                i = (min(h - 1, max(0, int(vv * h))) * w + min(w - 1, max(0, int(uu * w)))) * 4
                lum[vi] = (px[i] + px[i + 1] + px[i + 2]) / 3.0
    lo = min(v.co.z for v in me.vertices)
    neck = sorted(lum[v.index] for v in me.vertices if v.index in lum and lo < v.co.z < lo + 0.04 and v.co.y > 0.0)
    if not neck:
        return set()
    ref = neck[len(neck) * 3 // 4]
    # Behind his ears only: at his front the dark over the band is a beard, which takes the skin (Gawn).
    out = set(i for i, l in lum.items() if l < 0.5 * ref and me.vertices[i].co.y > 0.0)
    print("hair over the join: neck skin %.2f, %d points darker than half of it" % (ref, len(out)))
    return out


def fit(src, out, socket, tex_px):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    ob = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
    for o in bpy.context.scene.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # MEASURE (a MetaHuman head conformed to his Tripo scan, row 202 2d): the size and place come from the
    # scan, in the same space, exactly as the scan alone would be fitted; the MetaHuman head is what moves.
    meas = ob
    if os.environ.get("MEASURE"):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.environ["MEASURE"])
        meas = [o for o in bpy.data.objects if o not in before and o.type == "MESH"][0]
        meas.parent = None
        meas.data.transform(meas.matrix_world)
        meas.matrix_world = Matrix()
    tip, eye_y = eye_line(meas)
    # Blender z up = glTF y; Blender -y = glTF +z.
    co = [v.co.copy() for v in meas.data.vertices]
    # His depth measured on his surface, not his points (a head with few points at the back of the skull
    # read far too shallow, Cross 2026-11-18): lines fired at him from the front and from behind, across
    # 3 cm and 2 cm either side of the eye line; the front-most hit less the back-most.
    from mathutils.bvhtree import BVHTree
    hh = max(c.z for c in co) - min(c.z for c in co)
    bvh = BVHTree.FromPolygons([c.copy() for c in co], [p.vertices[:] for p in meas.data.polygons])
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
    if meas is not ob:  # the scan and its texture go, so his own texture is the one read below
        imgs = {n.image for m in meas.data.materials if m and m.node_tree for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image}
        bpy.data.objects.remove(meas, do_unlink=True)
        for i in imgs:
            bpy.data.images.remove(i)
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
    pid =os.path.splitext(os.path.basename(out))[0]
    hj = os.path.join(os.path.dirname(out), "heads.json")
    info = json.load(open(hj)) if os.path.exists(hj) else {}
    s = HEAD_DEPTH / depth * float(info.get(pid, {}).get("scale", HEAD_SCALE))
    print("nose tip", tip, "eye line", eye_y, "depth", depth, "scale", s)
    ob.data.transform(Matrix.Translation(Vector((0.0, -MH_Z, EYE_FIT + NECK))) @ Matrix.Scale(s, 4)
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
    off = float(os.environ.get("OFF", "0.0"))  # TRIAL; the cut runs on the socket's own line, just under his jaw
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
    # (No subdividing of his low neck: cutting the long edges there also cut up his beard's cards, whose
    # pieces then caught the light as dark shards.)
    bm.to_mesh(ob.data)
    bm.free()
    me = ob.data
    # Matched loops (TRIAL, director 2026-11-20 "try one, if it doesnt work try the other"): his neck's
    # bottom edge is centred on the socket ring before it is matched round the neck, so an off-centre neck
    # is moved over, not squeezed on one side. The move fades out up the band.
    if os.environ.get("MATCH"):
        lowv = [v.co for v in me.vertices if v.co.z - (plane(v.co.x, v.co.y) + off) < 0.005]
        ex = sum(c.x for c in lowv) / len(lowv)
        ey = sum(c.y for c in lowv) / len(lowv)
        print("neck edge off the ring centre: %.1f cm sideways, %.1f cm fore-aft" % (100 * (ex - cx), 100 * (ey - cy)))
        for v in me.vertices:
            u = v.co.z - (plane(v.co.x, v.co.y) + off)
            if u < BAND:
                w = max(0.0, min(1.0, 1.0 - u / BAND))
                w = w * w * (3.0 - 2.0 * w)
                v.co.x += w * (cx - ex)
                v.co.y += w * (cy - ey)
    # His neck's bottom edge, in 5-degree steps round the neck: how high it stands over the cut and its
    # radius there. Mostly it is the cut itself, but where his mesh is open below (Gawn's throat, under his
    # beard, 2 cm short of the socket) it is the lowest skin he has, and that is what goes onto the socket.
    # Sampled along every edge, not only at the corners, so a long triangle across a step still counts.
    # His skin only: the largest piece of the mesh, joined across its texture seams (glTF splits points
    # there). The beard's loose strands are separate pieces and hang lower than his throat skin.
    key = {}
    for v in me.vertices:
        key.setdefault((round(v.co.x, 5), round(v.co.y, 5), round(v.co.z, 5)), []).append(v.index)
    par = list(range(len(me.vertices)))

    def root(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for ids in key.values():
        for i in ids[1:]:
            par[root(i)] = root(ids[0])
    for e in me.edges:
        par[root(e.vertices[0])] = root(e.vertices[1])
    size = {}
    for i in range(len(par)):
        size[root(i)] = size.get(root(i), 0) + 1
    big = max(size, key=size.get)
    print("skin: %d of %d points in the largest piece, %d pieces" % (size[big], len(par), len(size)))
    low = {}
    for e in me.edges:
        if root(e.vertices[0]) != big:
            continue
        a0, a1 = me.vertices[e.vertices[0]].co, me.vertices[e.vertices[1]].co
        for i in range(9):
            c = a0.lerp(a1, i / 8.0)
            k = int(math.degrees(ang(c.x, c.y)) // 5) % 72
            u = c.z - (plane(c.x, c.y) + off)
            low.setdefault(k, []).append((u, math.hypot(c.x - cx, c.y - cy)))
    if os.environ.get("FIT_DEBUG"):
        for k in (70, 71, 0, 1, 2, 3, 6, 12):
            x = sorted(low.get(k, []))[:400:25]
            print("LOW %3d deg: " % (5 * k) + " ".join("%.1f/%.1f" % (100 * u, 100 * r) for u, r in x))
    lu, er = {}, {}
    for k, x in low.items():
        m = min(u for u, r in x)
        near = [r for u, r in x if u < m + 0.003]
        lu[k] = m
        er[k] = sum(near) / len(near)
    print("lowest skin: %d of 72 steps, %d stand over 5 mm above the cut: %s" % (
        len(lu), sum(1 for m in lu.values() if m > 0.005),
        ", ".join("%d deg %.1f cm" % (5 * k, 100 * m) for k, m in sorted(lu.items()) if m > 0.005)))

    def step(t, table):  # the table's value at angle t, between its two nearest 5-degree steps
        d = math.degrees(t) / 5.0 - 0.5
        k0 = int(math.floor(d))

        def at(k):
            for dd in range(36):
                for kk in ((k + dd) % 72, (k - dd) % 72):
                    if kk in table:
                        return table[kk]
            return 0.0
        w = d - k0
        return at(k0 % 72) * (1.0 - w) + at((k0 + 1) % 72) * w

    def edge_r(t):
        return step(t, er) or 0.06

    if os.environ.get("FIT_DEBUG"):
        for deg in range(0, 360, 20):
            t = math.radians(deg)
            rr, rz = ring_at(t)
            print("DBG %3d ring r %.4f z %.4f plane %.4f edge r %.4f" % (
                deg, rr, rz, plane(cx + rr * math.sin(t), cy - rr * math.cos(t)), edge_r(t)))
    # His mesh's open bottom edge itself: the edges with a face on one side only (points joined across
    # texture seams), in the one chain of them that runs along the cut. Every point of it goes exactly
    # onto the socket ring, so the edge closes on the socket with no gap anywhere round his neck.
    pos = {}
    for v in me.vertices:
        pos.setdefault((round(v.co.x, 5), round(v.co.y, 5), round(v.co.z, 5)), v.index)
    mid = [pos[(round(v.co.x, 5), round(v.co.y, 5), round(v.co.z, 5))] for v in me.vertices]
    faces_on = {}
    for f in me.polygons:
        vs = [mid[i] for i in f.vertices]
        for i in range(len(vs)):
            e = tuple(sorted((vs[i], vs[(i + 1) % len(vs)])))
            faces_on[e] = faces_on.get(e, 0) + 1
    nb = {}
    for (a, b), n in faces_on.items():
        if n == 1:
            nb.setdefault(a, []).append(b)
            nb.setdefault(b, []).append(a)
    on_cut = [i for i in nb if abs(me.vertices[i].co.z - (plane(me.vertices[i].co.x, me.vertices[i].co.y) + off)) < 1e-4]
    rim_m = set()
    todo = on_cut[:]
    while todo:
        i = todo.pop()
        if i in rim_m:
            continue
        rim_m.add(i)
        todo += nb[i]
    rim = set(v.index for v in me.vertices if mid[v.index] in rim_m)
    print("bottom edge: %d points, %d of them above the cut" % (len(rim_m), sum(
        1 for i in rim_m if me.vertices[i].co.z - (plane(me.vertices[i].co.x, me.vertices[i].co.y) + off) > 0.002)))
    # The band: from the cut edge (share 1) to 2 cm up (0). Each point moves down by the gap between the
    # cut and the socket at its angle, and in or out by the ring's radius over his neck's, by its share.
    share = [0.0] * len(me.vertices)
    skin = [0.0] * len(me.vertices)
    # Hair hanging over the join (Langford's nape: the back of his curls ends in points that reach the
    # band) keeps its own colour: a point whose texture is under half as bright as his own neck skin is
    # hair, not skin, so the band moves it but never paints it skin (painted, it showed as a pale flap).
    dark = hair_points(me)
    if os.environ.get("HDBG"):
        for lo_, hi_ in ((0.0, 0.01), (0.04, 0.05), (0.08, 0.09), (0.12, 0.13)):
            q = [w_.co for w_ in me.vertices if lo_ <= w_.co.z - (plane(w_.co.x, w_.co.y) + off) < hi_]
            if q: print("NECK %2d cm up: centre %.1f, %.1f cm off the ring; x %.1f..%.1f" % (100*lo_, 100*(sum(c.x for c in q)/len(q)-cx), 100*(sum(c.y for c in q)/len(q)-cy), 100*(min(c.x for c in q)-cx), 100*(max(c.x for c in q)-cx)))
    rs, hs = [], []
    HB = {}
    for v in me.vertices:
        c = v.co
        lo = step(ang(c.x, c.y), lu)
        if v.index in rim:
            lo = c.z - (plane(c.x, c.y) + off)
        pz = plane(c.x, c.y) + off + lo
        u = c.z - pz
        if u >= BAND:
            continue
        t = ang(c.x, c.y)
        w = max(0.0, min(1.0, 1.0 - u / BAND))
        w = w * w * (3.0 - 2.0 * w)
        rr, rz = ring_at(t)
        r = math.hypot(c.x - cx, c.y - cy)
        # In to the socket's width over the band's bottom 60% first, so his throat rises straight up from
        # the collar and turns out only under his jaw (director 2026-11-17: the throat sagged, coming out
        # diagonally instead of upwards).
        wr = min(1.0, w / 0.6)
        f = 1.0 + wr * (rr / max(1e-4, edge_r(t)) - 1.0)
        if v.index in rim:
            f = rr / max(1e-4, r)
        rs.append(rr / max(1e-4, edge_r(t)))
        c.x = cx + (c.x - cx) * f
        c.y = cy + (c.y - cy) * f
        c.z += w * (rz - pz)
        hs.append(rz - pz)
        if os.environ.get("HDBG"): HB.setdefault(int(math.degrees(t)) // 20 * 20, []).append((rz - pz, u, f))
        if v.index in dark:
            continue
        share[v.index] = w
        # His skin colour over the band's bottom 70%, his own texture fading in over its top 30%: the band
        # is stretched up to three times its height onto the socket, and at his throat it is beard.
        # Over SKIN_BAND his texture fades smoothly to skin, the way stubble and the scan's under-jaw shadow
        # thin out down a real neck (director 2026-11-20, "just hide the seam": over 2 cm it showed as a line
        # from his chin to behind his ear).
        ws = max(0.0, min(1.0, 1.0 - u / SKIN_BAND))
        skin[v.index] = ws * ws * (3.0 - 2.0 * ws)
    for k in sorted(HB):
        print("HB %3d deg move %.1f..%.1f cm, squeeze x%.2f..%.2f" % (k, 100*min(h for h,_,_ in HB[k]), 100*max(h for h,_,_ in HB[k]), min(f for _,_,f in HB[k]), max(f for _,_,f in HB[k])))
    if rs:
        print("neck to socket: radius x%.2f-%.2f, height %.1f to %.1f cm" % (
            min(rs), max(rs), 100 * min(hs), 100 * max(hs)))
        # Out of line with a clean fit: his neck squeezed or spread by over a quarter, or stretched over
        # 4 cm onto the ring. Printed for the batch report; the head is still written.
        bad = []
        if min(rs) < 0.75 or max(rs) > 1.25:
            bad.append("neck width x%.2f-%.2f" % (min(rs), max(rs)))
        if max(abs(h) for h in hs) > 0.04:
            bad.append("neck stretched %.1f cm" % (100 * max(abs(h) for h in hs)))
        print("CHECK %s scale %.3f %s" % (pid, s, "ok" if not bad else "LOOK: " + ", ".join(bad)))
    # The share in the vertex colour's red, the skin colour's blend in its green.
    col = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    for i, w in enumerate(share):
        col.data[i].color = (w, skin[i], 0.0, 1.0)
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
                hexc = "#%02x%02x%02x" % tuple(round(255 * acc[j] / k) for j in range(3))
                print("SKIN %s %s from %d" % (name, hexc, k))
                if name == "cheek":
                    # The body's neck wears his cheek's colour: always clear skin (under the back of
                    # the neck is often hair or shadow).
                    info.setdefault(pid, {})["skin"] = hexc
                    json.dump(info, open(hj, "w", newline=""))
    for img in bpy.data.images:
        if img.size[0] > tex_px:
            img.scale(tex_px, tex_px)
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_image_format="JPEG",
                              export_jpeg_quality=90, export_yup=True, export_vertex_color="ACTIVE",
                              export_all_vertex_colors=False)
    print("OUT", out, "tris", sum(len(p.vertices) - 2 for p in me.polygons))


a = sys.argv[sys.argv.index("--") + 1:] if __name__ == "__main__" else [None]
if a[0] is None:
    pass
elif a[0] == "--all":
    src_dir, out_dir, socket = a[1], a[2], a[3]
    px = int(a[4]) if len(a) > 4 else 2048
    for f in sorted(os.listdir(src_dir)):
        if f.endswith(".glb"):
            print("HEAD", f)
            fit(os.path.join(src_dir, f), os.path.join(out_dir, f), socket, px)
else:
    fit(a[0], a[1], a[2], int(a[3]) if len(a) > 3 else 2048)
