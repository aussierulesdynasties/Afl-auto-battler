p='scene.py'; s=open(p,newline='').read()
o="    _nt.links.new(_t.outputs['Color'], _fd.inputs[6]); _nt.links.new(_fd.outputs[2], _mu.inputs[7])\n"
n=o.replace("_nt.links.new(_fd.outputs[2], _mu.inputs[7])\n","") + """    _tm = _nt.nodes.new('ShaderNodeTexImage'); _tm.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'mt', 'suburb_macro.png'))   # km-scale neighbourhood tones, roads, parks: 1 tile = 4 km
    _uv = _nt.nodes.new('ShaderNodeTexCoord'); _mp = _nt.nodes.new('ShaderNodeMapping'); _mp.inputs['Scale'].default_value = (0.125, 0.125, 1)
    _nt.links.new(_uv.outputs['UV'], _mp.inputs['Vector']); _nt.links.new(_mp.outputs['Vector'], _tm.inputs['Vector'])
    _mm = _nt.nodes.new('ShaderNodeMix'); _mm.data_type = 'RGBA'; _mm.blend_type = 'MULTIPLY'; _mm.inputs[0].default_value = 1
    _nt.links.new(_fd.outputs[2], _mm.inputs[6]); _nt.links.new(_tm.outputs['Color'], _mm.inputs[7])
    _gm = _nt.nodes.new('ShaderNodeVectorMath'); _gm.operation = 'SCALE'; _gm.inputs['Scale'].default_value = 1 / float(open(os.path.join(HERE, 'tex', 'mt', 'suburb_macro.mean')).read())
    _nt.links.new(_mm.outputs[2], _gm.inputs[0]); _nt.links.new(_gm.outputs[0], _mu.inputs[7])
"""
assert o in s; s=s.replace(o,n); open(p,'w',newline='').write(s)
