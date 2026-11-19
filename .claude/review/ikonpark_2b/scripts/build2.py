# Ikon Park exterior builder, world metres (x east, y north, z up).
# usage: blender -b -P build.py -- GEOM.json OUT.glb TEXDIR
import bpy, bmesh, sys, json, math
from mathutils import Vector
gj, dst, tex = sys.argv[sys.argv.index('--') + 1:]
G = json.load(open(gj))
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('ikon')
ob = bpy.data.objects.new('ikonpark', me)
bpy.context.scene.collection.objects.link(ob)


def mat(name, rough=0.9):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(tex + '/' + name + '.png')
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    me.materials.append(m)
    return len(me.materials) - 1


MN = ['grass', 'park', 'asphalt', 'seats', 'terrace', 'brick', 'roof', 'sawtooth', 'wood', 'white', 'greyroof',
      'under', 'pool', 'yellow', 'red', 'orange', 'steel', 'concrete', 'glass', 'glassdark', 'timber',
      'brickdark', 'seatslegends', 'roofgrey', 'steeldark']
TILE = {'brick': 2, 'brickdark': 2, 'timber': 2, 'wood': 2, 'glass': 3, 'glassdark': 3, 'grass': 20, 'park': 20,
        'asphalt': 10}
M = {n: mat(n) for n in MN}
bm = bmesh.new()
uv = bm.loops.layers.uv.new()


def face(pts, m, uvs=None, scale=None):
    if scale is None:
        scale = TILE.get(m, 4.0)
    vs = [bm.verts.new(p) for p in pts]
    f = bm.faces.new(vs)
    f.material_index = M[m]
    if uvs is None:
        f.normal_update()
        n = f.normal
        for l in f.loops:
            p = l.vert.co
            if abs(n.z) > 0.7:
                l[uv].uv = (p.x / scale, p.y / scale)
            elif abs(n.x) > abs(n.y):
                l[uv].uv = (p.y / scale, p.z / scale)
            else:
                l[uv].uv = (p.x / scale, p.z / scale)
    else:
        for l, u in zip(f.loops, uvs):
            l[uv].uv = u
    return f


def V(p, z=None):
    return Vector((p[0], p[1], p[2] if z is None else z))


C = Vector((G['centre'][0], G['centre'][1], 0))


def outward(f, ref):
    f.normal_update()
    c = f.calc_center_median()
    if (c - ref).dot(f.normal) < 0:
        f.normal_flip()


def upward(f, up=True):
    f.normal_update()
    if (f.normal.z > 0) != up:
        f.normal_flip()


def pol(p):
    d = Vector((p[0], p[1], 0)) - C
    return math.atan2(d.y, d.x), d.length


NA = 360


def periodic_interp(samples):
    s = sorted(samples)
    out = []
    for i in range(NA):
        t = -math.pi + 2 * math.pi * (i + 0.5) / NA
        lo = None
        hi = None
        for (a, v) in s:
            if a <= t:
                lo = (a, v)
        for (a, v) in s:
            if a >= t:
                hi = (a, v)
                break
        if lo is None:
            lo = (s[-1][0] - 2 * math.pi, s[-1][1])
        if hi is None:
            hi = (s[0][0] + 2 * math.pi, s[0][1])
        w = 0 if hi[0] == lo[0] else (t - lo[0]) / (hi[0] - lo[0])
        out.append(tuple(lo[1][j] + (hi[1][j] - lo[1][j]) * w for j in range(len(lo[1]))))
    return out


# fence line: OSM pitch outline pushed out by the offset fitted to the photo's grass edge
P = G['pitch']
cp = Vector((sum(p[0] for p in P) / len(P), sum(p[1] for p in P) / len(P), 0))
fs = []
for p in P:
    d = Vector((p[0], p[1], 0)) - cp
    q = Vector((p[0], p[1], 0)) + d.normalized() * G['grass_offset']
    fs.append(pol(q))
fence = periodic_interp([(a, (r,)) for a, r in fs])
STANDS = G['stands']


