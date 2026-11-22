import bpy,bmesh,sys,json
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
o=bpy.data.objects['gmhba'];M=o.matrix_world;names=[s.material.name for s in o.material_slots]
bm=bmesh.new();bm.from_mesh(o.data);segs=[]
for e in bm.edges:
  fs=[f for f in e.link_faces if names[f.material_index] in ('pave','turf','line','pad')]
  if len(fs)==1 or (len(fs)==2 and fs[0].material_index!=fs[1].material_index):
    a,b=M@e.verts[0].co,M@e.verts[1].co
    if a.z<0.5 and b.z<0.5:segs.append([a.x,a.y,b.x,b.y,names[fs[0].material_index]])
json.dump(segs,open(out,'w'));print('SEGS',len(segs))
