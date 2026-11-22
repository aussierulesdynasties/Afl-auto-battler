# Accor surroundings landmarks (exec'd by scene.py via spec extra_py; shares BL, height, mk_obj, set_uv, mat_img, HERE).
# Positions: OSM centres (_find_lm.py). Sizes: Google search 2026-11-20.
#   Afterpay Arena (ex-SuperDome) way 4987356: masts 42 m, roof 33-39 m, glass curtain wall, ring of white masts.
#   The Dome (Showground) way 35029897: 97 m diameter, 42 m high, white ribbed.
#   Olympic Park station way 19003982: row of curved shell vaults over the platforms.
def _accor_landmarks():
    def _lm_drop(cx, cy, r):
        k = [i for i, b in enumerate(BL) if math.hypot(*(np.mean(b['p'], 0) - (cx, cy))) < r]
        P = max((BL[i] for i in k), key=lambda b: b.get('a', 0))['p'] if k else None
        BL[:] = [b for i, b in enumerate(BL) if i not in k]; return P
    _LMO = {}
    def _acc(key): return _LMO.setdefault(key, [[], [], []])
    def _quadm(key, a, b, c, d, uv):
        V, F, U = _acc(key); n = len(V); V += [a, b, c, d]; F.append((n, n + 1, n + 2, n + 3)); U += uv
    def _beam2(key, a, b, w):
        a, b = np.array(a, float), np.array(b, float); d = b - a; L = np.linalg.norm(d)
        if L < 1e-6: return
        d /= L; up = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0, 0])
        s = np.cross(d, up); s /= np.linalg.norm(s); t = np.cross(d, s); h = w / 2
        C = [s * h + t * h, -s * h + t * h, -s * h - t * h, s * h - t * h]
        for i in range(4):
            j = (i + 1) % 4; _quadm(key, tuple(a + C[i]), tuple(a + C[j]), tuple(b + C[j]), tuple(b + C[i]), [(0, 0), (1, 0), (1, 1), (0, 1)])

    # ---- Afterpay Arena: OSM outline, 20 m glass wall, ribbed roof rising 30 -> 36 m, 12 masts to 42 m ----
    P = _lm_drop(-134, 304, 60)
    if P is not None:
        P = np.array(P, float); c = P.mean(0); z0 = float(height([c[0]], [c[1]])[0])
        _d = P - c; _w, _v = np.linalg.eigh(_d.T @ _d); _u = _d @ _v; _ax = np.abs(_u).max(0) * 0.97   # fitted oval (photo: smooth oval)
        P = np.array([c + _v @ np.array([_ax[0] * math.cos(t), _ax[1] * math.sin(t)]) for t in np.linspace(0, 2 * math.pi, 72, endpoint=False)]); per = 0.0
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]; L = float(np.hypot(*(b - a)))
            _quadm('glass', (a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z0 + 20), (a[0], a[1], z0 + 20),
                   [(per / 6, 0), ((per + L) / 6, 0), ((per + L) / 6, 20 / 8), (per / 6, 20 / 8)]); per += L
        R = [c + (p - c) * 1.04 for p in P]; rings = 16
        for k in range(rings):
            f0, f1 = 1 - k / rings, 1 - (k + 1) / rings
            z_0, z_1 = z0 + 24 + 10 * (1 - f0 ** 2), z0 + 24 + 10 * (1 - f1 ** 2)
            for i in range(len(R)):
                p, q = R[i], R[(i + 1) % len(R)]
                A, B = c + (p - c) * f0, c + (q - c) * f0; Cc, D = c + (q - c) * f1, c + (p - c) * f1
                _quadm('roof', (*A, z_0), (*B, z_0), (*Cc, z_1), (*D, z_1), [(A[0] / 8, A[1] / 8), (B[0] / 8, B[1] / 8), (Cc[0] / 8, Cc[1] / 8), (D[0] / 8, D[1] / 8)])
        for i in range(len(R)):   # fascia 20 -> 30 m
            p, q = R[i], R[(i + 1) % len(R)]
            _quadm('roof', (*p, z0 + 20), (*q, z0 + 20), (*q, z0 + 24), (*p, z0 + 24), [(0, 0), (1, 0), (1, 1.2), (0, 1.2)])
        # 18 spike masts evenly round the roof edge: legs 3 m apart at the base (26 m), apex 42 m leaning 6 m outward (photos)
        Rn = np.array(R); per_ = np.r_[0, np.cumsum(np.hypot(*np.diff(np.vstack([Rn, Rn[:1]]), axis=0).T))]; tot = per_[-1]
        for m in range(18):
            d_ = tot * (m + 0.5) / 18; i_ = int(np.searchsorted(per_, d_) - 1); t_ = (d_ - per_[i_]) / (per_[i_ + 1] - per_[i_])
            e = Rn[i_] + (Rn[(i_ + 1) % len(Rn)] - Rn[i_]) * t_; tg = Rn[(i_ + 1) % len(Rn)] - Rn[i_]; tg /= np.linalg.norm(tg)
            out = (e - c) / np.linalg.norm(e - c); top = (e[0] + out[0] * 6, e[1] + out[1] * 6, z0 + 42)
            # arena_03.jpg close-up: one tapered tube spar per mast on a base node; cable fan = 2 cables each side to the roof rim + 2 backstays
            for s_ in (-5.0, 5.0): g_ = e + tg * s_; _beam2('white', (g_[0], g_[1], z0 + 24), top, 0.7)   # arena_01.jpg: A-frame, two legs
            for d in (-16.0, -8.0, 8.0, 16.0): f_ = e + tg * d; _beam2('white', top, (f_[0], f_[1], z0 + 24), 0.1)
            for f in (0.7, 0.5): q = c + (e - c) * f; _beam2('white', top, (q[0], q[1], z0 + 24 + 10 * (1 - f ** 2)), 0.1)
        for i in range(len(R)):   # raised flat lantern over the centre (f < 0.35), 2 m upstand
            p, q = R[i], R[(i + 1) % len(R)]; A, B = c + (p - c) * 0.45, c + (q - c) * 0.45; zt = z0 + 24 + 10 * (1 - 0.45 ** 2)
            _quadm('roof', (*A, zt), (*B, zt), (*B, zt + 3), (*A, zt + 3), [(0, 0), (1, 0), (1, 0.25), (0, 0.25)])
            _quadm('roof', (*A, zt + 3), (*B, zt + 3), (c[0], c[1], zt + 3), (c[0], c[1], zt + 3), [(A[0] / 8, A[1] / 8), (B[0] / 8, B[1] / 8), (c[0] / 8, c[1] / 8), (c[0] / 8, c[1] / 8)])
        for i in range(len(P)):   # low canopy ring at 12 m, 10 m deep, round the glass wall
            p, q = P[i], P[(i + 1) % len(P)]; po, qo = c + (p - c) * (1 + 18 / np.linalg.norm(p - c)), c + (q - c) * (1 + 18 / np.linalg.norm(q - c))
            _quadm('roof', (*p, z0 + 18), (*q, z0 + 18), (*qo, z0 + 21), (*po, z0 + 21), [(p[0] / 8, p[1] / 8), (q[0] / 8, q[1] / 8), (qo[0] / 8, qo[1] / 8), (po[0] / 8, po[1] / 8)])
        # 11 skylight strips (sat_arena_marked.jpg)
        Rn_ = np.array(R)
        for ang in (119.0, 108.3, 99.8, 101.3, 85.5, 73.6, 34.4, 175.5, -147.5, -141.4, -124.8):
            dv = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))]); pr = (Rn_ - c) @ dv; e = c + dv * pr.max(); nn = np.array([-dv[1], dv[0]]) * 1.25
            def zf(f): return z0 + 24 + 10 * (1 - f ** 2) + 0.15
            p0, p1 = c + (e - c) * 0.5, c + (e - c) * 0.85
            _quadm('white', (*(p0 - nn), zf(0.5)), (*(p0 + nn), zf(0.5)), (*(p1 + nn), zf(0.85)), (*(p1 - nn), zf(0.85)), [(0, 0), (1, 0), (1, 1), (0, 1)])
        print('landmark arena', len(P), 'pts')

    # ---- The Dome: 97 m diameter, 42 m high, white ribbed ----
    P = _lm_drop(434, 148, 35)
    if P is not None:
        c = np.mean(P, 0); z0 = float(height([c[0]], [c[1]])[0]); Rr, H, NA, NB = 48.5, 42.0, 48, 12
        def dp(i, j):
            th = 2 * math.pi * i / NA; ph = (math.pi / 2) * j / NB
            ph = ph * (72 / 90); r_ = Rr * math.cos(ph)   # drum 0-12 m, shallow dome to the lantern ring (aerial: lantern cap on top)
            return (c[0] + r_ * math.cos(th), c[1] + r_ * math.sin(th), z0 + 12 + 18 * math.sin(ph) / math.sin(math.radians(72)))
        for i in range(NA):
            for j in range(NB):
                u0, u1 = i * 2 * math.pi * Rr / NA / 8, (i + 1) * 2 * math.pi * Rr / NA / 8
                _quadm('dome', dp(i, j), dp(i + 1, j), dp(i + 1, j + 1), dp(i, j + 1), [(u0, j / 5), (u1, j / 5), (u1, (j + 1) / 5), (u0, (j + 1) / 5)])
        for i in range(NA):   # drum wall and lantern (r 8.4 m, 38 -> 42 m)
            t0, t1 = 2 * math.pi * i / NA, 2 * math.pi * (i + 1) / NA
            for (rr, za, zb, km) in ((Rr, z0, z0 + 12, 'glass'), (10.0, z0 + 30, z0 + 33, 'glass')):
                p0 = (c[0] + rr * math.cos(t0), c[1] + rr * math.sin(t0)); p1 = (c[0] + rr * math.cos(t1), c[1] + rr * math.sin(t1))
                _quadm(km, (*p0, za), (*p1, za), (*p1, zb), (*p0, zb), [(0, 0), (1, 0), (1, 1), (0, 1)] if rr == Rr else [(0, 0), (0.3, 0), (0.3, 0.4), (0, 0.4)])
            p0 = (c[0] + 11.5 * math.cos(t0), c[1] + 11.5 * math.sin(t0)); p1 = (c[0] + 11.5 * math.cos(t1), c[1] + 11.5 * math.sin(t1))
            _quadm('white', (*p0, z0 + 33), (*p1, z0 + 33), (c[0], c[1], z0 + 35), (c[0], c[1], z0 + 35), [(0, 0), (1, 0), (1, 1), (0, 1)])
            _quadm('white', (*p0, z0 + 32.4), (*p1, z0 + 32.4), (*p1, z0 + 33), (*p0, z0 + 33), [(0, 0), (1, 0), (1, 1), (0, 1)])
        for i in range(16):   # white pilasters on the drum
            t = 2 * math.pi * i / 16; q = (c[0] + (Rr + 0.6) * math.cos(t), c[1] + (Rr + 0.6) * math.sin(t)); _beam2('white', (*q, z0), (*q, z0 + 13), 1.4)
        print('landmark dome')

    # ---- Olympic Park station: curved shell vaults along the long axis ----
    P = _lm_drop(561, 59, 40)
    if P is not None:
        P = np.array(P, float); c = P.mean(0); z0 = float(height([c[0]], [c[1]])[0])
        w, v = np.linalg.eigh(np.cov((P - c).T)); ax = v[:, 1]; nx = v[:, 0]
        L = float(np.ptp((P - c) @ ax)); W = float(np.ptp((P - c) @ nx)); NV = 18; seg = L / NV
        for k in range(NV):
            s0 = -L / 2 + k * seg + 0.6; s1 = s0 + seg - 1.2      # separate shells, 1.2 m gap (aerial: 18 distinct vaults)
            for g in range(6):
              sa, sb = s0 + (s1 - s0) * g / 6, s0 + (s1 - s0) * (g + 1) / 6
              for e in range(16):
                a0, a1 = math.pi * e / 16, math.pi * (e + 1) / 16
                def sp(s, a): t_ = (s - s0) / (s1 - s0); q = c + ax * s + nx * (-W / 2 * math.cos(a)); return (q[0], q[1], z0 + 8 + (9 + 3 * math.sin(math.pi * t_)) * math.sin(a) + 1.5 * math.sin(math.pi * t_))
                _quadm('stshell', sp(sa, a0), sp(sb, a0), sp(sb, a1), sp(sa, a1), [(sa / 8, a0 * W / 16), (sb / 8, a0 * W / 16), (sb / 8, a1 * W / 16), (sa / 8, a1 * W / 16)])
            for side in (-1, 1):
                q = c + ax * (s0 + 2) + nx * (side * W / 2); _beam2('white', (q[0], q[1], z0), (q[0], q[1], z0 + 8), 0.6)
        print('landmark station', round(L), round(W))

    _MATS = {'glass': mat_img('acc_glass', os.path.join(HERE, 'tex', 'acc_glass.png'), 0.15),
             'roof': mat_img('acc_roof_arena', os.path.join(HERE, 'tex', 'acc_roof_arena.png'), 0.5),
             'dome': mat_img('acc_dome', os.path.join(HERE, 'tex', 'acc_dome.png'), 0.5),
             'shell': mat_img('acc_shell', os.path.join(HERE, 'tex', 'acc_shell.png'), 0.45),
             'stshell': mat_img('acc_station', os.path.join(HERE, 'tex', 'acc_station.png'), 0.35),
             'drum': mat_img('acc_drum', os.path.join(HERE, 'tex', 'acc_drum.png'), 0.3),
             'white': mat_img('acc_white', os.path.join(HERE, 'tex', 'lm_white.png'), 0.5)}
    for _k, (_V, _F, _U) in _LMO.items():
        _ob = mk_obj('bg_acc_lm_' + _k, _V, _F, _MATS[_k]); set_uv(_ob.data, [_U[i] for f_ in _F for i in f_])
        if _k == 'roof':   # weld and smooth the arena roof (flat facets showed a radial crease); fascia stays sharp at 40 deg
            import bmesh; _bm = bmesh.new(); _bm.from_mesh(_ob.data); bmesh.ops.remove_doubles(_bm, verts=_bm.verts, dist=0.05)
            [setattr(f, 'smooth', True) for f in _bm.faces]; [setattr(e, 'smooth', not (e.is_manifold and e.calc_face_angle(0) > 0.7)) for e in _bm.edges]
            _bm.to_mesh(_ob.data); _bm.free()

_accor_landmarks()
