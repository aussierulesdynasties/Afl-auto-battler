p='scene.py'; s=open(p,newline='').read()
old="    if LV: mk_obj('bg_court_lines', LV, LF, white)"
new="""    for cx, cy, ang, L_, W_ in cj.get('hockey', []):   # FIH pitch 91.4 x 55 m on a run-off slab (the OSM box)
        ux, uy = math.cos(ang), math.sin(ang); wx, wy = -uy, ux; z0 = float(height(np.array([cx]), np.array([cy]))[0])
        def quad(hl, hw, z, nm, mat):
            V = [(cx + ux * a * hl + wx * b * hw, cy + uy * a * hl + wy * b * hw, z) for a, b in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
            mk_obj(nm, V, [[0, 1, 2, 3]], mat)
        quad(L_ / 2, W_ / 2, z0 + 0.04, 'bg_hockey_runoff', mats['turf_runoff'])
        HX, HY = 45.7, 27.5; quad(HX, HY, z0 + 0.05, 'bg_hockey_field', mats['turf_blue']); z = z0 + 0.06
        for a, b, c_, d in [(-HX, -HY, HX, -HY), (-HX, HY, HX, HY), (-HX, -HY, -HX, HY), (HX, -HY, HX, HY), (0, -HY, 0, HY),
                            (-HX + 22.9, -HY, -HX + 22.9, HY), (HX - 22.9, -HY, HX - 22.9, HY)]:
            seg(cx, cy, ux, uy, a, b, c_, d, z, 0.075)
        for sgn in (-1, 1):   # shooting circle: 14.63 m quarter arcs from each post (1.83 m off centre) joined by 3.66 m; dashed 5 m line
            for r, dash in [(14.63, False), (19.63, True)]:
                pts = [(sgn * (HX - r * math.cos(t)), -1.83 - r * math.sin(t)) for t in np.linspace(0, math.pi / 2, 16)] + \
                      [(sgn * (HX - r * math.cos(t)), 1.83 + r * math.sin(t)) for t in np.linspace(math.pi / 2, 0, 16)]
                for i, ((a, b), (c_, d)) in enumerate(zip(pts, pts[1:])):
                    if dash and i % 3: continue
                    seg(cx, cy, ux, uy, a, b, c_, d, z, 0.075)
        print('hockey pitch', round(L_, 1), round(W_, 1))
    if LV: mk_obj('bg_court_lines', LV, LF, white)"""
assert old in s; s=s.replace(old,new); open(p,'w',newline='').write(s); print('ok')
