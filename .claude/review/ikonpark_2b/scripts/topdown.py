# straight-down ortho render, optional satellite lean shear (x+=k*dx*z, y+=k*dy*z)
# blender -b -P topdown.py -- GLB OUT.png CX CY HALF RES K DX DY
import bpy,sys,math
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
glb,out=a[0],a[1];CX,CY,HALF,RES,K,DX,DY=map(float,a[2:9])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
for ob in list(bpy.context.scene.objects):
  if ob.type!='MESH': continue
  M=ob.matrix_world.copy();Mi=M.inverted()
  for v in ob.data.vertices:
    w=M@v.co; w=Vector((w.x+K*DX*w.z,w.y+K*DY*w.z,w.z)); v.co=Mi@w
cam=bpy.data.cameras.new('c');cam.type='ORTHO';cam.ortho_scale=2*HALF;cam.clip_end=2000
co=bpy.data.objects.new('c',cam);bpy.context.scene.collection.objects.link(co)
co.location=(CX,CY,500)
sc=bpy.context.scene;sc.camera=co;n=int(2*HALF/RES)
sc.render.resolution_x=n;sc.render.resolution_y=n;sc.render.engine='BLENDER_EEVEE';sc.render.film_transparent=True
sun=bpy.data.lights.new('s','SUN');sun.energy=3.5;so=bpy.data.objects.new('s',sun);sc.collection.objects.link(so);so.rotation_euler=(math.radians(30),0,math.radians(-30))
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Strength'].default_value=0.8
sc.view_settings.view_transform='Standard';sc.render.filepath=out
bpy.ops.render.render(write_still=True)
