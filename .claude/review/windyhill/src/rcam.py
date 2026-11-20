import bpy,sys,json,math
from mathutils import Matrix,Vector
a=sys.argv[sys.argv.index('--')+1:];src,out=a[0],a[1]
import os; D = os.path.dirname(os.path.abspath(__file__)).replace(chr(92), '/')
sys.path.insert(0,D);from cam import R
p=json.load(open(D+'/cam84.json'))['p']
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
M=R(*p[3:6]);r,u,f=[Vector(list(x)) for x in M]
cd=bpy.data.cameras.new('c');co=bpy.data.objects.new('c',cd);bpy.context.scene.collection.objects.link(co)
co.matrix_world=Matrix(((r.x,u.x,-f.x,p[0]),(r.y,u.y,-f.y,p[1]),(r.z,u.z,-f.z,p[2]),(0,0,0,1)))
cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=p[6]*36/797;cd.clip_start=1300;cd.clip_end=1700
cd.shift_x=(p[7]-797/2)/797;cd.shift_y=-(p[8]-675/2)/797
sc=bpy.context.scene;sc.camera=co;sc.render.resolution_x=797;sc.render.resolution_y=675
ld=bpy.data.lights.new('s','SUN');ld.energy=4;lo=bpy.data.objects.new('s',ld);sc.collection.objects.link(lo)
# sun from ENE (shadows fall WSW, 18 deg south of west), 39 deg up, as read off the photo
el=math.radians(39);d=Vector((math.cos(el)*math.cos(math.radians(18)),math.cos(el)*math.sin(math.radians(18)),math.sin(el)))
lo.rotation_euler=d.to_track_quat('Z','Y').to_euler()
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[1].default_value=0.6
if len(a)>2 and a[2]=='clay':
    import random
    for i,o in enumerate([o for o in bpy.data.objects if o.type=='MESH']):
        pass
    sc.view_layers[0].material_override=None
    cm=bpy.data.materials.new('clay');cm.use_nodes=True;cm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.8,0.8,0.8,1)
    sc.view_layers[0].material_override=cm
for m in bpy.data.materials:
    if m.name.startswith('photo') and m.use_nodes:
        nt=m.node_tree;tx=[n for n in nt.nodes if n.type=='TEX_IMAGE'][0];em=nt.nodes.new('ShaderNodeEmission')
        nt.links.new(tx.outputs['Color'],em.inputs['Color']);outn=[n for n in nt.nodes if n.type=='OUTPUT_MATERIAL'][0]
        nt.links.new(em.outputs['Emission'],outn.inputs['Surface'])
sc.view_settings.view_transform='Standard'
sc.render.engine='BLENDER_EEVEE';sc.render.filepath=out;bpy.ops.render.render(write_still=True)
