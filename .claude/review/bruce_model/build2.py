# blender -b --python build2.py -- parts.json out.glb render.png [render2.png]
# Geometry from parts.json (world metres, x east, y north, z up, field level 0).
# Texturing: every face is projected from the real photo whose camera sees it most head-on with the most
# pixels per metre (ref46 or ref50), if that camera can see it (BVH ray test). Faces neither photo sees
# get the part's close-up texture (parts.json 'closeups'), mapped in world metres, one copy per bay.
import bpy, bmesh, json, math, sys, os
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index('--') + 1:]
P = json.load(open(a[0]))
bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
HERE = os.path.dirname(os.path.abspath(a[0]))

CAMS = []
for c in P['cams']:
    CAMS.append(dict(name=c['name'], C=Vector(c['C']), M=[Vector(r) for r in c['M']], f=c['f'], W=c['W'], H=c['H'],
                     img=None if P.get('no_photo') else bpy.data.images.load(os.path.join(HERE, c['img']))))


def project(cam, X):
    d = X - cam['C']
    x = cam['M'][0].dot(d); y = cam['M'][1].dot(d); z = cam['M'][2].dot(d)
    return (cam['W'] / 2 + cam['f'] * x / z, cam['H'] / 2 - cam['f'] * y / z), z


# ---------------------------------------------------------------- materials
MATS = {}


def img_mat(name, img, ext='CLIP'):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.extension = ext; t.interpolation = 'Cubic'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.9
    MATS[name] = m
    return m


NOPH = P.get('no_photo', False)
for c in CAMS:
    if not NOPH:
        img_mat('photo_' + c['name'], c['img'])
CLOSE = {}
for k, v in P.get('closeups', {}).items():
    CLOSE[k] = dict(v, mat=img_mat('close_' + k, bpy.data.images.load(os.path.join(HERE, v['img'])), 'REPEAT'))

# ---------------------------------------------------------------- mesh building
PARTS = []  # (object, closeup key, bay mapping)


def mk(name, faces, close, bay=None, uvs=None):
    """faces: list of vertex lists (world Vectors). close: texture key. uvs: per-face lists of (u, v) in metres
    (or bay units for a bay texture), laid out by the caller so rows and joints run continuously along the part."""
    bm = bmesh.new()
    lay = bm.loops.layers.uv.new('UVMap') if uvs is not None else None
    cl = CLOSE[close]
    cache = {}
    for fi, fv in enumerate(faces):
        vs = []
        for p in fv:
            k = (round(p.x, 3), round(p.y, 3), round(p.z, 3))
            if k not in cache:
                cache[k] = bm.verts.new(p)
            vs.append(cache[k])
        try:
            f = bm.faces.new(vs)
        except ValueError:
            continue
        if lay is not None:
            for lp, (uu, vv) in zip(f.loops, uvs[fi]):
                lp[lay].uv = (uu / cl['w'], (vv - cl.get('v0', 0.0)) / cl['h'])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o)
    PARTS.append((o, close, 'preset' if uvs is not None else bay))
    return o


def grid(p00, p10, p01, p11, step=2.0):
    """bilinear patch split so no edge is longer than step metres"""
    nu = max(1, int(math.ceil(max((p10 - p00).length, (p11 - p01).length) / step)))
    nv = max(1, int(math.ceil(max((p01 - p00).length, (p11 - p10).length) / step)))
    out = []
    for i in range(nu):
        for j in range(nv):
            def at(u, v):
                return (p00.lerp(p10, u)).lerp(p01.lerp(p11, u), v)
            u0, u1, v0, v1 = i / nu, (i + 1) / nu, j / nv, (j + 1) / nv
            out.append([at(u0, v0), at(u1, v0), at(u1, v1), at(u0, v1)])
    return out


def strip(A, B, step=2.0):
    """loft between two equal-length polylines"""
    out = []
    for i in range(len(A) - 1):
        out += grid(A[i], A[i + 1], B[i], B[i + 1], step)
    return out


