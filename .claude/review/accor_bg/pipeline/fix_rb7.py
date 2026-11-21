p='scene.py'; s=open(p,newline='').read()
i0=s.index("    def _drape(polys, mat, nm, tile, lift):"); i1=s.index("    PF = _drape(polys, m_park")
new='''    def _clipsq(poly, x, y):   # the polygon clipped to the 1 m square at (x, y) (Sutherland-Hodgman, square is convex)
        out = [tuple(q) for q in poly]
        for ax, sg, c in ((0, 1, x), (0, -1, x + 1), (1, 1, y), (1, -1, y + 1)):
            if not out: break
            inp, out = out, []
            for k in range(len(inp)):
                a, b = inp[k - 1], inp[k]; ia = (a[ax] - c) * sg >= 0; ib = (b[ax] - c) * sg >= 0
                if ia != ib:
                    t = (c - a[ax]) / (b[ax] - a[ax]); out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
                if ib: out.append(b)
        return out
    def _drape(polys, mat, nm, tile, lift):   # 1 m grid inside each outline; edge cells cut to the true outline
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
            E = _dens(np.vstack([poly, poly[:1]]), 0.25); edge = set(zip((np.floor(E[:, 0]) - x0).astype(int), (np.floor(E[:, 1]) - y0).astype(int)))
            for ii, jj in edge:
                if 0 <= jj < q.shape[0] and 0 <= ii < q.shape[1]: q[jj, ii] = False
            if q.any():
                Z = height(GX, GY) + lift; idx = -np.ones(GX.shape, int); used = np.zeros(GX.shape, bool)
                used[:-1, :-1] |= q; used[1:, :-1] |= q; used[:-1, 1:] |= q; used[1:, 1:] |= q
                s0 = len(PV); idx[used] = s0 + np.arange(used.sum())
                PV.extend(zip(GX[used], GY[used], Z[used]))
                jj_, ii_ = np.nonzero(q)
                PF.extend(zip(idx[jj_, ii_], idx[jj_, ii_ + 1], idx[jj_ + 1, ii_ + 1], idx[jj_ + 1, ii_]))
            for ii, jj in edge:   # boundary cells: the outline clipped to the cell, vertices on the true outline
                c = _clipsq(poly, x0 + ii, y0 + jj)
                if len(c) < 3: continue
                C = np.array(c); z = height(C[:, 0], C[:, 1]) + lift; s0 = len(PV)
                PV.extend(zip(C[:, 0], C[:, 1], z))
                for tri in tessellate_polygon([[Vector((a, b, 0)) for a, b in c]]): PF.append(tuple(s0 + t for t in tri))
        if PF:
            ob = mk_obj(nm, [tuple(map(float, v)) for v in PV], [tuple(map(int, f)) for f in PF], mat); co = np.array(PV, float); ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))
            vi = np.zeros(len(ob.data.loops), int); ob.data.loops.foreach_get('vertex_index', vi); set_uv(ob.data, co[vi, :2] / tile)
        return PF
'''
s=s[:i0]+new+s[i1:]
a="m_pave = mat_img('plaza_pavers', _tint(None, 'pavers_paved.png'), 0.85)"; assert a in s
s=s.replace(a,a.replace('0.85)','0.9); m_pave.node_tree.nodes[\'Principled BSDF\'].inputs[\'Specular IOR Level\'].default_value = 0.3'))
open(p,'w',newline='').write(s)
q=open('prep.py',newline='').read()
a="for pk, poly in spec.get('paint_poly', []): dr.polygon(P([tuple(q) for q in poly]), fill=tuple(PAL[pk]))"; assert a in q
q=q.replace(a,a+"""
if spec.get('road_mesh'):   # paved and car-park meshes cover these: grass under them (+1.5 m) so no halo shows at their edges
    _G = [poly for pk, poly in spec.get('paint_poly', []) if pk in ('parking', 'paved')]
    for el in js:
        t_ = el.get('tags', {})
        if el['type'] == 'way' and t_.get('amenity') == 'parking' and t_.get('parking', 'surface') == 'surface' and len(el.get('geometry') or []) > 3:
            _G.append([xy(p['lat'], p['lon']) for p in el['geometry'] if p])
    for poly in _G:
        pp = P([tuple(q_) for q_ in poly]); dr.polygon(pp, fill=tuple(PAL['lawn'])); dr.line(pp + pp[:1], fill=tuple(PAL['lawn']), width=max(1, round(3.0 / PX)))""",1)
open('prep.py','w',newline='').write(q); print('ok')
