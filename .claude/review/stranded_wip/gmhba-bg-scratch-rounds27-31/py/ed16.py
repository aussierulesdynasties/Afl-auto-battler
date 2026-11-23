import sys
p = sys.argv[1]; s = open(p, newline='').read()
o = "ob = mk_obj('bg_far_terrain', VF, FF.tolist(), mat_vcol('far', 0.95))\nlp = FF.ravel()\n"
assert o in s
s = s.replace(o, """_fm = mat_mul('far_land', os.path.join(HERE, 'tex', 'mt', 'far_land.png'), 0.95, 1 / float(open(os.path.join(HERE, 'tex', 'mt', 'far_land.mean')).read()))
_nt = _fm.node_tree; _t = [n for n in _nt.nodes if n.type == 'TEX_IMAGE'][0]; _mu = [n for n in _nt.nodes if n.type == 'MIX'][0]
_px = np.array(_t.image.pixels[:]).reshape(-1, 4)[:, :3]; _mc = list((_px ** 2.2).mean(0)) + [1.0]
_cd = _nt.nodes.new('ShaderNodeCameraData'); _mr = _nt.nodes.new('ShaderNodeMapRange')
_mr.inputs['From Min'].default_value = 4000; _mr.inputs['From Max'].default_value = 12000; _mr.inputs['To Min'].default_value = 0; _mr.inputs['To Max'].default_value = 0.6
_fd = _nt.nodes.new('ShaderNodeMix'); _fd.data_type = 'RGBA'; _fd.inputs[7].default_value = _mc   # paddocks soften toward the haze
_nt.links.new(_cd.outputs['View Distance'], _mr.inputs['Value']); _nt.links.new(_mr.outputs['Result'], _fd.inputs[0])
_nt.links.new(_t.outputs['Color'], _fd.inputs[6]); _nt.links.new(_fd.outputs[2], _mu.inputs[7])
ob = mk_obj('bg_far_terrain', VF, FF.tolist(), _fm)
lp = FF.ravel()
_c, _s = math.cos(0.41), math.sin(0.41); set_uv(ob.data, np.stack([VF[lp, 0] * _c - VF[lp, 1] * _s, VF[lp, 0] * _s + VF[lp, 1] * _c], 1) / 900.0)   # rotated tile: no screen-aligned repeat
""")
open(p, 'w', newline='').write(s); print('ok')
