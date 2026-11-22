# York Park's neighbours, modelled: the UTAS Inveresk precinct (the old Launceston railway workshops) south-east of
# the ground, Invermay Park's pavilions to the north, and the bigger Invermay Road blocks to the west.
#
# Each building stands on its OpenStreetMap footprint (neighbours_osm.json, frozen from the 2026-11-22 extract by
# `python3 neighbours.py --freeze <osm tiles>`); its walls, windows, doors and roof are read off the Google Earth 2026
# close-ups (qa/views_lm.json: lm_workshop_*, lm_riversedge_*, lm_stone_*, lm_tram_*, lm_invpark_*, lm_westblk_*,
# lm_nwblk_*, lm_sw_blk_*). Every window and door is an opening cut into the wall with its reveal, sill and glass set
# back (model/facades.py); sawtooth teeth, gables, parapets and solar arrays are geometry. Houses are not here: the
# ring's buildings.bin draws them (surrounds.py), and drops every footprint this file models.
#
#   blender -b --python neighbours.py -- <out.glb>      (or: python3 with pip bpy)
# Writes york_park_backdrop_part2.glb (model metres, Blender x east / y north / z up -> glTF), drawn by
# GroundModels.backdrop with the land (part1).
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
SPEC_OSM = os.path.join(HERE, 'neighbours_osm.json')


def freeze(paths):
    """Footprints of every non-house building within 460 m of the pitch centre, from the cached OSM tiles."""
    import importlib.util
    import numpy as np
    spec = importlib.util.spec_from_file_location('yps', os.path.join(HERE, 'surrounds.py'))
    M = importlib.util.module_from_spec(spec); sys.argv = ['x']; spec.loader.exec_module(M)
    S = M.S; foot = M.footprint(); ways = []
    for p in paths:
        ways += S.load(p)[1]
    out, seen = [], set()
    for t, p in ways:
        if 'building' not in t or len(p) < 4 or p[0] != p[-1]:
            continue
        P = np.array(p[:-1]); c = P.mean(0); k = (round(c[0], 1), round(c[1], 1))
        if k in seen or math.hypot(*c) > 460 or any(
                foot[int(np.clip(-y + S.SIZE / 2, 0, S.SIZE - 1)), int(np.clip(x + S.SIZE / 2, 0, S.SIZE - 1))] for x, y in P):
            continue
        seen.add(k)
        out.append({'c': [round(float(c[0]), 1), round(float(c[1]), 1)], 'pts': [[round(float(x), 2), round(float(y), 2)] for x, y in P],
                    'tags': {a: b for a, b in t.items() if a in ('building', 'name', 'height', 'building:levels')}})
    json.dump(out, open(SPEC_OSM, 'w'), indent=0)
    print('froze', len(out), 'footprints')


if __name__ == '__main__' and '--freeze' in sys.argv:
    freeze(sys.argv[sys.argv.index('--freeze') + 1:]); sys.exit(0)

sys.path.insert(0, os.path.join(HERE, 'model'))
import numpy as np
import bpy
import mb as MBm
import facades as FC

FOOT = json.load(open(SPEC_OSM))
Z0 = -0.6           # walls start below the ring's ground (y -0.04) so no sliver of sky shows under them


def find(e, n):
    b = min(FOOT, key=lambda f: math.hypot(f['c'][0] - e, f['c'][1] - n))
    assert math.hypot(b['c'][0] - e, b['c'][1] - n) < 3.0, ('no footprint near', e, n)
    return b


def ccw(P):
    P = [tuple(map(float, p)) for p in P]
    return P if MBm.sarea(P) > 0 else P[::-1]


def clip(P, u, a, keep_ge):
    """Sutherland-Hodgman: the part of polygon P with dot(p, u) >= a (keep_ge) or <= a."""
    out = []
    f = (lambda p: np.dot(p, u) - a) if keep_ge else (lambda p: a - np.dot(p, u))
    for i in range(len(P)):
        p, q = np.array(P[i - 1]), np.array(P[i]); fp, fq = f(p), f(q)
        if fq >= 0:
            if fp < 0:
                out.append(tuple(p + (q - p) * fp / (fp - fq)))
            out.append(tuple(q))
        elif fp >= 0:
            out.append(tuple(p + (q - p) * fp / (fp - fq)))
    return out


