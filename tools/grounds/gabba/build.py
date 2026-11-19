# Gabba exterior, world metres (x east, y north, z up).
# blender -b -P build.py -- model_in.json OUT.glb OUT.blend TEXDIR
import bpy, bmesh, sys, math, json
import numpy as np
import mathutils as mu
args = sys.argv[sys.argv.index('--') + 1:]
D = json.load(open(args[0])); TEX = args[3]
K = D.get('knobs', {})
def kn(n, v): return K.get(n, v)
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('gabba'); ob = bpy.data.objects.new('gabba', me)
bpy.context.scene.collection.objects.link(ob)

def mat(name, rgb, rough=0.8, tex=None, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*[c ** 2.2 for c in rgb], 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if tex:
        t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(TEX + '/' + tex)
        m.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
    me.materials.append(m); return len(me.materials) - 1

# every texture is hand-made (mktex_hand.py -> htex/); no photo pixels
W1 = (1, 1, 1)
GR = mat('grass', W1, 0.95, 'grass.png'); SE = mat('seats', W1, 0.85, 'seats.png')
WK = mat('walk', W1, 0.9, 'concrete.png'); GL = mat('glass', W1, 0.25, 'boxglass.png')
CO = mat('concrete', W1, 0.85, 'concrete.png'); MB = mat('membrane', W1, 0.6, 'membrane.png')
ST = mat('steel', W1, 0.4, 'steel.png'); DK = mat('dark', W1, 0.9, 'darkdeck.png')
T4 = mat('t411', W1, 0.5, 't411.png'); T4S = mat('t411s', W1, 0.5, 't411_slab.png'); LM = mat('lamps', W1, 0.3, 'lamphead.png')
SI = mat('site', W1, 0.9, 'path.png'); HY = mat('hyundai', W1, 0.7, 'hyundai.png'); SC = mat('screen', W1, 0.5, 'screen.png')
SF = mat('screenface', W1, 0.3, 'scoreface.png'); RD = mat('roofdeck', W1, 0.8, 'roofdeck.png'); FA = mat('facade', W1, 0.7, 'facade_bay.png')
BOX = {CO: 4.0, WK: 4.0, DK: 4.0, RD: 6.0, SC: 4.0, T4S: 19.0, HY: 11.0, T4: 19.0, ST: 4.0, MB: 12.0}

bm = bmesh.new(); uv = bm.loops.layers.uv.new()
cx, cy = D['Cc']

def interp(a, xs, ys):
    a = (a + math.pi) % (2 * math.pi) - math.pi
    if a < xs[0] or a >= xs[-1]:
        x0, x1 = xs[-1], xs[0] + 2 * math.pi
        aa = a if a >= xs[-1] else a + 2 * math.pi
        return ys[-1] + (ys[0] - ys[-1]) * (aa - x0) / (x1 - x0)
    lo, hi = 0, len(xs) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if xs[m] <= a: lo = m
        else: hi = m
    x0, x1 = xs[lo], xs[hi]
    return ys[lo] + (ys[hi] - ys[lo]) * (a - x0) / (x1 - x0) if x1 > x0 else ys[lo]

rI = lambda a: interp(a, *D['RI']); rO = lambda a: interp(a, *D['RO'])
rF = lambda a: interp(a, *D['RF']); rP = lambda a: interp(a, *D['pitch'])
def P(a, r, z): return (cx + r * math.cos(a), cy + r * math.sin(a), z)
def face(vs, mi, uvs=None):
    f = bm.faces.new([bm.verts.new(v) for v in vs]); f.material_index = mi
    if uvs:
        for l, t in zip(f.loops, uvs): l[uv].uv = t
    return f

N = 360; A = [2 * math.pi * i / N - math.pi for i in range(N)]
FENCE = kn('fence', 6.0); ZB = kn('bowl_top', 33.0)
def prof(a):
    r0 = rP(a) + FENCE; rb = rF(a) - 2.0; rm = r0 + kn('tier_split', 0.5) * (rb - r0)
    return [(r0, 0.0), (r0, 1.6), (rm, 13.0), (rm, 13.4), (rm + 2.5, 13.4), (rm + 2.5, 16.0), (rb, ZB), (rF(a), ZB)]
# the two seat rakes are concrete steps, one row each (the real 3D seats stand on them, end of file). Same row count
# all round, so every tread is level all the way round the bowl.
ROW = 0.8
def _tiers(a):
    p = prof(a); return [(p[1][0], p[1][1], p[2][0], p[2][1]), (p[5][0], p[5][1], p[6][0], p[6][1])]
NROWS = [max(2, int(round(float(np.median([_tiers(a)[ti][2] - _tiers(a)[ti][0] for a in A])) / ROW))) for ti in (0, 1)]
def _steps(r0, z0, r1, z1, n):
    t = (r1 - r0) / n; h = (z1 - z0) / (n - 1); out = []
    for k in range(n):
        if k: out.append((r0 + k * t, z0 + k * h))
        out.append((r0 + (k + 1) * t, z0 + k * h))
    return out
def prof_s(a):
    p = prof(a); T = _tiers(a); a_ = _steps(*T[0], NROWS[0]); b_ = _steps(*T[1], NROWS[1])
    pts = [p[0], p[1]] + a_ + [(p[2][0], p[3][1]), p[4], p[5]] + b_ + [p[7]]
    mats = [WK] + [WK] * len(a_) + [WK, WK, GL] + [WK] * len(b_) + [DK]
    return pts, mats
for i in range(N):
    a0 = A[i]; a1 = a0 + 2 * math.pi / N
    (p0, MATS), (p1, _m) = prof_s(a0), prof_s(a1)
    for k in range(len(p0) - 1):
        ns = 8 if MATS[k] == SE else 1
        for j in range(ns):
            t0, t1 = j / ns, (j + 1) / ns
            L = lambda pp, t: (pp[k][0] + (pp[k + 1][0] - pp[k][0]) * t, pp[k][1] + (pp[k + 1][1] - pp[k][1]) * t)
            q = [P(a0, *L(p0, t0)), P(a1, *L(p1, t0)), P(a1, *L(p1, t1)), P(a0, *L(p0, t1))]
            dv = math.hypot(p0[k + 1][0] - p0[k][0], p0[k + 1][1] - p0[k][1]) / 12.0
            dv = dv * 3.0
            if MATS[k] == SE: uu = [(i / 24, dv * t0), ((i + 1) / 24, dv * t0), ((i + 1) / 24, dv * t1), (i / 24, dv * t1)]   # seats.png = 24 deg of bowl, 4 rows
            else:   # arc metres along, profile metres up (tile per material)
                S = 6.0 if MATS[k] == GL else 4.0; ra, rb_ = p0[k][0], p0[k + 1][0]
                cum = sum(math.hypot(p0[q_ + 1][0] - p0[q_][0], p0[q_ + 1][1] - p0[q_][1]) for q_ in range(k))
                ln = math.hypot(p0[k + 1][0] - p0[k][0], p0[k + 1][1] - p0[k][1])
                ua0, ua1 = (a0 + math.pi) * ra / S, (a1 + math.pi) * ra / S; ub0, ub1 = (a0 + math.pi) * rb_ / S, (a1 + math.pi) * rb_ / S
                vv0, vv1 = (cum / S, (cum + ln) / S) if MATS[k] != GL else (0.0, 1.0)
                if MATS[k] == GL: ub0, ub1 = ua0, ua1
                uu = [(ua0, vv0), (ua1, vv0), (ub1, vv1), (ub0, vv1)]
            face(q, MATS[k], uu)
# playing surface out to the fence
c = bm.verts.new((cx, cy, 0.02)); ring = [bm.verts.new(P(A[i], rP(A[i]) + FENCE, 0.02)) for i in range(N)]
import importlib.util as _iu
_sp = _iu.spec_from_file_location('geo_pitch', TEX + '/../geo_pitch.py'); GP = _iu.module_from_spec(_sp); _sp.loader.exec_module(GP)
gx0, gy0, gx1, gy1 = GP.box
guv = lambda v: ((v.co.x - gx0) / (gx1 - gx0), (v.co.y - gy0) / (gy1 - gy0))
# director 2026-11-18 "Leave field out": no playing field; the game draws its own grass inside the fence
B = D['booms']
# facade at rF: one real bay texture per boom bay (u 0-1 between booms, v = height / 25 m), then the dark top band
ZF = 25.0
for i in range(len(B)):
    a0 = B[i]; a1 = B[(i + 1) % len(B)]
    if a1 < a0: a1 += 2 * math.pi
    NS = 6
    for j in range(NS):
        b0 = a0 + (a1 - a0) * j / NS; b1 = a0 + (a1 - a0) * (j + 1) / NS; u0, u1 = j / NS, (j + 1) / NS
        zt = min(ZB, ZF)
        face([P(b0, rF(b0), 0), P(b1, rF(b1), 0), P(b1, rF(b1), zt), P(b0, rF(b0), zt)], FA, [(u0, 0), (u1, 0), (u1, zt / ZF), (u0, zt / ZF)])
        if ZB > ZF: face([P(b0, rF(b0), ZF), P(b1, rF(b1), ZF), P(b1, rF(b1), ZB), P(b0, rF(b0), ZB)], DK)
        # floor slab edges standing proud of the face at each level
        for zs, dep in ((kn('podium', 10.5), 1.2), (16.0, 0.5), (22.0, 0.5)):
            o0, o1 = rF(b0) + dep, rF(b1) + dep
            face([P(b0, rF(b0), zs), P(b1, rF(b1), zs), P(b1, o1, zs), P(b0, o0, zs)], CO)
            face([P(b0, o0, zs), P(b1, o1, zs), P(b1, o1, zs + 0.45), P(b0, o0, zs + 0.45)], CO)
            face([P(b0, rF(b0), zs + 0.45), P(b0, o0, zs + 0.45), P(b1, o1, zs + 0.45), P(b1, rF(b1), zs + 0.45)], CO)
zi, zo = D['zi'], D['zo']; NU, NV = 6, 8; ARCH = kn('arch', 2.5); SCAL = kn('scallop', 3.0); NU, NV = 16, 24
def roofpt(a, t, s):
    ri = rI(a) + SCAL * 4 * t * (1 - t); ro = rO(a); r = ri + (ro - ri) * s
    # saddle bay (street photo tx/e4): the outer edge hangs down between the mast tops, the middle of the bay lifts
    z = zi + (zo - zi) * s + ARCH * math.sin(math.pi * t) * (math.sin(math.pi * s) - s)
    return P(a, r, z)
for i in range(len(B)):
    a0 = B[i]; a1 = B[(i + 1) % len(B)]
    if a1 < a0: a1 += 2 * math.pi
    G = [[bm.verts.new(roofpt(a0 + (a1 - a0) * u / NU, u / NU, v / NV)) for v in range(NV + 1)] for u in range(NU + 1)]
    for u in range(NU):
        for v in range(NV):
            f = bm.faces.new((G[u][v], G[u + 1][v], G[u + 1][v + 1], G[u][v + 1])); f.material_index = MB
            for l, t in zip(f.loops, [(u / NU, v / NV), ((u + 1) / NU, v / NV), ((u + 1) / NU, (v + 1) / NV), (u / NU, (v + 1) / NV)]): l[uv].uv = t

# dark band closing the slot between the facade top and the roof underside (g49: the stand back is closed up to the roof;
# an open slot let low sun through onto the shaded east seats and field)
ZC = kn('band_top', 99.0)   # flat top of the band: above it, the roof lifts at each mast and lets the sun through (g49's lit crescents)
def _roofz(a, t, r):
    ri = rI(a) + SCAL * 4 * t * (1 - t); ro = rO(a); s = min(1.0, max(0.0, (r - ri) / (ro - ri)))
    return zi + (zo - zi) * s + ARCH * math.sin(math.pi * t) * (math.sin(math.pi * s) - s)
for i in range(len(B)):
    a0 = B[i]; a1 = B[(i + 1) % len(B)]
    if a1 < a0: a1 += 2 * math.pi
    for j in range(NU):
        t0, t1 = j / NU, (j + 1) / NU; b0 = a0 + (a1 - a0) * t0; b1 = a0 + (a1 - a0) * t1; zt = min(ZB, ZF)
        z0 = min(_roofz(b0, t0, rF(b0)) - 0.15, ZC); z1 = min(_roofz(b1, t1, rF(b1)) - 0.15, ZC)
        if z0 > zt or z1 > zt: face([P(b0, rF(b0), zt), P(b1, rF(b1), zt), P(b1, rF(b1), max(z1, zt)), P(b0, rF(b0), max(z0, zt))], DK)

def tube(p0, p1, r0, r1, m, n=8):
    a = mu.Vector(p0); b = mu.Vector(p1); d = (b - a).normalized()
    up = mu.Vector((0, 0, 1)) if abs(d.z) < 0.9 else mu.Vector((1, 0, 0))
    x = d.cross(up).normalized(); y = d.cross(x)
    ra = [bm.verts.new(a + (x * math.cos(2 * math.pi * k / n) + y * math.sin(2 * math.pi * k / n)) * r0) for k in range(n)]
    rb = [bm.verts.new(b + (x * math.cos(2 * math.pi * k / n) + y * math.sin(2 * math.pi * k / n)) * r1) for k in range(n)]
    L = (b - a).length / 4.0    # steel.png = 4 m of painted tube
    for k in range(n):
        f = bm.faces.new((ra[k], ra[(k + 1) % n], rb[(k + 1) % n], rb[k])); f.material_index = m
        u0 = k / n; u1 = (k + 1) / n
        for l, t in zip(f.loops, [(u0, 0), (u1, 0), (u1, L), (u0, L)]): l[uv].uv = t
    f = bm.faces.new(rb); f.material_index = m
    for l in f.loops: l[uv].uv = (0.5, 0.5)

GT = kn('glass_top', 25)
for i, a in enumerate(B):
    an = B[(i + 1) % len(B)]
    pin = P(a, rI(a), zi + 0.4); pout = P(a, rO(a), zo + kn('mast', 0.4))
    tube(pin, pout, 0.45, 0.45, ST)
    tube(pout, P(a, rF(a) + 0.6, ZB), 0.35, 0.35, ST)
    tube(pout, P(an, rF(an) + 0.6, GT), 0.25, 0.25, ST)
    tube(P(an, rO(an), zo), P(a, rF(a) + 0.6, GT), 0.25, 0.25, ST)
    tube(P(a, rF(a) + 0.6, 0), P(a, rF(a) + 0.6, ZB), 0.3, 0.3, ST)

def prism(poly, z0, z1, m, vh=None, nz=6, uw=10.0, vm=None, capm=None, uo=0.0):
    poly = poly[:-1] if poly[0] == poly[-1] else poly
    n = len(poly); L = 0.0
    rings = [[bm.verts.new((x, y, z0 + (z1 - z0) * j / nz)) for x, y in poly] for j in range(nz + 1)]
    for k in range(n):
        seg = math.dist(poly[k], poly[(k + 1) % n])
        for j in range(nz):
            a, b = rings[j], rings[j + 1]
            f = bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k])); f.material_index = m
            if vh:
                for l, t in zip(f.loops, [(L, j / nz), (L + seg, j / nz), (L + seg, (j + 1) / nz), (L, (j + 1) / nz)]): l[uv].uv = (t[0] / uw + uo, (z0 + (z1 - z0) * t[1]) / vm if vm else t[1])
        L += seg
    try:
        f = bm.faces.new(rings[-1]); f.material_index = m if capm is None else capm
        r = bmesh.ops.triangulate(bm, faces=[f], quad_method='BEAUTY', ngon_method='EAR_CLIP')
        bmesh.ops.subdivide_edges(bm, edges=list({e for t in r['faces'] for e in t.edges}), cuts=2, use_grid_fill=True)
    except Exception as ex:
        print('CAP', ex)
