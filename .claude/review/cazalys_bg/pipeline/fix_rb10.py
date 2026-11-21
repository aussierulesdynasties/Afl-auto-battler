p='scene.py'; s=open(p,newline='').read()
a="    TILE = 8.0"; assert a in s
s=s.replace(a,"""    TILE = 104.0   # one seamless tile: asphalt at 8 m mixed with a rotated 20.8 m sample (mk_road_tex.py)
    from mathutils import noise as _nz
    def _mottle(me, co):   # 40 m noise (2 octaves, roughness 0.5) ramped 0.85-1.0 into vertex colour; glTF multiplies COLOR_0 into the base colour
        vi = np.zeros(len(me.loops), int); me.loops.foreach_get('vertex_index', vi); P_ = co[vi]
        n = np.array([_nz.noise(Vector((x / 40.0, y / 40.0, 0.5))) + 0.5 * _nz.noise(Vector((x / 20.0, y / 20.0, 7.5))) for x, y in P_[:, :2]]) / 1.5
        v = 0.85 + 0.15 * np.clip(n * 0.5 + 0.5, 0, 1)
        set_corner_col(me, np.stack([v, v, v, np.ones_like(v)], 1))
    def mat_img_vc(nm, path, rough):
        m = mat_img(nm, path, rough); nt = m.node_tree; b = nt.nodes['Principled BSDF']; t = [x for x in nt.nodes if x.type == 'TEX_IMAGE'][0]
        ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'Col'
        mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1
        nt.links.new(t.outputs['Color'], mul.inputs[6]); nt.links.new(ca.outputs['Color'], mul.inputs[7]); nt.links.new(mul.outputs[2], b.inputs['Base Color'])
        return m""")
for old,new in (("m_road = mat_img('road_asphalt'","m_road = mat_img_vc('road_asphalt'"),("m_park = mat_img('park_asphalt'","m_park = mat_img_vc('park_asphalt'")):
    assert old in s; s=s.replace(old,new)
a="set_uv(ob.data, co[vi, :2] / TILE)"; assert s.count(a)==1
s=s.replace(a,a+"; _mottle(ob.data, co)")
a="set_uv(ob.data, co[vi, :2] / tile)"; assert s.count(a)==1
s=s.replace(a,a+"\n            if mat is m_park: _mottle(ob.data, co)")
open(p,'w',newline='').write(s); print('ok')
