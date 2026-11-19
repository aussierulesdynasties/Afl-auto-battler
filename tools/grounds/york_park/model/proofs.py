# York Park proof renders + GLB (same method as the MCG proofs). blender -b --python model/proofs.py -- out_dir [glb|stills|close|joins|seats|sign|orbit ...]
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
T = mathutils.Vector((0, 0, 5))
dg = bpy.context.evaluated_depsgraph_get()


def look(eye, tgt):
    eye = mathutils.Vector(eye); d = mathutils.Vector(tgt) - eye
    co.location = eye; co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def orbit(az, el=32, r=380):
    a, e = math.radians(az), math.radians(el)
    look((T.x + r * math.cos(e) * math.sin(a), T.y + r * math.cos(e) * math.cos(a), r * math.sin(e)), T)


def shot(path):
    sc.render.filepath = path; bpy.ops.render.render(write_still=True); print('rendered', path)


def hit(b, z, inward=True):
    """first surface met along bearing b at height z: from 200 m out coming in, or from the centre going out"""
    s = mathutils.Vector((math.sin(math.radians(b)), math.cos(math.radians(b)), 0))
    o, d = (s * 200 + mathutils.Vector((0, 0, z)), -s) if inward else (mathutils.Vector((0, 0, z)), s)
    ok, loc, nrm, *_ = sc.ray_cast(dg, o, d)
    return loc if ok else None


if 'glb' in jobs:   # Blender +Y (north) becomes glTF -Z
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, 'york_park.glb'), export_format='GLB',
                              use_selection=False, export_cameras=False, export_lights=False)
if 'stills' in jobs:
    for az in range(0, 360, 45):
        orbit(az); shot(os.path.join(out, f'turntable_{az:03d}.png'))
if 'close' in jobs:  # one close-up per hand-painted facade, 16 m out
    cd.angle = math.radians(50)
    for b, z, name in ((325, 5, 'nw_back'), (10, 5, 'north_back'), (51, 2.5, 'north_pavilion'), (69, 2.5, 'east_pavilion'), (120, 5, 'east_back'),
                       (175, 5, 'south_east_back'), (215, 5, 'sw_building'), (250, 6, 'gunns_back'), (295, 6, 'cw_back')):
        p = hit(b, z)
        if p is None: print('no hit', b); continue
        n = mathutils.Vector((math.sin(math.radians(b)), math.cos(math.radians(b)), 0))
        look(p + n * 16 + mathutils.Vector((0, 0, 1.5)), p + mathutils.Vector((0, 0, 1.5)))
        shot(os.path.join(out, f'facade_{int(b):03d}_{name}.png'))
    cd.angle = math.radians(40)
if 'joins' in jobs:  # where parts meet, seen from outside 30 m out
    cd.angle = math.radians(55)
    for b, z0, up, name in ((305, 6, 8, 'cw_nw'), (280, 6, 8, 'gunns_cw'), (221, 5, 8, 'sw_gunns'), (208, 5, 6, 'es_sw'),
                            (40, 4, 6, 'north_ne_gap'), (60, 3, 9, 'scoreboard_base'), (76, 4, 6, 'ne_gap_east'), (157, 4, 5, 'south_tower_foot')):
        p = hit(b, z0) or mathutils.Vector((110 * math.sin(math.radians(b)), 110 * math.cos(math.radians(b)), z0))
        n = mathutils.Vector((math.sin(math.radians(b)), math.cos(math.radians(b)), 0))
        look(p + n * 30 + mathutils.Vector((0, 0, 3)), p + mathutils.Vector((0, 0, up)))
        shot(os.path.join(out, f'join_{int(b):03d}_{name}.png'))
    cd.angle = math.radians(40)
if 'seats' in jobs:  # empty seats: from the boundary looking up into the Gunns and the Northern stand
    cd.angle = math.radians(45)
    for b, name in ((250, 'gunns'), (10, 'north'), (120, 'east')):
        s = mathutils.Vector((math.sin(math.radians(b)), math.cos(math.radians(b)), 0)); p = s * (build.fence_r(b) - 6)
        look(p + mathutils.Vector((0, 0, 1.7)), p + s * 20 + mathutils.Vector((0, 0, 5)))
        shot(os.path.join(out, f'seats_{name}.png'))
    cd.angle = math.radians(40)
if 'sign' in jobs:   # the name sign from the pitch, as in the photo
    cd.angle = math.radians(30)
    G = build.D['signs'][0]; c = mathutils.Vector((*G['c'], G['z0'] + G['h'] / 2))
    look(c + mathutils.Vector((24, -6, -6)), c); shot(os.path.join(out, 'sign_utas.png'))
    cd.angle = math.radians(40)
if 'orbit' in jobs:
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    os.makedirs(os.path.join(out, 'orbit'), exist_ok=True)
    for k in range(120):
        orbit(k * 3); shot(os.path.join(out, 'orbit', f'f{k:03d}.png'))
