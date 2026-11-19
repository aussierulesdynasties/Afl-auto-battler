# render the saved blend with a camera json {C,fwd,up,f}: blender -b model.blend -P viewcam2.py -- cam.json out.png [W H]
import bpy,sys,math,json
from mathutils import Vector,Matrix
a=sys.argv[sys.argv.index('--')+1:];J=json.load(open(a[0]));out=a[1];W,H=(int(a[2]),int(a[3])) if len(a)>3 else (1280,720)
sc=bpy.context.scene;sc.render.resolution_x=W;sc.render.resolution_y=H;sc.render.film_transparent=False
cd=bpy.data.cameras.new('vc');cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=J['f']*36/W;cd.clip_start=1;cd.clip_end=3000
co=bpy.data.objects.new('vc',cd);sc.collection.objects.link(co);sc.camera=co
f=Vector(J['fwd']).normalized();u=Vector(J['up']).normalized();r=f.cross(u).normalized();u=r.cross(f)
co.matrix_world=Matrix.Translation(Vector(J['C']))@Matrix(((r.x,u.x,-f.x),(r.y,u.y,-f.y),(r.z,u.z,-f.z))).to_4x4()
sc.render.engine='BLENDER_EEVEE';sc.view_settings.view_transform='Standard'
if not any(o.type=='LIGHT' for o in sc.objects):
    sd=bpy.data.lights.new('sun','SUN');sd.energy=2.7;so=bpy.data.objects.new('sun',sd);sc.collection.objects.link(so);so.rotation_euler=(math.radians(40),0,math.radians(-141))
w=bpy.data.worlds.new('w');w.use_nodes=True;bg=w.node_tree.nodes['Background'];bg.inputs['Color'].default_value=(0.55,0.6,0.68,1);bg.inputs['Strength'].default_value=0.55;sc.world=w
import os
for mn in filter(None,os.environ.get('FLATMAT','').split(',')):
    m=bpy.data.materials.get(mn)
    if m:
        b=m.node_tree.nodes['Principled BSDF']
        for l in list(b.inputs['Base Color'].links):m.node_tree.links.remove(l)
sc.render.filepath=out;bpy.ops.render.render(write_still=True)
