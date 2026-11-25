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
        # Google Earth: slate navy seats all round, pale grey in the Reg Hickey Stand (east) and the
        # south-east corner.
        aq = ang(q[0], q[1])
        col = 'white' if (aq >= 277 or aq < 25) else 'blue'
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
# The fins screen at the west side's south end: grey fins 0.22 m wide every 0.48 m (the image's 17.6 a width,
# 8.5 m an image width), 0.3 m deep, over the dark openings.
S_FIN = slot(mat('fin', 'fin_grey.png', 0.6))
fin_us = [(33.5 + 29.0 * k) / 512.0 for k in range(-1, 18)]
n_fins = isoline_boxes(names.index('fins'), fin_us, 0.22, 0.3, outward, -10.0, 10.0, S_FIN)
retex('fins', 'fins_backing.png')

# The south-east corner between the Joel Selwood and Reg Hickey stands (Google Earth, from above and from
# the ground): past the lower tier's 7 rows a 1.5 m walkway, then an upper rake rising to the line of the
# two stands' backs (13.3 m at the Reg Hickey end), a back wall and a 5 m concourse to the street wall, with
# the big screen standing at the back. The source model had a grass yard there at ground level.
S_TREAD = names.index('tread')
S_AISLE = names.index('aisle')
S_WALL = names.index('wall')
S_PAVE = names.index('pave')
inner_w, outer_w = [], []
for f in bm.faces:
    if f.material_index not in (S_WALL, S_EAST) or abs(f.normal.z) > 0.1:
        continue
    zs = [v.co.z for v in f.verts]
    c = f.calc_center_median()
    a = ang(c.x, c.y)
    if not 276.0 < a < 297.0:
        continue
    r = math.hypot(c.x - PC[0], c.y - PC[1])
    if abs(max(zs) - 4.0) < 0.05 and r < 100.0:
        inner_w.append((a, r))
    elif abs(max(zs) - 7.5) < 0.05 and r > 105.0:
        outer_w.append((a, r))
inner_w.sort()
outer_w.sort()
A0, A1 = 277.6, 294.2


def r_in(a):
    return float(np.interp(a, [q[0] for q in inner_w], [q[1] for q in inner_w]))


def r_out(a):
    return float(np.interp(a, [q[0] for q in outer_w], [q[1] for q in outer_w]))


Z0, WALK, DEPTH, RISE = 4.0, 1.5, 0.8, 0.42
# The yard's grass becomes the concourse's paving.
for f in bm.faces:
    if f.material_index == names.index('turf'):
        c = f.calc_center_median()
        if 272.0 < ang(c.x, c.y) < 300.0 and math.hypot(c.x - PC[0], c.y - PC[1]) > 85.0:
            f.material_index = S_PAVE


def quad(ps, mat_slot, uvs=None):
    f = bm.faces.new([bm.verts.new(p) for p in ps])
    f.material_index = mat_slot
    if uvs is None:
        uvs = [(p.x / 2.0, p.y / 2.0) for p in ps] if abs(f.normal.z) > 0.5 else \
              [((p.x + p.y) / 2.0, p.z / 2.0) for p in ps]
    for l, uvq in zip(f.loops, uvs):
        l[uvl].uv = uvq
    return f


