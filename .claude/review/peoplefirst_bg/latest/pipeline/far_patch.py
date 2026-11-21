s = open('mk_far2.py', encoding='utf-8').read()
a = s.index('# paddocks'); b = s.index('a = np.asarray(im')
new = '''# paddocks: random recursive splits (no tile-long lines), each leaf its own tone; belts on some edges
def split(x0, y0, x1, y1, dep):
    w, h = x1 - x0, y1 - y0
    if dep > 7 or (w < 140 and h < 140) or (dep > 2 and R.random() < 0.15):
        t = R.choice([0.78, 0.86, 0.94, 1.02, 1.08, 0.9]); hue = R.uniform(-0.07, 0.05)
        c = tuple(int(v) for v in np.clip(np.array([t * (1 + hue), t, t * (1 - hue)]) * 225, 0, 255))
        rect_wrap(x0, y0, x1, y1, c)
        if R.random() < 0.5: rect_wrap(x0, y0, x1, y0 + 4, (118, 128, 104))
        if R.random() < 0.4: rect_wrap(x0, y0, x0 + 4, y1, (118, 128, 104))
        return
    if w > h: m = x0 + int(w * R.uniform(0.3, 0.7)); split(x0, y0, m, y1, dep + 1); split(m, y0, x1, y1, dep + 1)
    else: m = y0 + int(h * R.uniform(0.3, 0.7)); split(x0, y0, x1, m, dep + 1); split(x0, m, x1, y1, dep + 1)
split(0, 0, n, n, 0)
'''
open('mk_far2.py', 'w', encoding='utf-8').write(s[:a] + new + s[b:])
t = open('scene.py', encoding='utf-8', newline='').read()
o = "set_uv(ob.data, VF[lp, :2] / 600.0)"
assert t.count(o) == 1
t = t.replace(o, "_c, _s = math.cos(0.41), math.sin(0.41); set_uv(ob.data, np.stack([VF[lp, 0] * _c - VF[lp, 1] * _s, VF[lp, 0] * _s + VF[lp, 1] * _c], 1) / 900.0)   # rotated, larger tile: no screen-aligned repeat")
open('scene.py', 'w', encoding='utf-8', newline='').write(t); print('ok')
