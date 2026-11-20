# straight-down orthographic render of a glb in the model frame (x east, y north), north up, 0.25 m/px, alpha = footprint
import bpy,sys,math
GLB,OUT=sys.argv[sys.argv.index('--')+1:]
CX,CY,H,MPP=-10.75,-24.16,220.0,0.25
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
sc=bpy.context.scene
cam=bpy.data.cameras.new('c');cam.type='ORTHO';cam.ortho_scale=2*H;cam.clip_end=1000
co=bpy.data.objects.new('c',cam);sc.collection.objects.link(co);co.location=(CX,CY,300);co.rotation_euler=(0,0,0);sc.camera=co
sun=bpy.data.lights.new('s','SUN');sun.energy=3.5;so=bpy.data.objects.new('s',sun);sc.collection.objects.link(so);so.rotation_euler=(math.radians(35),math.radians(-20),0)
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(0.6,0.62,0.66,1);w.node_tree.nodes['Background'].inputs[1].default_value=0.5
sc.render.engine='BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
N=int(round(2*H/MPP));sc.render.resolution_x=N;sc.render.resolution_y=N;sc.render.film_transparent=True
sc.render.image_settings.color_mode='RGBA';sc.render.filepath=OUT
bpy.ops.render.render(write_still=True)