def bil(p00, p10, p01, p11, u, v):
    return (p00 * (1 - u) + p10 * u) * (1 - v) + (p01 * (1 - u) + p11 * u) * v


def strip_uv(A, B, U, step=2.0):
    """loft with uvs: u from U (per index, along the part), v = metres from A towards B"""
    F = []; T = []
    VB = [(B[i] - A[i]).length for i in range(len(A))]
    for i in range(len(A) - 1):
        p00, p10, p01, p11 = A[i], A[i + 1], B[i], B[i + 1]
        t00, t10, t01, t11 = Vector((U[i], 0)), Vector((U[i + 1], 0)), Vector((U[i], VB[i])), Vector((U[i + 1], VB[i + 1]))
        nu = max(1, int(math.ceil(max((p10 - p00).length, (p11 - p01).length) / step)))
        nv = max(1, int(math.ceil(max((p01 - p00).length, (p11 - p10).length) / step)))
        for a in range(nu):
            for b in range(nv):
                q = [(a / nu, b / nv), ((a + 1) / nu, b / nv), ((a + 1) / nu, (b + 1) / nv), (a / nu, (b + 1) / nv)]
                F.append([bil(p00, p10, p01, p11, x, y) for x, y in q])
                T.append([tuple(bil(t00, t10, t01, t11, x, y)) for x, y in q])
    return F, T


def arclen(A):
    out = [0.0]
    for i in range(1, len(A)):
        out.append(out[-1] + (A[i] - A[i - 1]).length)
    return out


V = lambda p: Vector(p)
R = {k: [V(p) for p in v] for k, v in P['rings'].items()}  # bowl rings, equal length, closed

# ---------------------------------------------------------------- seating built as seats (gate 2026-11-19: "Build them as seats")
# the seat surface is a flight of concrete steps (one tread per row, about 0.8 m deep), each row carrying moulded
# bucket seats 0.5 m apart (pan, back, a pedestal under the pan); aisles keep their steps and no seats
ROW_D = 0.8; SEAT_W = 0.5


def _box(o, t, f, x0, x1, y0, y1, z0, z1, bottom=False):
    """box in a local frame (o origin, t along the row, f toward the field, z up): outward-wound quads + metre uvs"""
    up = Vector((0, 0, 1))
    P_ = lambda x, y, z: o + t * x + f * y + up * z
    lo = [P_(x0, y0, z0), P_(x1, y0, z0), P_(x1, y1, z0), P_(x0, y1, z0)]
    hi = [P_(x0, y0, z1), P_(x1, y0, z1), P_(x1, y1, z1), P_(x0, y1, z1)]
    # (x0,y0)->(x1,y0)->(x1,y1)->(x0,y1) runs anticlockwise from above when t x f points up
    if t.cross(f).z < 0:
        lo = lo[::-1]; hi = hi[::-1]
    F = [hi] + ([lo[::-1]] if bottom else [])
    for i in range(4):
        j = (i + 1) % 4; F.append([lo[i], lo[j], hi[j], hi[i]])
    U = []
    for q in F:
        e = (q[1] - q[0]); h = e.length; e = e.normalized() if h > 0 else e
        n = e.cross(q[-1] - q[0]).normalized() if h > 0 else up
        w = n.cross(e)
        U.append([((p - q[0]).dot(e), (p - q[0]).dot(w)) for p in q])
    return F, U


