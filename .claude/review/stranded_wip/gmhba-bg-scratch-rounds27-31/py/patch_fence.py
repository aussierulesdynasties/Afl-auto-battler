import sys
p = sys.argv[1]; t = open(p, newline='').read()
a = "        set_uv_box(mk_obj('bg_court_slab_' + k, V, [[c, i, (i + 1) % c] for i in range(c)], mats[k]).data, 4.0)   # grain tile 0.25 m\n"
assert a in t and 'bg_court_fence' not in t
b = a + """        # perimeter chain-link (3 m, posts every ~3 m), hand-made tile tex/mt/chainlink.png, 1 m repeat
        fm = bpy.data.materials.new('court_fence'); fm.use_nodes = True; fn = fm.node_tree; fb = fn.nodes['Principled BSDF']
        ft = fn.nodes.new('ShaderNodeTexImage'); ft.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'mt', 'chainlink.png'))
        fn.links.new(ft.outputs['Color'], fb.inputs['Base Color']); fn.links.new(ft.outputs['Alpha'], fb.inputs['Alpha']); fb.inputs['Metallic'].default_value = 0.6; fb.inputs['Roughness'].default_value = 0.5
        try: fm.blend_method = 'CLIP'
        except Exception: pass
        FV, FF, FU, PV, PF = [], [], [], [], []
        Hc = np.vstack([H, H[:1]]); run = 0.0
        for (x0, y0), (x1, y1) in zip(Hc, Hc[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            if L < 0.2: continue
            n = len(FV); FV += [(x0, y0, z), (x1, y1, z), (x1, y1, z + 3.0), (x0, y0, z + 3.0)]; FF.append([n, n + 1, n + 2, n + 3]); FU.append([(run, 0), (run + L, 0), (run + L, 3), (run, 3)]); run += L
            for j in range(int(L // 3) + 1):
                px, py = x0 + (x1 - x0) * j * 3 / L, y0 + (y1 - y0) * j * 3 / L; m = len(PV); r = 0.03
                PV += [(px - r, py - r, z), (px + r, py - r, z), (px + r, py + r, z), (px - r, py + r, z), (px - r, py - r, z + 3.05), (px + r, py - r, z + 3.05), (px + r, py + r, z + 3.05), (px - r, py + r, z + 3.05)]
                PF += [[m, m + 1, m + 5, m + 4], [m + 1, m + 2, m + 6, m + 5], [m + 2, m + 3, m + 7, m + 6], [m + 3, m, m + 4, m + 7]]
        fo = mk_obj('bg_court_fence_' + k, FV, FF, fm); ul = fo.data.uv_layers.new()
        for f, uv in zip(fo.data.polygons, FU):
            for q, vi in enumerate(f.loop_indices): ul.data[vi].uv = uv[q]
        pm = bpy.data.materials.new('court_post'); pm.use_nodes = True; pb = pm.node_tree.nodes['Principled BSDF']; pb.inputs['Base Color'].default_value = (0.35, 0.36, 0.37, 1); pb.inputs['Metallic'].default_value = 0.7
        mk_obj('bg_court_posts_' + k, PV, PF, pm)
"""
open(p, 'w', newline='').write(t.replace(a, b))
print('ok')
