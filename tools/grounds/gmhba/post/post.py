# GMHBA post pass (the MCG standard, docs/MCG_STANDARD.md): from the Joel Selwood Stand model
# (tools/grounds/gmhba/gmhba.glb) to the match model, with the faults Google Earth 3D shows fixed
# (tools/grounds/gmhba/qa, 2026-11-22):
#   - the north stand's outer roof plates carry their solar panel field (dark rows on the outer 60 % of each plate);
#   - the north stands' outside wall: white fluted cladding, a white band, a dark glazed band behind white V struts;
#   - the Reg Hickey Stand's wall on Moorabool Street: pale grey panels and window strips, one bay between ribs;
#   - modelled, never painted (standing rule, docs/MCG_STANDARD.md): the north wall's white V struts and the east
#     wall's white pilasters, each under one of the roof's curved ribs.
# Textures are drawn by mktex.py (no photo pixels). Blender 5.2 (pip bpy works):
#   python3 tools/grounds/gmhba/post/mktex.py tools/grounds/gmhba/post/tex
#   python3 -c "import runpy,sys; sys.argv=['post', SRC, OUT, TEXDIR]; runpy.run_path('tools/grounds/gmhba/post/post.py')"
import bpy, bmesh, math, sys
from mathutils import Vector

SRC, OUT, TEX = sys.argv[-3:]
TEX = TEX.rstrip('/') + '/'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
o = bpy.data.objects['gmhba']
me = o.data
PC = (-8.89, -11.85)   # the field's centre in the model (GroundModels.FIT)


def mat(n, img, rough):
    m = bpy.data.materials.new(n)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    t = m.node_tree.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(TEX + img)
    t.image.name = n
    m.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = 0.0
    return m


def slot(m):
    me.materials.append(m)
    return len(me.materials) - 1


S_SOLAR = slot(mat('solar', 'solar.png', 0.55))
S_NORTH = slot(mat('fac_north', 'fac_north.png', 0.8))
S_EAST = slot(mat('fac_east', 'fac_east.png', 0.8))
names = [m.name for m in me.materials]
uv = me.uv_layers.active.data


def ang(x, y):
    return math.degrees(math.atan2(y - PC[1], x - PC[0])) % 360


def ang_u(x, y):
    """Angle in radians, unwrapped round east (the east wall spans 0)."""
    a = math.atan2(y - PC[1], x - PC[0])
    return a


# Solar: the outer roof plates of the north stands, 25-125 degrees (east 0, north 90). The plate's depth runs
# from its leading edge (nearest the field) to its back: measured per 3 degrees from the faces themselves.
sol = []
for p in me.polygons:
    if names[p.material_index] not in ('roof', 'roofg'):
        continue
    c = p.center
    a = ang(c.x, c.y)
    if 25.0 <= a <= 125.0 and abs(p.normal.z) > 0.3 and c.z > 12.0:
        sol.append(p)