def terrace(name, A, B, ub, aisle):
    """A front (low) and B back (high) polylines; ub per index: the aisle coordinate (bay units or metres); aisle(u) True
    where the aisle runs. Builds the stepped concrete, then the seats on every tread outside the aisles."""
    dep = sorted(((B[i] - A[i]).to_2d().length for i in range(len(A))))
    n = max(1, int(round(dep[len(dep) // 2] / ROW_D)))
    cols = []  # (a, b, u, s) columns along the strip, s = metres along A
    s_ = 0.0
    for i in range(len(A) - 1):
        m = max(1, int(math.ceil(max((A[i + 1] - A[i]).length, (B[i + 1] - B[i]).length) / 2.0)))
        for k in range(m + (1 if i == len(A) - 2 else 0)):
            x = k / m
            a = A[i].lerp(A[i + 1], x); b = B[i].lerp(B[i + 1], x)
            if cols: s_ += (a - cols[-1][0]).length
            cols.append((a, b, ub[i] + (ub[i + 1] - ub[i]) * x, s_))
    prof = []
    for a, b, u, s in cols:
        P0 = [a.lerp(b, k / n) for k in range(n + 1)]
        pts = [P0[0]]
        for k in range(n):
            pts.append(Vector((P0[k].x, P0[k].y, P0[k + 1].z))); pts.append(P0[k + 1])
        vv = [0.0]
        for k in range(1, len(pts)): vv.append(vv[-1] + (pts[k] - pts[k - 1]).length)
        prof.append((pts, vv, s))
    F = []; T = []
    for c in range(len(prof) - 1):
        (p0, v0, s0), (p1, v1, s1) = prof[c], prof[c + 1]
        for k in range(len(p0) - 1):
            if (p0[k + 1] - p0[k]).length < 1e-4 and (p1[k + 1] - p1[k]).length < 1e-4: continue
            F.append([p0[k], p1[k], p1[k + 1], p0[k + 1]]); T.append([(s0, v0[k]), (s1, v1[k]), (s1, v1[k + 1]), (s0, v0[k + 1])])
    mk(name + '_steps', F, 'concrete', uvs=T)
    # seats: one row per tread, set along a line 0.6 of the way back from the tread's front edge
    SF = []; ST = []; LF = []; LT = []; nseat = 0
    for k in range(n):
        line = []
        for a, b, u, s in cols:
            fr = a.lerp(b, k / n); bk = a.lerp(b, (k + 1) / n); p = fr.lerp(bk, 0.6); p.z = bk.z
            d = (fr - bk).to_2d().length
            line.append((p, u, d, (a - b).to_2d().normalized()))
        L = [0.0]
        for j in range(1, len(line)): L.append(L[-1] + (line[j][0] - line[j - 1][0]).to_2d().length)
        sv = SEAT_W / 2; j = 0; row = []; q = 0
        while sv < L[-1] - SEAT_W / 2:
            while L[j + 1] < sv: j += 1
            x = (sv - L[j]) / max(1e-9, L[j + 1] - L[j])
            p = line[j][0].lerp(line[j + 1][0], x); u = line[j][1] + (line[j + 1][1] - line[j][1]) * x
            sv += SEAT_W; q += 1
            if aisle(u): continue
            d = line[j][2] + (line[j + 1][2] - line[j][2]) * x
            f2 = line[j][3].lerp(line[j + 1][3], x).normalized(); f = Vector((f2.x, f2.y, 0)); t = Vector((0, 0, 1)).cross(f)
            row.append((q, p, t, f, d / 0.8))  # r: tread depth relative to 0.8 m, keeps the seat on its tread
        # as the passed grounds: pan 40 cm, back 36 cm behind the pan with its foot on the pan top (no faces cutting
        # through); one thin galvanised post (4 x 5 cm) under each gap, shared by both seats, and one flush under a row or aisle end
        for m_, (q, p, t, f, r) in enumerate(row):
            for bx in ((-0.20, 0.20, -0.24 * r, 0.20 * r, 0.40, 0.46),       # pan
                       (-0.18, 0.18, -0.30 * r, -0.24 * r, 0.40, 0.86)):     # back, flush on the pan's rear face
                Fb, Tb = _box(p, t, f, *bx, bottom=True); SF += Fb; ST += Tb
            right = m_ + 1 < len(row) and row[m_ + 1][0] == q + 1
            left = m_ > 0 and row[m_ - 1][0] == q - 1
            legs = [(0.23, 0.27) if right else (0.16, 0.20)] + ([] if left else [(-0.20, -0.16)])
            for x0, x1 in legs:
                Fb, Tb = _box(p, t, f, x0, x1, -0.06 * r, -0.01 * r, 0.0, 0.40); LF += Fb; LT += Tb
            nseat += 1
    if SF: mk(name + '_seats', SF, 'seat', uvs=ST)
    if LF: mk(name + '_seatlegs', LF, 'rail', uvs=LT)
    return nseat


NSEAT = 0

# bowl: grass edge -> apron -> fence face -> terraces (walkway where present) -> top band -> outer face
order = P['ring_order']
for si, s_ in enumerate(P['bowl_strips']):
    ka, kb, close = s_[:3]
    A = list(R[ka]); B = list(R[kb]); TH = list(P['ring_th'])
    if P.get('closed', True):
        A.append(R[ka][0]); B.append(R[kb][0]); TH.append(P['ring_th'][0])
    if len(s_) > 3:  # a run of rays [i0, i1]: the bowl changes material round the ground
        A = A[s_[3]:s_[4] + 1]; B = B[s_[3]:s_[4] + 1]; TH = TH[s_[3]:s_[4] + 1]
    if CLOSE[close].get('bay'):
        ph, ba = (s_[5], s_[6]) if len(s_) > 5 else (P['bay_phase'], P['bay_ang'])
        U = [(t - ph) / ba for t in TH]
    else:
        U = arclen(A)
    if close == 'seats':  # aisle where the bay coordinate's fraction is in the painted aisle (first 8% of the bay)
        NSEAT += terrace('bowl_%s_%s_%d' % (ka, kb, si), A, B, U, lambda u: (u % 1.0) < 0.08)
        continue
    F, T = strip_uv(A, B, U, P.get('step', 2.0))
    mk('bowl_%s_%s_%d' % (ka, kb, si), F, close, uvs=T)

# field
fe = [V(p) for p in P['field_ring']] if 'field_ring' in P else R['grass']
C0 = V((P['centre'][0], P['centre'][1], fe[0].z)); NS = 50
def fr(i, k):
    return C0.lerp(fe[i % len(fe)], k / NS)
bm_f = [[fr(i, 0), fr(i + 1, 1), fr(i, 1)] for i in range(0)]
for i in range(len(fe)):
    bm_f.append([fr(i, 0), fr(i, 1), fr(i + 1, 1)])
    for k in range(1, NS):
        bm_f.append([fr(i, k), fr(i, k + 1), fr(i + 1, k + 1), fr(i + 1, k)])
ca_, sa_ = math.cos(P.get('field_axis', 0.0)), math.sin(P.get('field_axis', 0.0))
fuv = [[((p - C0).x * ca_ + (p - C0).y * sa_, -(p - C0).x * sa_ + (p - C0).y * ca_) for p in f] for f in bm_f]
if not P.get('no_field'):
    mk('field', bm_f, 'grass_field' if 'grass_field' in CLOSE else 'grass', uvs=fuv)

# flat ground polygons (concave allowed), world-metre uvs turned by 'rot'
for fl in P.get('flats', []):
    bm = bmesh.new(); vs = [bm.verts.new(V(q)) for q in fl['poly']]; bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='EAR_CLIP')
    for f in bm.faces:
        if f.normal.z < 0: f.normal_flip()
    cr, sr = math.cos(fl['rot']), math.sin(fl['rot'])
    F = [[v.co.copy() for v in f.verts] for f in bm.faces]; bm.free()
    T = [[(q.x * cr + q.y * sr - fl.get('uoff', 0.0), -q.x * sr + q.y * cr) for q in f] for f in F]
    mk(fl['name'], F, fl['close'], uvs=T)


# generic polyline lofts and boxes from parts.json
for s in P.get('lofts', []):
    A = [V(p) for p in s['a']]; B = [V(p) for p in s['b']]
    if s['close'] == 'seats_m':  # covered stand: an aisle 1.2 m wide every 15 m along the stand
        NSEAT += terrace(s['name'], A, B, arclen(A), lambda u: (u % 15.0) < 1.2)
        continue
    F, T = strip_uv(A, B, arclen(A), s.get('step', 2.0))
    mk(s['name'], F, s['close'], uvs=T)


def box_faces(c, hx, hy, z0, z1, yaw, top=True):
    ca, sa = math.cos(yaw), math.sin(yaw)
    pts = [Vector((c[0] + ca * x - sa * y, c[1] + sa * x + ca * y, 0)) for x, y in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))]
    lo = [p + Vector((0, 0, z0)) for p in pts]; hi = [p + Vector((0, 0, z1)) for p in pts]
    f = [list(reversed(lo))] + ([hi] if top else [])
    for i in range(4):
        j = (i + 1) % 4
        f += grid(lo[i], lo[j], hi[i], hi[j])
    out = []
    for q in f:
        if len(q) == 4 and (q[1] - q[0]).length > 2.5:
            out += grid(q[0], q[1], q[3], q[2])
        else:
            out.append(q)
    return out


for b in P.get('boxes', []):
    BF = box_faces(b['c'], b['hx'], b['hy'], b['z0'], b['z1'], b['yaw'], 'top' not in b)
    if b.get('fuv'):  # per-face uvs: along the face and up (vertical faces), plan x/y (flat faces), in metres
        U = []
        for q in BF:
            nrm = (q[1] - q[0]).cross(q[-1] - q[0])
            if abs(nrm.z) > 0.7 * nrm.length:
                U.append([(v.x, v.y) for v in q])
            else:
                t = Vector((-nrm.y, nrm.x, 0)).normalized()
                U.append([(v.dot(t), v.z) for v in q])
        mk(b['name'], BF, b['close'], uvs=U)
    else:
        mk(b['name'], BF, b['close'])
    if 'top' in b:  # flat roof in its own material
        ca, sa = math.cos(b['yaw']), math.sin(b['yaw'])
        hi = [Vector((b['c'][0] + ca * x - sa * y, b['c'][1] + sa * x + ca * y, b['z1'])) for x, y in ((-b['hx'], -b['hy']), (b['hx'], -b['hy']), (b['hx'], b['hy']), (-b['hx'], b['hy']))]
        mk(b['name'] + '_top', grid(hi[0], hi[1], hi[3], hi[2]), b['top'])


def tube(p, q, r0, r1, seg=16):
    p = Vector(p); q = Vector(q); d = (q - p)
    ax = d.normalized(); t = ax.orthogonal().normalized(); u = ax.cross(t)
    n = max(1, int(d.length / 2.0))
    rings = []
    for k in range(n + 1):
        c = p + d * (k / n); r = r0 + (r1 - r0) * k / n
        rings.append([c + (t * math.cos(2 * math.pi * i / seg) + u * math.sin(2 * math.pi * i / seg)) * r for i in range(seg)])
    f = []
    for k in range(n):
        for i in range(seg):
            j = (i + 1) % seg
            f.append([rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]])
    f.append(list(reversed(rings[0]))); f.append(rings[-1])
    C = 2 * math.pi * (r0 + r1) / 2; L = d.length
    uv = []
    for k in range(n):
        for i in range(seg):
            uv.append([(C * i / seg, L * k / n), (C * (i + 1) / seg, L * k / n), (C * (i + 1) / seg, L * (k + 1) / n), (C * i / seg, L * (k + 1) / n)])
    uv.append([(C * math.cos(2 * math.pi * i / seg) * 0.1, C * math.sin(2 * math.pi * i / seg) * 0.1) for i in reversed(range(seg))])
    uv.append([(C * math.cos(2 * math.pi * i / seg) * 0.1, C * math.sin(2 * math.pi * i / seg) * 0.1) for i in range(seg)])
    return f, uv


