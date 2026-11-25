# Manuka proof renders (copied from Bellerive) + GLB. blender -b --python model/proofs.py -- out_dir [glb|stills|turn|close|ids ...]
# Axes: x east, y north, z up (Blender). The glTF exporter's +Y up conversion puts north on glTF -Z.
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE); 
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
T = mathutils.Vector((4.7, -5.0, 0))


def look(eye, tgt):
    eye = mathutils.Vector(eye); d = mathutils.Vector(tgt) - eye
    co.location = eye; co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def orbit(az, el=30, r=330):
    a, e = math.radians(az), math.radians(el)
    look((T.x + r * math.cos(e) * math.sin(a), T.y + r * math.cos(e) * math.cos(a), r * math.sin(e)), T)


def polar(b, r, z):
    return (4.7 + r * math.sin(math.radians(b)), -5.0 + r * math.cos(math.radians(b)), z)


def shot(path):
    sc.render.filepath = path; bpy.ops.render.render(write_still=True); print('rendered', path)


CLOSE = {  # name: (eye, target, fov)
    'bradman_out': (polar(275, 175, 14), polar(275, 100, 9), 45),
    'bradman_in': ((0, 0, 14), polar(275, 80, 9), 45),
    'north_in': ((0, -10, 12), polar(0, 85, 6), 50),
    'media_in': ((0, 10, 12), polar(182, 90, 8), 45),
    'media_out': (polar(182, 170, 12), polar(182, 100, 8), 45),
    'east_in': ((-10, 0, 10), polar(95, 85, 4), 55),
    'scoreboard': ((40, 15, 8), polar(63, 92, 6), 40),
    'tower': (polar(160, 150, 30), polar(160, 125, 38), 45),
}

if 'glb' in jobs:
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, 'manuka.glb'), export_format='GLB',
                              use_selection=False, export_cameras=False, export_lights=False)
    # the seats stay out of the glb: one shell (seat_tmpl.bin, glTF frame) instanced at every seat
    # (seats_<colour>.bin, row-major 3x4 a seat), the MCG's format (GroundModels._add_seats)
    import numpy as np
    for f in os.listdir(out):
        if f.startswith('seats_') and f.endswith('.bin'):
            os.remove(os.path.join(out, f))
    np.array(build.seat_template(), '<f4').tofile(os.path.join(out, 'seat_tmpl.bin'))
    seats = build.seat_list(); n = 0
    for c, xf in build.seat_transforms(seats).items():
        np.array(xf, '<f4').tofile(os.path.join(out, 'seats_%s.bin' % c)); n += len(xf)
        print('seats', c, len(xf))
    print('seats in all:', n)
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