# ---------------- walls ----------------
def openings_for(L, H, st):
    """The holes of one wall [(s0, s1, z0, z1, fill, mull)]: rows of windows per bay, ribbon bands, ground doors."""
    holes = []
    if L < 2.4:
        return holes
    for row in st.get('rows', []):
        z0, z1 = row['z']
        if z1 > H - 0.25:
            continue
        bay = row.get('bay', 4.0)
        for a, b in FC.bays(L, bay):
            if row.get('ribbon'):
                s0, s1 = a + row.get('pier', 0.3), b - row.get('pier', 0.3)
            else:
                m = 0.5 * (a + b); w = min(row['w'], b - a - 0.6); s0, s1 = m - w / 2, m + w / 2
            if s1 - s0 > 0.4 and s0 > 0.3 and s1 < L - 0.3:
                holes.append((s0, s1, z0, z1, row.get('fill', st.get('glass', 'glass_dark')), row.get('mull', 0.0),
                              row.get('transom')))
    for d in st.get('doors', []):          # ground doors: every `every` m, or at fixed s
        z1 = d['h']
        if z1 > H - 0.4:
            continue
        spots = d.get('at') or [0.5 * (a + b) for a, b in FC.bays(L, d['every'])] if L > d.get('min_len', 8.0) else []
        for m in spots:
            s0, s1 = m - d['w'] / 2, m + d['w'] / 2
            if s0 > 0.4 and s1 < L - 0.4 and not any(h[0] < s1 and s0 < h[1] and h[2] < z1 for h in holes):
                holes.append((s0, s1, 0.0, z1, d.get('fill', 'door_roller'), d.get('mull', 0.0), None))
    return holes


def facade(mb, W, H, st, top=None):
    """One wall of a building: the wall itself with its holes, each hole's reveal and fill, the bands and the plinth;
    then above H the gable or tooth infill up to top(x, y) when the roof rises over this wall."""
    m = st['mat']
    holes = openings_for(W.L, H, st)
    FC.wall(mb, W, 0.0, W.L, Z0, H, m, [h[:4] for h in holes])
    for s0, s1, z0, z1, fill, mull, tr in holes:
        if fill == 'door_roller':
            FC.opening(mb, W, s0, s1, z0, z1, 0.25, st.get('reveal', m), 'door_roller')
        else:
            FC.opening(mb, W, s0, s1, z0, z1, st.get('depth', 0.18), st.get('reveal', m), fill, mull=mull,
                       mull_m=st.get('frame', 'frame_alu'), transom=tr)
    for z0, z1, o, bm in st.get('bands', []):
        if z1 <= H + 0.01:
            FC.block(mb, W, 0.0, W.L, z0, z1, 0.0, o, bm, ends=True)
    if st.get('piers'):
        pw, pd, pm = st['piers']
        for a, b in FC.bays(W.L, st.get('pier_bay', 6.0)):
            FC.block(mb, W, a, a + pw, Z0, H, 0.0, pd, pm)
    if top is None:
        return
    # infill above the eave: quads with a sloped top, broken where the roof changes plane (tooth or ridge)
    ss = np.linspace(0.0, W.L, max(2, int(W.L / 0.5) + 1))
    zt = [top(*W.xy(s)) for s in ss]
    tu, tv = FC.tile(m)
    for k in range(len(ss) - 1):
        s0, s1 = ss[k], ss[k + 1]
        za = top(*W.xy(s0 + 1e-3)); zb = top(*W.xy(s1 - 1e-3))
        if max(za, zb) <= H + 1e-3:
            continue
        FC.oface(mb, [W.p3(s0, H), W.p3(s1, H), W.p3(s1, max(zb, H)), W.p3(s0, max(za, H))], m, W.normal(0.5 * (s0 + s1)),
                 [(s0 / tu, H / tv), (s1 / tu, H / tv), (s1 / tu, max(zb, H) / tv), (s0 / tu, max(za, H) / tv)])


def edges(P):
    """Each edge of a CCW polygon as a facades.Path with its outward side to the right."""
    out = []
    for i in range(len(P)):
        p, q = np.array(P[i]), np.array(P[(i + 1) % len(P)])
        d = q - p
        if np.linalg.norm(d) < 0.3:
            continue
        n = np.array([d[1], -d[0]]) / np.linalg.norm(d)
        mid = 0.5 * (p + q)
        out.append(FC.Path([p, q], outward_from=tuple(mid - n)))
    return out


# ---------------- roofs ----------------
def plane_cap(mb, poly, zf, m, axis=None, uvscale=None):
    """A roof plane over polygon poly, z = zf(x, y); ribs run down the slope along `axis` (a unit vector)."""
    if len(poly) < 3 or abs(MBm.sarea(poly)) < 0.05:
        return
    tu, tv = FC.tile(m)
    ax = np.array(axis if axis is not None else (0.0, 1.0)); ac = np.array([-ax[1], ax[0]])
    for tri in MBm.earclip(ccw(poly)):
        pts = [(x, y, zf(x, y)) for x, y in tri]
        uv = [(np.dot((x, y), ac) / tu, np.dot((x, y), ax) / tv) for x, y in tri]
        mb.face(pts, m, uv=uv)


