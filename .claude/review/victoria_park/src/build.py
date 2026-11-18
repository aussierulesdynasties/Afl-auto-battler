# blender -b --python build.py -- OUTDIR [glb]
import bpy, json, math, sys, os
from mathutils import Matrix, Vector
argv = sys.argv[sys.argv.index('--') + 1:]
OUT = argv[0]; DO_GLB = len(argv) > 1 and argv[1] == 'glb'
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()
os.chdir(r'C:/Users/DANTE/AppData/Local/Temp/claude/719bd28297a24873/353a80fe-22fd-45ba-8aa3-2524095314c7/scratchpad/vp')
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
MESH = json.load(open('meshes.json'))
J = json.load(open('cam5.json')); p = J['p']

TILE = json.load(open('tex3/tile.json'))
def mat(name, tex, rough=0.85):
    # hand-painted texture (tex3/, paint.py); UVs are in metres, Mapping divides by the tile size in metres
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes['Principled BSDF']; b.inputs['Roughness'].default_value = rough
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.abspath(tex))
    t.interpolation = 'Cubic'
    key = os.path.splitext(os.path.basename(tex))[0]
    if key in TILE and os.path.dirname(tex).endswith('tex3'):
        tu, tv = TILE[key]
        uvn = nt.nodes.new('ShaderNodeUVMap'); mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (1 / tu, 1 / tv, 1)
        nt.links.new(uvn.outputs['UV'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], t.inputs['Vector'])
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    return m
T3 = lambda k, **kw: mat(k, 'tex3/%s.png' % k, **kw)
M = {k: T3(k) for k in TILE}
M['glass'] = T3('glass', rough=0.15); M['sher_end'] = T3('sher_end', rough=0.15); M['steel'] = T3('steel', rough=0.5)
M['grass'] = mat('grass', 'tex/grass.png')

def metre_uv(V, f):
    # planar UVs in metres for a lone face: u along its horizontal edge direction, v up its slope
    import numpy as _n
    P = _n.array([V[i] for i in f], float); nrm = _n.cross(P[1] - P[0], P[2] - P[0])
    if _n.linalg.norm(nrm) < 1e-9: nrm = _n.cross(P[2] - P[0], P[-1] - P[0])
    nrm = nrm / (_n.linalg.norm(nrm) + 1e-12)
    h = _n.cross([0, 0, 1.0], nrm)
    if _n.linalg.norm(h) < 1e-3: h = _n.array([1.0, 0, 0])
    h = h / _n.linalg.norm(h); v = _n.cross(nrm, h)
    return [(float(q @ h), float(q @ v)) for q in P]
for m in MESH:
    me = bpy.data.meshes.new(m['name']); me.from_pydata(m['v'], [], m['f']); me.update()
    uv = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        if 'uv' in m:
            for li in poly.loop_indices: uv.data[li].uv = m['uv'][me.loops[li].vertex_index]
        else:
            for li, q in zip(poly.loop_indices, metre_uv(m['v'], list(poly.vertices))): uv.data[li].uv = q
    me.materials.append(M[m['mat']])
    ob = bpy.data.objects.new(m['name'], me); sc.collection.objects.link(ob)
# fix normals outward-ish: recalc on each
for ob in sc.objects:
    if ob.type != 'MESH': continue
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT'); ob.select_set(False)

if DO_GLB:
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'vicpark_exterior.glb'), export_format='GLB')

# sun: measured from the light pole and its shadow (elevation 35.9 deg, shadows toward -53.8 deg)
el, az = math.radians(35.9), math.radians(-53.8)
dvec = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), -math.sin(el)))
ld = bpy.data.lights.new('sun', 'SUN'); ld.energy = 4.5; ld.angle = math.radians(0.6)
so = bpy.data.objects.new('sun', ld); sc.collection.objects.link(so)
so.rotation_euler = dvec.to_track_quat('-Z', 'Y').to_euler()
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.62, 0.75, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9

# matched camera
def Rm(yaw, pt, roll):
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pt), math.sin(pt), math.cos(roll), math.sin(roll)
    f = Vector((cy * cp, sy * cp, sp)); r = Vector((sy, -cy, 0)); u = r.cross(f)
    return (cr * r + sr * u, -sr * r + cr * u, f)
r, u, f = Rm(*p[3:6])
cd = bpy.data.cameras.new('cam'); co = bpy.data.objects.new('cam', cd); sc.collection.objects.link(co); sc.camera = co
mw = Matrix(((r.x, u.x, -f.x, p[0]), (r.y, u.y, -f.y, p[1]), (r.z, u.z, -f.z, p[2]), (0, 0, 0, 1)))
co.matrix_world = mw
Wp, Hp = 747, 500
cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36; cd.lens = p[6] / Wp * 36
cd.shift_x = (p[7] - Wp / 2) / Wp; cd.shift_y = (Hp / 2 - p[8]) / Wp
cd.clip_start = 1; cd.clip_end = 5000
sc.render.resolution_x, sc.render.resolution_y = Wp * 2, Hp * 2
sc.render.film_transparent = True
sc.render.engine = 'CYCLES'; sc.cycles.samples = 32; sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = -0.45   # whites stopped clipping
sc.render.filepath = os.path.abspath(os.path.join(OUT, "render.png"))
# extra views: '-- OUT views.json' with [{"name", "eye": [x,y,z], "at": [x,y,z], "lens": mm}] (turntable, close-ups)
VIEWS = json.load(open(argv[1])) if len(argv) > 1 and argv[1].endswith('.json') else None
if VIEWS:
    sc.render.film_transparent = False; cd.shift_x = cd.shift_y = 0; sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
    for v in VIEWS:
        e = Vector(v['eye']); d = (Vector(v['at']) - e).normalized()
        co.matrix_world = Matrix.Translation(e) @ d.to_track_quat('-Z', 'Y').to_matrix().to_4x4()
        cd.lens = v.get('lens', 35)
        sc.render.filepath = os.path.abspath(os.path.join(OUT, v['name'] + '.png'))
        bpy.ops.render.render(write_still=True); print('RENDERED', v['name'])
else:
    bpy.ops.render.render(write_still=True)
    print('RENDERED', sc.render.engine)