# east complex roof (photo 1283-1328 x 345-400): open-topped white plant enclosure with rounded ends, 14 x 5.6 m, 4 m tall,
# dark plant inside; five round vents beside it (photo 1312-1332 x 422-440)
_A, _B, _R = (-133.47, -44.10), (-135.11, -30.20), 2.8
_dx, _dy = _B[0] - _A[0], _B[1] - _A[1]; _L = math.hypot(_dx, _dy); _ux, _uy = _dx / _L, _dy / _L; _nx, _ny = -_uy, _ux
_th0 = math.atan2(_ny, _nx); _st = []
for k in range(13): th = _th0 - math.pi * k / 12; _st.append((_B[0] + _R * math.cos(th), _B[1] + _R * math.sin(th)))   # end bulges out past B
for k in range(13): th = _th0 + math.pi - math.pi * k / 12; _st.append((_A[0] + _R * math.cos(th), _A[1] + _R * math.sin(th)))   # and past A
_st = [(x, y) for x, y in _st]
# photo: an open white shell (walls ~4 m, 0.3 m thick), pale floor ~1.6 m below the rim, three dark round fans along it
_mx, _my = (_A[0] + _B[0]) / 2, (_A[1] + _B[1]) / 2
_in = []
for x, y in _st:                                 # 0.3 m inset: the arcs shrink in radius, the straight sides move in
    _t = (x - _mx) * _ux + (y - _my) * _uy; _cxp, _cyp = _mx + _ux * max(-_L / 2, min(_L / 2, _t)), _my + _uy * max(-_L / 2, min(_L / 2, _t))
    _d = math.hypot(x - _cxp, y - _cyp); _in.append((_cxp + (x - _cxp) * (_d - 0.3) / _d, _cyp + (y - _cyp) * (_d - 0.3) / _d))
