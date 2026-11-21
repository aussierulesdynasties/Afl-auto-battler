# Round-1 board fixes (arena_14.jpg): smooth oval outline, low flat dark roof + raised drum, sloped eave over glass, masts clear.
p = 'accor_landmarks.py'; s = open(p, newline='').read()
a = "        P = np.array(P, float); c = P.mean(0); z0 = float(height([c[0]], [c[1]])[0]); per = 0.0\n"
b = a.replace("; per = 0.0", "") + """        _d = P - c; _w, _v = np.linalg.eigh(_d.T @ _d); _u = _d @ _v; _ax = np.abs(_u).max(0) * 0.97   # fitted oval (photo: smooth oval)
        P = np.array([c + _v @ np.array([_ax[0] * math.cos(t), _ax[1] * math.sin(t)]) for t in np.linspace(0, 2 * math.pi, 72, endpoint=False)]); per = 0.0
"""
assert a in s; s = s.replace(a, b)
for x, y in (("z0 + 26 + 13 * (1 - f0 ** 2), z0 + 26 + 13 * (1 - f1 ** 2)", "z0 + 24 + 4 * (1 - f0 ** 2), z0 + 24 + 4 * (1 - f1 ** 2)"),
             ("(*q, z0 + 26), (*p, z0 + 26)", "(*q, z0 + 24), (*p, z0 + 24)"),
             ("z0 + 26 + 13 * (1 - f ** 2)", "z0 + 24 + 4 * (1 - f ** 2)"),
             ("zt = z0 + 26 + 13 * (1 - 0.35 ** 2)", "zt = z0 + 24 + 4 * (1 - 0.35 ** 2)"),
             ("(*B, zt + 2), (*A, zt + 2)", "(*B, zt + 5), (*A, zt + 5)"),
             ("(*A, zt + 2), (*B, zt + 2), (c[0], c[1], zt + 2), (c[0], c[1], zt + 2)", "(*A, zt + 5), (*B, zt + 5), (c[0], c[1], zt + 5), (c[0], c[1], zt + 5)"),
             ("(f_[0], f_[1], z0 + 26), top", "(f_[0], f_[1], z0 + 24), top"),
             ("out[1] * 6, z0 + 42)", "out[1] * 6, z0 + 50)"),
             ("for m in range(18)", "for m in range(18)"),
             # eave: sloped dark ring from 20 m at the wall to 14 m, 12 m out (replaces flat 12 m canopy)
             ("(*p, z0 + 12), (*q, z0 + 12), (*qo, z0 + 11), (*po, z0 + 11)", "(*p, z0 + 20), (*q, z0 + 20), (*qo, z0 + 14), (*po, z0 + 14)"),
             ("(1 + 10 / np.linalg.norm(p - c)), c + (q - c) * (1 + 10 / np.linalg.norm(q - c))", "(1 + 12 / np.linalg.norm(p - c)), c + (q - c) * (1 + 12 / np.linalg.norm(q - c))")):
    assert x in s, x; s = s.replace(x, y)
open(p, 'w', newline='').write(s)
p = 'mk_accor_lm_tex.py'; s = open(p, newline='').read()
x = "('acc_roof_arena', (140, 146, 150))"; assert x in s; s = s.replace(x, "('acc_roof_arena', (96, 101, 106))"); open(p, 'w', newline='').write(s); print('ok')
