# Bay water (exec'd by scene.py when spec['coast_v2']): 250 m grid at the sea plane, vertex colour shallow teal at the shore
# to deep blue 600 m out (signed distance to the OSM coastline), hand-made ripple tile tex/mt/water.png (80 m) multiplied
# over it, ripple normal map for the sky glints, low roughness.
_g = np.linspace(-FA, FA, 481); _GX, _GY = np.meshgrid(_g, _g); _wq = np.stack([_GX.ravel(), _GY.ravel(), np.full(_GX.size, ZSEA + 1.2)], 1)
_i = np.arange(480); _I, _J = np.meshgrid(_i, _i); _a = (_J * 481 + _I).ravel(); _wf4 = np.stack([_a, _a + 1, _a + 482, _a + 481], 1)
_r = np.hypot(_wq[:, 0], _wq[:, 1]); _dd = np.full(len(_wq), -5000.0); _cl = _r < 20000; _dd[_cl] = COAST_SD(_wq[_cl, :2])
_t = np.clip(-_dd / 600.0, 0, 1)[:, None]
_wc = np.array(lin((70, 112, 118)))[None, :3] * (1 - _t) + np.array(lin((30, 58, 82)))[None, :3] * _t
_WC = np.load(os.path.join(HERE, 'data', name, 'water_col.npy')); _wr = np.clip(((FA - _wq[:, 1]) / 30).astype(int), 0, 1999); _wcl = np.clip(((_wq[:, 0] + FA) / 30).astype(int), 0, 1999)
_LU = np.load(os.path.join(HERE, 'data', name, 'landuse.npy')); _ref = (_WC[_LU == 3].mean(0) / 255.0) ** 2.2
_ms = ((_WC[_wr, _wcl] / 255.0) ** 2.2) / _ref   # measured tone relative to the bay mean: shallows, banks, channels
_wc = _wc * np.clip(_ms, 0.5, 2.0)
_wh = (1 - np.exp(-_r / spec.get('haze_m', 22000)))[:, None] * 0.85
_wc = _wc * (1 - _wh) + np.array(lin(PAL['haze']))[None, :3] * _wh
_wm = mat_mul('far_water', os.path.join(HERE, 'tex', 'mt', 'water.png'), 0.3, 1 / float(open(os.path.join(HERE, 'tex', 'mt', 'water.mean')).read()))
_nt = _wm.node_tree; _b = _nt.nodes['Principled BSDF']; _b.inputs['Specular IOR Level'].default_value = 0.1
_ln = _nt.nodes.new('ShaderNodeTexImage'); _ln.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'mt', 'water_n.png')); _ln.image.colorspace_settings.name = 'Non-Color'
_nm = _nt.nodes.new('ShaderNodeNormalMap'); _nm.uv_map = 'UVMap'; _nm.inputs['Strength'].default_value = 0.6
_nt.links.new(_ln.outputs['Color'], _nm.inputs['Color']); _nt.links.new(_nm.outputs['Normal'], _b.inputs['Normal'])
_wo = mk_obj('bg_far_water', _wq.tolist(), _wf4.tolist(), _wm)
_l = _wf4.ravel(); set_corner_col(_wo.data, np.concatenate([_wc[_l], np.ones((len(_l), 1))], 1))
_c, _s = math.cos(0.3), math.sin(0.3); set_uv(_wo.data, np.stack([_wq[_l, 0] * _c - _wq[_l, 1] * _s, _wq[_l, 0] * _s + _wq[_l, 1] * _c], 1) / 80.0)
# ripples and glints fade out with distance: past ~3 km the 80 m tile aliases into white streaks at grazing angles
_wt = [n for n in _nt.nodes if n.type == 'TEX_IMAGE' and n.image and 'water.png' in n.image.filepath][0]; _wmu = [n for n in _nt.nodes if n.type == 'MIX'][0]
_wpx = np.array(_wt.image.pixels[:]).reshape(-1, 4)[:, :3]; _wmc = list((_wpx ** 2.2).mean(0)) + [1.0]
_wcd = _nt.nodes.new('ShaderNodeCameraData'); _wmr = _nt.nodes.new('ShaderNodeMapRange')
_wmr.inputs['From Min'].default_value = 1500; _wmr.inputs['From Max'].default_value = 6000
_wfd = _nt.nodes.new('ShaderNodeMix'); _wfd.data_type = 'RGBA'; _wfd.inputs[7].default_value = _wmc
_nt.links.new(_wcd.outputs['View Distance'], _wmr.inputs['Value']); _nt.links.new(_wmr.outputs['Result'], _wfd.inputs[0])
_nt.links.new(_wt.outputs['Color'], _wfd.inputs[6]); _nt.links.new(_wfd.outputs[2], _wmu.inputs[7])
_wns = _nt.nodes.new('ShaderNodeMapRange'); _wns.inputs['From Min'].default_value = 1500; _wns.inputs['From Max'].default_value = 6000; _wns.inputs['To Min'].default_value = 0.6; _wns.inputs['To Max'].default_value = 0.0
_nt.links.new(_wcd.outputs['View Distance'], _wns.inputs['Value']); _nt.links.new(_wns.outputs['Result'], _nm.inputs['Strength'])
