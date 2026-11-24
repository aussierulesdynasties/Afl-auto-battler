# The buildings round ENGIE Stadium, modelled (runs inside Blender via the bpy module):
#   python3 landmarks.py OSM_DIR OUT.glb
# Every OpenStreetMap building within 1,100 m of the ground (OSM_DIR/*.osm, (c) OpenStreetMap contributors,
# ODbL) is stood up on its own footprint at its own height (height, building:levels) with its own roof form:
#  - the Royal Agricultural Society's pavilions: big steel sheds, a row of gables across the hall with a
#    clerestory strip along each ridge, roller doors in the walls (Google Earth: the showground's pavilions);
#  - offices, hotels and the Olympic Park towers: a floor slab edge every 3.3 m standing proud of a recessed
#    glazing band, a plant room on the roof;
#  - OSM's roof shapes where it gives them (gabled, hipped, round, dome, flat);
#  - landmarks modelled to Google Earth: Accor Stadium (bowl, roof ring, its two arches and four ramp towers),
#    Qudos Bank Arena (its mast-hung roof and east canopy), The Dome (a ribbed dome), the Brickpit Ring Walk.
# Model metres, Blender x east, y north, z up; the stadium model's origin (the OSM pitch's centre) at 0, 0.
import sys, os, math, glob, json
HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, '..', 'model')
sys.path.insert(0, MODEL)
import xml.etree.ElementTree as ET
import numpy as np
import bpy
from mb import MB, earclip, ccw, sarea

LAT0, LON0 = -33.8431119, 151.0676851
R_MAX = 1100.0
SITE = json.load(open(os.path.join(MODEL, 'engie.json')))['site']


def en(lat, lon):
    return ((lon - LON0) * 111320.0 * math.cos(math.radians(LAT0)), (lat - LAT0) * 110574.0)


def num(s, d=0.0):
    try:
        return float(str(s).split()[0].replace(';', '').replace('m', ''))
    except Exception:
        return d


def load(osm_dir):
    N, W, R = {}, {}, {}
    for f in sorted(glob.glob(os.path.join(osm_dir, '*.osm'))):
        r = ET.parse(f).getroot()
        for n in r.findall('node'):
            N[n.get('id')] = en(float(n.get('lat')), float(n.get('lon')))
        for w in r.findall('way'):
            W[w.get('id')] = ({t.get('k'): t.get('v') for t in w.findall('tag')}, [nd.get('ref') for nd in w.findall('nd')])
        for x in r.findall('relation'):
            R[x.get('id')] = ({t.get('k'): t.get('v') for t in x.findall('tag')},
                              [(m.get('type'), m.get('ref'), m.get('role')) for m in x.findall('member')])
    pts = lambda wid: [N[i] for i in W[wid][1] if i in N]
    return N, W, R, pts


def in_site(p):
    b = math.degrees(math.atan2(p[0], p[1])) % 360
    tab = SITE + [[360, SITE[0][1]]]
    r = np.interp(b, [x for x, _ in tab], [y for _, y in tab])
    return math.hypot(*p) < r + 2.0


# ---------------- footprint helpers ----------------
def clean(poly):
    p = [tuple(map(float, q)) for q in poly]
    if len(p) > 1 and math.dist(p[0], p[-1]) < 0.01:
        p = p[:-1]
    out = []
    for q in p:
        if not out or math.dist(out[-1], q) > 0.3:
            out.append(q)
    return ccw(out) if len(out) >= 3 else []


def min_rect(poly):
    """The footprint's smallest bounding rectangle: centre, angle (deg) of its long side, length, width."""
    P = np.array(poly); best = None
    for i in range(len(P)):
        d = P[(i + 1) % len(P)] - P[i]; L = np.linalg.norm(d)
        if L < 1e-6:
            continue
        u = d / L; v = np.array([-u[1], u[0]])
        a, b = P @ u, P @ v
        area = (a.max() - a.min()) * (b.max() - b.min())
        if best is None or area < best[0]:
            best = (area, u, v, a.min(), a.max(), b.min(), b.max())
    _, u, v, a0, a1, b0, b1 = best
    if a1 - a0 < b1 - b0:
        u, v, a0, a1, b0, b1 = v, -u, b0, b1, -a1, -a0
    c = u * (a0 + a1) / 2 + v * (b0 + b1) / 2
    return c, math.degrees(math.atan2(u[1], u[0])), a1 - a0, b1 - b0, u, v


def walls(mb, poly, z0, z1, m):
    for i in range(len(poly)):
        mb.wall(poly[i], poly[(i + 1) % len(poly)], z0, z1, m)


def offset(poly, d):
    """The footprint grown outward by d metres (miter, clamped)."""
    P = np.array(poly); n = len(P); out = []
    for i in range(n):
        a, b, c = P[i - 1], P[i], P[(i + 1) % n]
        e1 = (b - a) / (np.linalg.norm(b - a) + 1e-9); e2 = (c - b) / (np.linalg.norm(c - b) + 1e-9)
        n1 = np.array([e1[1], -e1[0]]); n2 = np.array([e2[1], -e2[0]])
        m = n1 + n2; m /= (np.linalg.norm(m) + 1e-9)
        k = d / max(0.35, float(np.dot(m, n1)))
        out.append(tuple(b + m * k))
    return out


