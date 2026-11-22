# ---------- Melbourne Park arenas (director 2026-11-20 "Yes, build all four"): OSM footprints, roofs copied from the aerial ----------
if 'arenas' in LM:
    AR = json.load(open(os.path.join(HERE, 'data', spec['name'], 'prep', 'arenas.json')))
    def gzm(P):   # walls start at the lowest ground round the footprint, so no side floats over a slope
        return float(np.min(height(np.array([q[0] for q in P]), np.array([q[1] for q in P])))) - 1.0
    def byname(nm):
        for i, b in enumerate(BL):
            if b.get('name') == nm: return i
        return None
    def dome(key, P, z0, rise, rings, f_top, uvmode='plan'):
        """roof rising from footprint P (at z0) to a smaller copy f_top of it; height follows a quarter sine; plan-mapped UVs."""
        tw, th = LMS['lm_%s.png' % key]; V, F, U = bk(key); k = len(P); c = np.mean(P, 0); n0 = len(V)
        for r in range(rings + 1):
            t = r / rings; f = 1 - (1 - f_top) * t; z = z0 + rise * math.sin(t * math.pi / 2)
            for x, y in P:
                q = c + (np.array((x, y)) - c) * f; V.append((q[0], q[1], z)); U.append((q[0] / tw, q[1] / th))
        for r in range(rings):
            for i in range(k):
                a = n0 + r * k + i; b = n0 + r * k + (i + 1) % k; F.append((a, b, b + k, a + k))
        return [tuple(np.array(V[n0 + rings * k + i][:2])) for i in range(k)], z0 + rise
    # Rod Laver: round ribbed white dome over white walls, glazed centre panel (aerial), 30 m
    i = byname('Rod Laver Arena'); P = ccw(AR['Rod Laver Arena']); z = gzm(P)
    if i is not None: drop.add(i)
    wall_ring('rla_wall', P, z, z + 12.5, z); top, zt = dome('ribwhite', P, z + 12.5, 15.5, 6, 0.55)   # glazed facade 12.5 m (photo 020); roof rise to 28 m unmeasured
    cap('ribwhite', scaled(top, 0.98), zt + 0.3); wall_ring('ribwhite', scaled(top, 0.98), zt - 0.5, zt + 0.3)
    c = np.mean(P, 0)
    cP = np.mean(P, 0); Pr = np.array(P) - cP; ax_, ay_ = np.abs(Pr[:, 0]).max(), np.abs(Pr[:, 1]).max()
    def dz(x_, y_):   # dome surface height at (x, y): same quarter-sine as dome(), radial fraction from the footprint's half-axes
        r_ = math.hypot((x_ - cP[0]) / ax_, (y_ - cP[1]) / ay_); t_ = min(1.0, max(0.0, (1 - r_) / 0.45)); return z + 12.5 + 15.5 * math.sin(t_ * math.pi / 2) + 1.0
    def hug(a2, b2, w_):
        pts = [np.array(a2) + (np.array(b2) - np.array(a2)) * s_ for s_ in np.linspace(0, 1, 11)]
        for p_, q_ in zip(pts, pts[1:]): beam('white', (p_[0], p_[1], dz(*p_)), (q_[0], q_[1], dz(*q_)), w_)
    for yb in (-146, -161, -176, -190, -205):   # opening-roof frame (aerial): 5 long E-W girders, 104 m, N-S ribs every 10.4 m, hugging the roof
        hug((-474, yb), (-370, yb), 0.9)
    for xb in np.linspace(-474, -370, 11): hug((xb, -146), (xb, -205), 0.5)
    print('landmark rod laver base', round(z, 1))
    # Margaret Court (OSM outline = the copper long-roof hall west of Rod Laver on the aerial): copper walls and roof, 16 m
    i = byname('Margaret Court Arena'); P = ccw(AR['Margaret Court Arena']); z = gzm(P)
    if i is not None: drop.add(i)
    wall_ring('mca_wall', P, z, z + 12, z); cap('copper', P, z + 12)   # glazed + diamond panels to a 12 m eave (photo 124)
    # folded-plate brown roof (aerial: lit/shaded stripe pairs, 8.75 m pitch, ridges ~15 deg west of north; photo 124 eave 12 m)
    def _inside(q, P=P):
        c_ = False; k_ = len(P)
        for i_ in range(k_):
            (x1_, y1_), (x2_, y2_) = P[i_], P[(i_ + 1) % k_]
            if (y1_ > q[1]) != (y2_ > q[1]) and q[0] < x1_ + (q[1] - y1_) * (x2_ - x1_) / (y2_ - y1_): c_ = not c_
        return c_
    d_ = np.array((-0.253, -0.967)); n_ = np.array((0.967, -0.253)); Pa = np.array(P)
    nn = Pa @ n_; dd = Pa @ d_; tw, th = LMS['lm_copper.png']; V, F, U = bk('copper')
    for s0 in np.arange(nn.min(), nn.max(), 8.75):
        s1_ = s0 + 8.75; ts = np.arange(dd.min(), dd.max() + 1, 1.0)
        ins = [_inside(n_ * (s0 + 0.6) + d_ * t) and _inside(n_ * (s1_ - 0.6) + d_ * t) for t in ts]
        runs = []; st = None
        for t, f in zip(ts, ins):
            if f and st is None: st = t
            if not f and st is not None: runs.append((st, t - 1)); st = None
        if st is not None: runs.append((st, ts[-1]))
        for a_, b_ in runs:
            if b_ - a_ < 4: continue
            sm = s0 + 4.375; pts6 = [(n_ * s0 + d_ * a_, z + 12), (n_ * sm + d_ * a_, z + 15), (n_ * s1_ + d_ * a_, z + 12),
                                    (n_ * s0 + d_ * b_, z + 12), (n_ * sm + d_ * b_, z + 15), (n_ * s1_ + d_ * b_, z + 12)]   # folded plate: ridge mid-bay, 3 m rise
            k0 = len(V)
            for q, zq in pts6: V.append((q[0], q[1], zq)); U.append((q[0] / tw, q[1] / th))
            F += [(k0, k0 + 3, k0 + 4, k0 + 1), (k0 + 1, k0 + 4, k0 + 5, k0 + 2), (k0, k0 + 1, k0 + 2), (k0 + 5, k0 + 4, k0 + 3)]
    print('landmark margaret court base', round(z, 1))
    # John Cain: traced on sat19 (0.25 m) in the arena's own frame, turned 5 deg clockwise from grid north about (-130, -305): u east, v north (out/mcg/qa/r5.png)
    # sat19 is not straight down: west and south wall faces show (2.0 m on the 12 m west wing, 2.5 m on the 15 m SW drum), so a roof at height h appears
    # 0.167 h north-east (u+, v+) of its footprint. Outlines below are the traced ROOF edges; each footprint is moved back by 0.167 h.
    i = byname('John Cain Arena'); P = ccw(AR['John Cain Arena']); z = gzm(P)
    if i is not None: drop.add(i)
    _c, _s, KL = math.cos(math.radians(5)), math.sin(math.radians(5)), 0.167
    def L(u_, v_, h_=0.0): return (-130 + (u_ - KL * h_) * _c + (v_ - KL * h_) * _s, -305 - (u_ - KL * h_) * _s + (v_ - KL * h_) * _c)
    def rect(u0_, v0_, u1_, v1_): return [(u0_, v0_), (u1_, v0_), (u1_, v1_), (u0_, v1_)]
    def quad(cu, cv, ru, rv, a0, a1, extra): return [(cu + ru * math.cos(t), cv + rv * math.sin(t)) for t in np.linspace(math.radians(a0), math.radians(a1), 10)] + extra
    eo = [(50.6, 30), (52, 30), (55, 27), (61, 21), (63, 10), (63, -38), (60, -46), (55, -52), (50.6, -55)]
    for R_, h_ in ((rect(-37.5, -28.75, 34.75, 35), 18), (rect(-66, -28, -37.5, 31), 12), (rect(34.75, -30.6, 50.6, 30), 16), (eo, 12),
                   (rect(-29, 35, 29, 55), 16), (rect(-26.5, 55, 26, 78), 10),
                   (quad(-34.4, 35, 17, 21, 90, 180, [(-34.4, 35)]), 15), (quad(34.75, 37, 15.25, 16.75, 0, 90, [(34.75, 30.6), (50, 30.6)]), 15),
                   (quad(-38.75, -30, 17, 20, 180, 270, [(-38.75, -28), (-55.75, -28)]), 15),
                   (rect(-38, -59, 30.6, -28.75), 15), (rect(-37, -82.5, 20, -59), 12)):   # heights: photos MCG OIC + Melbourne Park 011 (scaled off the 18 m parapet)
        P_ = ccw([L(u_, v_, h_) for u_, v_ in R_]); wall_ring('jca_wall', P_, z, z + h_, z); cap('ribwhite', P_, z + h_)
    D_ = ccw([L(u_, v_, 18) for u_, v_ in quad(30, -33, 16, 21, 270, 360, [(30, -33)])])   # SE signage drum facing Olympic Blvd (photo 011): glazed body to 14.5 m, grey crown with JOHN CAIN ARENA to 18 m
    # photo 2MCGG0C: ground storey set back behind round columns (to 5 m), silver panel band with a window strip to 14.5 m, grey sign crown to 18 m
    Di_ = ccw([L(u_, v_, 18) for u_, v_ in quad(30, -33, 13.5, 18.5, 270, 360, [(30, -33)])])
    wall_ring('glazed', Di_, z, z + 5, z); wall_ring('jca_wall', D_, z + 5, z + 14.5, z + 5); cap('ribwhite', D_, z + 5, down=True)
    wall_ring('jca_sign', D_, z + 14.5, z + 18, z + 14.5); cap('ribwhite', D_, z + 18)
    for t_ in np.linspace(math.radians(275), math.radians(355), 7):
        C_ = L(30 + 15 * math.cos(t_), -33 + 20 * math.sin(t_), 18); beam('white', (*C_, z), (*C_, z + 5), 0.7)
    wall_ring('jca_signq', ccw([L(u_, v_, 12) for u_, v_ in eo]), z + 9, z + 12.5, z + 9)   # east wing crown with sign facing the MCG (photo MCG OIC)
    for (ua, va), (ub, vb) in (((-31, 68), (-36.5, -68)), ((32.5, 68), (26.5, -68))):   # retractable-roof track girders, 19.5 m, ~3 deg off the hall axis on sat19
        A_, B_ = L(ua, va, 19.5), L(ub, vb, 19.5)
        beam('white', (*A_, z + 19.5), (*B_, z + 19.5), 1.2); beam('white', (*A_, z + 18), (*B_, z + 18), 0.6)
        for (ue, ve) in ((ua, va), (ub, vb)):   # photo 2MCGG0C: each end stands on a white lattice A-frame, legs splayed 8 m along the facade, ties and X-braces
            T_ = L(ue, ve, 19.5); F1, F2 = L(ue - 4, ve, 0), L(ue + 4, ve, 0)
            for F_ in (F1, F2): beam('white', (*F_, z), (*T_, z + 19.5), 0.7)
            for k3 in range(4):
                f0, f1 = k3 / 4, (k3 + 1) / 4
                P0 = [(F1[i] + (T_[i] - F1[i]) * f0, F2[i] + (T_[i] - F2[i]) * f0) for i in (0, 1)]; P1 = [(F1[i] + (T_[i] - F1[i]) * f1, F2[i] + (T_[i] - F2[i]) * f1) for i in (0, 1)]
                a0 = (P0[0][0], P0[1][0], z + 19.5 * f0); b0 = (P0[0][1], P0[1][1], z + 19.5 * f0); a1 = (P1[0][0], P1[1][0], z + 19.5 * f1); b1 = (P1[0][1], P1[1][1], z + 19.5 * f1)
                beam('white', a1, b1, 0.35); beam('white', a0, b1, 0.3); beam('white', b0, a1, 0.3)
    for vc in (20, -11.25):   # two E-W arched trusses, 27.5 m bands, X-braced in 5 bays (sat19)
        us = np.linspace(-34.4, 33, 11); ht_ = [19 + 5 * math.cos(u_ / 34 * math.pi / 2) for u_ in us]
        Q = lambda k2, sd: (*L(us[k2], vc + sd, ht_[k2]), z + ht_[k2])
        for side in (-13.75, 13.75):
            for k2 in range(10): beam('white', Q(k2, side), Q(k2 + 1, side), 0.6)
        for k2 in range(0, 10, 2):
            beam('white', Q(k2, -13.75), Q(k2 + 2, 13.75), 0.4); beam('white', Q(k2, 13.75), Q(k2 + 2, -13.75), 0.4)
        for k2 in range(0, 11, 2): beam('white', Q(k2, -13.75), Q(k2, 13.75), 0.4)
    print('landmark john cain base', round(z, 1))
    # AAMI Park: ring of white geodesic bubbles round a rectangular pitch (aerial: 6 lobes per long side, 4 per end), 30 m
    P = ccw(AR['AAMI Park']); z = gz(P); c = np.mean(P, 0)
    P = [P[j] for j in range(0, len(P), 2)]; k = len(P)
    ang = np.arctan2(np.array(P)[:, 1] - c[1], np.array(P)[:, 0] - c[0])
    per = np.concatenate([[0], np.cumsum([math.hypot(P[(j + 1) % k][0] - P[j][0], P[(j + 1) % k][1] - P[j][1]) for j in range(k)])]); L = per[-1]
    NL = 20; tw, th = LMS['lm_bubble.png']; V, F, U = bk('bubble'); n0 = len(V); S = 10
    inner = scaled(P, 0.6)
    for s_ in range(S + 1):
        t = s_ / S
        for j in range(k):
            lob = abs(math.sin(math.pi * NL * per[j] / L))     # 0 at the valleys between bubbles, 1 at each crown
            o = np.array(P[j]); q = o + (np.array(inner[j]) - o) * t
            zz = z + 6 + (22 + 6 * lob) * math.sin(math.pi * min(1, t * 1.15) / 1) ** 0.7 * (0.75 + 0.25 * lob)
            q = q + (o - c) / np.linalg.norm(o - c) * 4 * lob * math.sin(math.pi * t)   # bubbles bulge outward
            V.append((q[0], q[1], zz)); U.append((per[j] / tw, t * 40 / th))
    for s_ in range(S):
        for j in range(k):
            a = n0 + s_ * k + j; b = n0 + s_ * k + (j + 1) % k; F.append((a, b, b + k, a + k))
    wall_ring('arena_wall', P, z, z + 6, z)
    T1 = scaled(P, 0.6); T2 = scaled(P, 0.48)    # empty seat bowl inside the shell, down to the pitch
    V, F, U = bk('tiers'); n0 = len(V); tw, th = LMS['lm_tiers.png']
    for j in range(k):
        V += [(T1[j][0], T1[j][1], z + 16), (T2[j][0], T2[j][1], z + 1)]; U += [(per[j] / tw, 18 / th), (per[j] / tw, 0)]
    for j in range(k):
        a, b = n0 + 2 * j, n0 + 2 * ((j + 1) % k); F.append((a + 1, b + 1, b, a))
    # pitch: 136 x 88 m rectangle (real dimensions incl. run-off) aligned with the shell's long axis
    Pa = np.array(P) - c; ev = np.linalg.eigh(Pa.T @ Pa)[1][:, 1]; ex = np.array([-ev[1], ev[0]])
    R = [tuple(c + ev * su * 68 + ex * sv * 44) for su, sv in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
    cap('pitch', ccw(R), z + 1.05)
    print('landmark aami park base', round(z, 1))
