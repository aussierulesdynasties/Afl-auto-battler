# Turntable stills + podium facade close-up from model5.blend (same sun/world as the overlay render).
import bpy,math,os
from mathutils import Vector
sc=bpy.context.scene
for o in [o for o in sc.objects if o.type in('CAMERA','LIGHT')]:bpy.data.objects.remove(o)
sd=bpy.data.lights.new('sun','SUN');sd.energy=2.7;so=bpy.data.objects.new('sun',sd);sc.collection.objects.link(so)
so.rotation_euler=(math.radians(40),0,math.radians(-141))
w=bpy.data.worlds.new('w');w.use_nodes=True;bg=w.node_tree.nodes['Background'];bg.inputs['Color'].default_value=(0.55,0.6,0.68,1);bg.inputs['Strength'].default_value=0.55;sc.world=w
sc.view_settings.view_transform='Standard';sc.render.engine='BLENDER_EEVEE';sc.render.film_transparent=False
cd=bpy.data.cameras.new('c');co=bpy.data.objects.new('c',cd);sc.collection.objects.link(co);sc.camera=co;cd.clip_end=3000
def shot(eye,tgt,lens,fn,rx=2000,ry=1333):
    co.location=eye;co.rotation_euler=(Vector(tgt)-Vector(eye)).to_track_quat('-Z','Y').to_euler();cd.lens=lens
    sc.render.resolution_x=rx;sc.render.resolution_y=ry;sc.render.filepath=os.path.abspath('gate/'+fn);bpy.ops.render.render(write_still=True)
for i,az in enumerate((45,135,225,315)):
    t=math.radians(az);shot((420*math.cos(t),420*math.sin(t),230),(0,0,8),42,f'turn_{az:03d}.png')
# podium facade (SW face, (-131,2)->(-97,-39)), 14 m out, eye height 4 m
mx,my=-114,-18.5;nx,ny=-0.77,-0.64
shot((mx+nx*14,my+ny*14,4),(mx,my,5),30,'facade_closeup.png')
shot((mx+nx*5,my+ny*5,3),(mx,my,3.5),35,'facade_closeup_5m.png')
