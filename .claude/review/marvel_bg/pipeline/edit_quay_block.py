"""Texture session 2026-11-20: quay = adl_bluestone (3.6 x 3.2 m) on concrete (150,148,142) with a 0.4 m dark wet band
(x0.55) above the waterline; blocks (not sheds) = city_office at 3.2 m floors (bay 2.67 m keeps the 3.0x3.6 aspect)."""
import json
P = 'scene.py'; s = open(P, newline='').read(); nl = '\r\n' if '\r\n' in s else '\n'
def rep(a, b):
    global s
    a = a.replace('\n', nl); b = b.replace('\n', nl); assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
rep("        bb.inputs['Base Color'].default_value = (*lin((118, 114, 106)), 1); bb.inputs['Roughness'].default_value = 0.9; return m\n",
    "        nt = m.node_tree; bb.inputs['Roughness'].default_value = 0.9\n"
    "        uv = nt.nodes.new('ShaderNodeUVMap'); sc = nt.nodes.new('ShaderNodeVectorMath'); sc.operation = 'MULTIPLY'\n"
    "        sc.inputs[1].default_value = (4.0 / 3.6, 4.0 / 3.2, 1)   # mesh UVs: 4 m per unit\n"
    "        tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'adl_bluestone.png'))\n"
    "        nt.links.new(uv.outputs['UV'], sc.inputs[0]); nt.links.new(sc.outputs[0], tx.inputs['Vector'])\n"
    "        c1 = nt.nodes.new('ShaderNodeMix'); c1.data_type = 'RGBA'; c1.blend_type = 'MULTIPLY'; c1.inputs[0].default_value = 1\n"
    "        c1.inputs[6].default_value = (*(lin((150, 148, 142)) * 255 / 152.9), 1)   # texture mean 152.9 -> keeps (150,148,142)\n"
    "        nt.links.new(tx.outputs['Color'], c1.inputs[7])\n"
    "        gz = nt.nodes.new('ShaderNodeNewGeometry'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(gz.outputs['Position'], sp.inputs[0])\n"
    "        lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = WZ + 0.4; nt.links.new(sp.outputs['Z'], lt.inputs[0])\n"
    "        wet = nt.nodes.new('ShaderNodeMix'); wet.data_type = 'RGBA'; wet.blend_type = 'MULTIPLY'; wet.inputs[7].default_value = (0.55, 0.55, 0.55, 1)\n"
    "        nt.links.new(lt.outputs[0], wet.inputs[0]); nt.links.new(c1.outputs[2], wet.inputs[6]); nt.links.new(wet.outputs[2], bb.inputs['Base Color'])\n"
    "        return m\n")
rep("build_class('block', 'wall.png', 3.6, 3.2)\n",
    "if 'block_tex' in spec:\n"
    "    build_class('block', *spec['block_tex'], sel=lambda b: 'rc' not in b)\n"
    "    build_class('block', 'wall.png', 3.6, 3.2, sel=lambda b: 'rc' in b, tag='_shed')\n"
    "else: build_class('block', 'wall.png', 3.6, 3.2)\n")
open(P, 'w', newline='').write(s)
J = json.load(open('spec/marvel.json')); J['block_tex'] = ['city_office.png', 2.67, 3.2]
json.dump(J, open('spec/marvel.json', 'w'), indent=1); print('ok')
