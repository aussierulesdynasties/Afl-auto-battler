import bpy,os,sys,json
S=r'C:/Users/DANTE/AppData/Local/Temp/claude/4a2d69a2e2816321/2e119eb6-c1b8-4f9d-a827-983cffaeebc1/scratchpad'
out=sys.argv[-1]
for o in [o for o in bpy.data.objects if o.name.startswith('ground_grass')]:print('DEL',o.name);bpy.data.objects.remove(o,do_unlink=True)
exec(open(os.path.join(S,'ring.py')).read())
fence=[p for p in json.load(open(os.path.join(S,'prims.json'))) if p['name']=='fence_ring'][0]['pts']
T=json.load(open(os.path.join(S,'tex3','tex.json')));tile=(T.get('tile',T).get('grass_out') if isinstance(T.get('tile',T),dict) else None) or (6,6)
print('RING m2',round(ring_mesh(bpy.data.objects['ground_dirt'].data,[(-140,-135),(140,-135),(140,135),(-140,135)],fence,-0.05,tile)),'rect',280*270,'tile',tile)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,'traeger.blend'),relative_remap=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(out,'traeger.glb'),export_format='GLB',export_cameras=False,export_lights=False);print('SAVED11')
