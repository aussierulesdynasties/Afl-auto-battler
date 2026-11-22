s=open('scene.py',newline='').read()
a="bpy.ops.import_scene.gltf(filepath=glb)"
assert s.count(a)==1
s=s.replace(a,"if os.path.exists(glb): bpy.ops.import_scene.gltf(filepath=glb)\nelse: print('NO GROUND MODEL YET', glb)")
open('scene.py','w',newline='').write(s)
