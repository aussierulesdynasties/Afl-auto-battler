# ENGIE proof renders and the GLB. Run with the bpy module:
#   python3 proofs.py OUT_DIR glb            -> OUT_DIR/engie.glb + seat files (seat_tmpl_*.bin, seats_*.bin, legs_*.bin)
#   (renders: --with=OTHER.glb also draws that glb, e.g. the surroundings from surrounds/landmarks.py)
#   python3 proofs.py OUT_DIR plan             -> OUT_DIR/plan.png, orthographic, 520 m square, north up
#   python3 proofs.py OUT_DIR views V.json [names...]  -> renders matching Google Earth views (ge_compare.py cameras)
# Axes: x east, y north, z up (Blender); the glTF exporter puts north on glTF -Z.
import sys, os, math, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, mathutils
import numpy as np
import build
argv = sys.argv[1:]
WITH = [a.split('=', 1)[1] for a in argv if a.startswith('--with=')]   # extra glbs (the surroundings) for renders
argv = [a for a in argv if not a.startswith('--with=')]
out = argv[0]; job = argv[1]
os.makedirs(out, exist_ok=True)
build.build_all()
for g in WITH:
    bpy.ops.import_scene.gltf(filepath=g)
sc = bpy.context.scene


def glb():
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, 'engie.glb'), export_format='GLB',
                              use_selection=False, export_cameras=False, export_lights=False, export_image_format='WEBP')
    for f in os.listdir(out):
        if (f.startswith('seats_') or f.startswith('legs_') or f.startswith('seat_tmpl')) and f.endswith('.bin'):
            os.remove(os.path.join(out, f))
    seats = build.seat_list(); xf = build.seat_transforms(seats); n = 0
    for c, rows in xf.items():
        np.array(rows, '<f4').tofile(os.path.join(out, 'seats_%s.bin' % c)); n += len(rows)
        np.array(build.seat_pad(), '<f4').tofile(os.path.join(out, 'seat_tmpl_%s.bin' % c))
        print('seats', c, len(rows))
    allx = [r for rows in xf.values() for r in rows]
    np.array(allx, '<f4').tofile(os.path.join(out, 'legs_seat_engie_shell.bin'))
    np.array(build.seat_shell(), '<f4').tofile(os.path.join(out, 'leg_tmpl.bin'))
    print('seats in all:', n)


def setup_render(w=1280, h=720):
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.device = 'CPU'
    try:
        sc.cycles.use_denoising = True
    except Exception:
        pass
    sc.render.resolution_x, sc.render.resolution_y = w, h; sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = 'Standard'
    wd = bpy.data.worlds.new('w'); sc.world = wd; wd.use_nodes = True
    wd.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.68, 0.85, 1)
    wd.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.8
    sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.5; so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(40), 0, math.radians(30))
    # a field for context
    sur = os.path.join(HERE, '..', '..', '..', '..', 'assets', 'grounds', 'engie', 'surrounds.webp')
    big = bool(WITH) and os.path.exists(sur)
    bpy.ops.mesh.primitive_plane_add(size=2048 if big else 400, location=(0, 0, -0.04))
    fm = bpy.data.materials.new('field'); fm.use_nodes = True
    if big:   # the surroundings map (surrounds/surrounds.py), as the game lays it
        tx = fm.node_tree.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(sur)
        fm.node_tree.links.new(tx.outputs['Color'], fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    else:
        fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.12, 0.25, 0.08, 1)
    bpy.context.object.data.materials.append(fm)
    cd = bpy.data.cameras.new('cam'); cd.clip_end = 6000; cd.sensor_fit = 'VERTICAL'
    co = bpy.data.objects.new('cam', cd); sc.collection.objects.link(co); sc.camera = co
    return co


def views(vfile, names):
    co = setup_render()
    V = json.load(open(vfile))
    for v in V:
        if names and v['name'] not in names:
            continue
        e, n, u = v.get('at', [0, 0, 0])
        h, t, d = math.radians(v['h']), math.radians(v['t']), v['d']
        dirv = np.array([math.sin(t) * math.sin(h), math.sin(t) * math.cos(h), -math.cos(t)])
        cam = np.array([e, n, u]) - d * dirv
        if v['t'] < 3:
            cam[1] -= 0.05 * d
        co.location = mathutils.Vector(cam)
        co.rotation_euler = mathutils.Vector(np.array([e, n, u]) - cam).to_track_quat('-Z', 'Y').to_euler()
        co.data.angle = math.radians(v.get('fov', 26.8))
        sc.render.filepath = os.path.join(out, v['name'] + '.png'); bpy.ops.render.render(write_still=True)
        print('rendered', v['name'])


def plan(size=520.0, px=1040):
    # straight-down orthographic render, north up, centred on the origin: lines up with the Esri ortho
    co = setup_render(px, px)
    co.data.type = 'ORTHO'; co.data.ortho_scale = size
    co.location = (0, 0, 400); co.rotation_euler = (0, 0, 0)
    sc.render.filepath = os.path.join(out, 'plan.png'); bpy.ops.render.render(write_still=True)


if job == 'glb':
    glb()
elif job == 'plan':
    plan()
elif job == 'views':
    views(argv[2], argv[3:])
