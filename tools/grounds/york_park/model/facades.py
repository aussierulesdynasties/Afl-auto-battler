# York Park's outside walls, modelled (the MCG standard, docs/MCG_STANDARD.md "Walls", 2026-11-22).
# Before, each wall was one flat strip under a texture that painted its windows, louvres, piers and bands on.
# Now every window and louvre is an opening cut into the wall with reveals, a sill and a head, with the glass
# or the louvre blades set back inside it; piers, bands and fascias stand proud with their own top, ends and
# underside. Textures carry only detail too small to read in depth: sheet ribs, panel joints, render and brick.
#
# A wall runs along a Path (a polyline in plan with its outward side); s is metres along it, z metres up from
# the ground, out metres outward of the wall line. Each wall kind below is laid out bay by bay from the same
# reference measurements the painted textures used (model/paint.py, board 5_textures_vs_photo: drone5,
# aerial4, the grandstand and Centre West photos, Google Earth 2026 for the unchanged stands).
import math
import numpy as np


class Path:
    def __init__(s, pts, outward_from=(0.0, 0.0), flip=False):
        P = np.array(pts, float)
        keep = [0] + [i for i in range(1, len(P)) if np.linalg.norm(P[i] - P[i - 1]) > 1e-4]
        s.P = P[keep]
        d = np.diff(s.P, axis=0); L = np.linalg.norm(d, axis=1)
        s.S = np.concatenate([[0.0], np.cumsum(L)]); s.L = float(s.S[-1])
        t = d / L[:, None]; n = np.stack([t[:, 1], -t[:, 0]], 1)
        mid = 0.5 * (s.P[1:] + s.P[:-1])
        if np.sum(np.einsum('ij,ij->i', n, mid - np.array(outward_from))) < 0:
            n = -n
        if flip:
            n = -n
        vn = np.zeros_like(s.P); vn[:-1] += n; vn[1:] += n
        s.N = vn / np.linalg.norm(vn, axis=1)[:, None]
        s.T = t

    def xy(s, a, out=0.0):
        a = min(max(a, 0.0), s.L)
        i = int(np.clip(np.searchsorted(s.S, a) - 1, 0, len(s.S) - 2))
        f = (a - s.S[i]) / max(s.S[i + 1] - s.S[i], 1e-9)
        p = s.P[i] + (s.P[i + 1] - s.P[i]) * f
        n = s.N[i] + (s.N[i + 1] - s.N[i]) * f; n = n / np.linalg.norm(n)
        return p + n * out

    def p3(s, a, z, out=0.0):
        x, y = s.xy(a, out); return (float(x), float(y), float(z))

    def normal(s, a):
        i = int(np.clip(np.searchsorted(s.S, a) - 1, 0, len(s.S) - 2)); n = s.N[i] + s.N[i + 1]
        return np.array([*(n / np.linalg.norm(n)), 0.0])

    def tangent(s, a):
        i = int(np.clip(np.searchsorted(s.S, a) - 1, 0, len(s.S) - 2)); return np.array([*s.T[i], 0.0])

    def cuts(s, a, b):
        """a, b and every path vertex between them (so a piece of wall follows the curve)"""
        return [a] + [float(x) for x in s.S if a + 1e-6 < x < b - 1e-6] + [b]


def oface(mb, q, m, out, uv=None):
    q = [np.array(p, float) for p in q]
    n = np.cross(q[1] - q[0], q[2] - q[0])
    if np.linalg.norm(n) < 1e-12 and len(q) > 3:
        n = np.cross(q[2] - q[0], q[3] - q[0])
    if np.dot(n, out) < 0:
        q = q[::-1]; uv = uv[::-1] if uv else None
    mb.face([tuple(p) for p in q], m, uv=uv)


def tile(m):
    from mb import TILE
    return TILE.get(m, (1.0, 1.0))


def panel(mb, W, a, b, z0, z1, out, m, facing=1.0):
    """A wall piece in the wall's plane (out m off the line) from s a..b, z z0..z1, UVs in metres/tile."""
    tu, tv = tile(m); ss = W.cuts(a, b)
    for s0, s1 in zip(ss, ss[1:]):
        nrm = W.normal(0.5 * (s0 + s1)) * facing
        oface(mb, [W.p3(s0, z0, out), W.p3(s1, z0, out), W.p3(s1, z1, out), W.p3(s0, z1, out)], m, nrm,
              [(s0 / tu, z0 / tv), (s1 / tu, z0 / tv), (s1 / tu, z1 / tv), (s0 / tu, z1 / tv)])


