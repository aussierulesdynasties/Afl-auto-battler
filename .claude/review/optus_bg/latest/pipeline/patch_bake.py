import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scene.py')
s = open(P, encoding='utf-8', newline='').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)

# helper: box-projected UVs from object-space positions (stands in for Object texture coordinates)
rep("""def set_uv(me, uvs):
    uv = me.uv_layers.new(name='UVMap'); uv.data.foreach_set('uv', np.asarray(uvs, np.float32).ravel())
""", """def set_uv(me, uvs):
    uv = me.uv_layers.new(name='UVMap'); uv.data.foreach_set('uv', np.asarray(uvs, np.float32).ravel())
def set_uv_box(me, scale):   # UV = object position x scale, projected on each face's dominant axis
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    vi = np.zeros(len(me.loops), int); me.loops.foreach_get('vertex_index', vi)
    nr = np.zeros(len(me.polygons) * 3); me.polygons.foreach_get('normal', nr); nr = np.abs(nr.reshape(-1, 3))
    tot = np.zeros(len(me.polygons), int); me.polygons.foreach_get('loop_total', tot)
    ax = np.repeat(np.argmax(nr, 1), tot); p = co[vi]
    u = np.where(ax == 0, p[:, 1], p[:, 0]); v = np.where(ax == 2, p[:, 1], p[:, 2])
    set_uv(me, np.stack([u, v], 1) * scale)
""")

# ground detail: second UV map holds the 4 m tiling (was a Mapping node)
rep("""_mp = _nt.nodes.new('ShaderNodeMapping'); _tc = _nt.nodes.new('ShaderNodeTexCoord')
_mp.inputs['Scale'].default_value = (2 * NE / 4.0, 2 * NE / 4.0, 1)   # one detail tile = 4 m
_nt.links.new(_tc.outputs['UV'], _mp.inputs['Vector']); _nt.links.new(_mp.outputs['Vector'], _dt.inputs['Vector'])
""", """_uvd = _nt.nodes.new('ShaderNodeUVMap'); _uvd.uv_map = 'UVDetail'   # one detail tile = 4 m (UVs scaled in the mesh)
_nt.links.new(_uvd.outputs['UV'], _dt.inputs['Vector'])
""")
rep("""set_uv(ob.data, uv)
for p in ob.data.polygons: p.use_smooth = True
""", """set_uv(ob.data, uv)
_ud = ob.data.uv_layers.new(name='UVDetail'); _ud.data.foreach_set('uv', (uv * (2 * NE / 4.0)).astype(np.float32).ravel())
for p in ob.data.polygons: p.use_smooth = True
""")

# trees: hand-made leaf clump texture + normal map (was Voronoi + MapRange + Bump)
rep("""    # leaf clumps (procedural, hand-set): Voronoi cells ~0.35 m darken their edges and bump the crown so it reads as foliage
    tc = nt.nodes.new('ShaderNodeTexCoord'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 2.8
    vo.feature = 'F1'; nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Max'].default_value = 0.6; mr.inputs['To Min'].default_value = 1.15; mr.inputs['To Max'].default_value = 0.62
    nt.links.new(vo.outputs['Distance'], mr.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    nt.links.new(vc, mx.inputs[6]); nt.links.new(mr.outputs['Result'], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6; nt.links.new(vo.outputs['Distance'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
""", """    # leaf clumps (hand-made tex/leaf_clumps.png, tex_bake.py): cells ~0.35 m darken their edges and bump the crown so it reads as foliage
    lt = nt.nodes.new('ShaderNodeTexImage'); lt.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'leaf_clumps.png'))
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    nt.links.new(vc, mx.inputs[6]); nt.links.new(lt.outputs['Color'], mx.inputs[7])
    lf = nt.nodes.new('ShaderNodeMix'); lf.data_type = 'RGBA'; lf.blend_type = 'MULTIPLY'; lf.inputs['Factor'].default_value = 1.0
    lf.inputs[7].default_value = (1.15, 1.15, 1.15, 1)   # texture stores the clump multiplier / 1.15
    nt.links.new(mx.outputs[2], lf.inputs[6]); nt.links.new(lf.outputs[2], b.inputs['Base Color'])
    ln = nt.nodes.new('ShaderNodeTexImage'); ln.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'leaf_normal.png')); ln.image.colorspace_settings.name = 'Non-Color'
    nm_ = nt.nodes.new('ShaderNodeNormalMap'); nm_.uv_map = 'UVMap'
    nt.links.new(ln.outputs['Color'], nm_.inputs['Color']); nt.links.new(nm_.outputs['Normal'], b.inputs['Normal'])
""")
rep("""    ob = mk_obj('bg_trees_' + kn, verts, faces, tm)
    ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))
""", """    ob = mk_obj('bg_trees_' + kn, verts, faces, tm)
    ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))
    set_uv_box(ob.data, 2.8 / 8)   # leaf_clumps.png tile = 8 cells of 1/2.8 m
""")

# courts: hand-made grain texture (was Noise + MapRange)
rep("""        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 900.0; nz.inputs['Detail'].default_value = 4.0
        tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.86; mr.inputs['To Max'].default_value = 1.12
        nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs[6].default_value = (*srgb(rgb), 1); nt.links.new(mr.outputs['Result'], mx.inputs[7])
        nt.links.new(mx.outputs[2], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.75
""", """        gt = nt.nodes.new('ShaderNodeTexImage'); gt.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'court_grain.png'))   # tex_bake.py, 0.25 m tile
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs[6].default_value = (*[1.12 * c for c in srgb(rgb)], 1); nt.links.new(gt.outputs['Color'], mx.inputs[7])   # grain stored / 1.12
        nt.links.new(mx.outputs[2], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.75
""")
rep("""        mk_obj('bg_court_slab_' + k, V, [[c, i, (i + 1) % c] for i in range(c)], mats[k])
""", """        set_uv_box(mk_obj('bg_court_slab_' + k, V, [[c, i, (i + 1) % c] for i in range(c)], mats[k]).data, 4.0)   # grain tile 0.25 m
""")
open(P, 'w', encoding='utf-8', newline='').write(s)
print('patched')
