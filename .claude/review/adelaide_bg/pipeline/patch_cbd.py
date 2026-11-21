import shutil
H = 'D:/Temp/claude/b012626c2f559e8f/6855d913-d54b-43b8-92a6-1e4e1b34589b/scratchpad/proto/'
def sub(fn, a, b):
    s = open(H + fn, newline='').read()
    if '\r\n' in s: a, b = a.replace('\n', '\r\n'), b.replace('\n', '\r\n')
    assert s.count(a) == 1, (fn, a[:60], s.count(a))
    open(H + fn, 'w', newline='').write(s.replace(a, b))
shutil.copy(H + 'scene.py', H + 'scene.py.bak_cbd')
# Oval No.2: mown grass with a few worn patches (gate: it is a grass field), 48 m tile; square kept
sub('scene.py', "mat_img('oval2_dirt', os.path.join(_TX, 'adl_dry_grain.png'), 0.95), 0.04, 6.0)",
    "mat_img('oval2_dirt', os.path.join(_TX, 'adl_oval_grass.png'), 0.95), 0.04, 48.0)")
# towers: 5 hand-made CBD facades (colour = palette walls_tower via vertex colour)
sub('scene.py', "[('city_office.png', 3.0, 3.6), ('city_far.png', 12.0, 14.4), ('adl_conc.png', 3.0, 3.6), ('adl_fin.png', 6.0, 3.6), ('adl_band.png', 6.0, 3.6)]",
    "[('cbd_curtain.png', 6.0, 3.6), ('cbd_punched.png', 6.0, 3.6), ('cbd_stone.png', 6.0, 3.6), ('cbd_fins.png', 6.0, 3.6), ('cbd_ribbon.png', 6.0, 3.6)]")
# roof plant box on towers: footprint shrunk to 45 % about the centre, 4 m tall, wall colour x0.85, uv (0,0) = solid spandrel pixel
sub('scene.py', "        if _kov: kind = _kov\n",
    "        if cls == 'tower':\n"
    "            Q = cxy + 0.45 * (P - cxy); q0 = len(verts); pt = top + 4.0\n"
    "            for x_, y_ in Q: verts.append((x_, y_, top))\n"
    "            for x_, y_ in Q: verts.append((x_, y_, pt))\n"
    "            for i in range(k):\n"
    "                faces.append((q0 + i, q0 + (i + 1) % k, q0 + k + (i + 1) % k, q0 + k + i)); cols += [wc * 0.85] * 4; uvs += [(0.001, 0.999)] * 4\n"
    "            pr = RF['metal']; p0 = len(pr[0])\n"
    "            for x_, y_ in Q: pr[0].append((x_, y_, pt)); pr[3].append((x_ / 3.04, y_ / 3.04))\n"
    "            pr[1].append(tuple(p0 + i for i in range(k))); pr[2].extend([rc] * k)\n"
    "        if _kov: kind = _kov\n")
print('ok')