def hface(mb, W, a, b, z, o0, o1, m, up=True):
    """A horizontal strip at height z from o0 to o1 off the wall line (a sill, a ledge top, a soffit)."""
    tu, tv = tile(m); ss = W.cuts(a, b); nz = np.array([0, 0, 1.0 if up else -1.0])
    for s0, s1 in zip(ss, ss[1:]):
        oface(mb, [W.p3(s0, z, o0), W.p3(s1, z, o0), W.p3(s1, z, o1), W.p3(s0, z, o1)], m, nz,
              [(s0 / tu, o0 / tv), (s1 / tu, o0 / tv), (s1 / tu, o1 / tv), (s0 / tu, o1 / tv)])


def sface(mb, W, a, z0, z1, o0, o1, m, sign):
    """An end face across the wall at s = a (sign +1 faces increasing s)."""
    oface(mb, [W.p3(a, z0, o0), W.p3(a, z0, o1), W.p3(a, z1, o1), W.p3(a, z1, o0)], m, W.tangent(a) * sign,
          [(o0, z0), (o1, z0), (o1, z1), (o0, z1)])


def block(mb, W, a, b, z0, z1, o0, o1, m, top=True, bottom=True, ends=True):
    """Something standing proud of the wall, o0..o1 out, between s a..b and z z0..z1."""
    panel(mb, W, a, b, z0, z1, o1, m)
    if top: hface(mb, W, a, b, z1, o0, o1, m, True)
    if bottom and z0 > 0.01: hface(mb, W, a, b, z0, o0, o1, m, False)
    if ends:
        sface(mb, W, a, z0, z1, o0, o1, m, -1); sface(mb, W, b, z0, z1, o0, o1, m, 1)


def wall(mb, W, a, b, z0, z1, m, holes, ztop=None):
    """The wall line from s a..b and z z0..z1 (z1 may be a function of s), with rectangular holes
    [(s0, s1, h0, h1)] left open. Columns break at every hole edge and path vertex."""
    xs = set(W.cuts(a, b))
    for h in holes:
        xs |= {min(max(h[0], a), b), min(max(h[1], a), b)}
    xs = sorted(xs)
    tu, tv = tile(m)
    for s0, s1 in zip(xs, xs[1:]):
        if s1 - s0 < 1e-4:
            continue
        mid = 0.5 * (s0 + s1); zs = [z0]
        for h in holes:
            if h[0] <= mid <= h[1]:
                zs += [h[2], h[3]]
        top = ztop(mid) if ztop else z1
        zs = sorted(zs) + [top]
        nrm = W.normal(mid)
        for k in range(0, len(zs) - 1, 2):
            if zs[k + 1] > zs[k] + 1e-3:
                za, zb = zs[k], zs[k + 1]
                oface(mb, [W.p3(s0, za), W.p3(s1, za), W.p3(s1, zb), W.p3(s0, zb)], m, nrm,
                      [(s0 / tu, za / tv), (s1 / tu, za / tv), (s1 / tu, zb / tv), (s0 / tu, zb / tv)])


def opening(mb, W, a, b, z0, z1, d, reveal, fill, mull=0.0, mull_m='frame_alu', sill='sill', transom=None):
    """The reveals, sill and head of a hole cut d m into the wall, and what fills it at the back:
    'glass' (a pane with mullions every `mull` m standing 6 cm proud of it) or 'louvre' (a dark plenum
    behind blades 0.15 m apart, each tipped down and out)."""
    if a > 0.01: sface(mb, W, a, z0, z1, -d, 0.0, reveal, 1)
    if b < W.L - 0.01: sface(mb, W, b, z0, z1, -d, 0.0, reveal, -1)
    hface(mb, W, a, b, z1, -d, 0.0, reveal, False)                    # head
    hface(mb, W, a, b, z0, -d, 0.0, sill, True)                      # sill
    if z0 > 0.05:
        panel(mb, W, a, b, z0 - 0.05, z0, 0.04, sill)                 # sill nose
        hface(mb, W, a, b, z0, 0.0, 0.04, sill, True)
    if fill == 'louvre':
        panel(mb, W, a, b, z0, z1, -d, 'plenum')
        n = max(1, int((z1 - z0 - 0.04) / 0.15))
        for k in range(n):
            zt = z1 - 0.04 - k * (z1 - z0 - 0.04) / n; zb_ = zt - 0.12
            ss = W.cuts(a, b)
            for s0, s1 in zip(ss, ss[1:]):
                nrm = W.normal(0.5 * (s0 + s1))
                oface(mb, [W.p3(s0, zt, -d + 0.06), W.p3(s1, zt, -d + 0.06), W.p3(s1, zb_, -0.06), W.p3(s0, zb_, -0.06)],
                      'louvre', nrm + np.array([0, 0, 0.8]))
        return
    panel(mb, W, a, b, z0, z1, -d, fill)
    if mull > 0:
        n = max(1, int(round((b - a) / mull)))
        for k in range(1, n):
            x = a + (b - a) * k / n
            block(mb, W, x - 0.04, x + 0.04, z0, z1, -d, -d + 0.07, mull_m, top=False, bottom=False)
    if transom:
        for zt in transom:
            block(mb, W, a, b, zt - 0.04, zt + 0.04, -d, -d + 0.07, mull_m, ends=False)