def roof_saw(mb, P, H, r, pitch, axis, mat, glaze='glass_dark', frame='frame_alu', skylights=None):
    """North-light sawtooth: teeth repeat along `axis` (unit, pointing the way the glazing faces); each tooth rises from
    H at its back to H + r at its front, where a glazed upstand drops back to H. Returns the roof height function."""
    u = np.array(axis, float); u /= np.linalg.norm(u)
    proj = [np.dot(p, u) for p in P]; a0, a1 = min(proj), max(proj)
    n = max(1, int(round((a1 - a0) / pitch))); p = (a1 - a0) / n
    def h(x, y):
        t = (np.dot((x, y), u) - a0) / p; k = min(int(t), n - 1)
        return H + r * (t - k)
    for k in range(n):
        lo, hi = a0 + k * p, a0 + (k + 1) * p
        S = clip(clip(P, u, lo, True), u, hi, False)
        if len(S) < 3:
            continue
        plane_cap(mb, S, lambda x, y, lo=lo: H + r * (np.dot((x, y), u) - lo) / p, mat, axis=u)
        if k < n - 1:   # the glazed upstand at the tooth's front (the outer wall carries the last one)
            on = [q for q in S if abs(np.dot(q, u) - hi) < 1e-3]
            if len(on) >= 2:
                v = np.array([-u[1], u[0]]); on.sort(key=lambda q: np.dot(q, v))
                A, B = np.array(on[0]), np.array(on[-1])
                W = FC.Path([A, B], outward_from=tuple(0.5 * (A + B) - u))
                FC.panel(mb, W, 0, W.L, H, H + r, -0.25, glaze)
                FC.hface(mb, W, 0, W.L, H + r, -0.25, 0.0, mat, False)
                for s in np.arange(1.5, W.L - 0.2, 1.5):
                    FC.block(mb, W, s - 0.04, s + 0.04, H, H + r, -0.25, -0.18, frame, top=False, bottom=False)
                FC.block(mb, W, 0, W.L, H + r - 0.25, H + r, -0.25, 0.06, mat, ends=False)   # the tooth's head flashing
        if skylights and k % skylights[0] == 0:          # translucent strips laid in the slope (Stone Building)
            v = np.array([-u[1], u[0]]); sw = skylights[1]
            pv = [np.dot(q, v) for q in S]
            for c in np.arange(min(pv) + 3.0, max(pv) - 3.0, skylights[2]):
                R_ = clip(clip(clip(clip(S, v, c - sw / 2, True), v, c + sw / 2, False), u, lo + 0.25 * p, True), u, hi - 0.25 * p, False)
                lift = lambda x, y, lo=lo: H + r * (np.dot((x, y), u) - lo) / p + 0.06
                plane_cap(mb, R_, lift, 'skylight', axis=u)
    return h


def roof_gables(mb, P, H, r, span, axis, mat, gable_mat=None):
    """Parallel gabled bays: ridges run along `axis`, one bay every `span` m across it. Returns the height function."""
    v = np.array(axis, float); v /= np.linalg.norm(v); u = np.array([v[1], -v[0]])
    proj = [np.dot(p, u) for p in P]; a0, a1 = min(proj), max(proj)
    n = max(1, int(round((a1 - a0) / span))); w = (a1 - a0) / n
    def h(x, y):
        t = (np.dot((x, y), u) - a0) / w; k = min(int(t), n - 1); f = t - k
        return H + r * (1 - abs(2 * f - 1))
    for k in range(n):
        for lo, hi, up in ((a0 + k * w, a0 + (k + 0.5) * w, True), (a0 + (k + 0.5) * w, a0 + (k + 1) * w, False)):
            S = clip(clip(P, u, lo, True), u, hi, False)
            if len(S) >= 3:
                if up:
                    zf = lambda x, y, lo=lo: H + r * (np.dot((x, y), u) - lo) / (0.5 * w)
                else:
                    zf = lambda x, y, hi=hi: H + r * (hi - np.dot((x, y), u)) / (0.5 * w)
                plane_cap(mb, S, zf, mat, axis=u if up else -u)
    return h


