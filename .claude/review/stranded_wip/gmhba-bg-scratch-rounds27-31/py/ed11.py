import sys
p = sys.argv[1]; s = open(p, newline='').read()
o = "    if _sel.any():\n        _F = FF[_sel]; _o = mk_obj(_nm, VF, _F.tolist(), _mt)"
assert o in s
s = s.replace(o, """    _nt = _mt.node_tree; _t = [n for n in _nt.nodes if n.type == 'TEX_IMAGE'][0]; _mu = [n for n in _nt.nodes if n.type == 'MIX'][0]
    _px = np.array(_t.image.pixels[:]).reshape(-1, 4)[:, :3]; _mc = list((_px ** 2.2).mean(0)) + [1.0]   # the tile's own linear mean colour
    _cd = _nt.nodes.new('ShaderNodeCameraData'); _mr = _nt.nodes.new('ShaderNodeMapRange')
    _mr.inputs['From Min'].default_value = 1500; _mr.inputs['From Max'].default_value = 4000; _mr.inputs['To Min'].default_value = 0; _mr.inputs['To Max'].default_value = 0.7
    _fd = _nt.nodes.new('ShaderNodeMix'); _fd.data_type = 'RGBA'; _fd.inputs[7].default_value = _mc   # distance fade: tile -> its mean, contrast 30% by 4 km
    _nt.links.new(_cd.outputs['View Distance'], _mr.inputs['Value']); _nt.links.new(_mr.outputs['Result'], _fd.inputs[0])
    _nt.links.new(_t.outputs['Color'], _fd.inputs[6]); _nt.links.new(_fd.outputs[2], _mu.inputs[7])
""" + o)
open(p, 'w', newline='').write(s); print('ok')
