# Manuka Oval (Canberra) as it is in 2026, rebuilt to the MCG standard (docs/MCG_STANDARD.md). Runs inside Blender
# (pip bpy 5.2.4 works): import build; build.build_all(). Frame: x east, y north, z up, metres, origin at the OSM
# pitch way's node centroid. Every stand is swept round the fence from manuka.json: real stepped rows (a riser and a
# tread a row) carrying instanced 3D seats (seat_list()), roofs with thickness, fascias and soffits, modelled frames,
# fins, recesses and openings. Nothing that has depth in the real ground is painted on.
import bpy, math, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from mb import MB, rect, ccw, TILE, Frame, earclip, roof as hip_roof, window
D = json.load(open(os.path.join(HERE, 'manuka.json')))
G = json.load(open(os.path.join(HERE, '..', 'osm', 'geo.json')))
C = np.array(D['C'])
STEP = 0.5

# ---------------- the frame round the fence ----------------
_p = np.array(G['pitch']) - C
_b = np.degrees(np.arctan2(_p[:, 0], _p[:, 1])) % 360; _r = np.hypot(_p[:, 0], _p[:, 1]); _o = np.argsort(_b)
# The fence is smoothed a little: the OSM outline's nodes sit about 5 m apart, and the rows must not kink at them.
_bs = np.arange(0, 360, 0.5)
_rs = np.interp(_bs, _b[_o], _r[_o], period=360)
_k = np.exp(-0.5 * (np.arange(-8, 9) / 3.0) ** 2); _k /= _k.sum()
_rs = np.convolve(np.concatenate([_rs[-8:], _rs, _rs[:8]]), _k, 'valid')


def rf(b):
    return float(np.interp(b % 360, _bs, _rs, period=360))


def pol(b, r):
    a = math.radians(b); return (C[0] + r * math.sin(a), C[1] + r * math.cos(a))


def P3(b, r, z):
    return (*pol(b, r), z)


def Q(b, d, z):
    """bearing, metres past the fence, height"""
    return P3(b, rf(b) + d, z)


def arc(b0, b1, step=STEP):
    n = max(1, int(round(abs(b1 - b0) / step))); return list(np.linspace(b0, b1, n + 1))


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


def strip(mb, bs, A, B, m, tu=None):
    """Quad strip between section points A(b) -> (d, z) and B(b) -> (d, z) over bearings bs (d past the fence).
    UV: u = arc length / tile (rows and ribs run round the ground), v = length along the section / tile."""
    tu_, tv = TILE.get(m, (1, 1)); tu = tu or tu_; kk = math.pi / 180
    for b0, b1 in zip(bs, bs[1:]):
        a0, a1, c0, c1 = A(b0), A(b1), B(b0), B(b1)
        rm = 0.25 * (a0[0] + a1[0] + c0[0] + c1[0]) + rf(0.5 * (b0 + b1)); L = math.hypot(c0[0] - a0[0], c0[1] - a0[1])
        u0 = b0 * kk * rm / tu; u1 = b1 * kk * rm / tu
        mb.face([Q(b0, *a0), Q(b1, *a1), Q(b1, *c1), Q(b0, *c0)], m, uv=[(u0, 0), (u1, 0), (u1, L / tv), (u0, L / tv)])


def endcap(mb, b, S, m, flip=False):
    """Close a section at bearing b: S = [(d, z), ...] polygon."""
    poly2 = [(d, z) for d, z in S]
    sgn = 1 if sum(poly2[i][0] * poly2[(i + 1) % len(poly2)][1] - poly2[(i + 1) % len(poly2)][0] * poly2[i][1]
                   for i in range(len(poly2))) > 0 else -1
    for tri_ in earclip(poly2 if sgn > 0 else poly2[::-1]):
        q = [Q(b, d, z) for d, z in tri_]
        mb.face(q[::-1] if flip else q, m)


def sweep(mb, bs, sec, cap0=True, cap1=True, capm='conc'):
    """sec(b) -> [(d, z, material of the segment ending here), ...]; faces each segment over bs, caps the ends."""
    S = [sec(b) for b in bs]; n = len(S[0])
    for k in range(1, n):
        m = S[0][k][2]
        if m is None: continue
        strip(mb, bs, lambda b, k=k: sec(b)[k - 1][:2], lambda b, k=k: sec(b)[k][:2], m)
    outline = lambda s: [(p[0], p[1]) for p in s] + [(s[-1][0], 0.0), (s[0][0], 0.0)]
    if cap0: endcap(mb, bs[0], outline(S[0]), capm, flip=False)
    if cap1: endcap(mb, bs[-1], outline(S[-1]), capm, flip=True)


def stepped(d0, z0, d1, z1, n, mt='tread', mr='riser'):
    out = []; run = (d1 - d0) / n; rise = (z1 - z0) / n
    for k in range(n):
        out += [(d0 + k * run, z0 + (k + 1) * rise, mr), (d0 + (k + 1) * run, z0 + (k + 1) * rise, mt)]
    return out


def tangent(b):
    a = math.radians(b); return np.array([math.cos(a), -math.sin(a), 0.0])


def radial(b):
    a = math.radians(b); return np.array([math.sin(a), math.cos(a), 0.0])


def in_range(b, b0, b1):
    b = b % 360; b0 %= 360; b1 %= 360
    return b0 <= b <= b1 if b0 <= b1 else (b >= b0 or b <= b1)


# ---------------- the boundary fence and the low front terrace all round ----------------
L = D['lower']; FZ = D['fence_h']


def lower_ranges():
    """bearing ranges of the low terrace: everywhere but the east bank (and the Bradman takes its own)"""
    return [(133.0, 258.0), (293.0, 417.0)]


def lower_sec(b):
    return ([(0.0, 0.0, None), (0.0, FZ, 'fence'), (0.25, FZ, 'fence_top'), (L['d0'], FZ, 'conc')]
            + stepped(L['d0'], L['z0'], L['d1'], L['z1'], L['rows'])
            + [(L['conc'], L['z1'], 'concourse')])


def lower_all(col):
    mb = MB('lower_terrace')
    for b0, b1 in lower_ranges():
        bs = arc(b0, b1)
        # the concourse runs back under each stand's tier; where nothing stands behind, its back edge drops to the ground
        sweep(mb, bs, lower_sec, cap0=False, cap1=False)
    mb.build(col)


