import bpy, math, mathutils, sys
sc=bpy.context.scene; dg=bpy.context.evaluated_depsgraph_get()
def probe(i,px,py,W=1280,H=720,r=520,z=190,start=90,fovh=60,n=8,look=(0,0,10)):
    a=math.radians(start+360*i/n); eye=mathutils.Vector((r*math.cos(a),r*math.sin(a),z)); L=mathutils.Vector(look)
    f=(L-eye).normalized(); rt=f.cross(mathutils.Vector((0,0,1))).normalized(); up=rt.cross(f)
    t=math.tan(math.radians(fovh)/2); dx=(px/W*2-1)*t; dy=(1-py/H*2)*t*H/W
    d=(f+rt*dx+up*dy).normalized(); hit,loc,nrm,idx,ob,_=sc.ray_cast(dg,eye,d)
    print('PROBE',i,px,py,ob.name if ob else None, tuple(round(v,1) for v in loc), ob.active_material.name if ob and ob.active_material else '', round(nrm.z,2))
for p in [(89,x,y,1280,720,520,190,90,60,240) for x,y in ((925,550),(935,560),(940,545),(930,570),(945,575))]: probe(*p)
