# Render subB6.glb from viewpoints orbiting the ground centre at camB17t's distance and height (by-eye search for photo 17).
#   blender -b --python sweepB.py -- GLB OUTPREFIX A0 A1 STEP [DIST H LENS]
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; GLB, PRE = a[0], a[1]; A0, A1, ST = float(a[2]), float(a[3]), float(a[4])
D = float(a[5]) if len(a) > 5 else 1450; H = float(a[6]) if len(a) > 6 else 843; LENS = float(a[7]) if len(a) > 7 else 216
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=GLB)
sc = bpy.context.scene; cd = bpy.data.cameras.new('c'); co = bpy.data.objects.new('c', cd); sc.collection.objects.link(co); sc.camera = co
cd.lens = LENS; cd.clip_end = 20000
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'TEXTURE'; sc.display.shading.light = 'STUDIO'
sc.render.resolution_x = 500; sc.render.resolution_y = 300; sc.render.film_transparent = True
T = Vector((0.25, 10.22, 0))
ang = A0
while ang <= A1 + 1e-6:
    t = math.radians(ang); co.location = T + Vector((D * math.cos(t), D * math.sin(t), H))
    co.rotation_euler = (T - co.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = '%s_%03d.png' % (PRE, int(ang) % 360); bpy.ops.render.render(write_still=True); ang += ST
