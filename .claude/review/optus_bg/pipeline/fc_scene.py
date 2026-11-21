# exec'd from scene.py: the forecourt overlay (forecourt.png, 0.1 m/px, made by fc_overlay.py) on a 2 m grid draped 6 cm above the terrain.
_fj = os.path.join(D, 'forecourt.json')
if os.path.exists(_fj):
    _b = json.load(open(_fj))
    _nx = int((_b['x1'] - _b['x0']) / 2) + 1; _ny = int((_b['y1'] - _b['y0']) / 2) + 1
    _gx, _gy = np.meshgrid(np.linspace(_b['x0'], _b['x1'], _nx), np.linspace(_b['y0'], _b['y1'], _ny))
    _xy = np.column_stack([_gx.ravel(), _gy.ravel()])
    _z = drape(_xy) + 0.06
    _F = [(j * _nx + i, j * _nx + i + 1, (j + 1) * _nx + i + 1, (j + 1) * _nx + i) for j in range(_ny - 1) for i in range(_nx - 1)]
    _m = bpy.data.materials.new('forecourt'); _m.use_nodes = True; _nt = _m.node_tree; _bs = _nt.nodes['Principled BSDF']
    _t = _nt.nodes.new('ShaderNodeTexImage'); _t.image = bpy.data.images.load(os.path.join(D, 'forecourt.png')); _t.interpolation = 'Cubic'
    _nt.links.new(_t.outputs['Color'], _bs.inputs['Base Color']); _nt.links.new(_t.outputs['Alpha'], _bs.inputs['Alpha'])
    _bs.inputs['Roughness'].default_value = 0.85
    _o = mk_obj('forecourt', np.column_stack([_xy, _z]), _F, _m)
    _me = _o.data; _lv = np.empty(len(_me.loops), np.int32); _me.loops.foreach_get('vertex_index', _lv)
    _uv = np.column_stack([(_xy[:, 0] - _b['x0']) / (_b['x1'] - _b['x0']), (_xy[:, 1] - _b['y0']) / (_b['y1'] - _b['y0'])])[_lv]
    _me.uv_layers.new(name='UVMap').data.foreach_set('uv', _uv.astype(np.float32).ravel())
    print('forecourt overlay', _nx, _ny)
