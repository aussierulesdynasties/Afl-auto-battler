# 4 orbit stills + close-up. Usage: blender -b --python orbit.py -- wh.glb OUTPREFIX
import bpy,sys,math
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:];src,out=a[0],a[1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
sc=bpy.context.scene
for m in bpy.data.materials:
    if m.name.startswith('photo') and m.use_nodes:
        nt=m.node_tree;tx=[n for n in nt.nodes if n.type=='TEX_IMAGE']
        if not tx: continue
        tx=tx[0];em=nt.nodes.new('ShaderNodeEmission')
        nt.links.new(tx.outputs['Color'],em.inputs['Color']);o=[n for n in nt.nodes if n.type=='OUTPUT_MATERIAL'][0];nt.links.new(em.outputs['Emission'],o.inputs['Surface'])
ld=bpy.data.lights.new('s','SUN');ld.energy=4;lo=bpy.data.objects.new('s',ld);sc.collection.objects.link(lo)
el=math.radians(39);d=Vector((math.cos(el)*math.cos(math.radians(18)),math.cos(el)*math.sin(math.radians(18)),math.sin(el)))
lo.rotation_euler=d.to_track_quat('Z','Y').to_euler()
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;bg=w.node_tree.nodes['Background'];bg.inputs[0].default_value=(0.55,0.65,0.8,1);bg.inputs[1].default_value=0.8
sc.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new('c');cd.lens=35;cd.clip_start=1;cd.clip_end=2000;co=bpy.data.objects.new('c',cd);sc.collection.objects.link(co);sc.camera=co
sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.engine='BLENDER_EEVEE'
T=Vector((6,11,0))
shots=[('sw',225,28,230),('se',315,28,230),('ne',45,28,230),('nw',135,28,230),('close_reyn',320,10,45),('close_north',262,8,58),('close_sb',200,8,45)]
for n,az,elv,dist in shots:
    tgt=T if not n.startswith('close') else {'close_reyn':Vector((-45,55,5)),'close_north':Vector((-12,88,6)),'close_sb':Vector((95,38,7))}[n]
    r=math.radians(az);e=math.radians(elv)
    co.location=tgt+Vector((math.cos(r)*math.cos(e),math.sin(r)*math.cos(e),math.sin(e)))*dist
    co.rotation_euler=(tgt-co.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=out+n+'.png';bpy.ops.render.render(write_still=True)
