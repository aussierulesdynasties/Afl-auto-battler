"""Fit hairpieces made in Tripo Studio (one GLB per cut) to our footballer's head and export them
for the 3D oval: one GLB, one mesh per cut on the head bone, plus a greyed texture per cut.

blender --background --python export_tripo_hair_glb.py -- BODY_TYPES.json TYPE OUT.glb TEX_DIR [VIEW_DIR] STYLE=CUT.glb [...]

A Tripo hairpiece has no head of its own. It is either a wig (a closed shell of hair over a cap,
open underneath, sometimes on a stand) or one solid with a mannequin's head, scaled to about
1 unit and facing +X. The fit is measured, not searched:
- a wig's cavity (the cap's inside), or a solid's outer face, is measured by horizontal rays over
  a band below its top: widest left-right and front-back;
- his skull is measured the same way over the same band (BAND m below his crown, above the ears);
- a per-axis scale matches the two, and the tops and middles line up.
Then the stand, the cap's inside, mannequin plastic and cap lace (pale, colourless texels) and
loose bits below the ears go; hair that dips into his skull is pushed out to just above the skin.
Decimated to ARD_HAIR_TRIS. Its colour texture is greyed by luminance rank (as grey_hair_tex.py)
to TEX_DIR/STYLE.png, so Oval3D can tint it any hair colour.
VIEW_DIR: also render each fitted cut on the body, front, side and back (Workbench), for checking.
"""
import json, math, os, sys, time
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

PIPE = os.environ.get("ARD_PIPELINE_BLENDER", os.path.join(os.path.dirname(__file__), "..", "..", "..", "ard-asset-pipeline", "tools", "blender"))
sys.path.insert(0, PIPE)
import ard_body

TRIS = int(os.environ.get("ARD_HAIR_TRIS", "5000"))
TEX = 512
LOW = 0.70          # the darkest strand after greying: Tripo textures are noisy, so a narrow range
CRANIUM = 0.12      # m below the crown: where his head's middle is found
BAND = float(os.environ.get("ARD_HAIR_BAND", "0.09"))   # m below the crown: the skull above the ears
STEP = 0.004        # m between measured levels (his scale)
NEAR = 0.012        # m: a face looking at his skin this close to it is the cap's inside
BLUR = 2            # box-blur passes over the greyed texture
GROW = 4            # texels the islands grow into the uncovered ground
SPLITS = int(os.environ.get("ARD_HAIR_SPLITS", "2"))   # rounds of splitting faces that still dip
FACE = 0.055        # m either side of his nose: his eyes and cheeks, kept clear of hair
BROW = 0.085        # m below his crown: his brows; hair inside his face below them is cut
SKULL = 0.09        # m: his skull's radius, for how far a flat face sags inside it
SKIN = 0.002        # m: hair is kept at least this far off his skin
SOLID_OFF = 0.004   # m: a solid piece's outer face (hair painted on a mannequin) sits this far off his skull
WELD = 5e-5         # m: vertices this close are one (seam splits)
LOOSE = 40          # faces: a loose island smaller than this is a crumb
STRAY = float(os.environ.get("ARD_HAIR_STRAY", "0.0"))   # an island under this share of the biggest is a stray
UNDER = 0.001       # m: the under-layer (his scalp in hair colour) sits this far off his skin
UNDER_REACH = 0.045 # m: his scalp gets the under-layer where hair lies within this of it
PALE = float(os.environ.get("ARD_HAIR_PALE", "0.5"))    # brighter than this and colourless: plastic or lace

t0 = time.time()
argv = sys.argv[sys.argv.index("--") + 1:]
presets, body_type, out, tex_dir = json.load(open(argv[0])), argv[1], argv[2], argv[3]
rest = argv[4:]
view_dir = None
if rest and "=" not in rest[0]:
    view_dir, rest = rest[0], rest[1:]
cuts = []
for a in rest:
    style, path = a.split("=", 1)
    path, *kv = path.split("|")                 # STYLE=CUT.glb|off=0.02: a solid's hair depth (m)
    cuts.append((style, path, {k: float(v) for k, v in (x.split("=") for x in kv)}))
os.makedirs(tex_dir, exist_ok=True)