def roof_flat(mb, P, H, mat, parapet=0.8, cap='sill'):
    """A flat roof 0.15 m below a parapet whose inner face and capping are modelled."""
    plane_cap(mb, P, lambda x, y: H - 0.15, mat)
    for W in edges(P):
        FC.panel(mb, W, 0, W.L, H - 0.15, H + parapet, -0.25, cap, facing=-1.0)
        FC.hface(mb, W, 0, W.L, H + parapet, -0.25, 0.05, cap, True)
    return lambda x, y: H + parapet


def solar(mb, P, zf, axis, frac=(0.1, 0.9), rows=1, lift=0.15):
    """A modelled solar array on a roof plane: panel slabs 0.05 m thick on rails, over polygon P (already on one plane)."""
    u = np.array(axis, float); u /= np.linalg.norm(u); v = np.array([-u[1], u[0]])
    pu = [np.dot(q, u) for q in P]; pv = [np.dot(q, v) for q in P]
    a0, a1 = min(pu), max(pu); b0, b1 = min(pv), max(pv)
    a0, a1 = a0 + (a1 - a0) * frac[0], a0 + (a1 - a0) * frac[1]
    S = clip(clip(clip(clip(P, u, a0, True), u, a1, False), v, b0 + 1.0, True), v, b1 - 1.0, False)
    if len(S) < 3:
        return
    top = lambda x, y: zf(x, y) + lift + 0.05
    plane_cap(mb, S, top, 'solar', axis=u)
    for W in edges(ccw(S)):
        ss = np.linspace(0, W.L, max(2, int(W.L) + 1))
        for s0, s1 in zip(ss, ss[1:]):
            x0, y0 = W.xy(s0); x1, y1 = W.xy(s1)
            FC.oface(mb, [(x0, y0, zf(x0, y0) + lift), (x1, y1, zf(x1, y1) + lift), (x1, y1, top(x1, y1)), (x0, y0, top(x0, y0))],
                     'frame_alu', W.normal(0.5 * (s0 + s1)))


# ---------------- the wall treatments (Google Earth 2026 close-ups) ----------------
SHED = dict(mat='clad_bluegrey', rows=[dict(z=(2.6, 4.0), w=1.4, bay=4.2, mull=0.47, transom=[3.3])], frame='paint_white',
            doors=[dict(h=4.2, w=4.0, every=24.0, min_len=20.0)], reveal='paint_white',
            bands=[(-0.6, 0.5, 0.06, 'conc_wall')])                                  # the railway sheds: small multi-pane windows
SHED_RED = dict(SHED, mat='brick_red', reveal='render_cream', frame='paint_white')
WORKSHOP = dict(mat='clad_grey', frame='frame_black', reveal='panel_dark',
                rows=[dict(z=(0.4, 4.6), bay=6.0, ribbon=True, pier=0.4, mull=1.5, transom=[3.4]),
                      dict(z=(6.2, 8.6), bay=6.0, ribbon=True, pier=0.4, mull=1.5)],
                bands=[(4.6, 6.2, 0.1, 'panel_dark'), (-0.6, 0.4, 0.05, 'panel_dark')])
LEVEE = dict(mat='panel_dark', frame='frame_black', rows=[dict(z=(0.6, 3.2), bay=5.0, ribbon=True, pier=0.5, mull=1.25),
                                                         dict(z=(4.4, 6.6), bay=5.0, ribbon=True, pier=0.5, mull=1.25)])
SILVER = dict(mat='clad_silver', frame='frame_alu', depth=0.3,
              rows=[dict(z=(0.4, 3.4), bay=7.2, w=4.8, mull=1.2), dict(z=(5.0, 6.4), bay=4.8, w=2.4, mull=0.8),
                    dict(z=(8.6, 10.0), bay=4.8, w=2.4, mull=0.8), dict(z=(12.2, 13.6), bay=4.8, w=2.4, mull=0.8)])
LIBRARY = dict(mat='clad_silver', frame='frame_alu', depth=0.3, rows=[dict(z=(0.5, 3.6), bay=6.0, ribbon=True, pier=0.6, mull=1.5)],
               bands=[(-0.6, 0.5, 0.05, 'conc_wall')])
HERITAGE = dict(mat='render_cream', frame='paint_white', reveal='render_cream', depth=0.3,
                rows=[dict(z=(1.0, 3.4), bay=3.6, w=1.8, mull=0.6, transom=[2.6]), dict(z=(5.0, 7.4), bay=3.6, w=1.8, mull=0.6, transom=[6.6]),
                      dict(z=(9.0, 11.2), bay=3.6, w=1.8, mull=0.6, transom=[10.4])],
                bands=[(4.2, 4.5, 0.08, 'render_white'), (8.2, 8.5, 0.08, 'render_white'), (-0.6, 0.6, 0.05, 'conc_wall')])
