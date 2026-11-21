p='scene.py'; s=open(p).read()
s=s.replace("""def mat_facade(""","""def mat_mul(nm, path, rough=0.8):
    \"\"\"one base-colour texture x the vertex colour (the tint), as the trees do; glTF: baseColorTexture x COLOR_0.\"\"\"
    m = mat_vcol(nm, rough); nt = m.node_tree; b = nt.nodes['Principled BSDF']; vc = b.inputs['Base Color'].links[0].from_socket
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path)
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    nt.links.new(vc, mx.inputs[6]); nt.links.new(t.outputs['Color'], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    return m
def mat_facade(""",1)
s=s.replace("""    ob = mk_obj('bg_bld_' + cls, verts, faces, mat_facade('facade_' + cls, os.path.join(HERE, 'tex', tex)))""","""    fm = mat_mul('facade_' + cls, os.path.join(HERE, 'tex', tex), 0.5) if tex == 'city_office.png' else mat_facade('facade_' + cls, os.path.join(HERE, 'tex', tex))
    ob = mk_obj('bg_bld_' + cls, verts, faces, fm)""")
s=s.replace("""        ro = mk_obj('bg_roof_%s_%s' % (cls, kind), rv, rf, mat_facade('roof_%s_%s' % (cls, kind), os.path.join(HERE, 'tex', 'roof_%s.png' % kind)))""","""        rtex = spec.get('roof_metal_tex', 'roof_metal.png') if kind == 'metal' else 'roof_%s.png' % kind   # traeger: roof_corrugated.png (3.04 m tile)
        rmat = mat_mul('roof_%s_%s' % (cls, kind), os.path.join(HERE, 'tex', rtex), 0.6) if rtex == 'roof_corrugated.png' else mat_facade('roof_%s_%s' % (cls, kind), os.path.join(HERE, 'tex', rtex))
        ro = mk_obj('bg_roof_%s_%s' % (cls, kind), rv, rf, rmat)""")
s=s.replace("""build_class('tower', 'tower.png', 3.0, 3.6)""","""build_class('tower', 'city_office.png', 3.0, 3.6)   # curtain wall: one tile = 3.0 m bay x 3.6 m floor""")
open(p,'w').write(s)
import json; p='spec/traeger.json'; j=json.load(open(p)); j['roof_metal_tex']='roof_corrugated.png'; json.dump(j,open(p,'w'),indent=1)
