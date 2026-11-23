import json, shutil
R = 'D:/Temp/claude/b5e56bf702cd3703/4ee81fc3-6cf4-400f-9ad6-28a5df4e19ee/scratchpad/proto/'
p = R + 'prep.py'; s = open(p, encoding='utf-8', newline='').read()
a = "math.hypot(*pts[0]) < 400:"
b = "math.hypot(*pts[0]) < spec.get('court_r', 400):"
c = "                col = 'court_green'\n"
d = "                col = spec.get('court_default', 'court_green')\n"
if a in s:
    shutil.copy(p, p + '.bak_courts')
    assert c.replace('\n', '\r\n') in s or c in s
    s = s.replace(a, b).replace(c.replace('\n', '\r\n'), d.replace('\n', '\r\n')).replace(c, d)
    open(p, 'w', encoding='utf-8', newline='').write(s)
j = R + 'spec/mcg.json'; sp = json.load(open(j, encoding='utf-8'))
shutil.copy(j, j + '.bak_courts')
sp['palette']['court_blue'] = [64, 120, 180]
sp['palette']['court_green'] = [58, 108, 80]
sp['court_slabs'] = True; sp['court_r'] = 900; sp['court_default'] = 'court_blue'
json.dump(sp, open(j, 'w', encoding='utf-8'), indent=1)
print('ok', 'court_r' in open(p, encoding='utf-8').read())
