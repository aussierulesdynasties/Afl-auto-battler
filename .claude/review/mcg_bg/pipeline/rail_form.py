# Rail formation mesh (coordinator 2026-11-21): the track bed is its own fine mesh (0.75 m) on the graded profile, so
# the 7.5 m Vicmap grid stays untouched outside it. Each side of the bed meets the street by what is really there,
# per region in prep/formation_edges.json: 'wall' (vertical retaining wall), 'grass' (grassed batter 1:1.5) or
# 'ballast' (ballast batter 1:1.5); default grass. Each region carries its source (aerial tile or photo file).
import numpy as np

HALF = 3.3      # bed half-width from a track centre: 1.6 m gauge, 2.6 m sleeper, ballast shoulder to ~3.3 m
W = 20.0        # corridor reach beyond the centre line that the fine mesh replaces
SLOPE = {'grass': 1 / 1.5, 'ballast': 1 / 1.5, 'wall': 50.0}
KIND_ID = {'grass': 0, 'ballast': 1, 'wall': 2}


def _inpoly(x, y, P):
    P = np.asarray(P, float); ins = np.zeros(x.shape, bool); j = len(P) - 1
    for i in range(len(P)):
        xi, yi = P[i]; xj, yj = P[j]
        c = ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / ((yj - yi) + 1e-12) + xi)
        ins ^= c; j = i
    return ins


def _bil(Z, NE, NS, X, Y):
    fx = (X + NE) / NS; fy = (Y + NE) / NS
    i = np.clip(np.floor(fx).astype(int), 0, Z.shape[1] - 2); j = np.clip(np.floor(fy).astype(int), 0, Z.shape[0] - 2)
    ax = fx - i; ay = fy - j
    return Z[j, i] * (1 - ax) * (1 - ay) + Z[j, i + 1] * ax * (1 - ay) + Z[j + 1, i] * (1 - ax) * ay + Z[j + 1, i + 1] * ax * ay


