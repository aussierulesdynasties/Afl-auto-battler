"""Texture session 2026-11-20, orbit 'carpet' fault: normal map 48 m at strength 0.05; colour = 50/50 of the soft tile (40 m)
and a second sample at 0.37x scale rotated 36.87 deg, contrast x1.469 about the mean (sd 7.15 -> 10.5, water_gain.py);
broad 150 m brightness variation 0.85-1.0."""
P = 'scene.py'; s = open(P, newline='').read(); nl = '\r\n' if '\r\n' in s else '\n'
def rep(a, b):
    global s
    a = a.replace('\n', nl); b = b.replace('\n', nl); assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
rep("_nm.inputs['Strength'].default_value = 0.1\n",
    "_nm.inputs['Strength'].default_value = 0.05\n"
    "    _nu = _wn.nodes.new('ShaderNodeUVMap'); _nsc = _wn.nodes.new('ShaderNodeVectorMath'); _nsc.operation = 'SCALE'; _nsc.inputs['Scale'].default_value = 16.0 / 48.0\n"
    "    _wn.links.new(_nu.outputs['UV'], _nsc.inputs[0]); _wn.links.new(_nsc.outputs[0], _nn.inputs['Vector'])\n")
rep("    _wn.links.new(_tx.outputs['Color'], _mx.inputs[6]); _wn.links.new(_mx.outputs[2], _wb.inputs['Base Color'])\n",
    "    _t2 = _wn.nodes.new('ShaderNodeTexImage'); _t2.image = _tx.image\n"
    "    _mp = _wn.nodes.new('ShaderNodeMapping'); _wn.links.new(_wu.outputs['UV'], _mp.inputs['Vector'])\n"
    "    _sc2 = 16.0 * 0.37 / spec.get('water_tex', ['', 16.0])[1]; _mp.inputs['Scale'].default_value = (_sc2, _sc2, 1); _mp.inputs['Rotation'].default_value = (0, 0, math.radians(36.87))\n"
    "    _wn.links.new(_mp.outputs['Vector'], _t2.inputs['Vector'])\n"
    "    _av = _wn.nodes.new('ShaderNodeMix'); _av.data_type = 'RGBA'; _av.inputs[0].default_value = 0.5\n"
    "    _wn.links.new(_tx.outputs['Color'], _av.inputs[6]); _wn.links.new(_t2.outputs['Color'], _av.inputs[7])\n"
    "    _K = 1.469; _M = (51.2 / 255) ** 2.2\n"
    "    _ct = _wn.nodes.new('ShaderNodeVectorMath'); _ct.operation = 'MULTIPLY_ADD'; _ct.inputs[1].default_value = (_K,) * 3; _ct.inputs[2].default_value = (_M * (1 - _K),) * 3\n"
    "    _wn.links.new(_av.outputs[2], _ct.inputs[0])\n"
    "    _ge = _wn.nodes.new('ShaderNodeNewGeometry'); _nz = _wn.nodes.new('ShaderNodeTexNoise'); _nz.inputs['Scale'].default_value = 1.0 / 150.0; _nz.inputs['Detail'].default_value = 1.0\n"
    "    _wn.links.new(_ge.outputs['Position'], _nz.inputs['Vector'])\n"
    "    _mr = _wn.nodes.new('ShaderNodeMapRange'); _mr.inputs['From Min'].default_value = 0.3; _mr.inputs['From Max'].default_value = 0.7; _mr.inputs['To Min'].default_value = 0.85; _mr.inputs['To Max'].default_value = 1.0\n"
    "    _wn.links.new(_nz.outputs['Fac'], _mr.inputs['Value'])\n"
    "    _sl = _wn.nodes.new('ShaderNodeVectorMath'); _sl.operation = 'SCALE'; _wn.links.new(_ct.outputs[0], _sl.inputs[0]); _wn.links.new(_mr.outputs['Result'], _sl.inputs['Scale'])\n"
    "    _wn.links.new(_sl.outputs[0], _mx.inputs[6]); _wn.links.new(_mx.outputs[2], _wb.inputs['Base Color'])\n")
open(P, 'w', newline='').write(s); print('ok')
