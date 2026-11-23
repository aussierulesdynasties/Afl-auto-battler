# Mesh builder used by build.py (runs inside Blender). Faces carry a material name and optional explicit UVs;
# otherwise UVs are world metres / the material's tile size (walls: along-wall x height; flat: x y).
import bpy, math, json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
TILE = json.load(open(os.path.join(HERE, 'tex', 'tiles.json')))
MATS = {}
SPECIAL = {'glass': dict(rough=0.08, metal=0.0), 'steel_galv': dict(rough=0.35, metal=0.6),
           'steel_white': dict(rough=0.4), 'roof_grey': dict(rough=0.45, metal=0.35),
           'roof_tan': dict(rough=0.5, metal=0.2), 'roof_white': dict(rough=0.45, metal=0.25),
           'roof_dkgrey': dict(rough=0.45, metal=0.35), 'roof_deck': dict(rough=0.5, metal=0.2)}


def mat(name):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    im = bpy.data.images.load(os.path.join(HERE, 'tex', name + '.png'))
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = im; t.interpolation = 'Cubic'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    o = SPECIAL.get(name, {})
    b.inputs['Roughness'].default_value = o.get('rough', 0.85)
    b.inputs['Metallic'].default_value = o.get('metal', 0.0)
    if name in ('pickets', 'mesh'):
        nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
        for attr, val in (('blend_method', 'CLIP'), ('surface_render_method', 'DITHERED')):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
        m.use_backface_culling = False
    MATS[name] = m
    return m


def sarea(p):
    return sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p))) / 2


def ccw(p):
    p = [tuple(x[:2]) for x in p]
    return p if sarea(p) > 0 else p[::-1]


def rect(c, L, W, a):
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a)); u = (ca, sa); v = (-sa, ca)
    return [(c[0] + su * L / 2 * u[0] + sv * W / 2 * v[0], c[1] + su * L / 2 * u[1] + sv * W / 2 * v[1])
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def earclip(P):
    P = list(P); out = []
    def inside(p, a, b, c):
        d1 = (p[0]-b[0])*(a[1]-b[1])-(a[0]-b[0])*(p[1]-b[1]); d2 = (p[0]-c[0])*(b[1]-c[1])-(b[0]-c[0])*(p[1]-c[1])
        d3 = (p[0]-a[0])*(c[1]-a[1])-(c[0]-a[0])*(p[1]-a[1])
        return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))
    guard = 0
    while len(P) > 3 and guard < 10000:
        guard += 1; n = len(P)
        for i in range(n):
            a, b, c = P[i-1], P[i], P[(i+1) % n]
            if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]) <= 1e-9:
                continue
            if any(inside(p, a, b, c) for p in P if p not in (a, b, c)):
                continue
            out.append([a, b, c]); P.pop(i); break
        else:
            out.append(P[:3]); P.pop(1)
    out.append(P)
    return out


