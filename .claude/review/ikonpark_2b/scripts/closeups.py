# close-up proofs: seats empty, stand joins, facades. usage: blender -b -P closeups.py -- GLB OUTDIR A|B
import bpy,sys,math,os
from mathutils import Vector
glb,out,ver=sys.argv[sys.argv.index('--')+1:];os.makedirs(out,exist_ok=True)
V={'A':[('seats_pratt',(-13,-44,1.8),(-13,-62,6)),('join_pratt_west',(-30,-5,6),(-62,-22,10)),('join_pratt_farleft',(58,-30,6),(58,-66,8)),
        ('join_heroes_gardiner',(35,80,6),(35,116,8)),('facade_pratt_back',(-19,-112,6),(-19,-67,12)),('facade_heroes_back',(88,165,6),(88,119,8)),
        ('seats_heroes',(80,95,1.8),(82,112,6)),('facade_farleft_back',(88,-125,5),(88,-83,5)),('join_fosters_eaststep',(-40,35,6),(-72,30,10))],
   'B':[('seats_legends',(108,-6,1.8),(132,-10,6)),('join_pratt_legends',(60,-30,6),(62,-60,8)),('join_legends_heroes',(105,55,6),(122,82,8)),
        ('facade_legends_back',(195,-30,6),(142,-22,8)),('seats_pratt',(-13,-44,1.8),(-13,-62,6)),('facade_pratt_back',(-19,-112,6),(-19,-67,12)),
        ('join_heroes_gardiner',(35,80,6),(35,116,8)),('seats_heroes',(80,95,1.8),(82,112,6)),('join_pratt_west',(-30,-5,6),(-62,-22,10))]}[ver]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=glb)
sc=bpy.context.scene;cam=bpy.data.cameras.new('c');co=bpy.data.objects.new('c',cam);sc.collection.objects.link(co);sc.camera=co
cam.lens=20;cam.clip_end=3000
sun=bpy.data.lights.new('s','SUN');sun.energy=3.5;so=bpy.data.objects.new('s',sun);sc.collection.objects.link(so);so.rotation_euler=(math.radians(40),0,math.radians(-30))
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(0.55,0.68,0.85,1)
gp=bpy.data.meshes.new('g');gp.from_pydata([(-400,-400,-0.02),(400,-400,-0.02),(400,400,-0.02),(-400,400,-0.02)],[],[(0,1,2,3)])
go=bpy.data.objects.new('g',gp);sc.collection.objects.link(go);m=bpy.data.materials.new('gm');m.use_nodes=True
m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.12,0.13,0.11,1);gp.materials.append(m)
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.view_settings.view_transform='Standard'
C0=Vector((47.8,26.0,1.8))
def seat_eye(t):
    # eye 4 m in front of the first seat face on the line from the ground centre to the target, 1.8 m above it
    dg=bpy.context.evaluated_depsgraph_get();d=Vector((t[0],t[1],1.8))-C0;d.normalize()
    for k in range(400):
        p=C0+d*(k*0.5);hit,loc,_,_,_,_=sc.ray_cast(dg,p+Vector((0,0,60)),Vector((0,0,-1)))
        if hit and loc.z>0.5:
            q=C0+d*max(0,k*0.5-4.0);return (q.x,q.y,1.8)
    return t
for n,e,t in V:
    if n.startswith('seats'): e=seat_eye(t)
    co.location=Vector(e);co.rotation_euler=(Vector(t)-Vector(e)).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=os.path.join(out,n+'.png');bpy.ops.render.render(write_still=True)
