# Straight-down orthographic render matching sat/esri_025.png (2080 px, x,y -260..260, 0.25 m/px, north up).
# blender -b --python model/render_top.py -- out.png
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, build
build.build_all()
# RELEAN=1: give the model the satellite's own relief lean, so it compares like with like: each point moves by
# -(lean shift / lean height) x its height, from the per-stand tables in york_park.json (lean fitted at lean_z).
if os.environ.get('RELEAN'):
    import numpy as np
    K = sorted((b, dx / S['lean_z'], dy / S['lean_z']) for S in build.D['stands'] for b, dx, dy in S['lean'])
    Kb = np.array([k[0] for k in K]); Kx = np.array([k[1] for k in K]); Ky = np.array([k[2] for k in K])
    Kb = np.r_[Kb - 360, Kb, Kb + 360]; Kx = np.r_[Kx, Kx, Kx]; Ky = np.r_[Ky, Ky, Ky]
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH': continue
        for v in ob.data.vertices:
            x, y, z = v.co; b = math.degrees(math.atan2(x, y)) % 360
            v.co.x = x - np.interp(b, Kb, Kx) * z; v.co.y = y - np.interp(b, Kb, Ky) * z
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