def rows_at(a):
    # Google Earth from above and from the ground: the upper rake is about 1.5 times the lower tier's depth,
    # 14 rows (9.9 m), well under the two stands beside it.
    return max(0, min(14, int((r_out(a) - 5.0 - r_in(a) - WALK) // DEPTH)))


arc_aisles = []
step = 0.5
angs = list(np.arange(A0, A1 + 1e-6, step))
# Radial aisles every ~12 m along the walkway, 1.2 m wide.
L = 0.0
for i in range(len(angs) - 1):
    L += math.radians(step) * r_in(angs[i])
    if L > 8.0 and angs[i] < A1 - 2:
        arc_aisles.append(angs[i])
        L = 0.0
n_corner_seats = 0
top_line = []
for i in range(len(angs) - 1):
    a, b = angs[i], angs[i + 1]
    ra, rb = r_in(a), r_in(b)
    # The walkway.
    quad([at(a, ra, Z0), at(b, rb, Z0), at(b, rb + WALK, Z0), at(a, ra + WALK, Z0)], S_TREAD)
    k = min(rows_at(a), rows_at(b))
    in_aisle = any(abs((a + b) / 2 - q) < math.degrees(0.6 / ra) for q in arc_aisles)
    for j in range(k):
        r0a, r0b = ra + WALK + j * DEPTH, rb + WALK + j * DEPTH
        z1 = Z0 + (j + 1) * RISE
        # Riser, then tread.
        quad([at(a, r0a, z1 - RISE), at(b, r0b, z1 - RISE), at(b, r0b, z1), at(a, r0a, z1)], S_TREAD)
        quad([at(a, r0a, z1), at(b, r0b, z1), at(b, r0b + DEPTH, z1), at(a, r0a + DEPTH, z1)],
             S_AISLE if in_aisle else S_TREAD)
        if in_aisle:
            continue
        # Seats one each 0.5 m along the row, facing the ground.
        rm = (r0a + r0b) / 2 + 0.4
        am, bm_ = a, b
        span = math.radians(bm_ - am) * rm
        nseat = max(1, int(round(span / 0.5)))
        for s_ in range(nseat):
            aq = am + (bm_ - am) * (s_ + 0.5) / nseat
            q = at(aq, rm, 0.0)
            back = Vector((q.x - PC[0], q.y - PC[1], 0.0)).normalized()
            along = Vector((-back.y, back.x, 0.0))
            X = np.array([along.x, 0.0, -along.y])
            Z = np.array([back.x, 0.0, -back.y])
            Y = np.array([0.0, 1.0, 0.0])
            if np.dot(np.cross(X, Y), Z) < 0:
                X = -X
            o = np.array([q.x, z1 + 0.405, -q.y])
            seats['white'].append([X[0], Y[0], Z[0], o[0], X[1], Y[1], Z[1], o[1], X[2], Y[2], Z[2], o[2]])
            n_corner_seats += 1
    ztop = Z0 + k * RISE
    rta, rtb = ra + WALK + k * DEPTH, rb + WALK + k * DEPTH
    top_line.append((a, rta, ztop))
    # The back: a parapet 1.1 m over the top row, its wall down to the concourse, and the concourse paving.
    quad([at(a, rta, ztop), at(b, rtb, ztop), at(b, rtb, ztop + 1.1), at(a, rta, ztop + 1.1)], S_WALL)
    quad([at(a, rta + 0.25, ztop + 1.1), at(b, rtb + 0.25, ztop + 1.1), at(b, rtb + 0.25, 0.3), at(a, rta + 0.25, 0.3)], S_WALL)
    quad([at(a, rta, ztop + 1.1), at(b, rtb, ztop + 1.1), at(b, rtb + 0.25, ztop + 1.1), at(a, rta + 0.25, ztop + 1.1)], S_WALL)
# The rake's two ends: stepped side walls down to the ground.
for a in (A0, angs[-1]):
    k = rows_at(a)
    ra = r_in(a)
    prof = [(ra, 0.3), (ra, Z0)] + [(ra + WALK + j * DEPTH, Z0 + (j + 1) * RISE) for j in range(k)]
    for j in range(len(prof) - 1):
        r0, z0_ = prof[j]
        r1, z1_ = prof[j + 1]
        r1e = r1 if j == len(prof) - 2 else r1
        quad([at(a, r0, 0.3), at(a, r1e + (DEPTH if j == len(prof) - 2 and j > 0 else 0.0), 0.3),
              at(a, r1e + (DEPTH if j == len(prof) - 2 and j > 0 else 0.0), max(z0_, z1_)), at(a, r0, max(z0_, z1_))], S_WALL)
# A handrail along the walkway's front edge: a 50 mm rail 1.0 m up on posts every ~2 m.
rail = [at(a, r_in(a) + 0.15, Z0 + 1.0) for a in angs]
for p0, p1 in zip(rail, rail[1:]):
    tube(p0, p1, 0.03, 6)
for i in range(0, len(angs), 4):
    tube(at(angs[i], r_in(angs[i]) + 0.15, Z0), rail[i], 0.03, 6)
print('south-east corner: seats', n_corner_seats, 'aisles', len(arc_aisles), 'rows', rows_at(A0), '-', rows_at(A1))

# The big screen stands at the back of that rake (Google Earth): it moves back and up from the grass,
# on two columns, its base 0.5 m over the parapet.
scr = [f for f in bm.faces if f.material_index == names.index('screen')]
if scr:
    sv = {v for f in scr for v in f.verts}
    c = sum((v.co for v in sv), Vector()) / len(sv)
    a_s = ang(c.x, c.y)
    _, rt, zt = min(top_line, key=lambda q: abs(q[0] - a_s))
    zmin = min(v.co.z for v in sv)
    dst = at(a_s, rt + 1.2, 0.0)
    mv = Vector((dst.x - c.x, dst.y - c.y, zt + 1.1 + 0.5 - zmin))
    for v in sv:
        v.co += mv
    SCREEN_LIFT = mv
# The scoreboard: its red casing stands 0.4 m proud of the screen, 0.62 m wide at the sides and 0.81 m top
# and bottom (the painted border: 25/724 and 32/384 of the image).
S_RED = slot(mat('casing', 'frame_red.png', 0.5))
S_HEAD = slot(mat('lamphead', 'lamphead.png', 0.6))
n_case = 0
scr = [f for f in bm.faces if f.material_index == names.index('screen')]
if scr:
    pts = [(l.vert.co.copy(), l[uvl].uv.x, 1.0 - l[uvl].uv.y) for f in scr for l in f.loops]

    def corner(u, v):
        return min(pts, key=lambda q: (q[1] - u) ** 2 + (q[2] - v) ** 2)[0]
    TL, TR, BL, BR = corner(0, 0), corner(1, 0), corner(0, 1), corner(1, 1)
    o = -outward(scr[0]) * 0.4   # toward the ground

    def P(u, v):
        return (TL.lerp(TR, u)).lerp(BL.lerp(BR, u), v)
    bu, bv = 25.0 / 724.0, 32.0 / 384.0
    for (u0, v0, u1, v1) in ((0, 0, 1, bv), (0, 1 - bv, 1, 1), (0, bv, bu, 1 - bv), (1 - bu, bv, 1, 1 - bv)):
        q = [P(u0, v1), P(u1, v1), P(u1, v0), P(u0, v0)]
        box(q + [c + o for c in q], S_RED)
        n_case += 1
    # Its back and sides, so the board is a box and not a sheet seen from behind.
    back = outward(scr[0]) * 0.6
    q = [P(0, 1), P(1, 1), P(1, 0), P(0, 0)]
    box([c + back for c in q] + q, S_HEAD)
retex('screen', 'screen_plain.png')

# Light towers (Google Earth, all four): the head is an open inverted triangle, two white legs flaring from
# 52 m to the top at 74.7 m, and its floodlights fill the frame between the legs from 57 m to the top in
# rows 1.3 m apart, each row a grey rail carrying 0.6 m lamps 0.68 m apart, aimed down at the ground. The source
# model's three lamp boxes (a painted grid of circles on every face, top and bottom included) go.
S_LAMP = names.index('lamp')
old = [f for f in bm.faces if f.material_index == S_LAMP]
lamp_cs = [f.calc_center_median() for f in old]
bmesh.ops.delete(bm, geom=old, context='FACES')
towers = []
for c in lamp_cs:
    if not any(math.hypot(c.x - t.x, c.y - t.y) < 10.0 for t in towers):
        towers.append(c)
S_TOWER = names.index('tower')


def lamp(p, n, rad=0.3, depth=0.5, sides=10):
    u = n.cross(Vector((0, 0, 1))).normalized()
    w = n.cross(u)
    r0 = [bm.verts.new(p + (u * math.cos(2 * math.pi * k / sides) + w * math.sin(2 * math.pi * k / sides)) * rad)
          for k in range(sides)]
    r1 = [bm.verts.new(v.co + n * depth) for v in r0]
    for k in range(sides):
        bm.faces.new((r0[k], r0[(k + 1) % sides], r1[(k + 1) % sides], r1[k])).material_index = S_HEAD
    bm.faces.new(r0[::-1]).material_index = S_HEAD
    glass = bm.faces.new(r1)
    glass.material_index = S_LAMP
    for l in glass.loops:
        d = l.vert.co - (p + n * depth)
        l[uvl].uv = (0.5 + d.dot(u) / (2 * rad), 0.5 + d.dot(w) / (2 * rad))


n_lamps = 0
for tc in towers:
    hv = [v.co.copy() for v in bm.verts if v.link_faces and all(f.material_index == S_TOWER for f in v.link_faces)
          and math.hypot(v.co.x - tc.x, v.co.y - tc.y) < 9.0 and 51.5 < v.co.z < 75.0]
    top = np.array([[v.x, v.y] for v in hv if v.z > 72.0])
    cxy = top.mean(0)
    _, _, vt = np.linalg.svd(top - cxy)
    t = Vector((vt[0][0], vt[0][1], 0.0))
    n = Vector((PC[0] - cxy[0], PC[1] - cxy[1], 0.0)).normalized()
    n = (n - t * n.dot(t)).normalized()          # toward the ground, square to the frame
    c0 = Vector((cxy[0], cxy[1], 0.0))
    # Each leg's inner edge as a line t(z), and the frame's front face (furthest toward the ground).
    L = [((v - c0).dot(t), v.z) for v in hv]
    front = max((v - c0).dot(n) for v in hv)
    back = min((v - c0).dot(n) for v in hv)
    zs = sorted({round(z, 1) for _, z in L if 52.0 <= z <= 72.0})
    lft = [(z, max(tt for tt, zz in L if abs(zz - z) < 0.06 and tt < 0)) for z in zs]
    rgt = [(z, min(tt for tt, zz in L if abs(zz - z) < 0.06 and tt > 0)) for z in zs]
    fl = np.polyfit([z for z, _ in lft], [q for _, q in lft], 1)
    fr = np.polyfit([z for z, _ in rgt], [q for _, q in rgt], 1)
    mid = (front + back) / 2
    aim = (n * math.cos(math.radians(30)) - Vector((0, 0, math.sin(math.radians(30))))).normalized()
    z = 55.6
    while z < 73.6:
        a, b = np.polyval(fl, z), np.polyval(fr, z)
        # The rail: a 0.3 m x 0.3 m grey bar between the legs, at the frame's middle depth.
        p0 = c0 + t * a + n * mid + Vector((0, 0, z))
        p1 = c0 + t * b + n * mid + Vector((0, 0, z))
        hw = n * 0.15
        hz = Vector((0, 0, 0.15))
        box([p0 - hw - hz, p1 - hw - hz, p1 + hw - hz, p0 + hw - hz, p0 - hw + hz, p1 - hw + hz, p1 + hw + hz, p0 + hw + hz], S_HEAD)
        k = int((b - a - 0.3) // 0.68)
        for i in range(k):
            q = c0 + t * (a + 0.15 + (b - a - 0.3) * (i + 0.5) / k) + n * (mid + 0.15) + Vector((0, 0, z + 0.45))
            lamp(q, aim)
            n_lamps += 1
        z += 1.3
retex('lamp', 'lamp_glass.png')
retex('beige', 'beige_grey.png')
heads = towers
print('fins', n_fins, 'scoreboard casing', n_case, 'lamp heads', len(heads), 'lamps', n_lamps)
bm.to_mesh(me)
bm.free()
outdir = os.path.dirname(os.path.abspath(OUT))
for col, rows in seats.items():
    np.array(rows, '<f4').tofile(os.path.join(outdir, 'seats_seat_gmhba_%s.bin' % col))
print('V struts', nv, 'pilasters', npil, 'seats', {k: len(v) for k, v in seats.items()})
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB')
print('DONE')
