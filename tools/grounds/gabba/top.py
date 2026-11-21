# Orthographic straight-down render in the satellite frame (x,y -200..200, 0.25 m/px, north up).
# blender -b gabba.blend -P top.py -- OUT.png [kx ky]   (kx,ky: satellite lean, metres sideways per metre up)
import bpy, sys, math
args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]; kx, ky = (float(args[1]), float(args[2])) if len(args) > 2 else (0.0, 0.0)
sc = bpy.context.scene
for ob in sc.objects:
    if ob.type == 'MESH':
        for v in ob.data.vertices: v.co.x += kx * v.co.z; v.co.y += ky * v.co.z
sc.render.resolution_x = sc.render.resolution_y = 1600; sc.render.resolution_percentage = 100
sc.render.engine = 'BLENDER_EEVEE'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = 400; cd.clip_start = 1; cd.clip_end = 1000
co = bpy.data.objects.new('cam', cd); sc.collection.objects.link(co); sc.camera = co
co.location = (0, 0, 500); co.rotation_euler = (0, 0, 0)
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.55, 0.55, 1)
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 4.0; so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(30), 0, math.radians(-40))
sc.view_settings.view_transform = 'AgX'; sc.render.film_transparent = True
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
