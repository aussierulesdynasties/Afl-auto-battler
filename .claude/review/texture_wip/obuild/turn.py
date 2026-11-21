# Turntable stills: blender -b X.blend --python turn.py -- OUTDIR ELEV DIST AZ1,AZ2,... [W H lens target_z]
import bpy,sys,math,os
from mathutils import Vector
A=sys.argv[sys.argv.index('--')+1:];out=A[0];el=math.radians(float(A[1]));dist=float(A[2]);azs=[float(x) for x in A[3].split(',')]
W,H=(int(A[4]),int(A[5])) if len(A)>5 else (1600,900);lens=float(A[6]) if len(A)>6 else 50;tz=float(A[7]) if len(A)>7 else 15
sc=bpy.context.scene;cd=bpy.data.cameras.new('t');cam=bpy.data.objects.new('t',cd);sc.collection.objects.link(cam);sc.camera=cam
cd.lens=lens;cd.clip_end=5000;sc.render.resolution_x=W;sc.render.resolution_y=H
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(1,1,1,1);w.node_tree.nodes['Background'].inputs[1].default_value=0.12
sd=bpy.data.lights.new('sun','SUN');sd.energy=3.5;sd.angle=0.01;sun=bpy.data.objects.new('sun',sd);sc.collection.objects.link(sun)
_a=math.radians(165);_e=math.radians(42);sun.rotation_euler=Vector((math.cos(_e)*math.cos(_a),math.cos(_e)*math.sin(_a),math.sin(_e))).to_track_quat('Z','Y').to_euler()  # same sun as render.py
sc.render.engine='CYCLES';sc.cycles.samples=16;sc.cycles.device='CPU';sc.view_settings.view_transform='Standard'
tgt=Vector((float(A[8]),float(A[9]),tz)) if len(A)>9 else Vector((-22.8,2,tz))
for az in azs:
    a=math.radians(az);p=tgt+Vector((math.cos(a)*math.cos(el),math.sin(a)*math.cos(el),math.sin(el)))*dist
    cam.location=p;cam.rotation_euler=(tgt-p).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=os.path.join(out,'turn_%03d.png'%int(az%360));bpy.ops.render.render(write_still=True)