def _span(P):
    a = [pol(p)[0] for p in P]
    u = [a[0]]
    for x in a[1:]:
        d = x - u[-1]
        d -= 2 * math.pi * round(d / (2 * math.pi))
        u.append(u[-1] + d)
    return min(u), max(u)


def _near_corners(poly):
    # corners of a block seen from the centre: the seat bowl runs up to these faces only
    out = []
    for p in poly:
        a, r = pol(p)
        dx, dy = math.cos(a), math.sin(a)
        best = r
        for k in range(len(poly)):
            p0, p1 = poly[k], poly[(k + 1) % len(poly)]
            ex, ey = p1[0] - p0[0], p1[1] - p0[1]
            den = dx * ey - dy * ex
            if abs(den) < 1e-9:
                continue
            ox, oy = p0[0] - C.x, p0[1] - C.y
            t = (ox * ey - oy * ex) / den
            s_ = (ox * dy - oy * dx) / den
            if 0 <= s_ <= 1 and t > 0.01:
                best = min(best, t)
        if r <= best + 0.05:
            out.append(p)
    return out


standspan = [_span(G[n]['back']) for n in STANDS]


def _instand(a):
    return any(a0 - 1e-6 <= a + k * 2 * math.pi <= a1 + 1e-6 for a0, a1 in standspan for k in (-1, 0, 1))


outer = []
for n in STANDS:
    for p in G[n]['back']:
        a, r = pol(p)
        outer.append((a, (r, p[2] - G[n].get('seatdrop', 3.0))))
for p in G.get('terrace', []):
    a, r = pol(p)
    outer.append((a, (r, p[2])))
for n in G.get('bowlblocks', []):
    # a block shapes the seats only where no stand stands (the stand's seats run past it)
    for p in _near_corners(G['blocks'][n]['poly']):
        a, r = pol(p)
        if not _instand(a):
            outer.append((a, (r, G['blocks'][n].get('z0', 5.0))))
# stand ends: the seats in a gap between two stands sit at the lower end's level, so the step is at the
# stand end (one sector wide) instead of a ramp across the whole gap
_ends = []
for n in STANDS:
    for p in (G[n]['back'][0], G[n]['back'][-1]):
        a, r = pol(p)
        _ends.append((a, r, p[2] - G[n].get('seatdrop', 3.0), n))
_ends.sort()
_del = math.radians(0.6)
for k in range(len(_ends)):
    a1, r1, z1, n1 = _ends[k]
    a2, r2, z2, n2 = _ends[(k + 1) % len(_ends)]
    gap = (a2 - a1) % (2 * math.pi)
    if n1 == n2 or gap < 2.5 * _del:
        continue
    ins = [v for a, v in outer if 0 < (a - a1) % (2 * math.pi) < gap]
    if len(ins) > 3:
        continue
    lr, lz = min([(r1, z1), (r2, z2)] + ins, key=lambda v: v[1])
    outer.append((a1 + _del, (lr, lz)))
    outer.append((a2 - _del, (lr, lz)))
ob_ = periodic_interp(outer)


def pt(i, r, z):
    t = -math.pi + 2 * math.pi * (i + 0.5) / NA
    return Vector((C.x + r * math.cos(t), C.y + r * math.sin(t), z))


standang = []
for n in STANDS:
    a = [pol(p)[0] for p in G[n]['back']]
    u = [a[0]]
    for x in a[1:]:
        d = x - u[-1]
        d -= 2 * math.pi * round(d / (2 * math.pi))
        u.append(u[-1] + d)
    standang.append((min(u), max(u)))


def _inspan(t, a0, a1):
    return any(a0 <= t + k * 2 * math.pi <= a1 for k in (-1, 0, 1))


def understand(i):
    t = -math.pi + 2 * math.pi * (i + 0.5) / NA
    return any(_inspan(t, a0, a1) for a0, a1 in standang)


def seatmat(i):
    t = -math.pi + 2 * math.pi * (i + 0.5) / NA
    for n, (a0, a1) in zip(STANDS, standang):
        if _inspan(t, a0, a1):
            return G[n].get('seatmat', 'seats')
    return 'terrace'


