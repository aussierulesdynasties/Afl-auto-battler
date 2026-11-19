# Blender: straight-down orthographic render of out/scg.glb over a 340 m square centred on the pitch, 0.2 m per px
import bpy,sys,math
a=sys.argv[sys.argv.index('--')+1:];S=a[0];OUT=a[1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=S+'/out/scg.glb')
import bmesh
if len(a)>2:   # optional height cut: drop geometry above this z (light-tower heads lean in a satellite photo: parallax)
    zc=float(a[2])
    for o in [o for o in bpy.data.objects if o.type=='MESH']:
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if (o.matrix_world@v.co).z>zc],context='VERTS');bm.to_mesh(o.data);bm.free()
sc=bpy.context.scene;sc.render.resolution_x=sc.render.resolution_y=1700;sc.render.film_transparent=True
sc.render.engine='BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
sc.view_settings.view_transform='Standard'
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Strength'].default_value=0.6
sun=bpy.data.lights.new('sun','SUN');sun.energy=2.6;so=bpy.data.objects.new('sun',sun);sc.collection.objects.link(so);so.rotation_euler=(math.radians(30),0,math.radians(-60))
cd=bpy.data.cameras.new('c');cd.type='ORTHO';cd.ortho_scale=340;cd.clip_end=1000
co=bpy.data.objects.new('c',cd);sc.collection.objects.link(co);sc.camera=co;co.location=(0.94,-11.82,400);co.rotation_euler=(0,0,0)
sc.render.filepath=OUT;bpy.ops.render.render(write_still=True);print('TOP-DONE')