SCHOOL = dict(mat='render_sand', frame='frame_alu', rows=[dict(z=(0.9, 2.6), bay=3.6, w=2.4, mull=0.8),
                                                         dict(z=(4.0, 5.7), bay=3.6, w=2.4, mull=0.8)])
SHOP = dict(mat='render_white', frame='frame_alu', rows=[dict(z=(0.3, 3.0), bay=6.0, ribbon=True, pier=0.5, mull=1.5),
                                                         dict(z=(4.4, 5.8), bay=3.0, w=1.4, mull=0.7)],
            bands=[(3.2, 3.6, 0.6, 'paint_white')])                                    # Invermay Road: shopfronts, a verandah fascia
WAREHOUSE = dict(mat='clad_pale', rows=[dict(z=(2.4, 3.4), bay=8.0, w=2.4, mull=0.8)],
                 doors=[dict(h=4.5, w=4.5, every=18.0, min_len=14.0)])
PAVILION = dict(mat='brick_red', frame='paint_white', reveal='render_cream', rows=[dict(z=(1.0, 2.4), bay=3.0, w=1.6, mull=0.8)],
                doors=[dict(h=2.4, w=1.2, every=12.0, min_len=10.0, fill='glass_dark')])


MEASURED = json.load(open(os.path.join(HERE, 'neighbours_heights.json'))) if os.path.exists(
    os.path.join(HERE, 'neighbours_heights.json')) else {}


def measured(c):
    """(eave, ridge, median) in m above the turf, read off Google Earth with the mouse at 9 spots on the roof
    (qa/probe.py, the calibrated tool's status bar; whole metres). None when fewer than 4 spots hit the roof."""
    m = MEASURED.get('b_%d_%d' % (round(c[0]), round(c[1])))
    if not m:
        return None
    hs = sorted(h for h in m['all'] if h > 1.5)
    if len(hs) < 4:
        return None
    q = lambda f: hs[min(len(hs) - 1, int(f * (len(hs) - 1) + 0.5))]
    return q(0.25), q(0.9), q(0.5)


def build_one(mb, b, sty, H, roof):
    P = ccw(b['pts'])
    kind = roof[0]
    m = measured(b['c'])
    if m:                    # Google Earth's measured heights win over the eye's
        eave, ridge, med = m
        if kind == 'flat':
            H = med
        else:
            H = eave
            r = max(0.8, ridge - eave)
            if kind == 'gables':
                r = min(r, 0.3 * roof[2])
            roof = (roof[0], r) + tuple(roof[2:])
    if kind == 'saw':
        _, r, pitch, axis, mat = roof[:5]; extra = roof[5] if len(roof) > 5 else {}
        top = roof_saw(mb, P, H, r, pitch, axis, mat, skylights=extra.get('skylights'))
        for tooth in extra.get('solar', []):
            u = np.array(axis, float); u /= np.linalg.norm(u); pr = [np.dot(q, u) for q in P]; a0, a1 = min(pr), max(pr)
            n = max(1, int(round((a1 - a0) / pitch))); p = (a1 - a0) / n
            S = clip(clip(P, u, a0 + tooth * p + 0.6, True), u, a0 + (tooth + 1) * p - 0.6, False)
            if len(S) >= 3:
                v_ = np.array([-u[1], u[0]]); pv = [np.dot(q, v_) for q in S]; f0, f1 = extra.get('solar_frac', (0.0, 1.0))
                S = clip(clip(S, v_, min(pv) + f0 * (max(pv) - min(pv)), True), v_, min(pv) + f1 * (max(pv) - min(pv)), False)
                if len(S) >= 3:
                    solar(mb, S, lambda x, y, lo=a0 + tooth * p: H + r * (np.dot((x, y), u) - lo) / p, u, frac=(0.0, 1.0))
    elif kind == 'gables':
        _, r, span, axis, mat = roof[:5]
        top = roof_gables(mb, P, H, r, span, axis, mat)
    else:
        top = roof_flat(mb, P, H, roof[1], parapet=roof[2] if len(roof) > 2 else 0.8)
    for W in edges(P):
        facade(mb, W, H, sty, top=top if kind != 'flat' else None)
        if kind == 'flat':      # the parapet's outer face above the roof line, in the wall's own cladding
            FC.panel(mb, W, 0, W.L, H, top(0, 0), 0.0, sty['mat'])


