# Written sources (Wikipedia/austadiums): 18 masts, 42 m top, roof highest point 39 m. Edge 24 m (photos), centre drum top 39 m.
p = 'accor_landmarks.py'; s = open(p, newline='').read()
n = s.count("z0 + 24 + 4 * (1 - "); assert n >= 3, n
s = s.replace("z0 + 24 + 4 * (1 - ", "z0 + 24 + 10 * (1 - ")
for x, y in (("(*B, zt + 5), (*A, zt + 5)", "(*B, zt + 7), (*A, zt + 7)"),
             ("(*A, zt + 5), (*B, zt + 5), (c[0], c[1], zt + 5), (c[0], c[1], zt + 5)", "(*A, zt + 7), (*B, zt + 7), (c[0], c[1], zt + 7), (c[0], c[1], zt + 7)"),
             ("out[1] * 6, z0 + 50)", "out[1] * 6, z0 + 42)")):
    assert x in s, x; s = s.replace(x, y)
open(p, 'w', newline='').write(s); print('ok', n)
