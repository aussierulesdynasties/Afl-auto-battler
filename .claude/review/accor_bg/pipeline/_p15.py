# Photo pass 2026-11-21 (arena 12, station 10 photos): 18 narrow spike masts all round, leaning out; raised central lantern;
# 10 m low canopy ring at 12 m; grey zincalume roof; station shells grey (own material).
p = 'accor_landmarks.py'; s = open(p, newline='').read()
a0 = s.index('        # A-frame masts'); a1 = s.index("        print('landmark arena'")
new = """        # 18 spike masts evenly round the roof edge: legs 3 m apart at the base (26 m), apex 42 m leaning 6 m outward (photos)
        Rn = np.array(R); per_ = np.r_[0, np.cumsum(np.hypot(*np.diff(np.vstack([Rn, Rn[:1]]), axis=0).T))]; tot = per_[-1]
        for m in range(18):
            d_ = tot * (m + 0.5) / 18; i_ = int(np.searchsorted(per_, d_) - 1); t_ = (d_ - per_[i_]) / (per_[i_ + 1] - per_[i_])
            e = Rn[i_] + (Rn[(i_ + 1) % len(Rn)] - Rn[i_]) * t_; tg = Rn[(i_ + 1) % len(Rn)] - Rn[i_]; tg /= np.linalg.norm(tg)
            out = (e - c) / np.linalg.norm(e - c); top = (e[0] + out[0] * 6, e[1] + out[1] * 6, z0 + 42)
            for d in (-1.5, 1.5): f_ = e + tg * d; _beam2('white', (f_[0], f_[1], z0 + 26), top, 0.7)
            for f in (0.7, 0.4): q = c + (e - c) * f; _beam2('white', top, (q[0], q[1], z0 + 26 + 13 * (1 - f ** 2)), 0.12)
            g_ = e + out * 18; _beam2('white', top, (g_[0], g_[1], z0 + 12), 0.12)
        for i in range(len(R)):   # raised flat lantern over the centre (f < 0.35), 2 m upstand
            p, q = R[i], R[(i + 1) % len(R)]; A, B = c + (p - c) * 0.35, c + (q - c) * 0.35; zt = z0 + 26 + 13 * (1 - 0.35 ** 2)
            _quadm('roof', (*A, zt), (*B, zt), (*B, zt + 2), (*A, zt + 2), [(0, 0), (1, 0), (1, 0.25), (0, 0.25)])
            _quadm('roof', (*A, zt + 2), (*B, zt + 2), (c[0], c[1], zt + 2), (c[0], c[1], zt + 2), [(A[0] / 8, A[1] / 8), (B[0] / 8, B[1] / 8), (c[0] / 8, c[1] / 8), (c[0] / 8, c[1] / 8)])
        for i in range(len(P)):   # low canopy ring at 12 m, 10 m deep, round the glass wall
            p, q = P[i], P[(i + 1) % len(P)]; po, qo = c + (p - c) * (1 + 10 / np.linalg.norm(p - c)), c + (q - c) * (1 + 10 / np.linalg.norm(q - c))
            _quadm('roof', (*p, z0 + 12), (*q, z0 + 12), (*qo, z0 + 11), (*po, z0 + 11), [(p[0] / 8, p[1] / 8), (q[0] / 8, q[1] / 8), (qo[0] / 8, qo[1] / 8), (po[0] / 8, po[1] / 8)])
"""
s = s[:a0] + new + s[a1:]
s = s.replace("_quadm('shell', sp(sa", "_quadm('stshell', sp(sa")
a = "             'shell': mat_img('acc_shell', os.path.join(HERE, 'tex', 'acc_shell.png'), 0.45),\n"
assert a in s; s = s.replace(a, a + "             'stshell': mat_img('acc_station', os.path.join(HERE, 'tex', 'acc_station.png'), 0.35),\n")
open(p, 'w', newline='').write(s)
p = 'mk_accor_lm_tex.py'; s = open(p, newline='').read()
s = s.replace("(('acc_roof_arena', (178, 182, 186)), ('acc_shell', (196, 198, 196)))", "(('acc_roof_arena', (140, 146, 150)), ('acc_shell', (196, 198, 196)), ('acc_station', (138, 144, 148)))")
assert 'acc_station' in s; open(p, 'w', newline='').write(s); print('ok')
