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
        t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(TEX + '/' + tex, check_existing=True)   # one image per file: the bpy module's exporter lost duplicates' pixels
        m.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
    me.materials.append(m); return len(me.materials) - 1

# every texture is hand-made (mktex_hand.py -> htex/); no photo pixels
W1 = (1, 1, 1)
GR = mat('grass', W1, 0.95, 'grass.png'); SE = mat('seats', W1, 0.85, 'seats.png')
WK = mat('walk', W1, 0.9, 'concrete.png'); GL = mat('glass', W1, 0.25, 'boxglass_v7.png')
CO = mat('concrete', W1, 0.85, 'concrete.png'); MB = mat('membrane', W1, 0.6, 'membrane.png')
ST = mat('steel', W1, 0.4, 'steel.png'); DK = mat('dark', W1, 0.9, 'darkdeck.png')
T4 = mat('t411', W1, 0.5, 't411.png'); T4S = mat('t411s', W1, 0.5, 't411_slab.png'); LM = mat('lamps', W1, 0.3, 'lamphead.png')
SI = mat('site', W1, 0.9, 'path.png'); HY = mat('hyundai', W1, 0.7, 'hyundai.png'); SC = mat('screen', W1, 0.5, 'screen.png')
SF = mat('screenface', W1, 0.3, 'scoreface.png'); RD = mat('roofdeck', W1, 0.8, 'roofdeck.png'); FA = mat('facade', W1, 0.7, 'facade_v7.png')
RU = mat('membrane_lit_under', W1, 0.9, 'roofunder.png'); GD = mat('girder', W1, 0.6, 'girder.png')   # v7 (mktex_v7.py)
LT = mat('lattice', W1, 0.6, 'girder.png')   # the roof's lattice trusses: their own object, so a phone's Medium and Low can drop their shadows
BOX = {RU: 6.0, GD: 4.0, LT: 4.0, CO: 4.0, WK: 4.0, DK: 4.0, RD: 6.0, SC: 4.0, T4S: 19.0, HY: 11.0, T4: 19.0, ST: 4.0, MB: 12.0}

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
# the lower tier's top row (Google Earth hovers 2026-11-22: the lower rake climbs about 0.5 m a metre to 6-7 m at the
# box level, not 13 m), the box level above it 3 m deep
Z1 = kn('tier1_top', 13.0); ZU = kn('upper_front', Z1 + 3.0)
def prof(a):
    # v9 (2026-11-22): the upper tier overhangs the lower one, as at the real ground (capacity 37,478 for AFL,
    # Wikipedia; 42,000 on the venue's own page). The lower tier runs on under the upper tier's front to the boxes;
    # the upper tier starts further forward. Google Earth hovers: lower rake about 0.45 m a metre, upper tier front
    # near 10-11 m (the west screen's foot at 9 m), roof 24 m.
    r0 = rP(a) + FENCE; rb = rF(a) - 2.0
    rl = r0 + kn('lower_split', 0.70) * (rb - r0); ru = r0 + kn('upper_split', 0.45) * (rb - r0)
    return [(r0, 0.0), (r0, 1.6), (rl, Z1), (rl, Z1 + 0.4), (rl + 2.5, Z1 + 0.4), (ru, ZU), (rb, ZB), (rF(a), ZB)]
def soffit_z(a, r):
    """underside of the upper tier at radius r (0.7 m under its rake)"""
    p = prof(a); return p[5][1] - 0.7 + (r - p[5][0]) * (p[6][1] - p[5][1]) / (p[6][0] - p[5][0])
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
    pts = [p[0], p[1]] + a_ + [(p[2][0], p[3][1]), p[4], (p[4][0], Z1 + 3.06), (p[4][0], soffit_z(a, p[4][0])), (p[5][0], p[5][1] - 0.7), p[5]] + b_ + [p[7]]
    mats = [WK] + [WK] * len(a_) + [WK, WK, GL, DK, DK, DK] + [WK] * len(b_) + [DK]   # box glass, the wall over it, the upper tier's soffit, its front
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
        # v7: pale concrete at the first floor, the upper slab edges dark like the cladding (Google Earth)
        for zs, dep, sm in ((6.0, 0.8, CO), (kn('podium', 10.5), 1.2, GD), (16.0, 0.5, GD), (22.0, 0.5, GD)):
            o0, o1 = rF(b0) + dep, rF(b1) + dep
            face([P(b0, rF(b0), zs), P(b1, rF(b1), zs), P(b1, o1, zs), P(b0, o0, zs)], sm)
            face([P(b0, o0, zs), P(b1, o1, zs), P(b1, o1, zs + 0.45), P(b0, o0, zs + 0.45)], sm)
            face([P(b0, rF(b0), zs + 0.45), P(b0, o0, zs + 0.45), P(b1, o1, zs + 0.45), P(b1, rF(b1), zs + 0.45)], sm)
