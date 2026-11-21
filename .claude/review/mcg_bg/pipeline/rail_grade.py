"""Rail corridor ground: flat track, as in reality (coordinator OK 2026-11-20).
Each plan track gets a profile: the lowest ground within 4 m either side (the cutting floor, not the street above it),
lowest over 30 m along, averaged over 150 m along, capped so every road deck and footbridge underside clears the rail
head by 6.2 m (5.6 m wire + 0.6 m), then limited to 3 % grade by lowering only. Near-grid vertices inside the traced
corridor (rail_edges.json) or within 6 m of a track take the distance-weighted profile of the tracks around them;
everything outside is untouched."""
import numpy as np
import rail_geo

GRADE = 0.028; CLEAR = 6.2; HEAD = 0.36


def _samp(G, NE, NS, X, Y):
    fx = (np.asarray(X) + NE) / NS; fy = (np.asarray(Y) + NE) / NS
    i = np.clip(np.floor(fx).astype(int), 0, G.shape[1] - 2); j = np.clip(np.floor(fy).astype(int), 0, G.shape[0] - 2)
    ax = np.clip(fx - i, 0, 1); ay = np.clip(fy - j, 0, 1)
    return G[j, i] * (1 - ax) * (1 - ay) + G[j, i + 1] * ax * (1 - ay) + G[j + 1, i] * (1 - ax) * ay + G[j + 1, i + 1] * ax * ay


def _roll(z, w, fn):
    h = w // 2; zp = np.pad(z, h, mode='edge')
    S = np.lib.stride_tricks.sliding_window_view(zp, 2 * h + 1)
    return fn(S, axis=1)


def _inpoly(X, Y, P):
    c = np.zeros(X.shape, bool); n = len(P)
    for k in range(n):
        x1, y1 = P[k]; x2, y2 = P[(k + 1) % n]
        m = ((y1 > Y) != (y2 > Y)) & (X < (x2 - x1) * (Y - y1) / ((y2 - y1) or 1e-12) + x1)
        c ^= m
    return c


def bridge_unders(bridges, H):
    """(points Nx2 every 0.5 m, underside z, half width) for every drawn road deck and footbridge (same rules as scene.py)."""
    out = []
    for b in bridges:
        if b.get('rail'): continue
        P = np.array(b['p'], float)
        if b['w'] <= 6 and np.hypot(*np.diff(P, axis=0).T).sum() < 30: continue
        ends = H(P[[0, -1], 0], P[[0, -1], 1])
        cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))]); tot = max(cum[-1], 1e-6)
        d = np.arange(0, tot + 0.25, 0.5); S = np.stack([np.interp(d, cum, P[:, 0]), np.interp(d, cum, P[:, 1])], 1)
        if b['w'] <= 6:
            if float(ends.max()) - float(H(S[:, 0], S[:, 1]).min()) < 2.0: continue
            u = float(ends[0]) + 0.3 + (float(ends[1]) - float(ends[0])) * d / tot - 1.6
        else:
            u = np.full(len(d), float(ends.max()) + 0.3 - 1.4)
        out.append((S, u, b['w'] / 2.0))
    return out


def rail_bridge_pts(bridges):
    S = []
    for b in bridges:
        if not b.get('rail'): continue
        P = np.array(b['p'], float); S.append(rail_geo.densify(P, 1.0))
    return np.concatenate(S) if S else np.zeros((0, 2))


def profiles(tracks, near, NE, NS, bridges):
    H = lambda X, Y: _samp(near, NE, NS, X, Y)
    unders = bridge_unders(bridges, H); RB = rail_bridge_pts(bridges); lim = NE - NS
    res = []
    for t in tracks:
        Q = rail_geo.densify(np.array(t, float), 1.0)
        if len(Q) < 3: continue
        T = rail_geo.tangents(Q); N = np.stack([-T[:, 1], T[:, 0]], 1)
        z = np.min([H(Q[:, 0] + N[:, 0] * o, Q[:, 1] + N[:, 1] * o) for o in (-4, -2, 0, 2, 4)], 0)
        if len(RB):   # on a rail bridge the ground below is the road, not the bed: interpolate across the span
            onb = np.array([np.min(np.hypot(*(RB - p).T)) < 4 for p in Q[:: 1]])
            if onb.any() and (~onb).sum() > 1:
                k = np.arange(len(z)); z = np.where(onb, np.interp(k, k[~onb], z[~onb]), z)
        z = _roll(_roll(z, 31, np.min), 151, np.mean)
        cap = np.full(len(z), np.inf)
        for S, u, hw in unders:
            D = np.hypot(Q[:, None, 0] - S[None, :, 0], Q[:, None, 1] - S[None, :, 1])
            j = np.argmin(D, 1); hit = D[np.arange(len(Q)), j] < hw + 3
            cap[hit] = np.minimum(cap[hit], u[j[hit]] - CLEAR - HEAD - 0.05)
        z = np.minimum(z, cap)
        for _ in range(2):   # 3 % grade, lowering only (deeper cut, never a hump)
            for i in range(1, len(z)): z[i] = min(z[i], z[i - 1] + GRADE)
            for i in range(len(z) - 2, -1, -1): z[i] = min(z[i], z[i + 1] + GRADE)
        inside = (np.abs(Q[:, 0]) < lim) & (np.abs(Q[:, 1]) < lim)
        res.append((Q, z, inside))
    # tracks that meet (turnouts, parallel beds within 4.5 m) share one bed: take the lower level where they are close,
    # fading back to each track's own profile, then re-limit the grade; repeat until every junction agrees
    P = np.concatenate([Q for Q, z, _ in res]); own = np.concatenate([np.full(len(Q), k) for k, (Q, z, _) in enumerate(res)])
    off = np.cumsum([0] + [len(Q) for Q, z, _ in res])
    key = lambda X: (np.floor(X[:, 0] / 4.5).astype(np.int64) * 100003 + np.floor(X[:, 1] / 4.5).astype(np.int64))
    order = np.argsort(key(P)); ks = key(P)[order]
    for _ in range(6):
        Z = np.concatenate([z for Q, z, _ in res]); zt = Z.copy()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                kk = key(P + np.array([dx * 4.5, dy * 4.5])); lo = np.searchsorted(ks, kk, 'left'); hi = np.searchsorted(ks, kk, 'right')
                mx = int((hi - lo).max()) if len(lo) else 0
                for c in range(mx):
                    has = lo + c < hi; q = order[np.minimum(lo + c, len(order) - 1)]
                    ok = has & (own[q] != own) & (np.hypot(*(P[q] - P).T) < 4.5) & (Z[q] > Z - 4.0)   # a drop over 4 m is a grade separation, kept
                    zt[ok] = np.minimum(zt[ok], Z[q[ok]])
        moved = 0
        for k, (Q, z, ins) in enumerate(res):
            zn = zt[off[k]:off[k + 1]]; moved += int((zn < z - 1e-3).sum()); z = zn.copy()
            for _ in range(2):
                for i in range(1, len(z)): z[i] = min(z[i], z[i - 1] + GRADE)
                for i in range(len(z) - 2, -1, -1): z[i] = min(z[i], z[i + 1] + GRADE)
            res[k] = (Q, z, ins)
        if moved == 0: break
    return res, unders


