# Render the model from Google Earth camera params. blender -b --python model/render.py -- out_dir name:h:t:d:tx:ty:tz ...
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(SP, 'work'))
import bpy, mathutils
import build, earthcam
build.build_all()
sc = bpy.context.scene
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = eng; break
    except Exception:
        pass
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080; sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.68, 0.85, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.2; so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(35), 0, math.radians(200))  # sun high in the north (southern hemisphere, Launceston summer)
cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(35); cd.clip_end = 5000
co = bpy.data.objects.new('cam', cd); sc.collection.objects.link(co); sc.camera = co
argv = sys.argv[sys.argv.index('--') + 1:]
out = os.path.abspath(argv[0])
for spec_ in argv[1:]:
    name, h, t, d, tx, ty, tz = spec_.split(':'); c = earthcam.cam(float(h), float(t), float(d), tz=float(tz), tx=float(tx), ty=float(ty))
    R = mathutils.Matrix((c['right'], c['up'], -c['fwd'])).transposed()
    co.matrix_world = mathutils.Matrix.Translation(c['C']) @ R.to_4x4()
    sc.render.filepath = os.path.join(out, name + '.png'); bpy.ops.render.render(write_still=True)
    print('rendered', name)
