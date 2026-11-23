import bpy
from mathutils import Vector
sc=bpy.context.scene; dg=bpy.context.evaluated_depsgraph_get()
cam=Vector((742.0-0,0,0))
import json
j=json.load(open('out/gmhba/job_tw_g.json'))['views'][0]
c=Vector(j['cam']); l=Vector(j['look'])
for dz in (-30,-40,-50):
    d=(l+Vector((0,0,dz))-c).normalized(); r=sc.ray_cast(dg,c,d)
    print('HIT',dz,r[0], r[4].name if r[0] else None)
for o in bpy.data.objects:
    if o.name.startswith('bg_roof_block'): print('OBJ',o.name,len(o.data.polygons))
