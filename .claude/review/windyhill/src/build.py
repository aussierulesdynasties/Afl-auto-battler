import os
# Windy Hill 1984, from bb1984.jpg (fitted camera) + OSM. Usage: blender -b --python build.py -- OUT.glb
import bpy, bmesh, sys, json, math
import numpy as np
dst = sys.argv[sys.argv.index('--') + 1]
import os; D = os.path.dirname(os.path.abspath(__file__)).replace(chr(92), '/')
W = json.load(open(D + '/world.json')); G = json.load(open(D + '/geo.json'))
bpy.ops.wm.read_factory_settings(use_empty=True)
MATS = {}; BM = {}
TILE = {'grass': 16, 'concrete': 4, 'asphalt': 6, 'roof': 6, 'steps': 4, 'brick': 2, 'white': 4, 'board': 4,
        'pitchclay': 4, 'green': 8, 'render': 4, 'grass2': 16, 'roof_dark': 6, 'seat_grey': 4, 'seat_red': 4, 'bank': 8, 'concourse': 6, 'glass': 4, 'steel': 2, 'sbface': 1, 'signs': 24, 'tread': 4, 'bench_grey': 1.2, 'bench_red': 1.2}
sys.path.insert(0, D)
from cam import proj as _proj, R
CAMP = json.load(open(D + '/cam84.json'))['p']
OCC = []  # (polygon, top z) of everything that hides what is under it from the photo's camera
def inpoly(x, y, P):
    c = False; n = len(P)
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]: c = not c
    return c
def seen_from_photo(vs):
    if any(len(v) < 3 for v in vs): return False
    nx = ny = nz = 0.0
    for i in range(len(vs)):
        a, b = vs[i], vs[(i + 1) % len(vs)]
        nx += (a[1] - b[1]) * (a[2] + b[2]); ny += (a[2] - b[2]) * (a[0] + b[0]); nz += (a[0] - b[0]) * (a[1] + b[1])
    L = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
    if abs(nz) / L < 0.7: return False
    cx = sum(v[0] for v in vs) / len(vs); cy = sum(v[1] for v in vs) / len(vs); cz = sum(v[2] for v in vs) / len(vs)
    return not any(z > cz + 0.4 and inpoly(cx, cy, P) for P, z in OCC)

def mat(n, rough=0.9):
    if n in MATS: return
    m = bpy.data.materials.new(n); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(D + '/tex/' + n + '.png')
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = rough
    MATS[n] = m; BM[n] = bmesh.new()

def face(n, vs, uvs=None, both=True):
    if False:
        q = _proj(CAMP, np.array([[v[0], v[1], v[2]] for v in vs]))
        n = 'photo'; uvs = [(float(a) / 797, 1 - float(b) / 675) for a, b in q]; both = False
        if sum((vs[i][0] - vs[(i + 1) % len(vs)][0]) * (vs[i][1] + vs[(i + 1) % len(vs)][1]) for i in range(len(vs))) < 0:
            vs, uvs = vs[::-1], uvs[::-1]
    mat(n); bm = BM[n]; uvl = bm.loops.layers.uv.verify(); t = TILE[n]
    if uvs is None: uvs = [(v[0] / t, v[1] / t) for v in vs]
    if len(vs) > 4:
        from mathutils.geometry import tessellate_polygon
        from mathutils import Vector
        for tri in tessellate_polygon([[Vector((v[0], v[1], 0)) for v in vs]]):
            tv = [vs[i] for i in tri]; tu = [uvs[i] for i in tri]
            if (tv[1][0]-tv[0][0])*(tv[2][1]-tv[0][1])-(tv[1][1]-tv[0][1])*(tv[2][0]-tv[0][0]) < 0: tv, tu = tv[::-1], tu[::-1]
            face(n, tv, tu, both)
        return
    for vv, uu in ((vs, uvs), (vs[::-1], uvs[::-1])) if both else ((vs, uvs),):
        try: f = bm.faces.new([bm.verts.new(v) for v in vv])
        except ValueError: continue
        for l, u in zip(f.loops, uu): l[uvl].uv = u

