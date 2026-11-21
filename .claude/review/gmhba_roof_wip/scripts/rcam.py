import bpy,sys,math,json
from mathutils import Matrix,Vector
a=sys.argv[sys.argv.index('--')+1:];src,out,cj=a[0],a[1],a[2]
J=json.load(open(cj));bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
W,H=1280,585;sc.render.resolution_x,sc.render.resolution_y=W,H
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c'));sc.collection.objects.link(cam);sc.camera=cam
R=Matrix(J['R']);C=Vector(J['C']);Mw=R.transposed()@Matrix(((1,0,0),(0,-1,0),(0,0,-1)))
cam.matrix_world=Matrix.Translation(C)@Mw.to_4x4()
cam.data.sensor_fit='HORIZONTAL';cam.data.angle=2*math.atan(W/2/J['f']);cam.data.clip_end=5000
cam.data.shift_x=-(J['cx']-W/2)/W;cam.data.shift_y=(J['cy']-H/2)/W
sun=bpy.data.objects.new('s',bpy.data.lights.new('s','SUN'));sc.collection.objects.link(sun);sun.data.energy=4.0
el=math.radians(float(a[3]) if len(a)>3 else 67);az=math.radians(float(a[4]) if len(a)>4 else 90)  # sun from the east
d=Vector((math.sin(az)*math.cos(el),math.cos(az)*math.cos(el),math.sin(el)))
sun.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()

# review ground (not in the model): asphalt-grey plane just under z 0 so nothing floats
bpy.ops.mesh.primitive_plane_add(size=1200,location=(0,0,-0.05));_g=bpy.context.object;_gm=bpy.data.materials.new('ground');_gm.use_nodes=True;_gm.node_tree.nodes['Principled BSDF'].inputs[0].default_value=(0.32,0.31,0.28,1);_g.data.materials.append(_gm)
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.65,0.8,1);w.node_tree.nodes['Background'].inputs[1].default_value=0.8
sc.view_settings.view_transform='Standard'
sc.render.filepath=out;bpy.ops.render.render(write_still=True)
