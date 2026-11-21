"""Concourse copied from the aerial (grid_w.png): lawn islands with trees on the paving SW of the stadium."""
import json, shutil
sp = 'spec/peoplefirst.json'; shutil.copy(sp, 'spec/peoplefirst_pre8.json')
s = json.load(open(sp, encoding='utf-8'))
ISL = [
    [[-195, -18], [-165, -15], [-160, -45], [-190, -50]],
    [[-158, -28], [-122, -25], [-118, -78], [-150, -80]],
    [[-140, -82], [-115, -82], [-112, -112], [-138, -115]],
    [[-100, -128], [-70, -128], [-68, -158], [-98, -160]],
    [[-30, -140], [-5, -138], [-5, -165], [-30, -167]],
    [[-250, 60], [-205, 40], [-200, -5], [-250, -5]],
]
s['paint_poly'] = [p for p in s['paint_poly'] if p[0] != 'lawn_island'] + [['lawn_island', q] for q in ISL]
s['palette']['lawn_island'] = s['palette']['lawn']
TP = [[-175, -32], [-178, -42], [-135, -42], [-145, -60], [-130, -66], [-160, -50], [-126, -95], [-132, -104],
      [-88, -142], [-80, -150], [-18, -152], [-270, 50], [-245, 52], [-230, 30], [-215, 18], [-240, 10], [-222, 2]]
s['tree_pts'] = s['tree_pts'][:31] + TP
json.dump(s, open(sp, 'w', encoding='utf-8'), indent=1)
fn = 'scene.py'; shutil.copy(fn, 'scene_pre8.py'); t = open(fn, encoding='utf-8', newline='').read()
a = "    print('paved faces', len(PF2))"
assert t.count(a) == 1
b = ("    m_isl = mat_img_vc('bg_lawn_island', os.path.join(HERE, 'tex', 'pf_grass.png'), 0.95)   # garden islands on the concourse, from the aerial\n"
     "    _drape([np.array(p, float) for k, p in spec.get('paint_poly', []) if k == 'lawn_island'], m_isl, 'bg_lawn_islands', 8.0, 0.06)\n" + a)
t = t.replace(a, b)
a2 = "    for poly in [np.array(p, float) for k, p in spec.get('paint_poly', []) if k == 'paved'] + list(polys):"
assert t.count(a2) == 1
t = t.replace(a2, a2.replace("if k == 'paved']", "if k in ('paved', 'lawn_island')]"))
open(fn, 'w', encoding='utf-8', newline='').write(t)
print('ok')