def build(near, NE, NS, prof, regions=None, sub=10):
    """near: the Vicmap grid (bridge-under lowering applied). prof: rail_grade.profiles output.
    Returns dict(cells=bool[n-1,n-1] coarse cells replaced, V, F, kind per face, zf(X,Y) sampler, Zf grid)."""
    n = near.shape[0]; h = NS / sub; m = (n - 1) * sub + 1
    pts = np.concatenate([Q for Q, z, ins in prof]); zs = np.concatenate([z for Q, z, ins in prof])
    # coarse cells within reach of a track
    ci = np.floor((pts[:, 0] + NE) / NS).astype(int); cj = np.floor((pts[:, 1] + NE) / NS).astype(int)
    cells = np.zeros((n - 1, n - 1), bool); r = int(np.ceil(W / NS))
    for di in range(-r, r + 1):
        for dj in range(-r, r + 1):
            ii = ci + di; jj = cj + dj; ok = (ii >= 0) & (ii < n - 1) & (jj >= 0) & (jj < n - 1)
            cx = (ii[ok] + 0.5) * NS - NE; cy = (jj[ok] + 0.5) * NS - NE
            near_ = np.hypot(cx - pts[ok, 0], cy - pts[ok, 1]) < W - NS * 0.7
            cells[jj[ok][near_], ii[ok][near_]] = True
    # fine vertices: every fine node inside a replaced cell
    used = np.zeros((m, m), bool)
    J, I = np.nonzero(cells)
    for a in range(sub + 1):
        for b in range(sub + 1):
            used[J * sub + a, I * sub + b] = True
    fj, fi = np.nonzero(used); X = fi * h - NE; Y = fj * h - NE
    # nearest-track distance and IDW formation height (sharp weights so each bed carries its own track's level)
    dmin = np.full(len(X), np.inf); sw = np.zeros(len(X)); sz = np.zeros(len(X))
    idx = -np.ones((m, m), int); idx[fj, fi] = np.arange(len(X))
    R = int(np.ceil(W / h))
    pi = np.round((pts[:, 0] + NE) / h).astype(int); pj = np.round((pts[:, 1] + NE) / h).astype(int)
    for di in range(-R, R + 1):
        for dj in range(-R, R + 1):
            if di * di + dj * dj > R * R: continue
            ii = pi + di; jj = pj + dj; ok = (ii >= 0) & (ii < m) & (jj >= 0) & (jj < m)
            k = idx[jj[ok], ii[ok]]; g = k >= 0; k = k[g]
            d = np.hypot(X[k] - pts[ok][g, 0], Y[k] - pts[ok][g, 1]); w = 1.0 / (d ** 6 + 0.01)
            np.minimum.at(dmin, k, d); np.add.at(sw, k, w); np.add.at(sz, k, w * zs[ok][g])
    G = _bil(near, NE, NS, X, Y)
    Fe = np.where(sw > 0, sz / np.maximum(sw, 1e-12), G)
    kind = np.zeros(len(X), int)
    for reg in regions or []:
        kind[_inpoly(X, Y, reg['poly'])] = KIND_ID[reg['kind']]
    s = np.array([SLOPE['grass'], SLOPE['ballast'], SLOPE['wall']])[kind]
    e = np.maximum(dmin - HALF, 0)
    Z = np.where(dmin <= HALF, Fe, np.clip(G, Fe - e * s, Fe + e * s))
    # rim of the replaced area meets the coarse mesh exactly
    cpad = np.pad(cells, 1)
    def cell_on(jj, ii): return cpad[jj + 1, ii + 1]
    a = fj // sub; b = fi // sub; ra = fj % sub == 0; rb = fi % sub == 0
    full = cell_on(a, b) & cell_on(a - ra.astype(int), b) & cell_on(a, b - rb.astype(int)) & cell_on(a - ra.astype(int), b - rb.astype(int))
    Z = np.where(full, Z, G)
    # faces
    F = []
    for a_ in range(sub):
        for b_ in range(sub):
            v00 = idx[J * sub + a_, I * sub + b_]; v10 = idx[J * sub + a_, I * sub + b_ + 1]
            v11 = idx[J * sub + a_ + 1, I * sub + b_ + 1]; v01 = idx[J * sub + a_ + 1, I * sub + b_]
            F.append(np.stack([v00, v10, v11, v01], 1))
    F = np.concatenate(F)
    bed = (dmin[F] <= HALF + 0.01).all(1)
    fk = np.where(bed, -1, kind[F].max(1))
    Zf = np.full((m, m), np.nan); Zf[fj, fi] = Z
    def zf(Xq, Yq):
        Xq = np.asarray(Xq, float); Yq = np.asarray(Yq, float)
        fx = (Xq + NE) / h; fy = (Yq + NE) / h
        i = np.clip(np.floor(fx).astype(int), 0, m - 2); j = np.clip(np.floor(fy).astype(int), 0, m - 2)
        ax = np.clip(fx - i, 0, 1); ay = np.clip(fy - j, 0, 1)
        q = [Zf[j, i], Zf[j, i + 1], Zf[j + 1, i], Zf[j + 1, i + 1]]
        mx = np.nanmax(np.stack(q), 0) if False else np.maximum(np.maximum(q[0], q[1]), np.maximum(q[2], q[3]))
        bl = q[0] * (1 - ax) * (1 - ay) + q[1] * ax * (1 - ay) + q[2] * (1 - ax) * ay + q[3] * ax * ay
        # inside the fine mesh take the bilinear (quads are 0.75 m, the diagonal split differs by mm); NaN = outside
        return np.where(np.isnan(bl), np.nan, bl)
    return dict(cells=cells, V=np.stack([X, Y, Z], 1), F=F, face_kind=fk, zf=zf, dmin=dmin, n_bed=int(bed.sum()))
