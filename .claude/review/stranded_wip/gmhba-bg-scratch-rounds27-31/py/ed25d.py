import sys
p = sys.argv[1]; s = open(p, encoding='utf-8', newline='').read()
s = s.replace("_pm.inputs[0].default_value = 0.55", "_pm.inputs[0].default_value = 1.0")
s = s.replace("1 / (0.45 + 0.55 * float(open(", "1 / (0.0 + 1.0 * float(open(")
a = "print('horizon paddocks on'"
assert a in s
b = """# the paddock map now carries the land colour (measured from the aerial), so the old yellow far_land tile keeps only its
# grey grain and the vertex colour goes neutral (white -> haze); sandy shore cells keep their colour
_ti = [n for n in _nt.nodes if n.type == 'TEX_IMAGE' and n.image and 'far_land' in n.image.name][0]
_hs = _nt.nodes.new('ShaderNodeHueSaturation'); _hs.inputs['Saturation'].default_value = 0.0
_dst = _ti.outputs['Color'].links[0].to_socket; _nt.links.new(_ti.outputs['Color'], _hs.inputs['Color']); _nt.links.new(_hs.outputs['Color'], _dst)
_fdn = _dst.node; _g0 = sum(_fdn.inputs[7].default_value[:3]) / 3; _fdn.inputs[7].default_value = (_g0, _g0, _g0, 1)
_pf = _nt.nodes.new('ShaderNodeMix'); _pf.data_type = 'RGBA'; _pf.inputs[7].default_value = (1 / _pg.inputs['Scale'].default_value,) * 3 + (1,)
_pr = _nt.nodes.new('ShaderNodeMapRange'); _pr.inputs['From Min'].default_value = 8000; _pr.inputs['From Max'].default_value = 30000; _pr.inputs['To Max'].default_value = 0.7
_nt.links.new(_nt.nodes.new('ShaderNodeCameraData').outputs['View Distance'], _pr.inputs['Value']); _nt.links.new(_pr.outputs['Result'], _pf.inputs[0])
_nt.links.new(_pt.outputs['Color'], _pf.inputs[6]); _nt.links.new(_pf.outputs[2], _pm.inputs[7])   # paddock contrast fades into the haze
_vn = np.ones_like(vc) * (1 - hz) + lin(PAL['haze'])[None, :3] * hz; _sd = _sand.ravel(); _vn[_sd] = vc[_sd]
set_corner_col(ob.data, np.concatenate([_vn[lp], np.ones((len(lp), 1))], 1))
""" + a
s = s.replace(a, b); open(p, 'w', encoding='utf-8', newline='').write(s); print('ok')
