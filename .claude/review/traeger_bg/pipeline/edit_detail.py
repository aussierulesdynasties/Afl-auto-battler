p='scene.py'; s=open(p,newline='').read()
old="ob = mk_obj('bg_near_ground', V, F.tolist(), mat_img('ground', os.path.join(D, 'ground.png'), 0.8))"
new="""gm = mat_img('ground', os.path.join(D, 'ground.png'), 0.8)
_nt = gm.node_tree; _b = _nt.nodes['Principled BSDF']; _base = _b.inputs['Base Color'].links[0].from_socket
_dt = _nt.nodes.new('ShaderNodeTexImage'); _dt.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'ground_detail.png'))
_mp = _nt.nodes.new('ShaderNodeMapping'); _tc = _nt.nodes.new('ShaderNodeTexCoord')
_mp.inputs['Scale'].default_value = (2 * NE / 4.0, 2 * NE / 4.0, 1)   # one detail tile = 4 m
_nt.links.new(_tc.outputs['UV'], _mp.inputs['Vector']); _nt.links.new(_mp.outputs['Vector'], _dt.inputs['Vector'])
_mx = _nt.nodes.new('ShaderNodeMix'); _mx.data_type = 'RGBA'; _mx.blend_type = 'MULTIPLY'; _mx.inputs['Factor'].default_value = 1.0
_nt.links.new(_base, _mx.inputs[6]); _nt.links.new(_dt.outputs['Color'], _mx.inputs[7])
_lift = _nt.nodes.new('ShaderNodeMix'); _lift.data_type = 'RGBA'; _lift.blend_type = 'MULTIPLY'; _lift.inputs['Factor'].default_value = 1.0
_lift.inputs[7].default_value = (1.21, 1.21, 1.21, 1)   # 1 / detail mean 0.826 keeps the painted value
_nt.links.new(_mx.outputs[2], _lift.inputs[6]); _nt.links.new(_lift.outputs[2], _b.inputs['Base Color'])
ob = mk_obj('bg_near_ground', V, F.tolist(), gm)"""
assert old in s; s=s.replace(old,new); open(p,'w',newline='').write(s); print('ok')
