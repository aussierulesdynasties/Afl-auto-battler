s = open('accor_landmarks.py', encoding='utf-8', newline='').read()
s = s.replace("NV = 9; seg", "NV = 18; seg")   # 18 transverse vaults counted on the Google aerial (2026-11-20)
a = """        return (c[0] + Rr * math.cos(ph) * math.cos(th), c[1] + Rr * math.cos(ph) * math.sin(th), z0 + H * math.sin(ph))"""
b = """        ph = ph * (80 / 90); r_ = Rr * math.cos(ph) / math.cos(0)   # drum 0-12 m, shallow dome to the lantern ring (aerial: lantern cap on top)
        return (c[0] + r_ * math.cos(th), c[1] + r_ * math.sin(th), z0 + 12 + 26 * math.sin(ph) / math.sin(math.radians(80)))"""
assert a in s; s = s.replace(a, b)
a2 = "    print('landmark dome')"
b2 = """    for i in range(NA):   # drum wall and lantern (r 8.4 m, 38 -> 42 m)
        t0, t1 = 2 * math.pi * i / NA, 2 * math.pi * (i + 1) / NA
        for (rr, za, zb) in ((Rr, z0, z0 + 12), (8.4, z0 + 38, z0 + 42)):
            p0 = (c[0] + rr * math.cos(t0), c[1] + rr * math.sin(t0)); p1 = (c[0] + rr * math.cos(t1), c[1] + rr * math.sin(t1))
            _quadm('dome', (*p0, za), (*p1, za), (*p1, zb), (*p0, zb), [(0, 0), (0.6, 0), (0.6, 1), (0, 1)])
    print('landmark dome')"""
assert a2 in s; s = s.replace(a2, b2)
open('accor_landmarks.py', 'w', encoding='utf-8', newline='').write(s); print('ok')
