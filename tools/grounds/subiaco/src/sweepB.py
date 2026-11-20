# Render subB6.glb from viewpoints orbiting the ground centre at camB17t's distance and height (by-eye search for photo 17).
#   blender -b --python sweepB.py -- GLB OUTPREFIX A0 A1 STEP [DIST H LENS]
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; GLB, PRE = a[0], a[1]; A0, A1, ST = float(a[2]), float(a[3]), float(a[4])
D = float(a[5]) if len(a) > 5 else 1450; H = float(a[6]) if len(a) > 6 else 843; LENS = float(a[7]) if len(a) > 7 else 216
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=GLB)
import bmesh as _b
_m=bpy.data.meshes.new('g');_o=bpy.data.objects.new('g',_m);bpy.context.scene.collection.objects.link(_o);_bm=_b.new()
import json as _j;_A=_j.load(open('layoutA.json'));_c=_A['fence']['co'];_K=_A['fence']['K'];_C=_A['C0']
def _rf(t):return sum(_c[k]*math.cos(k*t) for k in range(_K+1))+sum(_c[_K+k]*math.sin(k*t) for k in range(1,_K+1))
_vs=[_bm.verts.new((_C[0]+_rf(t)*math.cos(t),_C[1]+_rf(t)*math.sin(t),0.03)) for t in [math.radians(i) for i in range(-180,180,2)]];_bm.faces.new(_vs);_bm.to_mesh(_m)
_mt=bpy.data.materials.new('grass');_mt.diffuse_color=(0.25,0.5,0.15,1);_mt.use_nodes=True;_tx=_mt.node_tree.nodes.new('ShaderNodeTexImage');_tx.image=bpy.data.images.load(__import__('os').path.abspath('tex/turf.png'));_mt.node_tree.links.new(_tx.outputs['Color'],_mt.node_tree.nodes['Principled BSDF'].inputs['Base Color']);_m.materials.append(_mt)
sc = bpy.context.scene; cd = bpy.data.cameras.new('c'); co = bpy.data.objects.new('c', cd); sc.collection.objects.link(co); sc.camera = co
cd.lens = LENS; cd.clip_end = 20000
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'TEXTURE'  # grass disc uses its material colour as fallback; sc.display.shading.light = 'STUDIO'
sc.render.resolution_x = 1000; sc.render.resolution_y = 600; sc.render.film_transparent = True
T = Vector((0.25, 10.22, 0))
ang = A0
while ang <= A1 + 1e-6:
    t = math.radians(ang); co.location = T + Vector((D * math.cos(t), D * math.sin(t), H))
    co.rotation_euler = (T - co.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = '%s_%03d.png' % (PRE, int(ang) % 360); bpy.ops.render.render(write_still=True); ang += ST
