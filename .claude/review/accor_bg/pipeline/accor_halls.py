# Showground exhibition halls beside The Dome: walls to 10 m, shallow white barrel roof (rise 6 m) along the long axis.
# Ref: ausleisure aerial (refacc/dome1.jpg, 2026-11-20): halls west of the Dome have pale curved barrel roofs.
# OSM centres (_find_lm.py): Pet 35030140, Showbag 35030189, Flower & Garden 35062193, Arts & Crafts 1226368336, Fashion & Style 1226368337.
def _accor_halls():
    V, F, U = [], [], []; VW, FW, UW = [], [], []
    for (cx, cy) in ((583, 213), (655, 240), (343, 228), (401, 269), (442, 278)):
        k = [i for i, b in enumerate(BL) if math.hypot(*(np.mean(b['p'], 0) - (cx, cy))) < 30]
        if not k: print('hall missing', cx, cy); continue
        P = np.array(max((BL[i] for i in k), key=lambda b: b.get('a', 0))['p'], float)
        BL[:] = [b for i, b in enumerate(BL) if i not in k]
        c = P.mean(0); z0 = float(height([c[0]], [c[1]])[0])
        w, v = np.linalg.eigh(np.cov((P - c).T)); ax, nx = v[:, 1], v[:, 0]
        a0, a1 = float(np.min((P - c) @ ax)), float(np.max((P - c) @ ax)); b0, b1 = float(np.min((P - c) @ nx)), float(np.max((P - c) @ nx))
        Wd = b1 - b0; NE = 12
        def pt(s, t, z): q = c + ax * s + nx * t; return (q[0], q[1], z)
        def rz(t): return z0 + 10 + 6 * (1 - ((2 * (t - b0) / Wd) - 1) ** 2)
        for e in range(NE):   # roof: barrel across the width, running the full length
            t0, t1 = b0 + Wd * e / NE, b0 + Wd * (e + 1) / NE; n = len(V)
            V += [pt(a0 - 1, t0, rz(t0)), pt(a1 + 1, t0, rz(t0)), pt(a1 + 1, t1, rz(t1)), pt(a0 - 1, t1, rz(t1))]
            F.append((n, n + 1, n + 2, n + 3)); U += [(a0 / 8, t0 / 8), (a1 / 8, t0 / 8), (a1 / 8, t1 / 8), (a0 / 8, t1 / 8)]
        R = [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]
        for i in range(4):    # walls
            (sa, ta), (sb, tb) = R[i], R[(i + 1) % 4]; n = len(VW); L = math.hypot(sb - sa, tb - ta)
            VW += [pt(sa, ta, z0), pt(sb, tb, z0), pt(sb, tb, z0 + 10), pt(sa, ta, z0 + 10)]
            FW.append((n, n + 1, n + 2, n + 3)); UW += [(0, 0), (L / 6, 0), (L / 6, 10 / 8), (0, 10 / 8)]
        for (sx, tt) in ((a0 - 1, None), (a1 + 1, None)):   # gable ends under the barrel
            for e in range(NE):
                t0, t1 = b0 + Wd * e / NE, b0 + Wd * (e + 1) / NE; n = len(VW)
                VW += [pt(sx, t0, z0 + 10), pt(sx, t1, z0 + 10), pt(sx, t1, rz(t1)), pt(sx, t0, rz(t0))]
                FW.append((n, n + 1, n + 2, n + 3)); UW += [(0, 0), (1, 0), (1, 1), (0, 1)]
        print('landmark hall', round(a1 - a0), round(Wd))
    o = mk_obj('bg_acc_lm_halls_roof', V, F, mat_img('acc_hall_roof', os.path.join(HERE, 'tex', 'acc_shell.png'), 0.45)); set_uv(o.data, [U[i] for f_ in F for i in f_])
    o = mk_obj('bg_acc_lm_halls_wall', VW, FW, mat_img('acc_hall_wall', os.path.join(HERE, 'tex', 'acc_drum.png'), 0.4)); set_uv(o.data, [UW[i] for f_ in FW for i in f_])

_accor_halls()
