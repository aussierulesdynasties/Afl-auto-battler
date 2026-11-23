"""Water albedo scale spec water_albedo_k: calibrated so the rendered p5 water matches the photo's median [25,50,73]."""
import sys
P = 'scene.py'; s = open(P, newline='').read()
a = "   # water: real IOR, near-mirror\n"
if 'water_albedo_k' not in s:
    nl = '\r\n' if '\r\n' in s else '\n'; a = a.replace('\n', nl); assert s.count(a) == 1
    s = s.replace(a, a + "    _tx = [nd_ for nd_ in _wn.nodes if nd_.type == 'TEX_IMAGE' and nd_.image.name.startswith('mv_water.')][0]\n".replace('\n', nl)
                  + "    _mx = _wn.nodes.new('ShaderNodeMix'); _mx.data_type = 'RGBA'; _mx.blend_type = 'MULTIPLY'; _mx.inputs['Factor'].default_value = 1.0\n".replace('\n', nl)
                  + "    _k = spec.get('water_albedo_k', 1.0); _mx.inputs[7].default_value = (_k, _k, _k, 1)\n".replace('\n', nl)
                  + "    _wn.links.new(_tx.outputs['Color'], _mx.inputs[6]); _wn.links.new(_mx.outputs[2], _wb.inputs['Base Color'])\n".replace('\n', nl))
    open(P, 'w', newline='').write(s)
import json
sp = json.load(open('spec/marvel.json')); sp['water_albedo_k'] = float(sys.argv[1]); json.dump(sp, open('spec/marvel.json', 'w'), indent=1)
print('k', sys.argv[1])
