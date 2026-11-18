# Albury Sports Ground exterior, built from OSM footprints and heights read off Google Earth 3D views and ground photos.
# Run in Blender:  blender -b --python model/build.py -- [out.glb]
# Metres; x east, y north, z up; ground z=0. Every texture is hand-made (model/paint.py), no photo pixels.
import sys, os, math, json
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(SP, 'work'))
import bpy
import importlib, mb as MBm; importlib.reload(MBm)
from mb import MB, Frame, roof, window, rect, ccw
import spec

D = json.load(open(os.path.join(SP, 'osm', 'geo.json'), encoding='utf-8'))
G = json.load(open(os.path.join(HERE, 'ground.json')))


def fp(i):
    p = D[str(i)]['pts']
    return [tuple(q) for q in (p[:-1] if p[0] == p[-1] else p)]


def line(i):
    return [tuple(q) for q in D[str(i)]['pts']]


def edges(poly):
    poly = ccw(poly)
    return [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


# ---------------------------------------------------------------- grandstand (OSM 482327969)
def grandstand():
    """Victorian grandstand: brick base with three arched openings, open seating deck of six bench tiers,
    white posts with brackets, cream valance, hip roof with a full-depth cross gable over the SW half.
    Local frame: u+ = SW end (left in the field photo), v+ = field side (SE)."""
    o = spec.obb(fp(482327969)); F = Frame(o); L, W = o['L'], o['W']; m = MB('grandstand')
    u0, u1, v0, v1 = -L / 2, L / 2, -W / 2, W / 2
    DECK, EAVE, RIDGE, GAPEX = 3.2, 7.8, 10.15, 10.6
    P = F.P
    # back wall (road side) full height, SW end wall full height, NE end wall to rail height
    # outward faces: back (v-), NE end (u-) to rail height, SW end (u+) full height
    m.wall(P(u0, v0), P(u1, v0), 0, EAVE, 'brick_red')
    m.wall(P(u0, v1), P(u0, v0), 0, 4.3, 'brick_red')
    m.wall(P(u1, v0), P(u1, v1), 0, EAVE, 'brick_red')
    # inner faces of the back and end walls, seen from the deck
    m.wall(P(u1 - 0.3, v0 + 0.3), P(u0 + 0.3, v0 + 0.3), DECK, EAVE, 'brick_red')
    m.wall(P(u1 - 0.3, v1), P(u1 - 0.3, v0 + 0.3), DECK, EAVE, 'brick_red')
    m.wall(P(u0 + 0.3, v0 + 0.3), P(u0 + 0.3, v1), DECK, 4.3, 'brick_red')
    m.face([P(u0, v0, 4.3), P(u0, v1, 4.3), P(u0 + 0.3, v1, 4.3), P(u0 + 0.3, v0, 4.3)][::-1], 'render_cream')
    # front (field) wall of the ground floor, with cream string course and plinth
    m.wall(P(u1, v1), P(u0, v1), 0, DECK - 0.25, 'brick_red')
    m.wall(P(u1, v1 + 0.05), P(u0, v1 + 0.05), DECK - 0.25, DECK + 0.1, 'render_cream')
    m.wall(P(u1, v1 + 0.04), P(u0, v1 + 0.04), 0, 0.35, 'render_cream')
    # arched openings (u centre, width, sill, kind) read off the field photo
    for uc, w, sill, kind in ((4.35, 1.7, 0.0, 'door'), (-1.56, 2.2, 0.9, 'round'), (-6.5, 2.3, 0.9, 'arch')):
        a, b = uc - w / 2, uc + w / 2; top = 2.0
        n = 10; cx = (a + b) / 2; r = w / 2
        arc = [P(cx + r * math.cos(math.pi * k / n), v1 + 0.06, top + r * math.sin(math.pi * k / n)) for k in range(n + 1)]
        m.face([P(b, v1 + 0.06, sill), P(a, v1 + 0.06, sill)] + arc[::-1],
               'steel_black' if kind == 'door' else 'glass')
        # cream surround: ring of quads around the arch and jambs
        R2 = r + 0.25
        arc2 = [P(cx + R2 * math.cos(math.pi * k / n), v1 + 0.09, top + R2 * math.sin(math.pi * k / n)) for k in range(n + 1)]
        arc1 = [P(cx + r * math.cos(math.pi * k / n), v1 + 0.09, top + r * math.sin(math.pi * k / n)) for k in range(n + 1)]
        for k in range(n):
            m.face([arc1[k], arc2[k], arc2[k + 1], arc1[k + 1]][::-1], 'render_cream')
        for s0, s1 in ((a - 0.25, a), (b, b + 0.25)):
            m.face([P(s0, v1 + 0.09, sill if kind != 'door' else 0), P(s1, v1 + 0.09, sill if kind != 'door' else 0),
                    P(s1, v1 + 0.09, top), P(s0, v1 + 0.09, top)][::-1], 'render_cream')
        if kind != 'door':
            m.face([P(a - 0.3, v1 + 0.12, sill - 0.12), P(b + 0.3, v1 + 0.12, sill - 0.12),
                    P(b + 0.3, v1 + 0.12, sill), P(a - 0.3, v1 + 0.12, sill)][::-1], 'render_cream')
    # deck floor and front walkway
    m.face([P(u0, v1 - 1.2, DECK), P(u1, v1 - 1.2, DECK), P(u1, v1, DECK), P(u0, v1, DECK)], 'concrete')
    # six tiers of bench seating rising to the back; aisles at u 3.0 and -2.7
    rows, rise, depth = 6, 0.43, 0.8; vf = v1 - 1.2
    for k in range(rows):
        z = DECK + rise * (k + 1); va = vf - depth * k; vb = va - depth
        m.face([P(u0 + 0.3, va, z - rise), P(u1 - 0.3, va, z - rise), P(u1 - 0.3, va, z), P(u0 + 0.3, va, z)][::-1], 'render_grey')
        m.face([P(u0 + 0.3, vb, z), P(u1 - 0.3, vb, z), P(u1 - 0.3, va, z), P(u0 + 0.3, va, z)], 'concrete')
        for sa, sb in ((u0 + 0.4, -3.1), (-2.3, 2.6), (3.4, u1 - 0.4)):
            c = P((sa + sb) / 2, va - 0.45); m.box(c, sb - sa, 0.32, 0.06, math.degrees(F.a), 'seat_slats', z0=z + 0.40)
            for ul in [sa + 0.3 + 1.8 * j for j in range(int((sb - sa - 0.3) / 1.8) + 1)]:
                m.box(P(ul, va - 0.45), 0.05, 0.25, 0.40, math.degrees(F.a), 'steel_galv', z0=z)
    vtop = vf - depth * rows
    m.face([P(u0 + 0.3, v0 + 0.3, DECK + rise * rows), P(u1 - 0.3, v0 + 0.3, DECK + rise * rows),
            P(u1 - 0.3, vtop, DECK + rise * rows), P(u0 + 0.3, vtop, DECK + rise * rows)], 'concrete')
    # front railing (white steel) with the stair gap at u -0.9..3.1
    for sa, sb in ((u0, -0.9), (3.1, u1)):
        for z in (DECK + 0.45, DECK + 1.05):
            m.beam(P(sa, v1 - 0.05, z), P(sb, v1 - 0.05, z), 0.05, 0.05, 'steel_white')
        for ul in [sa + 0.1 + 1.5 * j for j in range(int((sb - sa) / 1.5) + 1)]:
            m.beam(P(ul, v1 - 0.05, DECK), P(ul, v1 - 0.05, DECK + 1.1), 0.05, 0.05, 'steel_white')
    # NE end railing above the brick
    m.beam(P(u0 + 0.1, v0, 5.3), P(u0 + 0.1, v1, 5.3), 0.05, 0.05, 'steel_white')
    # posts with brackets, valance beam
    for uc in (8.34, 1.0, -4.0, -9.0):
        m.box(P(uc, v1 - 0.12), 0.22, 0.22, EAVE - 0.5 - DECK, math.degrees(F.a), 'steel_white', z0=DECK)
        m.box(P(uc, v1 - 0.12), 0.36, 0.36, 0.5, math.degrees(F.a), 'brick_red', z0=DECK)
        for du in (-0.9, 0.9):
            if u0 < uc + du < u1:
                m.beam(P(uc, v1 - 0.12, EAVE - 1.3), P(uc + du, v1 - 0.12, EAVE - 0.5), 0.07, 0.07, 'steel_white')
    m.box(P(0, v1 - 0.08), L + 0.1, 0.18, 0.5, math.degrees(F.a), 'render_cream', z0=EAVE - 0.5)
    # stairs down the front, from the deck at u 3.1 to the ground at u -0.9, outside the front wall
    n = 18; run = 4.0 / n; rs = DECK / (n + 1)
    for k in range(n):
        ua = 3.1 - run * k
        m.box(P(ua - run / 2, v1 + 0.75), run, 1.3, DECK - rs * (k + 1), math.degrees(F.a), 'concrete', z0=0)
    m.beam(P(3.1, v1 + 1.38, DECK + 1.0), P(-0.9, v1 + 1.38, 1.0), 0.05, 0.05, 'steel_white')
    m.beam(P(3.1, v1 + 0.12, DECK + 1.0), P(-0.9, v1 + 0.12, 1.0), 0.05, 0.05, 'steel_white')
    for ul in (3.1, 1.1, -0.9):
        zt = DECK * (ul + 0.9) / 4.0
        m.beam(P(ul, v1 + 1.38, zt), P(ul, v1 + 1.38, zt + 1.0), 0.05, 0.05, 'steel_white')
    # roofs: hip over the whole stand, full-depth cross gable over the SW half (cream gable ends)
    # main gable along the stand, cream pediment at the NE end; it runs under the cross gable to its centre line
    roof(m, F, u0, 4.65, v0, v1, 'gable', EAVE, RIDGE, 'roof_bluegrey', over=0.45, gm='render_pale')
    # cross wing over the SW half: hipped at the field and at the back (Earth views g_nw_000/090)
    roof(m, F, 0.05, u1, v0, v1, 'hip', EAVE, GAPEX, 'roof_bluegrey', over=0.6, ridge_axis='v')
    # SW end: cream parapet pediment standing on the end wall in front of the hip slope (g_nw_270)
    vm = (v0 + v1) / 2; ua, ub = u1 + 0.02, u1 - 0.25; PA = RIDGE + 0.2
    A, B, C = (v0 - 0.1, EAVE), (v1 + 0.1, EAVE), (vm, PA)
    m.face([P(ua, A[0], A[1]), P(ua, C[0], C[1]), P(ua, B[0], B[1])][::-1], 'render_pale')
    m.face([P(ub, A[0], A[1]), P(ub, C[0], C[1]), P(ub, B[0], B[1])], 'render_pale')
    for (s, t) in ((A, C), (C, B)):
        m.face([P(ua, s[0], s[1]), P(ub, s[0], s[1]), P(ub, t[0], t[1]), P(ua, t[0], t[1])], 'render_pale')
    # white raking cornices on both pediments
    for uu, over in ((ua + 0.06, 0.0), (u0 - 0.45, 0.45)):
        a3 = P(uu, v0 - 0.1 - over, EAVE); c3 = P(uu, vm, (PA if over == 0 else RIDGE) + 0.08); b3 = P(uu, v1 + 0.1 + over, EAVE)
        m.beam(a3, c3, 0.18, 0.16, 'paint_white'); m.beam(c3, b3, 0.18, 0.16, 'paint_white')
        m.beam(a3, b3, 0.18, 0.16, 'paint_white')
    return m.build()


# ---------------------------------------------------------------- club rooms (OSM 482327956), Earth views g_e2_090/270
CF = Frame(dict(c=(75.66, -46.28), L=34.17, W=19.47, a=262.89))  # u south, v east (street); field side is v-


def panel(m, F, ua, ub, v, z0, z1, mat, out=0.05, flip=False):
    """Textured quad on a wall at v (faces +v unless flip), u from ua to ub left-to-right as seen from outside."""
    o = -out if flip else out
    a, b = F.P(ua, v + o), F.P(ub, v + o)
    m.face([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], mat, uv=[(0, 0), (1, 0), (1, 1), (0, 1)])


def club():
    m = MB('club'); F = CF; P = F.P
    # field block: glazed two levels, ribbed skillion roof (eave 8.6 at the field face, 9.4 at the back)
    u0, u1, v0, v1 = -10.5, 11.6, -9.5, -1.5
    m.wall(P(u0, v0), P(u1, v0), -0.3, 8.6, 'paint_white')  # field face behind the glass
    m.wall(P(u1, v0), P(u1, v1), -0.3, 8.6, 'paint_white'); m.wall(P(u0, v1), P(u0, v0), -0.3, 8.6, 'paint_white')
    for z0, z1 in ((0.15, 3.85), (4.35, 7.25)):  # ground-floor dark glass and upper glazing, mullions every 1.5 m
        n = int((u1 - u0 - 0.6) / 1.5); w = (u1 - u0 - 0.6) / n
        for k in range(n):
            a = u0 + 0.3 + k * w
            window(m, P(u0, v0), P(u1, v0), a - u0 + 0.05, a - u0 + w - 0.05, z0, z1, frame='paint_white')
    m.box(P((u0 + u1) / 2, v0 - 0.4), u1 - u0, 0.8, 0.3, math.degrees(F.a), 'paint_white', z0=3.95)  # white floor slab edge
    a, b = P(u1 - 2.0, v0 - 0.06), P(u0 + 2.0, v0 - 0.06)  # banner, read from the field (faces -v)
    m.face([(a[0], a[1], 7.35), (b[0], b[1], 7.35), (b[0], b[1], 8.45), (a[0], a[1], 8.45)], 'sign_tradition', uv=[(1, 0), (0, 0), (0, 1), (1, 1)])
    roof(m, F, u0, u1, v0, v1, 'skillion', 8.6, 9.4, 'roof_ribbed', over=0.3)
    # street block: two storeys of red brick, flat white deck roof behind a parapet at 10.0
    s0, s1, t0, t1 = -17.1, 10.5, -1.5, 9.5
    m.wall(P(s1, t1), P(s0, t1), -0.3, 10.0, 'brick_red'); m.wall(P(s0, t1), P(s0, t0), -0.3, 10.0, 'brick_red')
    m.wall(P(s0, t0), P(s1, t0), -0.3, 10.0, 'brick_red'); m.wall(P(s1, t0), P(s1, t1), -0.3, 10.0, 'brick_red')
    m.wall(P(u0, -2.0), P(s0, -2.0), -0.3, 9.4, 'brick_red'); m.wall(P(s0, -2.0), P(s0, t0), -0.3, 9.4, 'brick_red')
    m.cap([P(s0, t0), P(s1, t0), P(s1, t1), P(s0, t1)], 9.75, 'roof_deck')
    for (pa, pb) in ((P(s1, t1), P(s0, t1)), (P(s0, t1), P(s0, t0)), (P(s0, t0), P(s1, t0)), (P(s1, t0), P(s1, t1))):
        m.beam((pa[0], pa[1], 10.05), (pb[0], pb[1], 10.05), 0.3, 0.12, 'paint_white')  # parapet capping
    S, T = P(s1, t1), P(s0, t1)  # street face, distances from the south end (u = 10.5 - d)
    for uc in (5.4, 1.7, -2.0, -5.7, -9.4):  # upper four-pane windows
        d0 = s1 - uc - 1.2; window(m, S, T, d0, d0 + 2.4, 6.7, 8.3, frame='render_cream')
        q = P(uc, t1 + 0.08); m.beam((q[0], q[1], 6.7), (q[0], q[1], 8.3), 0.06, 0.04, 'render_cream')
        a, b = P(uc + 1.2, t1 + 0.08), P(uc - 1.2, t1 + 0.08); m.beam((a[0], a[1], 7.5), (b[0], b[1], 7.5), 0.06, 0.04, 'render_cream')
    for uc in (1.6, -0.9):  # ground-floor windows beside the entry
        d0 = s1 - uc - 0.8; window(m, S, T, d0, d0 + 1.6, 1.0, 3.6, frame='render_cream')
    window(m, S, T, s1 - 3.6, s1 - 2.6, 0.0, 2.4, frame='render_cream')  # entry door
    m.box(P(5.1, t1 + 0.75), 4.8, 1.5, 0.8, math.degrees(F.a), 'render_cream', z0=4.2)  # cream entry canopy
    m.box(P(4.6, t1 + 0.5), 0.12, 0.9, 1.2, math.degrees(F.a), 'paint_white', z0=5.0)  # blade sign
    panel(m, F, 10.1, 7.9, t1, 7.5, 9.2, 'sign_tigers_club')
    panel(m, F, -12.2, -15.8, t1, 3.9, 8.3, 'mural_tiger', out=0.02)
    # south annex: single storey, dark-blue flat roof
    m.prism([P(10.5, -0.8), P(17.1, -0.8), P(17.1, 9.6), P(10.5, 9.6)], -0.3, 3.8, 'brick_red')
    roof(m, F, 10.5, 17.1, -0.8, 9.6, 'skillion', 3.8, 4.4, 'roof_dkgrey', over=0.3)
    return m.build()


# ---------------------------------------------------------------- open stands and gatehouse (Earth views g_e_*, g_se_000, g_s_000)
def _dist(p, a, b):  # signed distance of p from line a->b (positive on the left)
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
    return ((p[0] - a[0]) * dy * -1 + (p[1] - a[1]) * dx) / L


def clip(poly, f):  # keep the part of a polygon where f(p) >= 0 (f linear in p)
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]; fp_, fq = f(p), f(q)
        if fp_ >= 0:
            out.append(p)
        if (fp_ >= 0) != (fq >= 0):
            t = fp_ / (fp_ - fq); out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def openstand(name, poly, back, zf, zb, roofm, wallm, tiers=4, posts=(), strip=None, frontm=None, endm=None, seam=None, endpanel=None):
    """Open-fronted stand: walls on the back edge (poly[back]->poly[back+1]) and the two ends, roof sloping from zf
    at the front to zb at the back, tiered bench seating rising to the back."""
    m = MB(name); poly = ccw(poly); n = len(poly)  # back = a ground point beside the back wall; nearest edge wins
    back = min(range(n), key=lambda i: math.hypot((poly[i][0] + poly[(i + 1) % n][0]) / 2 - back[0], (poly[i][1] + poly[(i + 1) % n][1]) / 2 - back[1]))
    a, b = poly[back], poly[(back + 1) % n]
    depth = max(abs(_dist(p, a, b)) for p in poly)
    z = lambda p: zf + (zb - zf) * (1 - abs(_dist(p, a, b)) / depth)
    for i in range(n):  # walls: the back edge and the two ends; the field side stays open (or clear blinds: frontm)
        k = (i - back) % n
        mm = wallm if k == 0 else (endm or wallm) if k in (1, n - 1) else frontm
        if mm:
            p, q = poly[i], poly[(i + 1) % n]
            m.face([(p[0], p[1], -0.3), (q[0], q[1], -0.3), (q[0], q[1], z(q)), (p[0], p[1], z(p))], mm)
    parts = [(poly, roofm)]
    if strip:  # back strip of a second roof sheet: (fraction of depth from the back, material, extra keep test)
        fr, sm, keep = strip
        bi = lambda p: fr * depth - abs(_dist(p, a, b)); bo = lambda p: -bi(p)
        inner = clip(poly, bi)
        parts = [(clip(inner, keep), sm), (clip(inner, lambda p: -keep(p)), roofm), (clip(poly, bo), roofm)]
    if endpanel:  # a different sheet over the north end of the roof: (fraction of the length, material)
        fr, em = endpanel; e0, e1 = (a, b) if a[1] < b[1] else (b, a); ex, ey = e1[0] - e0[0], e1[1] - e0[1]; el = math.hypot(ex, ey)
        t = lambda p: ((p[0] - e0[0]) * ex + (p[1] - e0[1]) * ey) / el / el - (1 - fr)
        parts = [(clip(pp, t), em) for pp, _ in parts] + [(clip(pp, lambda p: -t(p)), mm) for pp, mm in parts]
    for pp, mm in parts:
        if len(pp) < 3:
            continue
        for tri in MBm.earclip(pp):
            m.face([(x, y, z((x, y))) for x, y in tri], mm)
            m.face([(x, y, z((x, y)) - 0.15) for x, y in tri[::-1]], 'steel_white')
    ux, uy = (b[0] - a[0], b[1] - a[1]); L = math.hypot(ux, uy); ux, uy = ux / L, uy / L; nx, ny = -uy, ux  # n points into the stand
    for k in range(tiers):  # bench tiers, back row against the wall
        d0 = 0.3 + k * 0.85; h = 0.45 * (tiers - k); c = ((a[0] + b[0]) / 2 + nx * (d0 + 0.42), (a[1] + b[1]) / 2 + ny * (d0 + 0.42))
        m.box(c, L - 0.6, 0.85, h, math.degrees(math.atan2(uy, ux)), 'concrete', mtop='seat_slats')
    for p in posts:
        m.box(p, 0.15, 0.15, z(p), 0, 'steel_white')
    for sf in (seam if isinstance(seam, tuple) else (seam,) if seam else ()):  # dark capping where roof sheets meet
        mx, my = a[0] + (b[0] - a[0]) * sf, a[1] + (b[1] - a[1]) * sf
        p0 = (mx, my, z((mx, my)) + 0.05); p1 = (mx + nx * depth, my + ny * depth, z((mx + nx * depth, my + ny * depth)) + 0.05)
        m.beam(p0, p1, 0.22, 0.06, 'gutter_brown')
    return m, a, b, z