def tier_w(i):
    t = -math.pi + 2 * math.pi * (i + 0.5) / NA
    tj = t + 2 * math.pi / NA
    for n, (a0, a1) in zip(STANDS, standang):
        tr = G[n].get('tier')
        if tr and _inspan(t, a0, a1) and _inspan(tj, a0, a1):
            A = [p[0] for p in tr['pts']]
            W = [p[1] for p in tr['pts']]

            def wat(x):
                x = x - 2 * math.pi * round((x - A[0]) / (2 * math.pi))
                if x <= A[0]:
                    return W[0]
                if x >= A[-1]:
                    return W[-1]
                for q in range(len(A) - 1):
                    if A[q] <= x <= A[q + 1]:
                        return W[q] + (W[q + 1] - W[q]) * (x - A[q]) / (A[q + 1] - A[q])
            sm = None
            for s0, s1, mm in tr.get('signs', []):
                lo, hi = min(s0, s1), max(s0, s1)
                if lo <= t + math.pi / NA <= hi:
                    sm = mm
            return (wat(t), wat(tj)), tr.get('rise', 1.0), sm
    return None


for i in range(NA):
    j = (i + 1) % NA
    rf0, rf1 = fence[i][0], fence[j][0]
    ro0, zo0 = ob_[i]
    ro1, zo1 = ob_[j]
    # no playing surface: the game draws the turf (lead 2026-11-18)
    f = face([pt(i, rf0, 0), pt(j, rf1, 0), pt(j, rf1, 1.1), pt(i, rf0, 1.1)], 'white')
    outward(f, C)
    m = seatmat(i)
    rows = max(1, round(math.hypot(ro0 - rf0, zo0 - 1.1) / 0.8)) / 4
    a0 = 2 * math.pi * rf0 / NA
    tw = tier_w(i)
    if tw is None:
        f = face([pt(i, rf0, 1.1), pt(j, rf1, 1.1), pt(j, ro1, zo1), pt(i, ro0, zo0)], m,
                 uvs=[(i * a0 / 4, 0), ((i + 1) * a0 / 4, 0), ((i + 1) * a0 / 4, rows), (i * a0 / 4, rows)])
        upward(f)
    else:
        (wi, wj), rise, sm = tw
        rbi, rbj = rf0 + (ro0 - rf0) * wi, rf1 + (ro1 - rf1) * wj
        zbi, zbj = 1.1 + (zo0 - 1.1) * wi, 1.1 + (zo1 - 1.1) * wj
        r1 = max(1, round(math.hypot(rbi - rf0, zbi - 1.1) / 0.8)) / 4
        r2 = max(1, round(math.hypot(ro0 - rbi, zo0 - zbi - rise) / 0.8)) / 4
        f = face([pt(i, rf0, 1.1), pt(j, rf1, 1.1), pt(j, rbj, zbj), pt(i, rbi, zbi)], m,
                 uvs=[(i * a0 / 4, 0), ((i + 1) * a0 / 4, 0), ((i + 1) * a0 / 4, r1), (i * a0 / 4, r1)])
        upward(f)
        f = face([pt(i, rbi, zbi), pt(j, rbj, zbj), pt(j, rbj, zbj + rise), pt(i, rbi, zbi + rise)], 'white')
        outward(f, Vector((C.x, C.y, zbi)))
        if sm:
            g = face([pt(i, rbi - 0.05, zbi + 0.1), pt(j, rbj - 0.05, zbj + 0.1),
                      pt(j, rbj - 0.05, zbj + rise - 0.1), pt(i, rbi - 0.05, zbi + rise - 0.1)], sm)
            outward(g, Vector((C.x, C.y, zbi)))
        f = face([pt(i, rbi, zbi + rise), pt(j, rbj, zbj + rise), pt(j, ro1, zo1), pt(i, ro0, zo0)], m,
                 uvs=[(i * a0 / 4, 0), ((i + 1) * a0 / 4, 0), ((i + 1) * a0 / 4, r2), (i * a0 / 4, r2)])
        upward(f)
    if seatmat(i) != 'seatslegends':
        f = face([pt(i, ro0, 0), pt(j, ro1, 0), pt(j, ro1, zo1), pt(i, ro0, zo0)],
                 'brick' if understand(i) else 'wood')
        outward(f, C)
