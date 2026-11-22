import bpy
try:
    r=bpy.ops.import_scene.gltf(filepath='ground/accor.glb'); print('IMPRES',r)
except Exception as e: print('IMPERR',repr(e)[:500])
print('NOBJ',len(bpy.data.objects))
