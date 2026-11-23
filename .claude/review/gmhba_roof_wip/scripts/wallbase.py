import bpy,bmesh,sys,math,json
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
o=bpy.data.objects['gmhba'];M=o.matrix_world;names=[s.material.name for s in o.material_slots]
bm=bmesh.new();bm.from_mesh(o.data);V={}
for f in bm.faces:
  if names[f.material_index]!='wall':continue
  for v in f.verts:
    p=M@v.co
    if p.z<0.3:V[(round(p.x,2),round(p.y,2))]=1
pts=list(V);
# outer ones: radius from oval centre (-6,-11) > 85
pts=[p for p in pts if math.hypot(p[0]+6,p[1]+11)>85]
json.dump(pts,open(out,'w'));print('WB',len(pts))
