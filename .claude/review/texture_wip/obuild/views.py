# Texture-pass board views: blender -b X.blend --python views.py -- VIEWS.json OUTDIR   (same sun and sky as turn.py)
import bpy,sys,math,os,json
from mathutils import Vector
A=sys.argv[sys.argv.index('--')+1:];V=json.load(open(A[0]));out=A[1]
sc=bpy.context.scene;cd=bpy.data.cameras.new('v');cam=bpy.data.objects.new('v',cd);sc.collection.objects.link(cam);sc.camera=cam
cd.clip_start=0.1;cd.clip_end=5000;sc.render.resolution_x=1200;sc.render.resolution_y=800
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(1,1,1,1);w.node_tree.nodes['Background'].inputs[1].default_value=0.12
sd=bpy.data.lights.new('sun','SUN');sd.energy=3.5;sd.angle=0.01;sun=bpy.data.objects.new('sun',sd);sc.collection.objects.link(sun)
_a=math.radians(165);_e=math.radians(42);sun.rotation_euler=Vector((math.cos(_e)*math.cos(_a),math.cos(_e)*math.sin(_a),math.sin(_e))).to_track_quat('Z','Y').to_euler()
sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.device='CPU';sc.view_settings.view_transform='Standard'
for n,v in V.items():
    E=Vector(v['eye']);T=Vector(v['tgt']);cam.location=E;cam.rotation_euler=(T-E).to_track_quat('-Z','Y').to_euler();cd.lens=v.get('lens',35)
    sc.render.filepath=os.path.join(out,n+'.png');bpy.ops.render.render(write_still=True)