_n = len(_st)
for _k in range(_n):
    _a, _b = _st[_k], _st[(_k + 1) % _n]; _c, _e = _in[_k], _in[(_k + 1) % _n]
    face([(_a[0], _a[1], 20.0), (_b[0], _b[1], 20.0), (_b[0], _b[1], 24.0), (_a[0], _a[1], 24.0)], RD)    # outer wall
    face([(_e[0], _e[1], 22.4), (_c[0], _c[1], 22.4), (_c[0], _c[1], 24.0), (_e[0], _e[1], 24.0)], RD)    # inner wall
    face([(_a[0], _a[1], 24.0), (_b[0], _b[1], 24.0), (_e[0], _e[1], 24.0), (_c[0], _c[1], 24.0)], RD)    # rim
prism(_in, 20.0, 22.4, RD, True, 1, 6.0)          # plant floor, capped
for _f in (0.2, 0.5, 0.8):                        # fans: grey shroud 3.2 m across, dark hub
    _fx, _fy = _A[0] + _dx * _f, _A[1] + _dy * _f
    tube((_fx, _fy, 22.4), (_fx, _fy, 23.0), 1.6, 1.6, ST, 20)       # grey fan shroud (photo: pale grey discs)
    tube((_fx, _fy, 23.0), (_fx, _fy, 23.15), 0.6, 0.6, DK, 12)      # dark hub
