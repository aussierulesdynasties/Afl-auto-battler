# blender -b X.blend --python rcam.py -- cam_opencv.json out.png [scale]
import bpy,json,sys,math
from mathutils import Matrix,Vector
A=sys.argv[sys.argv.index('--')+1:];c=json.load(open(A[0]));out=A[1];k=float(A[2]) if len(A)>2 else 1
import numpy as np
r=np.array(c['r'],float);th=np.linalg.norm(r)
if th<1e-12:R=np.eye(3)
else:
    kx=r/th;Kx=np.array([[0,-kx[2],kx[1]],[kx[2],0,-kx[0]],[-kx[1],kx[0],0]]);R=np.eye(3)+math.sin(th)*Kx+(1-math.cos(th))*Kx@Kx
T=np.array(c['t'],float);C=-R.T@T
# opencv camera axes (x right, y down, z forward) -> blender (x right, y up, -z forward)
Rw=R.T@np.diag([1,-1,-1])
sc=bpy.context.scene;cam=sc.camera
cam.matrix_world=Matrix(((Rw[0,0],Rw[0,1],Rw[0,2],C[0]),(Rw[1,0],Rw[1,1],Rw[1,2],C[1]),(Rw[2,0],Rw[2,1],Rw[2,2],C[2]),(0,0,0,1)))
W,H=c['w'],c['h'];cd=cam.data;cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=c['f']*36/W;cd.shift_x=0;cd.shift_y=0;cd.clip_start=0.1
sc.render.resolution_x=int(W*k);sc.render.resolution_y=int(H*k);sc.render.filepath=out
sun=bpy.data.objects.get('sun')
if len(A)>3:sun.rotation_euler=Vector(tuple(map(float,A[3].split(',')))).normalized().to_track_quat('-Z','Y').to_euler()
g=bpy.data.collections.get('ground')
if g:
    for o in g.objects:o.hide_render=True
bpy.ops.render.render(write_still=True);print('OK',out)