def rivers_edge(mb, b):
    """River's Edge (2020): a wedge in zinc standing seams, four floors of punched windows, and a folded parapet that
    zigzags up and down along the river side; behind it a white membrane roof with a sloped skylight and solar."""
    P = ccw(b['pts']); outline = []
    ms = measured(b['c']); H = ms[2] if ms else 15.5     # Google Earth: roof 19 m, the folds' peaks 22 m
    for i, W in enumerate(edges(P)):
        zig = W.L > 60
        if zig:     # the long sides fold in plan: facets 4.6 m wide stepping 1.4 m out and back, each with a slot window per floor
            p0, p1 = W.P[0], W.P[-1]; d = (p1 - p0) / W.L; nrm = np.array([d[1], -d[0]])
            n = max(2, int(round(W.L / 4.6)))
            pts = [p0 + d * W.L * k / n + nrm * (1.4 if k % 2 else 0.0) for k in range(n + 1)]
            W = FC.Path(pts, outward_from=tuple(0.5 * (p0 + p1) - nrm * 5))
            holes = []
            for k in range(n):
                m = 0.5 * (W.S[k] + W.S[k + 1])
                for z0, z1 in ((0.6, 3.6), (4.8, 7.0), (8.4, 10.6), (12.0, 14.2)):
                    if (k + int(z0)) % 3:
                        holes.append((m - 0.6, m + 0.6, z0, z1, 'glass_dark', 0.0, None))
            top = lambda s, W=W: H + (max(1.5, ms[1] - ms[2]) if ms else 2.4) * (1 - abs(((s / (2 * W.L / n)) % 1) * 2 - 1))
        else:
            st = dict(SILVER, rows=[dict(z=(0.4, 7.0), bay=6.0, ribbon=True, pier=0.5, mull=1.5, transom=[3.6])] + SILVER['rows'][2:])
            holes = openings_for(W.L, H, st)
        outline += [tuple(q) for q in W.P[:-1]]
        FC.wall(mb, W, 0.0, W.L, Z0, H, 'clad_silver', [h[:4] for h in holes])
        for s0, s1, z0, z1, fill, mull, tr in holes:
            FC.opening(mb, W, s0, s1, z0, z1, 0.3, 'clad_silver', fill, mull=mull, mull_m='frame_alu', transom=tr)
        ss = sorted(set(np.linspace(0, W.L, max(2, int(W.L / 1.5) + 1)).tolist()) | set(W.S.tolist()))
        for s0, s1 in zip(ss, ss[1:]):
            if s1 - s0 < 1e-3:
                continue
            za = top(s0) if zig else H + 0.9; zb = top(s1) if zig else H + 0.9
            nr = W.normal(0.5 * (s0 + s1))
            FC.oface(mb, [W.p3(s0, H), W.p3(s1, H), W.p3(s1, zb), W.p3(s0, za)], 'clad_silver', nr)
            FC.oface(mb, [W.p3(s0, H - 0.2, -0.3), W.p3(s1, H - 0.2, -0.3), W.p3(s1, zb, -0.3), W.p3(s0, za, -0.3)], 'roof_white', -nr)
            FC.oface(mb, [W.p3(s0, za, -0.3), W.p3(s1, zb, -0.3), W.p3(s1, zb, 0.0), W.p3(s0, za, 0.0)], 'sill', np.array([0, 0, 1.0]))
    plane_cap(mb, outline, lambda x, y: H - 0.2, 'roof_white')
    # the skylight: a glazed triangle sloping up from the roof towards the river (lm_riversedge_000/120)
    c = np.mean(P, axis=0); A = c + np.array([-8.0, -2.0]); B = c + np.array([8.0, 10.0]); C = c + np.array([10.0, -6.0])
    tri = [(A, H - 0.2), (B, H + 2.6), (C, H + 1.0)]
    mb.face([(*A, H - 0.2), (*C, H + 1.0), (*B, H + 2.6)], 'glass_dark')
    for (p, zp), (q, zq) in zip(tri, tri[1:] + tri[:1]):
        mb.face([(*p, H - 0.2), (*q, H - 0.2), (*q, zq), (*p, zp)], 'clad_silver')
        mb.beam((*p, zp), (*q, zq), 0.12, 0.12, 'frame_alu')
    for k in range(1, 6):          # glazing bars from the low edge up to the ridge corner
        t = k / 6.0; q = A + (C - A) * t
        mb.beam((*q, H - 0.2 + 1.2 * t), (*B, H + 2.6), 0.06, 0.06, 'frame_alu')
    pl = [tuple(c + np.array([-14.0, 8.0])), tuple(c + np.array([-4.0, 16.0])), tuple(c + np.array([2.0, 9.0])), tuple(c + np.array([-8.0, 1.0]))]
    solar(mb, ccw(pl), lambda x, y: H - 0.2, (0.6, 0.8), frac=(0.0, 1.0), lift=0.4)
    # plant: two boxes on the roof
    for off in ((-16.0, 0.0), (6.0, 18.0)):
        mb.box(tuple(c + np.array(off)), 6.0, 4.0, 2.2, 38.0, 'clad_grey', z0=H - 0.2, mtop='roof_flat')


