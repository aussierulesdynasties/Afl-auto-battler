"""Track layout from OSM rail ways (pure numpy, no Blender; checked top-down against the aerial with rail_check.py).
1. merge ways whose ends meet (< 1.5 m) on the same heading into continuous lines (no stubs)
2. densify to <= 2 m
3. drop only what the ground model covers (footprint / keep ellipse), keep every visible run longer than 4 m
4. overhead line: a portal every 55 m spanning each bundle of parallel tracks (posts 3 m outside the outer tracks),
   a single cantilever mast on lone tracks; never standing on a track."""
import numpy as np

def _unit(v):
    n = np.hypot(*v); return v / n if n > 1e-9 else v

def merge(ways, tol=1.5, cos_min=0.94):
    W = [np.array(w, float) for w in ways if len(w) > 1]
    changed = True
    while changed:
        changed = False
        ends = []   # (way, which end, point, outward heading)
        for i, w in enumerate(W):
            ends.append((i, 0, w[0], _unit(w[0] - w[1]))); ends.append((i, 1, w[-1], _unit(w[-1] - w[-2])))
        P = np.array([e[2] for e in ends]); H = np.array([e[3] for e in ends])
        best = None
        for a in range(len(ends)):
            d = np.hypot(*(P - P[a]).T); cand = np.where((d < tol) & (np.arange(len(ends)) // 2 != a // 2))[0]
            for b in cand:
                c = -float(H[a] @ H[b])   # outward headings opposite = the lines continue each other
                if c > cos_min and (best is None or c > best[0]): best = (c, a, b)
        if best:
            _, a, b = best; i, ei = ends[a][0], ends[a][1]; j, ej = ends[b][0], ends[b][1]
            A = W[i] if ei == 1 else W[i][::-1]; B = W[j] if ej == 0 else W[j][::-1]
            W[i] = np.vstack([A, B[1:]]); del W[j]; changed = True
    return W

def densify(P, step=2.0):
    Q = [P[0]]
    for p in P[1:]:
        k = max(1, int(np.ceil(np.hypot(*(p - Q[-1])) / step))); a = Q[-1]
        for t in range(1, k + 1): Q.append(a + (p - a) * t / k)
    return np.array(Q)

def visible(Q, KF=None, KE=None, min_len=4.0):
    if KF is None and not KE: return [Q]
    if KF is not None: ok = np.hypot(Q[:, 0], Q[:, 1]) > KF[((np.degrees(np.arctan2(Q[:, 1], Q[:, 0])) % 360) // 2).astype(int)] + 1.0
    else: ex, ey, ea, eb = KE; ok = np.hypot((Q[:, 0] - ex) / ea, (Q[:, 1] - ey) / eb) > 1.04
    runs = np.split(np.arange(len(Q)), np.where(np.diff(ok.astype(int)) != 0)[0] + 1)
    return [Q[r] for r in runs if ok[r[0]] and len(r) > 1 and np.hypot(*np.diff(Q[r], axis=0).T).sum() > min_len]

def smooth(Q, win=21):
    Q = densify(np.asarray(Q, float), 1.0)
    if len(Q) < win: return Q
    h = win // 2; P = np.concatenate([2 * Q[:1] - Q[h:0:-1], Q, 2 * Q[-1:] - Q[-2:-h - 2:-1]])
    k = np.ones(win) / win
    return np.stack([np.convolve(P[:, 0], k, 'valid'), np.convolve(P[:, 1], k, 'valid')], 1)

def turnouts(tracks, tol=0.6, min_len=5.0):
    """Where two tracks share a run (one OSM way drawn on top of another through a turnout), keep the longer track and
    cut the shared run out of the shorter one, so each turnout is one rail pair until the diverging track leaves at its
    switch toe. Returns the trimmed tracks and the switch-toe points (where a cut piece meets the through track)."""
    order = sorted(range(len(tracks)), key=lambda k: -len(tracks[k]))
    keep = []; toes = []
    for k in order:
        Q = tracks[k]; shared = np.zeros(len(Q), bool)
        lo, hi = Q.min(0) - 1, Q.max(0) + 1
        for K in keep:
            sel = np.all((K >= lo) & (K <= hi), 1)
            if not sel.any(): continue
            Ks = K[sel]
            for a in range(0, len(Q), 512):
                d = np.min(np.hypot(Q[a:a + 512, None, 0] - Ks[None, :, 0], Q[a:a + 512, None, 1] - Ks[None, :, 1]), 1)
                shared[a:a + 512] |= d < tol
        if not shared.any(): keep.append(Q); continue
        runs = np.split(np.arange(len(Q)), np.where(np.diff(shared.astype(int)) != 0)[0] + 1)
        for r in runs:
            if shared[r[0]]: continue
            if len(r) - 1 < min_len: continue
            a, b = r[0], r[-1]
            if a > 0: r = np.concatenate([[a - 1], r]); toes.append(Q[a - 1].tolist())
            if b < len(Q) - 1: r = np.concatenate([r, [b + 1]]); toes.append(Q[b + 1].tolist())
            keep.append(Q[r])
    return keep, toes

def tangents(Q):
    T = np.gradient(Q, axis=0); return T / np.maximum(np.hypot(*T.T), 1e-9)[:, None]

def overhead(tracks, every=55.0, reach=60.0, bundle_gap=12.0, clear=3.0, dedupe=30.0):
    segs = [(Q[:-1], Q[1:]) for Q in tracks]
    A = np.vstack([s[0] for s in segs]); B = np.vstack([s[1] for s in segs]); D = B - A
    Dn = D / np.maximum(np.hypot(*D.T), 1e-9)[:, None]
    portals, cants, centres = [], [], []
    for Q in tracks:
        T = tangents(Q); s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])
        for st in np.arange(every / 2, s[-1] - 5, every):
            i = int(np.searchsorted(s, st)); i = min(max(i, 0), len(Q) - 1)
            c, t = Q[i], T[i]; n = np.array([-t[1], t[0]])
            if centres and np.min(np.hypot(*(np.array(centres) - c).T)) < dedupe: continue
            # where the perpendicular crosses each parallel track segment
            M = np.stack([np.repeat(n[None], len(A), 0), -D], 2)   # [n, -d] [u; v] = A - c
            det = M[:, 0, 0] * M[:, 1, 1] - M[:, 0, 1] * M[:, 1, 0]
            ok = (np.abs(det) > 1e-9) & (np.abs(Dn @ t) > 0.85)
            r = A - c; u = np.where(ok, (r[:, 0] * M[:, 1, 1] - r[:, 1] * M[:, 0, 1]) / np.where(ok, det, 1), np.nan)
            v = np.where(ok, (M[:, 0, 0] * r[:, 1] - M[:, 1, 0] * r[:, 0]) / np.where(ok, det, 1), np.nan)
            hit = ok & (v >= 0) & (v <= 1) & (np.abs(u) <= reach)
            offs = np.sort(np.unique(np.round(np.r_[u[hit], 0.0], 1)))
            # the bundle that contains this track
            k0 = int(np.argmin(np.abs(offs))); lo = hi = k0
            while lo > 0 and offs[lo] - offs[lo - 1] < bundle_gap: lo -= 1
            while hi < len(offs) - 1 and offs[hi + 1] - offs[hi] < bundle_gap: hi += 1
            centres.append(c + n * (offs[lo] + offs[hi]) / 2)
            if hi > lo: portals.append((c + n * (offs[lo] - clear), c + n * (offs[hi] + clear), t))
            else:   # lone track: mast on the side with more room
                side = 1.0 if (hi + 1 >= len(offs) or offs[hi + 1] - offs[hi] > 6) else -1.0
                cants.append((c + n * side * 2.8, c, t))
    return portals, cants

def snap_post(p, inward, tracks, clear=2.6):
    """move a portal post outward until it stands >= clear m from every track centreline"""
    allp = np.vstack(tracks)
    for _ in range(40):
        if np.min(np.hypot(*(allp - p).T)) >= clear: return p
        p = p - inward * 0.25
    return p

def plan(ways, KF=None, KE=None, gantries=None, extra=None, shifts=None):
    """gantries: portals measured on the aerial (list of dict a, b world ends); other lines get masts every 37 m
    (pole pitch measured on the Clifton Hill line beside Wellington Pde)"""
    # extra: open-air track the aerial shows beyond an OSM tunnel tag (Mernda line runs 27 m further in the open)
    W = merge(list(ways) + list(extra or []))
    tracks = []
    for w in W: tracks += visible(densify(w), KF, KE)
    for sh in shifts or []:   # measured on Esri z19: rail pair centre vs model, per-track median over the corridor
        tracks[sh['track']] = tracks[sh['track']] + np.array(sh['d'])
    tracks = [smooth(t) for t in tracks]   # OSM vertex kinks (up to 2.3 deg) smoothed out: 21 m running mean, ends fixed
    tracks, toes = turnouts(tracks)
    tracks, TO = templates(tracks, toes, skip=(1, 2, 4, 5))   # Punt Rd toes wait for the retrace (trace crosses walls)
    portals, cants = [], []
    if gantries:
        for g in gantries:
            a, b = np.array(g['a']), np.array(g['b']); d = (b - a) / np.hypot(*(b - a))
            a = snap_post(a, d, tracks); b = snap_post(b, -d, tracks); t = np.array([d[1], -d[0]])
            portals.append((a, b, t))
        G = np.array([0.5 * (np.array(g['a']) + np.array(g['b'])) for g in gantries])
        rest = [Q for Q in tracks if np.min(np.hypot(*(Q[:, None] - G[None]).transpose(2, 0, 1))) > 120]
    else: rest = tracks
    if rest:
        p2, c2 = overhead(rest, every=37.0); portals += p2; cants += c2
    return dict(n_ways=len(ways), n_merged=len(W), tracks=tracks, portals=portals, cants=cants, toes=toes, turnouts=TO)

GAUGE = 1.6
def templates(tracks, toes, skip=()):
    """Rebuild each diverging leg from its switch toe as a standard turnout: centreline offset y = x^2/(2R) from the toe
    to the frog (y = gauge), angle a measured from the traced leg (separation growth 0.8-3.5 m), L = 2G/a, R = L/a;
    past the frog the straight leg blends into the trace over 12 m. Returns tracks and one dict per turnout."""
    tracks = [Q.copy() for Q in tracks]; out = []
    for ti, p in enumerate(np.array(toes)):
        if ti in skip: continue
        dv = [k for k, Q in enumerate(tracks) if min(np.hypot(*(Q[0] - p)), np.hypot(*(Q[-1] - p))) < 0.05]
        if not dv: continue
        k = dv[0]; rev = np.hypot(*(tracks[k][0] - p)) >= 0.05; S = tracks[k][::-1] if rev else tracks[k]
        best = None
        for m, U in enumerate(tracks):
            if m == k: continue
            d = np.hypot(*(U - p).T); j = int(np.argmin(d))
            if d[j] < 1.0 and (best is None or d[j] < best[1]): best = (m, d[j], j)
        if best is None: continue
        m, _, j = best; U = tracks[m]; TU = tangents(U)
        LS = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(S, axis=0).T))])
        dS = np.array([np.min(np.hypot(*(U - q).T)) for q in S[LS < 80]]); Ls = LS[:len(dS)]
        sel = (dS > 0.8) & (dS < 3.5)
        if sel.sum() < 4: continue
        a = float(np.arctan(max(np.polyfit(Ls[sel], dS[sel], 1)[0], 0.02)))
        t = TU[j]; t = t if (S[min(5, len(S) - 1)] - p) @ t >= 0 else -t
        nn = np.array([-t[1], t[0]]); sg = 1.0 if (S[np.searchsorted(LS, min(10, LS[-1] - 0.1))] - p) @ nn >= 0 else -1.0
        L = 2 * GAUGE / a; cross = LS[-1] < 2 * L + 2
        if any(o['div'] == k for o in out): continue   # one template per traced leg
        if cross:                            # crossover: two turnouts back to back; angle set by the track spacing D
            D = abs(float((S[-1] - p) @ nn)); Lx = float((S[-1] - p) @ t)
            if D < 2.5 or Lx < 6: continue
            L = Lx / 2.0; a = D / L          # S-curve: each half is a parabola reaching y = D/2 with slope D/L at mid-way
        R = L / a
        if not cross:   # place the toe from the traced straight leg: its back-extension meets the through track at the
            # intersection point IP, which for a curved switch lies L/2 past the toe, so the template's leg lands on the trace
            X = (S[:len(dS)] - p) @ t; f2 = (dS > 2.0) & (dS < 6.0)
            if f2.sum() >= 4:
                mm, cc = np.polyfit(X[f2], dS[f2], 1)
                sh = -cc / mm - (GAUGE / np.arctan(mm) if mm > 0 else 0)
                if 0.04 < mm < 0.2 and abs(sh) < 25:   # 1:5-1:25 and a toe within 25 m of the traced one, else keep the trace fit
                    a = float(np.arctan(mm)); L = 2 * GAUGE / a; R = L / a; p = p + t * sh
        xs = np.arange(0.0, L + 1e-6, 1.0)
        y = xs ** 2 / (2 * R)
        P = p + np.outer(xs, t) + np.outer(y * sg, nn)
        if cross:
            P2 = P[::-1]; q = S[-1]
            # mirror half from the far toe
            U2 = None
            Q2 = q - np.outer(xs, t) - np.outer(y * sg, nn)
            new = np.vstack([P, Q2[::-1][1:]])
            xf = np.sqrt(2 * R * GAUGE); frogs = [p + t * xf + nn * sg * GAUGE, S[-1] - t * xf - nn * sg * GAUGE]
        else:
            x0 = float((P[-1] - S[0]) @ t); fx = np.searchsorted(LS, x0 + 20.0)
            if fx >= len(S) - 1: continue
            tail = S[fx:]
            # straight frog leg from P[-1] at angle a, blended into the trace over 12 m
            dirv = t * np.cos(a) + nn * sg * np.sin(a)
            bl = np.arange(1.0, 20.0, 1.0)
            Sb = S[np.minimum(np.searchsorted(LS, x0 + bl), len(S) - 1)]
            St = P[-1] + np.outer(bl, dirv)
            w = (3 * (bl / 20.0) ** 2 - 2 * (bl / 20.0) ** 3)[:, None]
            new = np.vstack([P, St * (1 - w) + Sb * w, tail])
            frogs = [P[-1]]
        tracks[k] = new[::-1] if rev else new
        out.append(dict(toe=ti, div=k, thr=m, at=p.tolist(), trace_toe=np.array(toes)[ti].tolist(), t=t.tolist(), n=(nn * sg).tolist(), a=a, N=1 / np.tan(a), L=L, R=R,
                        cross=bool(cross), frog=[f.tolist() for f in frogs]))
    return tracks, out

def in_turnout(Q, TO, pad=0.3):
    """True where a track point sits on a turnout's bearer field (toe to 3 m past the frog; crossovers toe to toe),
    so its plain sleeper bed gives way to the turnout bearers."""
    m = np.zeros(len(Q), bool)
    for o in TO:
        p = np.array(o['at']); t = np.array(o['t']); n = np.array(o['n'])
        x = (Q - p) @ t; y = (Q - p) @ n
        if o['cross']:
            Lz = 2 * o['L']; w = 2 * o['L'] ** 2 / (2 * o['R']); ylim = np.full(len(Q), w)
        else:
            Lz = o['L'] + 3.0; ylim = np.where(x <= o['L'], x ** 2 / (2 * o['R']), o['L'] ** 2 / (2 * o['R']) + (x - o['L']) * np.tan(o['a']))
        m |= (x > -pad) & (x < Lz + pad) & (y > -1.7) & (y < ylim + 1.7)
    return m
