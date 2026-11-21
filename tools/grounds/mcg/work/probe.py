import sys,os;sys.path.insert(0,'model');sys.path.insert(0,'work')
import bpy,mathutils,build
build.build_all()
for ob in bpy.context.scene.objects:
    if ob.type=='MESH':
        ob.matrix_world = mathutils.Matrix(((1,0,0.22,0),(0,1,0.39,0),(0,0,1,0),(0,0,0,1))) @ ob.matrix_world
bpy.context.view_layer.update()
ob=bpy.data.objects['towers'];print('PARENT',ob.parent,ob.matrix_world)
zs=max(ob.data.vertices,key=lambda v:v.co.z);print('TOPV',zs.co,ob.matrix_world@zs.co)
print([ (o.name,o.parent.name if o.parent else None) for o in bpy.context.scene.objects][:20])