def tank(mb, c, r, h):
    mb.cyl(c, r, Z0, h, 'clad_pale', n=20, top='roof_pale')


# id: (centroid E, N) -> (treatment, eave H, roof)
#   roof ('saw', rise, pitch, glazing-facing axis, material, extras) | ('gables', rise, span, ridge axis, material) | ('flat', material)
SOUTH = (0.0, -1.0)
def ax(deg):   # a unit vector at compass-ish angle deg in model x/y (degrees from +x, counter-clockwise)
    return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))


B = [
    ((116.1, -72.9), 'The Workshop', WORKSHOP, 10.5, ('saw', 3.2, 9.0, ax(-100.8), 'roof_pale', {'solar': [5, 6]})),
    ((115.3, -24.1), 'Levee Studio', LEVEE, 7.6, ('flat', 'roof_flat')),
    ((132.2, -64.9), 'Workshop stair', WORKSHOP, 12.0, ('flat', 'roof_flat')),
    ((140.9, -53.3), 'Workshop annex', LEVEE, 7.6, ('flat', 'roof_flat')),
    ((124.6, -168.4), 'The Annexe', SHED, 8.0, ('saw', 3.0, 7.5, ax(-52.0), 'roof_pale')),
    ((93.7, -194.8), 'Library', LIBRARY, 7.4, ('saw', 3.6, 6.8, ax(-52.0), 'roof_pale')),
    ((138.0, -234.2), 'Stone Building', HERITAGE, 12.0, ('saw', 3.2, 9.0, ax(-52.0), 'roof_pale', {'skylights': (1, 1.2, 5.0), 'solar': [2, 4], 'solar_frac': (0.15, 0.55)})),
    ((184.4, -128.6), 'shed 104', SHED, 6.8, ('saw', 2.8, 7.0, ax(-52.0), 'roof_pale')),
    ((198.0, -154.6), 'shed 105', SHED, 7.2, ('saw', 2.8, 7.0, ax(-52.0), 'roof_pale')),
    ((232.4, -198.5), 'shed 103', SHED, 6.4, ('gables', 2.6, 10.0, ax(38.0), 'roof_grey')),
    ((221.7, -193.8), 'shed 107', SHED, 6.4, ('gables', 2.6, 11.2, ax(37.9), 'roof_grey')),
    ((248.5, -216.9), 'shed 106', SHED_RED, 5.4, ('gables', 1.8, 7.9, ax(37.9), 'roof_rust')),
    ((154.8, -279.5), 'QVMAG Inveresk', SHED, 8.6, ('gables', 3.2, 12.6, ax(37.9), 'roof_grey')),
    ((20.1, -223.5), 'Big Picture School', SCHOOL, 7.2, ('flat', 'roof_flat')),
    ((7.7, -250.2), 'Tramway Museum', SHED_RED, 5.8, ('gables', 2.4, 17.5, ax(-165.6), 'roof_grey')),
    ((-26.8, -274.6), 'Tramsheds', SHED_RED, 5.0, ('gables', 2.0, 13.6, ax(-166.0), 'roof_grey')),
    ((-39.0, -261.6), 'Tramsheds hall', SHED, 6.0, ('gables', 2.4, 17.5, ax(105.0), 'roof_grey')),
    ((-40.1, -238.0), 'Inveresk Rd workshop', WAREHOUSE, 6.0, ('flat', 'roof_flat')),
    ((-88.6, 150.5), 'Invermay Park stand', PAVILION, 4.8, ('gables', 1.4, 13.9, ax(-74.4), 'roof_white')),
    ((-65.6, 216.9), 'Invermay Park pavilion', PAVILION, 4.6, ('gables', 2.6, 18.8, ax(-117.0), 'roof_red')),
    ((-71.1, 183.6), 'Invermay Park rooms', PAVILION, 3.6, ('gables', 1.6, 8.3, ax(-92.4), 'roof_red')),
    ((-95.0, 92.9), 'Invermay Park kiosk', PAVILION, 3.4, ('gables', 1.6, 8.9, ax(-163.0), 'roof_red')),
    ((-42.4, 244.0), 'Invermay Park shed', PAVILION, 3.4, ('gables', 1.6, 7.9, ax(44.5), 'roof_red')),
    ((72.4, 308.8), 'Inveresk Rd shed', WAREHOUSE, 6.5, ('gables', 2.4, 22.3, ax(41.6 + 90), 'roof_grey')),
]


