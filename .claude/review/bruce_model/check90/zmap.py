# blender -b -P zmap.py -- in.glb out.npy [H=250] [n=1000]: height (Blender Z, m) of the top surface on an n x n grid, row 0 = north
import bpy,sys,numpy as np,bmesh
from mathutils.bvhtree import BVHTree
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:];H=float(a[2]) if len(a)>2 else 250.0;n=int(a[3]) if len(a)>3 else 1000
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
bm=bmesh.new()
for o in bpy.context.scene.objects:
    if o.type=='MESH':
        t=bmesh.new();t.from_mesh(o.data);t.transform(o.matrix_world);me=bpy.data.meshes.new('t');t.to_mesh(me);bm.from_mesh(me);t.free()
bvh=BVHTree.FromBMesh(bm);Z=np.full((n,n),np.nan,np.float32);m=2*H/n;d=Vector((0,0,-1))
for j in range(n):
    y=H-(j+0.5)*m
    for i in range(n):
        h=bvh.ray_cast(Vector((-H+(i+0.5)*m,y,300.0)),d)
        if h[0] is not None:Z[j,i]=h[0].z
np.save(a[1],Z);print('ZMAX',np.nanmax(Z))
