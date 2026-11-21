# sat_arena_crop.jpg (Esri z18): raised flat centre panel spans ~45% of the oval, not 35%.
p = 'accor_landmarks.py'; s = open(p, newline='').read()
for x, y in (("A, B = c + (p - c) * 0.35, c + (q - c) * 0.35; zt = z0 + 24 + 4 * (1 - 0.35 ** 2)", "A, B = c + (p - c) * 0.45, c + (q - c) * 0.45; zt = z0 + 24 + 4 * (1 - 0.45 ** 2)"),):
    assert x in s, x; s = s.replace(x, y)
open(p, 'w', newline='').write(s); print('ok')
