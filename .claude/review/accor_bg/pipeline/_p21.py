# 11 skylight strips counted on sat_arena_marked.jpg; angles (deg, east=0, north=90) from the centre panel; 2.5 m wide, f 0.5 -> 0.85.
p = 'accor_landmarks.py'; s = open(p, newline='').read()
a = "        print('landmark arena'"
new = """        Rn_ = np.array(R)
        for ang in (119.0, 108.3, 99.8, 101.3, 85.5, 73.6, 34.4, 175.5, -147.5, -141.4, -124.8):
            dv = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))]); pr = (Rn_ - c) @ dv; e = c + dv * pr.max(); nn = np.array([-dv[1], dv[0]]) * 1.25
            def zf(f): return z0 + 24 + 10 * (1 - f ** 2) + 0.15
            p0, p1 = c + (e - c) * 0.5, c + (e - c) * 0.85
            _quadm('white', (*(p0 - nn), zf(0.5)), (*(p0 + nn), zf(0.5)), (*(p1 + nn), zf(0.85)), (*(p1 - nn), zf(0.85)), [(0, 0), (1, 0), (1, 1), (0, 1)])
"""
assert a in s and 'skylight' not in s; s = s.replace(a, "        # 11 skylight strips (sat_arena_marked.jpg)\n" + new + a, 1)
open(p, 'w', newline='').write(s); print('ok')