HOUSES = ('house', 'detached', 'semidetached_house', 'bungalow', 'terrace', 'garage', 'garages', 'shed', 'carport', 'roof')
ROOF_CYCLE = ('roof_pale', 'roof_white', 'roof_grey', 'roof_pale', 'roof_rust', 'roof_white')


def area(P):
    return abs(MBm.sarea([tuple(p) for p in P]))


def obb(P):
    """The smallest box round a footprint: its long-side angle (deg), length, width and how much of it the footprint fills."""
    A = np.array(P, float); best = None
    for i in range(len(A)):
        d = A[(i + 1) % len(A)] - A[i]; L = np.linalg.norm(d)
        if L < 1e-6:
            continue
        u = d / L; v = np.array([-u[1], u[0]]); a = A @ u; c = A @ v
        ar = (a.max() - a.min()) * (c.max() - c.min())
        if best is None or ar < best[0]:
            best = (ar, u, a.max() - a.min(), c.max() - c.min())
    ar, u, L, W = best
    if W > L:
        u, L, W = np.array([-u[1], u[0]]), W, L
    return math.degrees(math.atan2(u[1], u[0])), L, W, area(P) / ar


def build_all(out):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    used = []
    for (e, n), name, sty, H, roof in B:
        b = find(e, n); used.append(b['c'])
        m = MBm.MB('nb_' + name.lower().replace(' ', '_').replace("'", ''))
        build_one(m, b, sty, H, roof)
        m.build()
    # OpenStreetMap's small university block between the Annexe and the sheds reads turf height on Google Earth
    # (gone, or never there): drawn by nobody.
    used.append(find(151.0, -174.4)['c'])
    m = MBm.MB('nb_rivers_edge'); b = find(150.1, -96.7); used.append(b['c']); rivers_edge(m, b)
    m.build()
    # Every other non-house footprint over 400 m2 (Invermay's warehouses, workshops and shops) gets the treatment most
    # of them show on Google Earth (lm_westblk_*, lm_nwblk_*, lm_sw_blk_*): a low-pitched gabled iron roof over
    # sheet walls with roller doors, or a flat roof behind a parapet where the footprint is not a plain box.
    m = MBm.MB('nb_invermay_sheds'); k = 0
    for b in FOOT:
        if b['c'] in used or b['tags'].get('building') in HOUSES or area(b['pts']) < 400.0:
            continue
        P = ccw(b['pts']); ang, L, Wd, fill = obb(P)
        roofm = ROOF_CYCLE[int(abs(b['c'][0] * 7 + b['c'][1] * 13)) % len(ROOF_CYCLE)]
        H = 5.2 if area(P) < 1500 else 6.4
        if fill > 0.85:
            span = Wd if Wd < 32 else Wd / round(Wd / 18.0)
            build_one(m, b, WAREHOUSE, H, ('gables', 0.09 * span, span, ax(ang), roofm))
        else:
            build_one(m, b, SHOP if b['tags'].get('building') == 'retail' else WAREHOUSE, H, ('flat', 'roof_flat', 0.9))
        used.append(b['c']); k += 1
    print('invermay sheds', k)
    for c in ((172.0, -168.0), (176.0, -164.0)):   # the two rainwater tanks by the Annexe (lm_riversedge_120)
        tank(m, c, 2.0, 3.2)
    m.build()
    # Material names must not start roof_ or facade_: GroundModels gives those the backdrop shader (vertex-tinted).
    for mt in bpy.data.materials:
        if not mt.name.startswith('nb_'):
            mt.name = 'nb_' + mt.name
    json.dump(used, open(os.path.join(HERE, 'neighbours_used.json'), 'w'))
    for ob in bpy.context.scene.objects:
        ob.select_set(ob.type == 'MESH')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_cameras=False, export_lights=False,
                              export_image_format='WEBP')   # a third of the size; Godot reads EXT_texture_webp
    nt = sum(len(p.vertices) - 2 for ob in bpy.context.scene.objects if ob.type == 'MESH' for p in ob.data.polygons)
    print('neighbours:', len(used), 'buildings,', nt, 'triangles ->', out)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    build_all(argv[0] if argv else os.path.join(HERE, '..', '..', '..', 'assets', 'grounds', 'york_park', 'york_park_backdrop_part2.glb'))
