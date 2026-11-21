import json
s = open('scene.py', encoding='utf-8', newline='').read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:60], s.count(a)); s = s.replace(a, b)
# concourse: hole for the bowl (the stadium model brings its own field and stands)
rep("    def _drape(polys, mat, nm, tile, lift, bays=False):", "    def _drape(polys, mat, nm, tile, lift, bays=False, hole=None):")
rep("""            for ii, jj in edge:
                if 0 <= jj < q.shape[0] and 0 <= ii < q.shape[1]: q[jj, ii] = False""",
"""            for ii, jj in edge:
                if 0 <= jj < q.shape[0] and 0 <= ii < q.shape[1]: q[jj, ii] = False
            if hole:   # cells whose centre is inside the ellipse are left out
                cx_ = GX[:-1, :-1] + 0.5; cy_ = GY[:-1, :-1] + 0.5; inh = (cx_ / hole[0]) ** 2 + (cy_ / hole[1]) ** 2 < 1
                q &= ~inh; edge = {(ii, jj) for ii, jj in edge if not (0 <= jj < inh.shape[0] and 0 <= ii < inh.shape[1] and inh[jj, ii])}""")
rep("""m_road, 'bg_paved', TILE, 0.03)""", """m_road, 'bg_paved', TILE, 0.03, hole=spec.get('pave_hole'))
    m_pale = mat_img_vc('park_pale', os.path.join(HERE, 'tex', 'park_bays_pale.png'), 0.92)   # the bare concrete end of the SW car park
    _drape([np.array(p, float) for k, p in spec.get('paint_poly', []) if k == 'parking_pale'], m_pale, 'bg_carparks_pale', TILE, 0.025, bays=True)""")
rep("            if mat in (m_park, m_road): _mottle(ob.data, co)", "            if mat in (m_park, m_road) or nm == 'bg_carparks_pale': _mottle(ob.data, co)")
open('scene.py', 'w', encoding='utf-8', newline='').write(s)
# prep: hand-traced tree points from the aerial
p = open('prep.py', encoding='utf-8', newline='').read()
a = "_td = spec.get('tree_default', 0)"
assert p.count(a) == 1
p = p.replace(a, "TR += [[float(x), float(y)] for x, y in spec.get('tree_pts', [])]   # trees traced by hand from the aerial (car park rows)\n" + a)
open('prep.py', 'w', encoding='utf-8', newline='').write(p)
sp = 'spec/peoplefirst.json'; d = json.load(open(sp))
d['pave_hole'] = [92, 80]
d['paint_poly'] = [x for x in d['paint_poly'] if x[0] != 'parking_pale'] + [['parking_pale', [[-250, -105], [-339, -186], [-172, -393], [-160, -375], [-205, -262], [-222, -215], [-262, -150]]]]
px = [(270, 60), (330, 130), (380, 180), (180, 100), (240, 150), (100, 165), (170, 230), (240, 320), (300, 330), (310, 400), (400, 380), (440, 420), (380, 480),
      (490, 310), (560, 380), (500, 470), (560, 540), (620, 490), (670, 540), (330, 600), (390, 650), (440, 730), (500, 790), (560, 870), (620, 950), (560, 1020), (520, 1060),
      (640, 630), (680, 700), (720, 720), (760, 790)]
d['tree_pts'] = [[-290 + a / 4, -110 - b / 4] for a, b in px]
json.dump(d, open(sp, 'w')); print('ok', len(px))
