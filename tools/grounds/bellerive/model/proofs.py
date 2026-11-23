# Bellerive proof renders + GLB. blender -b --python model/proofs.py -- out_dir [glb|stills|turn|close|ids ...]
# Axes: x east, y north, z up (Blender). The glTF exporter's +Y up conversion puts north on glTF -Z.
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(SP, 'work'))
import bpy, mathutils
import build
build.build_all()
sc = bpy.context.scene
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = eng; break
    except Exception:
        pass
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080; sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.68, 0.85, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.2; so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(35), 0, math.radians(200))
cd = bpy.data.cameras.new('cam'); cd.lens_unit = 'FOV'; cd.angle = math.radians(40); cd.clip_end = 5000
co = bpy.data.objects.new('cam', cd); sc.collection.objects.link(co); sc.camera = co
argv = sys.argv[sys.argv.index('--') + 1:]; out = argv[0]; jobs = argv[1:]
os.makedirs(out, exist_ok=True)
T = mathutils.Vector((0, 0, 0))


def look(eye, tgt):
    eye = mathutils.Vector(eye); d = mathutils.Vector(tgt) - eye
    co.location = eye; co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def orbit(az, el=30, r=330):
    a, e = math.radians(az), math.radians(el)
    look((T.x + r * math.cos(e) * math.sin(a), T.y + r * math.cos(e) * math.cos(a), r * math.sin(e)), T)


def polar(b, r, z):
    return (r * math.sin(math.radians(b)), r * math.cos(math.radians(b)), z)


def shot(path):
    sc.render.filepath = path; bpy.ops.render.render(write_still=True); print('rendered', path)


CLOSE = {  # name: (eye, target, fov)
    'facade_boon': (polar(180, 165, 10), polar(180, 100, 8), 45),
    'facade_ponting': (polar(255, 170, 14), polar(255, 100, 10), 45),
    'facade_members': (polar(320, 160, 9), polar(320, 100, 7), 45),
    'join_boon_ponting_out': (polar(212, 150, 12), polar(212, 100, 9), 40),
    'join_boon_ponting_in': (polar(212, 30, 14), polar(212, 85, 9), 45),
    'join_ponting_members_out': (polar(293, 150, 12), polar(293, 100, 9), 40),
    'join_ponting_members_in': (polar(293, 30, 14), polar(293, 85, 9), 45),
    'join_members_end': (polar(352, 60, 10), polar(345, 95, 7), 45),
    'join_terrace_boon': (polar(124, 140, 10), polar(124, 95, 4), 45),
    'join_nstand': (polar(40, 40, 8), polar(30, 82, 3), 45),
    'seats_boon': ((0, -35, 9), (0, -85, 5), 40),
    'seats_ponting': ((-35, 5, 12), (-85, 5, 9), 40),
    'sign_tower': ((-82, 130, 13), (-55, 96.5, 11), 42),
}

if 'glb' in jobs:
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, 'bellerive.glb'), export_format='GLB',
                              use_selection=False, export_cameras=False, export_lights=False)
if 'stills' in jobs:
    for az in (0, 45, 90, 135, 180, 225, 270, 315):
        orbit(az); shot(os.path.join(out, f'turntable_{az:03d}.png'))
if 'close' in jobs:
    for k, (e, t, f) in CLOSE.items():
        cd.angle = math.radians(f); look(e, t); shot(os.path.join(out, f'close_{k}.png'))
    cd.angle = math.radians(40)
if 'turn' in jobs:
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    os.makedirs(os.path.join(out, 'turn'), exist_ok=True)
    for k in range(48):
        orbit(k * 7.5); shot(os.path.join(out, 'turn', f'f{k:03d}.png'))
