c = open('scene.py', encoding='utf-8').read()
a = "bpy.ops.import_scene.gltf(filepath=glb)\n"
assert c.count(a) == 1
c = c.replace(a, a + "_sg = glb.replace('.glb', '_seats.glb')\nif os.path.exists(_sg): bpy.ops.import_scene.gltf(filepath=_sg)   # 3D seats ship as a second file\n")
open('scene.py', 'w', encoding='utf-8', newline='').write(c); print('ok')