for t in P.get('tubes', []):
    F, T = tube(t['p'], t['q'], t['r0'], t['r1'], t.get('seg', 16))
    mk(t['name'], F, t['close'], uvs=T)

# ---------------------------------------------------------------- texture assignment
deps = bpy.context.evaluated_depsgraph_get()
allv = []; allf = []
for o, _, _ in PARTS:
    base = len(allv)
    allv += [v.co.copy() for v in o.data.vertices]
    allf += [[base + i for i in p.vertices] for p in o.data.polygons]
BVH = BVHTree.FromPolygons(allv, allf, epsilon=0.0)
MIN_COS = P.get('min_cos', 0.30)
stats = {}
for o, close, bay in PARTS:
    me = o.data
    if bay == 'preset' and NOPH:
        me.materials.append(CLOSE[close]['mat'])
        stats['hand_' + close] = stats.get('hand_' + close, 0) + len(me.polygons)
        continue
    if not NOPH:
        for c in CAMS:
            me.materials.append(MATS['photo_' + c['name']])
    me.materials.append(CLOSE[close]['mat'])
    uv = me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        ctr = poly.center; n = poly.normal
        best = None
        for ci, c in enumerate([] if NOPH else CAMS):
            to = c['C'] - ctr; dist = to.length; to.normalize()
            cs = abs(n.dot(to))
            if cs < MIN_COS:
                continue
            hit = BVH.ray_cast(ctr + to * 0.05, to, dist)
            if hit[0] is not None:
                continue
            (pu, pv), z = project(c, ctr)
            if not (2 < pu < c['W'] - 2 and 2 < pv < c['H'] - 2):
                continue
            score = cs * c['f'] / dist
            if best is None or score > best[0]:
                best = (score, ci)
            if P.get('first_cam_wins', True):
                break  # cameras are listed reference first: the reference photo wins wherever it sees the face
        if best:
            ci = best[1]; c = CAMS[ci]; poly.material_index = ci
            for li in poly.loop_indices:
                (pu, pv), _ = project(c, me.vertices[me.loops[li].vertex_index].co)
                uv.data[li].uv = (pu / c['W'], 1 - pv / c['H'])
            stats[c['name']] = stats.get(c['name'], 0) + 1
        else:
            poly.material_index = 0 if NOPH else len(CAMS)
            cl = CLOSE[close]
            # world-metre mapping: u along the face's horizontal run (or x for flat faces), v up; one texture per bay
            for li in poly.loop_indices:
                X = me.vertices[me.loops[li].vertex_index].co
                if abs(n.z) > 0.7:
                    uu, vv = X.x, X.y
                else:
                    h = Vector((-n.y, n.x, 0)).normalized()
                    uu, vv = h.dot(X), X.z
                uv.data[li].uv = (uu / cl['w'], (vv - cl.get('v0', 0.0)) / cl['h'])
            stats['hand_' + close if NOPH else 'close_' + close] = stats.get('close_' + close, 0) + 1
