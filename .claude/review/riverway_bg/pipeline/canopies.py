# Carport canopy geometry from classified 1 m aerial cells (carport_cls.py -> carports_cls.json [x, y, lift, cls, group]).
# Shapes copied from Google Street View, image capture Sept 2022:
#   1 shade sails: square twisted fabric sails (two opposite corners high), ~11 m, on grey steel posts
#   2 solar rows: flat solar panel roof on white steel posts and beams
#   3 bus-interchange shelters: curved (barrel-vault) light grey metal roof on white posts
# Returns a list of (name, V, F, rgb-per-face 0..255) parts; the caller makes the objects and materials.
import numpy as np

SAIL = 11.0          # sail square, m (aerial: ~11 m per sail)
SAIL_GAP = 0.6       # gap between neighbouring sails
SAIL_LOW, SAIL_HIGH = 3.6, 5.4   # low / high corner height above ground
SOLAR_Z = 3.6        # solar roof height
POST = 0.28          # post width
ARCH_Z, ARCH_RISE = 3.0, 1.4

C_SAIL = (214, 192, 156); C_SAILPOST = (150, 152, 154)
C_SOLAR = (62, 66, 78); C_WHITE = (232, 232, 228)
C_SHELTER = (178, 180, 178)


def _axes(P):
    c = P.mean(0); w, v = np.linalg.eigh(np.cov((P - c).T))
    a = v[:, np.argmax(w)]; return c, a, np.array([-a[1], a[0]])


class _M:
    def __init__(s): s.V, s.F, s.C = [], [], []
    def quad(s, ps, col):
        i = len(s.V); s.V += [tuple(p) for p in ps]; s.F.append((i, i + 1, i + 2, i + 3)); s.C.append(col)
    def box(s, x, y, z0, z1, hx, hy, col, a=(1, 0), b=(0, 1)):
        a, b = np.array(a, float), np.array(b, float); c = np.array([x, y])
        P = [c - a * hx - b * hy, c + a * hx - b * hy, c + a * hx + b * hy, c - a * hx + b * hy]
        for k in range(4):
            p, q = P[k], P[(k + 1) % 4]
            s.quad([(*p, z0), (*q, z0), (*q, z1), (*p, z1)], col)
        s.quad([(*P[0], z1), (*P[1], z1), (*P[2], z1), (*P[3], z1)], col)


def build(CP, height, sails=None):
    parts = []
    sail, frame, solar, shel = _M(), _M(), _M(), _M()
    for g in np.unique(CP[:, 4]).astype(int):
        S = CP[CP[:, 4] == g]; k = int(S[0, 3]); P = S[:, :2]
        occ = set(map(tuple, np.floor(P).astype(int)))
        inside = lambda x, y: (int(np.floor(x)), int(np.floor(y))) in occ
        c, a, b = _axes(P); u = (P - c) @ a; v = (P - c) @ b
        if k == 1:   # sails: one per lattice square fitted to the aerial (sail_lattice.py -> sails.json), twisted fabric on 4 posts
            for si, sd in enumerate([q for q in (sails or []) if q['g'] == g]):
                Q = np.array(sd['corners'], float); flip = si % 2
                n = 6; G = np.linspace(0, 1, n + 1)
                def pt(s_, r_):
                    xy = (1 - s_) * (1 - r_) * Q[0] + s_ * (1 - r_) * Q[1] + s_ * r_ * Q[2] + (1 - s_) * r_ * Q[3]
                    tw = (2 * s_ - 1) * (2 * r_ - 1) * (-1 if flip else 1)   # two opposite corners high, as in Street View
                    return (*xy, float(height(*xy)) + (SAIL_LOW + SAIL_HIGH) / 2 + tw * (SAIL_HIGH - SAIL_LOW) / 2)
                for p in range(n):
                    for q in range(n):
                        sail.quad([pt(G[p], G[q]), pt(G[p + 1], G[q]), pt(G[p + 1], G[q + 1]), pt(G[p], G[q + 1])], C_SAIL)
                for s_, r_ in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    x, y, z = pt(s_, r_); frame.box(x, y, float(height(x, y)), z + 0.1, POST / 2, POST / 2, C_SAILPOST)
        elif k == 2:   # solar: flat roof over the measured cells, white posts every 7.5 m in two lines, white beams under
            for x, y in P:
                z = float(height(x, y)) + SOLAR_Z
                solar.quad([(x - .5, y - .5, z), (x + .5, y - .5, z), (x + .5, y + .5, z), (x - .5, y + .5, z)], C_SOLAR)
            w0, w1 = np.percentile(v, 2), np.percentile(v, 98); L0, L1 = u.min(), u.max()
            for vv in (w0 + 0.3 * (w1 - w0), w0 + 0.7 * (w1 - w0)):
                m = (L0 + L1) / 2; xy = c + a * m + b * vv
                frame.box(*xy, float(height(*xy)) + SOLAR_Z - 0.45, float(height(*xy)) + SOLAR_Z - 0.05, (L1 - L0) / 2, 0.15, C_WHITE, a, b)
                for uu in np.arange(L0 + 2, L1 - 1, 7.5):
                    xy = c + a * uu + b * vv
                    if inside(*xy): frame.box(*xy, float(height(*xy)), float(height(*xy)) + SOLAR_Z - 0.4, POST / 2, POST / 2, C_WHITE)
        elif k == 3:   # shelters: barrel vault across the short axis, posts every 6 m both sides
            L0, L1 = u.min() - .5, u.max() + .5; w0, w1 = np.percentile(v, 2) - .5, np.percentile(v, 98) + .5
            us = np.arange(L0, L1 + 1e-6, 1.0); vs = np.linspace(w0, w1, 13)
            def pv(uu, vv):
                xy = c + a * uu + b * vv; t = 2 * (vv - (w0 + w1) / 2) / (w1 - w0)
                return (*xy, float(height(*xy)) + ARCH_Z + ARCH_RISE * (1 - t * t))
            for p in range(len(us) - 1):
                for q in range(len(vs) - 1):
                    shel.quad([pv(us[p], vs[q]), pv(us[p + 1], vs[q]), pv(us[p + 1], vs[q + 1]), pv(us[p], vs[q + 1])], C_SHELTER)
            for uu in np.arange(L0 + 1, L1, 6.0):
                for vv in (w0 + .4, w1 - .4):
                    xy = c + a * uu + b * vv; frame.box(*xy, float(height(*xy)), ARCH_Z + float(height(*xy)), POST / 2, POST / 2, C_WHITE)
    for nm, m in (('bg_sails', sail), ('bg_carport_frames', frame), ('bg_solar_roofs', solar), ('bg_bus_shelters', shel)):
        if m.F: parts.append((nm, np.array(m.V), m.F, np.array(m.C, float)))
    return parts


if __name__ == '__main__':   # offline count check
    import json, sys
    CP = np.array(json.load(open(sys.argv[1])), float)
    for nm, V, F, C in build(CP, lambda x, y: 0.0): print(nm, len(F), 'faces')
    S = CP[CP[:, 3] == 1]
    n = sum(len(F) for nm, V, F, C in build(S, lambda x, y: 0.0) if nm == 'bg_sails') // 36
    print('sails', n)
