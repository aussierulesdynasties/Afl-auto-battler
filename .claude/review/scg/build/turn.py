# Blender: 4 turntable stills + a facade close-up of out/scg.glb (unlit photo materials)
import bpy,sys,math
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:];S=a[0];OUT=a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=S+'/out/scg.glb')
sc=bpy.context.scene;sc.render.resolution_x=1600;sc.render.resolution_y=1000
sc.render.engine='BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(0.55,0.62,0.7,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=0.45
sc.view_settings.view_transform='Standard'
sun=bpy.data.lights.new('sun','SUN');sun.energy=2.6;so=bpy.data.objects.new('sun',sun);sc.collection.objects.link(so);so.rotation_euler=(math.radians(40),0,math.radians(-60))
cd=bpy.data.cameras.new('c');co=bpy.data.objects.new('c',cd);sc.collection.objects.link(co);sc.camera=co;cd.clip_end=5000
C=Vector((0.94,-11.82,10))   # Blender imports Y-up GLB back to Z-up
ONLY=a[2].split(',') if len(a)>2 else None
def polt(deg,r,z):return Vector((0.94+r*math.cos(math.radians(deg)),-11.82+r*math.sin(math.radians(deg)),z))
def shot(name,az,el,dist,lens=35,tgt=C):
    if ONLY and name not in ONLY:return
    d=Vector((math.cos(math.radians(el))*math.cos(math.radians(az)),math.cos(math.radians(el))*math.sin(math.radians(az)),math.sin(math.radians(el))))
    co.location=tgt+d*dist;co.rotation_euler=(tgt-co.location).to_track_quat('-Z','Y').to_euler();cd.lens=lens
    sc.render.filepath=OUT+'/'+name+'.png';bpy.ops.render.render(write_still=True)
for k,az in enumerate((270,0,90,180)):shot('t%d'%k,az,28,420)
# facade close-up: near (Brewongle) stand from the street, eye 1.7 m up
shot('close',215,6,95,lens=30,tgt=Vector((0.94+150*math.cos(math.radians(200)),-11.82+150*math.sin(math.radians(200)),10)))
# stand backs from the street (Trumper south, O'Reilly east) and the heritage roofs from above
shot('trumper_back',-62,7,85,lens=30,tgt=polt(-68,128,13))
shot('oreilly_back',-2,7,85,lens=30,tgt=polt(-5,128,12))
shot('heritage_roofs',150,32,150,lens=35,tgt=polt(140,105,12))
print('TURN-DONE')