for vx, vy in [(-127.25, -16.88), (-130.66, -18.33), (-128.18, -13.65), (-130.32, -12.97), (-128.39, -11.5)]:
    tube((vx, vy, 20.0), (vx, vy, 20.8), 0.6, 0.6, ST, 12)
for k, poly in D["parts"].items():
    if k == "483353591": continue   # NE white building: built in sw.py from the satellite
    prism(poly, 0, 20, HY, True, 6, 11.0, 20.0, RD)   # Hyundai Centre wall, Commons e5
if D.get('t411'):   # 411 Vulture St office: outside the stadium site line, left out (director rule: model stops at the outer fence)
    prism(D['t411'], 0, D['h411'], T4, True, 6, 19.0, None, RD)
    # 411 Vulture St: a balcony slab at every floor, standing 1.0 m proud of the face (photo: serrated edge, 12 bands)
    _q = D['t411'][:-1] if D['t411'][0] == D['t411'][-1] else D['t411']
    _cx = sum(x for x, y in _q) / len(_q); _cy = sum(y for x, y in _q) / len(_q)
    _o = [(x + (x - _cx) / math.hypot(x - _cx, y - _cy) * 1.0, y + (y - _cy) / math.hypot(x - _cx, y - _cy) * 1.0) for x, y in _q]
    # slab faces sit on the photo's bright bands: bottoms 49.95 m down in 3.8 m steps, 0.7 m deep
    for lv in range(13):
        zz = 49.95 - 3.8 * lv
        prism(_o, zz, zz + 0.7, T4S, True, 1, 19.0, None, None, 0.25 * (lv % 2))   # notches alternate floor to floor
    # 411 rooftop plant (photo, unprojected at 54.1 m), clipped 1 m inside the roof edge
    def _clip(poly, x0, x1, y0, y1):
        for ax, lim, keep in ((0, x0, 1), (0, x1, -1), (1, y0, 1), (1, y1, -1)):
            out = []
            for i in range(len(poly)):
                P, Q = poly[i - 1], poly[i]
                pin, qin = (P[ax] - lim) * keep >= 0, (Q[ax] - lim) * keep >= 0
                if qin != pin:
                    t = (lim - P[ax]) / (Q[ax] - P[ax]); out.append((P[0] + t * (Q[0] - P[0]), P[1] + t * (Q[1] - P[1])))
                if qin: out.append(Q)
            poly = out
        return poly
    for _b in ([(-95.66, 76.99), (-105.17, 79.54), (-92.3, 102.87), (-83.07, 100.62)],
               [(-105.83, 88.85), (-114.25, 93.99), (-104.75, 108.67), (-97.25, 104.08)]):
        _b = _clip(_b, -110.5, -83.0, 65.5, 102.5)
        if len(_b) >= 3: prism(_b, D['h411'], D['h411'] + 2.5, SC, True, 1, 4.0, None, RD)
