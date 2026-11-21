import bpy,sys
a=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
T={'SW':(-122.47,-59.21),'NW':(-58.45,107.55),'SE':(25.67,-119.74),'NE':(104.82,68.38)}
best={k:[] for k in T}
for o in bpy.data.objects:
  if o.type!='MESH':continue
  for v in o.data.vertices:
    w=o.matrix_world@v.co;x,y,z=w.x,-w.z,w.y  # glTF y-up -> model z-up handled below
    for k,(tx,ty) in T.items():
      for (X,Y,Z) in((w.x,w.y,w.z),):
        if abs(X-tx)<25 and abs(Y-ty)<25 and Z>73.5:best[k].append((X,Y,Z))
print('TOPS',{k:tuple(round(sum(c)/len(c),2) for c in zip(*v)) for k,v in best.items() if v})
