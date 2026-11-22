# Arena roof edge 33 -> 26 m (sources: masts 42 m, roof top 39 m, interior ceiling 33 m max), roof panel joints.
p = 'accor_landmarks.py'; s = open(p, newline='').read()
for a, b in (('z0 + 33 + 6 * (1 - f0 ** 2), z0 + 33 + 6 * (1 - f1 ** 2)', 'z0 + 26 + 13 * (1 - f0 ** 2), z0 + 26 + 13 * (1 - f1 ** 2)'),
             ('(*q, z0 + 33), (*p, z0 + 33)', '(*q, z0 + 26), (*p, z0 + 26)'),
             ('(f_[0], f_[1], z0 + 33), top', '(f_[0], f_[1], z0 + 26), top'),
             ('z0 + 33 + 6 * (1 - f ** 2)', 'z0 + 26 + 13 * (1 - f ** 2)')):
    assert a in s, a; s = s.replace(a, b)
open(p, 'w', newline='').write(s)
p = 'mk_accor_lm_tex.py'; s = open(p, newline='').read()
a = "a[:, x + 3:x + 5] *= 1.08\n"
if 'panel joints' not in s:
    assert a in s; s = s.replace(a, a + "    if n == 'acc_roof_arena':\n        for y in range(0, 512, 128): a[y:y + 3] *= 0.85   # panel joints\n", 1)
open(p, 'w', newline='').write(s)
print('ok')
