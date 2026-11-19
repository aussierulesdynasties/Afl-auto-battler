# Straight-down orthographic render matching sat/esri_025.png (2080 px, x,y -260..260, 0.25 m/px, north up).
# blender -b --python model/render_top.py -- out.png
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, build
build.build_all()
sc = bpy.context.scene
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try: sc.render.engine = eng; break
    except Exception: pass
sc.render.resolution_x = sc.render.resolution_y = 2080; sc.render.film_transparent = True; sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.0; so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(35), 0, math.radians(200))
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = 520.0; cd.clip_end = 2000
co = bpy.data.objects.new('cam', cd); sc.collection.objects.link(co); sc.camera = co; co.location = (0, 0, 500); co.rotation_euler = (0, 0, 0)
sc.render.filepath = os.path.abspath(sys.argv[sys.argv.index('--') + 1]); bpy.ops.render.render(write_still=True); print('rendered top')