# ---------------- the A-frame stands: Hawke Terrace (north), the west stand, the south-east stand ----------------
def astand_sec(S):
    def sec(b):
        return ([(L['conc'], L['z1'], None), (S['d0'], L['z1'], 'concourse'), (S['d0'], S['z0'], 'tier_wall')]
                + stepped(S['d0'], S['z0'], S['d1'], S['z1'], S['rows'])
                + [(S['d1'] + 0.8, S['z1'], 'conc'), (S['d1'] + 0.8, S['rbz'] - 0.45, 'backwall'),
                   (S['rb'] + 0.3, S['rbz'] - 0.45, 'conc_dk'), (S['rb'] + 0.3, 0.0, 'render_white')])
    return sec


def roof_band(mb, bs, S, m_top='roof_grey', m_soffit='roof_soffit', fascia='fascia_dark'):
    """A roof with thickness: deck, soffit, a deep front fascia and a back edge."""
    th = 0.35
    top = lambda b: [(S['rf'], S['rfz']), (S['rb'], S['rbz'])]
    strip(mb, bs, lambda b: (S['rf'], S['rfz']), lambda b: (S['rb'], S['rbz']), m_top)
    strip(mb, bs, lambda b: (S['rb'], S['rbz'] - th), lambda b: (S['rf'], S['rfz'] - th), m_soffit)
    strip(mb, bs, lambda b: (S['rf'] - 0.05, S['rfz'] - 1.0), lambda b: (S['rf'] - 0.05, S['rfz'] + 0.12), fascia)
    strip(mb, bs, lambda b: (S['rf'] - 0.05, S['rfz'] + 0.12), lambda b: (S['rf'] + 0.25, S['rfz'] + 0.12), 'steel_galv')
    strip(mb, bs, lambda b: (S['rf'] + 0.25, S['rfz'] - 1.0), lambda b: (S['rf'] - 0.05, S['rfz'] - 1.0), 'steel_galv')
    strip(mb, bs, lambda b: (S['rb'], S['rbz'] - th), lambda b: (S['rb'], S['rbz'] + 0.1), 'steel_galv')
    for b, fl in ((bs[0], False), (bs[-1], True)):
        endcap(mb, b, [(S['rf'] - 0.05, S['rfz'] - 1.0), (S['rf'] + 0.25, S['rfz'] - 1.0), (S['rb'], S['rbz'] - th),
                       (S['rb'], S['rbz'] + 0.1), (S['rf'] - 0.05, S['rfz'] + 0.12)], 'fascia_dark', flip=fl)


def aframes(mb, b0, b1, S, every=18.0):
    """White tubular A-frames standing on the roof (Google Earth from the field): two legs splayed along the roof's
    front, an apex 3 m above it, a tie back to the roof's rear; one each ~18 m round the stand."""
    r = rf(0.5 * (b0 + b1)) + S['rf']; L_ = math.radians((b1 - b0) % 360 or 360) * r
    n = max(1, int(round(L_ / every)))
    for i in range(n + 1):
        b = b0 + ((b1 - b0) % 360) * i / n
        if i in (0, n):
            b = b0 + (0.6 if i == 0 else ((b1 - b0) % 360) - 0.6)
        d = S['rf'] + 1.2; z = S['rfz'] + (S['rbz'] - S['rfz']) * (d - S['rf']) / (S['rb'] - S['rf'])
        c = np.array(Q(b, d, z)); t = tangent(b); up = np.array([0, 0, 1.0])
        apex = c + up * 3.0
        for s in (-1, 1):
            mb.beam(tuple(c + t * s * 2.2), tuple(apex), 0.22, 0.22, 'steel_white')
        mb.beam(tuple(apex), tuple(np.array(Q(b, S['rb'] - 1.0, S['rbz'] + 0.1))), 0.12, 0.12, 'steel_white')
        mb.beam(tuple(apex), tuple(np.array(Q(b, S['rf'] - 0.1, S['rfz'] + 0.1))), 0.1, 0.1, 'steel_white')
        mb.box(tuple(apex[:2]), 0.4, 0.4, 0.3, b, 'steel_white', z0=apex[2] - 0.1)


def roof_posts(mb, b0, b1, S, every=9.0):
    """Columns at the back of the tier carrying the roof, and a raking beam under the soffit to each."""
    r = rf(0.5 * (b0 + b1)) + S['d1']; L_ = math.radians((b1 - b0) % 360 or 360) * r
    n = max(1, int(round(L_ / every)))
    for i in range(n + 1):
        b = b0 + ((b1 - b0) % 360) * i / n
        p = Q(b, S['d1'] + 0.5, S['z1']); q = Q(b, S['d1'] + 0.5, S['rbz'] - 0.4)
        mb.beam(p, q, 0.35, 0.35, 'steel_galv')
        mb.beam(Q(b, S['rf'] + 0.3, S['rfz'] - 0.75), Q(b, S['rb'], S['rbz'] - 0.75), 0.25, 0.45, 'steel_galv')


def astands(col):
    for name, S in ((k, v) for k, v in D['astands'].items() if not k.startswith('_')):
        mb = MB('stand_' + name); bs = arc(S['b0'], S['b1'])
        sweep(mb, bs, astand_sec(S), capm='conc')
        roof_band(mb, bs, S)
        aframes(mb, S['b0'], S['b1'], S); roof_posts(mb, S['b0'], S['b1'], S)
        # handrail along the front of the tier, above the concourse
        strip(mb, bs, lambda b: (S['d0'] - 0.05, S['z0']), lambda b: (S['d0'] - 0.05, S['z0'] + 1.0), 'glass_rail')
        mb.build(col)
    # The north-west link between the Bradman and Hawke Terrace: same tier, a translucent canopy over the gate.
    mb = MB('nw_canopy'); S = D['astands']['north']
    bs = arc(304.0, 312.0)
    strip(mb, bs, lambda b: (S['rf'] + 2.0, S['rfz'] + 0.6), lambda b: (S['rb'], S['rbz'] + 0.6), 'canopy_glass')
    for b in (304.0, 308.0, 312.0):
        mb.beam(Q(b, S['rf'] + 2.0, S['rfz'] + 0.6), Q(b, S['rb'], S['rbz'] + 0.6), 0.18, 0.3, 'steel_white')
    mb.build(col)


# ---------------- the Bradman Stand ----------------
B = D['bradman']


def bradman_sec(b):
    n5 = L['bradman_rows']; run = (L['d1'] - L['d0']) / L['rows']; rise = (L['z1'] - L['z0']) / L['rows']
    d5 = L['d0'] + n5 * run; z5 = L['z0'] + n5 * rise
    return ([(0.0, 0.0, None), (0.0, FZ, 'fence'), (0.25, FZ, 'fence_top'), (L['d0'], FZ, 'conc')]
            + stepped(L['d0'], L['z0'], d5, z5, n5)
            + [(B['d0'], z5, 'concourse'), (B['d0'], B['z0'], 'plinth')]
            + stepped(B['d0'], B['z0'], B['d1'], B['z1'], B['rows'])
            + [(B['d1'] + 1.2, B['z1'], 'conc'), (B['d1'] + 1.2, B['soffit_back'], 'box_glass'),
               (B['back'], B['soffit_back'], None), (B['back'], 0.0, None)])