def apply(near, NE, NS, tracks, edges, bridges, R=45.0, buf=6.0):
    near = near.copy(); near0 = near.copy(); n = near.shape[0]; g = np.arange(n) * NS - NE
    prof, unders = profiles(tracks, near, NE, NS, bridges)
    sw = np.zeros_like(near); sz = np.zeros_like(near); dmin = np.full(near.shape, np.inf)
    r = int(np.ceil(R / NS))
    for Q, z, _ in prof:
        ci = np.round((Q[:, 0] + NE) / NS).astype(int); cj = np.round((Q[:, 1] + NE) / NS).astype(int)
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                ii = ci + di; jj = cj + dj; ok = (ii >= 0) & (ii < n) & (jj >= 0) & (jj < n)
                ii, jj = ii[ok], jj[ok]; d = np.hypot(g[ii] - Q[ok, 0], g[jj] - Q[ok, 1])
                m = d < R; ii, jj, d = ii[m], jj[m], d[m]; w = 1.0 / (d * d + 4.0)
                np.add.at(sw, (jj, ii), w); np.add.at(sz, (jj, ii), w * z[ok][m]); np.minimum.at(dmin, (jj, ii), d)
    X, Y = np.meshgrid(g, g)
    mask = dmin < buf
    if edges is not None and len(edges):
        E = np.asarray(edges, float); poly = np.concatenate([E[:, 0], E[::-1, 1]])
        mask |= _inpoly(X, Y, poly) & (sw > 0) & (dmin < buf)
    new = np.where(sw > 0, sz / np.maximum(sw, 1e-12), near)
    near[mask] = new[mask]
    # bridge clearance on the mesh itself: every corridor vertex under or within 8 m of a deck sits 6.2 m + rail head below it
    for S, u, hw in unders:
        lo = S.min(0) - hw - 8; hi = S.max(0) + hw + 8
        sel = (mask | ((sw > 0) & (dmin < buf + 8))) & (X > lo[0]) & (X < hi[0]) & (Y > lo[1]) & (Y < hi[1])
        if not sel.any(): continue
        P_ = np.stack([X[sel], Y[sel]], 1); D = np.hypot(P_[:, None, 0] - S[None, :, 0], P_[:, None, 1] - S[None, :, 1])
        j = np.argmin(D, 1); hit = D[np.arange(len(P_)), j] < hw + 8
        v = near[sel]; v[hit] = np.minimum(v[hit], u[j[hit]] - CLEAR - HEAD - 0.1); near[sel] = v
    # grid grade limit inside the corridor: neighbouring tracks' profiles blend, so clamp the mesh itself to 2 % between
    # corridor vertices (lowering only, 8 neighbours), which keeps any track laid across it at 3 % or less
    Zm = np.where(mask, near, np.inf); s = 0.018 * NS
    for _ in range(400):
        P = np.pad(Zm, 1, constant_values=np.inf); best = Zm.copy()
        for dj, di, f in ((0, 1, 1), (0, -1, 1), (1, 0, 1), (-1, 0, 1), (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)):
            best = np.minimum(best, P[1 + dj:1 + dj + n, 1 + di:1 + di + n] + s * f)
        if np.array_equal(best, Zm): break
        Zm = best
    near[mask] = Zm[mask]
    # only the track formation is graded (coordinator 2026-11-21): roads and banks outside it stay on Vicmap
    return near, int(mask.sum()), prof, unders