# no park disc: the model stops at the stadium (director 2026-11-18)


def box(p0, p1, w, m):
    h = p1.z - p0.z
    x, y = p0.x, p0.y
    s = w / 2
    q = [Vector((x - s, y - s, p0.z)), Vector((x + s, y - s, p0.z)), Vector((x + s, y + s, p0.z)),
         Vector((x - s, y + s, p0.z))]
    for a in range(4):
        b_ = (a + 1) % 4
        f = face([q[a], q[b_], q[b_] + Vector((0, 0, h)), q[a] + Vector((0, 0, h))], m)
        outward(f, Vector((x, y, p0.z)))
    f = face([v + Vector((0, 0, h)) for v in q], m)
    upward(f)


def stand(n, thick=1.2, masts=False, band=None, facade=None):
    F = [V(p) for p in G[n]['front']]
    B = [V(p) for p in G[n]['back']]
    L = 0.0
    d = Vector((0, 0, -thick))
    for k in range(len(F) - 1):
        f0, f1, b0, b1 = F[k], F[k + 1], B[k], B[k + 1]
        seg = (f1 - f0).length
        u0 = L / 4
        u1 = (L + seg) / 4
        L += seg
        dep = ((f0 - b0).length + (f1 - b1).length) / 8
        f = face([f0, f1, b1, b0], G[n].get('roofmat', 'roof'), uvs=[(u0, 0), (u1, 0), (u1, dep), (u0, dep)])
        upward(f)
        f = face([f0 + d, f1 + d, b1 + d, b0 + d], 'under')
        upward(f, False)
        f = face([f0, f1, f1 + d, f0 + d], band if band else 'white')
        outward(f, (b0 + b1) / 2)
        f = face([b0, b1, b1 + d, b0 + d], 'white')
        outward(f, (f0 + f1) / 2)
        g0, g1 = Vector((b0.x, b0.y, 0)), Vector((b1.x, b1.y, 0))
        if facade == 'legends':
            s0, s1 = L - seg, L
            z0, z1 = (b0 + d).z, (b1 + d).z
            for (za, zb_, mm) in ((0, 3.6, 'glassdark'), (3.6, None, 'concrete')):
                ta, tb = Vector((0, 0, za)), Vector((0, 0, zb_ if zb_ else 0))
                if zb_ is None:
                    pts = [g0 + ta, g1 + ta, b1 + d, b0 + d]
                    uvs = [(s0 / 4, za / 4), (s1 / 4, za / 4), (s1 / 4, z1 / 4), (s0 / 4, z0 / 4)]
                else:
                    pts = [g0 + ta, g1 + ta, g1 + tb, g0 + tb]
                    uvs = [(s0 / 4, za / 4), (s1 / 4, za / 4), (s1 / 4, zb_ / 4), (s0 / 4, zb_ / 4)]
                f = face(pts, mm, uvs=uvs)
                outward(f, C)
        elif facade == 'band':
            bh = G[n].get('bandh', 3.0)
            t0, t1 = b0 + d, b1 + d
            m0, m1 = t0 - Vector((0, 0, bh)), t1 - Vector((0, 0, bh))
            f = face([g0, g1, m1, m0], 'brick')
            outward(f, C)
            s0, s1 = L - seg, L
            f = face([m0, m1, t1, t0], 'glassdark', uvs=[(s0 / 3, 0), (s1 / 3, 0), (s1 / 3, bh / 3), (s0 / 3, bh / 3)])
            outward(f, C)
        elif facade == 'posts':
            s0, s1 = L - seg, L
            z0, z1 = (b0 + d).z, (b1 + d).z
            f = face([g0, g1, b1 + d, b0 + d], G[n].get('wallmat', 'timber'),
                     uvs=[(s0 / 4, 0), (s1 / 4, 0), (s1 / 4, z1 / 4), (s0 / 4, z0 / 4)])
            outward(f, C)
        else:
            f = face([g0, g1, b1 + d, b0 + d], 'brick')
            outward(f, C)
        if G[n].get('ridge'):
            r = G[n]['ridge']
            w = 0.25 / max(0.5, ((f0 - b0).length + (f1 - b1).length) / 2)
            q = [f0.lerp(b0, r - w), f1.lerp(b1, r - w), f1.lerp(b1, r + w), f0.lerp(b0, r + w)]
            f = face([v + Vector((0, 0, 0.04)) for v in q], 'steeldark')
            upward(f)
    for e0, e1 in ((F[0], B[0]), (F[-1], B[-1])):
        face([e0, e1, e1 + d, e0 + d], 'white')
    if masts and G[n].get('mastidx'):
        for k in G[n]['mastidx']:
            b = B[k]
            box(b, b + Vector((0, 0, G[n].get('masth', 3.5))), 0.35, 'steel')
    elif masts:
        acc = 0.0
        for k in range(len(B) - 1):
            acc += (B[k + 1] - B[k]).length
            if acc > 10:
                acc = 0
                b = B[k]
                box(b, b + Vector((0, 0, 3.5)), 0.35, 'steel')