# ---------------- generic buildings ----------------
def storeys(mb, poly, h, levels, glass='bl_glass', band='bl_spandrel', top='bl_roof'):
    """A multi-storey block: per floor a slab edge 0.35 m proud (1.0 m deep spandrel) over a glazing band set
    0.25 m back, a parapet, a flat roof and a plant room."""
    fh = h / max(1, levels)
    inner = offset(poly, -0.25)
    for k in range(int(levels)):
        z = k * fh
        walls(mb, inner, z, z + fh - 1.0, glass)
        walls(mb, poly, z + fh - 1.0, z + fh, band)
        # the slab's underside and top between the glazing and the slab edge
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]; ai, bi = inner[i], inner[(i + 1) % len(poly)]
            mb.face([(a[0], a[1], z + fh - 1.0), (b[0], b[1], z + fh - 1.0), (bi[0], bi[1], z + fh - 1.0), (ai[0], ai[1], z + fh - 1.0)], band)
            if k == 0:
                continue
            mb.face([(ai[0], ai[1], z), (bi[0], bi[1], z), (b[0], b[1], z), (a[0], a[1], z)], band)
    walls(mb, poly, h, h + 1.1, band)
    inn = offset(poly, -0.3)
    walls(mb, inn[::-1] if False else inn, h + 1.1, h, band)
    mb.cap(inn, h + 0.05, top)
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]; ai, bi = inn[i], inn[(i + 1) % len(poly)]
        mb.face([(a[0], a[1], h + 1.1), (b[0], b[1], h + 1.1), (bi[0], bi[1], h + 1.1), (ai[0], ai[1], h + 1.1)], band)
    c, ang, L, W, u, v = min_rect(poly)
    if L > 12 and W > 10:
        pl = [tuple(c + u * su * L * 0.18 + v * sv * W * 0.2) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        mb.prism(pl, h, h + 3.2, 'bl_plant', top='bl_plant')


def low_block(mb, poly, h, wall='bl_wall', top='bl_roof'):
    """A one or two storey building: walls, a coping, a flat roof inside a low parapet."""
    walls(mb, poly, 0.0, h, wall)
    inn = offset(poly, -0.3)
    walls(mb, poly, h, h + 0.6, 'bl_coping')
    walls(mb, inn, h + 0.6, h, 'bl_coping')
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]; ai, bi = inn[i], inn[(i + 1) % len(poly)]
        mb.face([(a[0], a[1], h + 0.6), (b[0], b[1], h + 0.6), (bi[0], bi[1], h + 0.6), (ai[0], ai[1], h + 0.6)], 'bl_coping')
    mb.cap(inn, h + 0.05, top)


def rect_roof(mb, poly, h, kind, m='rf_metal', wallm='bl_wall', pitch=12.0):
    """Walls to the eaves, then a gabled, hipped or barrel roof on the footprint's bounding rectangle."""
    walls(mb, poly, 0.0, h, wallm)
    c, ang, L, W, u, v = min_rect(poly)
    over = 0.5
    P = lambda a, b, z: (c[0] + u[0] * a + v[0] * b, c[1] + u[1] * a + v[1] * b, z)
    a0, a1, b0, b1 = -L / 2 - over, L / 2 + over, -W / 2 - over, W / 2 + over
    rise = math.tan(math.radians(pitch)) * W / 2
    mb.cap(poly, h, 'bl_soffit', down=True)
    if kind == 'round':
        n = 12
        for k in range(n):
            t0, t1 = math.pi * k / n, math.pi * (k + 1) / n
            y0, y1 = -math.cos(t0) * (W / 2 + over), -math.cos(t1) * (W / 2 + over)
            z0, z1 = h + math.sin(t0) * W * 0.28, h + math.sin(t1) * W * 0.28
            mb.face([P(a0, y0, z0), P(a1, y0, z0), P(a1, y1, z1), P(a0, y1, z1)], m)
        for a, sg in ((a0, -1), (a1, 1)):
            pts = [P(a, -math.cos(math.pi * k / n) * (W / 2 + over), h + math.sin(math.pi * k / n) * W * 0.28) for k in range(n + 1)]
            for tri in earclip([(q[0], q[1]) for q in pts]) if False else []:
                pass
            mid = P(a, 0, h)
            for k in range(n):
                f = [mid, pts[k], pts[k + 1]]
                mb.face(f if sg > 0 else f[::-1], 'bl_wall')
        return
    if kind == 'hipped':
        ins = min(W / 2, L / 2)
        r0, r1 = a0 + ins, a1 - ins
        z = h + rise
        mb.face([P(a0, b0, h), P(a1, b0, h), P(r1, 0, z), P(r0, 0, z)], m)
        mb.face([P(a1, b1, h), P(a0, b1, h), P(r0, 0, z), P(r1, 0, z)], m)
        mb.face([P(a1, b0, h), P(a1, b1, h), P(r1, 0, z)], m)
        mb.face([P(a0, b1, h), P(a0, b0, h), P(r0, 0, z)], m)
        return
    # gabled: ridge along the long side
    z = h + rise
    mb.face([P(a0, b0, h), P(a1, b0, h), P(a1, 0, z), P(a0, 0, z)], m)
    mb.face([P(a1, b1, h), P(a0, b1, h), P(a0, 0, z), P(a1, 0, z)], m)
    for a, sg in ((-L / 2, -1), (L / 2, 1)):
        f = [P(a, -W / 2, h), P(a, W / 2, h), P(a, 0, h + rise * (W / 2) / (W / 2 + over))]
        mb.face(f if sg > 0 else f[::-1], wallm)


def pavilion(mb, poly, h):
    """A showground pavilion: steel walls with roller doors every 18 m, a row of narrow steep gables across the
    hall (one every ~7 m along it), each ridge carrying a raised clerestory strip (Google Earth: the livestock
    pavilions north of the ground)."""
    c, ang, L, W, u, v = min_rect(poly)
    walls(mb, poly, 0.0, h, 'pv_wall')
    # roller doors: recessed 0.3 m panels 5 m wide, 5.5 m tall, along the long walls
    for sgn in (-1, 1):
        for a in np.arange(-L / 2 + 9.0, L / 2 - 4.0, 18.0):
            base = c + v * sgn * (W / 2 + 0.02)
            p0 = base + u * (a - 2.5); p1 = base + u * (a + 2.5)
            q0 = p0 - v * sgn * 0.3; q1 = p1 - v * sgn * 0.3
            seq = (p0, p1) if sgn < 0 else (p1, p0)
            mb.face([(seq[0][0], seq[0][1], 0.0), (seq[1][0], seq[1][1], 0.0), (seq[1][0], seq[1][1], 5.5), (seq[0][0], seq[0][1], 5.5)], 'pv_door')
            mb.beam((p0[0], p0[1], 5.7), (p1[0], p1[1], 5.7), 0.25, 0.35, 'pv_trim')
    P = lambda a, b, z: (c[0] + u[0] * a + v[0] * b, c[1] + u[1] * a + v[1] * b, z)
    n = max(1, int(round(L / 7.0))); bay = L / n; over = 0.4
    rise = math.tan(math.radians(22)) * bay / 2
    mb.cap(poly, h, 'bl_soffit', down=True)
    for k in range(n):
        a0 = -L / 2 + k * bay; a1 = a0 + bay; am = (a0 + a1) / 2
        b0, b1 = -W / 2 - over, W / 2 + over
        z = h + rise
        mb.face([P(a0 - (over if k == 0 else 0), b0, h), P(am, b0, z), P(am, b1, z), P(a0 - (over if k == 0 else 0), b1, h)][::-1], 'pv_roof')
        mb.face([P(am, b0, z), P(a1 + (over if k == n - 1 else 0), b0, h), P(a1 + (over if k == n - 1 else 0), b1, h), P(am, b1, z)][::-1], 'pv_roof')
        for b, sg in ((b0, -1), (b1, 1)):   # gable ends on the long walls
            f = [P(a0, b, h), P(a1, b, h), P(am, b, z)]
            mb.face(f if sg < 0 else f[::-1], 'pv_wall')
        # the clerestory: a raised translucent strip 1.6 m wide along the ridge, 0.6 m proud
        cw = 0.5
        mb.prism([P(am - cw, b0 + 1.5, 0)[:2], P(am + cw, b0 + 1.5, 0)[:2], P(am + cw, b1 - 1.5, 0)[:2], P(am - cw, b1 - 1.5, 0)[:2]],
                 z - 0.1, z + 0.6, 'pv_clere', top='pv_clere')


