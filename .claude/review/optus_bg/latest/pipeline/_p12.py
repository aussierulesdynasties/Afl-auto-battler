s=open('scene.py',encoding='utf-8').read()
old="if os.path.exists(_sg): bpy.ops.import_scene.gltf(filepath=_sg)   # 3D seats ship as a second file"
new=old+'''
_sd = glb.replace('.glb', '_seats')   # Oval3D loader format: seat_tmpl.bin (one seat, float32 xyz tris) + one 3x4 transform per seat
if os.path.isdir(_sd):
    _T = np.fromfile(os.path.join(_sd, 'seat_tmpl.bin'), np.float32).reshape(-1, 3)
    _SC = {'lo_blue': (0.802, 0.807, 0.841), 'lo_tan': (0.892, 0.824, 0.751), 'mid_blue': (0.920, 0.858, 0.794),
           'mid_tan': (1.0, 0.875, 0.704), 'up_blue': (0.653, 0.705, 0.782), 'up_tan': (0.743, 0.722, 0.693)}   # Oval3D.gd SEAT_COLOURS (sRGB)
    for _k, _c in _SC.items():
        _M = np.fromfile(os.path.join(_sd, 'seats_seat_%s.bin' % _k), np.float32).reshape(-1, 3, 4)
        _W = np.einsum('nij,vj->nvi', _M[:, :, :3], _T) + _M[:, None, :, 3]
        _W = np.stack([_W[..., 0], -_W[..., 2], _W[..., 1]], -1).reshape(-1, 3)   # Godot Y-up -> Blender Z-up
        _F = np.arange(len(_W)).reshape(-1, 3)
        _me = bpy.data.meshes.new('seats_' + _k); _me.from_pydata(_W.tolist(), [], _F.tolist())
        _o = bpy.data.objects.new('seats_' + _k, _me); bpy.context.scene.collection.objects.link(_o)
        _mt = bpy.data.materials.new('seat_' + _k); _mt.use_nodes = True
        _mt.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = tuple(lin(np.array(_c) * 255)) + (1,) if False else tuple(float(((v + 0.055) / 1.055) ** 2.4) for v in _c) + (1,)
        _mt.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.55
        _me.materials.append(_mt)
        print('seats', _k, len(_M))'''
assert old in s; open('scene.py','w',encoding='utf-8',newline='').write(s.replace(old,new,1))