def beam(p0, p1, w, m):
    ax = (p1 - p0)
    if ax.length < 1e-6:
        return
    a = ax.normalized()
    up = Vector((0, 0, 1)) if abs(a.z) < 0.9 else Vector((1, 0, 0))
    s1 = a.cross(up).normalized() * (w / 2)
    s2 = a.cross(s1).normalized() * (w / 2)
    q0 = [p0 + s1 + s2, p0 - s1 + s2, p0 - s1 - s2, p0 + s1 - s2]
    q1 = [v + ax for v in q0]
    cen = (p0 + p1) / 2
    for k in range(4):
        f = face([q0[k], q0[(k + 1) % 4], q1[(k + 1) % 4], q1[k]], m)
        outward(f, cen)
    for q in (q0, q1):
        f = face(q, m)
        outward(f, cen)


def legends_steel(n):
    s = G[n]
    F = [V(p) for p in s['front']]
    B = [V(p) for p in s['back']]
    # roof trusses, front to back, every s['truss'] metres along the front edge; a back column under each
    acc = s['truss'] / 2
    for k in range(len(F) - 1):
        seg = (F[k + 1] - F[k]).length
        t = acc
        while t < seg:
            w_ = t / seg
            f = F[k].lerp(F[k + 1], w_)
            b = B[k].lerp(B[k + 1], w_)
            lift = Vector((0, 0, 0.7))
            beam(f + lift, b + lift, 0.35, 'steeldark')
            beam(f + Vector((0, 0, 0.1)), b + Vector((0, 0, 0.1)), 0.25, 'steeldark')
            beam(Vector((b.x, b.y, 0)), b - Vector((0, 0, s.get('thick', 1.2))), 0.5, 'white')
            t += s['truss']
        acc = t - seg
    # masts: A-frame on the back edge, forward ties into the roof, back-stays to the ground
    Cb = Vector((C.x, C.y, 0))
    for m in s.get('mastlist', []):
        i = m['i']
        b = B[i]
        j0, j1 = max(0, i - 1), min(len(B) - 1, i + 1)
        along = (B[j1] - B[j0]).normalized()
        outv = Vector((b.x, b.y, 0)) - Cb
        outv.z = 0
        outv.normalize()
        apex = b + Vector((0, 0, m['h']))
        for sgn in (-1, 1):
            beam(b + along * (2.5 * sgn), apex, 0.4, 'steel')
        fi = F[min(i, len(F) - 1)]
        for w_ in (0.35, 0.7):
            beam(apex, b.lerp(fi, w_) + Vector((0, 0, 0.2)), 0.12, 'steel')
        for sgn in (-1, 1):
            g = Vector((b.x, b.y, 0)) + outv * 7 + along * (4 * sgn)
            beam(apex, g, 0.12, 'steel')


def seat_z(x, y):
    a, r = pol((x, y))
    i = int((a + math.pi) / (2 * math.pi) * NA) % NA
    rf = fence[i][0]
    ro, zo = ob_[i]
    w = 0 if ro == rf else (r - rf) / (ro - rf)
    return 1.1 + (zo - 1.1) * max(0, min(1, w))