def big_shed(mb, poly, h):
    """The showground's biggest pavilions (west of the ground): one long low gable along the hall, a row of dark
    louvred ventilator boxes stepping down one side of the ridge every 7 m (Google Earth)."""
    rect_roof(mb, poly, h, 'gabled', m='pv_roof', wallm='pv_wall', pitch=9.0)
    c, ang, L, W, u, v = min_rect(poly)
    rise = math.tan(math.radians(9.0)) * W / 2
    for a in np.arange(-L / 2 + 5.0, L / 2 - 3.0, 7.0):
        for off in (-2.6,):
            zc = h + rise * (1 - abs(off - 1.5) / (W / 2))
            cc = c + u * a + v * off
            mb.box(tuple(cc), 4.2, 3.0, 1.8, ang, 'pv_vent', z0=zc - 0.6, mtop='pv_roof')


def dome(mb, poly, h_wall, h_top, m='dm_roof', rib_m='dm_rib'):
    """The Dome (Sydney Showground): a shallow ribbed dome over a ring of pale box "petals" round its foot,
    stepped in near the crown to a drum and a small cap (Google Earth)."""
    c = np.mean(np.array(poly), axis=0); r = max(math.dist(c, p) for p in poly) * 0.96
    ns = 64
    ring = lambda rr, z: [(c[0] + rr * math.cos(2 * math.pi * k / ns), c[1] + rr * math.sin(2 * math.pi * k / ns), z) for k in range(ns)]
    walls(mb, [q[:2] for q in ring(r - 2.0, 0)], 0.0, h_wall, 'dm_wall')
    # the petals: 24 boxes 2.4 m proud of the wall, 7 m tall, a dark joint between each
    for j in range(24):
        a0 = 2 * math.pi * (j + 0.06) / 24; a1 = 2 * math.pi * (j + 0.94) / 24
        pts = [(c[0] + (r - 2.0) * math.cos(a0), c[1] + (r - 2.0) * math.sin(a0)), (c[0] + (r + 0.4) * math.cos(a0), c[1] + (r + 0.4) * math.sin(a0)),
               (c[0] + (r + 0.4) * math.cos(a1), c[1] + (r + 0.4) * math.sin(a1)), (c[0] + (r - 2.0) * math.cos(a1), c[1] + (r - 2.0) * math.sin(a1))]
        mb.prism(pts, h_wall - 7.5, h_wall + 0.5, 'dm_petal', top='dm_petal', bot='dm_petal')
    # the dome: from the wall head to the step at 0.36 of the radius
    rise = (h_top - 4.5) - h_wall; nr = 9
    prof = [(r * (1 - 0.64 * i / nr), h_wall + rise * math.sin(math.pi / 2 * i / nr) ** 0.9) for i in range(nr + 1)]
    for (r0_, z0), (r1_, z1) in zip(prof, prof[1:]):
        A, B = ring(r0_, z0), ring(r1_, z1)
        for k in range(ns):
            mb.face([A[k], A[(k + 1) % ns], B[(k + 1) % ns], B[k]], m)
    for k in range(0, ns, 2):   # radial seam ribs
        for (r0_, z0), (r1_, z1) in zip(prof, prof[1:]):
            a = 2 * math.pi * k / ns
            mb.beam((c[0] + r0_ * math.cos(a), c[1] + r0_ * math.sin(a), z0 + 0.15), (c[0] + r1_ * math.cos(a), c[1] + r1_ * math.sin(a), z1 + 0.15), 0.25, 0.25, rib_m)
    # the crown: a 1.5 m step, a flat ring, the drum 3 m tall and its cap
    rs, zs = prof[-1]
    A = ring(rs, zs); B = ring(rs, zs + 1.5)
    for k in range(ns):
        mb.face([A[k], A[(k + 1) % ns], B[(k + 1) % ns], B[k]], 'dm_petal')
    rd = rs * 0.62
    C = ring(rd, zs + 1.5)
    for k in range(ns):
        mb.face([B[k], B[(k + 1) % ns], C[(k + 1) % ns], C[k]], m)
    walls(mb, [q[:2] for q in ring(rd, 0)], zs + 1.5, zs + 4.5, 'dm_petal')
    mb.cap([q[:2] for q in ring(rd + 0.4, 0)], zs + 4.5, 'dm_roof')
    walls(mb, [q[:2] for q in ring(rd + 0.4, 0)], zs + 4.2, zs + 4.5, 'dm_petal')