def bradman_plan():
    """The roof's outline: OSM's Bradman Stand way, its front edge pulled to roof_front past the fence."""
    return [tuple(p) for p in G['122524193'][:-1]]


def bradman(col):
    mb = MB('bradman'); bs = arc(B['b0'], B['b1'])
    sweep(mb, bs, bradman_sec, capm='render_white')
    # vomitories up through the upper tier: concrete portals with a dark tunnel set into them, roofs at the boxes
    for vb in B['voms']:
        w = 1.4; r0 = rf(vb) + B['d0'] + 6.0; r1 = rf(vb) + B['d1'] + 1.0
        zb = B['z0'] + 6.0 * (B['z1'] - B['z0']) / (B['d1'] - B['d0'])
        u = radial(vb); t = tangent(vb); o = np.array([*pol(vb, 0), 0.0])
        P = lambda r, s, z: tuple(o + u * r + t * s + np.array([0, 0, z]))
        for s in (-1, 1):
            mb.face([P(r0, s * w, zb - 0.2), P(r1, s * w, zb - 0.2), P(r1, s * w, B['z1'] + 0.3), P(r0, s * w, zb + 2.6)][::s], 'plinth')
            mb.face([P(r0, s * (w - 0.25), zb - 0.2), P(r0, s * (w - 0.25), zb + 2.4), P(r1, s * (w - 0.25), B['z1'] + 0.1), P(r1, s * (w - 0.25), zb - 0.2)][::s], 'vom_dark')
        mb.face([P(r0, -w, zb + 2.6), P(r1, -w, B['z1'] + 0.3), P(r1, w, B['z1'] + 0.3), P(r0, w, zb + 2.6)], 'plinth')
        mb.face([P(r0, -w + 0.25, zb - 0.15), P(r0, w - 0.25, zb - 0.15), P(r1, w - 0.25, zb - 0.15), P(r1, -w + 0.25, zb - 0.15)], 'tread')
        mb.face([P(r0, -w, zb + 2.4), P(r0, w, zb + 2.4), P(r0, w, zb + 2.6), P(r0, -w, zb + 2.6)][::-1], 'plinth')
        mb.face([P(r1 - 0.1, -w, zb - 0.2), P(r1 - 0.1, w, zb - 0.2), P(r1 - 0.1, w, B['z1']), P(r1 - 0.1, -w, B['z1'])][::-1], 'vom_dark')
    mb.build(col)
    # the roof: a deep white slab over OSM's footprint, fascia 2.6 m, the soffit falling to the boxes
    mb = MB('bradman_roof'); poly = ccw(bradman_plan()); top = B['roof_top']
    # each vertex's soffit height by how far it is from the field
    def soff(p):
        d = math.hypot(p[0] - C[0], p[1] - C[1]); b = math.degrees(math.atan2(p[0] - C[0], p[1] - C[1])) % 360
        dd = d - rf(b); f = np.clip((dd - B['roof_front']) / (B['back'] - B['roof_front']), 0, 1)
        return B['soffit_front'] + (B['soffit_back'] - B['soffit_front']) * f
    mb.cap(poly, top, 'roof_white')
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        mb.face([(*p, soff(p)), (*q, soff(q)), (*q, top), (*p, top)], 'fascia_white')
    for tri_ in earclip(poly):
        mb.face([(x, y, soff((x, y))) for x, y in tri_][::-1], 'roof_soffit')
    # a raised parapet strip round the edge and plant boxes on the deck (GE from above)
    for i in range(n):
        p, q = np.array(poly[i]), np.array(poly[(i + 1) % n]); e = q - p; L_ = np.linalg.norm(e)
        if L_ < 1.0: continue
        nn = np.array([e[1], -e[0]]) / L_
        a, b2 = p - nn * 0.35, q - nn * 0.35
        mb.face([(*p, top), (*q, top), (*q, top + 0.35), (*p, top + 0.35)], 'fascia_white')
        mb.face([(*b2, top), (*a, top), (*a, top + 0.35), (*b2, top + 0.35)], 'fascia_white')
        mb.face([(*p, top + 0.35), (*q, top + 0.35), (*b2, top + 0.35), (*a, top + 0.35)], 'fascia_white')
    for (x, y, l, w) in ((-86.0, 2.0, 6.0, 3.0), (-82.0, 18.0, 4.0, 3.0), (-90.0, -10.0, 3.0, 2.5)):
        mb.box((x, y), l, w, 1.8, 15.0, 'plant', z0=top, mtop='plant')
    # the stand's back: three storeys under the roof, a glazed top floor behind louvres (Google Earth from the west)
    back = []
    for p, q in zip(poly, poly[1:] + poly[:1]):
        mid = (np.array(p) + np.array(q)) / 2; d = math.hypot(mid[0] - C[0], mid[1] - C[1])
        b = math.degrees(math.atan2(mid[0] - C[0], mid[1] - C[1])) % 360
        if d - rf(b) > B['back'] - 6.0 and np.hypot(*(np.array(q) - np.array(p))) > 4.0:
            back.append((p, q))
    for p, q in back:
        p = np.array(p); q = np.array(q); e = q - p; L_ = np.linalg.norm(e); t = e / L_; nn = np.array([t[1], -t[0]])
        inset = 1.6
        A_ = p + nn * -inset; B_ = q + nn * -inset
        mb.face([(*A_, 0.0), (*B_, 0.0), (*B_, 4.2), (*A_, 4.2)], 'render_white')
        mb.face([(*A_, 4.2), (*B_, 4.2), (*B_, 8.0), (*A_, 8.0)], 'render_white')
        mb.face([(*A_, 8.0), (*B_, 8.0), (*B_, soff(tuple(q)) - 0.1), (*A_, soff(tuple(p)) - 0.1)], 'box_glass')
        # louvre fins standing 0.6 m proud of the top-floor glass every 1.2 m
        k = int(L_ / 1.2)
        for j in range(k + 1):
            c = A_ + t * (j * L_ / k) + nn * 0.3
            mb.box(tuple(c), 0.08, 0.6, soff(tuple(p)) - 8.2, math.degrees(math.atan2(t[1], t[0])), 'steel_white', z0=8.1)
        # floor slabs proud of the wall, windows set into the first two floors
        for z in (4.2, 8.0):
            mb.face([(*(A_ + nn * 0.45), z), (*(B_ + nn * 0.45), z), (*(B_ + nn * 0.45), z + 0.3), (*(A_ + nn * 0.45), z + 0.3)], 'render_white')
            mb.face([(*A_, z + 0.3), (*B_, z + 0.3), (*(B_ + nn * 0.45), z + 0.3), (*(A_ + nn * 0.45), z + 0.3)], 'render_white')
            mb.face([(*(A_ + nn * 0.45), z), (*A_, z), (*B_, z), (*(B_ + nn * 0.45), z)], 'render_white')
        for j in range(int(L_ / 3.0)):
            a_ = j * 3.0 + 0.6; b_ = a_ + 1.8
            if b_ > L_ - 0.4: break
            window(mb, tuple(A_), tuple(B_), a_, b_, 5.0, 7.2, glass='win_dark', frame='steel_white')
            window(mb, tuple(A_), tuple(B_), a_, b_, 1.0, 3.4, glass='win_dark', frame='steel_white')
    mb.build(col)