def stands():
    # east stand (482327982): tan roof 6.2 m at the front, 6.6 m at the back; sign and sponsor boards on the street side
    m, a, b, z = openstand('east_stand', fp(482327982), (82.0, 1.0), 5.8, 6.2, 'roof_tan', 'brick_red', tiers=5, seam=(0.33,),
                           strip=(0.38, 'roof_white', lambda p: 4.8 - p[1]),
                           posts=[(73.4, -9.0), (73.3, -2.0), (73.2, 4.7), (75.8, 11.0)])
    def back_panel(t0, t1, z0, z1, mat):
        p = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0); q = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
        d = (b[0] - a[0], b[1] - a[1]); L = math.hypot(*d); o = (d[1] / L * 0.06, -d[0] / L * 0.06)  # outward (right of a->b)
        m.face([(p[0] + o[0], p[1] + o[1], z0), (q[0] + o[0], q[1] + o[1], z0), (q[0] + o[0], q[1] + o[1], z1), (p[0] + o[0], p[1] + o[1], z1)],
               mat, uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    S = (lambda t: t) if a[1] < b[1] else (lambda t: 1 - t)  # fraction along the back wall from its south end
    for t0, t1, z0, z1, mat in ((0.26, 0.72, 1.4, 5.4, 'sign_east_stand'),):  # sponsor boards left out (director: no boards)
        x0, x1 = sorted((S(t0), S(t1)))
        back_panel(x0, x1, z0, z1, mat) if a[1] > b[1] else back_panel(x0, x1, z0, z1, mat)
    m.build()
    # south-east stand (482327961): tan roof 4.5 m, grey rendered walls
    openstand('se_stand', fp(482327961), (59.0, -88.0), 4.3, 4.7, 'roof_tan', 'blind_clear', tiers=4, frontm='blind_clear', endm='blind_clear', seam=0.5, endpanel=(0.15, 'roof_grey'),
              posts=[(54.8, -77.8), (46.4, -88.2)])[0].build()
    # gatehouse (482327958)
    m = MB('gatehouse'); o = spec.obb(fp(482327958)); F = Frame(o); L2, W2 = o['L'] / 2, o['W'] / 2
    # brick walls under a blue hipped roof with a raised lantern tier on top (g_se_000, g_se_270)
    m.prism([F.P(u, v) for u, v in ((-L2, -W2), (L2, -W2), (L2, W2), (-L2, W2))], 0, 4.2, 'brick_red')
    roof(m, F, -L2, L2, -W2, W2, 'hip', 4.2, 5.4, 'roof_blue', over=0.4, gm='roof_blue')
    li, wi = L2 * 0.8, W2 * 0.5  # upper tier: east-west gable over most of the length (Dutch gable), pale gable ends
    m.prism([F.P(u, v) for u, v in ((-li, -wi), (li, -wi), (li, wi), (-li, wi))], 5.0, 5.6, 'roof_blue')
    roof(m, F, -li, li, -wi, wi, 'gable', 5.6, 6.8, 'roof_blue', over=0.25, gm='paint_white')
    print('gatehouse', o)
    return m



# ---------------------------------------------------------------- light towers: the two poles the top view and photos show
def towers():
    m = MB('light_towers')
    for (x, y) in ((82.7, 14.0), (66.0, -73.0)):
        H = 30.0; n = 12
        for k in range(n):  # tapered galvanised pole, 0.6 m at the base to 0.3 m at the top
            a0 = 2 * math.pi * k / n; a1 = 2 * math.pi * (k + 1) / n
            m.face([(x + 0.3 * math.cos(a0), y + 0.3 * math.sin(a0), 0), (x + 0.3 * math.cos(a1), y + 0.3 * math.sin(a1), 0),
                    (x + 0.15 * math.cos(a1), y + 0.15 * math.sin(a1), H), (x + 0.15 * math.cos(a0), y + 0.15 * math.sin(a0), H)], 'steel_galv')
        ang = math.atan2(-20 - y, 0 - x); tx, ty = -math.sin(ang), math.cos(ang); fx, fy = math.cos(ang), math.sin(ang)
        c = (x + fx * 0.4, y + fy * 0.4)
        m.box(c, 0.3, 3.4, 2.4, math.degrees(ang), 'steel_galv', z0=H - 1.2)  # head frame
        for r in range(2):
            for k in range(3):  # six floodlights facing the ground centre
                o = (k - 1) * 1.1; z0 = H - 0.9 + r * 1.2
                m.box((c[0] + tx * o + fx * 0.35, c[1] + ty * o + fy * 0.35), 0.35, 0.8, 0.8, math.degrees(ang), 'steel_galv', z0=z0, mtop='steel_galv')
                q = (c[0] + tx * o + fx * 0.53, c[1] + ty * o + fy * 0.53)
                m.face([(q[0] - tx * 0.35, q[1] - ty * 0.35, z0 + 0.05), (q[0] + tx * 0.35, q[1] + ty * 0.35, z0 + 0.05),
                        (q[0] + tx * 0.35, q[1] + ty * 0.35, z0 + 0.75), (q[0] - tx * 0.35, q[1] - ty * 0.35, z0 + 0.75)], 'glass')
    return m.build()


# ---------------------------------------------------------------- generic buildings from spec.B
def generic(name):
    b = spec.B[name]; m = MB(name); poly = b['fp']
    wm = b.get('mat', 'brick') if b.get('mat') != 'brick' else 'brick_red'
    m.prism(poly, -0.3, b['eave'], wm)
    for p in b['roofs']:
        r = p['r']; F = Frame(r)
        roofmat = {'steel_grey': 'roof_grey'}.get(b['roofmat'], b['roofmat'])
        if p['kind'] == 'flat':
            m.cap(poly, p['ridge'], roofmat)
        else:
            roof(m, F, -r['L'] / 2, r['L'] / 2, -r['W'] / 2, r['W'] / 2, p['kind'], p['eave'], p['ridge'], roofmat,
                 over=p['over'], gm=wm)
    return m.build()


def tanks():
    m = MB('tanks')
    for pts, h in spec.TANKS:
        cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
        r = sum(math.hypot(p[0] - cx, p[1] - cy) for p in pts) / len(pts)
        m.cyl((cx, cy), r, -0.3, h, 'paint_white', n=32)
        n = 32; ring = [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
        for k in range(n):
            a, b = ring[k], ring[(k + 1) % n]; m.face([(a[0], a[1], h), (b[0], b[1], h), (cx, cy, h + 0.7)], 'paint_white')
    return m.build()


def fences():
    m = MB('fences')
    pit = G['pitch']
    for i in range(len(pit) - 1):  # white picket fence on the boundary line, 1.2 m
        a, b = pit[i], pit[i + 1]; L = math.hypot(b[0] - a[0], b[1] - a[1]); u = L / 1.15
        if L < 0.01:
            continue
        m.face([(a[0], a[1], 0), (b[0], b[1], 0), (b[0], b[1], 1.2), (a[0], a[1], 1.2)], 'pickets', uv=[(0, 0), (u, 0), (u, 1), (0, 1)])
    for i in (482327983, 482327984, 482327985, 482330186, 482330187, 482330188):
        pts = line(i)
        for a, b in zip(pts, pts[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            m.face([(a[0], a[1], 0), (b[0], b[1], 0), (b[0], b[1], 1.8), (a[0], a[1], 1.8)], 'mesh', uv=[(0, 0), (L / 0.5, 0), (L / 0.5, 3.6), (0, 3.6)])
            m.beam((a[0], a[1], 1.8), (b[0], b[1], 1.8), 0.04, 0.04, 'steel_black')
    return m.build()


def walls():
    m = MB('retaining_walls')
    for i in (482327964, 482327965, 482327968, 482327975, 482327976, 482327977, 482327980, 482330181, 482330182,
              482330183, 482330190):
        pts = line(i)
        for a, b in zip(pts, pts[1:]):
            m.beam((a[0], a[1], 0.45), (b[0], b[1], 0.45), 0.25, 0.9, 'render_grey')
    return m.build()


def ground():
    m = MB('apron')
    for key, mat in (('apron', 'grass'), ('court_red', 'court_red'), ('court_green', 'court_green')):  # flat court surface only: the apron has a hole there
        for t in G[key]:
            z = 0.02 if key != 'apron' else 0.0
            m.face([(x, y, z) for x, y in ccw(t)], mat)
    return m.build()


def extras():
    # brick lean-to on the east end of the north hall, x -10.8 to -3.5 (g_nw_180): red brick under a grey skillion that
    # falls east from the hall's gable end (frame u points west, so the high side v1 is against the hall)
    m = MB('north_hall_leanto'); o = dict(c=(-7.15, 80.4), L=7.3, W=6.0, a=171.3); F = Frame(o)
    m.prism([F.P(u, v) for u, v in ((-3.65, -3.0), (3.65, -3.0), (3.65, 3.0), (-3.65, 3.0))], -0.3, 3.6, 'brick_red')
    roof(m, F, -3.65, 3.65, -3.0, 3.0, 'skillion', 3.6, 4.6, 'roof_grey', over=0.2, ridge_axis='v')
    # bare sign wall on the west side (boards left out, director: no boards), x -87, y 2 to 22 (g_w_270 right, g_w_090 left): boards face the ground,
    # dark brown back
    m.box((-87.15, 12.0), 0.3, 20.0, 2.4, 0, 'gutter_brown')
    # south boundary sign wall, bare (boards left out), x -35 to 10 at y -111 (g_s_000): boards face the ground, dark brown back
    m.box((-12.5, -111.15), 45.0, 0.3, 2.4, 0, 'gutter_brown')
    for (x, y) in ((71.3, -14.1), (63.6, -58.4), (-68.0, 19.0), (-75.0, -31.0)):  # concrete service pits in the grass
        m.box((x, y), 1.6, 1.0, 0.12, 0, 'concrete'); m.box((x, y), 1.1, 0.6, 0.02, 0, 'asphalt', z0=0.12)
    # roof vents: round white vents on the NW wing's slopes (g_nw_180, g_n_090) and two dark vent pipes on the north
    # hall's south slope near its east end (g_nw_180); heights read off the roof plane at each spot
    def on_slope(name, part, u, v, h, r, mat):
        q = spec.B[name]['roofs'][part]; o = q['r']; F = Frame(o); hw = o['W'] / 2 + q['over']
        z = q['eave'] + (q['ridge'] - q['eave']) * (1 - abs(v) / hw); m.cyl(F.P(u, v), r, z - 0.2, z + h, mat, n=12, top=mat)
    L1 = spec.B['nw_wing']['roofs'][0]['r']['L']
    for k in range(5):
        on_slope('nw_wing', 0, -L1 / 2 + 5.0 + k * (L1 - 8.0) / 4, 2.6, 0.3, 0.22, 'paint_white')
    for k in range(3):
        on_slope('nw_wing', 0, -L1 / 2 + 6.5 + k * (L1 - 11.0) / 2, -2.6, 0.3, 0.22, 'paint_white')
    on_slope('nw_wing', 1, 0.0, 2.0, 0.3, 0.22, 'paint_white')
    for u in (7.4, 8.9):
        on_slope('north_hall', 0, u, -2.2, 1.1, 0.07, 'steel_galv')
    # NW wing north wall (field side), east to west: a dark doorway near the east end, then a row of seven high,
    # pale frosted windows under the eave (g_nw_180 close-up)
    p, q = (-50.64, 77.49), (-63.8, 68.6)
    window(m, p, q, 0.0, 1.2, 0.0, 2.2, glass='steel_black')
    for k in range(7):
        a0 = 2.4 + k * 1.95; window(m, p, q, a0, a0 + 0.9, 2.6, 3.3, glass='steel_white')
    # ne_bldg court side (SE wall): three arched verandah openings between brick piers (g_e_270)
    p, q = (58.10, 53.51), (64.88, 63.89); d = ((q[0]-p[0])/12.4, (q[1]-p[1])/12.4); nn = (d[1], -d[0])
    at = lambda s, z, o: (p[0] + d[0]*s + nn[0]*o, p[1] + d[1]*s + nn[1]*o, z)
    for k in range(3):
        a0 = 0.7 + k * 3.9; a1 = a0 + 3.2; cx = (a0 + a1) / 2; r = 1.6; spring = 2.0; n = 10
        arc = lambda rr, o: [at(cx + rr*math.cos(math.pi*j/n), spring + rr*math.sin(math.pi*j/n), o) for j in range(n + 1)]
        m.face([at(a0, 0.0, 0.03), at(a1, 0.0, 0.03)] + arc(r, 0.03), 'steel_black')
        A1, A2 = arc(r, 0.06), arc(r + 0.22, 0.06)
        for j in range(n):
            m.face([A1[j], A2[j], A2[j+1], A1[j+1]], 'render_pale')
    return m


def west():
    # west building (482327966, g_w_270, g_w_000): brick, grey gable roof, lower verandah roof on posts along the field side
    m = MB('west_bldg'); o = spec.obb(fp(482327966)); F = Frame(o); L2, W2 = o['L'] / 2, o['W'] / 2
    s_ = 1 if F.P(0, 1)[0] > F.P(0, -1)[0] else -1  # +v side faces the field (east) when s_ = 1
    vb = W2 - 3.2  # main block from the back wall to here; verandah over the last 3.2 m
    V = lambda v: s_ * v
    m.prism([F.P(u, V(v)) for u, v in ((-L2, -W2), (L2, -W2), (L2, vb), (-L2, vb))], -0.3, 6.0, 'brick_red')
    roof(m, F, -L2, L2, min(V(-W2), V(vb)), max(V(-W2), V(vb)), 'gable', 6.0, 8.5, 'roof_grey', over=0.35, gm='brick_red')
    m.prism([F.P(u, V(v)) for u, v in ((-L2, vb), (L2, vb), (L2, W2), (-L2, W2))], -0.3, 0.5, 'concrete', top='concrete')
    # verandah: skillion from 5.0 at the wall down to 3.2 at the front posts
    R = [F.P(-L2 - 0.3, V(vb), 5.0), F.P(L2 + 0.3, V(vb), 5.0), F.P(L2 + 0.3, V(W2 + 0.3), 3.2), F.P(-L2 - 0.3, V(W2 + 0.3), 3.2)]
    m.face(R if s_ == 1 else R[::-1], 'roof_grey'); m.face(R[::-1] if s_ == 1 else R, 'paint_white')
    for k in range(5):
        u = -L2 + 0.2 + k * (2 * L2 - 0.4) / 4
        m.box(F.P(u, V(W2 - 0.15)), 0.15, 0.15, 3.2, math.degrees(F.a), 'paint_white', z0=0.5)
    p, q = F.P(-L2, V(vb)), F.P(L2, V(vb)); e = F.P(0, V(W2))  # field face, outward normal to the right of p->q
    if (q[0] - p[0]) * (e[1] - p[1]) - (q[1] - p[1]) * (e[0] - p[0]) > 0:
        p, q = q, p
    for k in range(4):  # windows under the verandah roof on the field face
        w = 2 * L2 / 4
        window(m, p, q, k * w + 0.5, (k + 1) * w - 0.5, 1.4, 3.4)
    m.build()
    # coaches' box (482327967, g_w_270 far left, g_w_000 bottom): white frame, glass upper level, flat white roof
    m = MB('w_small'); poly = fp(482327967)
    m.prism(poly, -0.3, 2.4, 'paint_white'); m.prism(poly, 2.4, 4.4, 'glass'); m.prism(poly, 4.4, 4.8, 'paint_white', top='roof_white')
    return m.build()


def build_all():
    reset()
    grandstand(); club(); stands().build(); towers(); extras().build(); west()
    for n in spec.B:
        if n not in ('grandstand', 'club', 'west_bldg', 'w_small'):
            generic(n)
    tanks(); fences(); walls(); ground()


if __name__ == '__main__':
    build_all()
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if argv:
        bpy.ops.export_scene.gltf(filepath=argv[0], export_format='GLB')
        print('wrote', argv[0])
