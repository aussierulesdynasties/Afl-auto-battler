import bpy,sys,mathutils,numpy as np

O=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+'optus_roof11.glb')
sc=bpy.context.scene;dg=bpy.context.evaluated_depsgraph_get()
M=np.load(O+'mask.npy')
import collections;C=collections.Counter();n=0
# find dark px inside roof: dark pixel with white px 3 left and 3 right or up/down
for v in range(2,1838,1):
    row=M[v]
    for u in np.where(~row[3:-3]&row[:-6]&row[6:])[0]+3:
        x=-260+u*0.25;y=230-v*0.25
        hit,loc,nr,fi,ob,_=sc.ray_cast(dg,mathutils.Vector((x,y,100)),mathutils.Vector((0,0,-1)))
        k=ob.data.materials[ob.data.polygons[fi].material_index].name if hit else 'MISS';C[(k,round(loc.z) if hit else 0)]+=1;n+=1
print('N',n,C.most_common(15))