def bays(L, bay):
    n = max(1, int(round(L / bay))); w = L / n
    return [(k * w, (k + 1) * w) for k in range(n)]


# ---------------- the wall kinds ----------------
def nw_back(mb, W, H):
    """North-west stand back (aerial4, a 2024 close photo): pale grey render, a maroon brick pier every 6 m
    standing 0.3 m proud the full height, and in each bay a louvred vent high up and a window band below."""
    holes, ops = [], []
    for a, b in bays(W.L, 6.0):
        holes.append((a + 1.6, a + 5.4, H - 1.1, H - 0.5)); ops.append(('louvre', holes[-1]))
        if H > 6.5:
            holes.append((a + 1.6, a + 5.4, H - 4.7, H - 4.1)); ops.append(('glass', holes[-1]))
    wall(mb, W, 0, W.L, 0.0, H, 'render_grey', holes)
    for kind, (a, b, z0, z1) in ops:
        opening(mb, W, a, b, z0, z1, 0.22, 'render_grey', 'glass_dark' if kind == 'glass' else 'louvre',
                mull=1.25 if kind == 'glass' else 0.0)
    for a, b in bays(W.L, 6.0):
        block(mb, W, a, a + 1.0, 0.0, H + 0.15, 0.0, 0.3, 'brick_red')
    block(mb, W, 0, W.L, H - 0.05, H + 0.15, 0.0, 0.12, 'paint_white', ends=False)   # capping


def lattice_back(mb, W, H):
    """Northern Stand back (aerial4): teal ribbed cladding, and under the roof's rear edge a 1.6 m band of
    pale grey sheet standing 0.12 m proud with a drip at its foot. The white frame in front is build.bracing."""
    panel(mb, W, 0, W.L, 0.0, H - 1.6, 0.0, 'clad_teal')
    block(mb, W, 0, W.L, H - 1.6, H, 0.0, 0.12, 'clad_grey')
    block(mb, W, 0, W.L, H - 1.68, H - 1.6, 0.0, 0.16, 'paint_white', ends=False)


def es_back(mb, W, H):
    """East-south stand back (drone5, Google Earth 2026): pale ribbed sheet cladding, and in each 6 m bay
    of each 3.6 m floor (counted down from the top) a louvre panel 4 m wide and 0.7 m tall."""
    holes = []
    for a, b in bays(W.L, 6.0):
        zt = H
        while zt - 1.3 > 0.4:
            holes.append((a + 1.0, a + 5.0, zt - 1.3, zt - 0.6)); zt -= 3.6
    wall(mb, W, 0, W.L, 0.0, H, 'clad_pale', holes)
    for a, b, z0, z1 in holes:
        opening(mb, W, a, b, z0, z1, 0.18, 'clad_pale', 'louvre')
    block(mb, W, 0, W.L, H - 0.05, H + 0.1, 0.0, 0.1, 'paint_white', ends=False)


def gunns_back(mb, W, H):
    """Gunns Stand back (Google Earth 2026 l045): blue-grey panels 1.5 x 1.2 m and, on each 3.6 m floor,
    a window strip 0.8 m tall from 0.4 to 5.6 m along each 6 m bay, mullions every 1.3 m, a maroon base band."""
    holes = []
    for a, b in bays(W.L, 6.0):
        zt = H
        while zt - 2.2 > 1.2:
            holes.append((a + 0.4, a + 5.6, zt - 2.2, zt - 1.4)); zt -= 3.6
    wall(mb, W, 0, W.L, 0.6, H, 'panel_gunns', holes)
    for a, b, z0, z1 in holes:
        opening(mb, W, a, b, z0, z1, 0.2, 'panel_gunns', 'glass_dark', mull=1.3)
    block(mb, W, 0, W.L, 0.0, 0.6, -0.05, 0.08, 'steel_maroon', ends=False)
    block(mb, W, 0, W.L, H - 0.05, H + 0.12, 0.0, 0.1, 'paint_white', ends=False)


