# ---- south-west corner buildings (photo g49 x 262-700, y 725-1000): measured on pixel grids, unprojected through camB
PT = mat('paletile', W1, 0.8, 'paletile.png'); GF = mat('gatefront', W1, 0.8, 'gatefront.png')
NW = mat('navywall', W1, 0.7, 'navywall.png'); N7F = mat('n7front', W1, 0.7, 'n7front.png'); N7R = mat('n7roof', W1, 0.8, 'n7roof.png')
WR = mat('whiterender', W1, 0.8, 'whiterender.png'); DD = mat('deckdots', W1, 0.9, 'deckdots.png'); SK = mat('skylight', W1, 0.4, 'skylight.png')
BOX.update({PT: 4.8, NW: 3.0, WR: 3.0, DD: 6.0, GF: 46.0, N7F: 9.7, N7R: 10.0, SK: 12.0})
def _ccw(p):
    s = sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))
    return p if s > 0 else p[::-1]
def _ang(p): return math.atan2(p[1] - cy, p[0] - cx)
def _fac(a, d=0.5): return P(a, rF(a) - d, 0)[:2]
def _out(p, d=0.5):   # keep a roof point outside the facade line
    a = _ang(p); r = math.hypot(p[0] - cx, p[1] - cy); r = max(r, rF(a) - d); return (cx + r * math.cos(a), cy + r * math.sin(a))
def _arc(a0, a1, n=12, d=0.5): return [_fac(a0 + (a1 - a0) * k / n, d) for k in range(n + 1)]
def _skin(p0, p1, z00, z01, z10, z11, m, u0, u1, U, V, off=0.03):
    # one outward face from p0 to p1; z0x bottoms, z1x tops; uv = (u / U, z / V)
    nx, ny = p1[1] - p0[1], -(p1[0] - p0[0]); L = math.hypot(nx, ny); nx, ny = nx / L, ny / L
    mx, my = (p0[0] + p1[0]) / 2 - cx, (p0[1] + p1[1]) / 2 - cy
    if nx * mx + ny * my < 0: nx, ny = -nx, -ny
    q0 = (p0[0] + nx * off, p0[1] + ny * off); q1 = (p1[0] + nx * off, p1[1] + ny * off)
    vs = [(*q0, z00), (*q1, z01), (*q1, z11), (*q0, z10)]; uvs = [(u0 / U, z00 / V), (u1 / U, z01 / V), (u1 / U, z11 / V), (u0 / U, z10 / V)]
    e = (q1[0] - q0[0], q1[1] - q0[1]); n_ = (e[1], -e[0])          # (edge x up) for this vertex order
    if n_[0] * nx + n_[1] * ny < 0: vs, uvs = vs[::-1], uvs[::-1]
    face(vs, m, uvs)
def _slab(q, hs, m, capm, uw, vm):   # 4-sided block with a sloped top (heights per corner)
    vb = [bm.verts.new((x, y, 0)) for x, y in q]; vt = [bm.verts.new((x, y, h)) for (x, y), h in zip(q, hs)]
    L = 0.0
    for k in range(4):
        j = (k + 1) % 4; s = math.dist(q[k], q[j])
        f = bm.faces.new((vb[k], vb[j], vt[j], vt[k])); f.material_index = m
        for l, t in zip(f.loops, [(L / uw, 0), ((L + s) / uw, 0), ((L + s) / uw, hs[j] / vm), (L / uw, hs[k] / vm)]): l[uv].uv = t
        L += s
    f = bm.faces.new(vt); f.material_index = capm; f = bm.faces.new(vb[::-1]); f.material_index = capm