def wall(n, a, b, z0, za1, zb1=None):
    zb1 = za1 if zb1 is None else zb1; t = TILE[n]; L = math.hypot(b[0] - a[0], b[1] - a[1])
    face(n, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], zb1), (a[0], a[1], za1)],
         [(0, z0 / t), (L / t, z0 / t), (L / t, zb1 / t), (0, za1 / t)])

def top(n, pts, z):
    zz = z if callable(z) else (lambda p: z)
    face(n, [(p[0], p[1], zz(p)) for p in pts])

def prism(pts, z0, z1, ntop, nside):
    top(ntop, pts, z1)
    for i in range(len(pts)): wall(nside, pts[i], pts[(i + 1) % len(pts)], z0, z1)

def dline(a, b, p):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    return abs((b[0] - a[0]) * (a[1] - p[1]) - (a[0] - p[0]) * (b[1] - a[1])) / L

def bench(a0, b0, a1, b1, z, mat):
    # bench seat on a tread: 0.42 m high, from 35% to 75% of the tread depth (front a0-b0, back a1-b1)
    L_ = lambda P, Q, t: (P[0] + (Q[0] - P[0]) * t, P[1] + (Q[1] - P[1]) * t)
    f0, f1, k0, k1 = L_(a0, a1, 0.35), L_(b0, b1, 0.35), L_(a0, a1, 0.75), L_(b0, b1, 0.75); h = z + 0.42
    Lb = math.hypot(f1[0] - f0[0], f1[1] - f0[1]) / 1.2
    face(mat, [(f0[0], f0[1], h), (f1[0], f1[1], h), (k1[0], k1[1], h), (k0[0], k0[1], h)], [(0, 0), (Lb, 0), (Lb, 1), (0, 1)])
    wall('steps', f0, f1, z, h)
def rail(a, b, z):
    # front railing: galvanised top rail at 1.0 m, posts every 2 m
    L_ = math.hypot(b[0] - a[0], b[1] - a[1]); wall('steel', a, b, z + 0.94, z + 1.04); wall('steel', a, b, z + 0.5, z + 0.55)
    for k in range(int(L_ / 2) + 1):
        e = (a[0] + (b[0] - a[0]) * k * 2 / L_, a[1] + (b[1] - a[1]) * k * 2 / L_) if L_ > 0 else a
        wall('steel', (e[0] - 0.03, e[1]), (e[0] + 0.03, e[1]), z, z + 1.04); wall('steel', (e[0], e[1] - 0.03), (e[0], e[1] + 0.03), z, z + 1.04)