# far-end screen block in front of the south stand, base at the fence (photo 745-822 x 351-402)
for (x0, y0), (x1, y1) in [D.get('screen', ((-0.9, -90.6), (-22.2, -84.6)))]:
    nx, ny = x0 - cx, y0 - cy; L = math.hypot(nx, ny); nx, ny = nx / L * 2.0, ny / L * 2.0
    x0, y0, x1, y1 = x0 - nx * 1.25, y0 - ny * 1.25, x1 - nx * 1.25, y1 - ny * 1.25   # 2.5 m toward the field: clear of the seat rows
    prism([(x0, y0), (x1, y1), (x1 + nx / 2, y1 + ny / 2), (x0 + nx / 2, y0 + ny / 2)], 1.0, 19.0, SC)   # 1 m deep, top at photo y 352
    # screen face toward the field (the white box at its foot in the photo is left out: director 2026-11-18 "remove it")
    ox, oy = -nx / 2.0 * 0.06, -ny / 2.0 * 0.06
    face([(x0 + ox, y0 + oy, 1.0), (x1 + ox, y1 + oy, 1.0), (x1 + ox, y1 + oy, 19.0), (x0 + ox, y0 + oy, 19.0)], SF, [(0, 0), (1, 0), (1, 1), (0, 1)])
    bx = lambda f: (x0 + (x1 - x0) * f, y0 + (y1 - y0) * f)
    # plinth along its foot, wider than the face (photo 735-835 x 397-404: 13% past each end, 1.0 m tall, 2 m proud, the face stands on it, dark as photo)
    (lx_, ly_), (rx_, ry_) = bx(-0.13), bx(1.13); px_, py_ = -nx / 2.0 * 2.0, -ny / 2.0 * 2.0
    prism([(lx_ + nx / 2, ly_ + ny / 2), (rx_ + nx / 2, ry_ + ny / 2), (rx_ + px_, ry_ + py_), (lx_ + px_, ly_ + py_)], 0.0, 1.0, DK, True, 1, 4.0, None, DK)