zi, zo = D['zi'], D['zo']; NU, NV = 6, 8; ARCH = kn('arch', 2.5); SCAL = kn('scallop', 3.0); NU, NV = 8, 12   # sag is a smooth sine: 8 x 12 a bay keeps the shape and the model under SLICE_OVER
SAG7 = 1.2; RT = 0.35   # mid-bay sag at the outer edge; the roof's thickness (top sheet over the underside)
def roofpt(a, t, s, dz=0.0):
    ri = rI(a) + SCAL * 4 * t * (1 - t); ro = rO(a); r = ri + (ro - ri) * s
    # v7 (Google Earth close-ups, 2026-11-22): each bay's sheet hangs between the rafters, most at the outer edge
    # (the scalloped fascia seen from the street), a ridge over every rafter; no tent peaks.
    z = zi + (zo - zi) * s - SAG7 * math.sin(math.pi * t) * s ** 1.5 + dz
    return P(a, r, z)
for i in range(len(B)):
    a0 = B[i]; a1 = B[(i + 1) % len(B)]
    if a1 < a0: a1 += 2 * math.pi
    G = [[bm.verts.new(roofpt(a0 + (a1 - a0) * u / NU, u / NU, v / NV)) for v in range(NV + 1)] for u in range(NU + 1)]
    for u in range(NU):
        for v in range(NV):
            f = bm.faces.new((G[u][v], G[u][v + 1], G[u + 1][v + 1], G[u + 1][v])); f.material_index = MB   # faces up
            for l, t in zip(f.loops, [(u / NU, v / NV), (u / NU, (v + 1) / NV), ((u + 1) / NU, (v + 1) / NV), ((u + 1) / NU, v / NV)]): l[uv].uv = t
    # v7: the underside, RT below (pale grey-green membrane, photo sphere 2019), faces down, and the fascia closing
    # the edge all round: the roof is a sheet with depth, not a single skin
    GU = [[bm.verts.new(roofpt(a0 + (a1 - a0) * u / NU, u / NU, v / NV, -RT)) for v in range(NV + 1)] for u in range(NU + 1)]
    for u in range(NU):
        for v in range(NV):
            f = bm.faces.new((GU[u][v], GU[u + 1][v], GU[u + 1][v + 1], GU[u][v + 1])); f.material_index = RU
            for l, t in zip(f.loops, [(u / 2, v), ((u + 1) / 2, v), ((u + 1) / 2, v + 1), (u / 2, v + 1)]): l[uv].uv = (t[0] * 0.5, t[1] * 0.25)
        for v, ok in ((0, True), (NV, False)):   # inner and outer fascia
            q = [G[u][v], G[u + 1][v], GU[u + 1][v], GU[u][v]]
            f = bm.faces.new(q if ok else q[::-1]); f.material_index = MB
            for l, t in zip(f.loops, [(0, 0), (0.1, 0), (0.1, 0.02), (0, 0.02)]): l[uv].uv = t
        # the outer fascia drops 1.2 m below the sheet's edge (Google Earth: a deep white edge, scalloped with the sag)
        o0, o1 = GU[u][NV].co, GU[u + 1][NV].co
        d0 = bm.verts.new((o0.x, o0.y, o0.z - 1.2)); d1 = bm.verts.new((o1.x, o1.y, o1.z - 1.2))
        f = bm.faces.new((GU[u + 1][NV], GU[u][NV], d0, d1)); f.material_index = MB
        for l, t in zip(f.loops, [(0, 0), (0.1, 0), (0.1, 0.02), (0, 0.02)]): l[uv].uv = t

# dark band closing the slot between the facade top and the roof underside (g49: the stand back is closed up to the roof;
# an open slot let low sun through onto the shaded east seats and field)
ZC = kn('band_top', 99.0)   # flat top of the band: above it, the roof lifts at each mast and lets the sun through (g49's lit crescents)
def _roofz(a, t, r):
    ri = rI(a) + SCAL * 4 * t * (1 - t); ro = rO(a); s = min(1.0, max(0.0, (r - ri) / (ro - ri)))
    return zi + (zo - zi) * s - SAG7 * math.sin(math.pi * t) * s ** 1.5 - RT
