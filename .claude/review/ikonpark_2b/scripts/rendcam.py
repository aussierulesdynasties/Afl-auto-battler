# render a GLB from a fitted photo camera. usage: blender -b -P rendcam.py -- GLB CAM.json W H OUT.png
import bpy, sys, json, math
from mathutils import Matrix, Vector
glb, camj, W, H, out = sys.argv[sys.argv.index('--') + 1:]
W = int(W); H = int(H)
q = json.load(open(camj))['q']
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
Cx, Cy, Cz, yaw, pitch, roll, fo, cx, cy = q[:9]
cyw, syw, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
f = Vector((cyw * cp, syw * cp, sp)); r = Vector((syw, -cyw, 0)); u = r.cross(f)
cr, sr = math.cos(roll), math.sin(roll)
r2 = cr * r + sr * u; u2 = -sr * r + cr * u
cam = bpy.data.cameras.new('c'); co = bpy.data.objects.new('c', cam); bpy.context.scene.collection.objects.link(co)
Mrot = Matrix((r2, u2, -f)).transposed()
co.matrix_world = Matrix.Translation((Cx, Cy, Cz)) @ Mrot.to_4x4()
cam.sensor_fit = 'HORIZONTAL'; cam.sensor_width = 36.0; cam.lens = fo * 36.0 / W
cam.shift_x = (W / 2 - cx) / W; cam.shift_y = (cy - H / 2) / W
cam.clip_end = 5000
sc = bpy.context.scene; sc.camera = co
sc.render.resolution_x = W; sc.render.resolution_y = H
sc.render.engine = 'BLENDER_EEVEE'
sc.render.film_transparent = (len(sys.argv) < 99 and "close" not in out.lower())
sun = bpy.data.lights.new('s', 'SUN'); sun.energy = 3.5
so = bpy.data.objects.new('s', sun); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(40), 0, math.radians(-30))
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.6, 0.65, 0.7, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.8
sc.view_settings.view_transform = 'Standard'
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