def cw_wall(mb, W, H, a=0.0, b=None):
    """Old Centre West (2024-25 photos), full 12 m: white fascia, the sign band standing proud, the tall
    function level glazed 1.2 m back behind white posts every 6 m with mullions every 1.5 m, then grey render
    with a window band 2.6 m above the ground."""
    b = W.L if b is None else b
    k = H / 12.0                                            # the plan is drawn for 12 m; lower walls scale
    g0, g1 = H - 7.0 * k, H - 3.0 * k
    w0, w1 = H - 9.4 * k, H - 8.4 * k
    wall(mb, W, a, b, 0.0, H, 'render_white', [(a, b, g0, g1), (a + 0.6, b - 0.6, w0, w1)])
    opening(mb, W, a, b, g0, g1, 1.2, 'render_white', 'glass_dark', mull=1.5)
    hface(mb, W, a, b, g0 + 1.0, -1.2, -0.25, 'paint_white', True)                 # balustrade top rail behind
    for x0, x1 in bays(b - a, 6.0):
        block(mb, W, a + x0 - 0.2 if x0 > 0 else a, a + x0 + 0.2 if x0 > 0 else a + 0.4, g0, g1, -1.2, -0.1, 'paint_white',
              top=False, bottom=False)
    opening(mb, W, a + 0.6, b - 0.6, w0, w1, 0.2, 'render_white', 'glass_dark', mull=1.5)
    block(mb, W, a, b, H - 3.0 * k, H - 0.5 * k, 0.0, 0.1, 'panel_light', ends=True)  # the sign band
    block(mb, W, a, b, H - 0.5 * k, H, 0.0, 0.18, 'paint_white')                       # fascia


def sw_back(mb, W, H):
    """South-west corner building (Centre West photo): white render, a window 1.2 x 0.9 m in each 3 m bay
    on each 2.8 m floor, set 0.25 m in."""
    holes = []
    for a, b in bays(W.L, 3.0):
        for fl in (1.3, 4.1, 6.9):
            if H - fl - 0.9 > 0.8:
                holes.append((a + 0.9, a + 2.1, H - fl - 0.9, H - fl))
    wall(mb, W, 0, W.L, 0.0, H, 'render_white', holes)
    for a, b, z0, z1 in holes:
        opening(mb, W, a, b, z0, z1, 0.25, 'render_white', 'glass_dark', mull=0.6)
    block(mb, W, 0, W.L, H - 0.4, H, 0.0, 0.1, 'paint_white', ends=False)


def pav_wall(mb, W, H):
    """Scoreboard-corner pavilions (aerial4): white render, a glazed band from 1.0 to 2.6 m below the top
    set 0.2 m in with a mullion every 1.5 m, a grey plinth."""
    z0, z1 = max(0.4, H - 2.6), H - 1.0
    wall(mb, W, 0, W.L, 0.5, H, 'render_white', [(0.5, W.L - 0.5, z0, z1)])
    opening(mb, W, 0.5, W.L - 0.5, z0, z1, 0.2, 'render_white', 'glass_dark', mull=1.5)
    block(mb, W, 0, W.L, 0.0, 0.5, -0.02, 0.06, 'conc_wall', ends=False)


def box_front(mb, W, z0, z1):
    """Gunns Stand corporate-box front (the grandstand photo): tinted glass behind white mullions every
    1.5 m, a white sill band at the foot and a white head band at the top, each standing proud."""
    panel(mb, W, 0, W.L, z0 + 0.7, z1 - 0.3, -0.15, 'glass_dark')
    n = max(1, int(round(W.L / 1.5)))
    for k in range(n + 1):
        x = W.L * k / n
        block(mb, W, max(0.0, x - 0.06), min(W.L, x + 0.06), z0 + 0.7, z1 - 0.3, -0.15, 0.0, 'paint_white',
              top=False, bottom=False)
    block(mb, W, 0, W.L, z0, z0 + 0.7, -0.15, 0.05, 'paint_white', ends=False)
    block(mb, W, 0, W.L, z1 - 0.3, z1, -0.15, 0.05, 'paint_white', ends=False)


KINDS = {'facade_nw': nw_back, 'facade_lattice': lattice_back, 'facade_es': es_back, 'facade_gunns': gunns_back,
         'facade_cw': cw_wall, 'facade_sw': sw_back, 'facade_pav': pav_wall}
