import bpy, json, math
from mathutils import Vector
j=json.load(open('out/mars/job_fence_g.json')); v=[x for x in j['views'] if x['name']=='fence_270'][0]
sc=bpy.context.scene; dg=bpy.context.evaluated_depsgraph_get()
o=Vector(v['cam']); f=(Vector(v['look'])-o).normalized(); r=f.cross(Vector((0,0,1))).normalized(); u=r.cross(f)
t=math.tan(math.radians(v['fov_h'])/2); W,H=960,540
for px,py in [(500,380),(800,400),(400,330),(600,200),(100,400),(900,430)]:
    x=(px/W*2-1)*t; y=-(py/H*2-1)*t*H/W; d=(f+r*x+u*y).normalized()
    hit,loc,n,i,ob,m=sc.ray_cast(dg,o,d)
    mat=None
    if hit and ob.type=='MESH' and ob.material_slots: mat=ob.material_slots[ob.data.polygons[i].material_index].material.name if i<len(ob.data.polygons) else '?'
    print('PROBE',px,py,ob.name if hit else None,mat,tuple(round(c,2) for c in loc),tuple(round(c,2) for c in n))