for i in range(len(B)):
    a0 = B[i]; a1 = B[(i + 1) % len(B)]
    if a1 < a0: a1 += 2 * math.pi
    for j in range(NU):
        t0, t1 = j / NU, (j + 1) / NU; b0 = a0 + (a1 - a0) * t0; b1 = a0 + (a1 - a0) * t1; zt = min(ZB, ZF)
        z0 = min(_roofz(b0, t0, rF(b0)) - 0.15, ZC); z1 = min(_roofz(b1, t1, rF(b1)) - 0.15, ZC)
        if z0 > zt or z1 > zt: face([P(b0, rF(b0), zt), P(b1, rF(b1), zt), P(b1, rF(b1), max(z1, zt)), P(b0, rF(b0), max(z0, zt))], DK)

def tube(p0, p1, r0, r1, m, n=8, cap=True):
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
    if not cap: return
    f = bm.faces.new(rb); f.material_index = m
    for l in f.loops: l[uv].uv = (0.5, 0.5)

# ---- v7 steel (Google Earth close-ups and the 2019 photo sphere, 2026-11-22), every member modelled, none painted:
# outside, a white column at every rafter, from the footpath through the roof's edge to 5 m above it, with a stay from its
# top down onto the roof; two white ring beams joining the columns (under the fascia and at 14 m) with a big X in every
# bay between them, and struts back to the dark wall behind. Under the roof, a dark tapered rafter at every column, a
# lighter rib down the middle of each bay, and the leading-edge truss along the inner edge.
RC = lambda a: rO(a) + 0.3                       # the column line, just outside the roof's edge
ZR1 = zo - RT - SAG7 - 1.6; ZR2 = 14.0; ZTOP = zo + 5.0   # the top ring beam just clear of the fascia at mid-bay
# v7 box fronts (2019 photo sphere): the glass sits between dark aluminium mullions every 1.5 m, with a sill at the foot,
# a transom under the LED ribbon and a capping over it, all standing proud of the glass (modelled, none painted on)
def ring_box(a, r, z0, z1, wd, dr, m):
    """a small box on the bowl at angle a: wd m wide along the arc, from radius r out to r + dr, z0 to z1"""
    h = wd / 2 / r; q = [P(a - h, r, 0)[:2], P(a + h, r, 0)[:2], P(a + h, r + dr, 0)[:2], P(a - h, r + dr, 0)[:2]]
    for k in range(4):
        if k == 0: continue   # the back sits on the glass
        p0, p1 = q[k], q[(k + 1) % 4]
        face([(*p0, z0), (*p1, z0), (*p1, z1), (*p0, z1)], m)
    face([(x_, y_, z1) for x_, y_ in q], m); face([(x_, y_, z0) for x_, y_ in q[::-1]], m)
def ring_band(r, z0, z1, dr, m, n=360):
    """a band standing dr proud of the circle of radius r(a) all round the bowl, z0 to z1 (front, top and bottom faces)"""
    for i in range(n):
        a0 = A[i]; a1 = a0 + 2 * math.pi / n; r0, r1 = r(a0), r(a1)
        face([P(a0, r0 + dr, z0), P(a1, r1 + dr, z0), P(a1, r1 + dr, z1), P(a0, r0 + dr, z1)], m)
        face([P(a0, r0, z1), P(a0, r0 + dr, z1), P(a1, r1 + dr, z1), P(a1, r1, z1)], m)
        face([P(a0, r0, z0), P(a1, r1, z0), P(a1, r1 + dr, z0), P(a0, r0 + dr, z0)], m)