exec(open('sw.py').read())   # south-west corner buildings
# concourse apron around the facade
for i in range(N):
    a0 = A[i]; a1 = a0 + 2 * math.pi / N
    ap = kn('apron', 8); s0 = (a0 + math.pi) * rF(a0) / 3.0; s1 = s0 + math.dist(P(a0, rF(a0), 0)[:2], P(a1, rF(a1), 0)[:2]) / 3.0   # path.png = 3 x 3.2 m of the real footpath (Commons e2)
    face([P(a0, rF(a0), 0.01), P(a1, rF(a1), 0.01), P(a1, rF(a1) + ap, 0.01), P(a0, rF(a0) + ap, 0.01)], SI, [(s0, 0), (s1, 0), (s1, ap / 3.2), (s0, ap / 3.2)])
for ti, (x, y, h) in enumerate(D['towers']):
    tube((x, y, 0), (x, y, h - 4), 1.3, 0.95, ST, 12)
    a = math.atan2(cy - y, cx - x); ux, uy = -math.sin(a), math.cos(a); fx, fy = math.cos(a), math.sin(a)
    # fan-shaped lamp head read off the panorama photo: 12 m wide at the top, 7.7 m at the bottom, 12 m tall
    WT, WB, Hh = 5.5, 3.5, 5.5; tl = math.radians(12)
    if ti < 2: WT, WB, Hh = WT * 0.87, WB * 0.87, Hh * 0.87   # north heads measured 13% smaller in the photo
    def hp(s, t, back=0.0):
        hw = WB + (WT - WB) * (t + 1) / 2
        return (x + ux * s * hw - fx * (1.0 + back) + fx * t * Hh * math.sin(tl), y + uy * s * hw - fy * (1.0 + back) + fy * t * Hh * math.sin(tl), h + t * Hh * math.cos(tl))
    # bbox of the crop: u = (s*hw + 6) / 12 , v = (t + 1) / 2 (crop top = head top); trapezoid fills (3/48..45/48, 3/48..45/48)
    def tuv(s, t):
        hw = WB + (WT - WB) * (t + 1) / 2; m = 3 / 48
        return (m + (1 - 2 * m) * (s * hw + WT) / (2 * WT), m + (1 - 2 * m) * (t + 1) / 2)
    cs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    face([hp(a, b) for a, b in cs], LM, [tuv(a, b) for a, b in cs])
    face([hp(a, b, 0.6) for a, b in reversed(cs)], LM, [tuv(a, b) for a, b in reversed(cs)])   # back: the lamp grid shows through from behind (photo NW and SE towers)
    for k in range(4):
        a, b = cs[k], cs[(k + 1) % 4]
        face([hp(*a), hp(*a, 0.6), hp(*b, 0.6), hp(*b)], LM, [(0.01, 0.01), (0.03, 0.01), (0.03, 0.03), (0.01, 0.03)])