class MB:
    def __init__(s, name):
        s.name = name; s.V = []; s.F = []; s.M = []; s.UV = []

    def face(s, pts, m, uv=None):
        i0 = len(s.V); s.V += [tuple(map(float, p)) for p in pts]
        s.F.append(list(range(i0, i0 + len(pts)))); s.M.append(m); s.UV.append(uv)

    def wall(s, p, q, z0, z1, m):  # outward normal on the right of p->q (CCW polygons)
        s.face([(p[0], p[1], z0), (q[0], q[1], z0), (q[0], q[1], z1), (p[0], p[1], z1)], m)

    def prism(s, poly, z0, z1, m, top=None, bot=None):
        poly = ccw(poly)
        for i in range(len(poly)):
            s.wall(poly[i], poly[(i + 1) % len(poly)], z0, z1, m)
        if top:
            s.cap(poly, z1, top)
        if bot:
            s.cap(poly, z0, bot, down=True)

    def cap(s, poly, z, m, down=False):
        for c in earclip(ccw(poly)):
            if down:
                c = c[::-1]
            s.face([(x, y, z) for x, y in c], m)

    def box(s, c, L, W, H, a, m, z0=0.0, mtop=None):
        s.prism(rect(c, L, W, a), z0, z0 + H, m, top=mtop or m, bot=m)

    def cyl(s, c, r, z0, z1, m, n=24, top=None):
        poly = [(c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
        s.prism(poly, z0, z1, m, top=top)

    def beam(s, p, q, w, h, m):  # rectangular member from 3D p to q
        p = np.array(p, float); q = np.array(q, float); d = q - p; d /= np.linalg.norm(d)
        a = np.cross(d, [0, 0, 1.0])
        a = a / np.linalg.norm(a) if np.linalg.norm(a) > 1e-6 else np.array([1.0, 0, 0])
        b = np.cross(a, d); cs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
        P = [p + a * x * w / 2 + b * y * h / 2 for x, y in cs]; Q = [q + a * x * w / 2 + b * y * h / 2 for x, y in cs]
        for i in range(4):
            j = (i + 1) % 4; s.face([P[i], P[j], Q[j], Q[i]], m)
        s.face(P[::-1], m); s.face(Q, m)

    def build(s, col=None):
        me = bpy.data.meshes.new(s.name); me.from_pydata(s.V, [], s.F); me.update()
        names = sorted(set(s.M))
        for n in names:
            me.materials.append(mat(n))
        idx = {n: i for i, n in enumerate(names)}
        uvl = me.uv_layers.new(name='UVMap')
        for f, poly in enumerate(me.polygons):
            m = s.M[f]; poly.material_index = idx[m]; poly.use_smooth = False
            tu, tv = TILE.get(m, (1, 1)); n = poly.normal; uvx = s.UV[f]
            if uvx is None and abs(n.z) <= 0.7:  # wall: whole bays from the face's own edge, so no window wraps a corner
                h = math.hypot(n.x, n.y); tx, ty = (-n.y / h, n.x / h) if h > 1e-6 else (1, 0)
                pr = [me.vertices[me.loops[li].vertex_index].co for li in poly.loop_indices]
                pr = [c.x * tx + c.y * ty for c in pr]; p0 = min(pr); wd = max(pr) - p0; nb = round(wd / tu)
                tw, off = (wd / nb, 0.0) if nb >= 1 else (tu, 0.5 - 0.5 * wd / tu)
            for k, li in enumerate(poly.loop_indices):
                v = me.vertices[me.loops[li].vertex_index].co
                if uvx is not None:
                    uv = uvx[k]
                elif abs(n.z) > 0.7:
                    uv = (v.x / tu, v.y / tv)
                else:
                    uv = ((v.x * tx + v.y * ty - p0) / tw + off, v.z / tv)
                uvl.data[li].uv = uv
        ob = bpy.data.objects.new(s.name, me)
        (col or bpy.context.scene.collection).objects.link(ob)
        return ob


class Frame:  # local building frame: u along length, v across, origin at the footprint box centre
    def __init__(s, o):
        s.c = o['c']; s.a = math.radians(o['a']); s.L = o['L']; s.W = o['W']

    def P(s, u, v, z=None):
        ca, sa = math.cos(s.a), math.sin(s.a); x = s.c[0] + u * ca - v * sa; y = s.c[1] + u * sa + v * ca
        return (x, y) if z is None else (x, y, z)


def roof(mb, F, u0, u1, v0, v1, kind, eave, ridge, m, over=0.4, gm='brick_red', soffit='paint_white',
         fascia='paint_white', ridge_axis='u'):
    """Roof on local box u0..u1 x v0..v1 (before overhang). kind hip/gable/flat/skillion; ridge along u
    unless ridge_axis='v'. Skillion: high side at v1."""
    u0 -= over; u1 += over; v0 -= over; v1 += over
    if ridge_axis == 'v':
        P = lambda u, v, z: F.P(v, u, z); u0, u1, v0, v1 = v0, v1, u0, u1
    else:
        P = lambda u, v, z: F.P(u, v, z)
    Q = [P(u0, v0, eave), P(u1, v0, eave), P(u1, v1, eave), P(u0, v1, eave)]
    vm = (v0 + v1) / 2; hw = (v1 - v0) / 2
    if kind == 'hip':
        ri = max((u1 - u0) / 2 - hw, 0.01); um = (u0 + u1) / 2; A = P(um - ri, vm, ridge); B = P(um + ri, vm, ridge)
        mb.face([Q[0], Q[1], B, A], m); mb.face([Q[2], Q[3], A, B], m)
        mb.face([Q[3], Q[0], A], m); mb.face([Q[1], Q[2], B], m)
    elif kind == 'hip0':  # hip at the u0 end, gable at the u1 end
        A = P(min(u0 + hw, u1), vm, ridge); B = P(u1, vm, ridge)
        mb.face([Q[0], Q[1], B, A], m); mb.face([Q[2], Q[3], A, B], m)
        mb.face([Q[3], Q[0], A], m); mb.face([Q[1], Q[2], B], gm)
    elif kind == 'gable':
        A = P(u0, vm, ridge); B = P(u1, vm, ridge)
        mb.face([Q[0], Q[1], B, A], m); mb.face([Q[2], Q[3], A, B], m)
        mb.face([Q[3], Q[0], A], gm); mb.face([Q[1], Q[2], B], gm)
    elif kind == 'skillion':
        R = [P(u0, v0, eave), P(u1, v0, eave), P(u1, v1, ridge), P(u0, v1, ridge)]; mb.face(R, m)
        D = [P(u0, v0, eave - 0.2), P(u1, v0, eave - 0.2), P(u1, v1, ridge - 0.2), P(u0, v1, ridge - 0.2)]
        for i in range(4):
            j = (i + 1) % 4; mb.face([D[i], D[j], R[j], R[i]], fascia)
        mb.face(D[::-1], soffit); return
    elif kind == 'flat':
        T = [P(u0, v0, ridge), P(u1, v0, ridge), P(u1, v1, ridge), P(u0, v1, ridge)]; mb.face(T, m)
        for i in range(4):
            j = (i + 1) % 4; mb.face([Q[i], Q[j], T[j], T[i]], fascia)
        mb.face(Q[::-1], soffit); return
    D = [P(u0, v0, eave - 0.22), P(u1, v0, eave - 0.22), P(u1, v1, eave - 0.22), P(u0, v1, eave - 0.22)]
    for i in range(4):
        j = (i + 1) % 4; mb.face([D[i], D[j], Q[j], Q[i]], fascia)
    mb.face(D[::-1], soffit)


def window(mb, p, q, a, b, sill, head, glass='glass', frame='paint_white', out=0.04, fw=0.07):
    """Window on wall p->q (outward normal to the right), from a to b metres along it."""
    p = np.array(p[:2], float); q = np.array(q[:2], float); d = (q - p) / np.linalg.norm(q - p); n = np.array([d[1], -d[0]])
    A = p + d * a + n * out; B = p + d * b + n * out
    mb.face([(*A, sill), (*B, sill), (*B, head), (*A, head)], glass)
    for (x0, x1, z0, z1) in ((a, b, sill - fw, sill), (a, b, head, head + fw), (a - fw, a, sill - fw, head + fw),
                             (b, b + fw, sill - fw, head + fw)):
        P0 = p + d * x0 + n * (out + 0.03); P1 = p + d * x1 + n * (out + 0.03)
        mb.face([(*P0, z0), (*P1, z0), (*P1, z1), (*P0, z1)], frame)
