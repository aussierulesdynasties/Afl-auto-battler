p='scene.py';s=open(p,newline='').read();N='\r\n' if '\r\n' in s else '\n'
def rep(a,b,c=1):
    global s
    assert s.count(a)==c,(a[:70],s.count(a));s=s.replace(a,b)
rep("    verts, faces, cols = [], [], []"+N+"    deck_c = lin((204, 204, 199))","    verts, faces, cols, buv = [], [], [], []"+N+"    deck_c = lin((204, 204, 199))")
# box_strip: top face gets the full deck map across (u 0..1) and along (v = metres / 30); other faces the parapet strip
rep("    def box_strip(P, z, w, th, c):"+N+"        # one quad strip per segment: top, two sides, bottom"+N+"        for (x1, y1), (x2, y2) in zip(P, P[1:]):",
    "    def box_strip(P, z, w, th, c, deck=False):"+N+"        # one quad strip per segment: top, two sides, bottom"+N+"        run = 0.0"+N+"        for (x1, y1), (x2, y2) in zip(P, P[1:]):")
rep("                faces.append(tuple(s0 + i for i in f)); cols.extend([c] * 4)",
    "                faces.append(tuple(s0 + i for i in f)); cols.extend([c] * 4)"+N+
    "                if deck and f == (0, 3, 2, 1): buv.extend([(1, run / 30), (0, run / 30), (0, (run + L) / 30), (1, (run + L) / 30)])"+N+
    "                else: buv.extend([(0.0, run / 30), (0.06, run / 30), (0.06, (run + L) / 30), (0.0, (run + L) / 30)])"+N+
    "            run += L")
rep("cols.extend([deck_c] * 4)","cols.extend([deck_c] * 4); buv.extend([(0.0, 0), (0.06, 0), (0.06, 0.2), (0.0, 0.2)])",2)
rep("faces.append(tuple(s0 + k2 for k2 in f)); cols.extend([deck_c] * 4)","faces.append(tuple(s0 + k2 for k2 in f)); cols.extend([deck_c] * 4); buv.extend([(0.0, 0), (0.06, 0), (0.06, 0.2), (0.0, 0.2)])",0) if False else None
rep("faces.append((s0, s0 + 1, s0 + 2, s0 + 3)); cols.extend([rail_c] * 4)","faces.append((s0, s0 + 1, s0 + 2, s0 + 3)); cols.extend([rail_c] * 4); buv.extend([(0.0, 0), (0.06, 0), (0.06, 0.2), (0.0, 0.2)])")
rep("        box_strip(P, z, w, 1.4, deck_c)","        box_strip(P, z, w, 1.4, deck_c, deck=True)")
rep("        ob = mk_obj('bg_bridges', verts, faces, mat_vcol('bridge', 0.8))","        ob = mk_obj('bg_bridges', verts, faces, mat_img('bridge', os.path.join(HERE, 'tex', 'mv_bridge_deck.png'), 0.85)); set_uv(ob.data, buv)")
rep("build_class('tower', 'tower.png', 3.0, 3.6)","build_class('tower', *spec.get('tower_tex', ['tower.png', 3.0, 3.6]))")
open(p,'w',newline='').write(s);print('ok')
