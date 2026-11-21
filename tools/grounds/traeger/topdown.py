# blender -b X.blend --python topdown.py -- OUT.png x0 y0 x1 y1 ppm : straight-down orthographic render of the model (field frame), transparent
import bpy,sys
A=sys.argv[sys.argv.index('--')+1:];out=A[0];x0,y0,x1,y1,k=map(float,A[1:6])
sc=bpy.context.scene;cam=sc.camera;cd=cam.data;cd.type='ORTHO';cd.ortho_scale=max(x1-x0,y1-y0);cd.shift_x=cd.shift_y=0
cd.sensor_fit='AUTO';cd.clip_start=1;cd.clip_end=1000
cam.location=((x0+x1)/2,(y0+y1)/2,400);cam.rotation_euler=(0,0,0)
sc.render.resolution_x=int(round((x1-x0)*k));sc.render.resolution_y=int(round((y1-y0)*k));sc.render.resolution_percentage=100
sc.render.film_transparent=True
g=bpy.data.collections.get('ground')
for o in (g.objects if g else []):o.hide_render=True
sc.render.filepath=out;bpy.ops.render.render(write_still=True);print('TOP OK',sc.render.resolution_x,sc.render.resolution_y)
