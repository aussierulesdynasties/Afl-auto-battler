p = 'scene.py'
s = open(p, encoding='utf-8', newline='').read()
old = "OLV.extend([(P0[0] + nx, P0[1] + ny, z), (P1[0] + nx, P1[1] + ny, z), (P1[0] - nx, P1[1] - ny, z), (P0[0] - nx, P0[1] - ny, z)])"
assert s.count(old) == 1
new = ("z0_, z1_ = (float(v) + 0.08 for v in height(np.array([P0[0], P1[0]]), np.array([P0[1], P1[1]])))   # draped: ground height at each end" + ("\r\n" if "\r\n" in s else "\n") +
       "        OLV.extend([(P0[0] + nx, P0[1] + ny, z0_), (P1[0] + nx, P1[1] + ny, z1_), (P1[0] - nx, P1[1] - ny, z1_), (P0[0] - nx, P0[1] - ny, z0_)])")
s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