def lattice_beam(a, t, s0, s1, d0, d1, w, m, n=10, rc=0.12, rw=0.06):
    """an open lattice rafter hung under the roof along the radial line at bay position t (angle a), s from s0 to s1,
    d0 -> d1 deep: two top chords w apart under the membrane, one bottom chord, and a Warren web of diagonals with a
    vertical at every node, all square hollow sections (2019 photo sphere: dark open trusses, sky showing through between the members)"""
    nrm = mu.Vector((-math.sin(a), math.cos(a), 0)) * (w / 2)
    tops, bots = [], []
    for k in range(n + 1):
        ss = s0 + (s1 - s0) * k / n; dd = d0 + (d1 - d0) * k / n
        top = mu.Vector(roofpt(a, t, ss, -RT - 0.02)) - mu.Vector((0, 0, rc))
        tops.append((top - nrm, top + nrm)); bots.append(top - mu.Vector((0, 0, dd - 2 * rc)))
    for k in range(n):
        for j in (0, 1): tube(tops[k][j], tops[k + 1][j], rc, rc, m, 4, False)                 # top chords
        tube(bots[k], bots[k + 1], rc * 1.15, rc * 1.15, m, 4, False)                          # bottom chord
        j = k % 2
        tube(tops[k][j] if k % 2 == 0 else tops[k + 1][j], bots[k + 1] if k % 2 == 0 else bots[k], rw, rw, m, 4, False)   # diagonal
        tube(tops[k][1 - j] if k % 2 == 0 else tops[k + 1][1 - j], bots[k + 1] if k % 2 == 0 else bots[k], rw, rw, m, 4, False)
    for k in range(n + 1):
        for j in (0, 1): tube(tops[k][j], bots[k], rw, rw, m, 4, False)                         # verticals, a V in section
def bx_beam(a, t, s0, s1, d0, d1, w, m, n=8):
    """a tapered box beam hung under the roof along the radial line at bay position t (angle a), s from s0 to s1,
    d0 -> d1 deep, w wide (all four sides)"""
    pts = []
    for k in range(n + 1):
        ss = s0 + (s1 - s0) * k / n; dd = d0 + (d1 - d0) * k / n
        top = mu.Vector(roofpt(a, t, ss, -RT - 0.02)); nrm = mu.Vector((-math.sin(a), math.cos(a), 0)) * (w / 2)
        pts.append((top - nrm, top + nrm, top + nrm - mu.Vector((0, 0, dd)), top - nrm - mu.Vector((0, 0, dd))))
    vs = [[bm.verts.new(q) for q in ring] for ring in pts]
    for k in range(n):
        for j in range(4):
            f = bm.faces.new((vs[k][j], vs[k + 1][j], vs[k + 1][(j + 1) % 4], vs[k][(j + 1) % 4])); f.material_index = m
    for ring in (vs[0], vs[-1][::-1]):
        f = bm.faces.new(ring); f.material_index = m
for i, a in enumerate(B):
    an = B[(i + 1) % len(B)]
    if an < a: an += 2 * math.pi
    c0 = P(a, RC(a), 0); ctop = P(a, RC(a), ZTOP)
    tube(c0, ctop, 0.38, 0.32, ST)                                              # column
    tube(ctop, roofpt(a, 0.0, 0.55, 0.15), 0.18, 0.18, ST)                      # stay onto the roof
    for zr, rr in ((ZR1, 0.30), (ZR2, 0.26)):
        tube(P(a, RC(a), zr), P(an, RC(an), zr), rr, rr, ST)                     # ring beam
        tube(P(a, RC(a), zr), P(a, rF(a), zr), 0.16, 0.16, ST)                   # strut back to the wall
    tube(P(a, RC(a), ZR2), P(an, RC(an), ZR1), 0.22, 0.22, ST)                   # the bay's X
    tube(P(an, RC(an), ZR2), P(a, RC(a), ZR1), 0.22, 0.22, ST)
    lattice_beam(a, 0.0, 0.0, 1.0, 0.9, 1.6, 0.7, LT, 12)                       # rafter: open lattice truss (1.6 m at the back: the roof is 24 m up, GE hovers 2026-11-22)
    am = a + (an - a) * 0.5
    lattice_beam(am, 0.5, 0.06, 1.0, 0.45, 1.0, 0.35, LT, 8, 0.08, 0.04)        # mid-bay rib: a lighter lattice
    # leading-edge truss: two chords along the inner edge and a zig-zag web, 1.6 m deep, 8 panels a bay
    NP = 8
    for k in range(NP):
        t0, t1 = k / NP, (k + 1) / NP; b0, b1 = a + (an - a) * t0, a + (an - a) * t1
        u0 = roofpt(b0, t0, 0.03, -RT - 0.15); u1 = roofpt(b1, t1, 0.03, -RT - 0.15)
        l0 = (u0[0], u0[1], u0[2] - 1.6); l1 = (u1[0], u1[1], u1[2] - 1.6)
        tube(u0, u1, 0.14, 0.14, LT, 6); tube(l0, l1, 0.14, 0.14, LT, 6)
        tube(l0, u1, 0.07, 0.07, LT, 5) if k % 2 == 0 else tube(u0, l1, 0.07, 0.07, LT, 5)

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
def wall_box(p0, e, n, x0, x1, d0, d1, z0, z1, m):
    """a box on a wall: x along the wall from p0 (unit e), d out from it (unit n), z up; the back face is left off"""
    W_ = lambda x, d, z: (p0[0] + e[0] * x + n[0] * d, p0[1] + e[1] * x + n[1] * d, z)
    face([W_(x0, d1, z0), W_(x1, d1, z0), W_(x1, d1, z1), W_(x0, d1, z1)], m)                # front
    face([W_(x0, d0, z1), W_(x0, d1, z1), W_(x1, d1, z1), W_(x1, d0, z1)], m)                # top
    face([W_(x0, d0, z0), W_(x1, d0, z0), W_(x1, d1, z0), W_(x0, d1, z0)], m)                # bottom
    face([W_(x0, d0, z0), W_(x0, d1, z0), W_(x0, d1, z1), W_(x0, d0, z1)], m)                # ends
    face([W_(x1, d1, z0), W_(x1, d0, z0), W_(x1, d0, z1), W_(x1, d1, z1)], m)
