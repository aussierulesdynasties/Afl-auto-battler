# Render the model from the matched (undistorted) camera.
# blender -b gabba.blend -P render.py -- cam.json OUT.png [mask]
import bpy, sys, json, math
import mathutils as mu
args = sys.argv[sys.argv.index('--') + 1:]
cam = json.load(open(args[0])); out = args[1]; mask = len(args) > 2
C = mu.Vector(cam['C']); Rm = cam['M']  # rows: right, up, forward
sc = bpy.context.scene
W, H = 1600, 1066
sc.render.resolution_x = W; sc.render.resolution_y = H; sc.render.resolution_percentage = 100
sc.render.engine = 'BLENDER_EEVEE'
cd = bpy.data.cameras.new('cam'); co = bpy.data.objects.new('cam', cd); sc.collection.objects.link(co); sc.camera = co
right = mu.Vector(Rm[0]); up = mu.Vector(Rm[1]); fwd = mu.Vector(Rm[2])
m3 = mu.Matrix((right, up, -fwd)).transposed()
co.matrix_world = mu.Matrix.Translation(C) @ m3.to_4x4()
cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36.0; cd.lens = cam['f'] * 36.0 / W
cd.shift_x = (W / 2 - cam['cx']) / W; cd.shift_y = (cam['cy'] - H / 2) / W
cd.clip_start = 1.0; cd.clip_end = 5000
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']
if mask:
    bg.inputs['Color'].default_value = (0, 0, 0, 1)
    for i, m in enumerate(bpy.data.materials):
        m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        e = nt.nodes.new('ShaderNodeEmission'); o = nt.nodes.new('ShaderNodeOutputMaterial')
        e.inputs['Color'].default_value = (((i*67)%255)/255, ((i*131+40)%255)/255, ((i*29+90)%255)/255, 1); nt.links.new(e.outputs[0], o.inputs[0])
    sc.view_settings.view_transform = 'Standard'
else:
    bg.inputs['Color'].default_value = (0.42, 0.58, 0.85, 1); bg.inputs['Strength'].default_value = cam.get('sky', 0.85)   # clear blue sky: blue shade as in g49
    sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 4.0; so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so)
    # sun fitted to the roof's shadow edge on the oval (camB.json sun_az/sun_el)
    az = math.radians(cam.get('sun_az', 270)); el = math.radians(cam.get('sun_el', 25))
    d = mu.Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
    so.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    sc.view_settings.view_transform = 'AgX'
sc.render.film_transparent = False
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
