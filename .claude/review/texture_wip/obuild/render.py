# Render the .blend from the camera fitted to photo.jpg. Usage: blender -b X.blend --python render.py -- CAMJSON OUTPNG [night:purple|blue]
import bpy,sys,math,json
from mathutils import Matrix,Vector
A=sys.argv[sys.argv.index('--')+1:];cj,out=A[0],A[1]
p=json.load(open(cj))['p'];W,H=1920,1079
yaw,pit,rol=p[3],p[4],p[5]
cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pit),math.sin(pit);cr,sr=math.cos(rol),math.sin(rol)
f=Vector((cy*cp,sy*cp,sp));r=Vector((sy,-cy,0));u=r.cross(f)
R0=cr*r+sr*u;R1=-sr*r+cr*u
sc=bpy.context.scene
cd=bpy.data.cameras.new('cam');cam=bpy.data.objects.new('cam',cd);sc.collection.objects.link(cam);sc.camera=cam
M=Matrix(((R0.x,R1.x,-f.x),(R0.y,R1.y,-f.y),(R0.z,R1.z,-f.z)))
cam.matrix_world=Matrix.Translation(Vector(p[:3]))@M.to_4x4()
cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=p[6]*36/W;cd.shift_x=(p[7]-W/2)/W;cd.shift_y=-(p[8]-H/2)/W;cd.clip_end=5000
sc.render.resolution_x=W;sc.render.resolution_y=H;sc.render.film_transparent=True
SKY=0
if not SKY:
  sd=bpy.data.lights.new('sun','SUN')
  sd.energy=float(__import__('os').environ.get('SUNE','3.5'));sd.angle=0.01;sun=bpy.data.objects.new('sun',sd);sc.collection.objects.link(sun)
  # sun from the SSW, 45 deg up: o2 lift NNE face in shade, WNW face lit, lift shadow falls image-left
  az=math.radians(float(__import__('os').environ.get('SUNAZ','165')));el=math.radians(float(__import__('os').environ.get('SUNEL','42')));d=Vector((math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)))
  sun.rotation_euler=d.to_track_quat('Z','Y').to_euler()
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(1,1,1,1);w.node_tree.nodes['Background'].inputs[1].default_value=float(__import__('os').environ.get('SKYE','0.12'))  # neutral sky; sun 165/42, 3.5 and sky 0.12 fitted to the lift's lit and shaded faces in photo o2
sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.device='CPU';sc.cycles.use_denoising=True
sc.view_settings.view_transform='Standard'
sc.render.filepath=out;bpy.ops.render.render(write_still=True)
