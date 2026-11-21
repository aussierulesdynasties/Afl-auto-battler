R = 'D:/Temp/claude/b5e56bf702cd3703/4ee81fc3-6cf4-400f-9ad6-28a5df4e19ee/scratchpad/proto/'
import shutil
# prep: courts under a roof (centre inside any OSM building) are indoor show courts -> not drawn outside
p = R + 'prep.py'; s = open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'
a = "                CT.append([pts[:-1], col])"
b = ("                if spec.get('court_skip_indoor') and any(_inpoly(cx, cy, B_) for B_ in _BLD): continue   # under a roof: indoor court" + nl +
     "                CT.append([pts[:-1], col])")
h = "if spec.get('court_slabs'):" + nl + "    CT = []"
hb = ("def _inpoly(x, y, Q):" + nl +
      "    c = False" + nl +
      "    for i in range(len(Q)):" + nl +
      "        (x1, y1), (x2, y2) = Q[i], Q[i - 1]" + nl +
      "        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c" + nl +
      "    return c" + nl +
      "_BLD = [ring(el) for el in js if el['type'] == 'way' and 'building' in el.get('tags', {}) and 'geometry' in el] if spec.get('court_skip_indoor') else []" + nl +
      h)
assert a in s and h in s and '_inpoly' not in s
shutil.copy(p, p + '.bak_courts2')
s = s.replace(h, hb, 1).replace(a, b, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
# scene: lines and nets sit on the slab (slab z = highest ground under the hull), so lines never hide under a floating slab
p = R + 'scene.py'; s = open(p, encoding='utf-8', newline='').read()
a = "z = float(height(np.array([cx]), np.array([cy]))[0]) + 0.05; nc += 1"
b = ("_cx_ = np.array([cx + ux * i * L_ / 2 - uy * j * W_ / 2 for i in (-1, 1) for j in (-1, 1)]); _cy_ = np.array([cy + uy * i * L_ / 2 + ux * j * W_ / 2 for i in (-1, 1) for j in (-1, 1)])" + nl +
     "        z = float(height(_cx_, _cy_).max()) + 0.05; nc += 1")
assert a in s
shutil.copy(p, p + '.bak_courts2')
s = s.replace(a, b, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