PITCH = W['pitch_fit']['pts']; CX, CY = W['pitch_fit']['q'][0], W['pitch_fit']['q'][1]
for _k, _z in (('reyn_roof', 12.0), ('reyn_back', 12.0), ('showers_roof', 12.0), ('crichton', 5.0)): OCC.append((W[_k]['pts'], _z))
def nearest_pitch(p): return min(PITCH, key=lambda q: (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2)
def out(p, d):
    dx, dy = p[0] - CX, p[1] - CY; L = math.hypot(dx, dy); return (p[0] + dx / L * d, p[1] + dy / L * d)

def stand(k, fi, zf, zr, roof=None, terrace=True, seat='seat_grey', rise=0.0):
    pts = W[k]['pts']; n = len(pts); A, B = pts[fi], pts[(fi + 1) % n]
    md = max(dline(A, B, p) for p in pts); zd = lambda p: zf + (zr - zf) * dline(A, B, p) / md
    ux = (B[0] - A[0], B[1] - A[1]); L = math.hypot(*ux); ux = (ux[0] / L, ux[1] / L)
    if n == 4:
        # stepped seat rows: treads ~0.8 m deep, front edge A-B to back edge D-C
        C_, D_ = pts[(fi + 2) % 4], pts[(fi + 3) % 4]
        rows = max(2, int(round(md / 0.8)))
        lerp = lambda P, Q, t: (P[0] + (Q[0] - P[0]) * t, P[1] + (Q[1] - P[1]) * t)
        for r in range(rows):
            t0, t1 = r / rows, (r + 1) / rows; z = zf + (zr - zf) * t1
            a0, b0, a1, b1 = lerp(A, D_, t0), lerp(B, C_, t0), lerp(A, D_, t1), lerp(B, C_, t1)
            zprev = zf + (zr - zf) * t0
            wall('steps', a0, b0, zprev, z)
            Lr = math.hypot(b0[0] - a0[0], b0[1] - a0[1]) / 4
            # seat bays split by 1.2 m concrete aisles at each roof post (posts every L/m)
            m_ = max(2, int(L / 9)); hw = 0.6 / L; cuts = [0.0]
            for j in range(1, m_): cuts += [j / m_ - hw, j / m_ + hw]
            cuts.append(1.0)
            for c in range(len(cuts) - 1):
                u0, u1 = cuts[c], cuts[c + 1]
                p0, q0, p1, q1 = lerp(a0, b0, u0), lerp(a0, b0, u1), lerp(a1, b1, u0), lerp(a1, b1, u1)
                face('tread', [(p0[0], p0[1], z), (q0[0], q0[1], z), (q1[0], q1[1], z), (p1[0], p1[1], z)], [(Lr * u0, 0), (Lr * u1, 0), (Lr * u1, 1), (Lr * u0, 1)])
                if c % 2 == 0: bench(p0, q0, p1, q1, z, seat.replace('seat', 'bench'))
    else:
        face('steps', [(p[0], p[1], zd(p)) for p in pts],
             [(((p[0] - A[0]) * ux[0] + (p[1] - A[1]) * ux[1]) / 4, dline(A, B, p) / 4) for p in pts])
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        if i == fi: wall('brick', a, b, 0, zf); rail(a, b, zf); continue
        back = (n == 4 and i == (fi + 2) % 4) or (n != 4 and dline(A, B, a) > 0.6 * md and dline(A, B, b) > 0.6 * md)
        if roof and back: wall('brick', a, b, 0, roof - 0.6)
        else: wall('brick', a, b, 0, zd(a) + 1.1, zd(b) + 1.1)
    if roof:
        zt = lambda p: roof + rise * (1 - dline(A, B, p) / md)  # roof rises toward the front edge by `rise` m
        top('roof', pts, zt)
        for i in range(n): wall('white', pts[i], pts[(i + 1) % n], roof - 0.6, zt(pts[i]), zt(pts[(i + 1) % n]))
        m = max(2, int(L / 9))
        for j in range(m + 1):
            t = j / m; x = A[0] + (B[0] - A[0]) * t; y = A[1] + (B[1] - A[1]) * t; s = 0.15
            q = [(x - s, y - s), (x + s, y - s), (x + s, y + s), (x - s, y + s)]
            for i2 in range(4): wall('white', q[i2], q[(i2 + 1) % 4], zf, roof - 0.6)
    if terrace:
        A2 = out(nearest_pitch(A), 1.0); B2 = out(nearest_pitch(B), 1.0)
        dA = math.hypot(A[0] - A2[0], A[1] - A2[1]) / 4; dB = math.hypot(B[0] - B2[0], B[1] - B2[1]) / 4
        face('steps', [(A2[0], A2[1], 0.25), (B2[0], B2[1], 0.25), (B[0], B[1], zf), (A[0], A[1], zf)],
             [(0, 0), (L / 4, 0), (L / 4, dB), (0, dA)])

# ---- ground
S = 190
exec(open(D + '/world.py').read().split('import parts')[0].replace("open('cam84.json')", "open(D + '/cam84.json')").replace('from cam import R', ''))
GP = [at_z(0, 675, -0.05), at_z(797, 675, -0.05), at_z(797, 0, -0.05), at_z(0, 0, -0.05)]
fen = [out(p, 0.6) for p in PITCH]
def apron():
    # paved apron from the fence out to the ground's site line; inside the fence is left to the game's turf
    from mathutils.geometry import tessellate_polygon
    from mathutils import Vector
    loops = [G['26275746']['pts'], fen]  # director 'Fill with plain ground': greens' holes filled with paving
    _m = os.environ.get('WH_APRON', '')  # board variants only; unset = the current model
    if _m == 'trim': loops = [json.load(open(D + '/trim.json')), fen]
    if _m == 'fill': loops = [G['26275746']['pts'], fen]
    flat = [p for L_ in loops for p in L_]
    for tri in tessellate_polygon([[Vector((p[0], p[1], 0)) for p in L_] for L_ in loops]):
        tv = [(flat[t][0], flat[t][1], 0.0) for t in tri]
        if (tv[1][0]-tv[0][0])*(tv[2][1]-tv[0][1])-(tv[1][1]-tv[0][1])*(tv[2][0]-tv[0][0]) < 0: tv = tv[::-1]
        face('concourse', tv, both=False)
apron()
# boundary fence: bare white-painted pickets, no boards or sponsor panels (director: "C: no boards")
for i in range(len(fen)):
    wall('white', fen[i], fen[(i + 1) % len(fen)], 0.05, 1.0)
def FE(k):
    P = W[k]['pts']; n = len(P)
    return min(range(n), key=lambda i: math.hypot((P[i][0] + P[(i + 1) % n][0]) / 2 - CX, (P[i][1] + P[(i + 1) % n][1]) / 2 - CY))
# ---- stands: (front edge index, front deck z, rear deck z, roof z)
stand('reyn_back', 2, 7.0, 10.0, 12.0, terrace=False)
stand('cook_seats', 2, 1.8, 5.0)
stand('n_stand', 2, 1.8, 5.0)
stand('crichton', 0, 0.6, 3.2, 5.0, seat='seat_red')
stand('cook_roof', FE('cook_roof'), 7.4, 10.4, 12.4, terrace=False)
def glassband(a, b, z0, z1, off=0.06):
    # window row on a stand face, set just proud of the wall toward the pitch
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); dx, dy = m[0] - CX, m[1] - CY; L = math.hypot(dx, dy)
    a2 = (a[0] - dx / L * off, a[1] - dy / L * off); b2 = (b[0] - dx / L * off, b[1] - dy / L * off); wall('glass', a2, b2, z0, z1)
