p='scene.py'; s=open(p,newline='').read()
i0=s.index("    PV, PF = [], []\n    for poly in polys:"); i1=s.index("    print('roads', len(roads)")
body=s[i0:i1]
new='''    def _drape(polys, mat, nm, tile, lift):   # a 1 m grid inside each outline, draped on the terrain
        PV, PF = [], []
        for poly in polys:
            x0, y0 = np.floor(poly.min(0)); x1, y1 = np.ceil(poly.max(0))
            xs = np.arange(x0, x1 + 1); ys = np.arange(y0, y1 + 1); GX, GY = np.meshgrid(xs, ys)
            px, py = GX.ravel(), GY.ravel(); ins = np.zeros(len(px), bool); j = len(poly) - 1
            for i in range(len(poly)):   # even-odd ray test
                xi, yi = poly[i]; xj, yj = poly[j]
                ins ^= ((yi > py) != (yj > py)) & (px < (xj - xi) * (py - yi) / ((yj - yi) or 1e-9) + xi); j = i
            ins = ins.reshape(GX.shape)
            q = ins[:-1, :-1] & ins[1:, :-1] & ins[:-1, 1:] & ins[1:, 1:]
            if not q.any(): continue
            Z = height(GX, GY) + lift; idx = -np.ones(GX.shape, int); used = np.zeros(GX.shape, bool)
            used[:-1, :-1] |= q; used[1:, :-1] |= q; used[:-1, 1:] |= q; used[1:, 1:] |= q
            s0 = len(PV); idx[used] = s0 + np.arange(used.sum())
            PV.extend(zip(GX[used], GY[used], Z[used]))
            jj, ii = np.nonzero(q)
            PF.extend(zip(idx[jj, ii], idx[jj, ii + 1], idx[jj + 1, ii + 1], idx[jj + 1, ii]))
        if PF:
            ob = mk_obj(nm, [tuple(map(float, v)) for v in PV], [tuple(map(int, f)) for f in PF], mat); co = np.array(PV, float); ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))
            vi = np.zeros(len(ob.data.loops), int); ob.data.loops.foreach_get('vertex_index', vi); set_uv(ob.data, co[vi, :2] / tile)
        return PF
    PF = _drape(polys, m_park, 'bg_carparks', TILE, 0.02)   # 2 cm under the roads (0.04) so they never fight
    m_pave = mat_img('plaza_pavers', _tint(PAL['paved_pavers'], 'pavers_paved.png'), 0.85)
    PF2 = _drape([np.array(p, float) for k, p in spec.get('paint_poly', []) if k == 'paved'], m_pave, 'bg_paved', 6.0, 0.03)
    print('paved faces', len(PF2))
'''
s=s[:i0]+new+s[i1:]
open(p,'w',newline='').write(s); print('ok')
m=open('mk_road_tex.py').read()
m+="""pv = np.asarray(Image.open('tex/mv_plaza_pavers.png').convert('RGB'), np.float32)
t = np.clip(pv / pv.mean() * np.array(P.get('paved_pavers', [190, 188, 182]), np.float32), 0, 255).astype(np.uint8)
Image.fromarray(t).save('tex/pavers_paved.png'); print('pavers', t.mean(), t.std())
"""
open('mk_road_tex.py','w').write(m)