def front_posts(n, every=14.0, thick=1.2):
    F = [V(p) for p in G[n]['front']]
    acc = 0.0
    for k in range(len(F) - 1):
        acc += (F[k + 1] - F[k]).length
        if acc >= every:
            acc = 0
            f = F[k]
            box(Vector((f.x, f.y, seat_z(f.x, f.y))), Vector((f.x, f.y, f.z - thick)), 0.4, 'steel')


def sawtooth_roof(n):
    s = G[n]
    F = [V(p) for p in s['front']]
    B = [V(p) for p in s['back']]
    Ls = [0.0]
    for k in range(len(F) - 1):
        Ls.append(Ls[-1] + (F[k + 1] - F[k]).length)
    tot = Ls[-1]

    def at(P, t):
        x = t * tot
        for k in range(len(P) - 1):
            if x <= Ls[k + 1] or k == len(P) - 2:
                w = (x - Ls[k]) / max(1e-6, Ls[k + 1] - Ls[k])
                return P[k].lerp(P[k + 1], min(1.0, max(0.0, w)))
    bd = [0.0] + s['sawtooth']['bounds'] + [1.0]
    h = s['sawtooth']['h']
    up = Vector((0, 0, 0.06))
    for i in range(len(bd) - 1):
        t0, t1 = bd[i], bd[i + 1]
        if t1 - t0 < 1e-4:
            continue
        N = 4
        for j in range(N):
            a, b = t0 + (t1 - t0) * j / N, t0 + (t1 - t0) * (j + 1) / N
            la, lb = h * j / N, h * (j + 1) / N
            fa, fb, ba, bb = at(F, a), at(F, b), at(B, a), at(B, b)
            za, zb = Vector((0, 0, la)) + up, Vector((0, 0, lb)) + up
            ua, ub = a * tot / 4, b * tot / 4
            dep = (fa - ba).length / 4
            f = face([fa + za, fb + zb, bb + zb, ba + za], 'roof', uvs=[(ua, 0), (ub, 0), (ub, dep), (ua, dep)])
            upward(f)
            cr = s['sawtooth'].get('crease')
            if cr:
                q = [fa.lerp(ba, cr - 0.012) + za, fb.lerp(bb, cr - 0.012) + zb,
                     fb.lerp(bb, cr + 0.012) + zb, fa.lerp(ba, cr + 0.012) + za]
                f = face([v + Vector((0, 0, 0.03)) for v in q], 'steeldark')
                upward(f)
            # front and back fascia of the ramp
            for p0, p1 in ((fa, fb), (ba, bb)):
                face([p0 + up, p1 + up, p1 + zb, p0 + za], 'white')
        fe, be = at(F, t1), at(B, t1)
        f = face([fe + up, be + up, be + up + Vector((0, 0, h)), fe + up + Vector((0, 0, h))], 'steeldark')


for n in STANDS:
    s = G[n]
    stand(n, s.get('thick', 1.2), s.get('masts', False), s.get('band'), s.get('facade'))
    if s.get('posts'):
        front_posts(n, thick=s.get('thick', 1.2))
    if s.get('sawtooth'):
        sawtooth_roof(n)
    if s.get('facade') == 'legends':
        legends_steel(n)
    if s.get('facade') == 'posts':
        Bq = [V(p) for p in s['back']]
        acc = 0.0
        for k in range(len(Bq) - 1):
            acc += (Bq[k + 1] - Bq[k]).length
            if acc >= s.get('postevery', 5.0):
                acc = 0
                b = Bq[k] - Vector((0, 0, s.get('thick', 1.2)))
                o = Vector((b.x - C.x, b.y - C.y, 0)).normalized() * 0.15
                beam(Vector((b.x, b.y, 0)) + o, b + o, 0.3, s.get('postmat', 'concrete'))
    if s.get('facade') == 'band':
        Bq = [V(p) for p in s['back']]
        acc = 0.0
        for k in range(len(Bq) - 1):
            acc += (Bq[k + 1] - Bq[k]).length
            if acc >= s.get('postevery', 12.0):
                acc = 0
                b = Bq[k] - Vector((0, 0, s.get('thick', 1.2)))
                o = Vector((b.x - C.x, b.y - C.y, 0)).normalized() * 0.2
                beam(b + o - Vector((0, 0, s.get('bandh', 3.0))), b + o, 0.4, 'white')
