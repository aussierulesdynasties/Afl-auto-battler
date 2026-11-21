import bpy
H='D:/Temp/claude/2117a0e07442304a/b457f311-065b-4525-9ffd-7c62765dd586/scratchpad/obuild/hout/'
def ex(fn,keep):
    for o in bpy.data.objects:o.select_set(keep(o))
    bpy.ops.export_scene.gltf(filepath=H+fn,export_format='GLB',use_selection=True,export_apply=True)
ex('optus_stadium.glb',lambda o:o.name!='seats3d')