# ---------------- the red-seat terraces (east) ----------------
R_ = D['red']; HILL = D['hill']


def red_sec(b):
    return ([(HILL['path_to'], HILL['grass_z'][1], None), (R_['d0'], HILL['grass_z'][1], 'path'),
             (R_['d0'], R_['z0'], 'render_white')]
            + stepped(R_['d0'], R_['z0'], R_['d1'], R_['z1'], R_['rows'])
            + [(R_['d1'] + 0.6, R_['z1'], 'conc'), (R_['d1'] + 0.6, R_['z1'] + 1.1, 'render_white'),
               (R_['d1'] + 0.85, R_['z1'] + 1.1, 'render_white'), (R_['d1'] + 0.85, 0.0, 'render_white')])


def red_stands(col):
    mb = MB('red_terraces')
    for b0, b1 in R_['blocks']:
        sweep(mb, arc(b0, b1), red_sec, capm='render_white')
        # a glass balustrade along the front, white posts every 2.4 m
        bs = arc(b0, b1)
        strip(mb, bs, lambda b: (R_['d0'] + 0.1, R_['z0']), lambda b: (R_['d0'] + 0.1, R_['z0'] + 1.0), 'glass_rail')
        r = rf(0.5 * (b0 + b1)) + R_['d0'] + 0.1
        for b in np.arange(b0, b1 + 0.01, math.degrees(2.4 / r)):
            mb.beam(Q(b, R_['d0'] + 0.1, R_['z0']), Q(b, R_['d0'] + 0.1, R_['z0'] + 1.05), 0.06, 0.06, 'steel_white')
    # the stairs between the blocks: concrete flights up from the path, handrails each side
    for (a0, a1), (c0, c1) in zip(R_['blocks'], R_['blocks'][1:]):
        bs = arc(a1, c0, 0.25)
        n = R_['rows']
        sweep(mb, bs, lambda b: ([(HILL['path_to'], HILL['grass_z'][1], None), (R_['d0'], HILL['grass_z'][1], 'path')]
                                 + stepped(R_['d0'], HILL['grass_z'][1], R_['d1'], R_['z1'], 2 * n, 'tread', 'riser')
                                 + [(R_['d1'] + 0.85, R_['z1'], 'conc'), (R_['d1'] + 0.85, 0.0, 'render_white')]),
              capm='render_white')
        for b in (a1 + 0.15, c0 - 0.15):
            mb.beam(Q(b, R_['d0'], HILL['grass_z'][1] + 1.0), Q(b, R_['d1'], R_['z1'] + 1.0), 0.06, 0.06, 'steel_galv')
    mb.build(col)


# ---------------- the east bank ----------------
def hill_sec(b, short=False):
    g0, g1 = HILL['grass_z']; v0, v1 = HILL['gravel_z']
    sec = [(0.0, 0.0, None), (0.0, FZ, 'fence'), (0.25, FZ, 'fence_top')]
    for k in range(1, 9):   # the bank's convex slope
        f = k / 8.0; sec.append((0.25 + (HILL['grass_to'] - 0.25) * f, FZ + (g1 - FZ) * math.sin(f * math.pi / 2), 'grass_bank'))
    sec += [(HILL['path_to'], g1, 'path')]
    if short:
        return sec + [(HILL['path_to'] + 0.3, g1, 'path')]
    sec += [(HILL['path_to'] + 0.3, v0, 'kerb'), (HILL['gravel_to'], v1, 'gravel'),
            (HILL['gravel_to'], v1 + 0.15, 'kerb'), (HILL['hedge_to'] + 2.0, v1 + 0.15, 'path'),
            (HILL['hedge_to'] + 2.0, 0.0, 'render_white')]
    return sec


def hill(col):
    mb = MB('east_bank')
    sweep(mb, arc(57.0, 103.0), hill_sec, cap0=False, capm='render_white')
    sweep(mb, arc(103.0, 133.0), lambda b: hill_sec(b, True), cap0=False, cap1=False, capm='render_white')
    # the box hedge along the top of the gravel: a clipped block, its top and faces in leaf
    bs = arc(57.5, 102.5)
    v1 = HILL['gravel_z'][1] + 0.15; h = HILL['hedge_h']
    d0, d1 = HILL['gravel_to'] + 0.2, HILL['hedge_to']
    sweep(mb, bs, lambda b: [(d0, v1, None), (d0, v1 + h, 'hedge'), (d1, v1 + h + 0.05, 'hedge'), (d1, v1, 'hedge')], capm='hedge')
    # two stone piers on the gravel terrace (Google Earth from the field, bearing 86 and 95)
    for b in (86.0, 95.0):
        c = Q(b, 15.0, HILL['gravel_z'][0] + 0.5)
        mb.box(c[:2], 1.6, 1.6, 3.6, b, 'stone', z0=c[2] - 0.5, mtop='stone')
        mb.box(c[:2], 2.0, 2.0, 0.35, b, 'stone', z0=c[2] + 3.1, mtop='stone')
    mb.build(col)


# ---------------- the media and corporate building over the southern seats ----------------
M = D['media']


