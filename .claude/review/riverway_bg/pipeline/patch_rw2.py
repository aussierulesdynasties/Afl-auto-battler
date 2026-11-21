s = open('scene.py', encoding='utf-8', newline='').read()
a = "    print('paved faces', len(PF2))\n"
assert a in s
b = a + """    if spec.get('rw_water'):   # river: own surface, painted colour map (bank edge lighter) + ripple normal; lagoon pool
        m_w = bpy.data.materials.new('river_water'); m_w.use_nodes = True; nt = m_w.node_tree; bs = nt.nodes['Principled BSDF']
        tc = nt.nodes.new('ShaderNodeTexImage'); tc.image = bpy.data.images.load(os.path.join(HERE, 'data', name, 'prep', 'water_col.png'))
        nt.links.new(tc.outputs['Color'], bs.inputs['Base Color'])
        co_ = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / 8.0, 1 / 8.0, 1)
        nt.links.new(co_.outputs['Object'], mp.inputs['Vector'])
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'rw', 'water_ripple_n.png')); tn.image.colorspace_settings.name = 'Non-Color'
        nt.links.new(mp.outputs['Vector'], tn.inputs['Vector'])
        nm_ = nt.nodes.new('ShaderNodeNormalMap'); nm_.inputs['Strength'].default_value = 0.35
        nt.links.new(tn.outputs['Color'], nm_.inputs['Color']); nt.links.new(nm_.outputs['Normal'], bs.inputs['Normal'])
        bs.inputs['Roughness'].default_value = 0.22
        WP = []
        for el in els:
            t = el.get('tags', {})
            if el.get('type') != 'way' or t.get('natural') != 'water': continue
            P = np.array([_xy(p) for p in (el.get('geometry') or []) if p], float)
            if len(P) < 4: continue
            P = P[:-1] if np.allclose(P[0], P[-1]) else P
            P = np.clip(P, -NE + 2, NE - 2); WP.append(P)
        WF = _drape(WP, m_w, 'bg_river', 2 * NE, 0.06); print('water faces', len(WF))
        m_pool = mat_img('lagoon_pool', os.path.join(HERE, 'tex', 'rw', 'pool.png'), 0.15)
        LF_ = _drape([np.array(p, float) for k, p in spec.get('paint_poly', []) if k == 'lagoon'], m_pool, 'bg_lagoon', 8.0, 0.06); print('lagoon faces', len(LF_))
"""
s = s.replace(a, b, 1)
open('scene.py', 'w', encoding='utf-8', newline='').write(s); print('ok')