def hyundai_details(poly, T=11.0):
    """Hyundai Centre (Commons e5): on every 11 m bay of the wall (the texture's bay, same u), the two louvre boxes as
    real boxes, a dark frame 0.45 m proud with six white vertical fins in it, and the street-level shopfront's mullions
    and the head over it, standing proud of the glass (none of it painted on)"""
    poly = poly[:-1] if poly[0] == poly[-1] else poly
    ccx = sum(x for x, y in poly) / len(poly); ccy = sum(y for x, y in poly) / len(poly); L = 0.0
    for k in range(len(poly)):
        p0, p1 = poly[k], poly[(k + 1) % len(poly)]; seg = math.dist(p0, p1)
        if seg < 1e-6: continue
        e = ((p1[0] - p0[0]) / seg, (p1[1] - p0[1]) / seg); n = (e[1], -e[0])
        if n[0] * ((p0[0] + p1[0]) / 2 - ccx) + n[1] * ((p0[1] + p1[1]) / 2 - ccy) < 0: n = (-n[0], -n[1])
        b = math.floor(L / T) * T
        while b < L + seg:
            def has(x0, x1): return b + x0 >= L - 1e-6 and b + x1 <= L + seg + 1e-6
            off = b - L
            for zb in (6.2, 12.4):                                  # louvre boxes, 4.2 x 3.2 m
                if not has(4.5, 8.9): break
                X0, X1 = off + 4.6, off + 8.8
                wall_box(p0, e, n, X0 - 0.1, X1 + 0.1, 0.0, 0.45, zb + 3.1, zb + 3.3, GD)          # head
                wall_box(p0, e, n, X0 - 0.1, X1 + 0.1, 0.0, 0.45, zb - 0.1, zb + 0.1, GD)          # sill
                for xx in (X0 - 0.1, X1 - 0.1): wall_box(p0, e, n, xx, xx + 0.2, 0.0, 0.45, zb + 0.1, zb + 3.1, GD)
                for f_ in range(6):
                    fx = X0 + 0.2 + f_ * 0.7
                    wall_box(p0, e, n, fx, fx + 0.22, 0.05, 0.4, zb + 0.1, zb + 3.1, ST)             # white fin
            if has(3.0, 11.0):                                        # shopfront: mullions every 1.6 m, a head over it
                wall_box(p0, e, n, off + 3.0, off + 11.0, 0.0, 0.5, 3.6, 3.8, GD)
                for m_ in range(6): wall_box(p0, e, n, off + 3.0 + m_ * 1.6 - 0.05, off + 3.0 + m_ * 1.6 + 0.05, 0.0, 0.12, 0.0, 3.6, GD)
            b += T
        L += seg
