import bpy,bmesh,json,sys
D=sys.argv[-1];IZ=json.load(open(D+'../obuild/geom.json'))['iz']
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=D+'optus_roof6.glb')
me=bpy.data.objects['optus'].data;names=[m.name for m in me.materials];ie=names.index('roof_edge')
bm=bmesh.new();bm.from_mesh(me);n=0
for v in set(v for f in bm.faces if f.material_index==ie for v in f.verts):
    if v.co.z>IZ-0.02:v.co.z=IZ-0.02;n+=1
bm.to_mesh(me);print('MOVED',n)
bpy.ops.export_scene.gltf(filepath=D+'optus_roof7.glb',export_format='GLB')