bm.normal_update()
# any face still without UVs (slab edges, caps, the screen block) gets a box projection in metres / tile
nbox = 0
for f in bm.faces:
    if all(l[uv].uv.length < 1e-9 for l in f.loops):
        S = BOX.get(f.material_index, 4.0); nx, ny, nz_ = (abs(c_) for c_ in f.normal); nbox += 1
        for l in f.loops:
            x, y, z = l.vert.co
            l[uv].uv = (x / S, y / S) if nz_ >= max(nx, ny) else ((y / S, z / S) if nx >= ny else (x / S, z / S))
print('BOXUV', nbox)
bm.to_mesh(me); bm.free()

# ---------------------------------------------------------------- real 3D empty seats (as Optus): pan, back, two half legs;
# neighbours' half legs meet as one grey steel leg under each gap, block-end legs trimmed flush with the pan.
# Colour mix seat by seat as the painted seats had (g49 sunlit east stand): gold 50%, orange 15%, white 31%, blue 4%.
def _bx(x0, x1, y0, y1, z0, z1):
    return [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
_BF = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
_T = np.array(_bx(-0.20, 0.20, -0.22, 0.20, 0.40, 0.46) + _bx(-0.18, 0.18, -0.30, -0.24, 0.46, 0.86) +
              _bx(-0.25, -0.21, -0.22, 0.04, 0.0, 0.40) + _bx(0.21, 0.25, -0.22, 0.04, 0.0, 0.40))
_TF = [[f + o for f in ff] for o in (0, 8, 16, 24) for ff in _BF]
def plain(name, rgb, rough=0.55, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*[(c / 255) ** 2.2 for c in rgb], 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal; return m
SEATS = []; ASTEPS = []
AF = np.linspace(-math.pi, math.pi, 7201)
for ti in (0, 1):
    n = NROWS[ti]; TT = np.array([_tiers(a)[ti] for a in AF])
    for k in range(n):
        t = (TT[:, 2] - TT[:, 0]) / n; h = (TT[0, 3] - TT[0, 1]) / (n - 1); z = TT[0, 1] + k * h
        rr = TT[:, 0] + (k + 1) * t - 0.38
        xy = np.c_[cx + rr * np.cos(AF), cy + rr * np.sin(AF)]
        sm = np.r_[0, np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))]
        # blocks of about 24 seats (12 m at the tier's middle row) with a 1.2 m aisle stair between them, as the painted
        # seats had (aisle every 24); the aisles run straight up the rake, on the same bearings for every row
        if k == 0:
            rmid = TT[:, 0] + (n // 2 + 1) * t - 0.38; xm = np.c_[rmid * np.cos(AF), rmid * np.sin(AF)]
            smid = np.r_[0, np.cumsum(np.linalg.norm(np.diff(xm, axis=0), axis=1))]; nb = int(smid[-1] // 13.2)
            AIS = np.interp(np.arange(nb + 1) * smid[-1] / nb, smid, AF)
        for b in range(nb):
            sa, sb = np.interp(AIS[b], AF, sm), np.interp(AIS[b + 1], AF, sm); blk = sb - sa
            ns = int((blk - 1.2) // 0.5); s0 = sa + 0.6 + (blk - 1.2 - ns * 0.5) / 2
            for j in range(ns):
                s = s0 + (j + 0.5) * 0.5; a = float(np.interp(s, sm, AF)); r = float(np.interp(s, sm, rr))
                SEATS.append(((cx + r * math.cos(a), cy + r * math.sin(a), z), (-math.cos(a), -math.sin(a))))
            if k < n - 1:   # aisle stair: half steps up each riser
                a = float(AIS[b]); r0_ = float(np.interp(a, AF, TT[:, 0])); tk = float(np.interp(a, AF, t))
                rs = r0_ + (k + 1) * tk - tk / 4
                ASTEPS.append(((cx + rs * math.cos(a), cy + rs * math.sin(a), z), (-math.cos(a), -math.sin(a)), 1.2, tk / 2, h / 2))
from mathutils.bvhtree import BVHTree
from mathutils import Vector
import mathutils
PS = np.array([s[0] for s in SEATS]); fw = np.array([(*s[1], 0.0) for s in SEATS]); side = np.c_[fw[:, 1], -fw[:, 0], np.zeros(len(PS))]
me.update(); bvh = BVHTree.FromPolygons([tuple(v.co) for v in me.vertices], [list(q.vertices) for q in me.polygons])
keep = np.ones(len(PS), bool); up = Vector((0, 0, 1)); dn = Vector((0, 0, -1))
for i in range(len(PS)):   # each seat on the tread under it; dropped if the corners disagree or anything fills its space
    hz = []
    for x in (-0.21, 0.21):
        for y in (-0.26, 0.18):
            hh = bvh.ray_cast(Vector(PS[i] + x * side[i] + y * fw[i] + (0, 0, 1.0)), dn, 2.0); hz.append(None if hh[0] is None else hh[0].z)
    if None in hz or max(hz) - min(hz) > 0.02: keep[i] = False; continue
    PS[i, 2] = max(hz)
    for x in (-0.2, 0.0, 0.2):
        if bvh.ray_cast(Vector(PS[i] + x * side[i] + (0, 0, 0.05)), up, 0.85)[0] is not None: keep[i] = False
print('SEATS dropped', int((~keep).sum()))
PS, fw, side = PS[keep], fw[keep], side[keep]
FINAL = (PS, fw, side)
ci = np.random.default_rng(49).choice(4, len(PS), p=[0.50, 0.15, 0.31, 0.04])
# Lean seat mesh (glb under 50 MB): only faces that can be seen. Pan: top, front, two sides. Back: all but the bottom.
# One 8 cm steel leg under each gap (both neighbours stand on it), a 4 cm leg flush under a block end; leg sides only.
# Chunks of 800 seats keep each part under 65,536 vertices (16-bit indices).
kd = mathutils.kdtree.KDTree(len(PS))
for i, p_ in enumerate(PS): kd.insert(p_, i)
kd.balance()
PAN = (_bx(-0.20, 0.20, -0.22, 0.20, 0.40, 0.46), (1, 3, 4, 5)); BACK = (_bx(-0.18, 0.18, -0.30, -0.24, 0.46, 0.86), (1, 2, 3, 4, 5))
LEGF = (3, 4, 5)   # leg rear faces the riser 16 cm behind: never seen
mats = (plain('seat_gold', (226, 168, 30)), plain('seat_orange', (222, 120, 34)), plain('seat_white', (236, 236, 230)),
        plain('seat_blue', (34, 64, 152)), plain('seat_legs_steel', (62, 64, 67), 0.45, 0.6))
CH = 800
for c0 in range(0, len(PS), CH):
    vv = []; ff = []; mm = []
    def put(i, box, faces, mat):
        o = len(vv)
        for x, y, z in box: vv.append(tuple(PS[i] + x * side[i] + y * fw[i] + (0, 0, z)))
        for k in faces: ff.append([q + o for q in _BF[k]]); mm.append(mat)
    for i in range(c0, min(c0 + CH, len(PS))):
        put(i, PAN[0], PAN[1], int(ci[i])); put(i, BACK[0], BACK[1], int(ci[i]))
        if kd.find(PS[i] + 0.5 * side[i])[2] < 0.1: put(i, _bx(0.21, 0.29, -0.22, 0.04, 0.0, 0.40), LEGF, 4)
        else: put(i, _bx(0.16, 0.20, -0.22, 0.04, 0.0, 0.40), LEGF, 4)
        if kd.find(PS[i] - 0.5 * side[i])[2] > 0.1: put(i, _bx(-0.20, -0.16, -0.22, 0.04, 0.0, 0.40), LEGF, 4)
    sm_ = bpy.data.meshes.new('seats3d_%02d' % (c0 // CH)); sm_.from_pydata(vv, [], ff)
    for m in mats: sm_.materials.append(m)
    sm_.polygons.foreach_set('material_index', mm); sm_.update()
    bpy.context.scene.collection.objects.link(bpy.data.objects.new(sm_.name, sm_))
av = []; af = []
for p_, f_, w, d, hh in ASTEPS:
    f_ = np.array((*f_, 0.0)); sd = np.array([f_[1], -f_[0], 0.0]); o = len(av)
    av += [tuple(np.array(p_) + x * sd + y * f_ + np.array([0, 0, z_])) for x, y, z_ in _bx(-w / 2, w / 2, -d / 2, d / 2, 0, hh)]
    af += [[i + o for i in ff] for ff in _BF]
am = bpy.data.meshes.new('aisle_steps'); am.from_pydata(av, [], af); am.materials.append(plain('aisle_concrete', (182, 182, 176), 0.85))
am.update(); bpy.context.scene.collection.objects.link(bpy.data.objects.new('aisle_steps', am))
print('SEATS', len(PS), 'rows', NROWS, 'aisle steps', len(ASTEPS))
bpy.ops.wm.save_as_mainfile(filepath=args[2])
bpy.ops.export_scene.gltf(filepath=args[1], export_format='GLB', export_image_format='JPEG', export_jpeg_quality=92)
print('TRIS', sum(len(p.vertices) - 2 for p in me.polygons))