def media(col):
    """Curved in plan, four levels: a glazed corporate level just above the seats, then three levels behind vertical
    bronze fins, under a white curved roof with a dark rim. Its front leans out over the top rows."""
    mb = MB('media_centre'); bs = arc(M['b0'], M['b1'], 0.5)
    z0 = M['z_under']; zt = M['z_roof']
    # seats under it: the low terrace (lower_all) runs in front; the building's underside is open to the concourse
    face = lambda b: M['face'] + 1.2 * math.sin(math.pi * (b - M['b0']) / (M['b1'] - M['b0']))   # bowed toward the field
    back = lambda b: M['back'] - 4.0 * abs((b - 0.5 * (M['b0'] + M['b1'])) / (0.5 * (M['b1'] - M['b0']))) ** 2
    # floors (slab edges proud of the glass by 0.5 m) and the glass behind
    for i, z in enumerate(M['levels']):
        za = z; zb = M['levels'][i + 1] if i + 1 < len(M['levels']) else zt - 0.8
        strip(mb, bs, lambda b, za=za: (face(b) - 0.5, za), lambda b, za=za: (face(b) - 0.5, za + 0.4), 'slab_dark')
        strip(mb, bs, lambda b, za=za: (face(b), za + 0.4), lambda b, za=za: (face(b) - 0.5, za + 0.4), 'slab_dark')
        strip(mb, bs, lambda b, za=za: (face(b) - 0.5, za), lambda b, za=za: (face(b), za), 'slab_dark')
        strip(mb, bs, lambda b, za=za: (face(b), za + 0.4), lambda b, za=za, zb=zb: (face(b), zb), 'media_glass' if i == 0 else 'glass_dark')
    # the underside over the concourse and the sides and back of the block
    strip(mb, bs, lambda b: (back(b), z0), lambda b: (face(b), z0), 'roof_soffit')
    strip(mb, bs, lambda b: (back(b), 0.0), lambda b: (back(b), zt - 0.8), 'bronze_wall')
    for b, fl in ((bs[0], False), (bs[-1], True)):
        endcap(mb, b, [(face(b), z0), (back(b), z0), (back(b), zt - 0.8), (face(b), zt - 0.8)], 'bronze_wall', flip=fl)
        endcap(mb, b, [(L['conc'], 0.0), (back(b), 0.0), (back(b), z0), (L['conc'], z0)], 'render_white', flip=fl)
    # bronze fins: 0.12 m blades, 0.55 m deep, every 0.7 m on the three upper levels, front and back
    for side, dd, sgn in (('front', face, -1), ('back', back, 1)):
        b = bs[0]
        while b < bs[-1]:
            r = rf(b) + dd(b); step = math.degrees(0.7 / r)
            for i in range(1, len(M['levels'])):
                za = M['levels'][i] + 0.4; zb = M['levels'][i + 1] if i + 1 < len(M['levels']) else zt - 0.8
                p = Q(b, dd(b) + sgn * 0.3, za); q = Q(b, dd(b) + sgn * 0.3, zb)
                mb.beam(p, q, 0.12, 0.55, 'bronze')
            b += step
    # roof: white deck, dark rim 0.7 m deep standing 1 m out from the walls all round
    rm = lambda b: face(b) - 1.0; rb = lambda b: back(b) + 1.0
    strip(mb, bs, lambda b: (rm(b), zt), lambda b: (rb(b), zt), 'roof_white')
    strip(mb, bs, lambda b: (rb(b), zt - 0.8), lambda b: (rm(b), zt - 0.8), 'roof_soffit')
    strip(mb, bs, lambda b: (rm(b), zt - 0.8), lambda b: (rm(b), zt + 0.1), 'rim_dark')
    strip(mb, bs, lambda b: (rb(b), zt + 0.1), lambda b: (rb(b), zt - 0.8), 'rim_dark')
    for b, fl in ((bs[0] - 0.6, False), (bs[-1] + 0.6, True)):
        endcap(mb, b, [(rm(b), zt - 0.8), (rb(b), zt - 0.8), (rb(b), zt + 0.1), (rm(b), zt + 0.1)], 'rim_dark', flip=fl)
    strip(mb, arc(M['b0'] - 0.6, M['b1'] + 0.6), lambda b: (rm(b), zt + 0.1), lambda b: (rm(b) + 0.4, zt + 0.1), 'rim_dark')
    # the curved white canopy over the top floor's south-east balcony
    mb.build(col)


