import bpy, math
from mathutils import Vector
sc=bpy.context.scene; dg=bpy.context.evaluated_depsgraph_get()
def shoot(cam,look,fov,W,H,px,py):
    c=Vector(cam); f=(Vector(look)-c).normalized(); r=f.cross(Vector((0,0,1))).normalized(); u=r.cross(f)
    t=math.tan(math.radians(fov)/2); x=(2*px/W-1)*t; y=(1-2*py/H)*t*H/W
    d=(f+r*x+u*y).normalized(); h,loc,n,i,ob,m=sc.ray_cast(dg,c,d)
    return (ob.name if h else None, tuple(round(v,1) for v in loc) if h else None, ob.active_material.name if h and ob.active_material else None)
for px,py in [(100,700),(200,800),(300,650),(150,900)]: print('street',px,py,shoot((-95,-345,1.7),(-18.58,-280.88,-5.28),70,1280,960,px,py))
for px,py in [(850,350),(900,450),(700,500)]: print('f270',px,py,shoot((0,-152.8,22.0),(0,-107.8,4),60,960,540,px,py))
for px,py in [(860,281),(915,301),(767,262),(763,260)]: print("f315",px,py,shoot((102.3,-102.3,22),(70.5,-70.5,4),60,960,540,px,py))