bpy.ops.wm.read_homefile(use_empty=True)
basemesh, rig = ard_body.build_body(body_type, presets[body_type]["macros"], targets=presets[body_type].get("targets"))
dg = bpy.context.evaluated_depsgraph_get()
body = BVHTree.FromObject(basemesh, dg)
bw = [basemesh.matrix_world @ v.co for v in basemesh.data.vertices]
our_top = max(v.z for v in bw)
near = [v for v in bw if v.z > our_top - CRANIUM]
cx = sorted(v.x for v in near)[len(near) // 2]
near = [v for v in near if abs(v.x - cx) < 0.15]
lo = Vector((min(v.x for v in near), min(v.y for v in near)))
hi = Vector((max(v.x for v in near), max(v.y for v in near)))
our_c = (lo + hi) / 2
mine = set(bpy.data.objects)


def hits(bvh, o, d, far=3.0):
    """Every surface along the ray: [(point, normal, distance)]."""
    out, start, gone = [], o.copy(), 0.0
    while gone < far and len(out) < 64:
        loc, nrm, _, dist = bvh.ray_cast(start, d, far - gone)
        if loc is None:
            break
        gone += dist + 1e-4
        out.append((loc, nrm, gone))
        start = loc + d * 1e-4
    return out


def inner(bvh, o, d, skip=0.0):
    """The first surface along the ray, past skip, that faces back at o: the cap's inside, seen
    from the cavity."""
    for loc, nrm, dist in hits(bvh, o, d):
        if dist > skip and nrm.dot(d) < 0:
            return loc
    return None


def profile(bvh, cx, cy, ztop, depth, step, solid, skip=0.0):
    """[(z, left, right, front, back)] of a head surface at levels from ztop down: horizontal rays
    out from its middle, to the cap's inside (a wig; past `skip`, a stand's radius) or to where
    they leave the solid. An end is None where the ray finds nothing (an open face)."""
    rows = []
    z = ztop - step
    while z > ztop - depth:
        o = Vector((cx, cy, z))
        ends = []
        for d in (Vector((-1, 0, 0)), Vector((1, 0, 0)), Vector((0, -1, 0)), Vector((0, 1, 0))):
            ends.append(bvh.ray_cast(o, d)[0] if solid else inner(bvh, o, d, skip))
        rows.append((z, ends[0] and ends[0].x, ends[1] and ends[1].x, ends[2] and ends[2].y, ends[3] and ends[3].y))
        z -= step
    return rows


def measure(rows):
    """Widest left-right (with its middle), deepest front-back, the back of the head, and how many
    levels found a front."""
    lr = [r for r in rows if r[1] is not None and r[2] is not None]
    fb = [r for r in rows if r[3] is not None and r[4] is not None]
    if not lr or not [r for r in rows if r[4] is not None]:
        return None
    wide = max(lr, key=lambda r: r[2] - r[1])
    deep = max(fb, key=lambda r: r[4] - r[3])[4] - max(fb, key=lambda r: r[4] - r[3])[3] if fb else None
    back = max(r[4] for r in rows if r[4] is not None)
    return wide[2] - wide[1], (wide[1] + wide[2]) / 2, deep, back, len(fb)


OUR = profile(body, our_c.x, our_c.y, our_top, BAND, STEP, True)
OW, OX, OD, OB, _ = measure(OUR)
print(f"OUR head: crown {our_top:.3f}, over {BAND} m: width {OW:.3f} depth {OD:.3f} back {OB:.3f} middle x {OX:.3f}")
HEAD = Vector((OX, OB - OD / 2, our_top - 0.08))   # inside his skull: hair faces away from here


def ceiling(bvh, top, cxy, w):
    """The cap's inside at the crown: down rays on a ring round the middle (a stand may fill the
    middle), each to the first face looking down. None when most find none: a solid piece."""
    zs = []
    for k in range(9):
        r = 0.0 if k == 0 else 0.08 * w
        o = Vector((cxy.x + r * math.cos(k * math.pi / 4), cxy.y + r * math.sin(k * math.pi / 4), top + 0.1))
        for loc, nrm, dist in hits(bvh, o, Vector((0, 0, -1))):
            if nrm.z < -0.2:
                if loc.z > top - 0.3 * w:
                    zs.append(loc.z)
                break
    return sorted(zs)[len(zs) // 2] if len(zs) >= 5 else None


def stand(ob, top, w):
    """A stand's post: the piece's lowest tenth is narrow. Its middle, or None."""
    low = [v.co for v in ob.data.vertices if v.co.z < 0.12 * top]
    if len(low) < 20:
        return None
    if max(v.x for v in low) - min(v.x for v in low) > 0.2 * w or max(v.y for v in low) - min(v.y for v in low) > 0.2 * w:
        return None
    return Vector((sum(v.x for v in low) / len(low), sum(v.y for v in low) / len(low)))


def fit(bvh, top, cxy, w, post, off):
    """Scale and shift from measurement (see the module note): the width sets the scale; the depth
    may differ by up to 12% where the piece has a front; tops, left-right middles and backs line up.
    Returns scale, shift, solid, the piece's measured top."""
    o = post if post is not None else cxy
    ceil = ceiling(bvh, top, o, w)
    solid = ceil is None
    z0 = top if solid else ceil
    skip = 0.08 * w if post is not None else 0.0
    s, m = OW / (0.6 * w), None
    for _ in range(5):
        m = measure(profile(bvh, o.x, o.y, z0, BAND / s, STEP / s, solid, skip))
        if m is None:
            return None, None, solid, z0
        s = OW / m[0]
    mw, mx, md, mb, nfront = m
    n = int(BAND / STEP)
    sy = OD / md if (md and nfront >= n // 2) else s
    sy = min(max(sy, s * 0.88), s * 1.12)
    t = Vector((OX - mx * s, OB - mb * sy, our_top + off - z0 * s))
    print(f"  {'solid' if solid else 'wig'}{' on a stand' if post is not None else ''}: top {z0:.3f}, "
          f"width {mw:.3f} depth {md if md is None else round(md, 3)} ({nfront}/{n} levels with a front)")
    return Vector((s, sy, s)), t, solid, z0


def grey(img, ob):
    """The colour texture greyed by luminance rank over the faces kept, TEX px, as STYLE.png."""
    img.scale(TEX, TEX)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(TEX, TEX, 4)
    lum = 0.2126 * px[..., 0] + 0.7152 * px[..., 1] + 0.0722 * px[..., 2]
    uv = ob.data.uv_layers.active.data
    idx = []
    for poly in ob.data.polygons:
        us = [uv[i].uv for i in poly.loop_indices]
        for u in us + [sum(us, Vector((0, 0))) / len(us)]:
            idx.append((min(TEX - 1, max(0, int(u.y * TEX))), min(TEX - 1, max(0, int(u.x * TEX)))))
    idx = np.array(idx)
    samples = lum[idx[:, 0], idx[:, 1]]
    q = np.sort(samples)
    rank = np.searchsorted(q, lum, side="left") / max(1, len(q))
    g = LOW + (1.0 - LOW) * np.clip(rank, 0, 1)
    # Tripo packs the texture as small islands on a white ground. Texels the kept faces never cover
    # take the hair's middle grey, and the islands grow a few texels into them, so filtering and
    # mipmaps at an island's edge read hair, not white specks.
    cover = np.zeros((TEX, TEX), dtype=bool)
    ob.data.calc_loop_triangles()
    for tri in ob.data.loop_triangles:
        a2, b2, c2 = (np.array(uv[i].uv) * TEX for i in tri.loops)
        x0, y0 = np.floor(np.minimum(np.minimum(a2, b2), c2)).astype(int) - 1
        x1, y1 = np.ceil(np.maximum(np.maximum(a2, b2), c2)).astype(int) + 1
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, TEX), min(y1, TEX)
        if x1 <= x0 or y1 <= y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        d = (b2[1] - c2[1]) * (a2[0] - c2[0]) + (c2[0] - b2[0]) * (a2[1] - c2[1])
        if abs(d) < 1e-9:
            continue
        l1 = ((b2[1] - c2[1]) * (xs - c2[0]) + (c2[0] - b2[0]) * (ys - c2[1])) / d
        l2 = ((c2[1] - a2[1]) * (xs - c2[0]) + (a2[0] - c2[0]) * (ys - c2[1])) / d
        e = 0.03                                  # a little slack round each triangle (its own units)
        cover[y0:y1, x0:x1] |= (l1 > -e) & (l2 > -e) & (1 - l1 - l2 > -e)
    g = np.where(cover, g, np.median(g[cover]) if cover.any() else 0.7)
    for _ in range(GROW):
        acc = np.zeros_like(g); n = np.zeros_like(g)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            acc += np.roll(np.where(cover, g, 0), (dy, dx), (0, 1)); n += np.roll(cover, (dy, dx), (0, 1))
        grow = ~cover & (n > 0)
        g = np.where(grow, acc / np.maximum(n, 1), g)
        cover |= grow
    # Tripo's hair texture is high-contrast noise; at the size the game draws a head it reads as
    # specks of dirt, so it is softened: two box-blur passes.
    for _ in range(BLUR):
        g = sum(np.roll(g, (dy, dx), (0, 1)) for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9.0
    outp = np.stack([g, g, g, np.ones_like(g)], axis=-1).astype(np.float32)
    im = bpy.data.images.new("grey", TEX, TEX, alpha=True)
    im.pixels = outp.ravel()
    return im, float(np.mean(lum[idx[:, 0], idx[:, 1]]))


def looks_at_him(hair, c, n):
    """The cap's inside looks straight at his skin; a crevice between the outside's clumps looks
    at more hair first. True when a ray along the face's normal reaches his skin before any hair."""
    o = c + n * 1e-4
    sk = body.ray_cast(o, n, 0.05)
    if sk[0] is None:
        return False
    hh = hair.ray_cast(o, n, sk[3])
    return hh[0] is None


def islands(bm):
    bm.faces.ensure_lookup_table()
    seen, out = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, isl = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            isl.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        out.append(isl)
    return out


made = []
for style, path, opts in cuts:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    ob = next(o for o in new if o.type == "MESH")
    ob.data.transform(ob.matrix_world)
    ob.parent = None
    ob.matrix_world = Matrix.Identity(4)
    ob.data.transform(Matrix.Rotation(math.radians(-90), 4, "Z"))   # faces +X -> faces -Y, as he does
    for o in new:
        if o is not ob:
            bpy.data.objects.remove(o, do_unlink=True)
    img = next((n.image for m in ob.data.materials if m and m.use_nodes for n in m.node_tree.nodes
                if n.type == "TEX_IMAGE" and n.image and n.outputs[0].links
                and any(l.to_socket.name == "Base Color" for l in n.outputs[0].links)), None)
    vs = [v.co for v in ob.data.vertices]
    top = max(v.z for v in vs)
    w = max(max(v.x for v in vs) - min(v.x for v in vs), max(v.y for v in vs) - min(v.y for v in vs))
    cxy = Vector(((max(v.x for v in vs) + min(v.x for v in vs)) / 2, (max(v.y for v in vs) + min(v.y for v in vs)) / 2))
    bvh = BVHTree.FromObject(ob, dg)
    post = stand(ob, top, w)
    s, t, solid, z0 = fit(bvh, top, cxy, w, post, opts.get("off", SOLID_OFF) if ceiling(bvh, top, post or cxy, w) is None else opts.get("off", 0.0))
    if s is None:
        raise SystemExit(f"{style}: no head surface found under the hair")
    # A stand: a thin post up the middle, under the cap.
    pole = set() if post is None else set(i for i, v in enumerate(ob.data.vertices)
               if math.hypot(v.co.x - post.x, v.co.y - post.y) < 0.08 * w and v.co.z < z0 - 0.03 * w)
    plastic = None
    if img and (solid or opts.get("pale")):     # a mannequin; or lace, where a wig's cap shows it
        small = img.copy()
        small.scale(1024, 1024)
        px = np.array(small.pixels[:], dtype=np.float32).reshape(1024, 1024, 4)[..., :3]
        mx, mn = px.max(axis=-1), px.min(axis=-1)
        plastic = (mx > PALE) & ((mx - mn) < 0.10 * mx + 0.02)
        bpy.data.images.remove(small)
    for v in ob.data.vertices:
        v.co = Vector((v.co.x * s.x + t.x, v.co.y * s.y + t.y, v.co.z * s.z + t.z))
    ob.data.update()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    uvl = bm.loops.layers.uv.active
    brow_z = our_top - BROW
    front = [f for f in bm.faces if f.calc_center_median().y < HEAD.y - 0.02
             and min(v.co.z for v in f.verts) < brow_z < max(v.co.z for v in f.verts)]
    if front:
        es = list({e for f in front for e in f.edges})
        vs = list({v for f in front for v in f.verts})
        bmesh.ops.bisect_plane(bm, geom=front + es + vs, plane_co=Vector((0, 0, brow_z)), plane_no=Vector((0, 0, 1)))
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
        bm.normal_update()
    kill, n_pole, n_cap, n_pale, n_face = [], 0, 0, 0, 0
    bm.faces.ensure_lookup_table()
    hair = BVHTree.FromBMesh(bm)
    for f in bm.faces:
        if all(v.index in pole for v in f.verts):
            kill.append(f); n_pole += 1
            continue
        c = f.calc_center_median()
        q, nrm, _, dist = body.find_nearest(c)
        if f.normal.dot(c - HEAD) < 0 and ((c - q).dot(nrm) < 0 or (dist < NEAR and looks_at_him(hair, c, f.normal))):
            kill.append(f); n_cap += 1          # the cap's inside, looking at him
            continue
        if c.z < brow_z and c.y < HEAD.y - 0.02 and ((c - q).dot(nrm) < SKIN or abs(c.x - OX) < FACE):
            kill.append(f); n_face += 1         # a fringe over his face below the brows: it would mask his eyes
            continue
        if plastic is not None:
            u = sum((l[uvl].uv for l in f.loops), Vector((0, 0))) / len(f.loops)
            if plastic[min(1023, max(0, int(u.y * 1024))), min(1023, max(0, int(u.x * 1024)))]:
                kill.append(f); n_pale += 1
    n_all = len(bm.faces)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    # Tripo splits every vertex along its UV seams; weld them (UVs live on the corners) so the
    # decimator and the island pass see one surface, not thousands of seam-cut patches.
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=WELD)
    # Loose islands: keep those reaching above his ears and big enough to be hair.
    ear = our_top - 0.13
    drop = []
    isls = islands(bm)
    big = max(len(i) for i in isls) if isls else 0
    for isl in isls:
        if max(v.co.z for g in isl for v in g.verts) < ear or len(isl) < max(LOOSE, opts.get("stray", STRAY) * big):
            drop.extend(isl)
    bmesh.ops.delete(bm, geom=drop, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()
    n0 = len(ob.data.polygons)
    if not n0:
        raise SystemExit(f"{style}: nothing left after the cut (scale {tuple(s)})")
    tris = int(opts.get("tris", TRIS))
    if n0 > tris:
        bpy.context.view_layer.objects.active = ob
        dec = ob.modifiers.new("decimate", "DECIMATE")
        dec.ratio = tris / n0
        bpy.ops.object.modifier_apply(modifier=dec.name)
    # Hair that dips into his skull (his head is not the wig's, and decimating moves the surface)
    # is pushed out to just above the skin. Last, so nothing moves it back in.
    # A decimated face is flat: over his round skull a big one sags in between its corners (a 5 cm
    # face, 3 mm). So each corner near the skin stands off by SKIN plus the sag of its longest edge,
    # L^2 / 8R over a skull of radius SKULL; twice, as neighbours move.
    me = ob.data
    longest = [0.0] * len(me.vertices)
    for e in me.edges:
        a_, b_ = e.vertices
        L = (me.vertices[a_].co - me.vertices[b_].co).length
        longest[a_] = max(longest[a_], L)
        longest[b_] = max(longest[b_], L)
    pushed = 0
    for _ in range(2):
        for v in me.vertices:
            q, nrm, _, _ = body.find_nearest(v.co)
            want = SKIN + longest[v.index] ** 2 / (8 * SKULL)
            if (v.co - q).dot(nrm) < want:
                v.co = q + nrm * want
                pushed += 1
    me.update()
    # What still dips (a thin sliver, a fold) is split once or twice and its new corners pushed.
    bm = bmesh.new()
    bm.from_mesh(me)
    split = 0
    for _ in range(SPLITS):
        sag = set()
        for f in bm.faces:
            q, nrm, _, _ = body.find_nearest(f.calc_center_median())
            if (f.calc_center_median() - q).dot(nrm) < 0:
                sag.update(f.edges)
        if not sag:
            break
        split += len(sag)
        new = bmesh.ops.subdivide_edges(bm, edges=list(sag), cuts=1, use_grid_fill=True)["geom_inner"]
        for v in [g for g in new if isinstance(g, bmesh.types.BMVert)]:
            q, nrm, _, _ = body.find_nearest(v.co)
            if (v.co - q).dot(nrm) < SKIN:
                v.co = q + nrm * SKIN
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    while len(ob.data.uv_layers) > 1:
        ob.data.uv_layers.remove(ob.data.uv_layers[1])
    n_under = 0
    if not opts.get("nounder"):
        hb = BVHTree.FromPolygons([v.co for v in me.vertices], [p.vertices[:] for p in me.polygons])
        bme = basemesh.evaluated_get(dg).to_mesh()
        keep = {}
        for v in bme.vertices:
            if v.co.z < our_top - 0.2 or (v.co.y < HEAD.y - 0.02 and v.co.z < our_top - BROW + 0.025):
                continue                        # below his crown's dome, or his forehead under a fringe
            o = v.co + v.normal * 1e-4
            if hb.ray_cast(o, v.normal, UNDER_REACH)[0] is not None:
                keep[v.index] = v.co + v.normal * UNDER
        # A gap between clumps lets a ray through: fill a point most of whose neighbours are
        # covered (a hole), never one on the edge of the hair (about half are).
        ring = {}
        for e in bme.edges:
            a_, b_ = e.vertices
            ring.setdefault(a_, []).append(b_)
            ring.setdefault(b_, []).append(a_)
        for _ in range(4):
            add = [i for i, nb in ring.items() if i not in keep and bme.vertices[i].co.z > our_top - 0.2
                   and sum(j in keep for j in nb) >= 0.7 * len(nb)]
            for i in add:
                v = bme.vertices[i]
                keep[i] = v.co + v.normal * UNDER
        bm = bmesh.new()
        bm.from_mesh(me)
        uvl = bm.loops.layers.uv.active
        bm.faces.ensure_lookup_table()
        nv = {}
        for poly in bme.polygons:
            if not all(i in keep for i in poly.vertices):
                continue
            for i in poly.vertices:
                if i not in nv:
                    nv[i] = bm.verts.new(keep[i])
            try:
                f = bm.faces.new([nv[i] for i in poly.vertices])
            except ValueError:
                continue
            c = sum((keep[i] for i in poly.vertices), Vector()) / len(poly.vertices)
            hf = hb.find_nearest(c)[2]
            u = me.uv_layers.active.data[me.polygons[hf].loop_start].uv.copy()
            for lp in f.loops:
                lp[uvl].uv = u
            n_under += 1
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
        bm.to_mesh(me)
        bm.free()
        basemesh.evaluated_get(dg).to_mesh_clear()
        me.update()
    gimg, mean = grey(img, ob) if img else (None, 0)
    if gimg:
        gimg.filepath_raw = os.path.join(tex_dir, style + ".png")
        gimg.file_format = "PNG"
        gimg.save()
    mat = bpy.data.materials.new(f"ARD_hair_{style}")
    mat.use_nodes = True
    if gimg:
        tn = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tn.image = gimg
        mat.node_tree.links.new(tn.outputs[0], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.parent = rig
    ob.parent_type = "BONE"
    ob.parent_bone = "head"
    ob.matrix_world = Matrix.Identity(4)
    ob.name = ob.data.name = f"hair_{style}"
    print(f"HAIR {ob.name}: {n_all} faces, cut stand {n_pole} cap {n_cap} face {n_face} pale {n_pale} loose {len(drop)} "
          f"-> {n0} -> {len(ob.data.polygons)}; pushed {pushed}, split {split}, under {n_under}, islands {sorted((len(i) for i in isls), reverse=True)[:6]}, scale {tuple(round(x, 4) for x in s)}, tex mean {mean:.2f}")
    made.append(ob)
    if os.environ.get("ARD_HAIR_RAYS"):
        hb = BVHTree.FromPolygons([v.co for v in ob.data.vertices], [p.vertices[:] for p in ob.data.polygons])
        # From outside, as the views look: a ray that meets skin first, then hair within 2 cm, is
        # hair under his skin; skin first and no hair behind it inside the hair's outline is a hole.
        tally = {"hair": 0, "under": 0, "bare": 0}
        for d in (Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((-1, 0, 0))):
            u = d.cross(Vector((0, 0, 1))).normalized()
            for i in range(-40, 41):
                for j in range(-10, 41):
                    o = HEAD - d * 0.5 + u * (i * 0.0025) + Vector((0, 0, j * 0.0025))
                    hh = hb.ray_cast(o, d)
                    if hh[0] is None:
                        continue
                    sk = body.ray_cast(o, d)
                    if sk[0] is None or hh[3] <= sk[3]:
                        tally["hair"] += 1
                    elif hh[3] < sk[3] + 0.02:
                        tally["under"] += 1
                    else:
                        tally["bare"] += 1
        for k in range(0, 9):
            z = our_top - 0.10 - k * 0.01
            o = Vector((our_c.x, our_c.y + 0.5, z))
            d = Vector((0, -1, 0))
            hl = [(round(h[2] - 0.5, 4), "H" if h[1].dot(d) < 0 else "h") for h in hits(hb, o, d)][:4]
            sk = body.ray_cast(o, d)
            q, nrm, _, dist = body.find_nearest(sk[0]) if sk[0] else (None, None, None, None)
            print(f"PROBE {ob.name} z-{0.10 + k * 0.01:.2f}: skin at {sk[3] - 0.5 if sk[0] else None}, hair {hl}")
        inside, faces_in = 0, 0
        for v in ob.data.vertices:
            dd = (v.co - HEAD).normalized()
            if body.ray_cast(v.co + dd * 1e-4, dd, 0.3)[0] is not None:
                inside += 1
        for pg in ob.data.polygons:
            c = pg.center
            dd = (c - HEAD).normalized()
            if body.ray_cast(c + dd * 1e-4, dd, 0.3)[0] is not None:
                faces_in += 1
        print(f"RAYS {ob.name}: {tally}; verts under skin {inside}/{len(ob.data.vertices)}, face centres {faces_in}/{len(ob.data.polygons)}; body verts {len(basemesh.data.vertices)}")

for o in [o for o in bpy.data.objects if o not in mine and o not in made]:
    bpy.data.objects.remove(o, do_unlink=True)

if view_dir:
    os.makedirs(view_dir, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "TEXTURE"
    sc.render.resolution_x = sc.render.resolution_y = 320
    if sc.world is None:
        sc.world = bpy.data.worlds.new("w")
    cd = bpy.data.cameras.new("cam"); cd.type = "ORTHO"; cd.ortho_scale = 0.42
    cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
    head = Vector((our_c.x, our_c.y, our_top - 0.12))
    skin = bpy.data.materials.new("view_skin")
    skin.diffuse_color = (0.85, 0.62, 0.5, 1.0)
    basemesh.data.materials.clear()
    basemesh.data.materials.append(skin)
    basemesh.hide_render = bool(os.environ.get("ARD_HAIR_NOBODY"))   # holes show the backdrop
    for ob in made:
        im = next((n.image for n in ob.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE"), None)
        if im:
            px = np.array(im.pixels[:], dtype=np.float32).reshape(-1, 4)
            px[:, :3] *= np.array([0.30, 0.18, 0.09], dtype=np.float32)
            if os.environ.get("ARD_HAIR_FLAT"):      # no texture: holes show skin, texels don't
                px[:, :3] = np.array([0.0, 0.25, 0.6], dtype=np.float32)
            tint = bpy.data.images.new("view_" + ob.name, im.size[0], im.size[1], alpha=True)
            tint.pixels = px.ravel()
            vm = bpy.data.materials.new("view_" + ob.name)
            vm.use_nodes = True
            tn = vm.node_tree.nodes.new("ShaderNodeTexImage")
            tn.image = tint
            vm.node_tree.links.new(tn.outputs[0], vm.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
            ob["real_mat"] = ob.data.materials[0].name
            ob.data.materials[0] = vm
    for ob in made:
        ob.hide_render = True
    for ob in made:
        ob.hide_render = False
        for name, d in (("front", Vector((0, -1, 0))), ("side", Vector((1, 0, 0))), ("back", Vector((0, 1, 0)))):
            cam.location = head + d * 2
            cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
            sc.render.filepath = os.path.join(view_dir, f"{ob.name}_{name}.png")
            bpy.ops.render.render(write_still=True)
        ob.hide_render = True
    for ob in made:
        ob.hide_render = False
        if "real_mat" in ob:
            ob.data.materials[0] = bpy.data.materials[ob["real_mat"]]
            del ob["real_mat"]

bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
for ob in made:
    ob.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_animations=False,
                          export_apply=False, export_yup=True, export_image_format="NONE")
print(f"EXPORT {out}: {len(made)} cuts in {time.time() - t0:.1f}s")
