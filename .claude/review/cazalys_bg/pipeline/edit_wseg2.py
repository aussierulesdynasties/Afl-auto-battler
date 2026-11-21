p = 'scene.py'
s = open(p, encoding='utf-8', newline='').read()
nl = "\r\n" if "\r\n" in s else "\n"
old = "        if L < 1e-6: return" + nl + "        nx, ny = -dy / L * w / 2"
assert s.count(old) == 1
new = ("        if L < 1e-6: return" + nl +
       "        if L > 3.0:   # split so the line follows the ground between terrain grid points" + nl +
       "            k = int(math.ceil(L / 3.0))" + nl +
       "            for i in range(k): wseg((P0[0] + dx * i / k, P0[1] + dy * i / k), (P0[0] + dx * (i + 1) / k, P0[1] + dy * (i + 1) / k), z, w)" + nl +
       "            return" + nl +
       "        nx, ny = -dy / L * w / 2")
s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
