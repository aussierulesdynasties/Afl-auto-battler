# Orthographic straight-down render, north up, 0.25 m/px over X0..X1, Y0..Y1. Usage: blender -b X.blend --python topdown.py -- OUT.png
import bpy,sys,math
from mathutils import Vector,Euler,Matrix
import os
LV=[float(v) for v in os.environ.get('LEAN','0,0').split(',')]
# LEAN=vx,vy: shear x+=vx*z, y+=vy*z so the render leans like the satellite photo (tall parts shift with height)
SH=Matrix(((1,0,LV[0],0),(0,1,LV[1],0),(0,0,1,0),(0,0,0,1)))
for o in bpy.context.scene.objects:
    if o.type=='MESH':   # object transforms cannot hold a shear (Blender drops it), so shear the mesh data in world space
        M=o.matrix_world.copy();o.data.transform(M);o.matrix_world=Matrix.Identity(4);o.data.transform(SH)
out=sys.argv[sys.argv.index('--')+1]
X0,X1,Y0,Y1,R=-260,240,-230,230,0.25
sc=bpy.context.scene;cd=bpy.data.cameras.new('top');cd.type='ORTHO';cd.ortho_scale=X1-X0;cd.sensor_fit='HORIZONTAL';cd.clip_end=1000
cam=bpy.data.objects.new('top',cd);sc.collection.objects.link(cam);sc.camera=cam
cam.location=((X0+X1)/2,(Y0+Y1)/2,300);cam.rotation_euler=(0,0,0)
sc.render.resolution_x=int((X1-X0)/R);sc.render.resolution_y=int((Y1-Y0)/R);sc.render.resolution_percentage=100;sc.render.film_transparent=True
sd=bpy.data.lights.new('sun','SUN');sd.energy=2.0;sun=bpy.data.objects.new('sun',sd);sc.collection.objects.link(sun)
d=Vector((0.4,0.3,0.86)).normalized();sun.rotation_euler=d.to_track_quat('Z','Y').to_euler()
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[1].default_value=0.5
sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.device='CPU';sc.cycles.use_denoising=False;sc.view_settings.view_transform='Standard'
sc.render.filepath=out;bpy.ops.render.render(write_still=True)
