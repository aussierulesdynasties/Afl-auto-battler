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
shot('her_field',322,9,75,lens=30,tgt=polt(140,108,10))
shot('her_street',140,12,85,lens=30,tgt=polt(140,112,9))
shot('her_join',300,14,45,lens=30,tgt=polt(150,108,10))
shot('scoreboard',200,12,70,lens=35,tgt=Vector((89.2,45.0,21.0)))   # board face and its raised lettering, from the field
shot('mes_tip',230,20,60,lens=35,tgt=Vector((80.0,56.0,28.0)))   # Messenger roof tip over the scoreboard end (satellite corner)
shot('mes_tip_out',40,15,70,lens=35,tgt=Vector((82.0,58.0,26.0)))
for _az in (170,185,200,215):shot('brew%d'%_az,_az+180,3,90,lens=35,tgt=polt(_az,80,12))   # field-side looks at the stands beside the Ladies (refs3/044 view)
for _e,_n in ((1.0,'brew044'),(9,'brew044h')):shot(_n,5,_e,170,lens=85,tgt=polt(183,88,10))   # refs3/044 view: across the ground, long lens
shot('brew_end',259+180-25,10,70,lens=35,tgt=polt(259,88,8));shot('brew_west',170+180+25,10,70,lens=35,tgt=polt(170,85,8))   # the two ends of the near-stand box-level section
shot('brew_sign',5,4,22,lens=35,tgt=Vector((-84.6,-28.0,14.75)))   # Brewongle Stand fascia lettering close-up
shot('seats_close',240,14,16,lens=35,tgt=polt(60,74,4))   # empty-seat close-up: Messenger lower tier from the boundary
shot('seats_close2',150,12,16,lens=35,tgt=polt(-30,72,4))   # O'Reilly lower tier
print('TURN-DONE')
