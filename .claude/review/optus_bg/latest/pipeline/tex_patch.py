import sys
p = 'scene.py'; s = open(p, encoding='utf-8').read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a)); s = s.replace(a, b)
rep("t.image = bpy.data.images.load(path)", "t.image = bpy.data.images.load(path, check_existing=True)", 2)
PT = "'D:/Temp/claude/2117a0e07442304a/b457f311-065b-4525-9ffd-7c62765dd586/scratchpad/bgtex/'"
# ground: sand detail (8 m) replaces ground_detail; asphalt (7.2 m) on roads, water (60 m) on the river, via ground_mask.png
rep("""_dt = _nt.nodes.new('ShaderNodeTexImage'); _dt.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'ground_detail.png'))
_uvd = _nt.nodes.new('ShaderNodeUVMap'); _uvd.uv_map = 'UVDetail'   # one detail tile = 4 m (UVs scaled in the mesh)
_nt.links.new(_uvd.outputs['UV'], _dt.inputs['Vector'])""",
"""BGT = """ + PT + """
_uvd = _nt.nodes.new('ShaderNodeUVMap'); _uvd.uv_map = 'UVDetail'   # UVDetail: 1 unit = 4 m
def _tile(path, metres):
    mp = _nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (4.0 / metres,) * 3
    _nt.links.new(_uvd.outputs['UV'], mp.inputs['Vector'])
    t = _nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path, check_existing=True); _nt.links.new(mp.outputs['Vector'], t.inputs['Vector']); return t
_mk = _nt.nodes.new('ShaderNodeTexImage'); _mk.image = bpy.data.images.load(os.path.join(D, 'ground_mask.png')); _mk.image.colorspace_settings.name = 'Non-Color'
_nt.links.new(_nt.nodes.new('ShaderNodeUVMap').outputs['UV'], _mk.inputs['Vector'])
_sep = _nt.nodes.new('ShaderNodeSeparateColor'); _nt.links.new(_mk.outputs['Color'], _sep.inputs['Color'])
_as = _tile(BGT + 'mt/road_asphalt.png', 7.2); _wa = _tile(BGT + 'perth/perth_swan_water.png', 60.0)
_am = _nt.nodes.new('ShaderNodeMix'); _am.data_type = 'RGBA'; _am.blend_type = 'MULTIPLY'; _am.inputs['Factor'].default_value = 1.0
_nt.links.new(_base, _am.inputs[6]); _nt.links.new(_as.outputs['Color'], _am.inputs[7])
_al = _nt.nodes.new('ShaderNodeMix'); _al.data_type = 'RGBA'; _al.blend_type = 'MULTIPLY'; _al.inputs['Factor'].default_value = 1.0
_al.inputs[7].default_value = (1.76, 1.76, 1.76, 1); _nt.links.new(_am.outputs[2], _al.inputs[6])   # 1 / asphalt mean 0.567
_r = _nt.nodes.new('ShaderNodeMix'); _r.data_type = 'RGBA'; _nt.links.new(_sep.outputs[0], _r.inputs[0]); _nt.links.new(_base, _r.inputs[6]); _nt.links.new(_al.outputs[2], _r.inputs[7])
_w = _nt.nodes.new('ShaderNodeMix'); _w.data_type = 'RGBA'; _nt.links.new(_sep.outputs[1], _w.inputs[0]); _nt.links.new(_r.outputs[2], _w.inputs[6]); _nt.links.new(_wa.outputs['Color'], _w.inputs[7])
_base = _w.outputs[2]
_dt = _tile(BGT + 'perth/perth_sand_detail.png', 8.0)""")
rep("_lift.inputs[7].default_value = (1.21, 1.21, 1.21, 1)   # 1 / detail mean 0.826 keeps the painted value",
    "_lift.inputs[7].default_value = (1.78, 1.78, 1.78, 1)   # 1 / sand detail mean 0.563 keeps the painted value")
# build_class: subsets with their own texture / wall colour
rep("def build_class(cls, tex, tw, th):", "def build_class(cls, tex, tw, th, keep=lambda b: True, tag='', wcol=None):")
rep("        if b['c'] != cls: continue", "        if b['c'] != cls or not keep(b): continue")
rep("        wc = walls[b['wall'] % len(walls)] * (1 + 0.06 * (rng.random() - 0.5))",
    "        wc = (lin(wcol) if wcol else walls[b['wall'] % len(walls)]) * (1 + 0.06 * (rng.random() - 0.5))")
rep("mk_obj('bg_bld_' + cls, verts, faces, mat_facade('facade_' + cls, os.path.join(HERE, 'tex', tex)))",
    "mk_obj('bg_bld_' + cls + tag, verts, faces, mat_facade('facade_' + cls + tag, tex if os.path.isabs(tex) else os.path.join(HERE, 'tex', tex)))")
rep("ro = mk_obj('bg_roof_%s_%s' % (cls, kind), rv, rf, mat_facade('roof_%s_%s' % (cls, kind),",
    "ro = mk_obj('bg_roof_%s%s_%s' % (cls, tag, kind), rv, rf, mat_facade('roof_%s_%s' % (cls, kind),")
rep("""build_class('house', 'wall.png', 3.6, 3.2)
build_class('block', 'wall.png', 3.6, 3.2)
build_class('tower', 'tower.png', 3.0, 3.6)""",
"""_lime = lambda b: b['wall'] % 3 == 0   # one low-rise building in three: cream limestone (texture session)
_far = lambda b: float(np.hypot(*np.array(b['p'], float).mean(0))) > 1000.0
build_class('house', 'wall.png', 3.6, 3.2, keep=lambda b: not _lime(b))
build_class('block', 'wall.png', 3.6, 3.2, keep=lambda b: not _lime(b))
build_class('house', BGT + 'perth/perth_limestone.png', 3.6, 3.2, keep=_lime, tag='_lime', wcol=(215, 200, 165))
build_class('block', BGT + 'perth/perth_limestone.png', 3.6, 3.2, keep=_lime, tag='_lime', wcol=(215, 200, 165))
build_class('tower', 'tower.png', 3.0, 3.6, keep=lambda b: not _far(b))
build_class('tower', BGT + 'mt/city_far.png', 12.0, 14.4, keep=_far, tag='_far')""")
open(p, 'w', encoding='utf-8', newline='').write(s); print('ok')
