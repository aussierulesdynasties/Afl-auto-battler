p='scene.py'; s=open(p,newline='').read()
old="    ob = mk_obj('bg_trees_' + kn, verts, faces, mat_vcol('tree_' + kn, 0.9))"
new="""    tm = mat_vcol('tree_' + kn, 0.9); nt = tm.node_tree; b = nt.nodes['Principled BSDF']; vc = b.inputs['Base Color'].links[0].from_socket
    # leaf clumps (procedural, hand-set): Voronoi cells ~0.35 m darken their edges and bump the crown so it reads as foliage
    tc = nt.nodes.new('ShaderNodeTexCoord'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 2.8
    vo.feature = 'F1'; nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Max'].default_value = 0.6; mr.inputs['To Min'].default_value = 1.15; mr.inputs['To Max'].default_value = 0.62
    nt.links.new(vo.outputs['Distance'], mr.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    nt.links.new(vc, mx.inputs[6]); nt.links.new(mr.outputs['Result'], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6; nt.links.new(vo.outputs['Distance'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    ob = mk_obj('bg_trees_' + kn, verts, faces, tm)
    ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))"""
assert old in s; s=s.replace(old,new); open(p,'w',newline='').write(s); print('ok')
