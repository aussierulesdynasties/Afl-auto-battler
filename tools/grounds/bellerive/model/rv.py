# Render the model from the GE cameras in work/cams.json. blender -b --python model/rv.py -- out_dir view ...
import sys, os, math, json
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(SP, 'work'))
import bpy, mathutils
import build, earthcam
build.build_all()
if os.environ.get('FLAT'):
    import hashlib
    for m in list(bpy.data.materials):
        hh=hashlib.md5(m.name.encode()).digest();col=(hh[0]/255,hh[1]/255,hh[2]/255,1)
        m.use_nodes=True;nt=m.node_tree;nt.nodes.clear()
        if os.environ.get('FLAT')=='2':  # exact ID colours (unlit) for measuring
            e=nt.nodes.new('ShaderNodeEmission');e.inputs['Color'].default_value=col
        else:
            e=nt.nodes.new('ShaderNodeBsdfDiffuse');e.inputs['Color'].default_value=col
        o=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(e.outputs[0],o.inputs[0])
C = json.load(open(os.path.join(SP, 'work', 'cams.json')))
DZ = float(open(os.path.join(SP, 'work', 'dz.txt')).read())
sc = bpy.context.scene
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = eng; break
    except Exception:
        pass
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080; sc.render.resolution_percentage = 100
sc.render.film_transparent = True; sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.68, 0.85, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.2; so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(35), 0, math.radians(200))
cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(35); cd.clip_end = 5000
co = bpy.data.objects.new('cam', cd); sc.collection.objects.link(co); sc.camera = co
argv = sys.argv[sys.argv.index('--') + 1:]; out = argv[0] if os.path.isabs(argv[0]) else os.path.join(SP, argv[0])
for v in argv[1:]:
    if v.startswith('top'):  # top / top_<lx>_<ly>: north-up orthographic, 0.25 m/px over +-200 m; lean shears x,y by lx*z, ly*z
        sc.render.resolution_x = sc.render.resolution_y = 1600; cd.type = 'ORTHO'; cd.ortho_scale = 400
        co.matrix_world = mathutils.Matrix.Translation((0, 0, 600))
        if v != 'top':
            lx, ly = map(float, v.split('_')[1:3])
            for ob in sc.objects:
                if ob.type == 'MESH':
                    ob.data.transform(ob.matrix_world.inverted() @ mathutils.Matrix(((1, 0, lx, 0), (0, 1, ly, 0), (0, 0, 1, 0), (0, 0, 0, 1))) @ ob.matrix_world)  # shear the mesh: object matrices can't hold a shear
        sc.render.filepath = os.path.join(out, v + '.png'); bpy.ops.render.render(write_still=True)
        continue
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080; cd.type = 'PERSP'
    x0, y0, a, d, h, t = C[v]; c = earthcam.cam(h, t, d, tz=a - DZ, tx=x0, ty=y0)
    R = mathutils.Matrix((c['right'], c['up'], -c['fwd'])).transposed()
    co.matrix_world = mathutils.Matrix.Translation(c['C']) @ R.to_4x4()
    sc.render.filepath = os.path.join(out, v + '.png'); bpy.ops.render.render(write_still=True)
