p='scene.py'; s=open(p,newline='').read()
old="bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'scene.blend'))"
new='''# courts as real geometry: slab per group (hand-made grain), white lines at ITF dimensions, net (no ground paint blur)
CJ = os.path.join(D, 'courts.json')
if os.path.exists(CJ):
    cj = json.load(open(CJ))
    def court_mat(nm, rgb):
        m = bpy.data.materials.new(nm); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 900.0; nz.inputs['Detail'].default_value = 4.0
        tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.86; mr.inputs['To Max'].default_value = 1.12
        nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs[6].default_value = (*srgb(rgb), 1); nt.links.new(mr.outputs['Result'], mx.inputs[7])
        nt.links.new(mx.outputs[2], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.75
        return m
    mats = {k: court_mat('court_' + k, v) for k, v in cj['pal'].items()}
    for k, hull in cj['slabs']:
        H = np.array(hull, float); z = height(H[:, 0], H[:, 1]).max() + 0.04
        V = [(x, y, z) for x, y in H] + [(H[:, 0].mean(), H[:, 1].mean(), z)]; c = len(H)
        mk_obj('bg_court_slab_' + k, V, [[c, i, (i + 1) % c] for i in range(c)], mats[k])
    white = bpy.data.materials.new('court_line'); white.use_nodes = True; white.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.86, 0.86, 0.84, 1)
    net = bpy.data.materials.new('court_net'); net.use_nodes = True; nb = net.node_tree.nodes['Principled BSDF']
    nb.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1); nb.inputs['Alpha'].default_value = 0.55
    LV, LF, NV, NF = [], [], [], []
    def seg(cx, cy, ux, uy, x0, y0, x1, y1, z, w=0.05):
        wx, wy = -uy, ux; P0 = (cx + ux * x0 + wx * y0, cy + uy * x0 + wy * y0); P1 = (cx + ux * x1 + wx * y1, cy + uy * x1 + wy * y1)
        dx, dy = P1[0] - P0[0], P1[1] - P0[1]; L = math.hypot(dx, dy); nx, ny = -dy / L * w / 2, dx / L * w / 2; n = len(LV)
        LV.extend([(P0[0] + nx, P0[1] + ny, z), (P1[0] + nx, P1[1] + ny, z), (P1[0] - nx, P1[1] - ny, z), (P0[0] - nx, P0[1] - ny, z)]); LF.append([n, n + 1, n + 2, n + 3])
    nc = 0
    for k, cx, cy, ang, L_, W_ in cj['courts']:
        if L_ < 24.5 or W_ < 11.5: continue   # OSM box smaller than a doubles court: no lines rather than wrong ones
        ux, uy = math.cos(ang), math.sin(ang); z = float(height(np.array([cx]), np.array([cy]))[0]) + 0.05; nc += 1
        X, Y, SY, SV = 11.885, 5.485, 4.115, 6.40
        for a, b, c_, d in [(-X, -Y, X, -Y), (-X, Y, X, Y), (-X, -Y, -X, Y), (X, -Y, X, Y), (-X, -SY, X, -SY), (-X, SY, X, SY),
                            (-SV, -SY, -SV, SY), (SV, -SY, SV, SY), (-SV, 0, SV, 0), (-X, 0, -X + 0.1, 0), (X - 0.1, 0, X, 0)]:
            seg(cx, cy, ux, uy, a, b, c_, d, z)
        wx, wy = -uy, ux; n = len(NV)   # net: 0.914 m at the centre strap, posts 0.914 m outside the doubles lines
        for yy, hh in [(-Y - 0.914, 1.07), (0, 0.914), (Y + 0.914, 1.07)]:
            NV.extend([(cx + wx * yy, cy + wy * yy, z), (cx + wx * yy, cy + wy * yy, z + hh)])
        NF.extend([[n, n + 2, n + 3, n + 1], [n + 2, n + 4, n + 5, n + 3]])
    if LV: mk_obj('bg_court_lines', LV, LF, white)
    if NV: mk_obj('bg_court_nets', NV, NF, net)
    print('courts', len(cj['slabs']), 'slabs', nc, 'lined')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'scene.blend'))'''
assert old in s; s=s.replace(old,new); open(p,'w',newline='').write(s); print('ok')