for n in STANDS:
    if not G[n].get('fascia'):
        continue
    F = [V(p) for p in G[n]['front']]
    B = [V(p) for p in G[n]['back']]
    th = G[n].get('thick', 1.2)
    Ls = [0.0]
    for k in range(len(F) - 1):
        Ls.append(Ls[-1] + (F[k + 1] - F[k]).length)
    tot = Ls[-1]
    for t0, t1, mm in G[n]['fascia']:
        lo, hi = t0 * tot, t1 * tot
        for k in range(len(F) - 1):
            x0, x1 = max(lo, Ls[k]), min(hi, Ls[k + 1])
            if x1 <= x0:
                continue
            w0 = (x0 - Ls[k]) / (Ls[k + 1] - Ls[k])
            w1 = (x1 - Ls[k]) / (Ls[k + 1] - Ls[k])
            fa, fb = F[k].lerp(F[k + 1], w0), F[k].lerp(F[k + 1], w1)
            ba = B[k].lerp(B[k + 1], w0)
            o = (fa - ba)
            o.z = 0
            o = o.normalized() * 0.05
            f = face([fa + o + Vector((0, 0, -th + 0.15)), fb + o + Vector((0, 0, -th + 0.15)),
                      fb + o - Vector((0, 0, 0.15)), fa + o - Vector((0, 0, 0.15))], mm)
            outward(f, ba)
if 'fosters' in G and G['fosters'].get('sign'):
    sg = G['fosters']['sign']
    F = [V(p) for p in G['fosters']['front']]
    B = [V(p) for p in G['fosters']['back']]
    Ls = [0.0]
    for k in range(len(F) - 1):
        Ls.append(Ls[-1] + (F[k + 1] - F[k]).length)
    tot = Ls[-1]
    lo, hi = sg['t0'] * tot, sg['t1'] * tot
    for k in range(len(F) - 1):
        x0, x1 = max(lo, Ls[k]), min(hi, Ls[k + 1])
        if x1 <= x0:
            continue
        w0 = (x0 - Ls[k]) / (Ls[k + 1] - Ls[k])
        w1 = (x1 - Ls[k]) / (Ls[k + 1] - Ls[k])
        fa, fb = F[k].lerp(F[k + 1], w0), F[k].lerp(F[k + 1], w1)
        ba, bb = B[k].lerp(B[k + 1], w0), B[k].lerp(B[k + 1], w1)
        up = Vector((0, 0, 0.05))
        ua, ub = (x0 - lo) / (hi - lo), (x1 - lo) / (hi - lo)
        f = face([fa.lerp(ba, sg['d0']) + up, fb.lerp(bb, sg['d0']) + up, fb.lerp(bb, sg['d1']) + up,
                  fa.lerp(ba, sg['d1']) + up], sg['mat'], uvs=[(ua, 0), (ub, 0), (ub, 1), (ua, 1)])
        upward(f)