for k, poly in D["parts"].items():
    if k == "483353591": continue   # NE white building: built in sw.py from the satellite
    prism(poly, 0, 20, HY, True, 6, 11.0, 20.0, RD)   # Hyundai Centre wall, Commons e5
    hyundai_details(poly)
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
# Screen (Google Earth 3D, 2023, measured 2026-11-22 from a camera solved on 290 hovers): one video screen, at the west
# end over the goals, 18.8 m wide, 9.0 m to 19.1 m up, on the upper tier's front; centred 4.6 m north of the
# long axis.
# Google Earth shows none at the north, south or east (the v7 north and south screens were wrong). It hangs on the
# front of the upper tier in a dark housing that takes the seats behind it (the build's seat test drops them).
def screen(ac, W_=18.8, H_=10.1, z0_=9.0):
    p_ = prof(ac); r_ = p_[5][0] + 0.3   # its face on the upper tier's front
    H_ = min(H_, _roofz(ac, 0.5, r_ + 4.0) - 0.3 - z0_)   # under the roof (24 m, Google Earth hovers)
    hw = W_ / 2 / r_; e0, e1 = P(ac - hw, r_, 0)[:2], P(ac + hw, r_, 0)[:2]
    ux_, uy_ = math.cos(ac), math.sin(ac); D_ = 4.0
    q = [e0, e1, (e1[0] + ux_ * D_, e1[1] + uy_ * D_), (e0[0] + ux_ * D_, e0[1] + uy_ * D_)]
    prism(q, z0_, z0_ + H_, SC, True, 1, 4.0, None, GD)
    face([(x_, y_, z0_) for x_, y_ in q[::-1]], GD)   # the housing's floor: the seat test sees it over the seats it covers
    ox, oy = -ux_ * 0.06, -uy_ * 0.06
    face([(e1[0] + ox, e1[1] + oy, z0_), (e0[0] + ox, e0[1] + oy, z0_), (e0[0] + ox, e0[1] + oy, z0_ + H_), (e1[0] + ox, e1[1] + oy, z0_ + H_)], SF, [(0, 0), (1, 0), (1, 1), (0, 1)])
screen(math.pi - math.atan2(4.6, 105.5))    # the west end
_rbx = lambda a: prof(a)[4][0]          # the box glass line (rm + 2.5)
ZLED = Z1 + 3.0 - 0.9
ring_band(_rbx, Z1 + 0.4, Z1 + 0.55, 0.14, GD); ring_band(_rbx, ZLED - 0.08, ZLED + 0.04, 0.12, GD); ring_band(_rbx, Z1 + 2.92, Z1 + 3.06, 0.16, GD)
_mx = 0.0; _prev = P(A[0], _rbx(A[0]), 0)[:2]
for i in range(1, N * 4 + 1):     # a mullion every 1.5 m of arc
    a_ = -math.pi + 2 * math.pi * i / (N * 4); q_ = P(a_, _rbx(a_), 0)[:2]; _mx += math.dist(_prev, q_); _prev = q_
    if _mx >= 1.5:
        _mx -= 1.5; ring_box(a_, _rbx(a_), Z1 + 0.55, ZLED - 0.08, 0.07, 0.11, GD)
exec(open('sw.py').read())   # south-west corner buildings
# concourse apron around the facade
for i in range(N):
    a0 = A[i]; a1 = a0 + 2 * math.pi / N
    ap = kn('apron', 8); s0 = (a0 + math.pi) * rF(a0) / 3.0; s1 = s0 + math.dist(P(a0, rF(a0), 0)[:2], P(a1, rF(a1), 0)[:2]) / 3.0   # path.png = 3 x 3.2 m of the real footpath (Commons e2)
    face([P(a0, rF(a0), 0.01), P(a1, rF(a1), 0.01), P(a1, rF(a1) + ap, 0.01), P(a0, rF(a0) + ap, 0.01)], SI, [(s0, 0), (s1, 0), (s1, ap / 3.2), (s0, ap / 3.2)])