print('FACES', stats, 'SEATS', NSEAT)

out = os.path.abspath(a[1])
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_image_format='JPEG', export_jpeg_quality=95)

# ---------------------------------------------------------------- matched render, lit by the measured sun (bearing 301, 28 deg up)
az, el = math.radians(301.0), math.radians(28.0)
to_sun = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 4.0; sd.angle = math.radians(0.6)
so = bpy.data.objects.new('sun', sd); S.collection.objects.link(so)
so.rotation_euler = to_sun.to_track_quat('Z', 'Y').to_euler()
w = bpy.data.worlds.new('w'); S.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.65, 0.85, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
S.render.engine = 'CYCLES'; S.cycles.device = 'CPU'; S.cycles.samples = 24; S.cycles.use_denoising = True
S.render.threads_mode = 'FIXED'; S.render.threads = 8; S.render.film_transparent = True
S.view_settings.view_transform = 'Standard'
for k, c in enumerate(CAMS):
    if len(a) <= 2 + k:
        break
    cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
    cd.lens = c['f'] * 36 / c['W']; cd.clip_end = 5000
    co = bpy.data.objects.new('cam' + c['name'], cd); S.collection.objects.link(co); S.camera = co
    R3 = Matrix((c['M'][0], c['M'][1], -c['M'][2])).transposed()
    co.matrix_world = Matrix.Translation(c['C']) @ R3.to_4x4()
    S.render.resolution_x = c['W']; S.render.resolution_y = c['H']
    S.render.filepath = os.path.abspath(a[2 + k])
    bpy.ops.render.render(write_still=True)