def block(poly, z, wall='brick', roofm='greyroof', win=None, facemat=None, z0=0.0):
    # z0: the base, for a block that sits on the seating instead of the ground
    P = [Vector((p[0], p[1], z0)) for p in poly]
    z = z - z0
    cen = sum(P, Vector()) / len(P)
    best = None
    if facemat:
        best = max(range(len(P)), key=lambda q: -((P[q] + P[(q + 1) % len(P)]) / 2 - Vector((C.x, C.y, 0))).length)
    for k in range(len(P)):
        a, b = P[k], P[(k + 1) % len(P)]
        if k == best:
            f = face([a, b, b + Vector((0, 0, z)), a + Vector((0, 0, z))], facemat, uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
            outward(f, cen)
            if f.normal.dot(f.calc_center_median() - cen) < 0:
                pass
            continue
        f = face([a, b, b + Vector((0, 0, z)), a + Vector((0, 0, z))], wall)
        outward(f, cen)
        if win:
            mid = (a + b) / 2
            nrm = f.normal.copy()
            if (Vector((mid.x - C.x, mid.y - C.y, 0))).dot(nrm) <= 0:
                continue  # windows only on walls facing away from the ground, the side the photo shows
            e = b - a
            Lw = e.length
            ed = e.normalized()
            cnt = int((Lw - 1.0) // win['spacing'])
            off = (Lw - (cnt - 1) * win['spacing']) / 2
            for c in range(cnt):
              for zr in win.get('rows', [win.get('z0', 1.8)]):
                if zr < 0.6:
                    continue
                p = a + ed * (off + c * win['spacing']) + nrm * 0.04
                hw = ed * (win['w'] / 2)
                z0 = Vector((0, 0, zr))
                z1 = Vector((0, 0, zr + win['h']))
                g = face([p - hw + z0, p + hw + z0, p + hw + z1, p - hw + z1], 'glassdark',
                         uvs=[(0.06, 0.2), (0.47, 0.2), (0.47, 0.68), (0.06, 0.68)])
                outward(g, cen)
    f = face([p + Vector((0, 0, z)) for p in P], roofm)
    upward(f)


for n, b in G['blocks'].items():
    block(b['poly'], b['z'], b.get('wall', 'brick'), b.get('roof', 'greyroof'), b.get('windows'), b.get('facemat'),
          b.get('z0', 0.0))
for sg in G.get('signs', []):
    A = Vector((sg['a'][0], sg['a'][1], 0))
    Bv = Vector((sg['b'][0], sg['b'][1], 0))
    e = (Bv - A).normalized()
    nb = Vector((-e.y, e.x, 0))
    zt, zb = Vector((0, 0, sg['ztop'])), Vector((0, 0, sg['zbot']))
    mid = (A + Bv) / 2
    sgn = 1 if nb.dot(mid - Vector((C.x, C.y, 0))) > 0 else -1
    back = nb * sg['t'] * sgn
    f = face([A + zb, Bv + zb, Bv + zt, A + zt], sg['mat'], uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    if f.normal.dot(back) > 0:
        f.normal_flip()
        for l in f.loops:
            pass
    box_pts = [A + back, Bv + back]
    face([Bv + back + zb, A + back + zb, A + back + zt, Bv + back + zt], sg['back'])
    for p0, p1 in ((A, A + back), (Bv + back, Bv)):
        face([p0 + zb, p1 + zb, p1 + zt, p0 + zt], sg['back'])
    face([A + zt, Bv + zt, Bv + back + zt, A + back + zt], sg['back'])
    for q in (A + back * 0.5 + e * 1.0, Bv + back * 0.5 - e * 1.0):
        box(Vector((q.x, q.y, 0)), Vector((q.x, q.y, sg['zbot'])), 0.4, sg['back'])
for vp in G.get('vents', []):
    c0 = V(vp)
    R6 = 0.5
    pts = [Vector((math.cos(2 * math.pi * a / 12) * R6, math.sin(2 * math.pi * a / 12) * R6, 0)) for a in range(12)]
    for a in range(12):
        p, q = c0 + pts[a], c0 + pts[(a + 1) % 12]
        f = face([p, q, q + Vector((0, 0, 0.8)), p + Vector((0, 0, 0.8))], 'steel')
        outward(f, c0)
    f = face([c0 + p + Vector((0, 0, 0.8)) for p in pts], 'steel')
    upward(f)
if 'pool' in G:
    f = face([V(p, 0.08) for p in G['pool']], 'pool')
    upward(f)
if 'sign' in G:
    s0, s1 = V(G['sign'][0], 0), V(G['sign'][1], 0)
    f = face([s0 + Vector((0, 0, 4)), s1 + Vector((0, 0, 4)), s1 + Vector((0, 0, 7.5)), s0 + Vector((0, 0, 7.5))],
             'yellow')
    outward(f, C)
bm.to_mesh(me)
me.validate()
bm.free()
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB')
print('OK', len(me.polygons))