for ti, (x, y, h) in enumerate(D['towers']):
    tube((x, y, 0), (x, y, h - 1.0), 1.3, 0.95, ST, 12)
    # v7 head (2019 photo sphere): an open white basket widening upward, an arc of eleven ribs turned to the field
    # with four rails of lamps between them and the ribs' tips standing clear above the top rail; every member
    # modelled. The lamps' faces (material "lamps") look at the middle of the ground.
    a = math.atan2(cy - y, cx - x); sk = 0.87 if ti < 2 else 1.0   # north heads 13% smaller (photo g49)
    def hp(th, r, z): return (x + r * math.cos(a + th), y + r * math.sin(a + th), h + z)
    NR = 11; TH = [math.radians(-55 + 110 * k / (NR - 1)) for k in range(NR)]
    rb_, rt_, zb_, zt_ = 1.0 * sk, 5.2 * sk, -1.0, 8.5 * sk
    for th in TH:
        tube(hp(th, rb_, zb_), hp(th, rt_, zt_), 0.14, 0.12, ST, 6)
        tube(hp(th, rt_, zt_), hp(th, rt_ + 0.35 * sk, zt_ + 1.6 * sk), 0.1, 0.06, ST, 5)    # the rib's tip
    for q in range(4):
        f_ = (q + 0.6) / 4.2; rr = rb_ + (rt_ - rb_) * f_; zz = zb_ + (zt_ - zb_) * f_
        for k in range(NR - 1):
            tube(hp(TH[k], rr, zz), hp(TH[k + 1], rr, zz), 0.08, 0.08, ST, 5)                  # rail
            for j in (0.3, 0.7):                                                                 # two lamps a bay
                th = TH[k] + (TH[k + 1] - TH[k]) * j; c_ = mu.Vector(hp(th, rr + 0.25, zz + 0.45))
                fwd = (mu.Vector((cx, cy, 0)) - mu.Vector((c_.x, c_.y, 0))).normalized(); fwd.z = -0.35; fwd.normalize()
                sd = fwd.cross(mu.Vector((0, 0, 1))).normalized(); up_ = sd.cross(fwd).normalized()
                w, hh, d = 0.32 * sk, 0.28 * sk, 0.35
                cs = [c_ + sd * sx * w + up_ * sy * hh for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                back = [v - fwd * d for v in cs]
                face([tuple(v) for v in cs], LM, [(0.3, 0.3), (0.7, 0.3), (0.7, 0.7), (0.3, 0.7)])     # lamp glass
                for m_ in range(4):
                    face([tuple(cs[m_]), tuple(back[m_]), tuple(back[(m_ + 1) % 4]), tuple(cs[(m_ + 1) % 4])], ST)
                face([tuple(v) for v in back[::-1]], ST)
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
# the lattice trusses as their own object ("lattice"): the match drops their shadows on Medium and Low (Oval3DQuality)
_lm = me.copy(); _lm.name = 'lattice'
for _m, _keep in ((me, False), (_lm, True)):
    _b = bmesh.new(); _b.from_mesh(_m)
    bmesh.ops.delete(_b, geom=[f for f in _b.faces if (f.material_index == LT) != _keep], context='FACES')
    _b.to_mesh(_m); _b.free()
bpy.context.scene.collection.objects.link(bpy.data.objects.new('lattice', _lm))

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
SEATS = []; ASTEPS = []; BLK = []
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
                SEATS.append(((cx + r * math.cos(a), cy + r * math.sin(a), z), (-math.cos(a), -math.sin(a)))); BLK.append((ti, b, k // 6))
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
    for x, y in ((-0.2, 0.0), (0.0, 0.0), (0.2, 0.0), (0.0, -0.25), (0.0, 0.2)):
        if bvh.ray_cast(Vector(PS[i] + x * side[i] + y * fw[i] + (0, 0, 0.05)), up, 2.1)[0] is not None: keep[i] = False   # the seat rule's 2 m headroom (tools/grounds/seat_rule.gd)
print('SEATS dropped', int((~keep).sum()))
PS, fw, side = PS[keep], fw[keep], side[keep]; BLK = [b_ for b_, k_ in zip(BLK, keep) if k_]
FINAL = (PS, fw, side)
# v7 seat colours (photo sphere from the ground, 2019): gold above all, maroon in whole blocks and bands, some white.
# Each block of a tier, six rows deep, takes one mix: gold (most), maroon or white-flecked.
_rng = np.random.default_rng(49); _mix = {}
MIX = {'g': [0.86, 0.10, 0.04], 'm': [0.18, 0.78, 0.04], 'w': [0.40, 0.15, 0.45]}
ci = np.zeros(len(PS), int)
for i_, key in enumerate(BLK):
    if key not in _mix: _mix[key] = _rng.choice(['g', 'm', 'w'], p=[0.62, 0.26, 0.12])
    ci[i_] = _rng.choice(3, p=MIX[_mix[key]])
# Lean seat mesh (glb under 50 MB): only faces that can be seen. Pan: top, front, two sides. Back: all but the bottom.
# One 8 cm steel leg under each gap (both neighbours stand on it), a 4 cm leg flush under a block end; leg sides only.
# Chunks of 800 seats keep each part under 65,536 vertices (16-bit indices).
kd = mathutils.kdtree.KDTree(len(PS))
for i, p_ in enumerate(PS): kd.insert(p_, i)
kd.balance()
PAN = (_bx(-0.20, 0.20, -0.22, 0.20, 0.40, 0.46), (1, 3, 4, 5)); BACK = (_bx(-0.18, 0.18, -0.30, -0.24, 0.46, 0.86), (1, 2, 3, 4, 5))
LEGF = (3, 4, 5)   # leg rear faces the riser 16 cm behind: never seen
# Seats as the MCG: one seat drawn many times (MultiMesh), not meshes in the glb. seat_tmpl.bin and leg_tmpl.bin are
# float32 triangles in Godot axes (y up), outward faces counter-clockwise; seats_seat_<colour>.bin and legs_steel.bin
# hold a row-major 3x4 transform per seat or leg. A shared 8 cm leg under each gap; a block end gets a 4 cm leg
# (the leg template squeezed to half width), flush under the pan.
import os
OUTD = os.path.dirname(os.path.abspath(args[1]))
C = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)   # Blender (x, y, z) -> Godot (x, z, -y)
def tris(boxfaces):
    out = []
    for box, faces in boxfaces:
        for k in faces:
            q = [C @ np.array(box[j]) for j in _BF[k]]; out += [q[0], q[1], q[2], q[0], q[2], q[3]]
    return np.array(out, '<f4')
tris([PAN, BACK]).tofile(OUTD + '/seat_tmpl.bin')
tris([(_bx(-0.04, 0.04, -0.22, 0.04, 0.0, 0.40), LEGF)]).tofile(OUTD + '/leg_tmpl.bin')
def xf(o, sd, f, sx=1.0):
    B = np.c_[sd * sx, f, (0, 0, 1.0)]; R = C @ B @ C.T
    return np.c_[R, C @ o].astype('<f4').ravel()
SN = ('seat_gold', 'seat_maroon', 'seat_white'); XS = {n: [] for n in SN}; XL = []
for i in range(len(PS)):
    XS[SN[int(ci[i])]].append(xf(PS[i], side[i], fw[i]))
    if kd.find(PS[i] + 0.5 * side[i])[2] < 0.1: XL.append(xf(PS[i] + 0.25 * side[i], side[i], fw[i]))
    else: XL.append(xf(PS[i] + 0.18 * side[i], side[i], fw[i], 0.5))
    if kd.find(PS[i] - 0.5 * side[i])[2] > 0.1: XL.append(xf(PS[i] - 0.18 * side[i], side[i], fw[i], 0.5))
for n in SN: np.array(XS[n], '<f4').tofile(OUTD + '/seats_%s.bin' % n)
np.array(XL, '<f4').tofile(OUTD + '/legs_steel.bin')
print('SEAT BINS', {n: len(XS[n]) for n in SN}, 'legs', len(XL))
av = []; af = []
for p_, f_, w, d, hh in ASTEPS:
    f_ = np.array((*f_, 0.0)); sd = np.array([f_[1], -f_[0], 0.0]); o = len(av)
    av += [tuple(np.array(p_) + x * sd + y * f_ + np.array([0, 0, z_])) for x, y, z_ in _bx(-w / 2, w / 2, -d / 2, d / 2, 0, hh)]
    af += [[i + o for i in ff] for ff in _BF]
am = bpy.data.meshes.new('aisle_steps'); am.from_pydata(av, [], af); am.materials.append(plain('aisle_concrete', (182, 182, 176), 0.85))
am.update(); bpy.context.scene.collection.objects.link(bpy.data.objects.new('aisle_steps', am))
print('SEATS', len(PS), 'rows', NROWS, 'aisle steps', len(ASTEPS))
for im in bpy.data.images:   # textures as the MCG: 512 px at most, WebP
    if im.size[0] and max(im.size) > 512:
        k = 512 / max(im.size); im.scale(max(1, round(im.size[0] * k)), max(1, round(im.size[1] * k))); im.pack()   # packed: the glTF exporter reads the scaled pixels (the bpy module failed on an unpacked scaled image)
for im in bpy.data.images:   # load and pack every texture before export (the bpy module's exporter read unloaded ones as empty)
    if im.source == 'FILE' and not im.packed_file:
        im.reload(); im.pack()
bpy.ops.wm.save_as_mainfile(filepath=args[2])
bpy.ops.export_scene.gltf(filepath=args[1], export_format='GLB', export_image_format=os.environ.get('GABBA_IMG', 'WEBP'))   # GABBA_IMG=AUTO (PNG) where the bpy module's WebP copy fails
print('TRIS', sum(len(p.vertices) - 2 for p in me.polygons), 'lattice', sum(len(p.vertices) - 2 for p in _lm.polygons))