_cp = W['cook_roof']['pts']; _fi = FE('cook_roof'); glassband(_cp[_fi], _cp[(_fi + 1) % 4], 5.4, 6.9)
def twotier(k, fi, split, zl0, zl1, zband, zu1, roof, rfrom, ribs):
    # Hird: open lower terrace, brick band with glass boxes, upper tier under a cantilever roof with raised rafters
    P = W[k]['pts']; A, B, C_, D_ = P[fi], P[(fi + 1) % 4], P[(fi + 2) % 4], P[(fi + 3) % 4]
    lerp = lambda p, q, t: (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
    def rows(t0, t1, z0, z1, n, seat):
        for r in range(n):
            u0, u1 = t0 + (t1 - t0) * r / n, t0 + (t1 - t0) * (r + 1) / n; zp, z = z0 + (z1 - z0) * r / n, z0 + (z1 - z0) * (r + 1) / n
            a0, b0, a1, b1 = lerp(A, D_, u0), lerp(B, C_, u0), lerp(A, D_, u1), lerp(B, C_, u1)
            wall('steps', a0, b0, zp, z); Lr = math.hypot(b0[0] - a0[0], b0[1] - a0[1]) / 4
            face('tread', [(a0[0], a0[1], z), (b0[0], b0[1], z), (b1[0], b1[1], z), (a1[0], a1[1], z)], [(0, 0), (Lr, 0), (Lr, 1), (0, 1)])
            if seat != 'steps': bench(a0, b0, a1, b1, z, 'bench_grey')
            if seat == 'steps' and r % 4 == 3: barrier(a1, b1, z)
    dep = math.hypot(D_[0] - A[0], D_[1] - A[1])
    rows(0, split, zl0, zl1, max(2, int(dep * split / 0.8)), 'steps')
    sa, sb = lerp(A, D_, split), lerp(B, C_, split)
    wall('brick', sa, sb, zl1, zband); glassband(sa, sb, zl1 + 0.5, zband - 0.9); rail(sa, sb, zband); rail(A, B, zl0)
    rows(split, 0.92, zband, zu1, max(2, int(dep * (0.92 - split) / 0.8)), 'seat_grey')
    ga, gb = lerp(A, D_, 0.92), lerp(B, C_, 0.92); wall('glass', ga, gb, zu1, roof - 0.4)
    face('concrete', [(ga[0], ga[1], zu1), (gb[0], gb[1], zu1), (C_[0], C_[1], zu1), (D_[0], D_[1], zu1)])
    wall('brick', D_, C_, 0, roof); wall('brick', A, B, 0, zl0)
    for e0, e1 in ((A, D_), (B, C_)): face('brick', [(e0[0], e0[1], 0), (e1[0], e1[1], 0), (e1[0], e1[1], roof), (e0[0], e0[1], zband + 1.0), (e0[0], e0[1], zl0 + 1.0)])
    ra, rb = lerp(A, D_, rfrom), lerp(B, C_, rfrom)
    top('roof', [ra, rb, C_, D_], roof); wall('roof_dark', ra, rb, roof - 1.0, roof)
    for j in range(ribs):
        t = (j + 0.5) / ribs; f0, f1 = lerp(ra, rb, t), lerp(D_, C_, t)
        nx, ny = -(f1[1] - f0[1]), f1[0] - f0[0]; nl = math.hypot(nx, ny) / 0.15
        for sg in (-1, 1): wall('white', (f0[0] + sg * nx / nl, f0[1] + sg * ny / nl), (f1[0] + sg * nx / nl, f1[1] + sg * ny / nl), roof, roof + 0.7)
        face('white', [(f0[0] - nx / nl, f0[1] - ny / nl, roof + 0.7), (f0[0] + nx / nl, f0[1] + ny / nl, roof + 0.7), (f1[0] + nx / nl, f1[1] + ny / nl, roof + 0.7), (f1[0] - nx / nl, f1[1] - ny / nl, roof + 0.7)])
def barrier(a, b, z):
    # terrace crush barrier: galvanised rail at 1.05 m on posts, 3 m lengths with 1.2 m gaps
    L = math.hypot(b[0] - a[0], b[1] - a[1]); t = 0.6
    while t + 3.0 < L:
        p = (a[0] + (b[0] - a[0]) * t / L, a[1] + (b[1] - a[1]) * t / L); q = (a[0] + (b[0] - a[0]) * (t + 3) / L, a[1] + (b[1] - a[1]) * (t + 3) / L)
        wall('steel', p, q, z + 0.97, z + 1.07)
        for e in (p, q): wall('steel', (e[0] - 0.04, e[1]), (e[0] + 0.04, e[1]), z, z + 1.07); wall('steel', (e[0], e[1] - 0.04), (e[0], e[1] + 0.04), z, z + 1.07)
        t += 4.2
twotier('hird', 2, 0.42, 1.8, 4.2, 7.0, 10.5, 13.5, 0.38, 7)
for k in ('club', 'nw_bldg', 'nb1', 'nb2'):  # south free-standing huts deleted (director: pass after cut)
    prism(W[k]['pts'], 0, W[k]['h'], 'roof', 'render')
_sp = W['scoreboard']['pts']; prism(_sp, 0, 13.0, 'roof', 'render')  # painted structure, black board on the ground side only
_sf = FE('scoreboard'); glassband  # noqa
_a, _b = _sp[_sf], _sp[(_sf + 1) % 4]; _m = ((_a[0] + _b[0]) / 2, (_a[1] + _b[1]) / 2); _dx, _dy = _m[0] - CX, _m[1] - CY; _L = math.hypot(_dx, _dy)
_p, _q = (_a[0] - _dx / _L * 0.08, _a[1] - _dy / _L * 0.08), (_b[0] - _dx / _L * 0.08, _b[1] - _dy / _L * 0.08)
face('sbface', [(_p[0], _p[1], 3.0), (_q[0], _q[1], 3.0), (_q[0], _q[1], 12.4), (_p[0], _p[1], 12.4)], [(0, 0), (1, 0), (1, 1), (0, 1)])
# ---- east hill: terraced bank from the fence (0.3 m) to the crest (3.5 m) under the east wall
ho = W['hill_outer']['pts']
def resample(P, N):
    P = np.array(P); d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; t = np.linspace(0, d[-1], N)
    return np.c_[np.interp(t, d, P[:, 0]), np.interp(t, d, P[:, 1])]
def idx(p): return min(range(len(PITCH)), key=lambda i: (PITCH[i][0] - p[0]) ** 2 + (PITCH[i][1] - p[1]) ** 2)
i0, i1 = idx(ho[0]), idx(ho[-1]); n = len(PITCH)
arcA = [PITCH[(i0 + j) % n] for j in range((i1 - i0) % n + 1)]; arcB = [PITCH[(i0 - j) % n] for j in range((i0 - i1) % n + 1)]
arc = arcA if np.mean([p[0] for p in arcA]) > np.mean([p[0] for p in arcB]) else arcB
arc = [out(p, 1.0) for p in arc]
N = 60; I = resample(arc, N); O0 = resample(ho, N)
# 1984 photo: terrace rows end ~15 m from the fence; beyond that a grass bank runs to the wall (SE corner)
_dd = np.hypot(*(O0 - I).T)[:, None]; O = I + (O0 - I) * np.minimum(1.0, 14.0 / _dd)
for j in range(N - 1):
    if _dd[j, 0] > 14.2 or _dd[j + 1, 0] > 14.2:
        top('bank', [tuple(O[j]), tuple(O[j + 1]), tuple(O0[j + 1]), tuple(O0[j])], 3.5)
K = max(4, int(np.mean(np.hypot(*(O - I).T)) / 0.8)); K = min(K, 17)  # stepped rows about 0.8 m deep
for j in range(N - 1):
    for k in range(K):
        f0, f1 = k / K, (k + 1) / K; z0, z1 = 0.3 + 3.2 * f0, 0.3 + 3.2 * f1
        a, b = I[j] + (O[j] - I[j]) * f0, I[j + 1] + (O[j + 1] - I[j + 1]) * f0
        c, d = I[j + 1] + (O[j + 1] - I[j + 1]) * f1, I[j] + (O[j] - I[j]) * f1
        wall('steps', tuple(a), tuple(b), z0, z1)
        L = math.hypot(b[0] - a[0], b[1] - a[1]) / 4
        face('tread', [(a[0], a[1], z1), (b[0], b[1], z1), (c[0], c[1], z1), (d[0], d[1], z1)], [(0, 0), (L, 0), (L, 1), (0, 1)])
        if k % 4 == 3 and j % 3 == 0: barrier(tuple(d), tuple(I[j + 3] + (O[j + 3] - I[j + 3]) * f1) if j + 3 < N else tuple(c), z1)

def arcstand(a0, span, d0, d1, zf, zr, roof, bays, seat='seat_grey', rise=0.0):
    """Stand that follows the boundary curve (as Reynolds and the showers stand do in the 1984 photo):
    seat rows between d0 and d1 m outside the fence line, roof in `bays` flat panels with ridge strips."""
    rel = lambda p: (math.degrees(math.atan2(p[1] - CY, p[0] - CX)) - a0) % 360
    arc = sorted([p for p in PITCH if rel(p) <= span], key=rel)
    F = resample([out(p, d0) for p in arc], bays * 6 + 1); Bk = resample([out(p, d1) for p in arc], bays * 6 + 1)
    rows = max(2, int(round((d1 - d0) / 0.8)))
    for j in range(len(F) - 1):
        for r in range(rows):
            t0, t1 = r / rows, (r + 1) / rows; z, zp = zf + (zr - zf) * t1, zf + (zr - zf) * t0
            a_, b_ = F[j] + (Bk[j] - F[j]) * t0, F[j + 1] + (Bk[j + 1] - F[j + 1]) * t0
            c_, d_ = F[j + 1] + (Bk[j + 1] - F[j + 1]) * t1, F[j] + (Bk[j] - F[j]) * t1
            wall('steps', tuple(a_), tuple(b_), zp, z)
            Lr = math.hypot(*(b_ - a_)) / 4
            face('tread', [(a_[0], a_[1], z), (b_[0], b_[1], z), (c_[0], c_[1], z), (d_[0], d_[1], z)], [(0, 0), (Lr, 0), (Lr, 1), (0, 1)])
            if j % 6 != 0: bench(tuple(a_), tuple(b_), tuple(d_), tuple(c_), z, seat.replace('seat', 'bench'))  # aisle every bay
        wall('brick', tuple(Bk[j]), tuple(Bk[j + 1]), 0, roof - 0.6)
        wall('brick', tuple(F[j]), tuple(F[j + 1]), 0, zf); rail(tuple(F[j]), tuple(F[j + 1]), zf)
    for e in (0, -1): wall('brick', tuple(F[e]), tuple(Bk[e]), 0, roof - 0.6)
    zf_, zb_ = roof + rise, roof
    for j in range(0, len(F) - 1, 6):
        q = [F[j], F[j + 6], Bk[j + 6], Bk[j]]
        face('roof', [(q[0][0], q[0][1], zf_), (q[1][0], q[1][1], zf_), (q[2][0], q[2][1], zb_), (q[3][0], q[3][1], zb_)])
        wall('white', tuple(F[j]), tuple(F[j + 6]), zf_ - 0.6, zf_)
        for i in (j, j + 6):  # ridge strip and post at each bay line
            m = F[i] + (Bk[i] - F[i]) * 0.02; s = 0.15
            for k2 in range(4):
                c0 = (m[0] + s * ((k2 in (1, 2)) * 2 - 1), m[1] + s * ((k2 in (2, 3)) * 2 - 1))
                c1 = (m[0] + s * (((k2 + 1) % 4 in (1, 2)) * 2 - 1), m[1] + s * (((k2 + 1) % 4 in (2, 3)) * 2 - 1))
                wall('white', c0, c1, zf, zf_ - 0.6)
            r0, r1 = F[i], Bk[i]; nx_, ny_ = -(r1 - r0)[1], (r1 - r0)[0]; nl = math.hypot(nx_, ny_) / 0.2
            face('white', [(r0[0] - nx_ / nl, r0[1] - ny_ / nl, zf_ + 0.06), (r0[0] + nx_ / nl, r0[1] + ny_ / nl, zf_ + 0.06),
                           (r1[0] + nx_ / nl, r1[1] + ny_ / nl, zb_ + 0.06), (r1[0] - nx_ / nl, r1[1] - ny_ / nl, zb_ + 0.06)])
arcstand(126.7, 27.8, 10.0, 29.6, 1.8, 8.5, 12.0, 5, rise=1.5)
arcstand(174.7, 27.5, 4.0, 22.0, 1.8, 8.5, 12.0, 4)
# ---- south terrace: stepped rows round the south from the bowls corner to the east hill, grass bank behind
ang = lambda p: math.atan2(p[1] - CY, p[0] - CX)
a0 = max(ang(q) for q in W['bowl2']['pts']) + 0.03  # start clear of the bowls greens
a1 = min(ang(ho[0]), ang(ho[-1]))
sarc = [p for p in PITCH if a0 <= ang(p) <= a1]; sarc.sort(key=ang)
TW, TR = 11.0, 14
for i in range(len(sarc) - 1):
    p, q = sarc[i], sarc[i + 1]
    for r in range(TR):
        d0, d1 = 1.0 + TW * r / TR, 1.0 + TW * (r + 1) / TR; z0, z1 = 0.3 + 2.3 * r / TR, 0.3 + 2.3 * (r + 1) / TR
        A0, B0, A1, B1 = out(p, d0), out(q, d0), out(p, d1), out(q, d1)
        wall('steps', A0, B0, z0, z1)
        Lr = math.hypot(B0[0] - A0[0], B0[1] - A0[1]) / 4
        if r % 4 == 3 and i % 6 == 0 and i + 6 < len(sarc): barrier(A1, out(sarc[i + 6], d1), z1)
        face('tread', [(A0[0], A0[1], z1), (B0[0], B0[1], z1), (B1[0], B1[1], z1), (A1[0], A1[1], z1)], [(0, 0), (Lr, 0), (Lr, 1), (0, 1)])
    A1, B1, A2, B2 = out(p, 1 + TW), out(q, 1 + TW), out(p, 1 + TW + 12), out(q, 1 + TW + 12)
    top('bank', [(A1[0], A1[1]), (B1[0], B1[1]), (B2[0], B2[1]), (A2[0], A2[1])], lambda pt, A1=A1: 2.6 if math.hypot(pt[0] - CX, pt[1] - CY) < math.hypot(A1[0] - CX, A1[1] - CY) + 1 else 0.3)
ew = W['east_wall']['pts']
for i in range(len(ew) - 1): wall('brick', ew[i], ew[i + 1], 0, 6.4)
sw = W['south_wall']['pts']; wall('brick', sw[0], sw[1], 0, 2.4)
for n, bm in BM.items():
    me = bpy.data.meshes.new(n); bm.to_mesh(me); o = bpy.data.objects.new(n, me); me.materials.append(MATS[n])
    bpy.context.scene.collection.objects.link(o)
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB')
print('BUILD OK', len(BM))
