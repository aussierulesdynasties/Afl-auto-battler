# Far land paddock patchwork (exec'd by scene.py after bg_far_terrain when spec['horizon_v2']): a second UV map 'Macro'
# spans the whole far terrain; the hand-made paddocks.png multiplies the near-field detail tile, gain 1/its mean.
_uvm = ob.data.uv_layers.new(name='Macro'); _lp = np.array([l.vertex_index for l in ob.data.loops])
_uvm.data.foreach_set('uv', np.stack([(VF[_lp, 0] + FA) / (2 * FA), (VF[_lp, 1] + FA) / (2 * FA)], 1).ravel())
_nt = _fm.node_tree; _mu = [n for n in _nt.nodes if n.type == 'MIX' and n.blend_type == 'MULTIPLY'][0]
_un = _nt.nodes.new('ShaderNodeUVMap'); _un.uv_map = 'Macro'
_pt = _nt.nodes.new('ShaderNodeTexImage'); _pt.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'mt', 'paddocks.png')); _pt.interpolation = 'Cubic'
_nt.links.new(_un.outputs['UV'], _pt.inputs['Vector'])
_src = _mu.inputs[7].links[0].from_socket
_pm = _nt.nodes.new('ShaderNodeMix'); _pm.data_type = 'RGBA'; _pm.blend_type = 'MULTIPLY'; _pm.inputs[0].default_value = 1.0
_nt.links.new(_src, _pm.inputs[6]); _nt.links.new(_pt.outputs['Color'], _pm.inputs[7])
_pg = _nt.nodes.new('ShaderNodeVectorMath'); _pg.operation = 'SCALE'; _pg.inputs['Scale'].default_value = 1 / (0.0 + 1.0 * float(open(os.path.join(HERE, 'tex', 'mt', 'paddocks.mean')).read()))
_nt.links.new(_pm.outputs[2], _pg.inputs[0]); _nt.links.new(_pg.outputs[0], _mu.inputs[7])
# the paddock map now carries the land colour (measured from the aerial), so the old yellow far_land tile keeps only its
# grey grain and the vertex colour goes neutral (white -> haze); sandy shore cells keep their colour
_ti = [n for n in _nt.nodes if n.type == 'TEX_IMAGE' and n.image and 'far_land' in n.image.name][0]
_hs = _nt.nodes.new('ShaderNodeHueSaturation'); _hs.inputs['Saturation'].default_value = 0.0
_dst = _ti.outputs['Color'].links[0].to_socket; _nt.links.new(_ti.outputs['Color'], _hs.inputs['Color']); _nt.links.new(_hs.outputs['Color'], _dst)
_fdn = _dst.node; _g0 = sum(_fdn.inputs[7].default_value[:3]) / 3; _fdn.inputs[7].default_value = (_g0, _g0, _g0, 1)
_pf = _nt.nodes.new('ShaderNodeMix'); _pf.data_type = 'RGBA'; _pf.inputs[7].default_value = (1 / _pg.inputs['Scale'].default_value,) * 3 + (1,)
_pr = _nt.nodes.new('ShaderNodeMapRange'); _pr.inputs['From Min'].default_value = 8000; _pr.inputs['From Max'].default_value = 30000; _pr.inputs['To Max'].default_value = 0.7
_nt.links.new(_nt.nodes.new('ShaderNodeCameraData').outputs['View Distance'], _pr.inputs['Value']); _nt.links.new(_pr.outputs['Result'], _pf.inputs[0])
_nt.links.new(_pt.outputs['Color'], _pf.inputs[6]); _nt.links.new(_pf.outputs[2], _pm.inputs[7])   # paddock contrast fades into the haze
_vn = np.ones_like(vc) * (1 - hz) + lin(PAL['haze'])[None, :3] * hz; _sd = np.zeros(len(vc), bool); _sd[:_sand.size] = _sand.ravel(); _vn[_sd] = vc[_sd]
set_corner_col(ob.data, np.concatenate([_vn[lp], np.ones((len(lp), 1))], 1))
print('horizon paddocks on', len(_lp), 'loops')
