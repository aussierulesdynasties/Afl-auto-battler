# Render named views from an eye and a target. blender -b --python model/shot.py -- out_dir name:ex,ey,ez:tx,ty,tz:fovy ...
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, mathutils, build
build.build_all()
sc = bpy.context.scene
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = eng; break
    except Exception:
        pass
sc.render.resolution_x, sc.render.resolution_y = 1600, 1200; sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.62, 0.66, 0.72, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 2.6; so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(35), 0, math.radians(200))
cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'VERTICAL'; cd.clip_start = 0.05; cd.clip_end = 3000
co = bpy.data.objects.new('cam', cd); sc.collection.objects.link(co); sc.camera = co
argv = sys.argv[sys.argv.index('--') + 1:]; out = os.path.abspath(argv[0]); os.makedirs(out, exist_ok=True)
for spec in argv[1:]:
    name, e, t, f = spec.split(':'); e = mathutils.Vector([float(v) for v in e.split(',')]); t = mathutils.Vector([float(v) for v in t.split(',')])
    co.location = e; co.rotation_euler = (t - e).to_track_quat('-Z', 'Y').to_euler()
    if f.startswith('o'): cd.type = 'ORTHO'; cd.ortho_scale = float(f[1:])   # 'o<width m>': orthographic, for elevation boards
    else: cd.angle_y = math.radians(float(f))
    sc.render.filepath = os.path.join(out, name + '.png'); bpy.ops.render.render(write_still=True); print('rendered', name)
