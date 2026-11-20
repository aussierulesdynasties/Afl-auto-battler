import bpy,math,sys,mathutils,os
a=sys.argv[sys.argv.index('--')+1:];glb,out=a[0],a[1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=glb)
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x,sc.render.resolution_y=1920,1080
sc.view_settings.view_transform='Standard'
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.68,0.85,1)
sd=bpy.data.lights.new('s','SUN');sd.energy=3.2;so=bpy.data.objects.new('s',sd);sc.collection.objects.link(so);so.rotation_euler=(math.radians(50),0,math.radians(250))
cd=bpy.data.cameras.new('c');cd.angle=math.radians(40);cd.clip_end=5000;co=bpy.data.objects.new('c',cd);sc.collection.objects.link(co);sc.camera=co
def look(e,t):
    e=mathutils.Vector(e);co.location=e;co.rotation_euler=(mathutils.Vector(t)-e).to_track_quat('-Z','Y').to_euler()
def shot(n):sc.render.filepath=os.path.join(out,n);bpy.ops.render.render(write_still=True)
# seats bbox (gltf import: blender z up again)
xs=[];ys=[];zs=[]
for o in bpy.data.objects:
    if o.type=='MESH' and any(s.material and 'seat_blue' in s.material.name for s in o.material_slots):
        for v in o.bound_box:p=o.matrix_world@mathutils.Vector(v);xs.append(p.x);ys.append(p.y);zs.append(p.z)
print('SEATS',min(xs),max(xs),min(ys),max(ys),max(zs))
T=(2,-2,0)
for az in (45,135,225,315):
    r,e=300,math.radians(35);A=math.radians(az)
    look((T[0]+r*math.cos(e)*math.sin(A),T[1]+r*math.cos(e)*math.cos(A),r*math.sin(e)),T);shot('t%03d.png'%az)
cx=(min(xs)+max(xs))/2;cy=(min(ys)+max(ys))/2
look((cx+60 if cx<0 else cx-60,cy,10),(cx,cy,9));shot('facade.png')
look((cx+40 if cx<0 else cx-40,cy+20,45),(cx,cy,15));shot('roof.png')
