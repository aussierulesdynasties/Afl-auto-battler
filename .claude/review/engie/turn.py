# turntable + close-up stills of a built glb: blender -b --python turn.py -- in.glb outdir
import bpy,sys,math,os
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:];glb,od=os.path.abspath(a[0]),os.path.abspath(a[1])
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
bpy.ops.import_scene.gltf(filepath=glb)
sd=bpy.data.lights.new('sun','SUN');sd.energy=4.0;so=bpy.data.objects.new('sun',sd);sc.collection.objects.link(so)
so.rotation_euler=(Vector((27.9,93.7,0))-Vector((40.15,127.9,54.0))).normalized().to_track_quat('-Z','Y').to_euler()
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;bg=w.node_tree.nodes['Background'];bg.inputs[0].default_value=(0.50,0.62,0.85,1);bg.inputs[1].default_value=0.25
try:sc.render.engine='BLENDER_EEVEE_NEXT'
except Exception:sc.render.engine='BLENDER_EEVEE'
sc.view_settings.view_transform='Standard';sc.render.resolution_x=1920;sc.render.resolution_y=1080
cd=bpy.data.cameras.new('c');cam=bpy.data.objects.new('c',cd);sc.collection.objects.link(cam);sc.camera=cam
c0=Vector((18.4,43.3,0))
def shot(eye,look,lens,name):
    cam.location=eye;cam.rotation_euler=(look-eye).to_track_quat('-Z','Y').to_euler();cd.lens=lens;cd.clip_end=3000
    sc.render.filepath=os.path.join(od,name);bpy.ops.render.render(write_still=True)
for k,az in enumerate((0,90,180,270)):
    t=math.radians(az+20);shot(c0+Vector((330*math.cos(t),330*math.sin(t),140)),c0+Vector((0,0,5)),30,'turn_%d.png'%k)
def P(t,r,z):a=math.radians(t);return c0+Vector((r*math.cos(a),r*math.sin(a),z))
# facade close-up: the NW block from the plaza outside it, about 25 m off the wall
shot(P(165,160,6),P(165,120,8),35,'closeup_facade.png')
# SE corner close-up: the tan box, awnings and red wall from the plaza
shot(P(207,165,7),P(209,126,8),35,'closeup_se.png')
# a light tower head (25) from the field side, level with its lamps
import json
CT=json.load(open(os.path.join(os.path.dirname(glb),'cam8.json')))
tx,ty=CT['towers']['25'];hw=CT['p'][9];ht=Vector((tx,ty,hw-8))
shot(ht+(c0-ht).normalized()*0+Vector(((c0.x-tx),(c0.y-ty),0)).normalized()*45+Vector((0,0,2)),ht,35,'closeup_tower.png')
if os.environ.get('ORBIT')=='1':
    sc.render.resolution_x=1280;sc.render.resolution_y=720
    for f in range(120):
        t=math.radians(f*3+20);shot(c0+Vector((330*math.cos(t),330*math.sin(t),140)),c0+Vector((0,0,5)),30,'orbit/f%03d.png'%f)