def halls(mb, poly, h):
    """The exhibition halls by The Dome: each hall is two great tent bays side by side along its length, every
    bay a hipped roof whose ridge runs across the hall, valleys between the bays; a white fabric canopy hangs in
    scallops from masts along both long sides; glazed bands on clad walls (Google Earth)."""
    c, ang, L, W, u, v = min_rect(poly)
    walls(mb, poly, 0.0, h, 'hl_wall')
    for k in range(int(h // 4.5)):   # a dark glazing band near the top of each floor
        z = 4.5 * k + 3.2
        walls(mb, offset(poly, 0.05), z, z + 0.9, 'bl_glass')
    P = lambda a, b, z: (c[0] + u[0] * a + v[0] * b, c[1] + u[1] * a + v[1] * b, z)
    n = max(1, int(round(L / 45.0))); bay = L / n; over = 0.6
    mb.cap(poly, h, 'bl_soffit', down=True)
    for k in range(n):
        a0 = -L / 2 + k * bay - (over if k == 0 else 0); a1 = -L / 2 + (k + 1) * bay + (over if k == n - 1 else 0)
        am = -L / 2 + (k + 0.5) * bay; hb = bay / 2
        rise = math.tan(math.radians(19)) * hb
        b0, b1 = -W / 2 - over, W / 2 + over
        r0, r1 = b0 + hb * 0.9, b1 - hb * 0.9
        if r1 < r0:
            r0 = r1 = 0.0
        z = h + rise
        mb.face([P(a0, b0, h), P(am, r0, z), P(am, r1, z), P(a0, b1, h)][::-1], 'hl_roof')
        mb.face([P(a1, b1, h), P(am, r1, z), P(am, r0, z), P(a1, b0, h)][::-1], 'hl_roof')
        mb.face([P(a1, b0, h), P(am, r0, z), P(a0, b0, h)][::-1], 'hl_roof')
        mb.face([P(a0, b1, h), P(am, r1, z), P(a1, b1, h)][::-1], 'hl_roof')
        # standing seams down each slope every 3 m and a ridge cap
        mb.beam(P(am, r0, z + 0.12), P(am, r1, z + 0.12), 0.5, 0.25, 'hl_rib')
        for bb in np.arange(r0 + 3.0, r1, 3.0):
            for ae in (a0, a1):
                mb.beam(P(am, bb, z + 0.08), P(ae, bb, h + 0.08), 0.12, 0.1, 'hl_rib')
        # the fabric canopy along both long sides: two scallops per bay, high at its masts, 8 m deep
        for sg in (-1, 1):
            for half in (0, 1):
                s0 = -L / 2 + k * bay + half * hb
                m_ = 8
                for i in range(m_):
                    f0, f1 = i / m_, (i + 1) / m_
                    lo = lambda f: 7.5 - 3.5 * math.sin(math.pi * f)
                    p0 = s0 + hb * f0; p1 = s0 + hb * f1
                    q = [P(p0, sg * (W / 2), h - 1.5), P(p1, sg * (W / 2), h - 1.5), P(p1, sg * (W / 2 + 8.0), lo(f1)), P(p0, sg * (W / 2 + 8.0), lo(f0))]
                    mb.face(q if sg > 0 else q[::-1], 'hl_fabric'); mb.face(q[::-1] if sg > 0 else q, 'hl_fabric')
                mb.beam(P(s0, sg * (W / 2 + 8.0), 0.0), P(s0, sg * (W / 2 + 8.0), 9.0), 0.3, 0.3, 'hl_rib')
                mb.beam(P(s0, sg * (W / 2 + 8.0), 8.6), P(s0, sg * (W / 2), h + 1.0), 0.12, 0.12, 'hl_rib')
        if k == n - 1:
            for sg in (-1, 1):
                mb.beam(P(L / 2, sg * (W / 2 + 8.0), 0.0), P(L / 2, sg * (W / 2 + 8.0), 9.0), 0.3, 0.3, 'hl_rib')


def marquee(mb, poly, wall, rise, m='hl_fabric', rib_m='hl_rib'):
    """A permanent white event marquee on an oval or long footprint: low walls, then a fabric shell that rounds
    over to its crown (each ring a scaled copy of the footprint), ribs over it every few metres (Google Earth)."""
    c = np.mean(np.array(poly), axis=0)
    P = [np.array(p) for p in poly]
    if sarea(poly) < 0:
        P = P[::-1]
    walls(mb, [tuple(p) for p in P], 0.0, wall, m)
    nr = 8
    rings = []
    for i in range(nr + 1):
        t = i / nr
        s = math.cos(math.pi / 2 * t) * 0.92 + 0.08 if i < nr else 0.0
        rings.append([(*(c + (p - c) * (1.0 if i == 0 else s)), wall + rise * math.sin(math.pi / 2 * t)) for p in P])
    n = len(P)
    for A, B in zip(rings, rings[1:]):
        for k in range(n):
            mb.face([A[k], A[(k + 1) % n], B[(k + 1) % n], B[k]], m)
    for k in range(0, n, max(1, n // 12)):
        for A, B in zip(rings, rings[1:]):
            mb.beam((A[k][0], A[k][1], A[k][2] + 0.1), (B[k][0], B[k][1], B[k][2] + 0.1), 0.15, 0.15, rib_m)


def small_stand(mb, poly, face_to):
    """A showground ring's covered grandstand: eight stepped timber rows, a back wall, and a green skillion roof
    on round posts sloping up toward the ring (Google Earth, Schmidt Arena)."""
    c, ang, L, W, u, v = min_rect(poly)
    if np.dot(v, np.array(face_to) - c) < 0:
        v = -v
    P = lambda a, b, z: (c[0] + u[0] * a + v[0] * b, c[1] + u[1] * a + v[1] * b, z)
    rows = 8; dep = W / rows
    for i in range(rows):   # row 0 at the front (the ring side), rising toward the back
        bf, bb = W / 2 - i * dep, W / 2 - (i + 1) * dep
        z0, z1 = 0.5 + 0.38 * i, 0.5 + 0.38 * (i + 1)
        mb.face([P(-L / 2, bf, z1), P(L / 2, bf, z1), P(L / 2, bb, z1), P(-L / 2, bb, z1)], 'wc_bench')
        mb.face([P(-L / 2, bf, z0), P(L / 2, bf, z0), P(L / 2, bf, z1), P(-L / 2, bf, z1)][::-1], 'bl_wall')
    zt = 0.5 + 0.38 * rows
    walls(mb, [P(-L / 2, -W / 2, 0)[:2], P(L / 2, -W / 2, 0)[:2], P(L / 2, W / 2, 0)[:2], P(-L / 2, W / 2, 0)[:2]], 0.0, 0.5, 'bl_wall')
    for sx in (-1, 1):   # side walls stepping up with the rows
        pts = [P(sx * L / 2, W / 2, 0.0), P(sx * L / 2, -W / 2, 0.0), P(sx * L / 2, -W / 2, zt + 1.2), P(sx * L / 2, W / 2, 0.9)]
        mb.face(pts if sx > 0 else pts[::-1], 'pv_wall')
    mb.face([P(-L / 2, -W / 2, 0.0), P(L / 2, -W / 2, 0.0), P(L / 2, -W / 2, zt + 2.6), P(-L / 2, -W / 2, zt + 2.6)][::-1], 'pv_wall')
    zf, zb = zt + 3.2, zt + 2.6
    q = [P(-L / 2 - 0.5, -W / 2 - 0.5, zb), P(L / 2 + 0.5, -W / 2 - 0.5, zb), P(L / 2 + 0.5, W / 2 + 1.5, zf), P(-L / 2 - 0.5, W / 2 + 1.5, zf)]
    mb.face(q, 'gs_roof'); mb.face([(x, y, z - 0.15) for x, y, z in q][::-1], 'bl_soffit')
    for a in np.arange(-L / 2, L / 2 + 0.1, L / max(1, round(L / 6.0))):
        mb.cyl(P(a, W / 2 + 0.6, 0)[:2], 0.12, 0.0, zf, 'wc_post', n=8)


def polar(poly, c, n=180):
    """A closed outline as its radius from c at n even bearings (the outline is star-shaped from c)."""
    P = np.array(poly) - c; ang = np.arctan2(P[:, 1], P[:, 0]); r = np.hypot(P[:, 0], P[:, 1])
    o = np.argsort(ang); ang, r = ang[o], r[o]
    ang = np.concatenate([ang - 2 * np.pi, ang, ang + 2 * np.pi]); r = np.concatenate([r, r, r])
    t = np.linspace(-np.pi, np.pi, n, endpoint=False)
    return t, np.interp(t, ang, r)


# ---------------- Accor Stadium ----------------
def accor(mb, outer, bowl_in, roof_in):
    """Stadium Australia as it stands since 2003: an oval bowl under a ring roof of translucent panels, the
    roof hung from two white triangular arches running north-south over its east and west sides, four
    spiral ramp towers at the corners, the outside wall in concourse bands (Google Earth, OSM)."""
    c = np.mean(np.array(outer), axis=0)
    t, r_out = polar(outer, c); _, r_bin = polar(bowl_in, c); _, r_rin = polar(roof_in, c)
    n = len(t)
    E = lambda k, r, z: (c[0] + r * math.cos(t[k % n]), c[1] + r * math.sin(t[k % n]), z)
    side = lambda k: abs(math.cos(t[k % n]))        # 1 on the east/west sides, 0 at the north/south ends
    z_out = lambda k: 34.0
    z_in = lambda k: 40.0 + 5.0 * side(k)
    # the roof: sheet on top, underside 1.5 m below, fascias at both edges
    for k in range(n):
        a, b = k, k + 1
        top = [E(a, r_out[a], z_out(a)), E(b, r_out[b % n], z_out(b)), E(b, r_rin[b % n], z_in(b)), E(a, r_rin[a], z_in(a))]
        mb.face(top[::-1], 'ac_roof')
        mb.face([(p[0], p[1], p[2] - 1.5) for p in top], 'ac_under')
        for r_, zf, sg in ((r_out, z_out, 1), (r_rin, z_in, -1)):
            q = [E(a, r_[a], zf(a) - 1.5), E(b, r_[b % n], zf(b) - 1.5), E(b, r_[b % n], zf(b) + 0.2), E(a, r_[a], zf(a) + 0.2)]
            mb.face(q if sg > 0 else q[::-1], 'ac_fascia')
    # roof girders over the sheet every 6 degrees (the panel grid's ribs)
    for k in range(0, n, 3):
        mb.beam(E(k, r_out[k], z_out(k) + 0.3), E(k, r_rin[k], z_in(k) + 0.3), 0.5, 0.6, 'ac_steel')
    # the outside wall, 9 m in from the roof edge: eight concourse levels of glazing under slab bands
    wall = lambda k: r_out[k % n] - 9.0
    for lvl in range(7):
        z0 = lvl * 4.6
        for k in range(n):
            a, b = k, k + 1
            mb.face([E(a, wall(a) - 0.4, z0), E(b, wall(b) - 0.4, z0), E(b, wall(b) - 0.4, z0 + 3.6), E(a, wall(a) - 0.4, z0 + 3.6)][::-1], 'ac_glass')
            mb.face([E(a, wall(a), z0 + 3.6), E(b, wall(b), z0 + 3.6), E(b, wall(b), z0 + 4.6), E(a, wall(a), z0 + 4.6)][::-1], 'ac_band')
            mb.face([E(a, wall(a) - 0.4, z0 + 3.6), E(b, wall(b) - 0.4, z0 + 3.6), E(b, wall(b), z0 + 3.6), E(a, wall(a), z0 + 3.6)], 'ac_band')
    for k in range(n):
        a, b = k, k + 1
        mb.face([E(a, wall(a), 32.2), E(b, wall(b), 32.2), E(b, wall(b), z_out(b) - 1.5), E(a, wall(a), z_out(a) - 1.5)][::-1], 'ac_band')
    # columns from the ground to the roof's outer edge, every 6 degrees
    for k in range(0, n, 3):
        mb.cyl(E(k, r_out[k] - 3.0, 0)[:2], 0.7, 0.0, z_out(k) - 1.5, 'ac_steel', n=10)
    # the bowl: stepped rows from the field's edge up to the roof's inner edge line and on under it
    rows = 56
    def row_r(k, i):
        return r_bin[k % n] + (wall(k) - 6.0 - r_bin[k % n]) * i / rows
    def row_z(i):
        return 1.0 + 30.0 * (i / rows) ** 1.25
    for k in range(n):
        a, b = k, k + 1
        for i in range(rows):
            ra0, ra1 = row_r(a, i), row_r(a, i + 1); rb0, rb1 = row_r(b, i), row_r(b, i + 1)
            z0, z1 = row_z(i), row_z(i + 1)
            m = 'ac_aisle' if (k % 9 == 0) else ('ac_seat' if i not in (18, 38) else 'ac_tierwall')
            mb.face([E(a, ra0, z1), E(b, rb0, z1), E(b, rb1, z1), E(a, ra1, z1)][::-1], m)
            mb.face([E(a, ra0, z0), E(b, rb0, z0), E(b, rb0, z1), E(a, ra0, z1)], 'ac_riser')
        mb.face([E(a, r_bin[a], 0.02), E(b, r_bin[b % n], 0.02), E(b, r_bin[b % n], 1.0), E(a, r_bin[a], 1.0)], 'ac_tierwall')
    # the field: turf inside the bowl
    mb.cap([E(k, r_bin[k], 0)[:2] for k in range(n)], 0.03, 'ac_turf')
    # the two arches: triangular trusses springing from the ground north and south of the bowl
    for sx in (-1, 1):
        x0 = c[0] + sx * 58.0
        span = 300.0; top = 72.0
        pts = []
        for j in range(41):
            s = -span / 2 + span * j / 40
            z = top * (1 - (2 * s / span) ** 2)
            pts.append(np.array([x0, c[1] + s, z]))
        for j in range(40):
            p, q = pts[j], pts[j + 1]
            d = q - p; d /= np.linalg.norm(d); w = np.array([1.0, 0, 0]); up = np.cross(w, d)
            k0 = [p + w * 2.2 - up * 1.3, p - w * 2.2 - up * 1.3, p + up * 2.6]
            k1 = [q + w * 2.2 - up * 1.3, q - w * 2.2 - up * 1.3, q + up * 2.6]
            for i in range(3):
                mb.beam(tuple(k0[i]), tuple(k1[i]), 0.9, 0.9, 'ac_arch')
                mb.beam(tuple(k0[i]), tuple(k1[(i + 1) % 3]), 0.35, 0.35, 'ac_arch')
                mb.beam(tuple(k0[i]), tuple(k0[(i + 1) % 3]), 0.35, 0.35, 'ac_arch')
        # hangers from the arch down to the roof's inner edge
        for j in range(8, 33, 3):
            p = pts[j]
            ang = math.atan2(p[1] - c[1], p[0] - c[0]); kk = int(round((ang + math.pi) / (2 * math.pi) * n)) % n
            q = E(kk, r_rin[kk], z_in(kk) + 0.2)
            mb.beam(tuple(p - np.array([0, 0, 1.3])), q, 0.12, 0.12, 'ac_steel')
        for s in (-1, 1):   # concrete footings where the arch meets the ground
            mb.box((x0, c[1] + s * span / 2 * 0.99), 9.0, 9.0, 3.0, 90, 'ac_band')
    # the four spiral ramp towers at the corners
    for a in (45, 135, 225, 315):
        k = int(round((math.radians(a) + math.pi) / (2 * math.pi) * n)) % n
        tc = np.array(E(k, r_out[k] + 4.0, 0)[:2])
        mb.cyl(tuple(tc), 6.5, 0.0, 27.0, 'ac_band', n=24, top='ac_roof')
        turns, H, steps = 5, 25.0, 5 * 24
        for j in range(steps):
            a0 = 2 * math.pi * j / 24; a1 = 2 * math.pi * (j + 1) / 24
            z0 = H * j / steps; z1 = H * (j + 1) / steps
            for (ra, rb_, zz, m) in ((6.5, 14.0, 0.0, 'ac_ramp'), (14.0, 14.0, 1.2, 'ac_band')):
                pa = (tc[0] + ra * math.cos(a0), tc[1] + ra * math.sin(a0)); pb = (tc[0] + ra * math.cos(a1), tc[1] + ra * math.sin(a1))
                qa = (tc[0] + rb_ * math.cos(a0), tc[1] + rb_ * math.sin(a0)); qb = (tc[0] + rb_ * math.cos(a1), tc[1] + rb_ * math.sin(a1))
                if zz == 0.0:
                    mb.face([(pa[0], pa[1], z0), (qa[0], qa[1], z0), (qb[0], qb[1], z1), (pb[0], pb[1], z1)], m)
                    mb.face([(pa[0], pa[1], z0 - 0.5), (pb[0], pb[1], z1 - 0.5), (qb[0], qb[1], z1 - 0.5), (qa[0], qa[1], z0 - 0.5)], 'ac_band')
                else:   # the ramp's outer balustrade wall
                    mb.face([(qa[0], qa[1], z0 - 0.5), (qb[0], qb[1], z1 - 0.5), (qb[0], qb[1], z1 + zz), (qa[0], qa[1], z0 + zz)], m)
        mb.cyl(tuple(tc), 9.0, 27.0, 28.5, 'ac_band', n=24, top='ac_roof')


# ---------------- Qudos Bank Arena ----------------
def arena(mb, poly):
    """The Sydney SuperDome (Qudos Bank Arena): grey walls, a low domed roof with a raised lantern over the
    arena floor, a ring of white masts leaning out from the roof's edge holding it on stays, and the long
    curved canopy over the east forecourt (Google Earth)."""
    c = np.mean(np.array(poly), axis=0)
    t, r = polar(poly, c, 120); n = len(t)
    E = lambda k, rr, z: (c[0] + rr * math.cos(t[k % n]), c[1] + rr * math.sin(t[k % n]), z)
    HW, HR = 18.0, 27.0
    for k in range(n):
        a, b = k, k + 1
        mb.face([E(a, r[a] - 0.5, 0), E(b, r[b % n] - 0.5, 0), E(b, r[b % n] - 0.5, 14.0), E(a, r[a] - 0.5, 14.0)][::-1], 'qd_glass')
        mb.face([E(a, r[a], 14.0), E(b, r[b % n], 14.0), E(b, r[b % n], HW), E(a, r[a], HW)][::-1], 'qd_wall')
        mb.face([E(a, r[a] - 0.5, 14.0), E(b, r[b % n] - 0.5, 14.0), E(b, r[b % n], 14.0), E(a, r[a], 14.0)], 'qd_wall')
    # the roof: from the wall head up to the lantern's foot (0.45 of the radius)
    ring = [1.0, 0.85, 0.7, 0.55, 0.45]
    zr = lambda f: HW + (HR - HW) * (1 - (f - 0.45) / 0.55) ** 0.8
    for k in range(n):
        a, b = k, k + 1
        for f0, f1 in zip(ring, ring[1:]):
            mb.face([E(a, r[a] * f0, zr(f0)), E(b, r[b % n] * f0, zr(f0)), E(b, r[b % n] * f1, zr(f1)), E(a, r[a] * f1, zr(f1))][::-1], 'qd_roof')
        # the lantern: a 3 m upstand of louvres, then its own flat top
        f = 0.45
        mb.face([E(a, r[a] * f, HR), E(b, r[b % n] * f, HR), E(b, r[b % n] * f, HR + 3.0), E(a, r[a] * f, HR + 3.0)][::-1], 'qd_louvre')
    mb.cap([E(k, r[k] * 0.45, 0)[:2] for k in range(n)], HR + 3.0, 'qd_roof')
    # the masts: 16 white tubes leaning out from the roof edge, each with stays to the roof and a back-stay
    for j in range(16):
        k = int(j * n / 16)
        foot = np.array(E(k, r[k] - 1.0, HW))
        top = np.array(E(k, r[k] + 7.0, HW + 26.0))
        mb.beam(tuple(foot), tuple(top), 0.9, 0.9, 'qd_mast')
        for f in (0.85, 0.65, 0.5):
            mb.beam(tuple(top), E(k, r[k] * f, zr(f) + 0.2), 0.12, 0.12, 'qd_cable')
        mb.beam(tuple(top), E(k, r[k] + 16.0, 0.5), 0.14, 0.14, 'qd_cable')
        mb.box(E(k, r[k] + 16.0, 0)[:2], 2.0, 2.0, 0.8, 0, 'qd_wall')
    # the east canopy: a crescent of roof from the wall out 30 m, falling from 16 m to 9 m, on columns
    ks = [k for k in range(n) if math.cos(t[k]) > 0.55]
    for k in ks[:-1]:
        a, b = k, k + 1
        mb.face([E(a, r[a], 16.0), E(b, r[b], 16.0), E(b, r[b] + 30.0, 9.0), E(a, r[a] + 30.0, 9.0)][::-1], 'qd_roof')
        mb.face([E(a, r[a], 15.4), E(b, r[b], 15.4), E(b, r[b] + 30.0, 8.4), E(a, r[a] + 30.0, 8.4)], 'qd_under')
        mb.face([E(a, r[a] + 30.0, 8.4), E(b, r[b] + 30.0, 8.4), E(b, r[b] + 30.0, 9.1), E(a, r[a] + 30.0, 9.1)][::-1], 'qd_wall')
        if k % 3 == 0:
            mb.cyl(E(k, r[k] + 27.0, 0)[:2], 0.4, 0.0, 9.2, 'qd_mast', n=10)


# ---------------- the Brickpit Ring Walk ----------------
def ring_walk(mb, pts):
    """The Brickpit Ring Walk: a 4 m deck on round columns, glass-topped balustrades both sides."""
    P = [np.array(p) for p in pts]
    for p, q in zip(P, P[1:]):
        d = q - p; L = np.linalg.norm(d)
        if L < 0.5:
            continue
        u = d / L; v = np.array([-u[1], u[0]]) * 2.0
        z = 1.2
        mb.prism([tuple(p - v), tuple(q - v), tuple(q + v), tuple(p + v)], z - 0.6, z, 'rw_deck', top='rw_deck', bot='rw_deck')
        for s in (-1, 1):
            mb.beam((*(p + v * s * 0.97), z + 1.1), (*(q + v * s * 0.97), z + 1.1), 0.08, 0.08, 'rw_rail')
            mb.face([(*(p + v * s * 0.97), z), (*(q + v * s * 0.97), z), (*(q + v * s * 0.97), z + 1.05), (*(p + v * s * 0.97), z + 1.05)], 'rw_glass')
        mb.cyl(tuple(p), 0.5, -18.0, z - 0.6, 'rw_deck', n=10)


# ---------------- Woodchop Stadium ----------------
def woodchop(mb, poly):
    """The showground's round woodchop arena: an open ring of 12 stepped rows round a dirt floor, a red
    roof over its northern stand (Google Earth)."""
    c = np.mean(np.array(poly), axis=0)
    t, R = polar(poly, c, 72); n = len(t)
    E = lambda k, rr, z: (c[0] + rr * math.cos(t[k % n]), c[1] + rr * math.sin(t[k % n]), z)
    rows = 12
    for k in range(n):
        a, b = k, k + 1
        ri = lambda kk: R[kk % n] * 0.58
        for i in range(rows):
            f0, f1 = i / rows, (i + 1) / rows
            ra0 = ri(a) + (R[a] - 1.5 - ri(a)) * f0; ra1 = ri(a) + (R[a] - 1.5 - ri(a)) * f1
            rb0 = ri(b) + (R[b % n] - 1.5 - ri(b)) * f0; rb1 = ri(b) + (R[b % n] - 1.5 - ri(b)) * f1
            z0, z1 = 1.0 + 0.42 * i, 1.0 + 0.42 * (i + 1)
            mb.face([E(a, ra0, z1), E(b, rb0, z1), E(b, rb1, z1), E(a, ra1, z1)][::-1], 'wc_bench' if k % 8 else 'bl_coping')
            mb.face([E(a, ra0, z0), E(b, rb0, z0), E(b, rb0, z1), E(a, ra0, z1)], 'bl_wall')
        zt = 1.0 + 0.42 * rows
        mb.face([E(a, R[a] - 1.5, zt), E(b, R[b % n] - 1.5, zt), E(b, R[b % n], zt), E(a, R[a], zt)][::-1], 'bl_coping')
        mb.face([E(a, R[a], 0), E(b, R[b % n], 0), E(b, R[b % n], zt + 1.0), E(a, R[a], zt + 1.0)][::-1], 'pv_wall')
        mb.face([E(a, ri(a), 0), E(b, ri(b), 0), E(b, ri(b), 1.0), E(a, ri(a), 1.0)], 'bl_wall')
    mb.cap([E(k, R[k] * 0.58, 0)[:2] for k in range(n)], 0.05, 'wc_dirt')
    # the red roof over the north stand, on posts at the back and front
    ks = [k for k in range(n) if math.sin(t[k]) > 0.5]
    for k in ks[:-1]:
        a, b = k, k + 1
        mb.face([E(a, R[a] * 0.62, 9.0), E(b, R[b] * 0.62, 9.0), E(b, R[b] + 0.5, 11.0), E(a, R[a] + 0.5, 11.0)][::-1], 'wc_roof')
        mb.face([E(a, R[a] * 0.62, 8.8), E(b, R[b] * 0.62, 8.8), E(b, R[b] + 0.5, 10.8), E(a, R[a] + 0.5, 10.8)], 'bl_soffit')
        if k % 3 == 0:
            for f in (0.64, 0.99):
                mb.cyl(E(k, R[k] * f, 0)[:2], 0.2, 0.0, 9.0 + 2.0 * (f - 0.62) / 0.38, 'wc_post', n=8)


# ---------------- everything ----------------
SPECIAL_IDS = {'4385777': 'accor', '4987356': 'arena', '35029897': 'dome', '35029847': 'woodchop'}
ACCOR_BOWL, ACCOR_ROOF = '119388917', '119388911'
# Google Earth: Downes, Munro and Pig & Goat are the long low sheds with dark ventilator boxes; the other showground
# pavilions carry rows of small cross gables. 287001181 is the white oval marquee south of the Cattle Judging
# Lawn (about 9 m tall). Schmidt Arena's stand faces the ring to its north-west.
BIG_SHEDS = {'Downes Pavilion', 'Munro Pavilion', 'Pig & Goat Pavilion'}
MARQUEES = {'287001181': 6.5}
STAND_FACES = {'658169306': (-75.0, 160.0)}


def height_of(t, area):
    if 'height' in t:
        return max(3.0, num(t['height']))
    lv = num(t.get('building:levels', 0))
    if lv:
        return lv * 3.4 + 0.6
    b = t.get('building', 'yes')
    return {'house': 6.0, 'detached': 6.0, 'garage': 3.0, 'shed': 3.0, 'kiosk': 3.0, 'roof': 0.0, 'toilets': 3.2,
            'industrial': 9.0, 'warehouse': 9.0, 'parking': 12.0, 'train_station': 9.0, 'grandstand': 8.0,
            'tent': 5.0, 'service': 3.5}.get(b, 9.0 if area > 2000 else 5.0)


def main(osm_dir, out):
    N, W, R, pts = load(osm_dir)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    col = bpy.context.scene.collection
    acc_outer = clean(pts('4385777'))
    def inside(poly, q):
        x, y = q; c = False
        for i in range(len(poly)):
            (x0, y0), (x1, y1) = poly[i - 1], poly[i]
            if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
                c = not c
        return c
    groups = {}
    def G(name):
        if name not in groups:
            groups[name] = MB('surr_' + name)
        return groups[name]
    done = 0
    items = [(wid, t, refs) for wid, (t, refs) in W.items() if ('building' in t)]
    for rid, (t, mem) in R.items():
        if 'building' in t and t.get('type') == 'multipolygon':
            for typ, ref, role in mem:
                if typ == 'way' and role == 'outer' and ref in W and 'building' not in W[ref][0]:
                    items.append((ref, t, W[ref][1]))
    seen = set()
    for wid, t, refs in items:
        if wid in seen:
            continue
        seen.add(wid)
        poly = clean([N[i] for i in refs if i in N])
        if len(poly) < 3:
            continue
        cxy = np.mean(np.array(poly), axis=0)
        if math.hypot(*cxy) > R_MAX or in_site(cxy) or t.get('building') == 'roof' and wid not in SPECIAL_IDS:
            continue
        if t.get('layer', '0').startswith('-') or t.get('location') == 'underground':
            continue
        kind = SPECIAL_IDS.get(wid)
        if kind is None and wid != '4385777' and inside(acc_outer, cxy):
            continue   # Accor's own parts: the model below draws it
        area = abs(sarea(poly))
        if area < 12.0:
            continue
        h = height_of(t, area)
        if kind == 'accor':
            accor(G('accor'), acc_outer, clean(pts(ACCOR_BOWL)), clean(pts(ACCOR_ROOF)))
        elif kind == 'arena':
            arena(G('arena'), poly)
        elif kind == 'dome':
            dome(G('showground'), poly, 12.0, 31.0)
        elif kind == 'woodchop':
            woodchop(G('showground'), poly)
        else:
            name = t.get('name', ''); shape = t.get('roof:shape', '')
            lv = num(t.get('building:levels', 0))
            near_show = math.hypot(*cxy) < 520 and -330 < cxy[1] < 330
            if 'Pavil' in name and lv >= 3:
                halls(G('showground'), poly, h)
            elif t.get('building') == 'tent':
                rect_roof(G('showground'), poly, 4.0, 'round', m='pv_clere', wallm='pv_clere')
            elif wid in MARQUEES:
                marquee(G('showground'), poly, 2.5, MARQUEES[wid])
            elif t.get('building') == 'grandstand' and near_show:
                small_stand(G('showground'), poly, STAND_FACES.get(wid, (cxy[0], cxy[1] + 50)))
            elif name in BIG_SHEDS:
                big_shed(G('showground'), poly, 9.0)
            elif near_show and (('Pavil' in name) or (t.get('building') in ('yes', 'industrial', 'warehouse') and lv <= 2 and area > 1500)):
                pavilion(G('showground'), poly, max(7.5, min(h, 10.0)))
            elif shape in ('gabled', 'hipped', 'round', 'gabled_height_moved'):
                rect_roof(G('town'), poly, h, 'gabled' if shape.startswith('gabled') else shape)
            elif shape == 'dome':
                dome(G('town'), poly, h * 0.5, h)
            elif lv >= 3 or h >= 11.0:
                storeys(G('towers' if h > 30 else 'town'), poly, h, max(1, int(lv) or int(h // 3.4)))
            else:
                low_block(G('town'), poly, h)
        done += 1
    # the Brickpit Ring Walk
    if '287001201' in W:
        ring_walk(G('showground'), [N[i] for i in W['287001201'][1] if i in N])
    for g in groups.values():
        g.build(col)
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=False, export_cameras=False,
                              export_lights=False, export_image_format='WEBP')
    print('buildings', done, 'groups', {k: len(g.F) for k, g in groups.items()})


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
