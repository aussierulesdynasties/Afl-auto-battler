import bpy,math,json,sys
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath='optus_roof11.glb')
J=json.load(open('../obuild/geom.json'));oc=J['oc']
for o in bpy.data.objects:
    if o.type!='MESH':continue
    me=o.data;uv=me.uv_layers.active
    if not uv:continue
    for si,m in enumerate(me.materials):
        if m and m.name.startswith('roof_bay'):
            s=[]
            for p in me.polygons:
                if p.material_index!=si:continue
                for li in p.loop_indices:
                    v=o.matrix_world@me.vertices[me.loops[li].vertex_index].co
                    s.append((round(math.degrees(math.atan2(v.y-oc[1],v.x-oc[0]))%360,2),round(uv.data[li].uv[0],3),round(uv.data[li].uv[1],3)))
            s=sorted(set(s));print('N',len(s),o.name,m.name);print(s[:30:3]);print(s[-10:])
