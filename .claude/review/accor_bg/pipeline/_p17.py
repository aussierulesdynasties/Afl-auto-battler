# Round-1 board fix (dome_02.jpg): shallower cap, smaller lantern, dark glass drum band.
p = 'accor_landmarks.py'; s = open(p, newline='').read()
for x, y in (("z0 + 12 + 25 * math.sin(ph)", "z0 + 12 + 18 * math.sin(ph)"),
             ("(Rr, z0, z0 + 12, 'drum'), (15.0, z0 + 37, z0 + 40, 'glass')", "(Rr, z0, z0 + 12, 'glass'), (10.0, z0 + 30, z0 + 33, 'glass')"),
             ("if km == 'drum' else", "if rr == Rr else"),
             ("16.5 * math.cos(t0), c[1] + 16.5 * math.sin(t0)); p1 = (c[0] + 16.5 * math.cos(t1), c[1] + 16.5 * math.sin(t1))", "11.5 * math.cos(t0), c[1] + 11.5 * math.sin(t0)); p1 = (c[0] + 11.5 * math.cos(t1), c[1] + 11.5 * math.sin(t1))"),
             ("(*p0, z0 + 40), (*p1, z0 + 40), (c[0], c[1], z0 + 42), (c[0], c[1], z0 + 42)", "(*p0, z0 + 33), (*p1, z0 + 33), (c[0], c[1], z0 + 35), (c[0], c[1], z0 + 35)"),
             ("(*p0, z0 + 39.4), (*p1, z0 + 39.4), (*p1, z0 + 40), (*p0, z0 + 40)", "(*p0, z0 + 32.4), (*p1, z0 + 32.4), (*p1, z0 + 33), (*p0, z0 + 33)")):
    assert x in s, x; s = s.replace(x, y)
open(p, 'w', newline='').write(s); print('ok')