# ---------------- Jack Fingleton Scoreboard ----------------
def scoreboard(col):
    """The heritage scoreboard from the MCG: a white-painted box (OSM footprint), its face to the field framed with
    pilasters and a cornice standing proud, black name boards set back into it in three tiers, the lettering band
    on the frieze, a clock in a small pediment on top."""
    # (named fingleton_board, not scoreboard: a hand-worked board, so the match lays no live face over it)
    S = D['scoreboard']; mb = MB('fingleton_board')
    P = [np.array(p) for p in G['1290130248'][:-1]]
    # the long sides of the OSM rectangle: the face is the one nearer the field
    e0 = P[1] - P[0]; e1 = P[2] - P[1]
    if np.linalg.norm(e0) < np.linalg.norm(e1):
        P = P[1:] + P[:1]
    a, b, c, d = P
    mid_ab = (a + b) / 2; mid_cd = (c + d) / 2
    if np.linalg.norm(mid_ab - C) > np.linalg.norm(mid_cd - C):
        a, b, c, d = c, d, a, b
    # a-b is the face (toward the field); outward normal points to the field
    u = (b - a) / np.linalg.norm(b - a); Lf = np.linalg.norm(b - a); n_ = np.array([u[1], -u[0]])
    if np.dot(n_, C - a) < 0: n_ = -n_
    dep = np.linalg.norm(d - a); H = S['h']
    F = lambda s, z, o=0.0: (*(a + u * s + n_ * o), z)
    # The body stands 0.25 m back from the face; the face is a white frame (rails and mullions with depth) round the
    # recessed black name boards.
    ang = math.degrees(math.atan2(u[1], u[0]))
    R = 0.25
    mb.prism([tuple(a - n_ * R), tuple(b - n_ * R), tuple(c), tuple(d)], 0.0, H, 'scoreboard_white', top='roof_grey')
    tiers = ((1.6, 3.6), (4.0, 5.9), (6.2, 7.7))
    rails = [(0.0, tiers[0][0])] + [(tiers[i][1], tiers[i + 1][0]) for i in range(2)] + [(tiers[-1][1], H)]
    for z0, z1 in rails:
        mb.box(tuple(a + u * Lf / 2 - n_ * (R / 2)), Lf, R, z1 - z0, ang, 'scoreboard_white', z0=z0)
    bays = np.linspace(0.55, Lf - 0.55, 6)
    edges = [(0.0, bays[0] + 0.3)] + [(q - 0.3, q + 0.3) for q in bays[1:-1]] + [(bays[-1] - 0.3, Lf)]
    for s0, s1 in edges:
        mb.box(tuple(a + u * (s0 + s1) / 2 - n_ * (R / 2)), s1 - s0, R, tiers[-1][1] - tiers[0][0], ang, 'scoreboard_white',
               z0=tiers[0][0])
    # cornice and plinth standing proud
    for z0, z1, o in ((H - 0.6, H, 0.35), (0.0, 0.6, 0.15)):
        mb.box(tuple(a + u * Lf / 2 + n_ * (o / 2)), Lf + 0.5, o + 0.02, z1 - z0, ang, 'scoreboard_white', z0=z0)
    # pilasters, stopping under the name band
    for q in np.linspace(0.3, Lf - 0.3, 6):
        mb.box(tuple(a + u * q + n_ * 0.12), 0.5, 0.24, H - 1.35 - 0.6, ang, 'scoreboard_white', z0=0.6)
    # name boards: three tiers of black boards with white rails, in the recess
    for z0, z1 in tiers:
        for s0, s1 in zip(bays, bays[1:]):
            s0 += 0.3; s1 -= 0.3
            mb.face([F(s0, z0, -R + 0.01), F(s1, z0, -R + 0.01), F(s1, z1, -R + 0.01), F(s0, z1, -R + 0.01)], 'board_black',
                    uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    # the name band and the clock pediment
    mb.face([F(1.0, H - 1.25, 0.02), F(Lf - 1.0, H - 1.25, 0.02), F(Lf - 1.0, H - 0.7, 0.02), F(1.0, H - 0.7, 0.02)], 'sb_lettering',
            uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    cm = a + u * Lf / 2 + n_ * 0.1 - n_ * 1.0
    mb.box(tuple(cm), 2.6, 2.0, S['clock'], math.degrees(math.atan2(u[1], u[0])), 'scoreboard_white', z0=H, mtop='roof_grey')
    k = 24; r = 0.8; cz = H + S['clock'] / 2 + 0.1; cc = a + u * Lf / 2 + n_ * 0.12   # on the pediment's face (0.1)
    ring = [(*(cc + u * r * math.cos(2 * math.pi * i / k)), cz + r * math.sin(2 * math.pi * i / k)) for i in range(k)]
    centre = (*(cc + n_ * 0.03), cz)
    keep = np.dot(np.cross(np.append(u, 0.0), [0, 0, 1.0])[:2], n_) > 0
    for i in range(k):
        j = (i + 1) % k
        uv = [(0.5, 0.5), (0.5 + 0.5 * math.cos(2 * math.pi * i / k), 0.5 + 0.5 * math.sin(2 * math.pi * i / k)),
              (0.5 + 0.5 * math.cos(2 * math.pi * j / k), 0.5 + 0.5 * math.sin(2 * math.pi * j / k))]
        f = [centre, ring[i], ring[j]]
        mb.face(f if keep else f[::-1], 'clock_face', uv=uv if keep else uv[::-1])
    mb.build(col)


# ---------------- the video screen ----------------
def screen(col):
    """The screen on its steel frame (Google Earth from the field and from the north-east): a dark face in a frame,
    a 1.6 m deep box behind it, four trussed legs braced on a deck and diagonals to the ground."""
    S = D['screen']; mb = MB('video_screen')
    bm = 0.5 * (S['b0'] + S['b1'])
    a = np.array(Q(S['b0'], S['d'], 0))[:2]; b = np.array(Q(S['b1'], S['d'], 0))[:2]
    u = (b - a) / np.linalg.norm(b - a); Lf = np.linalg.norm(b - a); n_ = np.array([u[1], -u[0]])
    if np.dot(n_, C - a) < 0: n_ = -n_
    z0, z1 = S['z0'], S['z1']; dep = 1.6
    F = lambda s, z, o=0.0: (*(a + u * s + n_ * o), z)
    ang = math.degrees(math.atan2(u[1], u[0]))
    mb.box(tuple(a + u * Lf / 2 - n_ * dep / 2), Lf, dep, z1 - z0, ang, 'steel_dark', z0=z0)
    mb.face([F(0.35, z0 + 0.35, 0.03), F(Lf - 0.35, z0 + 0.35, 0.03), F(Lf - 0.35, z1 - 0.35, 0.03), F(0.35, z1 - 0.35, 0.03)][::-1]
            if np.dot(n_, [u[1], -u[0]]) < 0 else [F(0.35, z0 + 0.35, 0.03), F(Lf - 0.35, z0 + 0.35, 0.03), F(Lf - 0.35, z1 - 0.35, 0.03), F(0.35, z1 - 0.35, 0.03)],
            'screen', uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    # legs and bracing: four lattice legs (two chords each) from the ground to the box
    for s in (2.0, Lf / 2 - 2.5, Lf / 2 + 2.5, Lf - 2.0):
        for o in (-0.6, -dep - 1.2):
            mb.beam(F(s, 0.0, o), F(s, z0, o), 0.3, 0.3, 'steel_galv')
        for k in range(6):
            za = z0 * k / 6; zb = z0 * (k + 1) / 6
            mb.beam(F(s, za, -0.6), F(s, zb, -dep - 1.2), 0.1, 0.1, 'steel_galv')
            mb.beam(F(s, za, -dep - 1.2), F(s, zb, -0.6), 0.1, 0.1, 'steel_galv')
    for z in (0.35 * z0, 0.7 * z0, z0 - 0.2):
        mb.beam(F(1.5, z, -0.6), F(Lf - 1.5, z, -0.6), 0.18, 0.18, 'steel_galv')
    mb.box(tuple(a + u * Lf / 2 - n_ * (dep / 2 + 0.6)), Lf + 0.6, dep + 2.4, 0.25, ang, 'steel_galv', z0=z0 - 0.45)
    mb.build(col)


# ---------------- the camera box behind the north stand ----------------
def nest(col):
    S = D['nest']; mb = MB('camera_box'); c = np.array(Q(S['b'], S['d'], 0))[:2]
    mb.cyl(tuple(c), 0.9, 0.0, S['z0'] - 2.0, 'tower', n=14)
    # the tapered collar under the box (Google Earth: an inverted pyramid)
    t = tangent(S['b'])[:2]; r = radial(S['b'])[:2]
    def corner(su, sv, w, dp): return c + t * su * w / 2 + r * sv * dp / 2
    lo = [corner(su, sv, 2.0, 2.0) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    hi = [corner(su, sv, S['w'], S['dep']) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for i in range(4):
        j = (i + 1) % 4
        mb.face([(*lo[i], S['z0'] - 2.0), (*lo[j], S['z0'] - 2.0), (*hi[j], S['z0']), (*hi[i], S['z0'])], 'steel_dark')
    mb.face([(*p, S['z0'] - 2.0) for p in lo][::-1], 'steel_dark')
    mb.prism([tuple(p) for p in hi], S['z0'], S['z1'], 'steel_dark', top='roof_grey')
    # glazed slot toward the field
    a = corner(-1, -1, S['w'], S['dep']); b = corner(1, -1, S['w'], S['dep'])
    window(mb, tuple(b), tuple(a), 0.6, S['w'] - 0.6, S['z0'] + 1.0, S['z1'] - 0.8, glass='win_dark', frame='steel_galv')
    mb.build(col)


# ---------------- the six light towers ----------------
def towers(col):
    """47 m, leaning in: a tapered pale-grey pole, a narrow neck, then the shield-shaped head (wide at the top),
    its face a frame of modelled lamps in rows, the back closed by panels and a ladder cage up the pole."""
    T = D['towers']; mb = MB('light_towers'); H = T['H']; lean = math.radians(T['lean_deg'])
    for x, y in G['masts']:
        base = np.array([x, y, 0.0]); inw = C - base[:2]; inw = np.append(inw / np.linalg.norm(inw), 0.0)
        axis = np.array([0, 0, 1.0]) * math.cos(lean) + inw * math.sin(lean)
        side = np.cross(axis, inw); side /= np.linalg.norm(side); front = np.cross(side, axis)
        hn = H - T['head_h']
        n = 16
        def ring(h, r):
            c = base + axis * h
            return [tuple(c + r * (side * math.cos(2 * math.pi * k / n) + front * math.sin(2 * math.pi * k / n))) for k in range(n)]
        for (h0, r0), (h1, r1) in (((0.0, 1.05), (hn - 3.0, 0.62)), ((hn - 3.0, 0.62), (hn + 0.5, 0.5))):
            A_, B_ = ring(h0, r0), ring(h1, r1)
            for k in range(n):
                j = (k + 1) % n; mb.face([A_[k], A_[j], B_[j], B_[k]], 'tower')
        mb.cyl((x, y), 1.8, -0.2, 0.5, 'conc', n=12, top='conc')
        # head: a shield, wide at the top, built as a frame round rows of lamps facing the field (tilted 14 deg down)
        hc = base + axis * hn
        tilt = math.radians(14); fz = front * math.cos(tilt) - axis * math.sin(tilt); uz = axis * math.cos(tilt) + front * math.sin(tilt)
        def hp(u, v, w=0.0): return tuple(hc + side * u + uz * v + fz * w)
        Wt = T['head_w']; Hh = T['head_h']
        half = lambda v: 0.6 + (Wt / 2 - 0.6) * (v / Hh) ** 0.8
        vs = np.linspace(0, Hh, 15)
        for v0, v1 in zip(vs, vs[1:]):
            for s in (-1, 1):
                mb.beam(hp(s * half(v0), v0), hp(s * half(v1), v1), 0.22, 0.22, 'steel_galv')
        mb.beam(hp(-Wt / 2, Hh), hp(Wt / 2, Hh), 0.25, 0.25, 'steel_galv')
        # the back skin
        for v0, v1 in zip(vs, vs[1:]):
            mb.face([hp(half(v0), v0, -0.5), hp(-half(v0), v0, -0.5), hp(-half(v1), v1, -0.5), hp(half(v1), v1, -0.5)], 'tower')
        mb.face([hp(-half(Hh), Hh, -0.5), hp(half(Hh), Hh, -0.5), hp(half(Hh), Hh, 0.1), hp(-half(Hh), Hh, 0.1)], 'tower')
        # lamps: rows 0.75 m apart, as many as the shield is wide
        for v in np.arange(1.2, Hh - 0.3, 0.75):
            w = half(v) - 0.35; k = max(1, int(2 * w / 0.62))
            mb.beam(hp(-w - 0.2, v - 0.37), hp(w + 0.2, v - 0.37), 0.08, 0.08, 'steel_galv')
            for i in range(k):
                u = -w + (i + 0.5) * 2 * w / k; e = 0.25
                cb = [hp(u + du * e, v + dv * e, -0.35) for du, dv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                cf = [hp(u + du * e, v + dv * e, 0.15) for du, dv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                for q in range(4):
                    mb.face([cb[q], cb[(q + 1) % 4], cf[(q + 1) % 4], cf[q]], 'steel_dark')
                mb.face(cf, 'lamp_face')
        # ladder cage up the back of the pole
        for h in np.arange(2.5, hn, 2.5):
            p = base + axis * h - front * 0.95
            mb.beam(tuple(p - side * 0.35), tuple(p + side * 0.35), 0.05, 0.05, 'steel_galv')
        mb.beam(tuple(base + axis * 2.5 - front * 0.95 - side * 0.35), tuple(base + axis * hn - front * 0.95 - side * 0.35), 0.06, 0.06, 'steel_galv')
        mb.beam(tuple(base + axis * 2.5 - front * 0.95 + side * 0.35), tuple(base + axis * hn - front * 0.95 + side * 0.35), 0.06, 0.06, 'steel_galv')
    mb.build(col)


# ---------------- the curator's residence ----------------
def residence(col):
    S = D['residence']; mb = MB('residence'); c = pol(S['b'], rf(S['b']) + S['d'])
    F = Frame(dict(c=c, a=S['a'], L=S['L'], W=S['W'])); h = S['L'] / 2; w = S['W'] / 2
    poly = [F.P(-h, -w), F.P(h, -w), F.P(h, w), F.P(-h, w)]
    mb.prism(poly, 0.0, S['eave'], 'render_cream')
    hip_roof(mb, F, -h, h, -w, w, 'hip', S['eave'], S['ridge'], 'tile_red', over=0.55, soffit='render_cream', fascia='steel_white')
    # windows on every side, two storeys, sills and heads proud (window())
    for p, q in zip(poly, poly[1:] + poly[:1]):
        Lw = math.hypot(q[0] - p[0], q[1] - p[1]); k = int(Lw / 3.0)
        for j in range(k):
            a_ = (j + 0.5) * Lw / k - 0.6
            window(mb, p, q, a_, a_ + 1.2, 1.0, 2.6, glass='win_dark', frame='steel_white')
            window(mb, p, q, a_, a_ + 1.2, 4.2, 5.7, glass='win_dark', frame='steel_white')
    # chimney
    cc = F.P(h * 0.4, 0.0); mb.box(cc, 0.9, 0.6, S['ridge'] + 1.2, S['a'], 'render_cream', mtop='conc_dk')
    mb.build(col)


# ---------------- outside: the apron round the stands' backs ----------------
def apron(col):
    mb = MB('apron'); bs = arc(0, 360, 1.0)
    out = lambda b: (24.0 if not in_range(b, 258, 293) else B['back'] + 1.0) if not in_range(b, 171, 194) else M['back'] + 1.5
    strip(mb, bs, lambda b: (out(b), -0.02), lambda b: (L['conc'] - 0.5, -0.02), 'paving')
    mb.build(col)


def build_all():
    clear(); col = bpy.context.scene.collection
    lower_all(col); astands(col); bradman(col); red_stands(col); hill(col); media(col)
    scoreboard(col); screen(col); nest(col); towers(col); residence(col); apron(col)


# ---------------- seats: instanced 3D shells on the treads (the MCG standard's seat files) ----------------
SEAT_W = 0.5
AISLE_EVERY = 14.0
AISLE_W = 1.1
# Manuka's mixed seats in the A-frame stands (Google Earth from the field): reds and oranges with blues, greys
# and a few greens, scattered seat by seat.
MIX = [('seat_mk_red', 0.24), ('seat_mk_orange', 0.18), ('seat_mk_blue', 0.2), ('seat_mk_grey', 0.22),
       ('seat_mk_teal', 0.1), ('seat_mk_yellow', 0.06)]
_rng = np.random.default_rng(1929)


def _mix():
    x = _rng.random(); acc = 0.0
    for c, p in MIX:
        acc += p
        if x < acc: return c
    return MIX[-1][0]


def _rows(out, b0, b1, d0, z0, d1, z1, n, colour, skip=lambda b, k: False):
    for k in range(n):
        run = (d1 - d0) / n
        dd = d0 + (k + 1) * run - 0.30; z = z0 + (k + 1) * (z1 - z0) / n
        bm = 0.5 * (b0 + b1); r = rf(bm) + dd
        Ltot = math.radians(b1 - b0) * r; nb = max(1, int(round(Ltot / AISLE_EVERY)))
        for blk in range(nb):
            s0 = blk * Ltot / nb + AISLE_W / 2; s1 = (blk + 1) * Ltot / nb - AISLE_W / 2
            m = int((s1 - s0) // SEAT_W)
            for i in range(m):
                s = s0 + (s1 - s0 - m * SEAT_W) / 2 + (i + 0.5) * SEAT_W
                b = b0 + math.degrees(s / r)
                if skip(b, k): continue
                x, y = pol(b, rf(b) + dd)
                out.append((x, y, z, b, colour() if callable(colour) else colour))


def seat_list():
    out = []
    # the low terrace: light grey seats (the Bradman's five front rows too)
    for b0, b1 in lower_ranges():
        if b0 < 258.0 < b1:
            _rows(out, b0, 258.0, L['d0'], L['z0'], L['d1'], L['z1'], L['rows'], 'seat_mk_pale',
                  skip=lambda b, k: in_range(b, M['b0'] - 1, M['b1'] + 1) and False)
        else:
            _rows(out, b0, b1, L['d0'], L['z0'], L['d1'], L['z1'], L['rows'], 'seat_mk_pale')
    n5 = L['bradman_rows']; run = (L['d1'] - L['d0']) / L['rows']; rise = (L['z1'] - L['z0']) / L['rows']
    _rows(out, B['b0'], B['b1'], L['d0'], L['z0'], L['d0'] + n5 * run, L['z0'] + n5 * rise, n5, 'seat_mk_pale')
    # the A-frame stands: mixed colours; seats keep 2.6 m headroom under the roof (the seat rule)
    for name, S in ((k, v) for k, v in D['astands'].items() if not k.startswith('_')):
        def skip(b, k, S=S):
            dd = S['d0'] + (k + 1) * (S['d1'] - S['d0']) / S['rows'] - 0.3; z = S['z0'] + (k + 1) * (S['z1'] - S['z0']) / S['rows']
            if dd < S['rf']: return False
            rz = S['rfz'] - 0.35 + (S['rbz'] - S['rfz']) * (dd - S['rf']) / (S['rb'] - S['rf'])
            return rz - z < 2.6
        _rows(out, S['b0'], S['b1'], S['d0'], S['z0'], S['d1'], S['z1'], S['rows'], _mix, skip)
    # the Bradman's upper tier: white and light grey, none in the vomitories
    def bskip(b, k):
        dd = B['d0'] + (k + 1) * (B['d1'] - B['d0']) / B['rows']
        return dd > B['d0'] + 6.0 and any(abs(math.radians(b - v) * (rf(v) + dd)) < 1.7 for v in B['voms'])
    _rows(out, B['b0'], B['b1'], B['d0'], B['z0'], B['d1'], B['z1'], B['rows'],
          lambda: 'seat_mk_white' if _rng.random() < 0.7 else 'seat_mk_pale', bskip)
    # the east terraces: red
    for b0, b1 in R_['blocks']:
        _rows(out, b0 + 0.3, b1 - 0.3, R_['d0'], R_['z0'], R_['d1'], R_['z1'], R_['rows'], 'seat_mk_red')
    return out


def seat_template():
    """One moulded seat, glTF frame (x along the row, y up, +z toward the field): pan, back, pedestal."""
    tris = []
    def box(cx, cy, cz, sx, sy, sz, lean=0.0):
        ca, sa = math.cos(lean), math.sin(lean); P = []
        for dx, dy, dz in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
            y, z = dy * sy / 2, dz * sz / 2; y, z = y * ca + z * sa, -y * sa + z * ca
            P.append((cx + dx * sx / 2, cy + y, cz + z))
        ctr = np.mean(P, axis=0)
        for a, b_, c, d in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            for t in ((P[a], P[b_], P[c]), (P[a], P[c], P[d])):
                A, Bv, Cv = (np.array(q) for q in t)
                if np.dot(np.cross(A - Cv, A - Bv), (A + Bv + Cv) / 3 - ctr) < 0:
                    t = (t[0], t[2], t[1])
                tris.extend(t)
    box(0.0, 0.415, 0.24, 0.44, 0.05, 0.40)
    box(0.0, 0.66, 0.05, 0.42, 0.42, 0.05, lean=0.21)
    box(0.0, 0.2, 0.22, 0.08, 0.40, 0.25)
    return tris


def seat_transforms(seats):
    """Row-major 3x4 per seat in the glTF frame (x east, y up, z south); a seat faces back along its bearing."""
    out = {}
    for x, y, z, b, c in seats:
        a = math.radians(b); sb, cb = math.sin(a), math.cos(a)
        X = (cb, 0.0, sb); Y = (0.0, 1.0, 0.0); Zv = (-sb, 0.0, cb)
        o = (x, z, -y)
        out.setdefault(c, []).append([X[0], Y[0], Zv[0], o[0], X[1], Y[1], Zv[1], o[1], X[2], Y[2], Zv[2], o[2]])
    return out