# pale gate block on Vulture St: front at the footpath, back on the facade. Heights from vertical edges:
# photo (477,927)-(479,995) 23.6 m, (567,925) 24.7 m -> G1 24 m; G2 21 m (top y ~935); G3 slopes 17.3 m (600,947) -> 13.4 m (687,958)
_F = [(111.1, 93.3), (93.1, 98.2), (86.1, 100.0), (67.1, 104.6)]
_Bk = [_fac(_ang(p), 0.3) for p in _F]
_L = [math.dist(_F[i], _F[i + 1]) for i in range(3)]; _U = [0.0, _L[0], _L[0] + _L[1], sum(_L)]
prism(_ccw([_F[0], _F[1], _Bk[1], _Bk[0]]), 0, 24.0, PT, True, 4, 4.8, 4.8, RD)
prism(_ccw([_F[1], _F[2], _Bk[2], _Bk[1]]), 0, 21.0, PT, True, 4, 4.8, 4.8, RD)
_q = _ccw([_F[2], _F[3], _Bk[3], _Bk[2]]); _h = {_F[2]: 17.3, _F[3]: 13.4, _Bk[3]: 13.4, _Bk[2]: 17.3}
_slab(_q, [_h[p] for p in _q], PT, RD, 4.8, 4.8)
_skin(_F[0], _F[1], 0, 0, 24.0, 24.0, GF, _U[0], _U[1], 46.0, 24.0)
_skin(_F[1], _F[2], 0, 0, 21.0, 21.0, GF, _U[1], _U[2], 46.0, 24.0)
_skin(_F[2], _F[3], 0, 0, 17.3, 13.4, GF, _U[2], _U[3], 46.0, 24.0)

# navy gate-7 block: roof corners (360,940) (381,966) (420,944), front edge (381,966)-(384,990) -> 8.5 m
_NL, _NF, _NR = (134.7, 78.7), (131.3, 86.6), (122.3, 83.1); _NB = (_NL[0] + _NR[0] - _NF[0], _NL[1] + _NR[1] - _NF[1])
prism(_ccw([_NL, _NF, _NR, _NB]), 0, 8.5, NW, True, 2, 3.0, 3.0, NW)
_skin(_NF, _NR, 0, 0, 8.5, 8.5, N7F, 0, 9.7, 9.7, 8.5)
_rq = [_NB, _NL, _NF, _NR]; _rq = _rq if sum(_rq[i][0] * _rq[(i + 1) % 4][1] - _rq[(i + 1) % 4][0] * _rq[i][1] for i in range(4)) > 0 else None
face([(x, y, 8.53) for x, y in (_rq or [_NB, _NR, _NF, _NL])], N7R, [(0, 0), (1, 0), (1, 1), (0, 1)])

# white building with roof plant, 15 m (its wall rises 18 px above the navy roof): outline unprojected at 15 m
_W = [(142.3, 18.2), (147.7, 32.3), (151.3, 56.8), (151.2, 62.6), (149.05, 70.21), (142.03, 77.64), _NL, _NB, _NR, (123.36, 86.28), (115.99, 87.35)]
_W += _arc(_ang(_W[-1]), _ang(_W[0]), 16)
prism(_ccw(_W), 0, 15.0, WR, True, 3, 3.0, 3.0, RD)
face([(x, y, 15.05) for x, y in _ccw([(144.11, 38.69), (134.6, 40.28), (131.54, 49.73), (138.57, 55.95), (145.16, 52.1)])], DD)        # dark deck, photo 292-355 x 790-846
face([(x, y, 15.05) for x, y in _ccw([_out(p) for p in [(129.01, 70.11), (121.27, 62.63), (112.69, 67.81), (115.45, 86.76), (123.36, 86.28)]])], DD)   # dark deck, photo 372-452 x 852-938
_sk = [_out(p) for p in [(138.6, 57.43), (131.64, 51.54), (121.33, 63.8), (129.04, 71.25)]]                                           # skylight lantern, photo L(326,846) T(354,820) R(408,852) B(378,885)
prism(_ccw(_sk), 15.0, 16.5, WR, True, 1, 3.0, 3.0, WR)
_sq = _sk if sum(_sk[i][0] * _sk[(i + 1) % 4][1] - _sk[(i + 1) % 4][0] * _sk[i][1] for i in range(4)) > 0 else _sk[::-1]
face([(x, y, 16.53) for x, y in _sq], SK, [(0, 0), (1, 0), (1, 1), (0, 1)])
for (px, py), r in (((138.38, 70.33), 3.3), ((142.62, 62.36), 2.4)):                                                                 # round plant screens, photo (335,895) (311,871)
    tube((px, py, 15.0), (px, py, 18.5), r, r, WR, 28)
    face([(px + (r - 0.2) * math.cos(t), py + (r - 0.2) * math.sin(t), 18.52) for t in [2 * math.pi * k / 28 for k in range(28)]], DK)
