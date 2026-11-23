import shutil
shutil.copy('scene.py', 'scene.py.pre_detail')
p = 'scene.py'; s = open(p, encoding='utf-8').read()
a = "_nt.links.new(_base, _mx.inputs[6]); _nt.links.new(_dt.outputs['Color'], _mx.inputs[7])\n"
assert s.count(a) == 1
b = """# texture session 2026-11-20: break the 8 m repeat and fade the detail with distance (GODOT TODO: same in the ground shader)
_mp2 = _nt.nodes.new('ShaderNodeMapping'); _mp2.inputs['Scale'].default_value = (4.0 * 0.37 / 8.0,) * 3; _mp2.inputs['Rotation'].default_value = (0, 0, math.radians(36.87))
_nt.links.new(_uvd.outputs['UV'], _mp2.inputs['Vector'])
_dt2 = _nt.nodes.new('ShaderNodeTexImage'); _dt2.image = _dt.image; _nt.links.new(_mp2.outputs['Vector'], _dt2.inputs['Vector'])
_avg = _nt.nodes.new('ShaderNodeMix'); _avg.data_type = 'RGBA'; _avg.inputs['Factor'].default_value = 0.5
_nt.links.new(_dt.outputs['Color'], _avg.inputs[6]); _nt.links.new(_dt2.outputs['Color'], _avg.inputs[7])
# contrast back: mean + (c - mean) x 1.414 (averaging two unrelated samples cuts the spread by sqrt 2)
_ct = _nt.nodes.new('ShaderNodeMix'); _ct.data_type = 'RGBA'; _ct.blend_type = 'MIX'; _ct.clamp_result = True; _ct.inputs['Factor'].default_value = 1.414
_ct.inputs[6].default_value = (0.563, 0.563, 0.563, 1); _nt.links.new(_avg.outputs[2], _ct.inputs[7])
_ct.clamp_factor = False
# fade to the mean from 150 m to 400 m from the camera
_cd = _nt.nodes.new('ShaderNodeCameraData'); _mr = _nt.nodes.new('ShaderNodeMapRange')
_mr.inputs['From Min'].default_value = 150.0; _mr.inputs['From Max'].default_value = 400.0
_nt.links.new(_cd.outputs['View Distance'], _mr.inputs['Value'])
_fd = _nt.nodes.new('ShaderNodeMix'); _fd.data_type = 'RGBA'; _fd.inputs[7].default_value = (0.563, 0.563, 0.563, 1)
_nt.links.new(_mr.outputs['Result'], _fd.inputs['Factor']); _nt.links.new(_ct.outputs[2], _fd.inputs[6])
_nt.links.new(_base, _mx.inputs[6]); _nt.links.new(_fd.outputs[2], _mx.inputs[7])
"""
s = s.replace(a, b)
if 'import math' not in s: s = 'import math\n' + s
open(p, 'w', encoding='utf-8', newline='').write(s); print('ok')