lo, hi = {}, {}
for p in sol:
    for i in p.vertices:
        v = me.vertices[i].co
        k = int(ang(v.x, v.y) // 3)
        r = math.hypot(v.x - PC[0], v.y - PC[1])
        lo[k] = min(lo.get(k, 1e9), r)
        hi[k] = max(hi.get(k, -1e9), r)


def depth(x, y):
    a = ang(x, y)
    k = int(a // 3)
    f = a / 3 - k - 0.5
    k2 = k + (1 if f > 0 else -1)
    r = math.hypot(x - PC[0], y - PC[1])
    l0, h0 = lo.get(k), hi.get(k)
    l1, h1 = lo.get(k2, l0), hi.get(k2, h0)
    w = abs(f)
    l, h = l0 * (1 - w) + l1 * w, h0 * (1 - w) + h1 * w
    return min(1.0, max(0.0, (r - l) / max(1.0, h - l)))


for p in sol:
    p.material_index = S_SOLAR
    for li in p.loop_indices:
        v = me.vertices[me.loops[li].vertex_index].co
        uv[li].uv = (ang_u(v.x, v.y) * 120.0 / 6.0, 1.0 - depth(v.x, v.y))

# The east roof's curved white ribs (fascia above 17 m, 280-25 degrees): each rib's foot, lowest points first.
def east_a(x, y):
    """Degrees round from east, -80..25 across the Reg Hickey Stand."""
    a = ang(x, y)
    return a - 360.0 if a > 180.0 else a


rib_pts = []
for p in me.polygons:
    c = p.center
    a = east_a(c.x, c.y)
    if names[p.material_index] == 'fascia' and c.z > 17.0 and -80.0 <= a < 25.0:
        rib_pts.append((a, c.z, c.x, c.y))
rib_pts.sort()
RIBS = []
cur = []
for q in rib_pts + [(1e9, 0, 0, 0)]:
    if cur and q[0] - cur[-1][0] > 3.0:
        low = sorted(cur, key=lambda t: t[1])[:max(1, len(cur) // 4)]
        RIBS.append((sum(t[2] for t in low) / len(low), sum(t[3] for t in low) / len(low)))
        cur = []
    cur.append(q)
RIB_A = sorted(east_a(x, y) for x, y in RIBS)
print('east ribs', len(RIB_A), [round(a, 1) for a in RIB_A])


def bay_u(x, y):
    """Bays between ribs: u = bay index + share of the way across it, so each bay is one texture tile."""
    a = east_a(x, y)
    if a <= RIB_A[0]:
        return (a - RIB_A[0]) / (RIB_A[1] - RIB_A[0])
    for i in range(len(RIB_A) - 1):
        if a <= RIB_A[i + 1]:
            return i + (a - RIB_A[i]) / (RIB_A[i + 1] - RIB_A[i])
    return len(RIB_A) - 1 + (a - RIB_A[-1]) / (RIB_A[-1] - RIB_A[-2])


# Walls: vertical faces of the plain 'wall' material on the outside.
nn = ne = 0
for p in me.polygons:
    if names[p.material_index] != 'wall' or abs(p.normal.z) > 0.3:
        continue
    c = p.center
    r = math.hypot(c.x - PC[0], c.y - PC[1])
    a = ang(c.x, c.y)
    radial = abs((p.normal.x * (c.x - PC[0]) + p.normal.y * (c.y - PC[1])) / r)
    if radial < 0.3:
        continue
    if 22.0 <= a <= 112.0 and r > 80.0:
        p.material_index = S_NORTH
        nn += 1
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = (ang_u(v.x, v.y) * 140.0 / 12.0, v.z / 25.0)
    elif (a >= 285.0 or a < 22.0) and r > 80.0 and c.z < 17.5:
        p.material_index = S_EAST
        ne += 1
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = (bay_u(v.x, v.y), v.z / 17.0)
print('solar faces', len(sol), 'north wall', nn, 'east wall', ne)

# ---- Modelled detail (no painted-on geometry) ----
white = bpy.data.materials.new('strut')
white.use_nodes = True
wb = white.node_tree.nodes['Principled BSDF']
wb.inputs['Base Color'].default_value = (0.86, 0.87, 0.88, 1.0)
wb.inputs['Roughness'].default_value = 0.6
S_WHITE = slot(white)


def wall_r(a, mat_slot, zlo, zhi):
    """The wall's outer radius at angle a (deg) from the faces drawn with mat_slot between zlo and zhi."""
    best = None
    for p in me.polygons:
        if p.material_index != mat_slot:
            continue
        c = p.center
        if not zlo <= c.z <= zhi:
            continue
        d = (ang(c.x, c.y) - a + 540.0) % 360.0 - 180.0
        if abs(d) < 1.2:
            r = max(math.hypot(me.vertices[i].co.x - PC[0], me.vertices[i].co.y - PC[1]) for i in p.vertices)
            best = r if best is None else max(best, r)
    return best


def at(a, r, z):
    t = math.radians(a)
    return Vector((PC[0] + r * math.cos(t), PC[1] + r * math.sin(t), z))


bm = bmesh.new()
bm.from_mesh(me)


def tube(p0, p1, rad, sides=8):
    """A round tube from p0 to p1 (white painted steel)."""
    ax = (p1 - p0).normalized()
    u = ax.cross(Vector((0, 0, 1)))
    if u.length < 1e-3:
        u = Vector((1, 0, 0))
    u.normalize()
    w = ax.cross(u)
    ring0, ring1 = [], []
    for k in range(sides):
        t = 2 * math.pi * k / sides
        off = (u * math.cos(t) + w * math.sin(t)) * rad
        ring0.append(bm.verts.new(p0 + off))
        ring1.append(bm.verts.new(p1 + off))
    for k in range(sides):
        f = bm.faces.new((ring0[k], ring0[(k + 1) % sides], ring1[(k + 1) % sides], ring1[k]))
        f.material_index = S_WHITE
    for ring in (ring0, ring1[::-1]):
        f = bm.faces.new(ring)
        f.material_index = S_WHITE


def box(corners, mat_slot=None):
    """A box from 8 corners (bottom 4 then top 4, same winding)."""
    vs = [bm.verts.new(c) for c in corners]
    for q in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        f = bm.faces.new([vs[i] for i in q])
        f.material_index = S_WHITE if mat_slot is None else mat_slot


# North: white V struts in front of the glazed band, as Google Earth shows from the north: each roof fold's
# peak on the back edge is held by two arms, one from each neighbouring V, so the struts zigzag with the folds.
# Feet together on the white band at 16 m, 0.8 m proud of the wall; 0.5 m tubes.
edge = {}
for p in me.polygons:
    if p.material_index not in (S_SOLAR,) and names[p.material_index] not in ('roof', 'roofg', 'roofd', 'under'):
        continue
    for i in p.vertices:
        v = me.vertices[i].co
        a = ang(v.x, v.y)
        if 30.0 <= a <= 102.0:
            k = round(a * 4)
            r = math.hypot(v.x - PC[0], v.y - PC[1])
            if k not in edge or r > edge[k][0]:
                edge[k] = (r, v.z, v.copy())
# The back edge proper (bins nearer than 120 m are the stand's inner rows), peaks every ~4 degrees.
ks = [k for k in sorted(edge) if edge[k][0] > 120.0 and edge[k][1] > 20.0]
peaks = []
for k in ks:
    z = edge[k][1]
    near = [edge[q][1] for q in ks if abs(q - k) <= 6]
    if z >= max(near) - 1e-3 and z - min(near) > 1.0 and (not peaks or k - peaks[-1] > 8):
        peaks.append(k)
nv = 0
for k0, k1 in zip(peaks, peaks[1:]):
    p0, p1 = edge[k0][2], edge[k1][2]
    am = (ang(p0.x, p0.y) + ang(p1.x, p1.y)) / 2
    r = wall_r(am, S_NORTH, 16.0, 25.0)
    if r is None:
        continue
    foot = at(am, r + 0.8, 16.0)
    tube(foot, p0 - Vector((0, 0, 0.3)), 0.25)
    tube(foot, p1 - Vector((0, 0, 0.3)), 0.25)
    nv += 1
print('north roof peaks', len(peaks))
# East: a white pilaster under each rib, 0.8 m wide and 0.5 m proud, ground to the roof's edge (17.2 m).
npil = 0
for ra in RIB_A:
    a = ra % 360.0
    r = wall_r(a, S_EAST, 0.5, 17.0)
    if r is None:
        continue
    hw = math.degrees(0.4 / r)
    c = [at(a - hw, r - 0.1, 0.0), at(a + hw, r - 0.1, 0.0), at(a + hw, r + 0.5, 0.0), at(a - hw, r + 0.5, 0.0)]
    box(c + [Vector((v.x, v.y, 17.2)) for v in c])
    npil += 1
# Seats: the model drew each row's seats as flat strips with the shells painted on and cut out by alpha. They
# become real 3D seats (the ground kit's shell, seat_tmpl.bin, as at the MCG), one every 0.5 m along each
# strip, facing the field; the strips go. Colours from photo p12: blue and white in pairs, shifted one seat a row.
import os
import numpy as np
bm.faces.ensure_lookup_table()
pan_slots = {i for i, n in enumerate(names) if n in ('seatpan', 'seatpan_d')}
shell_slots = pan_slots | {i for i, n in enumerate(names) if n in ('seatback', 'seatback_d')}
pans = [f for f in bm.faces if f.material_index in pan_slots]
seats = {'blue': [], 'white': []}
used = set()
for n, f in enumerate(pans):
    if f.index in used:
        continue
    # Each strip piece is a quad split in two triangles, stored one after the other; they share two corners
    # by position (the triangles do not share vertices).
    def key(v):
        return (round(v.co.x, 3), round(v.co.y, 3), round(v.co.z, 3))
    vs = {key(v): v.co.copy() for v in f.verts}
    used.add(f.index)
    if n + 1 < len(pans):
        g = pans[n + 1]
        if len(set(vs) & {key(v) for v in g.verts}) == 2:
            used.add(g.index)
            vs.update({key(v): v.co.copy() for v in g.verts})
    P = np.array([[v.x, v.y] for v in vs.values()])
    z = float(np.mean([v.z for v in vs.values()]))
    c = P.mean(0)
    _, _, vt = np.linalg.svd(P - c)
    along = vt[0]
    t = (P - c) @ along
    L = float(t.max() - t.min())
    if L < 0.35:
        continue
    back = np.array([-along[1], along[0]])
    if back @ (c - np.array(PC)) < 0:
        back = -back
    mid = c + along * float(t.max() + t.min()) / 2
    k = max(1, int(round(L / 0.5)))
    row = int(round(z / 0.3))
    for i in range(k):
        q = mid + along * (-L / 2 + (i + 0.5) * L / k)
        # Google Earth: slate navy seats all round, pale grey in the Reg Hickey Stand (east).
        aq = ang(q[0], q[1])
        col = 'white' if (aq >= 285 or aq < 25) else 'blue'
        # glTF frame: x east, y up, z south. Seat local x along the row, y up, +z its back.
        X = np.array([along[0], 0.0, -along[1]])
        Z = np.array([back[0], 0.0, -back[1]])
        Y = np.array([0.0, 1.0, 0.0])
        if np.dot(np.cross(X, Y), Z) < 0:
            X = -X
        o = np.array([q[0], z + 0.005, -q[1]])
        seats[col].append([X[0], Y[0], Z[0], o[0], X[1], Y[1], Z[1], o[1], X[2], Y[2], Z[2], o[2]])
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in shell_slots], context='FACES')

# Painted geometry made real. isoline_boxes: along each line of constant u (a slat, a beam) across a
# material's faces, a box `w` wide standing `d` off the face toward `side(face)`, kept where the image's
# v (0 at the top) lies in [v0, v1].
uvl = bm.loops.layers.uv.active


def isoline_boxes(slot, us, w, d, side, v0=0.0, v1=1.0, mat=None):
    segs = 0
    for f in [f for f in bm.faces if f.material_index == slot]:
        L = list(f.loops)
        P = [l.vert.co.copy() for l in L]
        U = [l[uvl].uv.x for l in L]
        V = [1.0 - l[uvl].uv.y for l in L]
        out = side(f)
        if out is None:
            continue
        lo, hi = min(U), max(U)
        for k in range(int(math.floor(lo)) - 1, int(math.ceil(hi)) + 1):
            for c0 in us:
                c = k + c0
                if not lo < c < hi:
                    continue
                pts = []
                for i in range(len(L)):
                    j = (i + 1) % len(L)
                    if (U[i] - c) * (U[j] - c) < 0:
                        t = (c - U[i]) / (U[j] - U[i])
                        pts.append((P[i].lerp(P[j], t), V[i] + (V[j] - V[i]) * t))
                if len(pts) != 2:
                    continue
                (A, va), (B, vb) = pts
                # clip to [v0, v1]
                if va > vb:
                    (A, va), (B, vb) = (B, vb), (A, va)
                if vb < v0 or va > v1 or vb - va < 1e-6:
                    continue
                A2 = A.lerp(B, max(0.0, (v0 - va) / (vb - va)))
                B2 = A.lerp(B, min(1.0, (v1 - va) / (vb - va)))
                ax = (B2 - A2)
                if ax.length < 0.05:
                    continue
                t = ax.normalized().cross(out).normalized() * (w / 2)
                o = out * d
                box([A2 - t, A2 + t, A2 + t + o, A2 - t + o, B2 - t, B2 + t, B2 + t + o, B2 - t + o], mat)
                segs += 1
    return segs


def outward(f):
    c = f.calc_center_median()
    r = Vector((c.x - PC[0], c.y - PC[1], 0.0)).normalized()
    n = Vector((f.normal.x, f.normal.y, 0.0))
    if n.length < 1e-3:
        return None
    n.normalize()
    return n if n.dot(r) > 0 else -n


def down(f):
    return Vector((0.0, 0.0, -1.0))


def retex(slot_name, img):
    m = me.materials[names.index(slot_name)]
    for nd in m.node_tree.nodes:
        if nd.type == 'TEX_IMAGE':
            nd.image = bpy.data.images.load(TEX + img)
            nd.image.name = slot_name


# Players Stand south-west face: white slats 0.3 m wide every 0.5 m, 0.2 m proud, from 7 m to the top
# (the image's top 71 %; 30.5 m an image width).
n_slats = isoline_boxes(names.index('slats'), [(i + 0.5) * 0.5 / 30.53 for i in range(61)], 0.3, 0.2,
                        outward, 0.0, 0.71, S_WHITE)
retex('slats', 'slats_backing.png')
# Under the west upper tier: concrete rake beams 0.5 m wide hanging 0.6 m, every 4.5 m (9.01 m an image width).
S_CONC = slot(mat('beam', 'recess_plain.png', 0.85))
n_beams = isoline_boxes(names.index('recess'), [0.031, 0.527], 0.5, 0.6, down, 0.0, 1.0, S_CONC)
retex('recess', 'recess_plain.png')
print('slats', n_slats, 'beams', n_beams)

# The Reg Hickey Stand's south end: one flat wall carried a painted elevation of the building (its stepped
# roofline and the grey sky above it). The wall is cut to the building's own outline: the north block to
# 28/340 of the image from the top, the stair tower to 20/340, the south block to 50/340, nothing left of
# 62/940. Its windows and louvres stay painted (flat glazing).
S_RH = names.index('rhend')
rh = [f for f in bm.faces if f.material_index == S_RH]
RECTS = ((62 / 940, 290 / 940, 28 / 340), (290 / 940, 408 / 940, 20 / 340), (408 / 940, 1.0, 50 / 340))


def clip(poly, k, c, keep_ge):
    """Sutherland-Hodgman: keep the part of poly (list of (u, v, x, y, z)) with coordinate k >= c (or <= c)."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        pin = (p[k] >= c) if keep_ge else (p[k] <= c)
        qin = (q[k] >= c) if keep_ge else (q[k] <= c)
        if pin:
            out.append(p)
        if pin != qin:
            t = (c - p[k]) / (q[k] - p[k])
            out.append(tuple(p[j] + t * (q[j] - p[j]) for j in range(5)))
    return out


n_rh = 0
new_faces = []
for f in rh:
    # Each face is clipped in its own (u, v) space, so its own mapping carries over exactly.
    poly = [(l[uvl].uv.x, 1.0 - l[uvl].uv.y, *l.vert.co) for l in f.loops]
    for u0, u1, vt in RECTS:
        piece = poly
        for k, c, ge in ((0, u0, True), (0, u1, False), (1, vt, True)):
            piece = clip(piece, k, c, ge) if len(piece) >= 3 else []
        if len(piece) >= 3:
            new_faces.append(piece)
bmesh.ops.delete(bm, geom=rh, context='FACES')
for piece in new_faces:
    try:
        nf = bm.faces.new([bm.verts.new(Vector(q[2:])) for q in piece])
    except ValueError:
        continue
    nf.material_index = S_RH
    for l, q in zip(nf.loops, piece):
        l[uvl].uv = (q[0], 1.0 - q[1])
    n_rh += 1
print('rhend faces', len(rh), '->', n_rh)
bm.to_mesh(me)
bm.free()
outdir = os.path.dirname(os.path.abspath(OUT))
for col, rows in seats.items():
    np.array(rows, '<f4').tofile(os.path.join(outdir, 'seats_seat_gmhba_%s.bin' % col))
print('V struts', nv, 'pilasters', npil, 'seats', {k: len(v) for k, v in seats.items()})
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB')
print('DONE')
