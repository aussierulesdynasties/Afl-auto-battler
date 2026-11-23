"""Texture session 2026-11-20: water colour = mv_harbour_water_soft.png at 40 m per tile (flat-colour test proved the
old texture caused the streaks). Normal map keeps the mesh's 16 m UVs."""
import json
P = 'scene.py'; s = open(P, newline='').read(); nl = '\r\n' if '\r\n' in s else '\n'
def rep(a, b):
    global s
    a = a.replace('\n', nl); b = b.replace('\n', nl); assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
rep("os.path.join(HERE, 'tex', 'mv_harbour_water.png'), 0.12)", "os.path.join(HERE, 'tex', spec.get('water_tex', ['mv_harbour_water.png', 16.0])[0]), 0.12)")
rep("    _mx = _wn.nodes.new('ShaderNodeMix'); _mx.data_type = 'RGBA'; _mx.blend_type = 'MULTIPLY'; _mx.inputs['Factor'].default_value = 1.0\n    _k = spec.get('water_albedo_k'",
    "    _wu = _wn.nodes.new('ShaderNodeUVMap'); _ws = _wn.nodes.new('ShaderNodeVectorMath'); _ws.operation = 'SCALE'\n"
    "    _ws.inputs['Scale'].default_value = 16.0 / spec.get('water_tex', ['', 16.0])[1]   # mesh UVs: 16 m per unit\n"
    "    _wn.links.new(_wu.outputs['UV'], _ws.inputs[0]); _wn.links.new(_ws.outputs[0], _tx.inputs['Vector'])\n"
    "    _mx = _wn.nodes.new('ShaderNodeMix'); _mx.data_type = 'RGBA'; _mx.blend_type = 'MULTIPLY'; _mx.inputs['Factor'].default_value = 1.0\n    _k = spec.get('water_albedo_k'")
open(P, 'w', newline='').write(s)
J = json.load(open('spec/marvel.json')); J['water_tex'] = ['mv_harbour_water_soft.png', 40.0]
json.dump(J, open('spec/marvel.json', 'w'), indent=1); print('ok')
