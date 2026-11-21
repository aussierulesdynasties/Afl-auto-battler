import os
H = os.path.dirname(os.path.abspath(__file__))
def edit(f, pairs):
    p = os.path.join(H, f); s = open(p, encoding='utf-8', newline='').read()
    for a, b in pairs:
        assert s.count(a) == 1, a[:50]; s = s.replace(a, b)
    open(p, 'w', encoding='utf-8', newline='').write(s)
edit('scene.py', [
 # trees: no lift node; the x1.15 goes into the vertex colours (vcol x texture is what glTF carries)
 ("""    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    nt.links.new(vc, mx.inputs[6]); nt.links.new(lt.outputs['Color'], mx.inputs[7])
    lf = nt.nodes.new('ShaderNodeMix'); lf.data_type = 'RGBA'; lf.blend_type = 'MULTIPLY'; lf.inputs['Factor'].default_value = 1.0
    lf.inputs[7].default_value = (1.15, 1.15, 1.15, 1)   # texture stores the clump multiplier / 1.15
    nt.links.new(mx.outputs[2], lf.inputs[6]); nt.links.new(lf.outputs[2], b.inputs['Base Color'])
""", """    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    nt.links.new(vc, mx.inputs[6]); nt.links.new(lt.outputs['Color'], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
"""),
 ("    set_corner_col(ob.data, np.concatenate([np.array(cols), np.ones((len(cols), 1))], 1))\nprint('trees built')",
  "    cols = np.array(cols) * 1.15   # texture stores the clump multiplier / 1.15; the x1.15 lives in the vertex colours\n    if cols.max() > 1: print('WARN tree colour over 1', kn, cols.max())\n    set_corner_col(ob.data, np.concatenate([np.clip(cols, 0, 1), np.ones((len(cols), 1))], 1))\nprint('trees built')"),
 ("    set_uv_box(ob.data, 2.8 / 8)   # leaf_clumps.png tile = 8 cells of 1/2.8 m", "    set_uv_box(ob.data, 2.8 / 16)   # leaf_clumps.png tile = 8 cells of 2/2.8 m (cells doubled to match the old blotch size)"),
 # courts: x1.25 folded into the colour that multiplies the texture (exported as baseColorFactor)
 ("        mx.inputs[6].default_value = (*[1.25 * c for c in srgb(rgb)], 1);",
  "        fc = [1.25 * c for c in srgb(rgb)]\n        if max(fc) > 1: print('WARN court colour over 1, clamped', nm, fc)\n        mx.inputs[6].default_value = (*[min(1.0, c) for c in fc], 1);"),
])
