s = open('scene.py', newline='').read()
anchor = "    m_park = mat_img_vc('park_asphalt', _tint(PAL['parking'], 'road_asphalt_park.png'), 0.92)"
add = r"""
    # texture session 2026-11-20 (Mars): road_asphalt_v2 at 8 m + repeat break (2nd sample 0.37x scale, rot 36.87, 50/50,
    # contrast x1.414) faded to the mean from 150 to 400 m. Live nodes for renders; GODOT TODO: same in the road shader.
    def _rbreak(m, rgb):
        nt = m.node_tree; b = nt.nodes['Principled BSDF']; t = [x for x in nt.nodes if x.type == 'TEX_IMAGE'][0]
        mul = [x for x in nt.nodes if x.type == 'MIX'][0]
        t.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'road_asphalt.png'), check_existing=True)   # = road_asphalt_v2.png (md5 a6040f66)
        uvn = nt.nodes.new('ShaderNodeUVMap')
        m1 = nt.nodes.new('ShaderNodeMapping'); m1.inputs['Scale'].default_value = (TILE / 8.0,) * 3
        nt.links.new(uvn.outputs['UV'], m1.inputs['Vector']); nt.links.new(m1.outputs['Vector'], t.inputs['Vector'])
        m2 = nt.nodes.new('ShaderNodeMapping'); m2.inputs['Scale'].default_value = (TILE * 0.37 / 8.0,) * 3; m2.inputs['Rotation'].default_value = (0, 0, math.radians(36.87))
        nt.links.new(uvn.outputs['UV'], m2.inputs['Vector'])
        t2 = nt.nodes.new('ShaderNodeTexImage'); t2.image = t.image; nt.links.new(m2.outputs['Vector'], t2.inputs['Vector'])
        avg = nt.nodes.new('ShaderNodeMix'); avg.data_type = 'RGBA'; avg.inputs['Factor'].default_value = 0.5
        nt.links.new(t.outputs['Color'], avg.inputs[6]); nt.links.new(t2.outputs['Color'], avg.inputs[7])
        MEAN = (0.4248, 0.4248, 0.4248, 1)   # linear mean of road_asphalt_v2
        ct = nt.nodes.new('ShaderNodeMix'); ct.data_type = 'RGBA'; ct.clamp_factor = False; ct.clamp_result = True; ct.inputs['Factor'].default_value = 1.414
        ct.inputs[6].default_value = MEAN; nt.links.new(avg.outputs[2], ct.inputs[7])
        cd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange')
        mr.inputs['From Min'].default_value = 150.0; mr.inputs['From Max'].default_value = 400.0; nt.links.new(cd.outputs['View Distance'], mr.inputs['Value'])
        fd = nt.nodes.new('ShaderNodeMix'); fd.data_type = 'RGBA'; fd.inputs[7].default_value = MEAN
        nt.links.new(mr.outputs['Result'], fd.inputs['Factor']); nt.links.new(ct.outputs[2], fd.inputs[6])
        col = nt.nodes.new('ShaderNodeMix'); col.data_type = 'RGBA'; col.blend_type = 'MULTIPLY'; col.inputs['Factor'].default_value = 1.0
        col.inputs[7].default_value = (*[c / 0.4248 for c in lin(rgb)], 1)   # palette colour x detail / its mean
        nt.links.new(fd.outputs[2], col.inputs[6]); nt.links.new(col.outputs[2], mul.inputs[6])
    _rbreak(m_road, PAL['road']); _rbreak(m_park, PAL['parking'])"""
assert anchor in s; s = s.replace(anchor, anchor + add.replace('\n', '\r\n' if '\r\n' in s else '\n'), 1)
open('scene.py', 'w', newline='').write(s); print('patched')
